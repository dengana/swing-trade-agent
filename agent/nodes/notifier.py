import os
import requests
from agent.state import AgentState

def notifier(state: AgentState):
    """
    判定がSTRONG BUYの銘柄のみ抽出し、LINE Messaging APIでPush通知を送信する
    """
    decisions = state.get("decisions", {})
    
    strong_buys = {ticker: data for ticker, data in decisions.items() if data["decision"] == "STRONG BUY"}
    
    if not strong_buys:
        print("No STRONG BUY signals. Skipping notification.")
        return state
        
    line_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    line_user_id = os.getenv("LINE_USER_ID")
    
    if not line_token or not line_user_id:
        print("Warning: LINE API keys are not set. Cannot send notification.")
        return state
        
    # 通知メッセージの構築
    message_lines = ["🚨 【厳格アルゴ 検知レポート】 🚨", "以下の銘柄で極めて優位性の高いシグナルが点灯しました。\n"]
    
    for ticker, info in strong_buys.items():
        message_lines.append(f"📈 **{ticker}**")
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
