from flask import Flask, render_template, send_from_directory

from models.db import init_db
from controllers.task_controller import register_task_routes
from controllers.log_controller import register_log_routes
from controllers.test_controller import register_test_routes
from controllers.gitlab_controller import register_gitlab_routes
from controllers.github_controller import register_github_routes
from scheduler.task_scheduler import update_scheduler

from utils.init import log_init, start_init

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = 'feishu_bot_secret_key'

register_task_routes(app)
register_log_routes(app)
register_test_routes(app)
register_gitlab_routes(app)
register_github_routes(app)

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
    init_db()
    update_scheduler()
    log_init()
    start_init()
    app.run(host='0.0.0.0', port=9096, debug=False)

