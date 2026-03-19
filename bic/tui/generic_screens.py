from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Header, Footer, Static, DataTable, Button, Input
from textual.containers import Vertical, Horizontal
from functools import partial
import inspect

from bic.core import BIC_DB
from bic.ui.schema import UIView, UIAction, UIMenuItem

class GenericListScreen(Screen):
    """A generic screen to display a list of items in a table."""

    BINDINGS = [Binding("b", "app.pop_screen", "Back")]

    def __init__(self, db_core: BIC_DB, view: UIView, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core
        self.view = view
        self.items = []
        self.selected_item = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(self.view.name, classes="title")
        yield DataTable()
        yield Horizontal(id="action-buttons-container", classes="hidden")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        columns = [col['label'] for col in self.view.columns]
        table.add_columns(*columns)

        self.items = self.view.handler(self.db_core)
        for item in self.items:
            row_data = [str(item.get(col['key'], '')) for col in self.view.columns]
            table.add_row(*row_data)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.selected_item = self.items[event.cursor_row]
        buttons_container = self.query_one("#action-buttons-container")
        buttons_container.remove_children()
        
        action_buttons = []
        for action_item in self.view.actions:
            button = Button(action_item.name, id=action_item.path)
            action_buttons.append(button)
        
        if action_buttons:
            buttons_container.mount(*action_buttons)
            buttons_container.remove_class("hidden")
        else:
            buttons_container.add_class("hidden")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        action_to_run = None
        for action_item in self.view.actions:
            if event.button.id == action_item.path:
                action_to_run = action_item.item
                break
        
        if action_to_run and isinstance(action_to_run, UIAction):
            self.app.push_screen(GenericFormScreen(self.db_core, action_to_run, self.selected_item['id']))

class GenericFormScreen(Screen):
    """A generic screen to display a form for an action."""

    BINDINGS = [Binding("b", "app.pop_screen", "Back")]

    def __init__(self, db_core: BIC_DB, action: UIAction, item_id: int = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core
        self.action = action
        self.item_id = item_id

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(self.action.name, classes="title")
        
        initial_data = {}
        if self.action.loader:
            sig = inspect.signature(self.action.loader)
            if 'id' in sig.parameters and self.item_id is not None:
                initial_data = self.action.loader(db_core=self.db_core, id=self.item_id)
            elif 'id' not in sig.parameters:
                try:
                    initial_data = self.action.loader(db_core=self.db_core)
                except TypeError:
                    # This can happen if the loader expects no arguments
                    initial_data = self.action.loader()

        with Vertical(id="form-container"):
            for field in self.action.form_fields:
                input_widget = Input(
                    placeholder=field.label, 
                    id=field.name, 
                    value=str(initial_data.get(field.name, ''))
                )
                if field.type == 'hidden' or field.name == 'id':
                    input_widget.display = False
                yield input_widget
            yield Button("Submit", id="submit_button", variant="success")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit_button":
            form_data = {}
            for field in self.action.form_fields:
                form_data[field.name] = self.query_one(f"#{field.name}", Input).value
            
            if self.item_id and 'id' not in form_data:
                 form_data['id'] = self.item_id

            try:
                self.action.handler(db_core=self.db_core, **form_data)
                self.app.pop_screen()
            except Exception as e:
                self.query_one(".title").update(f"{self.action.name} [bold red]Error: {e}[/]")
