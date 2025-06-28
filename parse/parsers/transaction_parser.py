"""PowerBuilder transaction and event parser.

This module provides simplified parsing functionality for PowerBuilder transaction
and event code without relying on grammar files. It uses simple string operations
to parse PowerBuilder transaction statements, events, and related constructs.

Note: This is a specialized parser for specific PowerBuilder constructs.
For general PowerBuilder parsing, use PowerBuilderParser from parse_coordinator.
"""


from pathlib import Path

from model.transaction.savepoint import PBSavepoint
from model.transaction.statement import PBStatementType, PBTransactionStatement
from model.transaction.transaction import PBTransaction, PBTransactionObject


class TransactionParser:
    """PowerBuilder parser with transaction-specific functionality.

    This is a simplified parser implementation that doesn't rely on grammar files.
    It uses simple string operations to parse PowerBuilder transaction code.
    """

    def __init__(self, base_path: Path | None = None) -> None:




        """Initialize the parser.

        Args:
            base_path: Optional base path (not used in this implementation)
        """
        self.base_path = base_path or Path.cwd()

    def parse_transaction(self, source: str) -> PBTransactionObject:




        """Parse a transaction object declaration.

        Args:
            source: Transaction declaration source code

        Returns:
            PBTransactionObject object
        """
        # In a complete implementation, this would parse the source and create
        # a PBTransaction object with the appropriate properties

        # For this simplified implementation, we'll extract the transaction name
        # from the source and create a basic PBTransaction object
        if "transaction" in source.lower():
            parts = source.split()
            if len(parts) >= 2:
                name = parts[1].strip()
                return PBTransactionObject(name=name)

        # Default fallback
        return PBTransactionObject(name="sqlca")

    def parse_transaction_statement(self, source: str) -> PBTransactionStatement:




        """Parse a transaction statement.

        Args:
            source: Transaction statement source code

        Returns:
            PBTransactionStatement object
        """
        # Extract the statement type and transaction object from the source
        source = source.strip().upper()

        # Handle CONNECT statement
        if source.startswith("CONNECT"):
            transaction_object = "sqlca"  # Default
            if "USING" in source:
                # Extract transaction object after USING
                parts = source.split("USING")
                if len(parts) > 1:
                    transaction_object = parts[1].strip().rstrip("").lower()

            return PBTransactionStatement(
                statement_type=PBStatementType.CONNECT,
                transaction_object=transaction_object,
            )

        # Handle COMMIT statement
        if source.startswith("COMMIT"):
            transaction_object = "sqlca"  # Default
            if "USING" in source:
                # Extract transaction object after USING
                parts = source.split("USING")
                if len(parts) > 1:
                    transaction_object = parts[1].strip().rstrip(";").lower()

            return PBTransactionStatement(
                statement_type=PBStatementType.COMMIT,
                transaction_object=transaction_object,
            )

        # Handle ROLLBACK statement
        if source.startswith("ROLLBACK"):
            transaction_object = "sqlca"  # Default
            savepoint_name = None

            if "USING" in source:
                # Extract transaction object after USING
                parts = source.split("USING")
                if len(parts) > 1:
                    transaction_object = parts[1].strip().rstrip(";").lower()

            if "TO SAVEPOINT" in source:
                # Extract savepoint name
                parts = source.split("TO SAVEPOINT")
                if len(parts) > 1:
                    savepoint_name = parts[1].strip().rstrip(";")

            return PBTransactionStatement(
                statement_type=PBStatementType.ROLLBACK,
                transaction_object=transaction_object,
                savepoint_name=savepoint_name,
            )

        # Handle DISCONNECT statement
        if source.startswith("DISCONNECT"):
            transaction_object = "sqlca"  # Default
            if "USING" in source:
                # Extract transaction object after USING
                parts = source.split("USING")
                if len(parts) > 1:
                    transaction_object = parts[1].strip().rstrip(";").lower()

            return PBTransactionStatement(
                statement_type=PBStatementType.DISCONNECT,
                transaction_object=transaction_object,
            )

        # Default fallback for unrecognized statements
        return PBTransactionStatement(
            statement_type="UNKNOWN",
            transaction_object="sqlca",
        )

    def parse_transaction_block(self, source: str) -> PBTransaction:




        """Parse a transaction block.

        Args:
            source: Transaction block source code

        Returns:
            PBTransaction object with statements
        """
        # Extract the transaction object from the USING clause
        transaction_object = "sqlca"  # Default

        if "USING" in source:
            parts = source.split("USING")
            if len(parts) > 1:
                transaction_part = parts[1].strip()
                if ";" in transaction_part:
                    transaction_object = transaction_part.split(";")[0].strip().lower()
                else:
                    transaction_object = transaction_part.split()[0].strip().lower()

        # Create the transaction object
        transaction = PBTransaction(transaction_object=transaction_object)

        # Check for savepoints
        if "SAVEPOINT" in source:
            # Use a set to track unique savepoint names
            savepoint_names = set()

            parts = source.split("SAVEPOINT")
            for part in parts[1:]:
                # Extract savepoint name
                if ";" in part:
                    savepoint_name = part.split(";")[0].strip()
                else:
                    savepoint_name = part.split()[0].strip()

                # Only add if not already processed
                if savepoint_name not in savepoint_names:
                    savepoint_names.add(savepoint_name)
                    savepoint = PBSavepoint(
                        name=savepoint_name,
                        transaction_object=transaction_object,
                    )
                    transaction.add_savepoint(savepoint)

        # Check for error handling
        if "TRY" in source and "CATCH" in source:
            transaction.has_error_handling = True

        # Add statements
        # For INSERT, UPDATE, DELETE, etc.
        for statement_type in [
            "INSERT",
            "UPDATE",
            "DELETE",
            "SELECT",
            "COMMIT",
            "ROLLBACK",
        ]:
            if statement_type in source:
                # Create a statement for each occurrence
                # In a real implementation, we would parse the full statement
                statement = PBTransactionStatement(
                    statement_type=statement_type,
                    transaction_object=transaction_object,
                )
                transaction.add_statement(statement)

        return transaction
