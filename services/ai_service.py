import requests
from openai import OpenAI
from datetime import datetime
from utils.logger import logger

def get_ai_news(url="http://127.0.0.1:4399/v2/ai-news"):
    """获取AI新闻"""
    logger.info(f"获取AI新闻，URL: {url}")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data['code'] == 200 and 'news' in data['data']:
            news_list = data['data']['news']
            logger.info(f"获取到 {len(news_list)} 条新闻")
            news_text = f"🤖【AI新闻播报】{data['data']['date']}\n\n"
            for i, news in enumerate(news_list, 1):
                news_text += f"{i}. {news['title']}\n"
                news_text += f"   {news['detail']}\n"
                news_text += f"   来源: {news['source']}\n"
                # 清理链接格式
                link = news.get('link', '').strip().replace('`', '')
                news_text += f"   链接: {link}\n\n"
            return True, news_text
        else:
            logger.error("获取新闻失败: 返回数据格式错误")
            return False, "获取新闻失败: 返回数据格式错误"
    except Exception as e:
        logger.error(f"获取新闻失败: {str(e)}")
        return False, f"获取新闻失败: {str(e)}"

def call_llm(api_url, api_key, prompt, model_name='deepseek-chat'):
    """调用大模型"""
    logger.info(f"调用大模型，API URL: {api_url}, 模型: {model_name}")
    try:
        client = OpenAI(api_key=api_key, base_url=api_url)
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": f"# 角色\n你是一位AI智能播报助手,能够根据要求播报内容。\n\n# 要求\n语言幽默，建议使用emoji # 系统时间:{time}"},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )

        logger.info("大模型调用成功")
        return True, response.choices[0].message.content
    except Exception as e:
        logger.error(f"调用大模型失败: {str(e)}")
        return False, f"调用大模型失败: {str(e)}"
