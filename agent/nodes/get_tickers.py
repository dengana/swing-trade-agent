import pandas as pd
import json
import os
from agent.state import AgentState

def get_tickers(state: AgentState):
    """
    JPX（日本取引所グループ）の公開Excelから全上場銘柄を取得し、yfinance用のティッカー（.T付き）を生成する。
    負荷軽減のため、1度取得したら tickers.json に保存してキャッシュする。
    """
    tickers_file = "tickers.json"
    
    # すでに多数の銘柄が存在する場合はキャッシュを利用（テスト時はリストを削除すれば再取得される）
    if os.path.exists(tickers_file):
        with open(tickers_file, "r", encoding="utf-8") as f:
            tickers = json.load(f)
            if len(tickers) > 100:
                print(f"Loaded {len(tickers)} tickers from cache.")
                state["tickers"] = tickers
                return state

    print("Fetching latest JPX listed companies list...")
    jpx_url = "https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xls"
    
    try:
        # JPXのExcelをダウンロード（xlrd ライブラリが必要）
        df = pd.read_excel(jpx_url)
        
        # 'コード' 列からティッカーシンボルを生成（yfinanceの日本株は <コード>.T）
        # 普通株式のみを抽出（ETFなどは一旦除外）するため '市場・商品区分' 等でフィルタも可能ですが
        # 今回は全コードを対象とします。
        raw_codes = df['コード'].astype(str).tolist()
        raw_names = df['銘柄名'].astype(str).tolist()
        
        tickers = []
        company_names = {}
        for code, name in zip(raw_codes, raw_names):
            # 4桁のコードのみを対象（インデックス等を除く）
            if len(code) == 4 and code.isdigit():
                ticker = f"{code}.T"
                tickers.append(ticker)
                company_names[ticker] = name
                
        # 保存
        with open(tickers_file, "w", encoding="utf-8") as f:
            json.dump(tickers, f, indent=4)
            
        with open("company_names.json", "w", encoding="utf-8") as f:
            json.dump(company_names, f, indent=4, ensure_ascii=False)
            
        print(f"Successfully fetched {len(tickers)} Japanese stock tickers.")
        state["tickers"] = tickers
        
    except Exception as e:
        print(f"Error fetching JPX data: {e}")
        # フォールバック: キャッシュがあればそれを使う
        if os.path.exists(tickers_file):
            with open(tickers_file, "r", encoding="utf-8") as f:
                state["tickers"] = json.load(f)
        else:
            state["tickers"] = ["7203.T", "6758.T", "9984.T"] # デフォルトのトヨタ、ソニー、SBG
            
    return state
