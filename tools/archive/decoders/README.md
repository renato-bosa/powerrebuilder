# Archived PowerBuilder Decoders

This directory contains archived PowerBuilder decoder implementations that were consolidated into `powerbuilder_decoder_v2.py`.

## Archived Files

1. **powerbuilder_decoder.py** - Original dictionary-based decoder with pattern matching
2. **powerbuilder_decoder_fixed.py** - Control byte sequence decoder (different approach)
3. **powerbuilder_decoder_integrated.py** - Integration-focused decoder for pipeline
4. **position_based_decoder.py** - Statistical analysis decoder
5. **test_decoder.py** - Tests for original decoder
6. **test_position_decoder.py** - Tests for position-based decoder
7. **analyze_pb_encoding.py** - Analysis utility
8. **decode_test_patterns.py** - Test pattern decoder

## Active Decoder

The active decoder is `extract/pbd/utils/powerbuilder_decoder_v2.py` which combines the best features from all implementations:
- Domain dictionary from original decoder
- Control byte mappings from fixed decoder
- Position-based analysis from position decoder
- Pipeline integration features
- State management and caching

## Consolidation Date

Archived on: 2025-06-28

## Reason for Consolidation

Multiple decoder implementations were creating confusion and maintenance burden. The v2 decoder successfully combines all strategies and is the only one actively used in the codebase.