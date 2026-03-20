from dataclasses import dataclass, field
from typing import List, Optional, Callable, Any, Dict

# --- Form Field Definitions ---

@dataclass
class FormSelectOption:
    """Represents a single option in a form select field."""
    label: str
    value: Any

@dataclass
class FormField:
    """Represents a single field within a form."""
    name: str
    label: str
    type: str = "text"
    required: bool = False
    default: Optional[Any] = None
    placeholder: Optional[str] = None
    readonly: bool = False
    help_text: Optional[str] = None
    options: List[FormSelectOption] = field(default_factory=list)
    required_role: Optional[str] = None

    options_loader: Optional[Callable] = None

# --- UI Action & View Definitions ---

@dataclass
class TableColumn:
    """Represents a single column in a UI data table."""
    name: str
    label: str

# --- UI Action & View Definitions ---

@dataclass
class UIAction:
    """Represents an action that can be performed in the UI (e.g., submitting a form)."""
    name: str
    handler: Callable
    form_fields: List[FormField] = field(default_factory=list)
    redirect_to: Optional[str] = None
    template: Optional[str] = None
    loader: Optional[Callable] = None
    actions: Optional[List['UIMenuItem']] = field(default_factory=list)
    required_role: Optional[str] = None

@dataclass
class UIView:
    """Represents a view of data in the UI (e.g., a list of clients)."""
    name: str
    template: str
    handler: Optional[Callable] = None
    loader: Optional[Callable] = None
    table_columns: List[TableColumn] = field(default_factory=list)
    actions: Optional[List['UIMenuItem']] = field(default_factory=list)
    context_name: str = "data"

# --- Menu Item & Menu Definitions ---

@dataclass
class UIMenuItem:
    """Represents a single item in a menu, which can be a link, a submenu, or an action."""
    name: str
    path: str
    item: Optional[Any] = None  # Can be a UIView, UIAction, or UIMenu
    hidden: bool = False
    required_role: Optional[str] = None

@dataclass
class UIMenu:
    """Represents a menu, which contains a list of UIMenuItems."""
    name: str
    items: List[UIMenuItem]
    required_role: Optional[str] = None
