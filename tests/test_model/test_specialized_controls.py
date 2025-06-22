"""Tests for PowerBuilder specialized UI controls.

This module contains tests for specialized UI controls like ListView and RichText.
"""

from model.ui.ui_elements import (
    DataWindowControl,
    EditMaskControl,
    ListViewControl,
    RichTextControl,
    TreeViewControl,
)


class TestDataWindowControl:
    """Tests for DataWindow control."""

    def test_initialization(self):




        """Test initialization with basic properties."""
        dw_control = DataWindowControl(
            name="dw_customers",
            position=(10, 10),
            size=(500, 300),
            datawindow=None,  # Would typically be a DataWindow object
            retrieve_args=["customer_id"],
        )

        assert dw_control.name == "dw_customers"
        assert dw_control.type == "datawindow"
        assert dw_control.position == (10, 10)
        assert dw_control.size == (500, 300)
        assert dw_control.retrieve_args == ["customer_id"]


class TestEditMaskControl:
    """Tests for EditMask control."""

    def test_initialization(self):




        """Test initialization with basic properties."""
        mask_control = EditMaskControl(
            name="em_phone",
            position=(10, 50),
            size=(150, 30),
            mask="(###) ###-####",
            validation=r"^\(\d{3}\) \d{3}-\d{4}$",
        )

        assert mask_control.name == "em_phone"
        assert mask_control.type == "editmask"
        assert mask_control.position == (10, 50)
        assert mask_control.size == (150, 30)
        assert mask_control.mask == "(###) ###-####"
        assert mask_control.validation == r"^\(\d{3}\) \d{3}-\d{4}$"


class TestListViewControl:
    """Tests for ListView control."""

    def test_initialization(self):




        """Test initialization with basic properties."""
        columns = [
            {"name": "id", "title": "ID", "width": 50, "alignment": "right"},
            {"name": "name", "title": "Name", "width": 200, "alignment": "left"},
        ]

        items = [
            {
                "id": "1",
                "values": {"id": "1001", "name": "John Doe"},
                "selected": False,
            },
            {
                "id": "2",
                "values": {"id": "1002", "name": "Jane Smith"},
                "selected": False,
            },
        ]

        list_view = ListViewControl(
            name="lv_customers",
            position=(10, 10),
            size=(300, 200),
            columns=columns,
            items=items,
            view_mode="report",
        )

        assert list_view.name == "lv_customers"
        assert list_view.type == "listview"
        assert list_view.position == (10, 10)
        assert list_view.size == (300, 200)
        assert list_view.columns == columns
        assert list_view.items == items
        assert list_view.view_mode == "report"
        assert list_view.selected_items == []
        assert list_view.sort_column is None
        assert list_view.sort_order == "ascending"
        assert list_view._next_item_id == 3  # Since there are 2 items already

    def test_add_column(self):




        """Test adding columns."""
        list_view = ListViewControl(
            name="lv_customers",
            position=(10, 10),
            size=(300, 200),
        )

        # Add a column
        result = list_view.add_column("id", "ID", 50, "right")
        assert result is True
        assert len(list_view.columns) == 1
        assert list_view.columns[0] == {
            "name": "id",
            "title": "ID",
            "width": 50,
            "alignment": "right",
        }

        # Add another column
        result = list_view.add_column("name", "Name", 200)
        assert result is True
        assert len(list_view.columns) == 2
        assert list_view.columns[1] == {
            "name": "name",
            "title": "Name",
            "width": 200,
            "alignment": "left",
        }

        # Try to add a duplicate column
        result = list_view.add_column("id", "ID2", 75)
        assert result is False
        assert len(list_view.columns) == 2

    def test_remove_column(self):




        """Test removing columns."""
        list_view = ListViewControl(
            name="lv_customers",
            position=(10, 10),
            size=(300, 200),
            columns=[
                {"name": "id", "title": "ID", "width": 50, "alignment": "right"},
                {"name": "name", "title": "Name", "width": 200, "alignment": "left"},
            ],
        )

        # Add an item with values for both columns
        list_view.add_item({"id": "1001", "name": "John Doe"})

        # Remove a column
        result = list_view.remove_column("id")
        assert result is True
        assert len(list_view.columns) == 1
        assert list_view.columns[0]["name"] == "name"

        # Check that the column data was removed from items
        item = list_view.get_item("1")
        assert "id" not in item["values"]
        assert "name" in item["values"]

        # Try to remove a non-existent column
        result = list_view.remove_column("nonexistent")
        assert result is False
        assert len(list_view.columns) == 1

    def test_add_item(self):




        """Test adding items."""
        list_view = ListViewControl(
            name="lv_customers",
            position=(10, 10),
            size=(300, 200),
            columns=[
                {"name": "id", "title": "ID", "width": 50},
                {"name": "name", "title": "Name", "width": 200},
            ],
        )

        # Add an item without specifying an ID
        item_id = list_view.add_item({"id": "1001", "name": "John Doe"})
        assert item_id == "1"
        assert len(list_view.items) == 1
        assert list_view.items[0]["values"] == {"id": "1001", "name": "John Doe"}
        assert list_view.items[0]["selected"] is False

        # Add an item with a specific ID
        item_id = list_view.add_item({"id": "1002", "name": "Jane Smith"}, "custom_id")
        assert item_id == "custom_id"
        assert len(list_view.items) == 2
        assert list_view.items[1]["id"] == "custom_id"
        assert list_view.items[1]["values"] == {"id": "1002", "name": "Jane Smith"}

        # Verify the item map
        assert "1" in list_view._item_map
        assert "custom_id" in list_view._item_map
        assert list_view._item_map["1"] is list_view.items[0]
        assert list_view._item_map["custom_id"] is list_view.items[1]

    def test_get_item(self):




        """Test getting items."""
        list_view = ListViewControl(
            name="lv_customers",
            position=(10, 10),
            size=(300, 200),
        )

        # Add some items
        id1 = list_view.add_item({"name": "John Doe"})
        id2 = list_view.add_item({"name": "Jane Smith"})

        # Get items by ID
        item1 = list_view.get_item(id1)
        item2 = list_view.get_item(id2)
        nonexistent = list_view.get_item("999")

        assert item1 is not None
        assert item1["values"]["name"] == "John Doe"
        assert item2 is not None
        assert item2["values"]["name"] == "Jane Smith"
        assert nonexistent is None

    def test_update_item(self):




        """Test updating items."""
        list_view = ListViewControl(
            name="lv_customers",
            position=(10, 10),
            size=(300, 200),
        )

        # Add an item
        item_id = list_view.add_item({"name": "John Doe"})

        # Update the item
        result = list_view.update_item(item_id, {"name": "John Smith", "age": "30"})
        assert result is True

        # Check that the item was updated
        item = list_view.get_item(item_id)
        assert item["values"]["name"] == "John Smith"
        assert item["values"]["age"] == "30"

        # Try to update a non-existent item
        result = list_view.update_item("nonexistent", {"name": "Invalid"})
        assert result is False

    def test_delete_item(self):




        """Test deleting items."""
        list_view = ListViewControl(
            name="lv_customers",
            position=(10, 10),
            size=(300, 200),
        )

        # Add some items
        id1 = list_view.add_item({"name": "John Doe"})
        id2 = list_view.add_item({"name": "Jane Smith"})
        list_view.add_item({"name": "Bob Johnson"})

        # Select an item
        list_view.select_item(id2)
        assert list_view.selected_items[0]["values"]["name"] == "Jane Smith"

        # Delete the selected item
        result = list_view.delete_item(id2)
        assert result is True
        assert len(list_view.items) == 2
        assert list_view.get_item(id2) is None
        assert len(list_view.selected_items) == 0

        # Delete another item
        result = list_view.delete_item(id1)
        assert result is True
        assert len(list_view.items) == 1
        assert list_view.get_item(id1) is None

        # Try to delete a non-existent item
        result = list_view.delete_item("nonexistent")
        assert result is False
        assert len(list_view.items) == 1

    def test_clear_items(self):




        """Test clearing all items."""
        list_view = ListViewControl(
            name="lv_customers",
            position=(10, 10),
            size=(300, 200),
        )

        # Add some items
        list_view.add_item({"name": "John Doe"})
        list_view.add_item({"name": "Jane Smith"})
        list_view.add_item({"name": "Bob Johnson"})

        # Select an item
        list_view.select_item("2")

        # Clear all items
        list_view.clear_items()
        assert len(list_view.items) == 0
        assert len(list_view._item_map) == 0
        assert len(list_view.selected_items) == 0

    def test_selection(self):




        """Test item selection."""
        list_view = ListViewControl(
            name="lv_customers",
            position=(10, 10),
            size=(300, 200),
        )

        # Add some items
        id1 = list_view.add_item({"name": "John Doe"})
        id2 = list_view.add_item({"name": "Jane Smith"})
        id3 = list_view.add_item({"name": "Bob Johnson"})

        # Select a single item
        result = list_view.select_item(id1)
        assert result is True
        assert len(list_view.selected_items) == 1
        assert list_view.selected_items[0]["values"]["name"] == "John Doe"
        assert list_view.get_item(id1)["selected"] is True
        assert list_view.get_item(id2)["selected"] is False
        assert list_view.get_item(id3)["selected"] is False

        # Select another item (should replace the current selection)
        result = list_view.select_item(id2)
        assert result is True
        assert len(list_view.selected_items) == 1
        assert list_view.selected_items[0]["values"]["name"] == "Jane Smith"
        assert list_view.get_item(id1)["selected"] is False
        assert list_view.get_item(id2)["selected"] is True
        assert list_view.get_item(id3)["selected"] is False

        # Select an additional item with multi-select
        result = list_view.select_item(id3, multi_select=True)
        assert result is True
        assert len(list_view.selected_items) == 2
        assert list_view.selected_items[0]["values"]["name"] == "Jane Smith"
        assert list_view.selected_items[1]["values"]["name"] == "Bob Johnson"
        assert list_view.get_item(id1)["selected"] is False
        assert list_view.get_item(id2)["selected"] is True
        assert list_view.get_item(id3)["selected"] is True

        # Deselect an item
        result = list_view.deselect_item(id2)
        assert result is True
        assert len(list_view.selected_items) == 1
        assert list_view.selected_items[0]["values"]["name"] == "Bob Johnson"
        assert list_view.get_item(id1)["selected"] is False
        assert list_view.get_item(id2)["selected"] is False
        assert list_view.get_item(id3)["selected"] is True

        # Try to select a non-existent item
        result = list_view.select_item("nonexistent")
        assert result is False
        assert len(list_view.selected_items) == 1

        # Try to deselect a non-existent item
        result = list_view.deselect_item("nonexistent")
        assert result is False
        assert len(list_view.selected_items) == 1

    def test_view_mode(self):




        """Test changing view mode."""
        list_view = ListViewControl(
            name="lv_customers",
            position=(10, 10),
            size=(300, 200),
            view_mode="report",
        )

        # Change to valid view modes
        assert list_view.set_view_mode("list") is True
        assert list_view.view_mode == "list"

        assert list_view.set_view_mode("largeicon") is True
        assert list_view.view_mode == "largeicon"

        assert list_view.set_view_mode("smallicon") is True
        assert list_view.view_mode == "smallicon"

        assert list_view.set_view_mode("report") is True
        assert list_view.view_mode == "report"

        # Try invalid view mode
        assert list_view.set_view_mode("invalid") is False
        assert list_view.view_mode == "report"

    def test_sorting(self):




        """Test item sorting."""
        list_view = ListViewControl(
            name="lv_customers",
            position=(10, 10),
            size=(300, 200),
            columns=[
                {"name": "id", "title": "ID", "width": 50},
                {"name": "name", "title": "Name", "width": 200},
            ],
        )

        # Add items in non-alphabetical order
        list_view.add_item({"id": "1003", "name": "Bob Johnson"})
        list_view.add_item({"id": "1001", "name": "John Doe"})
        list_view.add_item({"id": "1002", "name": "Jane Smith"})

        # Sort by name ascending
        result = list_view.sort("name", "ascending")
        assert result is True
        assert list_view.sort_column == "name"
        assert list_view.sort_order == "ascending"
        assert list_view.items[0]["values"]["name"] == "Bob Johnson"
        assert list_view.items[1]["values"]["name"] == "Jane Smith"
        assert list_view.items[2]["values"]["name"] == "John Doe"

        # Sort by name descending
        result = list_view.sort("name", "descending")
        assert result is True
        assert list_view.sort_column == "name"
        assert list_view.sort_order == "descending"
        assert list_view.items[0]["values"]["name"] == "John Doe"
        assert list_view.items[1]["values"]["name"] == "Jane Smith"
        assert list_view.items[2]["values"]["name"] == "Bob Johnson"

        # Sort by ID ascending
        result = list_view.sort("id", "ascending")
        assert result is True
        assert list_view.sort_column == "id"
        assert list_view.sort_order == "ascending"
        assert list_view.items[0]["values"]["id"] == "1001"
        assert list_view.items[1]["values"]["id"] == "1002"
        assert list_view.items[2]["values"]["id"] == "1003"

        # Try to sort by a non-existent column
        result = list_view.sort("nonexistent")
        assert result is False
        assert list_view.sort_column == "id"
        assert list_view.sort_order == "ascending"

        # Try to sort with an invalid order
        result = list_view.sort("id", "invalid")
        assert result is False
        assert list_view.sort_column == "id"
        assert list_view.sort_order == "ascending"

    def test_find_items(self):




        """Test finding items."""
        list_view = ListViewControl(
            name="lv_customers",
            position=(10, 10),
            size=(300, 200),
            columns=[
                {"name": "id", "title": "ID", "width": 50},
                {"name": "name", "title": "Name", "width": 200},
                {"name": "city", "title": "City", "width": 150},
            ],
        )

        # Add some items
        list_view.add_item({"id": "1001", "name": "John Doe", "city": "New York"})
        list_view.add_item({"id": "1002", "name": "Jane Smith", "city": "Los Angeles"})
        list_view.add_item({"id": "1003", "name": "Bob Johnson", "city": "New York"})
        list_view.add_item({"id": "1004", "name": "Alice Brown", "city": "Chicago"})

        # Find items with exact match
        results = list_view.find_items("city", "New York")
        assert len(results) == 2
        assert results[0]["values"]["name"] == "John Doe"
        assert results[1]["values"]["name"] == "Bob Johnson"

        # Find items with partial match
        results = list_view.find_items("name", "son", partial_match=True)
        assert len(results) == 1
        assert results[0]["values"]["name"] == "Bob Johnson"

        # Case-insensitive search
        results = list_view.find_items("city", "new york")
        assert len(results) == 2

        # No matches
        results = list_view.find_items("city", "Boston")
        assert len(results) == 0

    def test_item_tags(self):




        """Test item tags."""
        list_view = ListViewControl(
            name="lv_customers",
            position=(10, 10),
            size=(300, 200),
        )

        # Add an item
        item_id = list_view.add_item({"name": "John Doe"})

        # Set a tag
        result = list_view.set_item_tag(item_id, "status", "active")
        assert result is True

        # Set another tag
        result = list_view.set_item_tag(item_id, "priority", 1)
        assert result is True

        # Check the tags
        item = list_view.get_item(item_id)
        assert item["tags"]["status"] == "active"
        assert item["tags"]["priority"] == 1

        # Try to set a tag on a non-existent item
        result = list_view.set_item_tag("nonexistent", "status", "inactive")
        assert result is False


class TestRichTextControl:
    """Tests for RichText control."""

    def test_initialization(self):




        """Test initialization with basic properties."""
        rich_text = RichTextControl(
            name="rt_notes",
            position=(10, 10),
            size=(400, 300),
            content="Initial text",
            readonly=False,
            file_formats=["rtf", "txt", "html"],
        )

        assert rich_text.name == "rt_notes"
        assert rich_text.type == "richtext"
        assert rich_text.position == (10, 10)
        assert rich_text.size == (400, 300)
        assert rich_text.content == "Initial text"
        assert rich_text.readonly is False
        assert rich_text.file_formats == ["rtf", "txt", "html"]
        assert rich_text.selection_start == 0
        assert rich_text.selection_length == 0
        assert rich_text.current_font == "Arial"
        assert rich_text.current_font_size == 10
        assert rich_text.current_text_color == "black"
        assert rich_text.current_background_color == "white"
        assert rich_text.current_style == {
            "bold": False,
            "italic": False,
            "underline": False,
            "strikethrough": False,
        }

    def test_text_operations(self):




        """Test basic text operations."""
        rich_text = RichTextControl(
            name="rt_notes",
            position=(10, 10),
            size=(400, 300),
            content="Hello World",
        )

        # Get text
        assert rich_text.get_text() == "Hello World"

        # Set text
        rich_text.set_text("New text content")
        assert rich_text.content == "New text content"
        assert rich_text.selection_start == 0
        assert rich_text.selection_length == 0

        # Append text
        rich_text.append_text(" with more text")
        assert rich_text.content == "New text content with more text"

        # Insert text
        result = rich_text.insert_text(4, " inserted")
        assert result is True
        assert rich_text.content == "New inserted text content with more text"

        # Insert text at invalid position
        result = rich_text.insert_text(-1, "invalid")
        assert result is False
        assert rich_text.content == "New inserted text content with more text"

        result = rich_text.insert_text(1000, "invalid")
        assert result is False
        assert rich_text.content == "New inserted text content with more text"

        # Delete text
        result = rich_text.delete_text(4, 10)  # Delete " inserted"
        assert result is True
        assert rich_text.content == "New text content with more text"

        # Delete text with invalid parameters
        result = rich_text.delete_text(-1, 5)
        assert result is False
        assert rich_text.content == "New text content with more text"

        result = rich_text.delete_text(100, 5)
        assert result is False
        assert rich_text.content == "New text content with more text"

        result = rich_text.delete_text(0, 0)
        assert result is False
        assert rich_text.content == "New text content with more text"

    def test_selection(self):




        """Test text selection operations."""
        rich_text = RichTextControl(
            name="rt_notes",
            position=(10, 10),
            size=(400, 300),
            content="Hello World",
        )

        # Select text
        result = rich_text.select_text(6, 5)  # Select "World"
        assert result is True
        assert rich_text.selection_start == 6
        assert rich_text.selection_length == 5

        # Get selection
        selection = rich_text.get_selection()
        assert selection == (6, 5)

        # Get selected text
        selected_text = rich_text.get_selected_text()
        assert selected_text == "World"

        # Select with invalid parameters
        result = rich_text.select_text(-1, 5)
        assert result is False
        assert rich_text.selection_start == 6
        assert rich_text.selection_length == 5

        result = rich_text.select_text(100, 5)
        assert result is False
        assert rich_text.selection_start == 6
        assert rich_text.selection_length == 5

        result = rich_text.select_text(0, -1)
        assert result is False
        assert rich_text.selection_start == 6
        assert rich_text.selection_length == 5

        # Select beyond end of text
        result = rich_text.select_text(8, 10)
        assert result is True
        assert rich_text.selection_start == 8
        assert rich_text.selection_length == 3  # Limited to end of text

        # No selection
        rich_text.select_text(0, 0)
        assert rich_text.get_selected_text() == ""

    def test_formatting(self):




        """Test text formatting operations."""
        rich_text = RichTextControl(
            name="rt_notes",
            position=(10, 10),
            size=(400, 300),
            content="Formatted text",
        )

        # Set font
        rich_text.set_font("Times New Roman")
        assert rich_text.current_font == "Times New Roman"
        assert rich_text.current_font_size == 10

        # Set font with size
        rich_text.set_font("Courier New", 12)
        assert rich_text.current_font == "Courier New"
        assert rich_text.current_font_size == 12

        # Set text color
        rich_text.set_text_color("blue")
        assert rich_text.current_text_color == "blue"

        # Set background color
        rich_text.set_background_color("#FFFFCC")
        assert rich_text.current_background_color == "#FFFFCC"

        # Set styles
        result = rich_text.set_style("bold", True)
        assert result is True
        assert rich_text.current_style["bold"] is True

        result = rich_text.set_style("italic", True)
        assert result is True
        assert rich_text.current_style["italic"] is True

        result = rich_text.set_style("underline", True)
        assert result is True
        assert rich_text.current_style["underline"] is True

        # Try to set invalid style
        result = rich_text.set_style("nonexistent", True)
        assert result is False
        assert "nonexistent" not in rich_text.current_style

    def test_find_replace(self):




        """Test find and replace operations."""
        rich_text = RichTextControl(
            name="rt_notes",
            position=(10, 10),
            size=(400, 300),
            content="This is a test with multiple occurrences of test words.",
        )

        # Find text
        pos = rich_text.find_text("test")
        assert pos == 10

        # Find with start position
        pos = rich_text.find_text("test", 11)
        assert pos == 34

        # Find with case sensitivity
        rich_text.set_text("Case Test test")
        pos = rich_text.find_text("test", 0, case_sensitive=True)
        assert pos == 10  # Finds "test" but not "Test"

        # Find non-existent text
        pos = rich_text.find_text("nonexistent")
        assert pos == -1

        # Replace single occurrence
        rich_text.set_text("This is a test with other text.")
        count = rich_text.replace_text(
            "test", "demo", 0, case_sensitive=False, all_occurrences=False,
        )
        assert count == 1
        assert rich_text.content == "This is a demo with other text."

        # Replace all occurrences
        rich_text.set_text("test Test test TEST")
        count = rich_text.replace_text(
            "test", "demo", 0, case_sensitive=False, all_occurrences=True,
        )
        assert count == 4
        assert rich_text.content == "demo demo demo demo"

        # Replace with case sensitivity
        rich_text.set_text("test Test test TEST")
        count = rich_text.replace_text(
            "test", "demo", 0, case_sensitive=True, all_occurrences=True,
        )
        assert count == 2
        assert rich_text.content == "demo Test demo TEST"

        # Replace with empty search string
        count = rich_text.replace_text("", "x", 0, all_occurrences=True)
        assert count == 0
        assert rich_text.content == "demo Test demo TEST"

    def test_file_operations(self):




        """Test file operations (placeholders)."""
        rich_text = RichTextControl(
            name="rt_notes",
            position=(10, 10),
            size=(400, 300),
            content="File operation test",
            file_formats=["rtf", "txt", "html"],
        )

        # These are placeholders that don't actually perform file I/O
        assert rich_text.load_from_file("test.rtf") is True
        assert rich_text.save_to_file("test.rtf") is True
        assert rich_text.save_to_file("test.doc", "rtf") is True


# Common test functionality for controls
def test_control_inheritance():


    """Test that specialized controls inherit from Control base class."""
    controls = [
        DataWindowControl("dw_test", (0, 0), (100, 100), None),
        EditMaskControl("em_test", (0, 0), (100, 100), "###-##-####"),
        ListViewControl("lv_test", (0, 0), (100, 100)),
        RichTextControl("rt_test", (0, 0), (100, 100)),
        TreeViewControl("tv_test", (0, 0), (100, 100)),
    ]

    for control in controls:
        assert hasattr(control, "name")
        assert hasattr(control, "type")
        assert hasattr(control, "position")
        assert hasattr(control, "size")
        assert hasattr(control, "properties")
