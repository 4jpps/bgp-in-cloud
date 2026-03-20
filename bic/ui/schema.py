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
    options: List[FormSelectOption] = field(default_factory=list)
    options_loader: Optional[Callable] = None
    default: Optional[Any] = None
    placeholder: Optional[str] = None

# --- UI Action & View Definitions ---

@dataclass
class UIAction:
    """Represents a form-based action in the UI (e.g., Edit, Create)."""
    name: str
    handler: Callable
    form_fields: List[FormField]
    loader: Optional[Callable] = None
    actions: Optional[List['UIMenuItem']] = field(default_factory=list)

@dataclass
class UIView:
    """Represents a view of data in the UI (e.g., a list of clients)."""
    name: str
    handler: Callable
    columns: List[Dict[str, str]]
    actions: Optional[List['UIMenuItem']] = field(default_factory=list)

# --- Menu Item & Menu Definitions ---

@dataclass
class UIMenuItem:
    """Represents a single item in a menu, which can be a link, a submenu, or an action."""
    name: str
    path: str
    item: Optional[Any] = None  # Can be a UIView, UIAction, or UIMenu
    hidden: bool = False

@dataclass
class UIMenu:
    """Represents a menu, which contains a list of UIMenuItems."""
    name: str
    items: List[UIMenuItem]
