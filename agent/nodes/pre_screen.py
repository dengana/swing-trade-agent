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
            
            # 1. 流動性と価格のフィルタ (5日平均出来高 > 100,000株 ＆ 価格 > 100 JPY)
            avg_vol = df[vol_col].tail(5).mean()
            if avg_vol < 100000 or recent[close_col] < 100:
                continue
                
            is_oversold_reversal = False
            is_breakout = False
            
            # パターンA: ディープバリュー・リバーサル（売られすぎからの反発初動）
            # RSIが35以下、かつ価格がボリンジャーバンド下限付近(-2σ)、かつMACDヒストグラムが増加に転じた
            if recent[rsi_col] < 35 and recent[close_col] <= recent[bbl_col] * 1.02:
                # 1日前のMACDヒストグラムと比較
                prev_macdh = df[macdh_col].iloc[-2]
                if recent[macdh_col] > prev_macdh:
                    is_oversold_reversal = True
                    
            # パターンB: モメンタム・ブレイクアウト（ゴールデンクロス直後 ＆ ボリューム急増）
            if recent[macd_col] > recent[macds_col]: # MACD > Signal
                prev_macd = df[macd_col].iloc[-2]
                prev_macds = df[macds_col].iloc[-2]
                # 前日は MACD < Signal だった（＝たった今ゴールデンクロスした）
                if prev_macd <= prev_macds and recent[vol_col] > avg_vol * 1.5:
                    is_breakout = True
                    
            # どちらかのエッジを満たした銘柄のみを通過させる
            if is_oversold_reversal or is_breakout:
                screened_data[ticker] = df
                
        except Exception as e:
            continue
            
    print(f"Pre-screening complete: {len(market_data)} total -> {len(screened_data)} candidates passed.")
    
    # 足切り通過銘柄のみに上書きして次（LLM判定）へ渡す
    state["market_data"] = screened_data
    return state
