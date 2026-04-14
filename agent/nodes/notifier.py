import os
import requests
import json
from agent.state import AgentState

def notifier(state: AgentState):
    """
    判定がBUYの銘柄をスコア順にソートし、上位3銘柄を抽出してLINE Messaging APIでPush通知を送信する
    """
    decisions = state.get("decisions", {})
    
    buys = [(ticker, data) for ticker, data in decisions.items() if data.get("decision") == "BUY"]
    buys.sort(key=lambda x: x[1].get("score", 0), reverse=True)
    top_3_buys = buys[:3]
    
    line_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    line_user_id = os.getenv("LINE_USER_ID")
    
    if not line_token or not line_user_id:
        print("Warning: LINE API keys are not set. Cannot send notification.")
        return state
        
    if not top_3_buys:
        print("No BUY signals. Sending 'no signal' notification.")
        message_text = "✅ 【今週のスキャン完了】\n\n銘柄を解析しましたが、現在の相場環境において推奨できる銘柄はひとつも検出されませんでした。\n\n無理なエントリーは控え、キャッシュを温存することをお勧めします。"
    else:
        # 通知メッセージの構築（該当銘柄がある場合）
        message_lines = ["🚨 【注目銘柄 検知レポート】 🚨", "以下の銘柄で優位性の高いシグナルが点灯しました（上位最大3銘柄）。\n"]
        
        company_names = {}
        if os.path.exists("company_names.json"):
            with open("company_names.json", "r", encoding="utf-8") as f:
                company_names = json.load(f)
        
        for ticker, info in top_3_buys:
            score = info.get('score', 0)
            comp_name = company_names.get(ticker, "")
            name_display = f" {comp_name}" if comp_name else ""
            
            message_lines.append(f"📈 **{ticker}**{name_display} (スコア: {score}/100)")
            message_lines.append(f"⏳ 保有期間の目安: {info.get('holding_period', '-')}")
            message_lines.append(f"🚀 エントリー時の株価: {info.get('entry_price', '-')}")
            message_lines.append(f"🎯 利確目標: {info['target_price']}")
            message_lines.append(f"🛡️ 損切り: {info['stop_loss']}")
            message_lines.append(f"📝 理由: {info['reason']}\n")
            
        message_text = "\n".join(message_lines)
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {line_token}"
    }
    
    payload = {
        "to": line_user_id,
        "messages": [
            {
                "type": "text",
                "text": message_text
            }
        ]
    }
    
    print("Sending LINE notification...")
    url = "https://api.line.me/v2/bot/message/push"
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        print("Notification sent successfully.")
    except Exception as e:
        print(f"Error sending LINE notification: {e}")
        if 'response' in locals():
            print(response.text)
            
    return state
