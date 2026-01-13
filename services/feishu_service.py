import json
import requests
from utils.logger import logger

def send_feishu_message(webhook_url, content):
    """发送飞书消息"""
    logger.info(f"发送飞书消息到: {webhook_url}")
    logger.debug(f"消息内容: {content[:50]}...")
    
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
        logger.info("飞书消息发送成功")
        return True, "消息发送成功"
    except Exception as e:
        logger.error(f"飞书消息发送失败: {str(e)}")
        return False, f"消息发送失败: {str(e)}"
