import re

coverage_data = """
common - 7% (multiple files with very low coverage)
extract - ~5-10% (most files have 0% coverage)
parse - ~10-15% (most files have 0-20% coverage)
generate - ~0% (all files show 0% coverage)
decompile - ~0% (all files show 0% coverage)
model - ~30-40% (mixed coverage, some files at 80-90%, many at 0-20%)
"""

# Extract specific high/low coverage files
high_coverage = [
    "model/ast/node_kind.py - 95%",
    "model/ast/sql.py - 96%",
    "model/pb_datawindow/column.py - 97%",
    "model/system/functions.py - 94%",
    "model/system/events.py - 86%",
    "model/system/globals.py - 89%",
    "model/pb_transaction/transaction.py - 87%",
    "model/pb_transaction/error_handling.py - 85%",
    "model/pb_transaction/statement.py - 85%"
]

zero_coverage = [
    "All decompile modules - 0%",
    "All generate modules - 0%", 
    "Most parse modules - 0%",
    "Many test files - 0%"
]

critical_low_coverage = [
    "parse/parse_coordinator.py - 13%",
    "parse/powerbuilder_transformer.py - 9%",
    "model/cfg_integration.py - 17%",
    "model/cross_module_resolver.py - 20%",
    "model/security_analyzer.py - 16%",
    "model/ui.py - 20%",
    "common/types.py - 12%"
]

print("COVERAGE SUMMARY BY MODULE:")
print(coverage_data)
print("\nHIGH COVERAGE FILES (>85%):")
for f in high_coverage:
    print(f"  - {f}")
    
print("\nCRITICAL LOW COVERAGE FILES (<20%):")
for f in critical_low_coverage:
    print(f"  - {f}")
    
print("\nZERO COVERAGE MODULES:")
for f in zero_coverage:
    print(f"  - {f}")
    
print("\nOVERALL PROJECT COVERAGE: 7%")
print("\nRECOMMENDATIONS:")
print("1. Focus on writing tests for decompile and generate modules (currently 0%)")
print("2. Improve parse module coverage, especially parse_coordinator.py")
print("3. Add tests for critical model components like ui.py and security_analyzer.py")
print("4. Common module needs significant test coverage improvements")
