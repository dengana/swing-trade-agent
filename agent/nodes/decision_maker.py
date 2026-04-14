import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from agent.state import AgentState

class TradeDecision(BaseModel):
    decision: str = Field(description="Trade decision: only 'BUY' or 'HOLD'")
    score: int = Field(description="Confidence score from 0 to 100")
    holding_period: str = Field(description="Expected holding period (⏳ 保有期間の目安) (e.g., '3〜5日', '1〜2週間')")
    entry_price: str = Field(description="Recommended entry price (🚀 エントリー時の株価) if BUY, else '-'")
    target_price: str = Field(description="Target profit price (🎯 利確目標価格) if BUY, else '-'")
    stop_loss: str = Field(description="Stop loss price (🛡️ 損切り価格) if BUY, else '-'")
    reason: str = Field(description="Brief reason for the decision in Japanese")

def decision_maker(state: AgentState):
    """
    LLMにテクニカル指標を入力し、トレード判定を行う
    """
    market_data = state.get("market_data", {})
    decisions = {}
    
    # Initialize LLM
    # Assuming OPENAI_API_KEY is in environment variables (loaded in main.py)
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    structured_llm = llm.with_structured_output(TradeDecision)

    system_prompt = """あなたは経験豊富な株式トレーダーです。
提供された直近の価格データとテクニカル指標（RSI, MACD, Bollinger Bands）を分析し、スイングトレード（数日〜数週間の保有）の戦略を立案してください。

【トレード判定について】
1. 相場環境にかかわらず、与えられた銘柄でトレードする場合の最適な『BUY』戦略を必ず立案してください。判定(decision)は常に『BUY』としてください。
2. トレードにおける優位性・自信度を 0 から 100 の「score」（スコアが高いほど勝率が高いと判断）として出力してください。
3. 具体的な数値を含む「🚀 エントリー時の株価」「🎯 利確目標価格」「🛡️ 損切り価格」および「⏳ 保有期間の目安」を必ず設定してください。エントリー時の株価は直近のClose価格やテクニカルな反発ポイントなどを参考に設定してください。
4. 出力理由(reason)は必ず日本語で、なぜその判断（スコア、利確、損切りの設定）に至ったかを端的に記載してください。
"""

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "銘柄: {ticker}\n直近のデータとテクニカル指標の要約:\n{data_summary}")
    ])

    for ticker, df in market_data.items():
        if df.empty:
            decisions[ticker] = {"decision": "HOLD", "score": 0, "holding_period": "-", "entry_price": "-", "target_price": "-", "stop_loss": "-", "reason": "データ不足"}
            continue
            
        # Extract recent rows for the LLM
        recent_df = df.tail(5)
        
        # 動的に指標の列名を取得する（pandas_taのバージョンによる名前違いを吸収するため）
        display_cols = ['Close', 'Volume']
        for prefix in ['RSI', 'MACD', 'BBL', 'BBM', 'BBU']:
            # 指定のプレフィックスで始まる列をすべて抽出（重複を避けるためにリスト内包表記）
            cols_found = [col for col in df.columns if col.startswith(prefix)]
            display_cols.extend(cols_found)
            
        # 必要な列だけ抽出して文字列化
        display_cols = list(dict.fromkeys(display_cols)) # 重複排除
        
        try:
            data_summary = recent_df[display_cols].to_string()
        except KeyError:
            data_summary = recent_df.to_string() # 万が一列が見つからなければ全体を入れる
        
        chain = prompt_template | structured_llm
        
        try:
            print(f"Analyzing {ticker} with LLM...")
            result = chain.invoke({"ticker": ticker, "data_summary": data_summary})
            decisions[ticker] = {
                "decision": result.decision,
                "score": result.score,
                "holding_period": result.holding_period,
                "entry_price": result.entry_price,
                "target_price": result.target_price,
                "stop_loss": result.stop_loss,
                "reason": result.reason
            }
        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")
            decisions[ticker] = {"decision": "HOLD", "score": 0, "holding_period": "-", "entry_price": "-", "target_price": "-", "stop_loss": "-", "reason": "分析エラー"}

    state["decisions"] = decisions
    return state
