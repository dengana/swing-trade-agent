import json
import os
import pandas as pd
import certifi
import shutil
from tqdm import tqdm
import time
import pandas as pd
import yfinance as yf
import json
import os
from agent.state import AgentState

def fetch_data(state: AgentState):
    """
    tickersリストから全銘柄の直近6ヶ月の日足データを一括取得する
    （数千銘柄のAPI制限を防ぐため、チャンクごとに並列ダウンロード）
    """
    tickers = state.get("tickers", [])
    if not tickers:
        print("No tickers to fetch.")
        return state

    # --- Windowsマルチバイトパス問題（curl 77エラー）の回避策 ---
    temp_dir = os.environ.get("TEMP", "C:\\temp")
    temp_cert_path = os.path.join(temp_dir, "cacert.pem")
    try:
        if not os.path.exists(temp_cert_path):
            shutil.copy2(certifi.where(), temp_cert_path)
        os.environ["CURL_CA_BUNDLE"] = temp_cert_path
    except Exception as e:
        print(f"Warning: Could not set up temporary CA bundle: {e}")
    # -------------------------------------------------------------

    market_data = state.get("market_data", {})
    
    # 既にデータがあるティッカーは除外
    tickers_to_fetch = [t for t in tickers if t not in market_data]
    
    if not tickers_to_fetch:
        return state

    print(f"Fetching data for {len(tickers_to_fetch)} tickers...")
    
    # 500件ずつチャンク分割して一括取得（レートリミット対策）
    chunk_size = 500
    chunks = [tickers_to_fetch[i:i + chunk_size] for i in range(0, len(tickers_to_fetch), chunk_size)]
    
    for idx, chunk in enumerate(chunks):
        print(f"Downloading chunk {idx+1}/{len(chunks)}...")
        try:
            # group_by='ticker' でティッカーごとに列がまとまる
            bulk_df = yf.download(chunk, period="6mo", interval="1d", group_by='ticker', threads=True, progress=False)
            
            # yfinanceの仕様：1件リクエストと複数件リクエストでDataFrameの構造が変わる
            if len(chunk) == 1:
                ticker = chunk[0]
                if not bulk_df.empty:
                    market_data[ticker] = bulk_df
            else:
                for ticker in chunk:
                    try:
                        # bulk_dfのマルチインデックスから当該ティッカーのDataFrameを切り出す
                        df_ticker = bulk_df[ticker].dropna(how='all')
                        if not df_ticker.empty:
                            market_data[ticker] = df_ticker
                    except KeyError:
                        pass # データが存在しない場合
        except Exception as e:
            print(f"Error fetching chunk {idx+1}: {e}")
            
        # 連続リクエストでブロックされないための休止
        time.sleep(2)

    state["market_data"] = market_data
    return state
