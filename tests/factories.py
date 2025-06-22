"""Test factories for generating test data using factory_boy."""

import factory

from extract.pbd.structures.data_block import DataClass
from extract.pbd.structures.entry import PbEntryDefinition
from model.ast import (
    Assignment,
    BinaryExpression,
    IntegerLiteral,
    StringLiteral,
    Variable,
)
from model.utils.base import SourceAnchor


class SourceAnchorFactory(factory.Factory):
    """Factory for creating source anchors."""

    class Meta:
        model = SourceAnchor

    line = factory.Faker("pyint", min_value=1, max_value=1000)
    column = factory.Faker("pyint", min_value=1, max_value=100)
    offset = factory.LazyAttribute(lambda obj: (obj.line - 1) * 80 + obj.column)
    file_path = factory.Faker("file_path", depth=3)


class VariableFactory(factory.Factory):
    """Factory for creating variable nodes."""

    class Meta:
        model = Variable

    name = factory.Faker("pystr", min_chars=3, max_chars=20)
    source_anchor = factory.SubFactory(SourceAnchorFactory)


class IntegerLiteralFactory(factory.Factory):
    """Factory for creating integer literal nodes."""

    class Meta:
        model = IntegerLiteral

    value = factory.Faker("pyint", min_value=0, max_value=1000)
    source_anchor = factory.SubFactory(SourceAnchorFactory)


class StringLiteralFactory(factory.Factory):
    """Factory for creating string literal nodes."""

    class Meta:
        model = StringLiteral

    value = factory.Faker("pystr", min_chars=5, max_chars=20)
    source_anchor = factory.SubFactory(SourceAnchorFactory)


class BinaryExpressionFactory(factory.Factory):
    """Factory for creating binary expression nodes."""

    class Meta:
        model = BinaryExpression

    operator = factory.Faker("random_element", elements=["+", "-", "*", "/", "==", "!=", "<", ">", "<=", ">=", "and", "or"])
    left = factory.SubFactory(VariableFactory)
    right = factory.SubFactory(IntegerLiteralFactory)
    source_anchor = factory.SubFactory(SourceAnchorFactory)


class AssignmentFactory(factory.Factory):
    """Factory for creating assignment nodes."""

    class Meta:
        model = Assignment

    # For dataclasses, we need to pass values through _create
    @classmethod
    def _create(cls, model_class, **kwargs):

        # Create the assignment with proper field names
        return model_class(
            target=kwargs.get("target", VariableFactory()),
            value=kwargs.get("value", IntegerLiteralFactory()),
            source_anchor=kwargs.get("source_anchor", SourceAnchorFactory()),
        )


class PbEntryDefinitionFactory(factory.Factory):
    """Factory for creating PowerBuilder entry definitions."""

    class Meta:
        model = PbEntryDefinition

    objectname = factory.Faker("file_name", extension="sru")
    objecttype = factory.Faker("random_element", elements=[0, 1, 8, 9, 13, 18, 55])
    version = factory.Faker("random_element", elements=["10.5", "11.0", "12.5", "2017", "2019"])
    filesize = factory.Faker("pyint", min_value=100, max_value=100000)
    offset = factory.Faker("pyint", min_value=0, max_value=10000)
    objectsize = factory.LazyAttribute(lambda obj: obj.filesize - 100)
    commentlen = factory.Faker("pyint", min_value=0, max_value=500)


class DataClassFactory(factory.Factory):
    """Factory for creating DAT block data classes."""

    class Meta:
        model = DataClass

    address = factory.Faker("pyint", min_value=0, max_value=1000000)
    data = factory.Faker("binary", length=1024)
    next_block_offset = factory.Faker("pyint", min_value=0, max_value=1000000)
    data_length_in_block = factory.LazyAttribute(lambda obj: len(obj.data))
    is_unicode_data_block_header = factory.Faker("pybool")


class PowerBuilderCodeFactory:
    """Factory for generating PowerBuilder code snippets."""

    @staticmethod
    def window_definition(name: str = None) -> str:


        """Generate a window definition."""
        if not name:
            from faker import Faker
            fake = Faker()
            name = f"w_{fake.pystr(min_chars=5, max_chars=15)}"

        return f"""forward
global type {name} from window
end type
end forward

global type {name} from window
integer width = 1234
integer height = 567
boolean titlebar = true
string title = "Test Window"
end type
global {name} {name}

on {name}.create
end on

on {name}.destroy
end on"""

    @staticmethod
    def function_definition(name: str = None, return_type: str = "integer") -> str:


        """Generate a function definition."""
        if not name:
            from faker import Faker
            fake = Faker()
            name = f"f_{fake.pystr(min_chars=5, max_chars=15)}"

        return f"""public function {return_type} {name} (string as_param1, integer ai_param2)
// Function: {name}
// Description: Test function

{return_type} li_return

if isnull(as_param1) then
    return -1
end if

li_return = ai_param2 + len(as_param1)

return li_return
end function"""

    @staticmethod
    def datawindow_syntax() -> str:


        """Generate DataWindow syntax."""
        from faker import Faker
        fake = Faker()
        table_name = f"tbl_{fake.pystr(min_chars=5, max_chars=10)}"

        return f"""release 12.5;
datawindow(units=0 timer_interval=0 color=1073741824 brushmode=0 transparency=0 gradient.angle=0 gradient.color=8421504 gradient.focus=0 gradient.repetition.count=0 gradient.repetition.length=100 gradient.repetition.mode=0 gradient.scale=100 gradient.spread=100 gradient.transparency=0 picture.blur=0 picture.clip.bottom=0 picture.clip.left=0 picture.clip.right=0 picture.clip.top=0 picture.mode=0 picture.scale.x=100 picture.scale.y=100 picture.transparency=0 processing=0 HTMLDW=no print.printername="" print.documentname="" print.orientation = 0 print.margin.left = 110 print.margin.right = 110 print.margin.top = 96 print.margin.bottom = 96 print.paper.source = 0 print.paper.size = 0 print.canusedefaultprinter=yes print.prompt=no print.buttons=no print.preview.buttons=no print.cliptext=no print.overrideprintjob=no print.collate=yes print.background=no print.preview.background=no print.preview.outline=yes hidegrayline=no showbackcoloronxp=no picture.file="" grid.lines=0 )
header(height=80 color="536870912" transparency="0" gradient.color="8421504" gradient.transparency="0" gradient.angle="0" brushmode="0" gradient.repetition.mode="0" gradient.repetition.count="0" gradient.repetition.length="100" gradient.focus="0" gradient.scale="100" gradient.spread="100" )
summary(height=0 color="536870912" transparency="0" gradient.color="8421504" gradient.transparency="0" gradient.angle="0" brushmode="0" gradient.repetition.mode="0" gradient.repetition.count="0" gradient.repetition.length="100" gradient.focus="0" gradient.scale="100" gradient.spread="100" )
footer(height=0 color="536870912" transparency="0" gradient.color="8421504" gradient.transparency="0" gradient.angle="0" brushmode="0" gradient.repetition.mode="0" gradient.repetition.count="0" gradient.repetition.length="100" gradient.focus="0" gradient.scale="100" gradient.spread="100" )
detail(height=96 color="536870912" transparency="0" gradient.color="8421504" gradient.transparency="0" gradient.angle="0" brushmode="0" gradient.repetition.mode="0" gradient.repetition.count="0" gradient.repetition.length="100" gradient.focus="0" gradient.scale="100" gradient.spread="100" )
table(column=(type=number updatewhereclause=yes name=id dbname="{table_name}.id" )
 column=(type=char(50) updatewhereclause=yes name=name dbname="{table_name}.name" )
 column=(type=datetime updatewhereclause=yes name=created_date dbname="{table_name}.created_date" )
 retrieve="SELECT id, name, created_date FROM {table_name}" )"""
