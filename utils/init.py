from base64 import decode

from utils.logger import logger

def log_init():
    try:
        from werkzeug.serving import WSGIRequestHandler
        original_log_request = WSGIRequestHandler.log_request
        def custom_log_request(self, *args, **kwargs):
            path = self.path
            if path not in ['/api/logs',
                            '/api/tasks',
                            '/static/css',
                            '/static/css/style.css',
                            '/static/js/app.js',
                            '/'
                            ]:
                original_log_request(self, *args, **kwargs)
        WSGIRequestHandler.log_request = custom_log_request
        logger.info("*** 日志加载器已就绪！")
    except Exception as e:
        logger.error(f"加载日志过滤功能失败: {str(e)}")

def start_init():
    logger.info("系统初始化完成！")
    doge = """                                                                                                               
                                    .-%%+                       
                                    :%%%%.                      
                  ..=:>    . -%%%%%%%+.:%..                      
                  %%%%%%%%%%%%%%%%%%%%%:                        
                 .+%%%%%%%%%·%%%: %.%%%%::   .                  
                      . %%%%%%**%*%.%=%%%=.  .%                  
                       .%%%%%%%%* - %%%%*:%%%*.%%.               
                       -+%%%%%%%%%%%*++%%%%%%=.* .              
                   :%%%%%%%%*****%%%%%%%%%%%*..                 
                  *%%%%%%%%%%%%%%%%%%%%%%%.                     
                  *%%+-*%%%%%%%%%%%%%%%%%%                      
                       %%%%%%%%%%%%%%%%%%%                      
                 +   .=%%%%%%%%%%%%%%%%%%%                      
                 .+%% %%%%%%%%%%%%%%%%%%%%+                     
                     =%%%%%%%%%%%%%%%%%%%%=.                   
                    .*%%%%%*       : .%%%%%*                
                 ___________________________
                    启动成功了，小狗给你点赞！  
                 ___________________________                                                              
"""
    logger.info(f"{doge}")
