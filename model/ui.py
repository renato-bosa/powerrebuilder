"""UI elements for PowerBuilder applications.

This module contains classes for representing PowerBuilder UI components.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from .utils.base import PBNode

if TYPE_CHECKING:
    from .ast.ast_nodes import Event
    from .pb_datawindow.datawindow import PBDataWindow as DataWindow


# ─── Base UI Elements ────────────────────────────────────────────────────
@dataclass
class UIProperties:
    """UI element properties."""

    properties: dict[str, str] = field(default_factory=dict)


@dataclass
class UIElement(PBNode):
    """Base class for UI elements."""

    name: str
    properties: dict[str, str] = field(default_factory=dict)


# ─── Window Elements ────────────────────────────────────────────────────
@dataclass
class Window(PBNode):
    """PowerBuilder window."""

    name: str
    title: str
    properties: dict[str, str] = field(default_factory=dict)
    controls: list[Control] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)


@dataclass
class Control(PBNode):
    """Base class for window controls."""

    name: str
    type: str  # button, edit, text, etc.
    position: tuple[int, int]
    size: tuple[int, int]
    properties: dict[str, str] = field(default_factory=dict)


# ─── Menu Elements ──────────────────────────────────────────────────────
@dataclass
class Menu(PBNode):
    """PowerBuilder menu."""

    name: str
    properties: dict[str, str] = field(default_factory=dict)
    items: list[MenuItem] = field(default_factory=list)


@dataclass
class MenuItem(PBNode):
    """Menu item."""

    name: str
    text: str
    properties: dict[str, str] = field(default_factory=dict)
    action: str | None = None
    submenu: Menu | None = None
    is_separator: bool = False


# ─── User Objects ──────────────────────────────────────────────────────
@dataclass
class UserObject(PBNode):
    """PowerBuilder user object."""

    name: str
    type: str
    properties: dict[str, str] = field(default_factory=dict)
    controls: list[Control] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)


# ─── Specialized Controls ─────────────────────────────────────────────────
class DataWindowControl(Control):
    """DataWindow control."""

    def __init__(
        self,
        name: str,
        position: tuple[int, int],
        size: tuple[int, int],
        datawindow: DataWindow,
        properties: dict[str, str] | None = None,
        retrieve_args: list[str] | None = None,
    ) -> None:
        super().__init__(
            name=name,
            type="datawindow",
            position=position,
            size=size,
            properties=properties or {},
        )
        self.datawindow = datawindow
        self.retrieve_args = retrieve_args or []


@dataclass
class TreeViewItem:
    """Item within a TreeView control."""

    label: str
    data: any | None = None
    children: bool = False
    expanded: bool = False
    selected: bool = False
    picture_index: int | None = None
    selected_picture_index: int | None = None
    state_picture_index: int | None = None
    overlay_picture_index: int | None = None
    item_level: int = 1
    handle: int | None = None
    parent_handle: int | None = None
    key: str | None = None
    tags: dict[str, any] = field(default_factory=dict)


class TreeViewControl(Control):
    """TreeView control for displaying hierarchical data.

    The TreeView control displays data in a hierarchical tree structure,
    allowing for parent-child relationships with collapsible/expandable nodes.
    """

    def __init__(
        self,
        name: str,
        position: tuple[int, int],
        size: tuple[int, int],
        properties: dict[str, str] | None = None,
        items: list[TreeViewItem] | None = None,
        picture_list: list[str] | None = None,
        has_lines: bool = True,
        has_buttons: bool = True,
        has_root_lines: bool = True,
        sort_items: bool = False,
    ) -> None:
        """Initialize a TreeView control.

        Args:
            name: Control name
            position: (x, y) position
            size: (width, height) size
            properties: Additional properties
            items: List of tree items
            picture_list: List of picture paths/names for node icons
            has_lines: Whether to show lines connecting nodes
            has_buttons: Whether to show +/- buttons for expandable nodes
            has_root_lines: Whether to show lines from root node
            sort_items: Whether items should be sorted automatically
        """
        super().__init__(
            name=name,
            type="treeview",
            position=position,
            size=size,
            properties=properties or {},
        )
        self.items = items or []
        self.picture_list = picture_list or []
        self.has_lines = has_lines
        self.has_buttons = has_buttons
        self.has_root_lines = has_root_lines
        self.sort_items = sort_items
        self.selected_item = None
        self.next_handle = 1  # For generating unique handles
        self._item_map = {}  # Maps handles to items for quick lookup

        # Initialize the item map and handle assignments for existing items
        for item in self.items:
            if item.handle is None:
                item.handle = self.next_handle
                self.next_handle += 1
            self._item_map[item.handle] = item

    def add_item(
        self,
        parent_handle: int | None,
        label: str,
        data: any | None = None,
    ) -> int:
        """Add an item to the TreeView.

        Args:
            parent_handle: Handle of parent item (None for root level)
            label: Text label for the item
            data: Optional data associated with the item

        Returns:
            Handle of the newly created item
        """
        handle = self.next_handle
        self.next_handle += 1

        item = TreeViewItem(
            label=label,
            data=data,
            handle=handle,
            parent_handle=parent_handle,
            item_level=1
            if parent_handle is None
            else self._get_parent_level(parent_handle) + 1,
        )

        self.items.append(item)
        self._item_map[handle] = item

        # Update parent's children flag
        if parent_handle is not None and parent_handle in self._item_map:
            self._item_map[parent_handle].children = True

        # Sort items if enabled
        if self.sort_items:
            self._sort_children(parent_handle)

        return handle

    def add_item_with_key(
        self,
        parent_handle: int | None,
        label: str,
        key: str,
        data: any | None = None,
    ) -> int:
        """Add an item with a custom key to the TreeView.

        Args:
            parent_handle: Handle of parent item (None for root level)
            label: Text label for the item
            key: Unique string key for the item (for easier lookups)
            data: Optional data associated with the item

        Returns:
            Handle of the newly created item
        """
        handle = self.add_item(parent_handle, label, data)
        self._item_map[handle].key = key
        return handle

    def find_item_by_key(self, key: str) -> TreeViewItem | None:
        """Find an item by its key.

        Args:
            key: The key to search for

        Returns:
            The TreeViewItem if found, None otherwise
        """
        for item in self.items:
            if item.key == key:
                return item
        return None

    def find_items_by_label(self, label: str) -> list[TreeViewItem]:
        """Find items by their label.

        Args:
            label: The label to search for

        Returns:
            List of TreeViewItem objects with matching labels
        """
        return [item for item in self.items if item.label == label]

    def get_item(self, handle: int) -> TreeViewItem | None:
        """Get an item by handle.

        Args:
            handle: The item handle

        Returns:
            The TreeViewItem if found, None otherwise
        """
        return self._item_map.get(handle)

    def get_children(self, parent_handle: int | None = None) -> list[TreeViewItem]:
        """Get child items of a parent.

        Args:
            parent_handle: Handle of parent item (None for root level)

        Returns:
            List of child items
        """
        return [item for item in self.items if item.parent_handle == parent_handle]

    def get_descendants(self, parent_handle: int) -> list[TreeViewItem]:
        """Get all descendants of a parent item (children, grandchildren, etc.).

        Args:
            parent_handle: Handle of parent item

        Returns:
            List of all descendant items
        """
        result = []

        # First get immediate children
        children = self.get_children(parent_handle)
        result.extend(children)

        # Then recursively get their descendants
        for child in children:
            result.extend(self.get_descendants(child.handle))

        return result

    def delete_item(self, handle: int) -> bool:
        """Delete an item and all its children.

        Args:
            handle: Handle of the item to delete

        Returns:
            True if successful, False otherwise
        """
        if handle not in self._item_map:
            return False

        # First, delete all children recursively
        children = self.get_children(handle)
        for child in children:
            self.delete_item(child.handle)

        # Remove the item itself
        item = self._item_map[handle]
        self.items.remove(item)
        del self._item_map[handle]

        # If this was the selected item, clear the selection
        if self.selected_item is item:
            self.selected_item = None

        return True

    def select_item(self, handle: int) -> bool:
        """Select an item.

        Args:
            handle: Handle of the item to select

        Returns:
            True if successful, False otherwise
        """
        if handle not in self._item_map:
            return False

        # Deselect the currently selected item
        if self.selected_item is not None:
            self.selected_item.selected = False

        # Select the new item
        item = self._item_map[handle]
        item.selected = True
        self.selected_item = item

        return True

    def get_selected_item(self) -> TreeViewItem | None:
        """Get the currently selected item.

        Returns:
            The selected TreeViewItem, or None if nothing is selected
        """
        return self.selected_item

    def expand_item(self, handle: int) -> bool:
        """Expand an item to show its children.

        Args:
            handle: Handle of the item to expand

        Returns:
            True if successful, False otherwise
        """
        if handle not in self._item_map:
            return False

        item = self._item_map[handle]
        item.expanded = True

        return True

    def expand_all(self) -> None:
        """Expand all items in the tree."""
        for item in self.items:
            item.expanded = True

    def collapse_item(self, handle: int) -> bool:
        """Collapse an item to hide its children.

        Args:
            handle: Handle of the item to collapse

        Returns:
            True if successful, False otherwise
        """
        if handle not in self._item_map:
            return False

        item = self._item_map[handle]
        item.expanded = False

        return True

    def collapse_all(self) -> None:
        """Collapse all items in the tree."""
        for item in self.items:
            item.expanded = False

    def move_item(self, handle: int, new_parent_handle: int | None) -> bool:
        """Move an item (and its descendants) to a new parent.

        Args:
            handle: Handle of the item to move
            new_parent_handle: Handle of the new parent (None for root level)

        Returns:
            True if successful, False otherwise
        """
        if handle not in self._item_map:
            return False

        # Can't move to a descendant of itself
        if new_parent_handle is not None:
            if new_parent_handle not in self._item_map:
                return False

            # Check if new_parent_handle is a descendant of handle
            current = new_parent_handle
            while current is not None:
                if current == handle:
                    return False  # Would create a cycle
                parent = self._item_map[current].parent_handle
                current = parent

        # Update the parent of the item
        item = self._item_map[handle]
        old_parent = item.parent_handle
        item.parent_handle = new_parent_handle

        # Update the level of the item and all its descendants
        new_level = (
            1
            if new_parent_handle is None
            else self._get_parent_level(new_parent_handle) + 1
        )
        level_diff = new_level - item.item_level

        item.item_level = new_level
        for descendant in self.get_descendants(handle):
            descendant.item_level += level_diff

        # Update the children flag of the old and new parents
        if old_parent is not None and old_parent in self._item_map:
            old_children = self.get_children(old_parent)
            if not old_children:
                self._item_map[old_parent].children = False

        if new_parent_handle is not None:
            self._item_map[new_parent_handle].children = True

        # Sort items if enabled
        if self.sort_items:
            self._sort_children(new_parent_handle)

        return True

    def set_item_picture(
        self,
        handle: int,
        picture_index: int,
        type: str = "normal",
    ) -> bool:
        """Set the picture for an item.

        Args:
            handle: Handle of the item
            picture_index: Index in the picture list
            type: Type of picture ('normal', 'selected', 'state', 'overlay')

        Returns:
            True if successful, False otherwise
        """
        if (
            handle not in self._item_map
            or picture_index < 0
            or picture_index >= len(self.picture_list)
        ):
            return False

        item = self._item_map[handle]
        if type == "normal":
            item.picture_index = picture_index
        elif type == "selected":
            item.selected_picture_index = picture_index
        elif type == "state":
            item.state_picture_index = picture_index
        elif type == "overlay":
            item.overlay_picture_index = picture_index
        else:
            return False

        return True

    def set_item_tag(self, handle: int, tag_name: str, tag_value: Any) -> bool:
        """Set a tag (custom property) for an item.

        Args:
            handle: Handle of the item
            tag_name: Name of the tag
            tag_value: Value of the tag

        Returns:
            True if successful, False otherwise
        """
        if handle not in self._item_map:
            return False

        self._item_map[handle].tags[tag_name] = tag_value
        return True

    def get_item_tag(self, handle: int, tag_name: str) -> Any | None:
        """Get a tag (custom property) from an item.

        Args:
            handle: Handle of the item
            tag_name: Name of the tag

        Returns:
            The tag value, or None if not found
        """
        if handle not in self._item_map:
            return None

        return self._item_map[handle].tags.get(tag_name)

    def _get_parent_level(self, parent_handle: int) -> int:
        """Get the level of a parent item.

        Args:
            parent_handle: Handle of the parent item

        Returns:
            Level of the parent item
        """
        if parent_handle not in self._item_map:
            return 0

        return self._item_map[parent_handle].item_level

    def _sort_children(self, parent_handle: int | None) -> None:
        """Sort the children of a parent item by label.

        Args:
            parent_handle: Handle of the parent item (None for root level)
        """
        # Get all children of the parent
        children = self.get_children(parent_handle)

        # Sort them by label
        children.sort(key=lambda item: item.label.lower())

        # Not changing the items list order since it's more complex
        # This is normally handled by the UI framework for display


class EditMaskControl(Control):
    """Edit mask control."""

    def __init__(
        self,
        name: str,
        position: tuple[int, int],
        size: tuple[int, int],
        mask: str,
        properties: dict[str, str] | None = None,
        validation: str | None = None,
    ) -> None:
        super().__init__(
            name=name,
            type="editmask",
            position=position,
            size=size,
            properties=properties or {},
        )
        self.mask = mask
        self.validation = validation


class ListViewControl(Control):
    """ListView control for displaying data in columns and rows.

    The ListView control displays data in a tabular format with columns
    and rows, allowing for different view modes such as report, list,
    large icons, and small icons.
    """

    def __init__(
        self,
        name: str,
        position: tuple[int, int],
        size: tuple[int, int],
        columns: list[dict[str, str]] | None = None,
        items: list[dict[str, list[str]]] | None = None,
        properties: dict[str, str] | None = None,
        view_mode: str = "report",
    ) -> None:
        """Initialize a ListView control.

        Args:
            name: Control name
            position: (x, y) position
            size: (width, height) size
            columns: List of column definitions with name, title, width
            items: List of items, each with an ID and values for each column
            properties: Additional properties
            view_mode: Display mode ("report", "list", "largeicon", "smallicon")
        """
        super().__init__(
            name=name,
            type="listview",
            position=position,
            size=size,
            properties=properties or {},
        )
        self.columns = columns or []
        self.items = items or []
        self.view_mode = view_mode
        self.selected_items = []
        self.sort_column = None
        self.sort_order = "ascending"
        self._next_item_id = 1
        self._item_map = {}  # Maps item IDs to items

        # Initialize item map
        for item in self.items:
            if "id" not in item:
                item["id"] = str(self._next_item_id)
                self._next_item_id += 1
            self._item_map[item["id"]] = item

    def add_column(
        self,
        name: str,
        title: str,
        width: int = 100,
        alignment: str = "left",
    ) -> bool:
        """Add a column to the ListView.

        Args:
            name: Column identifier
            title: Display title for the column
            width: Column width in pixels
            alignment: Text alignment ("left", "center", "right")

        Returns:
            True if successful
        """
        # Check if column already exists
        for col in self.columns:
            if col.get("name") == name:
                return False

        self.columns.append(
            {"name": name, "title": title, "width": width, "alignment": alignment},
        )
        return True

    def remove_column(self, name: str) -> bool:
        """Remove a column from the ListView.

        Args:
            name: Column identifier

        Returns:
            True if successful, False if column not found
        """
        for i, col in enumerate(self.columns):
            if col.get("name") == name:
                self.columns.pop(i)

                # Remove this column's data from all items
                for item in self.items:
                    if "values" in item and name in item["values"]:
                        del item["values"][name]

                return True
        return False

    def add_item(self, values: dict[str, str], item_id: str | None = None) -> str:
        """Add an item to the ListView.

        Args:
            values: Dictionary of column name to value
            item_id: Optional custom ID for the item

        Returns:
            ID of the added item
        """
        # Generate ID if not provided
        if item_id is None:
            item_id = str(self._next_item_id)
            self._next_item_id += 1

        # Create the item
        item = {
            "id": item_id,
            "values": values,
            "selected": False,
            "icon_index": None,
            "tags": {},
        }

        self.items.append(item)
        self._item_map[item_id] = item

        return item_id

    def get_item(self, item_id: str) -> dict | None:
        """Get an item by its ID.

        Args:
            item_id: The item ID

        Returns:
            The item dictionary if found, None otherwise
        """
        return self._item_map.get(item_id)

    def update_item(self, item_id: str, values: dict[str, str]) -> bool:
        """Update an item's values.

        Args:
            item_id: The item ID
            values: Dictionary of column name to new value

        Returns:
            True if successful, False if item not found
        """
        if item_id not in self._item_map:
            return False

        item = self._item_map[item_id]

        # Update values
        if "values" not in item:
            item["values"] = {}

        for col_name, value in values.items():
            item["values"][col_name] = value

        return True

    def delete_item(self, item_id: str) -> bool:
        """Delete an item from the ListView.

        Args:
            item_id: The item ID

        Returns:
            True if successful, False if item not found
        """
        if item_id not in self._item_map:
            return False

        item = self._item_map[item_id]
        self.items.remove(item)
        del self._item_map[item_id]

        # Remove from selection if selected
        if item in self.selected_items:
            self.selected_items.remove(item)

        return True

    def clear_items(self) -> None:
        """Remove all items from the ListView."""
        self.items.clear()
        self._item_map.clear()
        self.selected_items.clear()

    def select_item(self, item_id: str, multi_select: bool = False) -> bool:
        """Select an item in the ListView.

        Args:
            item_id: The item ID
            multi_select: Whether to add to existing selection or replace it

        Returns:
            True if successful, False if item not found
        """
        if item_id not in self._item_map:
            return False

        item = self._item_map[item_id]

        # Clear existing selection if not multi-select
        if not multi_select:
            for selected_item in self.selected_items:
                selected_item["selected"] = False
            self.selected_items.clear()

        # Select this item
        item["selected"] = True
        if item not in self.selected_items:
            self.selected_items.append(item)

        return True

    def deselect_item(self, item_id: str) -> bool:
        """Deselect an item in the ListView.

        Args:
            item_id: The item ID

        Returns:
            True if successful, False if item not found
        """
        if item_id not in self._item_map:
            return False

        item = self._item_map[item_id]

        if item in self.selected_items:
            item["selected"] = False
            self.selected_items.remove(item)

        return True

    def get_selected_items(self) -> list[dict]:
        """Get all selected items.

        Returns:
            List of selected item dictionaries
        """
        return self.selected_items.copy()

    def set_view_mode(self, mode: str) -> bool:
        """Set the view mode of the ListView.

        Args:
            mode: One of "report", "list", "largeicon", "smallicon"

        Returns:
            True if successful, False if invalid mode
        """
        valid_modes = ["report", "list", "largeicon", "smallicon"]
        if mode not in valid_modes:
            return False

        self.view_mode = mode
        return True

    def sort(self, column_name: str, order: str = "ascending") -> bool:
        """Sort the items in the ListView by a column.

        Args:
            column_name: Name of the column to sort by
            order: Sort order ("ascending" or "descending")

        Returns:
            True if successful, False if invalid column or order
        """
        # Validate inputs
        if order not in {"ascending", "descending"}:
            return False

        # Check if column exists
        col_exists = False
        for col in self.columns:
            if col.get("name") == column_name:
                col_exists = True
                break

        if not col_exists:
            return False

        # Set sort properties
        self.sort_column = column_name
        self.sort_order = order

        # Sort the items
        def get_sort_key(item):
            if "values" in item and column_name in item["values"]:
                return str(item["values"][column_name]).lower()
            return ""

        self.items.sort(key=get_sort_key, reverse=(order == "descending"))

        return True

    def find_items(
        self,
        column_name: str,
        value: str,
        partial_match: bool = False,
    ) -> list[dict]:
        """Find items with a specific value in a column.

        Args:
            column_name: The column to search in
            value: The value to search for
            partial_match: Whether to do partial string matching

        Returns:
            List of matching items
        """
        results = []

        for item in self.items:
            if "values" in item and column_name in item["values"]:
                item_value = str(item["values"][column_name])

                if partial_match:
                    if value.lower() in item_value.lower():
                        results.append(item)
                elif item_value.lower() == value.lower():
                    results.append(item)

        return results

    def set_item_icon(self, item_id: str, icon_index: int) -> bool:
        """Set the icon for an item.

        Args:
            item_id: The item ID
            icon_index: Index in the icon list

        Returns:
            True if successful, False if item not found
        """
        if item_id not in self._item_map:
            return False

        self._item_map[item_id]["icon_index"] = icon_index
        return True

    def set_item_tag(self, item_id: str, tag_name: str, tag_value: Any) -> bool:
        """Set a tag (custom property) for an item.

        Args:
            item_id: The item ID
            tag_name: Name of the tag
            tag_value: Value of the tag

        Returns:
            True if successful, False if item not found
        """
        if item_id not in self._item_map:
            return False

        if "tags" not in self._item_map[item_id]:
            self._item_map[item_id]["tags"] = {}

        self._item_map[item_id]["tags"][tag_name] = tag_value
        return True


class RichTextControl(Control):
    """RichText control for displaying formatted text.

    The RichText control displays and allows editing of formatted text
    with various fonts, styles, colors, and embedded objects such as
    images and tables.
    """

    def __init__(
        self,
        name: str,
        position: tuple[int, int],
        size: tuple[int, int],
        content: str = "",
        properties: dict[str, str] | None = None,
        readonly: bool = False,
        file_formats: list[str] | None = None,
    ) -> None:
        """Initialize a RichText control.

        Args:
            name: Control name
            position: (x, y) position
            size: (width, height) size
            content: Initial text content
            properties: Additional properties
            readonly: Whether the text can be edited
            file_formats: List of supported file formats (e.g., "rtf", "txt", "html")
        """
        super().__init__(
            name=name,
            type="richtext",
            position=position,
            size=size,
            properties=properties or {},
        )
        self.content = content
        self.readonly = readonly
        self.file_formats = file_formats or ["rtf", "txt"]
        self.selection_start = 0
        self.selection_length = 0
        self.current_font = "Arial"
        self.current_font_size = 10
        self.current_text_color = "black"
        self.current_background_color = "white"
        self.current_style = {
            "bold": False,
            "italic": False,
            "underline": False,
            "strikethrough": False,
        }

    def set_text(self, text: str) -> None:
        """Set the plain text content of the control.

        Args:
            text: The new text content
        """
        self.content = text
        # Reset selection
        self.selection_start = 0
        self.selection_length = 0

    def get_text(self) -> str:
        """Get the plain text content of the control.

        Returns:
            The text content
        """
        return self.content

    def append_text(self, text: str) -> None:
        """Append text to the end of the current content.

        Args:
            text: The text to append
        """
        self.content += text

    def insert_text(self, position: int, text: str) -> bool:
        """Insert text at a specific position.

        Args:
            position: Character position to insert at
            text: The text to insert

        Returns:
            True if successful, False if position is invalid
        """
        if position < 0 or position > len(self.content):
            return False

        self.content = self.content[:position] + text + self.content[position:]
        return True

    def delete_text(self, start: int, length: int) -> bool:
        """Delete text from a specific position.

        Args:
            start: Start position
            length: Number of characters to delete

        Returns:
            True if successful, False if positions are invalid
        """
        if start < 0 or start >= len(self.content) or length <= 0:
            return False

        end = min(start + length, len(self.content))
        self.content = self.content[:start] + self.content[end:]
        return True

    def select_text(self, start: int, length: int) -> bool:
        """Select a range of text.

        Args:
            start: Start position
            length: Number of characters to select

        Returns:
            True if successful, False if positions are invalid
        """
        if start < 0 or start >= len(self.content) or length < 0:
            return False

        self.selection_start = start
        self.selection_length = min(length, len(self.content) - start)
        return True

    def get_selection(self) -> tuple[int, int]:
        """Get the current text selection.

        Returns:
            Tuple of (selection_start, selection_length)
        """
        return (self.selection_start, self.selection_length)

    def get_selected_text(self) -> str:
        """Get the currently selected text.

        Returns:
            The selected text, or empty string if no selection
        """
        if self.selection_length <= 0:
            return ""

        end = min(self.selection_start + self.selection_length, len(self.content))
        return self.content[self.selection_start : end]

    def set_font(self, font_name: str, size: int | None = None) -> None:
        """Set the current font.

        Args:
            font_name: Name of the font
            size: Font size in points (optional)
        """
        self.current_font = font_name
        if size is not None:
            self.current_font_size = size

    def set_text_color(self, color: str) -> None:
        """Set the current text color.

        Args:
            color: Text color (name or hex code)
        """
        self.current_text_color = color

    def set_background_color(self, color: str) -> None:
        """Set the current background color.

        Args:
            color: Background color (name or hex code)
        """
        self.current_background_color = color

    def set_style(self, style: str, value: bool) -> bool:
        """Set a text style.

        Args:
            style: Style name ("bold", "italic", "underline", "strikethrough")
            value: Whether to enable or disable the style

        Returns:
            True if successful, False if style is invalid
        """
        if style not in self.current_style:
            return False

        self.current_style[style] = value
        return True

    def load_from_file(self, file_path: str) -> bool:
        """Load content from a file.

        Args:
            file_path: Path to the file

        Returns:
            True if successful, False if file not found or format not supported
        """
        # In a real implementation, this would actually read the file
        # This is a placeholder for the interface
        return True

    def save_to_file(self, file_path: str, file_format: str | None = None) -> bool:
        """Save content to a file.

        Args:
            file_path: Path to save to
            file_format: Format to use (if None, inferred from file_path)

        Returns:
            True if successful, False if format not supported
        """
        # In a real implementation, this would actually write to the file
        # This is a placeholder for the interface
        return True

    def find_text(
        self,
        search_text: str,
        start: int = 0,
        case_sensitive: bool = False,
    ) -> int:
        """Find text in the content.

        Args:
            search_text: Text to search for
            start: Position to start searching from
            case_sensitive: Whether to match case

        Returns:
            Position of found text, or -1 if not found
        """
        if not case_sensitive:
            content = self.content.lower()
            search_text = search_text.lower()
        else:
            content = self.content

        return content.find(search_text, start)

    def replace_text(
        self,
        search_text: str,
        replace_text: str,
        start: int = 0,
        case_sensitive: bool = False,
        all_occurrences: bool = False,
    ) -> int:
        """Replace text in the content.

        Args:
            search_text: Text to search for
            replace_text: Text to replace with
            start: Position to start searching from
            case_sensitive: Whether to match case
            all_occurrences: Whether to replace all occurrences

        Returns:
            Number of replacements made
        """
        if not search_text:
            return 0

        count = 0

        if all_occurrences:
            if not case_sensitive:
                # Case-insensitive replace all
                new_content = ""
                current_pos = 0

                while current_pos < len(self.content):
                    # Find next occurrence
                    search_lower = self.content.lower()
                    next_pos = search_lower.find(search_text.lower(), current_pos)

                    if next_pos == -1:
                        # No more occurrences, add rest of content
                        new_content += self.content[current_pos:]
                        break

                    # Add text up to match
                    new_content += self.content[current_pos:next_pos]
                    # Add replacement
                    new_content += replace_text

                    # Move past this occurrence
                    current_pos = next_pos + len(search_text)
                    count += 1

                self.content = new_content
            else:
                # Case-sensitive replace all (simpler)
                old_content = self.content
                self.content = self.content.replace(search_text, replace_text)

                # Count replacements
                count = (len(old_content) - len(self.content)) // (
                    len(search_text) - len(replace_text)
                )
                if len(search_text) == len(replace_text):
                    # If same length, count differently
                    count = old_content.count(search_text)
        else:
            # Replace first occurrence only
            pos = self.find_text(search_text, start, case_sensitive)
            if pos >= 0:
                self.content = (
                    self.content[:pos]
                    + replace_text
                    + self.content[pos + len(search_text) :]
                )
                count = 1

        return count
