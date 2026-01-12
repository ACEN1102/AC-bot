from flask import request, jsonify
from services.feishu_service import send_feishu_message
from services.ai_service import get_ai_news

def register_test_routes(app):
    """注册测试相关路由"""
    
    @app.route('/api/test_webhook', methods=['POST'])
    def test_webhook():
        """测试Webhook连接"""
        data = request.json
        webhook_url = data.get('webhook_url')
        content = data.get('content', '这是一条测试消息，用于验证飞书webhook连接是否正常。')
        if not webhook_url:
            return jsonify({'success': False, 'message': '请提供webhook_url'})
        
        success, message = send_feishu_message(webhook_url, content)
        return jsonify({'success': success, 'message': message})
    
    @app.route('/api/fetch_ai_news', methods=['GET'])
    def fetch_ai_news_api():
        """获取AI新闻"""
        success, message = get_ai_news()
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message})
