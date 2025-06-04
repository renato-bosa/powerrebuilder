"""Tests for PowerBuilder SQL model."""


from model.constructs.pb_sql import (
    PBCursorNode,
    PBDeleteNode,
    PBInsertNode,
    PBSelectNode,
    PBSQLNode,
    PBSQLStatementNode,
    PBTransactionNode,
    PBUpdateNode,
)


class TestPBSQLNode:
    """Test PBSQLNode base class."""

    def test_sql_node_creation(self):
        """Test creating a SQL node."""
        node = PBSQLNode(sql_type="SELECT")
        assert node.sql_type == "SELECT"


class TestPBSQLStatementNode:
    """Test PBSQLStatementNode class."""

    def test_sql_statement_node_creation(self):
        """Test creating a SQL statement node."""
        node = PBSQLStatementNode(
            statement="SELECT * FROM customers",
            statement_type="SELECT",
        )
        assert node.statement == "SELECT * FROM customers"
        assert node.statement_type == "SELECT"


class TestPBSelectNode:
    """Test PBSelectNode class."""

    def test_simple_select(self):
        """Test creating a simple SELECT statement."""
        select = PBSelectNode(
            columns=["*"],
            from_table="customers",
        )
        assert select.columns == ["*"]
        assert select.from_table == "customers"

    def test_select_with_where(self):
        """Test SELECT with WHERE clause."""
        select = PBSelectNode(
            columns=["customer_id", "name"],
            from_table="customers",
            where_clause="status = 'active'",
        )
        assert len(select.columns) == 2
        assert select.where_clause == "status = 'active'"

    def test_select_with_join(self):
        """Test SELECT with JOIN."""
        select = PBSelectNode(
            columns=["c.name", "o.order_date"],
            from_table="customers c",
            joins=[{
                "type": "INNER JOIN",
                "table": "orders o",
                "condition": "c.customer_id = o.customer_id",
            }],
        )
        assert len(select.joins) == 1
        assert select.joins[0]["type"] == "INNER JOIN"

    def test_select_with_order_by(self):
        """Test SELECT with ORDER BY."""
        select = PBSelectNode(
            columns=["name", "created_date"],
            from_table="customers",
            order_by=["created_date DESC", "name ASC"],
        )
        assert len(select.order_by) == 2
        assert "DESC" in select.order_by[0]

    def test_select_with_group_by(self):
        """Test SELECT with GROUP BY and HAVING."""
        select = PBSelectNode(
            columns=["status", "COUNT(*)"],
            from_table="customers",
            group_by=["status"],
            having_clause="COUNT(*) > 10",
        )
        assert select.group_by == ["status"]
        assert select.having_clause == "COUNT(*) > 10"


class TestPBInsertNode:
    """Test PBInsertNode class."""

    def test_simple_insert(self):
        """Test creating an INSERT statement."""
        insert = PBInsertNode(
            table="customers",
            columns=["name", "email"],
            values=["'John Doe'", "'john@example.com'"],
        )
        assert insert.table == "customers"
        assert len(insert.columns) == 2
        assert len(insert.values) == 2

    def test_insert_with_select(self):
        """Test INSERT with SELECT statement."""
        insert = PBInsertNode(
            table="customers_archive",
            columns=["customer_id", "name", "archived_date"],
            select_statement="SELECT customer_id, name, CURRENT_DATE FROM customers WHERE status = 'inactive'",
        )
        assert insert.table == "customers_archive"
        assert insert.select_statement is not None


class TestPBUpdateNode:
    """Test PBUpdateNode class."""

    def test_simple_update(self):
        """Test creating an UPDATE statement."""
        update = PBUpdateNode(
            table="customers",
            assignments=[
                ("status", "'active'"),
                ("updated_date", "CURRENT_TIMESTAMP"),
            ],
        )
        assert update.table == "customers"
        assert len(update.assignments) == 2
        assert update.assignments[0] == ("status", "'active'")

    def test_update_with_where(self):
        """Test UPDATE with WHERE clause."""
        update = PBUpdateNode(
            table="orders",
            assignments=[("shipped", "true")],
            where_clause="order_date < CURRENT_DATE - 7",
        )
        assert update.where_clause == "order_date < CURRENT_DATE - 7"


class TestPBDeleteNode:
    """Test PBDeleteNode class."""

    def test_simple_delete(self):
        """Test creating a DELETE statement."""
        delete = PBDeleteNode(
            table="customers",
            where_clause="status = 'inactive' AND last_login < '2023-01-01'",
        )
        assert delete.table == "customers"
        assert "inactive" in delete.where_clause

    def test_delete_all(self):
        """Test DELETE without WHERE clause."""
        delete = PBDeleteNode(table="temp_data")
        assert delete.table == "temp_data"
        assert delete.where_clause is None


class TestPBCursorNode:
    """Test PBCursorNode class."""

    def test_cursor_declaration(self):
        """Test creating a cursor declaration."""
        cursor = PBCursorNode(
            name="customer_cursor",
            select_statement="SELECT * FROM customers WHERE status = :status",
            parameters=[":status"],
        )
        assert cursor.name == "customer_cursor"
        assert ":status" in cursor.select_statement
        assert cursor.parameters == [":status"]

    def test_cursor_with_for_update(self):
        """Test cursor with FOR UPDATE clause."""
        cursor = PBCursorNode(
            name="update_cursor",
            select_statement="SELECT * FROM orders WHERE shipped = false",
            for_update=True,
        )
        assert cursor.for_update is True


class TestPBTransactionNode:
    """Test PBTransactionNode class."""

    def test_transaction_commit(self):
        """Test creating a COMMIT statement."""
        trans = PBTransactionNode(
            action="COMMIT",
            transaction_object="SQLCA",
        )
        assert trans.action == "COMMIT"
        assert trans.transaction_object == "SQLCA"

    def test_transaction_rollback(self):
        """Test creating a ROLLBACK statement."""
        trans = PBTransactionNode(
            action="ROLLBACK",
            transaction_object="SQLCA",
        )
        assert trans.action == "ROLLBACK"

    def test_transaction_connect(self):
        """Test creating a CONNECT statement."""
        trans = PBTransactionNode(
            action="CONNECT",
            transaction_object="SQLCA",
            connection_string="DSN=MyDatabase;UID=user;PWD=pass",
        )
        assert trans.action == "CONNECT"
        assert trans.connection_string is not None

    def test_transaction_savepoint(self):
        """Test transaction with savepoint."""
        trans = PBTransactionNode(
            action="SAVEPOINT",
            savepoint_name="before_update",
        )
        assert trans.action == "SAVEPOINT"
        assert trans.savepoint_name == "before_update"
