# 風險分數範圍常數
# 若需調整評分尺度，修改此處即可，評估邏輯會自動對應

RISK_SCORE_MIN: int = 0    # 最低風險（無風險）
RISK_SCORE_MAX: int = 100  # 最高風險


def clamp_score(score: float) -> float:
    """將分數限制在合法範圍內。"""
    return max(RISK_SCORE_MIN, min(RISK_SCORE_MAX, score))
