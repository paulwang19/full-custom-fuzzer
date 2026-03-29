# custom-fuzzer 專案摘要

基於最新版 AFL++ 修改的自製 argv fuzzer，參考 CarpetFuzz-fuzzer 的做法，核心目的是在單次 fuzzing campaign 中自動測試不同命令列選項組合。

## 核心機制

- **`-j seeds_dir`**：使用者提供種子目錄（與 `-i` 互斥），目錄下每個子目錄代表一組 argv 組合，各含 `.argv` 檔（指定命令列參數）及 seed 檔案
- **`.argvs` 檔案**：以 null-separated binary 格式寫入當前 argv 組合
- **LLVM 插樁**：在目標程式 `main()` 入口注入 `__afl_parse_argv()`，讀取 `.argvs` 檔案替換 argc/argv
- **Queue 追蹤**：每個 queue entry 記錄 `argvs_idx`，crash/queue 檔名含 `argv:XXXXXX` 標記

## 兩階段執行

1. **Argv 遍歷階段**（`fuzz_one_with_argvs()`，只跑一次）：對每個 queue entry x 每個 argv 組合，做 havoc 變異
2. **正常 fuzzing 階段**：每個 queue entry 使用自己記錄的 `argvs_idx` 對應的 argv 組合

## 修改的檔案（相對於原版 AFL++）

| 檔案 | 修改內容 |
|---|---|
| `src/afl-fuzz-argv.c` | **新增**，核心實作：`init_argv_list()`, `write_argvs_file()`, `fuzz_one_with_argvs()` |
| `src/afl-fuzz.c` | `-j` 參數解析、初始化、主迴圈整合（3 個插入點）、清理 |
| `src/afl-fuzz-queue.c` | 新 queue entry 記錄 `argvs_idx` |
| `src/afl-fuzz-bitmap.c` | crash/queue 檔名加上 `argv:XXXXXX` |
| `src/afl-forkserver.c` | 複製 forkserver 時傳遞 `argvs_file` |
| `include/afl-fuzz.h` | 新增資料結構：`struct argv_list`, `STAGE_ARGV`, 相關欄位 |
| `include/forkserver.h` | 新增 `argvs_file` 欄位 |
| `instrumentation/afl-compiler-rt.o.c` | 新增 `__afl_parse_argv()` runtime 函式 |
| `instrumentation/SanitizerCoverageLTO.so.cc` | LTO 模式插樁 |
| `instrumentation/SanitizerCoveragePCGUARD.so.cc` | PC-Guard 模式插樁 |

## 如何辨識 My-Fuzzer 的修改

在既有的 AFL++ 原始碼中，所有 My-Fuzzer 的修改區塊都以註解標記包夾，依模組區分：

**argv 模組**：
```c
// My-Fuzzer argv support modified
... 修改的程式碼 ...
// My-Fuzzer argv support end
```

**Function-weight 模組**：
```c
// My-Fuzzer func-weight module modified
... 修改的程式碼 ...
// My-Fuzzer func-weight module end
```

可用以下指令快速定位所有修改處：

```bash
grep -rn "My-Fuzzer" custom-fuzzer/src/ custom-fuzzer/include/ custom-fuzzer/instrumentation/
```

全新新增的檔案（`src/afl-fuzz-argv.c`、`src/afl-fuzz-funcweight.c`）整個檔案都是 My-Fuzzer 的實作，沒有標記。

## Function-Weight 模組

函式層級權重能量排程（`-H`），讓觸碰高權重函式的種子獲得更多變異能量，並隨覆蓋率飽和自動衰減。僅支援 LTO 模式。

### 修改的檔案

| 檔案 | 修改內容 |
|---|---|
| `src/afl-fuzz-funcweight.c` | **新增**，核心邏輯：`init_func_weights()`, `calc_func_weight_score()`, `record_func_hits()`, `update_func_weight_saturation()`, `cleanup_func_weights()` |
| `src/afl-fuzz.c` | `-H` 參數解析、初始化、主迴圈衰減更新、cleanup |
| `src/afl-fuzz-queue.c` | `calculate_score()` 加入權重乘數、`add_to_queue()` 記錄 `func_hits` |
| `include/afl-fuzz.h` | `func_weight_entry` 結構、`afl_state_t` 權重欄位、`queue_entry` 新增 `func_hits` |
| `include/envs.h` | 新增 `AFL_LLVM_FUNC_MAP_OUTPUT`、`AFL_LLVM_FUNC_WEIGHTS`、`AFL_FUNC_MAP` |
| `instrumentation/SanitizerCoverageLTO.so.cc` | 輸出映射檔 + call graph 權重傳播 |

### 使用方式

```bash
# 編譯（LTO 模式）
AFL_LLVM_FUNC_MAP_OUTPUT=funcmap.txt AFL_LLVM_FUNC_WEIGHTS=weights.txt \
  afl-clang-lto -O0 -fno-inline target.c -o target

# Fuzzing
AFL_FUNC_MAP=funcmap.txt afl-fuzz -H weights.txt -i seeds -o out -- ./target @@
```

詳細說明見 `docs/CUSTOM-DOC_func-weight-user-guide-zh-TW.md`。

## 與 CarpetFuzz 的主要差異

- `-K` 改為 `-j`（新版 AFL++ 的 `-K` 已被 GUI mode 佔用）
- 用 `extern` 宣告 `choose_block_len()` 避免 linker 多重定義錯誤
- 更新 LLVM API 以相容 LLVM 15+

## 使用方式

```bash
afl-fuzz -j seeds_dir -o out -- ./target @@
```

其中 `seeds_dir` 的結構如下：

```
seeds_dir/
├── combo_0_a/
│   ├── .argv        # 內容如：-a @@
│   └── seed1        # seed 檔案
├── combo_1_b/
│   ├── .argv        # 內容如：-b @@
│   └── seed1
└── ...
```

注意：`-j` 取代 `-i`，兩者不可同時使用。

## Git 歷史

初始 commit `40be571` 為原版 AFL++，後續 commits 依序新增 argv fuzzing 功能，最終 `f19aee3` 重命名所有標記為 My-Fuzzer。
