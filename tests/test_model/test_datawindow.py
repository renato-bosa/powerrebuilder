"""Test PowerBuilder DataWindow functionality."""

from model.pb_datawindow import (
    ColumnType,
    PBColumn,
    PBColumnNameOption,
    PBColumnTypeOption,
    PBDataWindow,
    PBTable,
)


def test_column():






    """Test column functionality.

    Ported from reference/moose-pb-parser/PowerBuilder-Parser-AST/PWBASTColumn.class.st
    """
    # Test basic column
    col = PBColumn(
        name="test_col",
        column_name="id",
        column_type=ColumnType.INTEGER,
        is_nullable=False,
    )
    assert str(col) == "id integer not null"

    # Test varchar column with length
    varchar_col = PBColumn(
        name="varchar_col",
        column_name="name",
        column_type=ColumnType.VARCHAR,
        length=50,
        default_value="'unknown'",
    )
    assert str(varchar_col) == "name varchar(50) default 'unknown'"

    # Test decimal column
    decimal_col = PBColumn(
        name="decimal_col",
        column_name="amount",
        column_type=ColumnType.DECIMAL,
        precision=10,
        scale=2,
    )
    assert str(decimal_col) == "amount decimal(10,2)"


def test_table():






    """Test table functionality."""
    # Create table with columns
    table = PBTable(
        name="test_table",
        table_name="employees",
    )

    # Add columns
    id_col = PBColumn(
        name="id_col",
        column_name="id",
        column_type=ColumnType.INTEGER,
        is_nullable=False,
    )
    name_col = PBColumn(
        name="name_col",
        column_name="name",
        column_type=ColumnType.VARCHAR,
        length=100,
    )

    table.add_column(id_col)
    table.add_column(name_col)
    table.primary_key = ["id"]

    expected = """create table employees (
  id integer not null,
  name varchar(100),
  primary key (id))"""

    assert str(table) == expected

    # Test column retrieval
    assert table.get_column("id") == id_col
    assert table.get_column("name") == name_col
    assert table.get_column("nonexistent") is None


def test_datawindow():






    """Test DataWindow functionality."""
    # Create DataWindow with table
    dw = PBDataWindow(name="emp_dw")

    table = PBTable(
        name="emp_table",
        table_name="employees",
        columns=[
            PBColumn(
                name="id_col",
                column_name="id",
                column_type=ColumnType.INTEGER,
                is_nullable=False,
            ),
            PBColumn(
                name="name_col",
                column_name="name",
                column_type=ColumnType.VARCHAR,
                length=100,
            ),
        ],
        primary_key=["id"],
    )

    dw.set_table(table)
    assert dw.get_table() == table

    # Add SQL statements
    dw.retrieve_sql = "select * from employees"
    dw.update_sql = "update employees set name = :name where id = :id"
    dw.insert_sql = "insert into employees (id, name) values (:id, :name)"
    dw.delete_sql = "delete from employees where id = :id"

    expected = """datawindow emp_dw
create table employees (
  id integer not null,
  name varchar(100),
  primary key (id))
retrieve: select * from employees
update: update employees set name = :name where id = :id
insert: insert into employees (id, name) values (:id, :name)
delete: delete from employees where id = :id"""

    assert str(dw) == expected


def test_column_name_option():






    """Test column name option functionality.

    Ported from reference/moose-pb-parser/PowerBuilder-Parser-AST/PWBASTColumnNameOption.class.st
    """
    # Test basic name option
    name_opt = PBColumnNameOption(
        name="test_opt",
        expression="'Employee Name'",
    )
    assert str(name_opt) == "name='Employee Name'"

    # Test column with name option
    col = PBColumn(
        name="test_col",
        column_name="emp_name",
        column_type=ColumnType.VARCHAR,
        length=100,
        name_option=name_opt,
    )
    assert str(col) == "emp_name varchar(100) name='Employee Name'"


def test_column_type_option():






    """Test column type option functionality.

    Ported from reference/moose-pb-parser/PowerBuilder-Parser-AST/PWBASTColumnTypeOption.class.st
    """
    # Test basic type option
    type_opt = PBColumnTypeOption(
        name="test_opt",
        expression="'edit'",
    )
    assert str(type_opt) == "type='edit'"

    # Test column with type option
    col = PBColumn(
        name="test_col",
        column_name="emp_name",
        column_type=ColumnType.VARCHAR,
        length=100,
        type_option=type_opt,
    )
    assert str(col) == "emp_name varchar(100) type='edit'"

    # Test column with both name and type options
    name_opt = PBColumnNameOption(
        name="name_opt",
        expression="'Employee Name'",
    )
    col.name_option = name_opt
    assert str(col) == "emp_name varchar(100) name='Employee Name' type='edit'"
