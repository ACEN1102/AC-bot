from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from models.db import execute_query
from services.task_service import execute_task

# 初始化调度器
scheduler = BackgroundScheduler()
scheduler.start()

def update_scheduler():
    """更新调度器任务"""
    # 移除所有任务
    for job in scheduler.get_jobs():
        scheduler.remove_job(job.id)
    
    # 添加所有启用的任务
    tasks = execute_query("SELECT id, cron_expression, days_of_week FROM tasks WHERE enabled = 1")
    
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
