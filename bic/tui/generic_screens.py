from textual.app import ComposeResult, App
from textual.screen import Screen
from textual.binding import Binding
from textual.widgets import Header, Footer, Static, DataTable, Button, Input, Select
from textual.containers import Vertical
from textual.css.query import NoMatches

from bic.core import BIC_DB
from bic.ui.schema import UIView, UIAction, FormField
from bic.tui.utils import find_ui_item_by_path

class GenericListScreen(Screen):
    """A generic screen to display a list of items from a handler."""

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
        yield Vertical(id="action-buttons-container", classes="hidden")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        if not self.view.columns:
            self.app.pop_screen()
            return
        
        table.add_columns(*[col['label'] for col in self.view.columns])
        self.items = self.view.handler(db_core=self.db_core)
        for item in self.items:
            row = [str(item.get(col['key'], '')) for col in self.view.columns]
            table.add_row(*row)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        self.selected_item = self.items[event.cursor_row]
        buttons_container = self.query_one("#action-buttons-container")
        buttons_container.remove_children()
        
        action_buttons = []
        if self.view.actions:
            for action_menu_item in self.view.actions:
                # The path for the button is the action's path, with {id} replaced.
                action_path = action_menu_item.path.format(id=self.selected_item['id'])
                button = Button(action_menu_item.name, id=action_path)
                action_buttons.append(button)

        if action_buttons:
            buttons_container.mount(*action_buttons)
            buttons_container.remove_class("hidden")
        else:
            buttons_container.add_class("hidden")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        action_path = event.button.id
        action_item = find_ui_item_by_path(action_path)

        if isinstance(action_item, UIAction):
            # Extract dynamic parts of the path to pass to the form screen
            path_parts = action_path.split('/')
            item_id = path_parts[-1] if path_parts[-1].isdigit() else None
            self.app.push_screen(GenericFormScreen(self.db_core, action_item, item_id=item_id))
        # Add logic for other item types if needed (e.g., navigating to another view)

class GenericFormScreen(Screen):
    """A generic screen that dynamically builds a form from a UIAction."""

    BINDINGS = [Binding("b", "app.pop_screen", "Back")]

    def __init__(self, db_core: BIC_DB, action: UIAction, item_id: str | int | None = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_core = db_core
        self.action = action
        self.item_id = item_id
        self.form_widgets = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(self.action.name, classes="title")
        
        initial_data = {}
        if self.action.loader and self.item_id:
            initial_data = self.action.loader(db_core=self.db_core, id=self.item_id)
        elif self.action.loader:
            initial_data = self.action.loader(db_core=self.db_core)

        with Vertical(id="form-container"):
            for field in self.action.form_fields:
                # Use the loaded data for the value, falling back to the field's default
                value = initial_data.get(field.name, field.default)
                
                if field.type == 'select':
                    options = field.options or []
                    if field.options_loader:
                        options.extend(field.options_loader(db_core=self.db_core))
                    
                    # Textual Select expects a list of tuples (label, value)
                    select_options = [(opt.label, opt.value) for opt in options]
                    widget = Select(select_options, value=value, id=field.name, prompt=field.label)
                else:
                    widget = Input(
                        placeholder=field.label,
                        id=field.name,
                        value=str(value or ''),
                        password=(field.type == 'password'),
                        type=field.type
                    )

                if field.type == 'hidden' or field.readonly:
                    widget.display = False # Or set to read_only if that's a feature
                
                self.form_widgets[field.name] = widget
                yield widget
            yield Button("Submit", id="submit_button", variant="success")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit_button":
            form_data = {}
            for name, widget in self.form_widgets.items():
                form_data[name] = widget.value
            
            # Ensure the ID from the path is included if not in the form
            if self.item_id and 'id' not in form_data:
                 form_data['id'] = self.item_id

            try:
                self.action.handler(db_core=self.db_core, **form_data)
                # Pop twice if coming from a list screen -> form
                self.app.pop_screen()
                self.app.pop_screen()
            except Exception as e:
                self.query_one(".title").update(f"{self.action.name} [bold red]Error: {e}[/]")
