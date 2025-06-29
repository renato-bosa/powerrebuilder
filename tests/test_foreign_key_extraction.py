"""Test foreign key extraction from DataWindows."""

from src.generate.coordinator import extract_datawindow_from_ast


def test_foreign_key_extraction():






    """Test that foreign keys are correctly extracted from DataWindow AST."""

    # Test case 1: Basic foreign key in column definition
    ast_data = {
        "node_type": "DataWindow",
        "columns": [
            {
                "name": "id",
                "column_type": "integer",
                "is_primary_key": True,
            },
            {
                "name": "customer_id",
                "column_type": "integer",
                "foreign_key": True,
                "foreign_table": "customers",
                "foreign_column": "id",
            },
            {
                "name": "amount",
                "column_type": "decimal",
            },
        ],
        "table": {
            "name": "orders",
            "primary_key": ["id"],
        },
        "retrieve_sql": "SELECT id, customer_id, amount FROM orders",
    }

    result = extract_datawindow_from_ast(ast_data)
    assert result is not None
    assert len(result["relationships"]) == 1
    assert result["relationships"][0]["type"] == "foreign_key"
    assert result["relationships"][0]["source_column"] == "customer_id"
    assert result["relationships"][0]["target_table"] == "customers"
    assert result["relationships"][0]["target_column"] == "id"
    assert result["primary_keys"] == ["id"]
    print("✓ Test 1 passed: Basic foreign key extraction")

    # Test case 2: Multiple foreign keys
    ast_data2 = {
        "type": "datawindow",
        "columns": [
            {
                "name": "order_id",
                "primary_key": True,
            },
            {
                "name": "customer_id",
                "foreign_key": True,
                "foreign_table": "customers",
            },
            {
                "name": "product_id",
                "foreign_key": True,
                "foreign_table": "products",
                "foreign_column": "product_code",
            },
        ],
    }

    result2 = extract_datawindow_from_ast(ast_data2)
    assert result2 is not None
    assert len(result2["relationships"]) == 2
    assert result2["relationships"][0]["target_table"] == "customers"
    assert result2["relationships"][1]["target_table"] == "products"
    assert result2["relationships"][1]["target_column"] == "product_code"
    print("✓ Test 2 passed: Multiple foreign keys extraction")

    # Test case 3: Nested DataWindow relationship
    ast_data3 = {
        "node_type": "DataWindow",
        "datawindow_type": "nested",
        "nested_datawindow": {
            "parent_columns": ["order_id"],
            "child_datawindow": "dw_order_details",
            "linkage_columns": ["order_id", "line_item_id"],
        },
        "columns": [
            {"name": "order_id", "is_primary_key": True},
            {"name": "order_date", "column_type": "date"},
        ],
    }

    result3 = extract_datawindow_from_ast(ast_data3)
    assert result3 is not None
    assert len(result3["relationships"]) == 1
    assert result3["relationships"][0]["type"] == "nested"
    assert result3["relationships"][0]["parent_columns"] == ["order_id"]
    assert result3["relationships"][0]["child_datawindow"] == "dw_order_details"
    print("✓ Test 3 passed: Nested DataWindow relationship extraction")

    # Test case 4: Explicit relationships in AST
    ast_data4 = {
        "node_type": "DataWindow",
        "table": {"name": "order_items"},
        "columns": [
            {"name": "id"},
            {"name": "order_id"},
            {"name": "product_id"},
        ],
        "relationships": [
            {
                "type": "many_to_one",
                "source_column": "order_id",
                "target_table": "orders",
                "target_column": "id",
            },
            {
                "type": "many_to_one",
                "source_column": "product_id",
                "target_table": "products",
                "target_column": "id",
                "join_type": "left",
            },
        ],
    }

    result4 = extract_datawindow_from_ast(ast_data4)
    assert result4 is not None
    assert len(result4["relationships"]) == 2
    assert result4["relationships"][0]["source_column"] == "order_id"
    assert result4["relationships"][1]["join_type"] == "left"
    print("✓ Test 4 passed: Explicit relationships extraction")

    # Test case 5: Combined primary keys from table and columns
    ast_data5 = {
        "node_type": "DataWindow",
        "columns": [
            {"name": "region_id", "primary_key": True},
            {"name": "product_id", "is_primary_key": True},
            {"name": "sales_amount"},
        ],
        "table": {
            "primary_key": "region_id",
        },
    }

    result5 = extract_datawindow_from_ast(ast_data5)
    assert result5 is not None
    assert set(result5["primary_keys"]) == {"region_id", "product_id"}
    print("✓ Test 5 passed: Combined primary key extraction")

    print("\n✅ All foreign key extraction tests passed!")


if __name__ == "__main__":
    test_foreign_key_extraction()
