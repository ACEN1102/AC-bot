from flask import Flask, render_template, send_from_directory, request
from models.db import init_db
from controllers.task_controller import register_task_routes
from controllers.log_controller import register_log_routes
from controllers.test_controller import register_test_routes
from controllers.gitlab_controller import register_gitlab_routes
from scheduler.task_scheduler import update_scheduler
from utils.logger import logger
import logging

# 初始化Flask应用
app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'feishu_bot_secret_key'

# 配置Flask日志，启用werkzeug的INFO级别日志
log = logging.getLogger('werkzeug')
log.setLevel(logging.INFO)

# 自定义请求日志过滤器，忽略/api/logs和/api/tasks这两个精确路径
class WerkzeugRequestFilter(logging.Filter):
    def filter(self, record):
        # 检查日志消息是否包含要忽略的精确路径
        message = record.getMessage()
        # werkzeug的日志格式通常是："GET /path HTTP/1.1" 200 - 315
        # 只忽略精确匹配的/api/logs和/api/tasks路径，不忽略它们的子路径
        if '"GET /api/logs HTTP/' in message or \
           '"POST /api/logs HTTP/' in message or \
           '"PUT /api/logs HTTP/' in message or \
           '"DELETE /api/logs HTTP/' in message or \
           '"GET /api/tasks HTTP/' in message or \
           '"POST /api/tasks HTTP/' in message or \
           '"PUT /api/tasks HTTP/' in message or \
           '"DELETE /api/tasks HTTP/' in message:
            return False
        return True

# 为werkzeug日志处理器添加自定义过滤器
for handler in log.handlers:
    handler.addFilter(WerkzeugRequestFilter())

# 自定义请求日志记录器，忽略/api/logs和/api/tasks这两个精确路径
@app.before_request
def log_request():
    path = request.path
    # 只忽略精确匹配的/api/logs和/api/tasks路径，不忽略它们的子路径
    if path != '/api/logs' and path != '/api/tasks':
        logger.info(f"Request: {request.method} {path}")

@app.after_request
def log_response(response):
    path = request.path
    # 只忽略精确匹配的/api/logs和/api/tasks路径，不忽略它们的子路径
    if path != '/api/logs' and path != '/api/tasks':
        logger.info(f"Response: {request.method} {path} {response.status_code}")
    return response

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

