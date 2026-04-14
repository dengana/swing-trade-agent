import pandas as pd
from agent.state import AgentState

def pre_screen(state: AgentState):
    """
    全銘柄の計算済みデータに対して、プログラム的（機械的）な足切りフィルタを適用する。
    LLM APIのコストと時間を削減するため、高優位な条件を満たした銘柄のみを抽出する。
    """
    market_data = state.get("market_data", {})
    screened_data = {}
    
    for ticker, df in market_data.items():
        if df.empty or len(df) < 60:
            continue
            
        try:
            # 必要な列を動的に取得
            close_col = 'Close'
            vol_col = 'Volume'
            rsi_col = next((c for c in df.columns if c.startswith('RSI')), None)
            macd_col = next((c for c in df.columns if c.startswith('MACD_')), None)
            macds_col = next((c for c in df.columns if c.startswith('MACDs_')), None)
            macdh_col = next((c for c in df.columns if c.startswith('MACDh_')), None)
            bbl_col = next((c for c in df.columns if c.startswith('BBL')), None)
            bbu_col = next((c for c in df.columns if c.startswith('BBU')), None)
            
            if not all([rsi_col, macdh_col, bbl_col, bbu_col, macd_col, macds_col]):
                continue
                
            recent = df.tail(1).iloc[0]
            
            # --- フィルタ条件（プロフェショナル仕様の一次審査） ---
            
            # 1. 流動性と価格のフィルタ (5日平均出来高 > 30,000株 ＆ 価格 > 100 JPY)
            avg_vol = df[vol_col].tail(5).mean()
            if avg_vol >= 30000 and recent[close_col] >= 100:
                # RSI値を使ってソートするために保持
                screened_data[ticker] = (df, recent[rsi_col])
                
        except Exception as e:
            continue
            
    # RSIの低い順（売られすぎ）にソートして上位20銘柄に絞り込む
    sorted_candidates = sorted(screened_data.items(), key=lambda x: x[1][1])
    top_candidates = sorted_candidates[:20]
    
    # 元の辞書形式に戻す (ticker: df)
    final_screened_data = {ticker: data[0] for ticker, data in top_candidates}
            
    print(f"Pre-screening complete: {len(market_data)} total -> {len(final_screened_data)} candidates passed.")
    
    # 足切り通過銘柄のみに上書きして次（LLM判定）へ渡す
    state["market_data"] = final_screened_data
    return state
