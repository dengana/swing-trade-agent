import pandas as pd
import pandas_ta as ta
from agent.state import AgentState

def calculate_indicators(state: AgentState):
    """
    取得したデータに対し、RSI (14日)、MACD、ボリンジャーバンド (2σ) を計算する
    """
    market_data = state.get("market_data", {})
    
    for ticker, df in market_data.items():
        if df.empty or len(df) < 30:
            continue
            
        # RSI (14)
        df.ta.rsi(length=14, append=True)
        
        # MACD (12, 26, 9)
        df.ta.macd(fast=12, slow=26, signal=9, append=True)
        
        # Bollinger Bands (20, 2σ)
        df.ta.bbands(length=20, std=2, append=True)

        # NaNをForward Fill または Backward Fill で補間
        df.bfill(inplace=True)

        market_data[ticker] = df
        
    state["market_data"] = market_data
    return state
