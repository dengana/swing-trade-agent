import sys
from dotenv import load_dotenv
from agent.graph import create_agent

def main():
    # 環境変数の読み込み (.env)
    load_dotenv()
    
    print("Starting Autonomous Weekly Swing Trade Agent...")
    
    # グラフの構築
    app = create_agent()
    
    # 初期状態
    initial_state = {
        "tickers": [],
        "market_data": {},
        "decisions": {},
        "chart_paths": {}
    }
    
    # エージェント実行
    print("--- Execution Started ---")
    final_state = app.invoke(initial_state)
    print("--- Execution Finished ---")

if __name__ == "__main__":
    main()
