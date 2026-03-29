Function-Weight Energy Scheduling Test
=======================================

Compile (LTO mode):
  AFL_LLVM_FUNC_MAP_OUTPUT=./funcmap.txt AFL_LLVM_FUNC_WEIGHTS=./weights.txt \
    ../custom-fuzzer/afl-clang-lto target.c -o target

Fuzz:
  AFL_FUNC_MAP=./funcmap.txt \
    ../custom-fuzzer/afl-fuzz -H weights.txt -i seeds -o out -- ./target @@

Expected call graph propagation:
  parse_header = 90 (user)
  validate_crc = 60 (user)
  process_input: propagated = 90/2 + 60/2 = 75
  main:          propagated = 90/4 + 60/4 = 37

Seeds:
  seed1: "HELLO WORLD" - goes to process_input path (starts with uppercase)
  seed2: "HDR!testdata" - hits full parse_header match
  seed3: "FB" - goes to fallback_handler (no weight)
