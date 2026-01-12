import sqlite3
from datetime import datetime

DATABASE_NAME = 'feishu_bot.db'

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE_NAME)
    # 设置数据库时区为东八区
    conn.execute("PRAGMA timezone='+08:00'")
    return conn

def init_db():
    """初始化数据库"""
    conn = get_db_connection()
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

def execute_query(query, params=(), fetch_one=False, commit=False):
    """执行SQL查询"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    
    result = None
    if fetch_one:
        result = cursor.fetchone()
    else:
        result = cursor.fetchall()
    
    if commit:
        conn.commit()
    
    conn.close()
    return result
