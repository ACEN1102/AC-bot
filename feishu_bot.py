import os
import json
import time
import requests
import sqlite3
import threading
from datetime import datetime, timedelta
from flask import Flask, request, render_template, jsonify, send_from_directory
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from openai import OpenAI

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'feishu_bot_secret_key'

# 初始化数据库
def init_db():
    conn = sqlite3.connect('feishu_bot.db')
    cursor = conn.cursor()
    # 创建任务表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        webhook_url TEXT NOT NULL,
        cron_expression TEXT NOT NULL,
        enabled INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
        updated_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
        content TEXT,
        api_url TEXT,
        api_key TEXT,
        days_of_week TEXT,
        model_name TEXT,
        ai_news_url TEXT
    )
    ''')
    # 创建日志表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY,
        task_id INTEGER,
        status TEXT,
        message TEXT,
        created_at TIMESTAMP DEFAULT (datetime('now', 'localtime')),
        FOREIGN KEY (task_id) REFERENCES tasks (id)
    )
    ''')
    conn.commit()
    conn.close()

# 发送飞书消息
def send_feishu_message(webhook_url, content):

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

# 获取AI新闻
def get_ai_news(url="http://127.0.0.1:4399/v2/ai-news"):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data['code'] == 200 and 'news' in data['data']:
            news_list = data['data']['news']
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
            return False, "获取新闻失败: 返回数据格式错误"
    except Exception as e:
        return False, f"获取新闻失败: {str(e)}"

# 调用大模型
def call_llm(api_url, api_key, prompt, model_name='deepseek-chat'):
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

        # response.raise_for_status()
        return True, response.choices[0].message.content
    except Exception as e:
        return False, f"调用大模型失败: {str(e)}"

# 执行任务
def execute_task(task_id):
    conn = sqlite3.connect('feishu_bot.db')
    # 设置数据库时区为东八区
    conn.execute("PRAGMA timezone='+08:00'")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()
    conn.close()
    
    if not task or task[5] == 0:  # 任务不存在或已禁用
        return
    
    # 确保task元组有足够的元素
    task_data = list(task)
    while len(task_data) < 14:  # 确保至少有14个元素（包含新增的model_name和ai_news_url）
        task_data.append(None)
    
    task_id, name, type, webhook_url, cron_expression, enabled, created_at, updated_at, content, api_url, api_key, days_of_week, model_name, ai_news_url = task_data
    
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
    conn = sqlite3.connect('feishu_bot.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO logs (task_id, status, message) VALUES (?, ?, ?)",
        (task_id, log_status, log_message)
    )
    conn.commit()
    conn.close()

# 初始化调度器
scheduler = BackgroundScheduler()
scheduler.start()

# 更新调度器任务
def update_scheduler():
    # 移除所有任务
    for job in scheduler.get_jobs():
        scheduler.remove_job(job.id)
    
    # 添加所有启用的任务
    conn = sqlite3.connect('feishu_bot.db')
    # 设置数据库时区为东八区
    conn.execute("PRAGMA timezone='+08:00'")
    cursor = conn.cursor()
    cursor.execute("SELECT id, cron_expression, days_of_week FROM tasks WHERE enabled = 1")
    tasks = cursor.fetchall()
    conn.close()
    
    for task_info in tasks:
        try:
            task_id = task_info[0]
            cron_expression = task_info[1]
            days_of_week = task_info[2] if len(task_info) > 2 else ''
            
            # 解析cron表达式（格式：HH:MM:SS）
            parts = cron_expression.split(':')
            if len(parts) != 3:
                print(f"无效的cron表达式: {cron_expression}")
                continue
            
            hour = int(parts[0])
            minute = int(parts[1])
            second = int(parts[2])
            
            # 设置触发器
            if days_of_week:
                # 按指定的星期几执行
                selected_days = [int(day) for day in days_of_week.split(',') if day.isdigit()]
                # 转换为APScheduler的星期表示（0-6，0表示周一）
                aps_days = []
                for day in selected_days:
                    if day == 0:  # 0表示周日
                        aps_days.append(6)
                    else:
                        aps_days.append(day - 1)
                
                # 将列表转换为APScheduler接受的格式：逗号分隔的字符串
                aps_days_str = ','.join(map(str, aps_days))
                
                trigger = CronTrigger(
                    second=second, minute=minute, hour=hour, 
                    day_of_week=aps_days_str
                )
            else:
                # 每天执行
                trigger = CronTrigger(
                    second=second, minute=minute, hour=hour
                )
            
            # 添加任务到调度器
            scheduler.add_job(
                execute_task, 
                trigger, 
                args=[task_id], 
                id=f"task_{task_id}",
                misfire_grace_time=300  # 允许5分钟的执行延迟
            )
        except Exception as e:
            print(f"添加任务 {task_id} 到调度器失败: {str(e)}")

# 路由定义
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    conn = sqlite3.connect('feishu_bot.db')
    # 设置数据库时区为东八区
    conn.execute("PRAGMA timezone='+08:00'")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks")
    tasks = cursor.fetchall()
    conn.close()
    
    task_list = []
    for task in tasks:
        task_data = {
            'id': task[0],
            'name': task[1],
            'type': task[2],
            'webhook_url': task[3],
            'cron_expression': task[4],
            'enabled': bool(task[5]),
            'created_at': task[6],
            'updated_at': task[7],
            'content': task[8],
            'api_url': task[9],
            'api_key': task[10]
        }
        # 如果有第11个元素（days_of_week），则添加到task_data中
        if len(task) > 11:
            task_data['days_of_week'] = task[11]
        else:
            task_data['days_of_week'] = ''
        
        # 如果有第12个元素（model_name），则添加到task_data中
        if len(task) > 12:
            task_data['model_name'] = task[12]
        else:
            task_data['model_name'] = ''
        
        # 如果有第13个元素（ai_news_url），则添加到task_data中
        if len(task) > 13:
            task_data['ai_news_url'] = task[13]
        else:
            task_data['ai_news_url'] = ''
        
        task_list.append(task_data)
    
    return jsonify({'tasks': task_list})

@app.route('/api/tasks', methods=['POST'])
def add_task():
    data = request.json
    
    conn = sqlite3.connect('feishu_bot.db')
    # 设置数据库时区为东八区
    conn.execute("PRAGMA timezone='+08:00'")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (name, type, webhook_url, cron_expression, enabled, content, api_url, api_key, days_of_week, model_name, ai_news_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (data['name'], data['type'], data['webhook_url'], data['cron_expression'], 
         1 if data.get('enabled', True) else 0, data.get('content'), 
         data.get('api_url'), data.get('api_key'), data.get('days_of_week', ''),
         data.get('model_name'), data.get('ai_news_url'))
    )
    task_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    # 更新调度器
    update_scheduler()
    
    return jsonify({'success': True, 'task_id': task_id})

@app.route('/api/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    conn = sqlite3.connect('feishu_bot.db')
    # 设置数据库时区为东八区
    conn.execute("PRAGMA timezone='+08:00'")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    task = cursor.fetchone()
    conn.close()
    
    if not task:
        return jsonify({'success': False, 'message': '任务不存在'}), 404
    
    task_data = {
        'id': task[0],
        'name': task[1],
        'type': task[2],
        'webhook_url': task[3],
        'cron_expression': task[4],
        'enabled': bool(task[5]),
        'created_at': task[6],
        'updated_at': task[7],
        'content': task[8],
        'api_url': task[9],
        'api_key': task[10]
    }
    # 如果有第11个元素（days_of_week），则添加到task_data中
    if len(task) > 11:
        task_data['days_of_week'] = task[11]
    else:
        task_data['days_of_week'] = ''
    
    # 如果有第12个元素（model_name），则添加到task_data中
    if len(task) > 12:
        task_data['model_name'] = task[12]
    else:
        task_data['model_name'] = ''
    
    # 如果有第13个元素（ai_news_url），则添加到task_data中
    if len(task) > 13:
        task_data['ai_news_url'] = task[13]
    else:
        task_data['ai_news_url'] = ''
    
    return jsonify({'success': True, 'task': task_data})

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    data = request.json
    
    conn = sqlite3.connect('feishu_bot.db')
    # 设置数据库时区为东八区
    conn.execute("PRAGMA timezone='+08:00'")
    cursor = conn.cursor()
    
    # 如果只更新enabled字段
    if len(data) == 1 and 'enabled' in data:
        cursor.execute(
            "UPDATE tasks SET enabled = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (1 if data['enabled'] else 0, task_id)
        )
    else:
        # 完整更新所有字段
        cursor.execute(
            "UPDATE tasks SET name = ?, type = ?, webhook_url = ?, cron_expression = ?, enabled = ?, content = ?, api_url = ?, api_key = ?, days_of_week = ?, model_name = ?, ai_news_url = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (data['name'], data['type'], data['webhook_url'], data['cron_expression'], 
             1 if data.get('enabled', True) else 0, data.get('content'), 
             data.get('api_url'), data.get('api_key'), data.get('days_of_week', ''),
             data.get('model_name'), data.get('ai_news_url'), task_id)
        )
    conn.commit()
    conn.close()
    
    # 更新调度器
    update_scheduler()
    
    return jsonify({'success': True})

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    conn = sqlite3.connect('feishu_bot.db')
    # 设置数据库时区为东八区
    conn.execute("PRAGMA timezone='+08:00'")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    
    # 更新调度器
    update_scheduler()
    
    return jsonify({'success': True})

@app.route('/api/tasks/<int:task_id>/execute', methods=['POST'])
def manual_execute_task(task_id):
    # 在线程中执行任务，避免阻塞
    threading.Thread(target=execute_task, args=(task_id,)).start()
    return jsonify({'success': True, 'message': '任务已开始执行'})

@app.route('/api/logs', methods=['GET'])
def get_logs():
    conn = sqlite3.connect('feishu_bot.db')
    # 设置数据库时区为东八区
    conn.execute("PRAGMA timezone='+08:00'")
    cursor = conn.cursor()
    # 按时间倒序获取最近100条日志
    cursor.execute("SELECT l.*, t.name FROM logs l LEFT JOIN tasks t ON l.task_id = t.id ORDER BY l.created_at DESC LIMIT 100")
    logs = cursor.fetchall()
    conn.close()
    
    log_list = []
    for log in logs:
        log_list.append({
            'id': log[0],
            'task_id': log[1],
            'task_name': log[5],
            'status': log[2],
            'message': log[3],
            'created_at': log[4]
        })
    
    return jsonify({'logs': log_list})

@app.route('/api/test_webhook', methods=['POST'])
def test_webhook():
    data = request.json
    webhook_url = data.get('webhook_url')
    content = data.get('content', '这是一条测试消息，用于验证飞书webhook连接是否正常。')
    if not webhook_url:
        return jsonify({'success': False, 'message': '请提供webhook_url'})
    
    success, message = send_feishu_message(webhook_url, content)
    return jsonify({'success': success, 'message': message})

@app.route('/api/fetch_ai_news', methods=['GET'])
def fetch_ai_news_api():
    success, message = get_ai_news()
    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'success': False, 'message': message})

@app.route('/api/clear_logs', methods=['POST'])
def clear_logs():
    try:
        conn = sqlite3.connect('feishu_bot.db')
        # 设置数据库时区为东八区
        conn.execute("PRAGMA timezone='+08:00'")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM logs")
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': '日志已清空'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'清空日志失败: {str(e)}'})

@app.route('/api/task_stats', methods=['GET'])
def get_task_stats():
    try:
        conn = sqlite3.connect('feishu_bot.db')
        # 设置数据库时区为东八区
        conn.execute("PRAGMA timezone='+08:00'")
        cursor = conn.cursor()
        
        # 获取总任务数
        cursor.execute("SELECT COUNT(*) FROM tasks")
        total_tasks = cursor.fetchone()[0]
        
        # 获取活跃任务数
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE enabled = 1")
        active_tasks = cursor.fetchone()[0]
        
        # 获取下一次执行时间
        next_run = "暂无"
        
        # 如果有活跃任务，尝试计算下一次执行时间
        if active_tasks > 0:
            now = datetime.now()
            next_run_times = []
            
            # 获取所有活跃任务
            cursor.execute("SELECT id, cron_expression, days_of_week FROM tasks WHERE enabled = 1")
            tasks = cursor.fetchall()
            
            for task in tasks:
                task_id, cron_expression, days_of_week = task
                
                # 解析cron表达式
                parts = cron_expression.split(':')
                if len(parts) == 3:
                    hour = int(parts[0])
                    minute = int(parts[1])
                    second = int(parts[2])
                    
                    # 创建任务执行时间
                    task_time = now.replace(hour=hour, minute=minute, second=second, microsecond=0)
                    
                    # 检查是否需要调整到明天或指定的星期几
                    if task_time <= now:
                        task_time += timedelta(days=1)
                    
                    # 处理按星期执行的情况
                    if days_of_week:
                        selected_days = [int(day) for day in days_of_week.split(',') if day.isdigit()]
                        current_day = now.weekday() + 1  # 转换为1-7（1表示周一，7表示周日）
                        
                        # 如果今天是周日，调整为0
                        if current_day == 7:
                            current_day = 0
                        
                        # 找到下一个执行的星期几
                        days_ahead = None
                        for day in selected_days:
                            if day > current_day or (day == current_day and task_time > now):
                                days_ahead = day - current_day
                                break
                        
                        # 如果没有找到，说明需要到下周
                        if days_ahead is None:
                            # 找到下周最早的执行日
                            min_day = min(selected_days)
                            days_ahead = (7 - current_day) + min_day
                        
                        # 调整执行时间
                        if days_ahead > 0:
                            task_time += timedelta(days=days_ahead)
                    
                    next_run_times.append(task_time)
            
            # 找到最早的下一次执行时间
            if next_run_times:
                next_run = min(next_run_times).isoformat()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'task_stats': {
                'total': total_tasks,
                'active': active_tasks,
                'next_run': next_run
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取任务统计失败: {str(e)}'
        })

# 静态文件服务
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# 主函数
if __name__ == '__main__':
    # 初始化数据库
    init_db()
    # 更新调度器
    update_scheduler()
    # 启动Flask应用
    app.run(host='0.0.0.0', port=9096, debug=False)