from flask import request, jsonify
from services.github_service import verify_github_signature, parse_github_event
from services.feishu_service import send_feishu_message
from models.db import execute_query
from datetime import datetime
from utils.logger import logger

def register_github_routes(app):
    """注册GitHub相关路由"""
    
    @app.route('/api/github/webhook', methods=['POST'])
    def github_webhook():
        """处理GitHub Webhook请求"""
        logger.info("接收到GitHub Webhook请求")
        # 获取请求头中的事件类型和签名
        event_type = request.headers.get('X-GitHub-Event', '')
        signature_header = request.headers.get('X-Hub-Signature-256', '')
        
        logger.info(f"GitHub事件类型: {event_type}")
        
        # 获取请求体
        request_body = request.get_data()
        
        # 尝试解析请求体
        try:
            event_data = request.get_json()
            logger.debug(f"GitHub事件数据: {event_data}")
        except Exception as e:
            logger.error(f"解析请求体失败: {str(e)}")
            return jsonify({'success': False, 'message': f'解析请求体失败: {str(e)}'}), 400
        
        # 获取项目路径，用于匹配任务
        project_path = event_data.get('repository', {}).get('full_name', '')
        logger.info(f"GitHub项目路径: {project_path}")
        
        # 查询所有启用的GitHub任务
        tasks = execute_query("SELECT id, name, type, webhook_url, enabled, github_token, github_events, github_project, days_of_week FROM tasks WHERE type = 'github' AND enabled = 1")
        logger.info(f"找到 {len(tasks)} 个启用的GitHub任务")
        
        # 遍历所有匹配的任务
        for task in tasks:
            task_id, name, type, feishu_webhook, enabled, github_token, github_events, github_project, days_of_week = task
            
            # 检查项目是否匹配
            if github_project and project_path != github_project:
                continue
            
            # 验证GitHub签名
            if github_token and not verify_github_signature(github_token, request_body, signature_header):
                continue
            
            # 检查事件类型是否匹配
            if github_events and event_type not in github_events:
                continue
            
            # 检查是否是指定的星期几
            if days_of_week:
                current_day = datetime.now().weekday()  # 0-6, 0表示星期一
                # 转换为 1(周一), 2(周二), ..., 7(周日)的格式
                current_day += 1
                if current_day == 7:  # 周日
                    current_day = 0
                
                selected_days = [int(day) for day in days_of_week.split(',') if day.isdigit()]
                if current_day not in selected_days:
                    # 不是指定的星期几，不执行任务
                    continue
            
            # 解析GitHub事件
            message, success = parse_github_event(event_type, event_data)
            
            if success:
                # 发送飞书消息
                send_success, send_message = send_feishu_message(feishu_webhook, message)
                
                # 记录日志
                execute_query(
                    "INSERT INTO logs (task_id, status, message) VALUES (?, ?, ?)",
                    (task_id, "成功" if send_success else "失败", f"GitHub事件处理: {event_type}" if send_success else f"GitHub事件处理失败: {send_message}"),
                    commit=True
                )
        
        return jsonify({'success': True, 'message': 'GitHub Webhook已处理'})
