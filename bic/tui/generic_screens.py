from textual.app import ComposeResult
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Header, Footer, Static, DataTable, Button
from textual.containers import Vertical, Horizontal
from textual.coordinate import Coordinate

from bic.core import BIC_DB
from bic.ui.schema import UIView, UIAction

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
        table.add_columns(*[col['label'] for col in self.view.columns])
        self.items = self.view.handler(self.db_core)
        for item in self.items:
            table.add_row(*[str(item.get(col['key'], '')) for col in self.view.columns])

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.selected_item = self.items[event.cursor_row]
        buttons_container = self.query_one("#action-buttons-container")
        buttons_container.remove_children()
        
        action_buttons = []
        for action in self.view.actions:
            action_buttons.append(Button(action.name, id=action.name.lower().replace(' ', '-')))
        
        if action_buttons:
            buttons_container.mount(*action_buttons)
            buttons_container.remove_class("hidden")
        else:
            buttons_container.add_class("hidden")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        action_to_run = None
        for action in self.view.actions:
            if event.button.id == action.name.lower().replace(' ', '-'):
                action_to_run = action
                break

        if action_to_run:
            # For forms, we need to pass the selected item ID to the loader
            if action_to_run.form_fields:
                # A bit of a hack: create a new action instance with a bound loader
                from functools import partial
                bound_loader = partial(action_to_run.loader, db_core=self.db_core, id=self.selected_item['id'])
                # We need a new type of form screen that can handle this, or modify GenericFormScreen
                # For now, let's assume GenericFormScreen is modified.
                self.app.push_screen(GenericFormScreen(self.db_core, action_to_run, self.selected_item['id']))
            else:
                # For actions without forms (like Send Email), just run the handler
                action_to_run.handler(db_core=self.db_core, id=self.selected_item['id'])
                self.query_one(".title").update(f"{self.view.name} - '{action_to_run.name}' executed.")


from textual.widgets import Input

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
        if self.action.loader and self.item_id:
            initial_data = self.action.loader(db_core=self.db_core, id=self.item_id)
        elif self.action.loader: # For loaders that don't need an ID (like global settings)
             initial_data = self.action.loader(self.db_core)

        with Vertical(id="form-container"):
            for field in self.action.form_fields:
                # Hide the ID field if it exists
                input_widget = Input(placeholder=field.label, id=field.name, value=str(initial_data.get(field.name, '')))
                if field.name == 'id':
                    input_widget.display = False
                yield input_widget
            yield Button("Submit", id="submit_button", variant="success")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit_button":
            form_data = {}
            for field in self.action.form_fields:
                form_data[field.name] = self.query_one(f"#{field.name}", Input).value
            
            # Ensure the item_id is included for handlers that need it (edit/delete/swap)
            if self.item_id and 'id' not in form_data:
                 form_data['id'] = self.item_id

            try:
                self.action.handler(db_core=self.db_core, **form_data)
                self.app.pop_screen()
                # We may need to refresh the parent list screen here
            except Exception as e:
                self.query_one(".title").update(f"{self.action.name} [bold red]Error: {e}[/]")
