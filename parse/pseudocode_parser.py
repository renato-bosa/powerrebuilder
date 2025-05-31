"""PowerBuilder pseudocode parser module."""
from pathlib import Path

from lark import Lark

from .base_parser import PowerBuilderBaseParser


class PowerBuilderPseudocodeParser(PowerBuilderBaseParser):
    """Parser for PowerBuilder pseudocode.

    Features:
    - Lark-based grammar
    - Enhanced error reporting
    - Integration with PowerBuilder parser infrastructure
    - Support for PowerBuilder-specific constructs
    """

    @classmethod
    def supported_extensions(cls) -> list[str]:
        """Get supported file extensions."""
        return ['pseudo', 'psc']

    def __init__(self, base_path: Path | None = None) -> None:
        """Initialize parser.

        Args:
            base_path: Optional base path for resolving includes
        """
        super().__init__(base_path)

        # Load pseudocode grammar
        with open(self.base_path / 'parse/pseudocode.lark', encoding='utf-8') as f:
            grammar = f.read()

        self.parser = Lark(
            grammar,
            parser='lalr',
            propagate_positions=True,
            maybe_placeholders=True,
            import_paths=[str(self.base_path / 'parse')],
        )

    def parse_and_transform(self, source: str | Path) -> list[str]:
        """Parse pseudocode and transform to Python.

        Args:
            source: Source code string or file path

        Returns:
            List of Python code lines

        Raises:
            ValueError: On parsing or transformation errors
        """
        from .pseudocode_transformer import PseudocodeToPython

        tree = self.parse(source)
        transformer = PseudocodeToPython()
        return transformer.transform(tree)
