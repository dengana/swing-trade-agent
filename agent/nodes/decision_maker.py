import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from agent.state import AgentState

class TradeDecision(BaseModel):
    decision: str = Field(description="Trade decision: only 'STRONG BUY' or 'HOLD'")
    target_price: str = Field(description="Target profit price (🎯 利確目標価格) if STRONG BUY, else '-'")
    stop_loss: str = Field(description="Stop loss price (🛡️ 損切り価格) if STRONG BUY, else '-'")
    reason: str = Field(description="Brief reason for the decision in Japanese")

def decision_maker(state: AgentState):
    """
    LLMにテクニカル指標を入力し、厳格なトレード判定を行う
    """
    market_data = state.get("market_data", {})
    decisions = {}
    
    # Initialize LLM
    # Assuming OPENAI_API_KEY is in environment variables (loaded in main.py)
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    structured_llm = llm.with_structured_output(TradeDecision)

    system_prompt = """あなたは世界トップクラスのクオンツファンドのリードエンジニアであり、冷徹で厳格なトレーダーです。
提供された直近の価格データとテクニカル指標（RSI, MACD, Bollinger Bands）を分析し、スイングトレード（数日〜数週間の保有）の可否を判定してください。

【超・厳格なリスク管理制約】
1. テクニカル的に極めて優位性が高く、反発や上昇の公算が非常に強い局面でのみ『STRONG BUY』を出力してください。
2. 少しでも懸念材料がある場合、トレンドが不明確な場合、またはリスクリワードが見合わない場合は、容赦なく『HOLD』としてください。
3. ポジションを持たないことも立派なトレードです。「BUY」や「SELL」といった曖昧な評価は一切不要です。『STRONG BUY』か『HOLD』の2択です。
4. STRONG BUYの場合、具体的な数値を含む「🎯 利確目標価格」と「🛡️ 損切り価格」を必ずPromptから算出または推測して設定してください。
5. 出力理由(reason)は必ず日本語で、なぜその判断に至ったかを端的なプロの視点で記載してください。
"""

    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("user", "銘柄: {ticker}\n直近のデータとテクニカル指標の要約:\n{data_summary}")
    ])

    for ticker, df in market_data.items():
        if df.empty:
            decisions[ticker] = {"decision": "HOLD", "target_price": "-", "stop_loss": "-", "reason": "データ不足"}
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
                "target_price": result.target_price,
                "stop_loss": result.stop_loss,
                "reason": result.reason
            }
        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")
            decisions[ticker] = {"decision": "HOLD", "target_price": "-", "stop_loss": "-", "reason": "分析エラー"}

    state["decisions"] = decisions
    return state
