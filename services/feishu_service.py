import json
import requests

def send_feishu_message(webhook_url, content):
    """发送飞书消息"""
    
    content = content.replace("@所有人", "<at user_id='all'>所有人</at>")
    headers = {"Content-Type": "application/json",
                "charset": "utf-8"}
    data = {
        "msg_type": "text",
        "content": {
            "text": content
        }
    }
    msg_encode = json.dumps(data, ensure_ascii=True).encode("utf-8")
    
    try:
        response = requests.post(webhook_url, headers=headers, data=msg_encode)
        response.raise_for_status()
        return True, "消息发送成功"
    except Exception as e:
        return False, f"消息发送失败: {str(e)}"
