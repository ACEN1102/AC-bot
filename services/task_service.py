import sqlite3
from models.db import execute_query
from services.feishu_service import send_feishu_message
from services.ai_service import get_ai_news, call_llm
from datetime import datetime

def get_all_tasks():
    """获取所有任务"""
    return execute_query("SELECT * FROM tasks")

def get_task_by_id(task_id):
    """根据ID获取任务"""
    return execute_query("SELECT * FROM tasks WHERE id = ?", (task_id,), fetch_one=True)

def create_task(task_data):
    """创建任务"""
    conn = sqlite3.connect('feishu_bot.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (name, type, webhook_url, cron_expression, enabled, content, api_url, api_key, days_of_week, model_name, ai_news_url, gitlab_url, gitlab_token, gitlab_events, gitlab_project) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (task_data['name'], task_data['type'], task_data['webhook_url'], task_data['cron_expression'], 
         1 if task_data.get('enabled', True) else 0, task_data.get('content'), 
         task_data.get('api_url'), task_data.get('api_key'), task_data.get('days_of_week', ''),
         task_data.get('model_name'), task_data.get('ai_news_url'),
         task_data.get('gitlab_url'), task_data.get('gitlab_token'), task_data.get('gitlab_events', ''),
         task_data.get('gitlab_project'))
    )
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return task_id

def update_task(task_id, task_data):
    """更新任务"""
    # 如果只更新enabled字段
    if len(task_data) == 1 and 'enabled' in task_data:
        execute_query(
            "UPDATE tasks SET enabled = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (1 if task_data['enabled'] else 0, task_id),
            commit=True
        )
    else:
        # 完整更新所有字段
        execute_query(
            "UPDATE tasks SET name = ?, type = ?, webhook_url = ?, cron_expression = ?, enabled = ?, content = ?, api_url = ?, api_key = ?, days_of_week = ?, model_name = ?, ai_news_url = ?, gitlab_url = ?, gitlab_token = ?, gitlab_events = ?, gitlab_project = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (task_data['name'], task_data['type'], task_data['webhook_url'], task_data['cron_expression'], 
             1 if task_data.get('enabled', True) else 0, task_data.get('content'), 
             task_data.get('api_url'), task_data.get('api_key'), task_data.get('days_of_week', ''),
             task_data.get('model_name'), task_data.get('ai_news_url'),
             task_data.get('gitlab_url'), task_data.get('gitlab_token'), task_data.get('gitlab_events', ''),
             task_data.get('gitlab_project'), task_id),
            commit=True
        )

def delete_task(task_id):
    """删除任务"""
    execute_query("DELETE FROM tasks WHERE id = ?", (task_id,), commit=True)

def execute_task(task_id):
    """执行任务"""
    task = get_task_by_id(task_id)
    
    if not task or task[5] == 0:  # 任务不存在或已禁用
        return
    
    # 确保task元组有足够的元素
    task_data = list(task)
    while len(task_data) < 18:  # 确保至少有18个元素（包含新增的GitLab相关字段）
        task_data.append(None)
    
    task_id, name, type, webhook_url, cron_expression, enabled, created_at, updated_at, content, api_url, api_key, days_of_week, model_name, ai_news_url, gitlab_url, gitlab_token, gitlab_events, gitlab_project = task_data
    
    try:
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
                return
        
        # 根据任务类型生成内容
        if type == 'custom':
            success, message = True, content
        elif type == 'ai_news':
            # 如果有自定义的AI新闻URL，则使用它，否则使用默认值
            success, message = get_ai_news(ai_news_url if ai_news_url else None)
        elif type == 'llm':
            # 如果有自定义的模型名称，则使用它，否则使用默认值
            success, message = call_llm(api_url, api_key, content, model_name)
        elif type == 'gitlab':
            # GitLab任务类型不需要在这里执行，它是由Webhook触发的
            success, message = True, "GitLab任务是由Webhook触发的，不需要定时执行"
        else:
            success, message = False, f"未知任务类型: {type}"
        
        # 发送消息
        if success:
            send_success, send_msg = send_feishu_message(webhook_url, message)
            if send_success:
                log_status = "成功"
                log_message = f"任务 '{name}' 执行成功"
            else:
                log_status = "失败"
                log_message = send_msg
        else:
            log_status = "失败"
            log_message = message
    except Exception as e:
        log_status = "失败"
        log_message = f"任务执行异常: {str(e)}"
    
    # 记录日志
    execute_query(
        "INSERT INTO logs (task_id, status, message) VALUES (?, ?, ?)",
        (task_id, log_status, log_message),
        commit=True
    )
