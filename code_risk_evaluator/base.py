"""
code-risk-evaluator 抽象介面

使用方式：
    繼承 CodeRiskEvaluator，實作 evaluate()，
    即可接入 CLI 流程與輸出格式。
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

from constants import clamp_score


# ---------------------------------------------------------------------------
# 資料模型
# ---------------------------------------------------------------------------

@dataclass
class FunctionInfo:
    """描述一個從原始碼中擷取出的函數。"""
    name: str           # 函數名稱
    file_path: str      # 相對於專案根目錄的路徑
    start_line: int     # 函數起始行號（1-based）
    end_line: int       # 函數結束行號（1-based）
    source: str = ""    # 函數原始碼（可選，供評估器使用）


@dataclass
class RiskResult:
    """單一函數的風險評估結果。"""
    function: FunctionInfo
    score: float                        # 分數範圍：[RISK_SCORE_MIN, RISK_SCORE_MAX]
    details: dict[str, Any] = field(default_factory=dict)  # 評估器自訂細節

    def __post_init__(self) -> None:
        self.score = clamp_score(self.score)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# 抽象介面
# ---------------------------------------------------------------------------

class CodeRiskEvaluator(ABC):
    """
    程式碼風險評估器抽象基底類別。

    實作子類別時需覆寫：
        evaluate(project_path) — 掃描專案並回傳所有函數的風險評估結果

    可選覆寫：
        write_output(results, output_path) — 自訂輸出格式（預設為 JSON）
    """

    @abstractmethod
    def evaluate(self, project_path: Path) -> list[RiskResult]:
        """
        掃描 project_path 下的程式碼，並對每個函數計算風險分數。

        Args:
            project_path: 專案根目錄路徑

        Returns:
            RiskResult 的列表，每個元素代表一個函數的評估結果
        """
        ...

    def write_output(self, results: list[RiskResult], output_path: Path) -> None:
        """
        將評估結果寫入輸出檔案。預設為 JSON 格式。

        子類別可覆寫此方法改為 CSV、HTML 等其他格式。
        """
        payload = {
            "total_functions": len(results),
            "results": [r.to_dict() for r in results],
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    def run(self, project_path: Path, output_path: Path) -> list[RiskResult]:
        """
        執行完整的掃描 → 評估 → 輸出流程。

        Args:
            project_path: 程式碼專案根目錄
            output_path:  結果輸出檔案路徑

        Returns:
            所有函數的 RiskResult 列表
        """
        results = self.evaluate(project_path)
        self.write_output(results, output_path)
        return results
