import sqlite3
from datetime import datetime
from utils.logger import logger

DATABASE_NAME = 'feishu_bot.db'

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DATABASE_NAME)
    # 设置数据库时区为东八区
    conn.execute("PRAGMA timezone='+08:00'")
    return conn

def init_db():
    """初始化数据库"""
    logger.info("***正在初始化AC-bot数据库...")
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
        ai_news_url TEXT,
        gitlab_url TEXT,
        gitlab_token TEXT,
        gitlab_events TEXT,
        gitlab_project TEXT,
        github_url TEXT,
        github_token TEXT,
        github_events TEXT,
        github_project TEXT
    )
    ''')
    
    # 为现有表添加GitHub相关字段（如果不存在）
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN github_url TEXT")
        logger.info("添加github_url字段成功")
    except Exception as e:
        logger.debug(f"github_url字段已存在或添加失败: {str(e)}")
    
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN github_token TEXT")
        logger.info("添加github_token字段成功")
    except Exception as e:
        logger.debug(f"github_token字段已存在或添加失败: {str(e)}")
    
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN github_events TEXT")
        logger.info("添加github_events字段成功")
    except Exception as e:
        logger.debug(f"github_events字段已存在或添加失败: {str(e)}")
    
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN github_project TEXT")
        logger.info("添加github_project字段成功")
    except Exception as e:
        logger.debug(f"github_project字段已存在或添加失败: {str(e)}")
    
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
    logger.info("***数据库初始化完成!")

def execute_query(query, params=(), fetch_one=False, commit=False):
    """执行SQL查询"""
    logger.debug(f"执行SQL查询: {query[:50]}...  参数: {params}")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    
    result = None
    if fetch_one:
        result = cursor.fetchone()
        logger.debug(f"查询结果(单行): {result}")
    else:
        result = cursor.fetchall()
        logger.debug(f"查询结果(多行): {len(result)} 行")
    
    if commit:
        conn.commit()
        logger.debug("事务已提交")
    
    conn.close()
    return result
