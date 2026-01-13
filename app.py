from flask import Flask, render_template, send_from_directory

from models.db import init_db
from controllers.task_controller import register_task_routes
from controllers.log_controller import register_log_routes
from controllers.test_controller import register_test_routes
from controllers.gitlab_controller import register_gitlab_routes
from scheduler.task_scheduler import update_scheduler
import logging

# 初始化Flask应用
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'feishu_bot_secret_key'

# 直接修改werkzeug的日志处理方式，完全控制日志输出
# 1. 首先保存原始的处理器
original_handlers = logging.getLogger('werkzeug').handlers.copy()

# 2. 移除所有原始处理器
for handler in list(logging.getLogger('werkzeug').handlers):
    logging.getLogger('werkzeug').removeHandler(handler)

# 3. 创建自定义的日志处理器，只输出非/api/logs和/api/tasks的请求日志
class CustomWerkzeugHandler(logging.Handler):
    def emit(self, record):
        message = record.getMessage()
        
        # 检查是否是请求日志
        is_request_log = ' - - [' in message and ('HTTP/1.0' in message or 'HTTP/1.1' in message)
        
        if is_request_log:
            # 检查是否是需要过滤的请求路径
            if '/api/logs' in message or '/api/tasks' in message:
                return  # 过滤掉这个请求日志
        
        # 对于其他日志，使用原始处理器输出
        for handler in original_handlers:
            if record.levelno >= handler.level:
                handler.emit(record)

# 4. 添加自定义处理器
custom_handler = CustomWerkzeugHandler()
logging.getLogger('werkzeug').addHandler(custom_handler)

# 5. 设置日志级别为INFO，确保开发服务器信息和警告能正常输出
logging.getLogger('werkzeug').setLevel(logging.INFO)

# 注册路由
register_task_routes(app)
register_log_routes(app)
register_test_routes(app)
register_gitlab_routes(app)

# 主页路由
@app.route('/')
def index():
    return render_template('index.html')

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
    ip = app.config.get('IP')
    app.run(host='0.0.0.0', port=9096, debug=False)

