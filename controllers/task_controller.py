from flask import request, jsonify
from services.task_service import get_all_tasks, get_task_by_id, create_task, update_task, delete_task, execute_task
from scheduler.task_scheduler import update_scheduler
import threading

def register_task_routes(app):
    """注册任务相关路由"""
    
    @app.route('/api/tasks', methods=['GET'])
    def get_tasks():
        """获取所有任务"""
        tasks = get_all_tasks()
        
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
            
            # 添加GitLab相关字段
            if len(task) > 14:
                task_data['gitlab_url'] = task[14]
            else:
                task_data['gitlab_url'] = ''
            
            if len(task) > 15:
                task_data['gitlab_token'] = task[15]
            else:
                task_data['gitlab_token'] = ''
            
            if len(task) > 16:
                task_data['gitlab_events'] = task[16]
            else:
                task_data['gitlab_events'] = ''
            
            if len(task) > 17:
                task_data['gitlab_project'] = task[17]
            else:
                task_data['gitlab_project'] = ''
            
            task_list.append(task_data)
        
        return jsonify({'tasks': task_list})
    
    @app.route('/api/tasks/<int:task_id>', methods=['GET'])
    def get_task(task_id):
        """根据ID获取任务"""
        task = get_task_by_id(task_id)
        
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
        
        # 添加GitLab相关字段
        if len(task) > 14:
            task_data['gitlab_url'] = task[14]
        else:
            task_data['gitlab_url'] = ''
        
        if len(task) > 15:
            task_data['gitlab_token'] = task[15]
        else:
            task_data['gitlab_token'] = ''
        
        if len(task) > 16:
            task_data['gitlab_events'] = task[16]
        else:
            task_data['gitlab_events'] = ''
        
        if len(task) > 17:
            task_data['gitlab_project'] = task[17]
        else:
            task_data['gitlab_project'] = ''
        
        return jsonify({'success': True, 'task': task_data})
    
    @app.route('/api/tasks', methods=['POST'])
    def add_task():
        """添加任务"""
        data = request.json
        
        task_id = create_task(data)
        
        # 更新调度器
        update_scheduler()
        
        return jsonify({'success': True, 'task_id': task_id})
    
    @app.route('/api/tasks/<int:task_id>', methods=['PUT'])
    def update_task_route(task_id):
        """更新任务"""
        data = request.json
        
        update_task(task_id, data)
        
        # 更新调度器
        update_scheduler()
        
        return jsonify({'success': True})
    
    @app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
    def delete_task_route(task_id):
        """删除任务"""
        delete_task(task_id)
        
        # 更新调度器
        update_scheduler()
        
        return jsonify({'success': True})
    
    @app.route('/api/tasks/<int:task_id>/execute', methods=['POST'])
    def manual_execute_task(task_id):
        """手动执行任务"""
        # 在线程中执行任务，避免阻塞
        threading.Thread(target=execute_task, args=(task_id,)).start()
        return jsonify({'success': True, 'message': '任务已开始执行'})
    
    @app.route('/api/task_stats', methods=['GET'])
    def get_task_stats():
        """获取任务统计信息"""
        try:
            from models.db import execute_query
            from datetime import datetime, timedelta
            
            # 获取总任务数
            total_tasks = execute_query("SELECT COUNT(*) FROM tasks", fetch_one=True)[0]
            
            # 获取活跃任务数
            active_tasks = execute_query("SELECT COUNT(*) FROM tasks WHERE enabled = 1", fetch_one=True)[0]
            
            # 获取下一次执行时间
            next_run = "暂无"
            
            # 如果有活跃任务，尝试计算下一次执行时间
            if active_tasks > 0:
                now = datetime.now()
                next_run_times = []
                
                # 获取所有活跃任务
                tasks = execute_query("SELECT id, cron_expression, days_of_week FROM tasks WHERE enabled = 1")
                
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
