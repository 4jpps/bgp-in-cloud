from bic.ui.main import main_menu as menu_structure
from bic.ui.schema import UIMenu, UIAction, UIView, UIMenuItem

def find_ui_item_by_path(path: str, menu: UIMenu = menu_structure) -> UIMenu | UIAction | UIView | None:
    """Recursively searches the menu structure for an item by its path."""
    for item in menu.items:
        # First, check for dynamic path matches (e.g., /edit/{id})
        # This is a simple placeholder replacement. A real implementation would use regex.
        if '{' in item.path and '}' in item.path:
            base_path = item.path.split('{')[0]
            if path.startswith(base_path):
                return item.item # It's a match, return the underlying action/view

        # Then check for an exact static path match
        if item.path == path:
            return item.item

        # Then, recurse into submenus
        if isinstance(item.item, UIMenu) and path.startswith(item.path + '/'):
            found = find_ui_item_by_path(path, item.item)
            if found:
                return found
    return None
