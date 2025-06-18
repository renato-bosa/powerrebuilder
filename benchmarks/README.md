# Performance Benchmarks

This directory contains comprehensive performance benchmarks for the SIME Finch PowerBuilder reverse engineering system.

## Overview

The benchmark suite measures performance across all major components:

- **Extraction**: PBL/PBD file extraction speed
- **Parsing**: PowerBuilder grammar parsing performance
- **Generation**: Code generation throughput
- **End-to-End**: Complete conversion pipeline

## Running Benchmarks

### Run All Benchmarks

```bash
python benchmarks/run_benchmarks.py
```

This will:
1. Execute all benchmark suites
2. Generate a performance report in `benchmarks/performance_report.md`
3. Save detailed results in `benchmarks/benchmark_results_full.json`

### Run Individual Suites

```bash
# Extraction benchmarks
pytest benchmarks/benchmark_extraction.py --benchmark-only

# Parsing benchmarks  
pytest benchmarks/benchmark_parsing.py --benchmark-only

# Generation benchmarks
pytest benchmarks/benchmark_generation.py --benchmark-only

# End-to-end benchmarks
pytest benchmarks/benchmark_end_to_end.py --benchmark-only
```

### Benchmark Options

```bash
# Compare against baseline
pytest benchmarks/ --benchmark-compare=baseline

# Save results
pytest benchmarks/ --benchmark-save=my_results

# Set minimum rounds
pytest benchmarks/ --benchmark-min-rounds=10
```

## Performance Targets

| Component | Operation | Target | Rationale |
|-----------|-----------|--------|-----------|
| Extraction | Single PBL (<1MB) | <100ms | Fast enough for interactive use |
| Extraction | Large PBL (10MB) | <2s | Reasonable for batch processing |
| Parsing | Simple function | <10ms | Near-instant feedback |
| Parsing | Complex window | <50ms | Smooth user experience |
| Generation | Single widget | <1ms | Negligible overhead |
| Generation | Large project (85 files) | <500ms | Quick project generation |
| End-to-End | Small project | <1s | Rapid prototyping |
| Memory | Peak usage | <200MB | Run on modest hardware |

## Benchmark Structure

### benchmark_extraction.py
- PBL/PBD extraction speed
- Corrupted file recovery
- Batch extraction performance
- Memory usage during extraction

### benchmark_parsing.py
- PowerBuilder grammar parsing
- AST transformation
- Error recovery overhead
- Incremental parsing

### benchmark_generation.py
- Template rendering speed
- AST to Flutter conversion
- DataWindow processing
- Batch file generation

### benchmark_end_to_end.py
- Complete pipeline performance
- Parallel processing efficiency
- Incremental conversion
- Memory efficiency

## Interpreting Results

The performance report includes:

1. **Executive Summary**: Overall benchmark statistics
2. **Performance Targets**: Pass/fail for each target
3. **Detailed Results**: Timing statistics for each test
4. **Recommendations**: Performance optimization suggestions

### Key Metrics

- **Mean**: Average execution time
- **Min/Max**: Best/worst case performance
- **Std Dev**: Consistency of performance

## Adding New Benchmarks

1. Create a test class in the appropriate file
2. Use `@pytest.mark.benchmark` or `benchmark` fixture
3. Assert performance targets
4. Update this README with new targets

Example:
```python
def test_new_feature(benchmark):
    def operation():
        # Code to benchmark
        return result
    
    result = benchmark(operation)
    assert benchmark.stats['mean'] < 0.1  # 100ms target
```

## Continuous Performance Monitoring

Consider integrating benchmarks into CI/CD:

1. Run benchmarks on each PR
2. Compare against baseline
3. Fail if performance regresses significantly
4. Track performance trends over time

## Optimization Guidelines

When optimizing based on benchmark results:

1. Profile first - identify actual bottlenecks
2. Optimize algorithms before micro-optimizations
3. Consider memory vs speed tradeoffs
4. Maintain code readability
5. Document any complex optimizations

## Dependencies

- pytest-benchmark
- pytest
- All SIME Finch dependencies

Install with:
```bash
pip install pytest-benchmark
```