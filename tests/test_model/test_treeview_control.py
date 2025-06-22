"""Tests for PowerBuilder TreeView UI control.

This module contains tests for the TreeView control functionality.
"""

from model.ui.ui_elements import TreeViewControl


class TestTreeViewControl:
    """Tests for TreeView control."""

    def test_basic_properties(self):




        """Test basic TreeView properties."""
        # Create a basic TreeView control
        treeview = TreeViewControl(
            name="tv_hierarchy",
            position=(10, 10),
            size=(300, 200),
            has_lines=True,
            has_buttons=True,
            has_root_lines=True,
            sort_items=False,
        )

        # Check basic properties
        assert treeview.name == "tv_hierarchy"
        assert treeview.type == "treeview"
        assert treeview.position == (10, 10)
        assert treeview.size == (300, 200)
        assert treeview.has_lines is True
        assert treeview.has_buttons is True
        assert treeview.has_root_lines is True
        assert treeview.sort_items is False
        assert len(treeview.items) == 0
        assert treeview.selected_item is None
        assert treeview.next_handle == 1

    def test_add_item(self):




        """Test adding items to the TreeView."""
        treeview = TreeViewControl(
            name="tv_hierarchy",
            position=(10, 10),
            size=(300, 200),
        )

        # Add root level items
        handle1 = treeview.add_item(None, "Root Item 1", "data1")
        handle2 = treeview.add_item(None, "Root Item 2", "data2")

        # Check items were added correctly
        assert len(treeview.items) == 2
        assert treeview.items[0].label == "Root Item 1"
        assert treeview.items[0].data == "data1"
        assert treeview.items[0].handle == handle1
        assert treeview.items[0].item_level == 1
        assert treeview.items[0].parent_handle is None

        assert treeview.items[1].label == "Root Item 2"
        assert treeview.items[1].data == "data2"
        assert treeview.items[1].handle == handle2
        assert treeview.items[1].item_level == 1
        assert treeview.items[1].parent_handle is None

        # Add child items
        handle3 = treeview.add_item(handle1, "Child Item 1.1", "data3")
        handle4 = treeview.add_item(handle1, "Child Item 1.2", "data4")
        handle5 = treeview.add_item(handle3, "Child Item 1.1.1", "data5")

        # Check child items were added correctly
        assert len(treeview.items) == 5
        assert treeview.items[2].label == "Child Item 1.1"
        assert treeview.items[2].data == "data3"
        assert treeview.items[2].handle == handle3
        assert treeview.items[2].item_level == 2
        assert treeview.items[2].parent_handle == handle1

        assert treeview.items[3].label == "Child Item 1.2"
        assert treeview.items[3].data == "data4"
        assert treeview.items[3].handle == handle4
        assert treeview.items[3].item_level == 2
        assert treeview.items[3].parent_handle == handle1

        assert treeview.items[4].label == "Child Item 1.1.1"
        assert treeview.items[4].data == "data5"
        assert treeview.items[4].handle == handle5
        assert treeview.items[4].item_level == 3
        assert treeview.items[4].parent_handle == handle3

        # Check parent's children flag was updated
        assert treeview.get_item(handle1).children is True
        assert treeview.get_item(handle2).children is False
        assert treeview.get_item(handle3).children is True
        assert treeview.get_item(handle4).children is False

    def test_get_item(self):




        """Test getting items by handle."""
        treeview = TreeViewControl(
            name="tv_hierarchy",
            position=(10, 10),
            size=(300, 200),
        )

        # Add items
        handle1 = treeview.add_item(None, "Root Item 1", "data1")
        handle2 = treeview.add_item(None, "Root Item 2", "data2")
        handle3 = treeview.add_item(handle1, "Child Item 1.1", "data3")

        # Get items by handle
        item1 = treeview.get_item(handle1)
        item2 = treeview.get_item(handle2)
        item3 = treeview.get_item(handle3)
        non_existent = treeview.get_item(999)  # Non-existent handle

        # Check results
        assert item1.label == "Root Item 1"
        assert item2.label == "Root Item 2"
        assert item3.label == "Child Item 1.1"
        assert non_existent is None

    def test_get_children(self):




        """Test getting child items."""
        treeview = TreeViewControl(
            name="tv_hierarchy",
            position=(10, 10),
            size=(300, 200),
        )

        # Add root and child items
        handle1 = treeview.add_item(None, "Root Item 1", "data1")
        handle2 = treeview.add_item(None, "Root Item 2", "data2")
        handle3 = treeview.add_item(handle1, "Child Item 1.1", "data3")
        treeview.add_item(handle1, "Child Item 1.2", "data4")
        treeview.add_item(handle2, "Child Item 2.1", "data5")

        # Get children of root level (parent_handle=None)
        root_children = treeview.get_children(None)
        assert len(root_children) == 2
        assert root_children[0].label == "Root Item 1"
        assert root_children[1].label == "Root Item 2"

        # Get children of Root Item 1
        root1_children = treeview.get_children(handle1)
        assert len(root1_children) == 2
        assert root1_children[0].label == "Child Item 1.1"
        assert root1_children[1].label == "Child Item 1.2"

        # Get children of Root Item 2
        root2_children = treeview.get_children(handle2)
        assert len(root2_children) == 1
        assert root2_children[0].label == "Child Item 2.1"

        # Get children of a leaf node (no children)
        leaf_children = treeview.get_children(handle3)
        assert len(leaf_children) == 0

    def test_delete_item(self):




        """Test deleting items and their children."""
        treeview = TreeViewControl(
            name="tv_hierarchy",
            position=(10, 10),
            size=(300, 200),
        )

        # Add root and child items
        handle1 = treeview.add_item(None, "Root Item 1", "data1")
        treeview.add_item(None, "Root Item 2", "data2")
        handle3 = treeview.add_item(handle1, "Child Item 1.1", "data3")
        handle4 = treeview.add_item(handle1, "Child Item 1.2", "data4")
        handle5 = treeview.add_item(handle3, "Child Item 1.1.1", "data5")

        # Delete a leaf item
        assert treeview.delete_item(handle4) is True
        assert len(treeview.items) == 4
        assert treeview.get_item(handle4) is None

        # Children of Root Item 1 should now only have one item
        root1_children = treeview.get_children(handle1)
        assert len(root1_children) == 1
        assert root1_children[0].label == "Child Item 1.1"

        # Delete an item with children - should delete all children recursively
        assert treeview.delete_item(handle1) is True
        assert len(treeview.items) == 1  # Only Root Item 2 remains
        assert treeview.get_item(handle1) is None
        assert treeview.get_item(handle3) is None
        assert treeview.get_item(handle5) is None

        # Try to delete a non-existent item
        assert treeview.delete_item(999) is False

    def test_select_item(self):




        """Test selecting items."""
        treeview = TreeViewControl(
            name="tv_hierarchy",
            position=(10, 10),
            size=(300, 200),
        )

        # Add items
        handle1 = treeview.add_item(None, "Root Item 1", "data1")
        handle2 = treeview.add_item(None, "Root Item 2", "data2")
        handle3 = treeview.add_item(handle1, "Child Item 1.1", "data3")

        # Initially, no item is selected
        assert treeview.selected_item is None

        # Select an item
        assert treeview.select_item(handle2) is True
        assert treeview.selected_item is treeview.get_item(handle2)
        assert treeview.get_item(handle2).selected is True
        assert treeview.get_item(handle1).selected is False
        assert treeview.get_item(handle3).selected is False

        # Select another item
        assert treeview.select_item(handle3) is True
        assert treeview.selected_item is treeview.get_item(handle3)
        assert treeview.get_item(handle3).selected is True
        assert treeview.get_item(handle1).selected is False
        assert treeview.get_item(handle2).selected is False

        # Try to select a non-existent item
        assert treeview.select_item(999) is False
        # Selected item should remain the same
        assert treeview.selected_item is treeview.get_item(handle3)

    def test_expand_collapse_item(self):




        """Test expanding and collapsing tree items."""
        treeview = TreeViewControl(
            name="tv_hierarchy",
            position=(10, 10),
            size=(300, 200),
        )

        # Add items
        handle1 = treeview.add_item(None, "Root Item 1", "data1")
        treeview.add_item(handle1, "Child Item 1.1", "data2")

        # Initially, items are not expanded
        assert treeview.get_item(handle1).expanded is False

        # Expand an item
        assert treeview.expand_item(handle1) is True
        assert treeview.get_item(handle1).expanded is True

        # Collapse the item
        assert treeview.collapse_item(handle1) is True
        assert treeview.get_item(handle1).expanded is False

        # Try to expand/collapse a non-existent item
        assert treeview.expand_item(999) is False
        assert treeview.collapse_item(999) is False

    def test_complex_hierarchy(self):




        """Test creating and manipulating a complex hierarchy."""
        treeview = TreeViewControl(
            name="tv_hierarchy",
            position=(10, 10),
            size=(300, 200),
        )

        # Create a complex hierarchy
        # Level 1
        root1 = treeview.add_item(None, "Company", "company_data")
        treeview.add_item(None, "Customers", "customers_data")

        # Level 2 under Company
        dept1 = treeview.add_item(root1, "HR", "hr_data")
        dept2 = treeview.add_item(root1, "Engineering", "eng_data")
        dept3 = treeview.add_item(root1, "Sales", "sales_data")

        # Level 3 under Engineering
        team1 = treeview.add_item(dept2, "Frontend", "frontend_data")
        team2 = treeview.add_item(dept2, "Backend", "backend_data")
        team3 = treeview.add_item(dept2, "DevOps", "devops_data")

        # Level 3 under Sales
        treeview.add_item(dept3, "North", "north_data")
        treeview.add_item(dept3, "South", "south_data")

        # Level 4 under Frontend team
        dev1 = treeview.add_item(team1, "Bob", "bob_data")
        dev2 = treeview.add_item(team1, "Alice", "alice_data")

        # Verify the hierarchy
        assert len(treeview.get_children(None)) == 2  # 2 root items
        assert len(treeview.get_children(root1)) == 3  # 3 departments
        assert len(treeview.get_children(dept2)) == 3  # 3 teams in Engineering
        assert len(treeview.get_children(team1)) == 2  # 2 developers in Frontend

        # Verify levels
        assert treeview.get_item(root1).item_level == 1
        assert treeview.get_item(dept2).item_level == 2
        assert treeview.get_item(team1).item_level == 3
        assert treeview.get_item(dev1).item_level == 4

        # Test expansion
        treeview.expand_item(root1)
        treeview.expand_item(dept2)
        treeview.expand_item(team1)

        assert treeview.get_item(root1).expanded is True
        assert treeview.get_item(dept2).expanded is True
        assert treeview.get_item(team1).expanded is True

        # Test deletion (whole department)
        treeview.delete_item(dept2)

        # Verify Engineering department and all its children are gone
        assert treeview.get_item(dept2) is None
        assert treeview.get_item(team1) is None
        assert treeview.get_item(team2) is None
        assert treeview.get_item(team3) is None
        assert treeview.get_item(dev1) is None
        assert treeview.get_item(dev2) is None

        # But other departments should still exist
        assert treeview.get_item(dept1) is not None
        assert treeview.get_item(dept3) is not None
