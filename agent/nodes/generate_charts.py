import os
import mplfinance as mpf
from agent.state import AgentState

def generate_charts(state: AgentState):
    """
    全銘柄について、ローソク足、MACD、ボリンジャーバンドを描画したチャートを生成し保存する
    """
    market_data = state.get("market_data", {})
    chart_paths = {}
    
    os.makedirs("charts", exist_ok=True)
    
    for ticker, df in market_data.items():
        if df.empty or len(df) < 50:
            continue
            
        print(f"Generating chart for {ticker}...")
        save_path = f"charts/{ticker}.png"
        
        try:
            # 直近N日のデータを描画
            plot_df = df.tail(60)
            
            # 動的に列名を取得
            bbu_col = next((c for c in plot_df.columns if c.startswith('BBU')), None)
            bbl_col = next((c for c in plot_df.columns if c.startswith('BBL')), None)
            bbm_col = next((c for c in plot_df.columns if c.startswith('BBM')), None)
            
            macd_col = next((c for c in plot_df.columns if c.startswith('MACD_')), None)
            macds_col = next((c for c in plot_df.columns if c.startswith('MACDs_')), None)
            macdh_col = next((c for c in plot_df.columns if c.startswith('MACDh_')), None)

            addplots = []
            
            # ボリンジャーバンドのプロット設定
            if all([bbu_col, bbl_col, bbm_col]):
                addplots.extend([
                    mpf.make_addplot(plot_df[bbu_col], color='cornflowerblue'),
                    mpf.make_addplot(plot_df[bbl_col], color='cornflowerblue'),
                    mpf.make_addplot(plot_df[bbm_col], color='orange', linestyle='--')
                ])
                
            # MACDのプロット設定（パネル1に配置）
            if all([macd_col, macds_col, macdh_col]):
                addplots.extend([
                    mpf.make_addplot(plot_df[macd_col], panel=1, color='fuchsia', secondary_y=False),
                    mpf.make_addplot(plot_df[macds_col], panel=1, color='b', secondary_y=False),
                    mpf.make_addplot(plot_df[macdh_col], type='bar', width=0.7, panel=1, color='dimgray', alpha=1, secondary_y=False)
                ])
            
            mpf.plot(
                plot_df, 
                type='candle', 
                style='yahoo',
                addplot=addplots,
                volume=True,
                volume_panel=2,
                panel_ratios=(4, 2, 1),
                title=f"{ticker} - Daily Chart (BB, MACD)",
                savefig=dict(fname=save_path, dpi=150, bbox_inches='tight')
            )
            
            chart_paths[ticker] = save_path
            
        except Exception as e:
            print(f"Error generating chart for {ticker}: {e}")
            
    state["chart_paths"] = chart_paths
    return state
