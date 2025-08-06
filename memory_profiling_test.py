#!/usr/bin/env python3
"""Memory profiling test script for PowerRebuilder project.

This script exercises key modules and functionality to profile memory usage,
identify potential leaks, and analyze allocation patterns.
"""

import gc
import sys
import tracemalloc
from pathlib import Path
from typing import Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


def memory_intensive_extract_operations() -> dict[str, Any]:
    """Exercise the extract module with memory-intensive operations."""
    print("Testing extract module...")

    results = {"files_processed": 0, "memory_objects": []}

    try:
        # Test PBD library operations
        from src.extract.pbd.library import Library
        from src.extract.pbd.structures import PBDHeader

        # Test fixture files if available
        test_files = [
            Path("data/input/pbd_files/dcm.pbd"),
            Path("tests/fixtures/pbd_files/dcm_email.pbd"),
            Path("tests/fixtures/pbd_files/pb6_example_fe.pbd"),
        ]

        for test_file in test_files:
            if test_file.exists():
                print(f"  Processing {test_file}...")
                try:
                    # Test library operations
                    with Library(test_file) as lib:
                        entries = list(lib.list_entries())
                        results["files_processed"] += 1
                        results["memory_objects"].extend(entries[:5])  # Sample entries

                        # Force garbage collection
                        gc.collect()

                except Exception as e:
                    print(f"    Error processing {test_file}: {e}")

    except ImportError as e:
        print(f"  Import error in extract module: {e}")
    except Exception as e:
        print(f"  Error in extract operations: {e}")

    return results


def memory_intensive_parse_operations() -> dict[str, Any]:
    """Exercise the parse module with memory-intensive operations."""
    print("Testing parse module...")

    results = {"ast_nodes": 0, "parse_attempts": 0}

    try:
        from src.parse.coordinator import ParseCoordinator
        from src.parse.grammar.loader import GrammarLoader
        from src.parse.parser.powerbuilder import PowerBuilderParser

        # Test fixture source files
        test_files = [
            Path("tests/fixtures/inheritance_test.sru"),
            Path("tests/fixtures/custom_control.sru"),
            Path("tests/fixtures/event_handling.sru"),
        ]

        try:
            # Initialize parser with grammar
            grammar_loader = GrammarLoader()
            parser = PowerBuilderParser(grammar_loader.load_powerbuilder_grammar())

            for test_file in test_files:
                if test_file.exists():
                    print(f"  Parsing {test_file}...")
                    try:
                        with open(test_file, encoding="utf-8", errors="ignore") as f:
                            content = f.read()

                        # Parse the content - this can be memory intensive
                        ast = parser.parse(content)
                        if ast:
                            results["ast_nodes"] += len(list(ast.iter_subtrees()))
                            results["parse_attempts"] += 1

                        # Force garbage collection after each parse
                        gc.collect()

                    except Exception as e:
                        print(f"    Error parsing {test_file}: {e}")

        except Exception as e:
            print(f"  Error initializing parser: {e}")

    except ImportError as e:
        print(f"  Import error in parse module: {e}")
    except Exception as e:
        print(f"  Error in parse operations: {e}")

    return results


def memory_intensive_decompile_operations() -> dict[str, Any]:
    """Exercise the decompile module with memory-intensive operations."""
    print("Testing decompile module...")

    results = {"pcode_files": 0, "opcodes_processed": 0}

    try:
        from src.decompile.coordinator import DecompileCoordinator
        from src.decompile.pcode.decoder import PCodeDecoder
        from src.decompile.pcode.detector import PCodeDetector

        # Test P-code files
        test_files = [
            Path("tests/fixtures/pcode_files/test.pcode"),
            Path("tests/fixtures/pcode_files/test_binary.fun"),
            Path("tests/fixtures/pcode_files/test_decode.pcode"),
        ]

        try:
            decoder = PCodeDecoder()
            detector = PCodeDetector()

            for test_file in test_files:
                if test_file.exists():
                    print(f"  Decompiling {test_file}...")
                    try:
                        with open(test_file, "rb") as f:
                            pcode_data = f.read()

                        # Detect P-code sections
                        sections = detector.detect_pcode_sections(pcode_data)

                        # Decode each section - memory intensive
                        for section in sections:
                            opcodes = decoder.decode_section(section)
                            results["opcodes_processed"] += len(opcodes)

                        results["pcode_files"] += 1

                        # Force garbage collection
                        gc.collect()

                    except Exception as e:
                        print(f"    Error decompiling {test_file}: {e}")

        except Exception as e:
            print(f"  Error initializing decompiler: {e}")

    except ImportError as e:
        print(f"  Import error in decompile module: {e}")
    except Exception as e:
        print(f"  Error in decompile operations: {e}")

    return results


def memory_intensive_model_operations() -> dict[str, Any]:
    """Exercise the model module with memory-intensive operations."""
    print("Testing model module...")

    results = {"models_created": 0, "entities_processed": 0}

    try:
        from src.model.services.ast_processor import ASTProcessor
        from src.model.services.entity_factory import EntityFactory
        from src.model.services.model_persistence import ModelPersistence

        try:
            # Create service instances
            processor = ASTProcessor()
            factory = EntityFactory()
            persistence = ModelPersistence()

            # Simulate model creation with dummy data
            for i in range(100):  # Create many objects to test memory usage
                # Create mock AST data
                mock_ast = {
                    "type": "function",
                    "name": f"test_function_{i}",
                    "parameters": [
                        {"name": f"param_{j}", "type": "string"} for j in range(10)
                    ],
                    "body": {
                        "statements": [
                            {"type": "assignment", "value": f"value_{k}"}
                            for k in range(20)
                        ]
                    },
                }

                # Process through model pipeline
                try:
                    processed = processor.process_ast(mock_ast)
                    entity = factory.create_function_entity(processed)
                    results["entities_processed"] += 1

                    if i % 20 == 0:  # Periodic cleanup
                        gc.collect()

                except Exception as e:
                    print(f"    Error processing model {i}: {e}")

            results["models_created"] = results["entities_processed"]

        except Exception as e:
            print(f"  Error in model operations: {e}")

    except ImportError as e:
        print(f"  Import error in model module: {e}")
    except Exception as e:
        print(f"  Error in model operations: {e}")

    return results


def memory_intensive_generate_operations() -> dict[str, Any]:
    """Exercise the generate module with memory-intensive operations."""
    print("Testing generate module...")

    results = {"templates_rendered": 0, "widgets_generated": 0}

    try:
        from src.generate.coordinators.flutter import FlutterCoordinator
        from src.generate.templates.engine import TemplateEngine

        try:
            # Initialize generation components
            flutter_coordinator = FlutterCoordinator()
            template_engine = TemplateEngine()

            # Generate many templates to test memory usage
            for i in range(50):
                try:
                    # Mock model data for generation
                    mock_model = {
                        "name": f"TestWidget{i}",
                        "properties": [
                            {"name": f"prop_{j}", "type": "String"} for j in range(10)
                        ],
                        "methods": [
                            {"name": f"method_{k}", "returns": "void"} for k in range(5)
                        ],
                    }

                    # Render templates - can be memory intensive
                    widget_code = template_engine.render_widget(mock_model)
                    if widget_code:
                        results["templates_rendered"] += 1
                        results["widgets_generated"] += 1

                    if i % 10 == 0:  # Periodic cleanup
                        gc.collect()

                except Exception as e:
                    print(f"    Error generating widget {i}: {e}")

        except Exception as e:
            print(f"  Error in generate operations: {e}")

    except ImportError as e:
        print(f"  Import error in generate module: {e}")
    except Exception as e:
        print(f"  Error in generate operations: {e}")

    return results


def run_memory_intensive_operations():
    """Run all memory-intensive operations and collect results."""
    print("Starting memory-intensive operations for profiling...")

    # Start memory tracing
    tracemalloc.start()

    results = {}

    # Run each module's memory-intensive operations
    try:
        results["extract"] = memory_intensive_extract_operations()
        results["parse"] = memory_intensive_parse_operations()
        results["decompile"] = memory_intensive_decompile_operations()
        results["model"] = memory_intensive_model_operations()
        results["generate"] = memory_intensive_generate_operations()

        # Force final garbage collection
        gc.collect()

        # Get memory usage snapshot
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics("lineno")

        print("\nTop 10 memory allocations:")
        for index, stat in enumerate(top_stats[:10], 1):
            print(f"{index:2d}. {stat}")

        # Stop memory tracing
        tracemalloc.stop()

    except Exception as e:
        print(f"Error during memory profiling: {e}")
        tracemalloc.stop()

    return results


if __name__ == "__main__":
    print("PowerRebuilder Memory Profiling Test")
    print("=" * 40)

    # Run the memory-intensive operations
    results = run_memory_intensive_operations()

    print("\nResults Summary:")
    print("=" * 20)
    for module, module_results in results.items():
        print(f"{module.capitalize()}:")
        for key, value in module_results.items():
            print(f"  {key}: {value}")

    print("\nMemory profiling test completed!")
