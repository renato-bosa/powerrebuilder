"""Famix importer for PowerBuilder source code.

Ported from reference/moose-pb-parser/PowerBuilder-Parser-Visitor/PWBFamixImporter.class.st

Features:
- Creates a references solver
- Creates a model
- Creates an importing context
- Searches for PowerBuilder files in a directory
- Preprocesses PowerBuilder code to remove comments and join lines
- Parses the files to get an AST
- Visits the AST to populate the model
- Resolves names after parsing
"""

from dataclasses import dataclass
from pathlib import Path

from model.pb_famix import FamixImportingContext, FamixModel
from parse.parser import PowerBuilderParser
from parse.pb_preprocessor import PowerBuilderPreprocessor

from .entity_creator import PowerBuilderEntityCreatorVisitor


@dataclass
class ImporterState:
    """State for Famix importer."""
    target_model: FamixModel | None = None
    importing_context: FamixImportingContext | None = None
    visitor: PowerBuilderEntityCreatorVisitor | None = None
    preprocessor: PowerBuilderPreprocessor | None = None
    parser: PowerBuilderParser | None = None


class PowerBuilderFamixImporter:
    """Importer for creating Famix models from PowerBuilder source code.

    Features:
    - Creates Famix model from PowerBuilder source
    - Handles preprocessing and parsing
    - Manages importing context and visitors
    - Resolves references after parsing
    """

    def __init__(self) -> None:
        """Initialize importer."""
        self.state = ImporterState()
        self.initialize()

    def initialize(self) -> None:
        """Initialize importer state."""
        self.state.target_model = FamixModel()
        self.state.importing_context = self.default_importing_context()

    def default_importing_context(self) -> FamixImportingContext:
        """Get default importing context.

        Returns:
            Importing context with maximum imports enabled
        """
        context = FamixImportingContext()
        context.import_maximum = True
        return context

    def setup(self) -> None:
        """Set up importer for processing.

        Creates and configures:
        - Entity creator visitor
        - Preprocessor
        - Parser
        """
        self.state.visitor = PowerBuilderEntityCreatorVisitor()
        self.state.visitor.model = self.state.target_model
        self.state.visitor.importing_context = self.state.importing_context

        self.state.preprocessor = PowerBuilderPreprocessor(Path.cwd())
        self.state.parser = PowerBuilderParser()

    def run(self) -> FamixModel:
        """Run the importer.

        Returns:
            Populated Famix model

        Steps:
        1. Set up importer
        2. Process files
        3. Resolve references
        """
        self.setup()
        self.basic_run()
        return self.state.target_model

    def basic_run(self) -> None:
        """Run basic import process.

        Steps:
        1. Process files
        2. Resolve unresolved references
        """
        self.process_files()
        self.state.visitor.resolve_unresolved_references()

    def process_files(self) -> None:
        """Process PowerBuilder source files.

        Steps for each file:
        1. Preprocess source
        2. Parse to AST
        3. Visit AST to create entities
        """
        # TODO: Implement file processing
        pass

    @classmethod
    def import_from_folder(cls, folder_path: str | Path) -> FamixModel:
        """Import PowerBuilder code from a folder.

        Args:
            folder_path: Path to folder containing PowerBuilder source

        Returns:
            Populated Famix model

        Steps:
        1. Create importer
        2. Set source folder
        3. Run import process
        """
        importer = cls()
        importer.state.target_model.name = Path(folder_path).name
        # TODO: Set source folder and process files
        return importer.run()
