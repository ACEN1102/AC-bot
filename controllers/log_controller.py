from flask import jsonify
from services.log_service import get_logs, clear_logs

def register_log_routes(app):
    """注册日志相关路由"""
    
    @app.route('/api/logs', methods=['GET'])
    def get_logs_route():
        """获取日志列表"""
        logs = get_logs()
        
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
    
    @app.route('/api/clear_logs', methods=['POST'])
    def clear_logs_route():
        """清空日志"""
        try:
            clear_logs()
            return jsonify({'success': True, 'message': '日志已清空'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'清空日志失败: {str(e)}'})
