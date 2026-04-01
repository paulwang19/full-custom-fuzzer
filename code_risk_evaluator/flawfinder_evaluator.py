"""
Flawfinder + ctags 風險評估器

必要工具：ctags（未安裝時報錯退出）

流程：
  1. ctags 提取所有 C 函數的檔案與起始行號
  2. flawfinder 掃描專案，取得每個安全問題的行號與嚴重等級（1–5）
  3. 將 flawfinder hit 對應到所屬函數（hit 行號 >= 函數起始行號）
  4. 每個函數依 hit 的加權分數加總，正規化到 0–100

Hit 加權：
  Level 1 = 5 分、Level 2 = 10 分、Level 3 = 20 分、
  Level 4 = 40 分、Level 5 = 70 分

使用方式：
  python3 code_risk_evaluator/flawfinder_evaluator.py <project_path> <output_path>
"""

import csv
import io
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from base import CodeRiskEvaluator, FunctionInfo, RiskResult
from constants import clamp_score

# ------------------------------------------------------------------
# 評分參數
# ------------------------------------------------------------------

LEVEL_WEIGHTS: dict[int, float] = {
    1: 5,
    2: 10,
    3: 20,
    4: 40,
    5: 70,
}


# ------------------------------------------------------------------
# ctags 函數表
# ------------------------------------------------------------------

def _build_func_table(project_dir: str) -> dict[str, list[tuple[str, int]]]:
    """ctags 解析，回傳 abs_path -> [(func_name, start_line)]。未安裝 ctags 則報錯退出。"""
    ctags_bin = None
    for name in ('ctags', 'universal-ctags', 'exuberant-ctags'):
        try:
            r = subprocess.run(['which', name], capture_output=True, text=True)
            if r.returncode == 0:
                ctags_bin = r.stdout.strip()
                break
        except OSError:
            pass

    if not ctags_bin:
        print('錯誤：找不到 ctags，請先安裝（apt install universal-ctags）', file=sys.stderr)
        sys.exit(1)

    tags_file = '/tmp/_flawfinder_eval_tags.txt'
    cmd = [ctags_bin, '-R', '--languages=C', '--fields=+n', '--kinds-C=f', '-f', tags_file, project_dir]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f'錯誤：ctags 執行失敗：{r.stderr}', file=sys.stderr)
        sys.exit(1)

    symbols: dict[str, list[tuple[str, int]]] = defaultdict(list)
    with open(tags_file, errors='replace') as f:
        for line in f:
            if line.startswith('!'):
                continue
            parts = line.split('\t')
            if len(parts) < 4:
                continue
            name = parts[0]
            filepath = os.path.abspath(parts[1])
            for field in parts[3:]:
                m = re.match(r'line:(\d+)', field)
                if m:
                    symbols[filepath].append((name, int(m.group(1))))
                    break

    for fp in symbols:
        symbols[fp].sort(key=lambda x: x[1])
    return dict(symbols)


# ------------------------------------------------------------------
# Flawfinder
# ------------------------------------------------------------------

def _run_flawfinder(project_dir: str) -> list[dict]:
    """flawfinder --csv 掃描，回傳 hit 列表。"""
    uv_path = os.path.expanduser('~/.local/bin/uv')
    if not os.path.exists(uv_path):
        uv_path = 'uv'

    cmd = [uv_path, 'run', 'flawfinder', '--csv', '--minlevel=1', project_dir]
    cwd = str(Path(__file__).parent.parent)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    except OSError as e:
        print(f'flawfinder 執行失敗：{e}', file=sys.stderr)
        return []

    hits = []
    reader = csv.DictReader(io.StringIO(result.stdout))
    for row in reader:
        try:
            hits.append({
                'file':  os.path.abspath(row['File']),
                'line':  int(row['Line']),
                'level': int(row['Level']),
                'name':  row.get('Name', ''),
            })
        except (KeyError, ValueError):
            continue
    return hits


# ------------------------------------------------------------------
# 評估器實作
# ------------------------------------------------------------------

class FlawfinderEvaluator(CodeRiskEvaluator):
    """
    以 ctags + flawfinder 評估 C 專案中每個函數的安全風險。
    """

    def evaluate(self, project_path: Path) -> list[RiskResult]:
        project_dir = str(project_path)

        # Step 1：建立函數表
        func_table = _build_func_table(project_dir)

        # Step 2：執行 flawfinder
        hits = _run_flawfinder(project_dir)

        # Step 3：將 hit 對應到函數，累計加權分數
        # func_key = (abs_path, func_name, start_line)
        score_map: dict[tuple, float] = defaultdict(float)
        hit_detail: dict[tuple, list[dict]] = defaultdict(list)

        for hit in hits:
            fpath = hit['file']
            funcs = func_table.get(fpath, [])
            best_name, best_start = None, -1
            for fname, fstart in funcs:
                if fstart <= hit['line'] and fstart > best_start:
                    best_name, best_start = fname, fstart
            if best_name is None:
                continue
            key = (fpath, best_name, best_start)
            score_map[key] += LEVEL_WEIGHTS.get(hit['level'], 0)
            hit_detail[key].append({'line': hit['line'], 'level': hit['level'], 'name': hit['name']})

        # Step 4：收集所有函數的原始分數
        entries = []
        for abs_path, funcs in func_table.items():
            rel_path = os.path.relpath(abs_path, project_dir)
            for i, (fname, start_line) in enumerate(funcs):
                end_line = funcs[i + 1][1] - 1 if i + 1 < len(funcs) else start_line
                key = (abs_path, fname, start_line)
                entries.append((
                    FunctionInfo(name=fname, file_path=rel_path,
                                 start_line=start_line, end_line=end_line),
                    score_map.get(key, 0.0),
                    hit_detail.get(key, []),
                ))

        # Step 5：正規化到 0–100
        max_raw = max((raw for _, raw, _ in entries), default=0.0)

        results: list[RiskResult] = []
        for func_info, raw_score, func_hits in entries:
            normalized = (raw_score / max_raw * 100) if max_raw > 0 else 0.0
            results.append(RiskResult(
                function=func_info,
                score=clamp_score(normalized),
                details={
                    'hit_count': len(func_hits),
                    'raw_score': raw_score,
                    'hits':      func_hits,
                },
            ))

        results.sort(key=lambda r: r.score, reverse=True)
        return results


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f'用法：python3 {sys.argv[0]} <project_path> <output_path>')
        sys.exit(1)

    project_path = Path(sys.argv[1]).resolve()
    output_path  = Path(sys.argv[2]).resolve()

    if not project_path.exists():
        print(f'錯誤：專案路徑不存在：{project_path}', file=sys.stderr)
        sys.exit(1)

    results = FlawfinderEvaluator().run(project_path, output_path)

    total = len(results)
    hit_funcs = [r for r in results if r.score > 0]
    avg = sum(r.score for r in results) / total if total else 0

    print(f"\n{'='*55}")
    print(f'共 {total} 個函數，有 hit 的函數 {len(hit_funcs)} 個，平均風險分數 {avg:.1f}')
    print('\n--- 最高風險函數（Top 10）---')
    for r in results[:10]:
        d = r.details
        print(
            f'  [{r.score:5.1f}] {r.function.file_path}:{r.function.name}'
            f'  (hits={d["hit_count"]})'
        )
    print(f"{'='*55}")
    print(f'\n結果已寫入：{output_path}')
