from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict):
    tickers: List[str]                  # 分析対象の銘柄リスト
    market_data: Dict[str, Any]         # {"AAPL": pd.DataFrame, ...}
    decisions: Dict[str, Dict[str, str]]# {"AAPL": {"decision": "STRONG BUY", "target_price": "...", "stop_loss": "...", "reason": "..."}}
    chart_paths: Dict[str, str]         # {"AAPL": "charts/AAPL.png"}
