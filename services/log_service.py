from models.db import execute_query

def get_logs():
    """获取日志列表"""
    # 按时间倒序获取最近100条日志
    return execute_query("SELECT l.*, t.name FROM logs l LEFT JOIN tasks t ON l.task_id = t.id ORDER BY l.created_at DESC LIMIT 100")

def clear_logs():
    """清空日志"""
    execute_query("DELETE FROM logs", commit=True)

def add_log(task_id, status, message):
    """添加日志"""
    execute_query(
        "INSERT INTO logs (task_id, status, message) VALUES (?, ?, ?)",
        (task_id, status, message),
        commit=True
    )
