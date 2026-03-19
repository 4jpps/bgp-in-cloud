from dataclasses import dataclass, field
from typing import List, Dict, Any, Callable, Type, Optional

from textual.screen import Screen

@dataclass
class FormSelectOption:
    label: str
    value: Any

@dataclass
class FormField:
    name: str
    label: Optional[str] = None
    type: str = "text"
    required: bool = False
    default: Any = None
    options: List[FormSelectOption] = field(default_factory=list)
    options_loader: Callable = None

@dataclass
class UIAction:
    name: str
    handler: Callable
    loader: Callable = None # Optional function to load initial form data
    tui_screen: Type[Screen] = None
    form_fields: List[FormField] = field(default_factory=list)
    actions: List["UIMenuItem"] = field(default_factory=list) # Nested actions

@dataclass
class UIMenuItem:
    name: str
    path: str # e.g. "/clients/list"
    description: str = ""
    item: Any = None # Can be a UIAction, UIView, or another UIMenu
    hidden: bool = False

@dataclass
class UIView:
    name: str
    handler: Callable
    tui_screen: Type[Screen] = None
    columns: List[Dict[str, str]] = field(default_factory=list)
    actions: List[UIMenuItem] = field(default_factory=list)

@dataclass
class UIMenu:
    name: str
    items: List[UIMenuItem] = field(default_factory=list)
