"""PowerBuilder menu to Flutter/Python converter.

Converts PowerBuilder menu definitions to Flutter AppBar actions
or Python Tkinter/PyQt menus.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MenuItem:
    """Represents a menu item."""
    name: str
    text: str
    enabled: bool = True
    visible: bool = True
    checked: bool = False
    shortcut: str | None = None
    icon: str | None = None
    on_click: str | None = None
    children: list["MenuItem"] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:




        """Convert to dictionary for template rendering."""
        result = {
            "name": self.name, "text": self.text, "enabled": self.enabled, "visible": self.visible, "checked": self.checked, "shortcut": self.shortcut, "icon": self.icon, "on_click": self.on_click, "has_children": len(self.children) > 0, "children": [child.to_dict() for child in self.children],
        }

        # Convert shortcut to Flutter format
        if self.shortcut:
            result["flutter_shortcut"] = self._convert_shortcut_to_flutter(self.shortcut)
            result["python_shortcut"] = self._convert_shortcut_to_python(self.shortcut)

        return result

    def _convert_shortcut_to_flutter(self, shortcut: str) -> str:




        """Convert PowerBuilder shortcut to Flutter format."""
        # PowerBuilder uses Ctrl+X, Alt+X, Shift+X, F1-F12
        # Flutter uses LogicalKeySet with LogicalKeyboardKey

        parts = shortcut.upper().split("+")
        modifiers = []
        key = parts[-1]

        for part in parts[:-1]:
            if part == "CTRL":
                modifiers.append("control")
            elif part == "ALT":
                modifiers.append("alt")
            elif part == "SHIFT":
                modifiers.append("shift")

        # Convert key
        if key.startswith("F") and key[1:].isdigit():
            flutter_key = f"f{key[1:]}"
        else:
            flutter_key = key.lower()

        return {
            "modifiers": modifiers, "key": flutter_key,
        }

    def _convert_shortcut_to_python(self, shortcut: str) -> str:




        """Convert PowerBuilder shortcut to Python/Tkinter format."""
        # Tkinter uses <Control-x>, <Alt-x>, <Shift-x>
        shortcut = shortcut.replace("Ctrl+", "<Control-")
        shortcut = shortcut.replace("Alt+", "<Alt-")
        shortcut = shortcut.replace("Shift+", "<Shift-")
        if not shortcut.startswith("<"):
            shortcut = f"<{shortcut}"
        if not shortcut.endswith(">"):
            shortcut = f"{shortcut}>"
        return shortcut


@dataclass
class MenuDefinition:
    """Represents a complete menu definition."""
    name: str
    menu_bar: list[MenuItem] = field(default_factory=list)
    context_menus: dict[str, list[MenuItem]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:




        """Convert to dictionary for template rendering."""
        return {
            "name": self.name, "menu_bar": [item.to_dict() for item in self.menu_bar], "has_menu_bar": len(self.menu_bar) > 0, "context_menus": {
                name: [item.to_dict() for item in items]
                for name, items in self.context_menus.items()
            }, "has_context_menus": len(self.context_menus) > 0,
        }


class MenuConverter:
    """Converts PowerBuilder menus to Flutter/Python menus."""

    def __init__(self) -> None:




        """Initialize the menu converter."""
        self._current_menu = None
        self._menu_items = {}

    def convert_menu(self, menu_syntax: str, menu_name: str) -> MenuDefinition:




        """Convert PowerBuilder menu syntax to MenuDefinition.

        Args:
            menu_syntax: PowerBuilder menu syntax/source
            menu_name: Name of the menu

        Returns:
            MenuDefinition object
        """
        definition = MenuDefinition(name=self._to_pascal_case(menu_name))
        self._current_menu = definition

        # Parse menu structure
        menu_items = self._parse_menu_structure(menu_syntax)

        # Build hierarchy
        root_items = self._build_menu_hierarchy(menu_items)

        # Separate menu bar from context menus
        for item in root_items:
            if self._is_context_menu(item):
                definition.context_menus[item.name] = item.children
            else:
                definition.menu_bar.append(item)

        return definition

    def _parse_menu_structure(self, syntax: str) -> dict[str, MenuItem]:




        """Parse menu structure from PowerBuilder syntax."""
        items = {}

        # Pattern to match menu definitions
        # Format: on m_menu.create
        #         m_menu = this
        #         this.Item[1] = m_file
        #         this.Item[2] = m_edit
        #         ...

        # First, extract all menu item definitions
        menu_pattern = r"global\s+type\s+(\w+)\s+from\s+menu"
        menu_matches = re.findall(menu_pattern, syntax, re.IGNORECASE)

        for menu_name in menu_matches:
            item = self._parse_menu_item(syntax, menu_name)
            if item:
                items[menu_name] = item

        # Also look for inline menu definitions
        item_pattern = r"this\.(\w+)\s*=\s*create\s+(\w+)"
        item_matches = re.findall(item_pattern, syntax, re.IGNORECASE)

        for prop_name, menu_type in item_matches:
            if menu_type not in items:
                item = MenuItem(name=menu_type, text=self._humanize_name(menu_type))
                items[menu_type] = item

        return items

    def _parse_menu_item(self, syntax: str, item_name: str) -> MenuItem | None:




        """Parse a single menu item definition."""
        # Look for the menu item's properties
        item = MenuItem(name=item_name, text=self._humanize_name(item_name))

        # Extract text property
        text_pattern = rf'{item_name}\.text\s*=\s*"([^"]*)"'
        text_match = re.search(text_pattern, syntax, re.IGNORECASE)
        if text_match:
            item.text = text_match.group(1)

        # Extract enabled property
        enabled_pattern = rf"{item_name}\.enabled\s*=\s*(true|false)"
        enabled_match = re.search(enabled_pattern, syntax, re.IGNORECASE)
        if enabled_match:
            item.enabled = enabled_match.group(1).lower() == "true"

        # Extract visible property
        visible_pattern = rf"{item_name}\.visible\s*=\s*(true|false)"
        visible_match = re.search(visible_pattern, syntax, re.IGNORECASE)
        if visible_match:
            item.visible = visible_match.group(1).lower() == "true"

        # Extract checked property
        checked_pattern = rf"{item_name}\.checked\s*=\s*(true|false)"
        checked_match = re.search(checked_pattern, syntax, re.IGNORECASE)
        if checked_match:
            item.checked = checked_match.group(1).lower() == "true"

        # Extract shortcut
        shortcut_pattern = rf'{item_name}\.shortcut\s*=\s*"([^"]*)"'
        shortcut_match = re.search(shortcut_pattern, syntax, re.IGNORECASE)
        if shortcut_match:
            item.shortcut = shortcut_match.group(1)

        # Extract click event
        click_pattern = rf"on\s+{item_name}\.clicked.*?end\s+on"
        click_match = re.search(click_pattern, syntax, re.IGNORECASE | re.DOTALL)
        if click_match:
            item.on_click = f"on{self._to_pascal_case(item_name)}Click"

        # Look for child items
        child_pattern = rf"{item_name}\.Item\[\d+\]\s*=\s*(\w+)"
        child_matches = re.findall(child_pattern, syntax, re.IGNORECASE)

        for child_name in child_matches:
            # These will be linked in hierarchy building
            pass

        return item

    def _build_menu_hierarchy(self, items: dict[str, MenuItem]) -> list[MenuItem]:




        """Build menu hierarchy from flat item list."""
        root_items = []

        # Find parent-child relationships
        for item_name, item in items.items():
            # Look for items that are top-level (usually start with m_)
            if item_name.startswith("m_") and "_" not in item_name[2:]:
                root_items.append(item)
                # Find children
                self._find_children(item, items)

        return root_items

    def _find_children(self, parent: MenuItem, all_items: dict[str, MenuItem]) -> None:




        """Recursively find children for a menu item."""
        parent_prefix = parent.name + "_"

        for item_name, item in all_items.items():
            if item_name.startswith(parent_prefix) and item_name != parent.name:
                # Check if this is a direct child (no additional underscores)
                suffix = item_name[len(parent_prefix):]
                if "_" not in suffix:
                    parent.children.append(item)
                    # Recursively find children of this item
                    self._find_children(item, all_items)

    def _is_context_menu(self, item: MenuItem) -> bool:




        """Check if a menu item is a context menu."""
        # Context menus typically have names like m_popup or m_context
        name_lower = item.name.lower()
        return "popup" in name_lower or "context" in name_lower

    def _humanize_name(self, name: str) -> str:




        """Convert menu name to human-readable text."""
        # Remove m_ prefix
        if name.startswith("m_"):
            name = name[2:]

        # Split by underscore and capitalize
        parts = name.split("_")
        return " ".join(p.capitalize() for p in parts)

    def _to_pascal_case(self, name: str) -> str:




        """Convert name to PascalCase."""
        # Remove m_ prefix if present
        if name.startswith("m_"):
            name = name[2:]

        # Convert to PascalCase
        parts = name.split("_")
        return "".join(p.capitalize() for p in parts)

    def generate_flutter_menu(self, menu_def: MenuDefinition) -> dict[str, list[str]]:




        """Generate Flutter menu implementation.

        Returns:
            Dictionary with 'app_bar_actions' and 'popup_menu' code
        """
        code = {
            "app_bar_actions": [], "popup_menu": [], "menu_callbacks": [],
        }

        # Generate app bar actions for top-level menu
        if menu_def.menu_bar:
            code["app_bar_actions"] = self._generate_flutter_app_bar_actions(menu_def.menu_bar)

        # Generate popup menus
        for menu_name, items in menu_def.context_menus.items():
            popup_code = self._generate_flutter_popup_menu(menu_name, items)
            code["popup_menu"].extend(popup_code)

        # Generate callback methods
        code["menu_callbacks"] = self._generate_flutter_callbacks(menu_def)

        return code

    def _generate_flutter_app_bar_actions(self, items: list[MenuItem]) -> list[str]:




        """Generate Flutter AppBar actions."""
        lines = []

        lines.append("actions: [")

        for item in items:
            if item.children:
                # Dropdown menu
                lines.append("  PopupMenuButton(")
                lines.append(f'    tooltip: "{item.text}", ')
                lines.append("    itemBuilder: (context) => [")

                for child in item.children:
                    if child.text == "-":
                        lines.append("      const PopupMenuDivider(), ")
                    else:
                        lines.append("      PopupMenuItem(")
                        lines.append(f'        value: "{child.name}", ')
                        lines.append(f"        enabled: {str(child.enabled).lower()}, ")
                        lines.append("        child: ListTile(")
                        if child.icon:
                            lines.append(f"          leading: Icon(Icons.{child.icon}), ")
                        lines.append(f'          title: Text("{child.text}"), ')
                        if child.shortcut:
                            lines.append(f'          trailing: Text("{child.shortcut}"), ')
                        lines.append("        ), ")
                        lines.append("      ), ")

                lines.append("    ], ")
                lines.append("    onSelected: (value) => _handleMenuAction(value), ")
                lines.append("  ), ")
            else:
                # Simple action button
                lines.append("  IconButton(")
                lines.append(f'    icon: Icon(Icons.{item.icon or "more_vert"}), ')
                lines.append(f'    tooltip: "{item.text}", ')
                if item.on_click:
                    lines.append(f"    onPressed: {item.on_click}, ")
                else:
                    lines.append('    onPressed: () => _handleMenuAction("' + item.name + '"), ')
                lines.append("  ), ")

        lines.append("], ")

        return lines

    def _generate_flutter_popup_menu(self, menu_name: str, items: list[MenuItem]) -> list[str]:




        """Generate Flutter popup menu."""
        lines = []

        method_name = f"_show{self._to_pascal_case(menu_name)}Menu"

        lines.append(f"void {method_name}(BuildContext context, Offset position) async {{")
        lines.append("  final selected = await showMenu(")
        lines.append("    context: context, ")
        lines.append("    position: RelativeRect.fromLTRB(")
        lines.append("      position.dx, position.dy, ")
        lines.append("      position.dx, position.dy, ")
        lines.append("    ), ")
        lines.append("    items: [")

        for item in items:
            if item.text == "-":
                lines.append("      const PopupMenuDivider(), ")
            else:
                lines.append(f'      PopupMenuItem(value: "{item.name}", ')
                lines.append(f"        enabled: {str(item.enabled).lower()}, ")
                lines.append(f'        child: Text("{item.text}"), ')
                lines.append("      ), ")

        lines.append("    ], ")
        lines.append("  )")
        lines.append("")
        lines.append("  if (selected != null) {")
        lines.append("    _handleMenuAction(selected);")
        lines.append("  }")
        lines.append("}")

        return lines

    def _generate_flutter_callbacks(self, menu_def: MenuDefinition) -> list[str]:




        """Generate Flutter callback methods."""
        lines = []

        # Main menu action handler
        lines.append("void _handleMenuAction(String action) {")
        lines.append("  switch (action) {")

        # Collect all menu items
        all_items = []
        all_items.extend(menu_def.menu_bar)
        for items in menu_def.context_menus.values():
            all_items.extend(items)

        # Add cases for each item with onClick
        for item in self._flatten_menu_items(all_items):
            if item.on_click:
                lines.append(f'    case "{item.name}":')
                lines.append(f"      {item.on_click}();")
                lines.append("      break;")

        lines.append("    default:")
        lines.append('      debugPrint("Unknown menu action: $action");')
        lines.append("  }")
        lines.append("}")
        lines.append("")

        # Generate individual callback methods
        for item in self._flatten_menu_items(all_items):
            if item.on_click:
                lines.append(f"void {item.on_click}() {{")
                lines.append(f"  // TODO: Implement {item.text} action")
                lines.append("}")
                lines.append("")

        return lines

    def _flatten_menu_items(self, items: list[MenuItem]) -> list[MenuItem]:




        """Flatten menu hierarchy into a single list."""
        result = []
        for item in items:
            result.append(item)
            if item.children:
                result.extend(self._flatten_menu_items(item.children))
        return result

    def generate_python_menu(self, menu_def: MenuDefinition) -> dict[str, list[str]]:




        """Generate Python/Tkinter menu implementation.

        Returns:
            Dictionary with menu creation code
        """
        code = {
            "menu_creation": [],
            "menu_callbacks": [],
        }

        # Generate menu bar
        if menu_def.menu_bar:
            code["menu_creation"] = self._generate_python_menu_bar(menu_def.menu_bar)

        # Generate context menus
        for menu_name, items in menu_def.context_menus.items():
            context_code = self._generate_python_context_menu(menu_name, items)
            code["menu_creation"].extend(["", "# Context menu"])
            code["menu_creation"].extend(context_code)

        # Generate callbacks
        code["menu_callbacks"] = self._generate_python_callbacks(menu_def)

        return code

    def _generate_python_menu_bar(self, items: list[MenuItem]) -> list[str]:




        """Generate Python/Tkinter menu bar."""
        lines = []

        lines.append("# Create menu bar")
        lines.append("menubar = tk.Menu(self)")
        lines.append("self.config(menu=menubar)")
        lines.append("")

        for item in items:
            var_name = f"{item.name}_menu"
            lines.append(f"# {item.text} menu")
            lines.append(f"{var_name} = tk.Menu(menubar, tearoff=0)")

            if item.children:
                for child in item.children:
                    if child.text == "-":
                        lines.append(f"{var_name}.add_separator()")
                    else:
                        lines.append(f"{var_name}.add_command(")
                        lines.append(f'    label="{child.text}",')
                        if child.shortcut:
                            py_shortcut = child.to_dict()["python_shortcut"]
                            lines.append(f'    accelerator="{child.shortcut}",')
                            lines.append(f'    command=self.{child.on_click or "_handle_" + child.name}')
                            lines.append(")")
                            # Bind shortcut
                            lines.append(f'self.bind_all("{py_shortcut}", lambda e: self.{child.on_click or "_handle_" + child.name}())')
                        else:
                            lines.append(f'    command=self.{child.on_click or "_handle_" + child.name}')
                            lines.append(")")

                        if not child.enabled:
                            lines.append(f'{var_name}.entryconfig("{child.text}", state="disabled")')

            lines.append(f'menubar.add_cascade(label="{item.text}", menu={var_name})')
            lines.append("")

        return lines

    def _generate_python_context_menu(self, menu_name: str, items: list[MenuItem]) -> list[str]:




        """Generate Python context menu."""
        lines = []

        var_name = f"self.{menu_name}_menu"

        lines.append(f"{var_name} = tk.Menu(self, tearoff=0)")

        for item in items:
            if item.text == "-":
                lines.append(f"{var_name}.add_separator()")
            else:
                lines.append(f"{var_name}.add_command(")
                lines.append(f'    label="{item.text}",')
                lines.append(f'    command=self.{item.on_click or "_handle_" + item.name}')
                lines.append(")")

                if not item.enabled:
                    lines.append(f'{var_name}.entryconfig("{item.text}", state="disabled")')

        # Bind to right-click
        lines.append("")
        lines.append(f"# Bind context menu to right-click")
        lines.append(f"self.bind('<Button-3>', lambda e: {var_name}.post(e.x_root, e.y_root))")

        return lines

    def _generate_python_callbacks(self, menu_def: MenuDefinition) -> list[str]:




        """Generate Python callback methods."""
        lines = []

        # Collect all menu items
        all_items = []
        all_items.extend(menu_def.menu_bar)
        for items in menu_def.context_menus.values():
            all_items.extend(items)

        # Generate callback methods
        for item in self._flatten_menu_items(all_items):
            callback_name = item.on_click or f"_handle_{item.name}"

            lines.append(f"def {callback_name}(self):")
            lines.append(f'    """Handle {item.text} menu action."""')
            lines.append(f"    # TODO: Implement {item.text} action")
            lines.append("    pass")
            lines.append("")

        return lines
