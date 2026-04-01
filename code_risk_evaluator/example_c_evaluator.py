"""
範例評估器：C 程式碼風險評估

掃描專案內所有 .c 和 .h 檔案，對每個函數以三個指標計算風險分數：
  1. 函數長度（行數）              — 越長越難維護
  2. 分支數（if/for/while/switch）  — 越多越複雜
  3. 巨集呼叫數                    — 巨集會隱藏邏輯，增加風險

使用方式：
  python3 code_risk_evaluator/example_c_evaluator.py <project_path> <output_path>
"""

import re
import sys
from pathlib import Path

from base import CodeRiskEvaluator, FunctionInfo, RiskResult
from constants import RISK_SCORE_MAX, clamp_score

# ------------------------------------------------------------------
# 評分參數（可依需求調整）
# ------------------------------------------------------------------

LINES_PER_POINT: int   = 5     # 每 5 行算 1 分
MAX_LINE_SCORE: float  = 40.0  # 長度分上限

BRANCH_PER_POINT: int  = 1     # 每個分支算 1 分
MAX_BRANCH_SCORE: float = 40.0 # 分支分上限

MACRO_PER_POINT: int   = 2     # 每個巨集呼叫算 2 分
MAX_MACRO_SCORE: float = 20.0  # 巨集分上限

# 判定為函數定義的 regex：
#   - 不以 # / / * 開頭（排除前置處理器、註解）
#   - 回傳型別 + 函數名稱 + 括號 + 左大括號（可在下一行）
_FUNC_DEF_RE = re.compile(
    r'^(?![\s#/*])[\w\s\*]+?\b(\w+)\s*\([^;]*\)\s*$'
)

# 分支關鍵字
_BRANCH_RE = re.compile(r'\b(if|else\s+if|for|while|switch|case)\b')

# 巨集呼叫：全大寫識別符後接 (
_MACRO_CALL_RE = re.compile(r'\b([A-Z_][A-Z0-9_]{1,})\s*\(')


# ------------------------------------------------------------------
# 輔助函數
# ------------------------------------------------------------------

def _extract_functions(source: str, rel_path: str) -> list[FunctionInfo]:
    """從 C 原始碼中擷取所有函數定義。"""
    lines = source.splitlines()
    functions: list[FunctionInfo] = []
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        # 嘗試比對函數簽名（本行無大括號，下一行才是 {）
        if _FUNC_DEF_RE.match(line):
            # 找到開頭的 {
            brace_line = i
            while brace_line < len(lines) and '{' not in lines[brace_line]:
                brace_line += 1
            if brace_line >= len(lines):
                i += 1
                continue

            # 追蹤大括號配對找函數結尾
            depth = 0
            start = i + 1  # 1-based
            end = brace_line + 1

            for j in range(brace_line, len(lines)):
                depth += lines[j].count('{') - lines[j].count('}')
                if depth == 0:
                    end = j + 1  # 1-based
                    break

            match = _FUNC_DEF_RE.match(line)
            name = match.group(1) if match else line.strip()
            func_source = "\n".join(lines[i:end])

            functions.append(FunctionInfo(
                name=name,
                file_path=rel_path,
                start_line=start,
                end_line=end,
                source=func_source,
            ))
            i = end
            continue

        i += 1

    return functions


def _count_branches(source: str) -> int:
    """計算函數中的分支關鍵字數。"""
    return len(_BRANCH_RE.findall(source))


def _count_macro_calls(source: str) -> int:
    """計算函數中的巨集呼叫數（全大寫識別符 + 括號）。"""
    return len(_MACRO_CALL_RE.findall(source))


# ------------------------------------------------------------------
# 評估器實作
# ------------------------------------------------------------------

class CComplexityEvaluator(CodeRiskEvaluator):
    """
    以函數長度、分支複雜度與巨集呼叫數評估 C 程式碼風險。
    """

    def evaluate(self, project_path: Path) -> list[RiskResult]:
        """遍歷所有 .c 和 .h 檔案，擷取函數並計算風險分數。"""
        results: list[RiskResult] = []

        for c_file in sorted(project_path.rglob("*.[ch]")):
            try:
                source = c_file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            rel_path = str(c_file.relative_to(project_path))
            for func in _extract_functions(source, rel_path):
                line_count   = func.end_line - func.start_line + 1
                branch_count = _count_branches(func.source)
                macro_count  = _count_macro_calls(func.source)

                line_score   = min(line_count   / LINES_PER_POINT,  MAX_LINE_SCORE)
                branch_score = min(branch_count * BRANCH_PER_POINT, MAX_BRANCH_SCORE)
                macro_score  = min(macro_count  * MACRO_PER_POINT,  MAX_MACRO_SCORE)

                scale = RISK_SCORE_MAX / (MAX_LINE_SCORE + MAX_BRANCH_SCORE + MAX_MACRO_SCORE)
                raw_score = (line_score + branch_score + macro_score) * scale

                results.append(RiskResult(
                    function=func,
                    score=clamp_score(raw_score),
                    details={
                        "line_count":   line_count,
                        "branch_count": branch_count,
                        "macro_count":  macro_count,
                        "line_score":   round(line_score,   2),
                        "branch_score": round(branch_score, 2),
                        "macro_score":  round(macro_score,  2),
                    },
                ))

        return results


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"用法：python3 {sys.argv[0]} <project_path> <output_path>")
        sys.exit(1)

    project_path = Path(sys.argv[1]).resolve()
    output_path  = Path(sys.argv[2]).resolve()

    if not project_path.exists():
        print(f"錯誤：專案路徑不存在：{project_path}", file=sys.stderr)
        sys.exit(1)

    results = CComplexityEvaluator().run(project_path, output_path)

    total = len(results)
    if total == 0:
        print("未找到任何函數")
        sys.exit(0)

    avg  = sum(r.score for r in results) / total
    top5 = sorted(results, key=lambda r: r.score, reverse=True)[:5]

    print(f"\n{'='*50}")
    print(f"共 {total} 個函數，平均風險分數 {avg:.1f}")
    print("\n--- 最高風險函數（Top 5）---")
    for r in top5:
        d = r.details
        print(
            f"  [{r.score:5.1f}] {r.function.file_path}:{r.function.name}"
            f"  (行數={d['line_count']}, 分支={d['branch_count']}, 巨集={d['macro_count']})"
        )
    print(f"{'='*50}")
    print(f"\n結果已寫入：{output_path}")
