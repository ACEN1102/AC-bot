// 主入口文件
$(document).ready(function() {
    // 初始化任务列表
    initTasks();
    
    // 初始化日志
    initLogs();
    
    // 初始化测试表单
    initTestForm();
    
    // 初始化任务类型切换
    initTaskTypeSwitch();
    
    // 初始化模态框关闭按钮
    initModalClose();
    
    // 初始化清空日志按钮
    initClearLogsButton();
});

// 初始化任务列表
function initTasks() {
    loadTasks();
    updateTaskStats();
    
    // 添加上下文菜单功能
    $('#task-list-body').on('click', '.edit-task-btn', function() {
        const taskId = $(this).data('id');
        loadTaskForEdit(taskId);
    });
    
    $('#task-list-body').on('click', '.delete-task-btn', function() {
        const taskId = $(this).data('id');
        const taskName = $(this).data('name');
        deleteTask(taskId, taskName);
    });
    
    $('#task-list-body').on('click', '.execute-task-btn', function() {
        const taskId = $(this).data('id');
        executeTask(taskId);
    });
    
    // 表单提交事件
    $('#task-form').submit(function(e) {
        e.preventDefault();
        saveTask();
    });
    
    // 添加任务按钮
    $('#add-task-btn').click(function() {
        resetTaskForm();
        $('#modal-title').text('新建任务');
        $('#task-modal').removeClass('hidden');
    });
    
    // 刷新任务按钮
    $('#refresh-tasks-btn').click(function() {
        loadTasks();
        updateTaskStats();
    });
}

// 初始化日志
function initLogs() {
    loadLogs();
    
    // 定时刷新日志（每10秒）
    setInterval(loadLogs, 10000);
}

// 初始化测试表单
function initTestForm() {
    // 打开测试连接模态框
    $('#test-connection-btn').click(function() {
        $('#test-connection-modal').removeClass('hidden');
    });
    
    // 测试表单提交
    $('#test-connection-form').submit(function(e) {
        e.preventDefault();
        testWebhook();
    });
}

// 初始化任务类型切换
function initTaskTypeSwitch() {
    $('#task-type').change(function() {
        const taskType = $(this).val();
        
        // 隐藏所有内容组
        $('#custom-content-section').addClass('hidden');
        $('#llm-config-section').addClass('hidden');
        
        // 根据任务类型显示对应的内容组
        if (taskType === 'custom') {
            $('#custom-content-section').removeClass('hidden');
        } else if (taskType === 'llm') {
            $('#llm-config-section').removeClass('hidden');
        }
        // AI新闻类型不需要特殊内容输入
    });
}

// 初始化模态框关闭
function initModalClose() {
    // 关闭任务模态框
    $('#close-modal-btn, #cancel-task-btn').click(function() {
        $('#task-modal').addClass('hidden');
    });
    
    // 关闭测试连接模态框
    $('#close-test-modal-btn, #cancel-test-btn').click(function() {
        $('#test-connection-modal').addClass('hidden');
    });
}

// 重置任务表单
function resetTaskForm() {
    $('#taskId').val('');
    $('#taskName').val('');
    $('#taskType').val('custom');
    $('#taskWebhookUrl').val('');
    $('#customContent').val('');
    $('#llmPrompt').val('');
    $('#llmApiUrl').val('');
    $('#llmApiKey').val('');
    $('#dailyFrequency').prop('checked', true);
    $('#weeklyFrequency').prop('checked', false);
    $('#weekdaysGroup').addClass('d-none');
    $('#executionTime').val('');
    $('#enableTask').prop('checked', true);
    
    // 重置星期选择
    $('input[id^="weekday"]').prop('checked', false);
    
    // 触发任务类型切换事件
    $('#taskType').trigger('change');
}

// 显示成功提示
function showSuccess(message) {
    showAlert(message, 'success');
}

// 显示错误提示
function showError(message) {
    showAlert(message, 'danger');
}

// 显示警告提示
function showWarning(message) {
    showAlert(message, 'warning');
}

// 显示信息提示
function showInfo(message) {
    showAlert(message, 'info');
}

// 显示提示框
function showAlert(message, type) {
    const alertDiv = $(`<div class="alert alert-${type} alert-dismissible fade show" role="alert">
        ${message}
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
            <span aria-hidden="true">&times;</span>
        </button>
    </div>`);
    
    // 添加到页面顶部
    $('body').prepend(alertDiv);
    
    // 自动关闭
    setTimeout(function() {
        alertDiv.alert('close');
    }, 3000);
}

// 显示加载中状态
function showLoading(element) {
    const originalContent = element.html();
    element.data('originalContent', originalContent);
    element.html('<i class="fa fa-spinner fa-spin mr-2"></i>加载中...');
    element.prop('disabled', true);
}

// 隐藏加载中状态
function hideLoading(element) {
    const originalContent = element.data('originalContent');
    element.html(originalContent);
    element.prop('disabled', false);
}