# SQL Optimization in PowerBuilder Model

This directory contains SQL optimization functionality for the PowerBuilder AST model. The SQL optimizer transforms SQL queries to improve performance and compatibility with target databases.

## Overview

The optimization system provides:

1. **SQLOptimizer** - SQL query optimizer for PowerBuilder SQL statements

Note: Expression optimization is handled by the ExpressionOptimizer in `src/decompile/analysis/data_flow.py`. Advanced expression optimization features (strength reduction, distributive law, CSE) were removed during consolidation but can be reimplemented if needed.

## SQL Optimization Features

### Query Transformation
The SQLOptimizer transforms PowerBuilder SQL queries for:
- Target database compatibility
- Performance optimization
- Syntax normalization

### Key Features
- Parameter marker conversion (`:param` to `?` or `@param`)
- Datatype mapping for different databases
- Query structure optimization
- Proper handling of PowerBuilder-specific SQL constructs

### Supported Databases
- PostgreSQL
- MySQL
- SQL Server
- Oracle
- SQLite

## Usage

### SQL Optimization
```python
from src.model.optimization import SQLOptimizer, optimize_sql
from src.model.ast.nodes.sql import SQLStatement

# Create a SQL statement
sql_stmt = SQLStatement(
    query="SELECT * FROM users WHERE user_id = :user_id"
)

# Optimize for target database
optimizer = SQLOptimizer(target_db="postgresql")
optimized = optimizer.optimize(sql_stmt)
# Result: "SELECT * FROM users WHERE user_id = $1"
```


## Implementation Details

### SQL Transformation Process
1. Parse SQL statement structure
2. Identify parameter markers and datatypes
3. Apply database-specific transformations
4. Optimize query structure where possible

### Database-Specific Handling
Each target database has specific requirements:
- **PostgreSQL**: Uses `$1`, `$2` style parameters
- **MySQL**: Uses `?` placeholders
- **SQL Server**: Uses `@param` style parameters
- **Oracle**: Maintains `:param` style
- **SQLite**: Uses `?` placeholders

## Testing

Test suite is provided in `tests/unit/model/test_optimization/`

Run tests with:
```bash
pytest tests/unit/model/test_optimization/
```

## Future Enhancements

Potential improvements:
1. Query plan optimization
2. Index hint generation
3. Join order optimization
4. Subquery optimization
5. Common table expression (CTE) support
6. Database-specific performance hints

## PowerBuilder SQL Considerations

The optimizer handles PowerBuilder-specific SQL features:
- Dynamic SQL with parameter markers
- Embedded SQL syntax
- Transaction handling statements
- PowerBuilder datatype conversions
- NULL handling semantics