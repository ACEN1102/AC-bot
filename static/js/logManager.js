// 日志管理模块

// 加载日志
function loadLogs() {
    $.ajax({
        url: '/api/logs',
        type: 'GET',
        dataType: 'json',
        success: function(response) {
            const logs = response.logs || [];
            const logContainer = $('#logContainer');
            
            // 清空日志容器
            logContainer.empty();
            
            if (logs.length === 0) {
                logContainer.html('<div class="text-muted text-center py-4">暂无日志记录</div>');
            } else {
                // 填充日志
                logs.forEach(log => {
                    const logElement = createLogElement(log);
                    logContainer.append(logElement);
                });
            }
        },
        error: function(xhr, status, error) {
            console.error('加载日志失败:', error);
            const logContainer = $('#logContainer');
            logContainer.html('<div class="text-danger text-center py-4">加载日志失败，请刷新页面重试</div>');
        }
    });
}

// 创建日志元素
function createLogElement(log) {
    // 格式化时间
    const formattedTime = formatDateTime(log.created_at);
    
    // 根据状态设置不同的样式
    let statusClass = '';
    let statusIcon = '';
    
    switch (log.status) {
        case '成功':
            statusClass = 'text-success';
            statusIcon = '<i class="fa fa-check-circle mr-1"></i>';
            break;
        case '失败':
            statusClass = 'text-danger';
            statusIcon = '<i class="fa fa-times-circle mr-1"></i>';
            break;
        default:
            statusClass = 'text-info';
            statusIcon = '<i class="fa fa-info-circle mr-1"></i>';
    }
    
    // 创建日志行
    const logRow = $(`<div class="log-row mb-2 pb-2 border-b border-gray-200">
        <div class="log-header d-flex justify-content-between align-items-center">
            <div class="log-task">
                <span class="font-semibold">${escapeHtml(log.task_name || '未知任务')}</span>
            </div>
            <div class="log-time text-xs text-muted">${formattedTime}</div>
        </div>
        <div class="log-content mt-1">
            <span class="${statusClass}">${statusIcon}${log.status}</span>
            <span class="ml-2">${escapeHtml(log.message)}</span>
        </div>
    </div>`);
    
    return logRow;
}

// 测试Webhook连接
function testWebhook() {
    const webhookUrl = $('#test-webhook-url').val().trim();
    const testContent = $('#test-message').val().trim();
    const testForm = $('#test-connection-form');
    
    // 验证输入
    if (!webhookUrl) {
        showWarning('请输入飞书Webhook地址');
        return;
    }
    
    if (!testContent) {
        showWarning('请输入测试内容');
        return;
    }
    
    // 验证Webhook URL格式
    const urlRegex = /^(https?:\/\/)?([\da-z.-]+)\.([a-z.]{2,6})([/\w .-]*)*\/?$/;
    if (!urlRegex.test(webhookUrl)) {
        showWarning('请输入有效的Webhook URL');
        return;
    }
    
    // 显示加载状态
    const submitBtn = testForm.find('button[type="submit"]');
    const originalText = submitBtn.html();
    submitBtn.html('<i class="fa fa-spinner fa-spin mr-1"></i> 发送中...');
    submitBtn.prop('disabled', true);
    
    // 发送测试请求
    $.ajax({
        url: '/api/test_webhook',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ webhook_url: webhookUrl, content: testContent }),
        success: function(response) {
            // 恢复按钮状态
            submitBtn.html(originalText);
            submitBtn.prop('disabled', false);
            
            // 显示结果
            if (response.success) {
                showSuccess('测试消息发送成功！');
            } else {
                showError(`测试消息发送失败：${response.message}`);
            }
        },
        error: function(xhr, status, error) {
            // 恢复按钮状态
            submitBtn.html(originalText);
            submitBtn.prop('disabled', false);
            
            // 显示错误结果
            showError(`测试消息发送失败：${error}`);
        }
    });
}

// 格式化日期时间
function formatDateTime(dateTimeString) {
    try {
        const date = new Date(dateTimeString);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        const hours = String(date.getHours()).padStart(2, '0');
        const minutes = String(date.getMinutes()).padStart(2, '0');
        const seconds = String(date.getSeconds()).padStart(2, '0');
        
        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    } catch (e) {
        return dateTimeString;
    }
}

// 清空日志（可选功能）
function clearLogs() {
    if (confirm('确定要清空所有日志吗？此操作不可恢复。')) {
        $.ajax({
            url: '/api/clear_logs',
            type: 'POST',
            success: function(response) {
                if (response.success) {
                    loadLogs();
                    showSuccess('日志已清空');
                } else {
                    showError('清空日志失败');
                }
            },
            error: function(xhr, status, error) {
                console.error('清空日志失败:', error);
                showError('清空日志失败，请重试');
            }
        });
    }
}

// 初始化清空日志按钮
function initClearLogsButton() {
    $('#clear-logs-btn').click(function() {
        clearLogs();
    });
}

// 更新任务统计
function updateTaskStats() {
    $.ajax({
        url: '/api/task_stats',
        type: 'GET',
        dataType: 'json',
        success: function(response) {
            const taskStats = response.task_stats || { total: 0, active: 0, next_run: '暂无' };
            
            // 更新统计数据显示
            // 总任务数卡片
            $('#total-tasks-card h3').text(taskStats.total);
            
            // 已启用任务卡片
            $('#enabled-tasks-card h3').text(taskStats.active);
            
            // 如果有下一次执行时间，更新最近执行状态卡片
            if (taskStats.next_run && taskStats.next_run !== '暂无') {
                const formattedNextRun = formatDateTime(taskStats.next_run);
                $('#recent-status-text').text('下一次执行');
                $('#recent-status-time').text(formattedNextRun);
                
                // 为下一次执行时间添加颜色提示
                try {
                    const nextRunDate = new Date(taskStats.next_run);
                    const now = new Date();
                    const diffMinutes = Math.floor((nextRunDate - now) / (1000 * 60));
                    
                    // 清除之前的所有颜色类
                    $('#recent-status-text').removeClass('text-danger text-warning text-success text-info');
                    $('#recent-status-time').removeClass('text-danger text-warning text-success text-info');
                    
                    // 根据时间差设置不同的颜色
                    if (diffMinutes < 10) {
                        $('#recent-status-text').addClass('text-danger'); // 即将执行，红色
                        $('#recent-status-time').addClass('text-danger');
                    } else if (diffMinutes < 60) {
                        $('#recent-status-text').addClass('text-warning'); // 一小时内执行，橙色
                        $('#recent-status-time').addClass('text-warning');
                    } else {
                        $('#recent-status-text').addClass('text-success'); // 一小时后执行，绿色
                        $('#recent-status-time').addClass('text-success');
                    }
                } catch (e) {
                    console.error('日期格式解析错误:', e);
                    $('#recent-status-text').text('解析失败');
                    $('#recent-status-time').text('无效日期');
                }
            } else {
                $('#recent-status-text').text('暂无数据');
                $('#recent-status-time').text('--');
            }
        },
        error: function(xhr, status, error) {
            console.error('获取任务统计失败:', error);
        }
    });
}

// 显示警告消息
function showWarning(message) {
    if (window.showToast) {
        window.showToast(message, 'warning');
    } else {
        console.warn(message);
        alert(message);
    }
}

// 显示成功消息
function showSuccess(message) {
    if (window.showToast) {
        window.showToast(message, 'success');
    } else {
        console.log(message);
        alert(message);
    }
}

// 显示错误消息
function showError(message) {
    if (window.showToast) {
        window.showToast(message, 'error');
    } else {
        console.error(message);
        alert(message);
    }
}