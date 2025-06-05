"""Transaction stub classes for PowerBuilder AST.

This module provides backward compatibility aliases for transaction classes.
New code should use the classes from transaction.py directly.
"""

from .transaction import PBTransactionObject as TransactionObject
from .transaction import PBTransaction as TransactionBlock
from .statement import PBTransactionStatement as TransactionStatement
