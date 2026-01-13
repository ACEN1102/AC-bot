from flask import request, jsonify
from services.gitlab_service import verify_gitlab_signature, parse_gitlab_event
from services.feishu_service import send_feishu_message
from models.db import execute_query
from datetime import datetime
from utils.logger import logger

def register_gitlab_routes(app):
    """注册GitLab相关路由"""
    
    @app.route('/api/gitlab/webhook', methods=['POST'])
    def gitlab_webhook():
        """处理GitLab Webhook请求"""
        logger.info("接收到GitLab Webhook请求")
        # 获取请求头中的事件类型和签名
        event_type = request.headers.get('X-Gitlab-Event', '')
        signature_header = request.headers.get('X-Gitlab-Token', '') or request.headers.get('X-Hub-Signature-256', '')
        
        logger.info(f"GitLab事件类型: {event_type}")
        
        # 获取请求体
        request_body = request.get_data()
        
        # 尝试解析请求体
        try:
            event_data = request.get_json()
            logger.debug(f"GitLab事件数据: {event_data}")
        except Exception as e:
            logger.error(f"解析请求体失败: {str(e)}")
            return jsonify({'success': False, 'message': f'解析请求体失败: {str(e)}'}), 400
        
        # 获取项目路径，用于匹配任务
        project_path = event_data.get('project', {}).get('path_with_namespace', '')
        logger.info(f"GitLab项目路径: {project_path}")
        
        # 查询所有启用的GitLab任务
        tasks = execute_query("SELECT id, name, type, webhook_url, enabled, gitlab_token, gitlab_events, gitlab_project, days_of_week FROM tasks WHERE type = 'gitlab' AND enabled = 1")
        logger.info(f"找到 {len(tasks)} 个启用的GitLab任务")
        
        # 遍历所有匹配的任务
        for task in tasks:
            task_id, name, type, feishu_webhook, enabled, gitlab_token, gitlab_events, gitlab_project, days_of_week = task
            
            # 检查项目是否匹配
            if gitlab_project and project_path != gitlab_project:
                continue
            
            # 验证GitLab签名
            if gitlab_token and not verify_gitlab_signature(gitlab_token, request_body, signature_header):
                continue
            
            # 检查事件类型是否匹配
            if gitlab_events and event_type not in gitlab_events:
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
            
            # 解析GitLab事件
            message, success = parse_gitlab_event(event_type, event_data)
            
            if success:
                # 发送飞书消息
                send_success, send_message = send_feishu_message(feishu_webhook, message)
                
                # 记录日志
                execute_query(
                    "INSERT INTO logs (task_id, status, message) VALUES (?, ?, ?)",
                    (task_id, "成功" if send_success else "失败", f"GitLab事件处理: {event_type}" if send_success else f"GitLab事件处理失败: {send_message}"),
                    commit=True
                )
        
        return jsonify({'success': True, 'message': 'GitLab Webhook已处理'})
