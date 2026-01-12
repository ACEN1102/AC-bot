// 任务管理模块

// 加载任务列表
function loadTasks() {
    $.ajax({
        url: '/api/tasks',
        type: 'GET',
        dataType: 'json',
        success: function(response) {
            const tasks = response.tasks || [];
            const taskTableBody = $('#task-list-body');
            
            // 清空表格
            taskTableBody.empty();
            
            if (tasks.length === 0) {
                // 显示无任务提示
                taskTableBody.append(`
                    <tr>
                        <td colspan="7" class="px-6 py-10 text-center text-gray-500">
                            <div class="flex flex-col items-center justify-center">
                                <i class="fa fa-calendar-check-o text-4xl mb-3 text-gray-300"></i>
                                <p>暂无任务，请点击上方"新建任务"按钮创建</p>
                            </div>
                        </td>
                    </tr>
                `);
            } else {
                // 填充表格
                tasks.forEach(task => {
                    const typeText = {
                        'custom': '自定义消息',
                        'ai_news': 'AI新闻',
                        'llm': '大模型内容'
                    }[task.type] || task.type;
                    
                    const statusBadge = task.enabled ? 
                        '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">启用</span>' : 
                        '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">禁用</span>';
                    
                    // 格式化执行时间
                    let cron_expression = task.cron_expression;
                    let frequencyDisplay = '每天';
                    
                    if (task.days_of_week) {
                        frequencyDisplay = '每周 ' + formatWeekdays(task.days_of_week);
                    }
                    
                    const hour = cron_expression.split(' ')[2];
                    const minute = cron_expression.split(' ')[1];
                    const second = cron_expression.split(' ')[0];
                    const timeDisplay = `${hour}:${minute}:${second}`;
                    
                    const row = $(`
                        <tr class="hover:bg-gray-50 transition-colors">
                            <td class="px-6 py-4 whitespace-nowrap">${escapeHtml(task.name)}</td>
                            <td class="px-6 py-4 whitespace-nowrap">${typeText}</td>
                            <td class="px-6 py-4 whitespace-nowrap">${timeDisplay}</td>
                            <td class="px-6 py-4 whitespace-nowrap">${frequencyDisplay}</td>
                            <td class="px-6 py-4 whitespace-nowrap">${statusBadge}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${new Date(task.created_at).toLocaleString()}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                <button class="edit-task-btn text-primary hover:text-primary/80 mr-3" data-id="${task.id}" title="编辑">
                                    <i class="fa fa-pencil"></i> 编辑
                                </button>
                                <button class="execute-task-btn text-success hover:text-success/80 mr-3" data-id="${task.id}" title="立即执行">
                                    <i class="fa fa-play"></i> 执行
                                </button>
                                <button class="delete-task-btn text-danger hover:text-danger/80" data-id="${task.id}" data-name="${escapeHtml(task.name)}" title="删除">
                                    <i class="fa fa-trash"></i> 删除
                                </button>
                            </td>
                        </tr>
                    `);
                    
                    taskTableBody.append(row);
                });
            }
        },
        error: function(xhr, status, error) {
            console.error('加载任务失败:', error);
            showError('加载任务失败，请刷新页面重试');
        }
    });
}

// 加载任务详情用于编辑
function loadTaskForEdit(taskId) {
    $.ajax({
        url: '/api/tasks',
        type: 'GET',
        dataType: 'json',
        success: function(response) {
            const tasks = response.tasks || [];
            const task = tasks.find(t => t.id === parseInt(taskId));
            
            if (task) {
                // 填充表单
                $('#task-id').val(task.id);
                $('#task-name').val(task.name);
                $('#task-type').val(task.type);
                $('#webhook-url').val(task.webhook_url);
                
                // 解析cron表达式获取时、分、秒
                const cronParts = task.cron_expression.split(' ');
                if (cronParts.length >= 3) {
                    $('#task-second').val(cronParts[0] || '0');
                    $('#task-minute').val(cronParts[1] || '0');
                    $('#task-hour').val(cronParts[2] || '0');
                }
                
                // 根据任务类型填充相应的内容
                if (task.type === 'custom') {
                    $('#task-content').val(task.content || '');
                } else if (task.type === 'llm') {
                    $('#llm-prompt').val(task.content || '');
                    $('#llm-api-url').val(task.api_url || '');
                    $('#llm-api-key').val(task.api_key || '');
                }
                
                // 设置执行星期
                if (task.days_of_week) {
                    const selectedDays = task.days_of_week.split(',');
                    $('input[name="days_of_week"]').each(function() {
                        $(this).prop('checked', selectedDays.includes($(this).val()));
                    });
                } else {
                    $('input[name="days_of_week"]').prop('checked', false);
                }
                
                // 设置启用状态
                $('#task-enabled').prop('checked', task.enabled);
                
                // 更新模态框标题
                $('#modal-title').text('编辑任务');
                
                // 触发任务类型切换事件以显示正确的内容区域
                $('#task-type').trigger('change');
                
                // 显示模态框
                $('#task-modal').removeClass('hidden');
            } else {
                showError('未找到任务');
            }
        },
        error: function(xhr, status, error) {
            console.error('加载任务详情失败:', error);
            showError('加载任务详情失败，请重试');
        }
    });
}

// 保存任务
function saveTask() {
    // 表单验证
    if (!validateTaskForm()) {
        return;
    }
    
    const taskId = $('#task-id').val();
    const isEdit = !!taskId;
    
    // 构建cron表达式
    const second = $('#task-second').val() || '0';
    const minute = $('#task-minute').val() || '0';
    const hour = $('#task-hour').val() || '0';
    const cron_expression = `${second} ${minute} ${hour} * * *`; // 秒 分 时 日 月 周
    
    // 构建任务数据
    const taskData = {
        name: $('#task-name').val(),
        type: $('#task-type').val(),
        webhook_url: $('#webhook-url').val(),
        cron_expression: cron_expression,
        enabled: $('#task-enabled').prop('checked')
    };
    
    // 根据任务类型添加相应的内容
    if (taskData.type === 'custom') {
        taskData.content = $('#task-content').val();
    } else if (taskData.type === 'llm') {
        taskData.content = $('#llm-prompt').val();
        taskData.api_url = $('#llm-api-url').val();
        taskData.api_key = $('#llm-api-key').val();
    }
    
    // 添加星期设置
    const selectedDays = [];
    $('input[name="days_of_week"]:checked').each(function() {
        selectedDays.push($(this).val());
    });
    taskData.days_of_week = selectedDays.length > 0 ? selectedDays.join(',') : '';
    
    // 发送请求
    let url = '/api/tasks';
    let method = 'POST';
    
    if (isEdit) {
        url = `/api/tasks/${taskId}`;
        method = 'PUT';
    }
    
    $.ajax({
        url: url,
        type: method,
        contentType: 'application/json',
        data: JSON.stringify(taskData),
        success: function(response) {
            if (response.success) {
                // 关闭模态框
                $('#task-modal').addClass('hidden');
                
                // 重置表单
                document.getElementById('task-form').reset();
                
                // 刷新任务列表
                loadTasks();
                
                // 更新统计数据
                updateTaskStats();
                
                // 显示成功提示
                showSuccess(isEdit ? '任务更新成功' : '任务添加成功');
            } else {
                showError(isEdit ? '任务更新失败' : '任务添加失败');
            }
        },
        error: function(xhr, status, error) {
            console.error('保存任务失败:', error);
            showError('保存任务失败，请重试');
        }
    });
}

// 删除任务
function deleteTask(taskId, taskName) {
    if (confirm(`确定要删除任务 "${taskName}" 吗？`)) {
        $.ajax({
            url: `/api/tasks/${taskId}`,
            type: 'DELETE',
            success: function(response) {
                if (response.success) {
                    // 刷新任务列表
                    loadTasks();
                    
                    // 显示成功提示
                    showSuccess('任务删除成功');
                } else {
                    showError('任务删除失败');
                }
            },
            error: function(xhr, status, error) {
                console.error('删除任务失败:', error);
                showError('删除任务失败，请重试');
            }
        });
    }
}

// 执行任务
function executeTask(taskId) {
    $.ajax({
        url: `/api/tasks/${taskId}/execute`,
        type: 'POST',
        success: function(response) {
            if (response.success) {
                showSuccess('任务已开始执行，请查看日志');
                // 延迟加载日志，给任务执行留出时间
                setTimeout(loadLogs, 1000);
            } else {
                showError('任务执行失败');
            }
        },
        error: function(xhr, status, error) {
            console.error('执行任务失败:', error);
            showError('执行任务失败，请重试');
        }
    });
}

// 验证任务表单
function validateTaskForm() {
    const taskName = $('#task-name').val().trim();
    const webhookUrl = $('#webhook-url').val().trim();
    const hour = $('#task-hour').val();
    const minute = $('#task-minute').val();
    const second = $('#task-second').val();
    
    if (!taskName) {
        showWarning('请输入任务名称');
        $('#task-name').focus();
        return false;
    }
    
    if (!webhookUrl) {
        showWarning('请输入飞书Webhook地址');
        $('#webhook-url').focus();
        return false;
    }
    
    // 验证时间输入
    if (hour === '' || minute === '' || second === '') {
        showWarning('请完整设置执行时间');
        return false;
    }
    
    if (isNaN(hour) || isNaN(minute) || isNaN(second)) {
        showWarning('请输入有效的时间数字');
        return false;
    }
    
    if (hour < 0 || hour > 23 || minute < 0 || minute > 59 || second < 0 || second > 59) {
        showWarning('请输入有效的时间范围');
        return false;
    }
    
    // 验证Webhook URL格式
    const urlRegex = /^(https?:\/\/)?([\da-z.-]+)\.([a-z.]{2,6})([/\w .-]*)*\/?$/;
    if (!urlRegex.test(webhookUrl)) {
        showWarning('请输入有效的Webhook URL');
        $('#webhook-url').focus();
        return false;
    }
    
    // 验证自定义消息内容
    if ($('#task-type').val() === 'custom' && !$('#task-content').val().trim()) {
        showWarning('请输入自定义消息内容');
        $('#task-content').focus();
        return false;
    }
    
    // 验证大模型相关配置
    if ($('#task-type').val() === 'llm') {
        if (!$('#llm-prompt').val().trim()) {
            showWarning('请输入大模型提示词');
            $('#llm-prompt').focus();
            return false;
        }
        
        if (!$('#llm-api-url').val().trim()) {
            showWarning('请输入大模型API URL');
            $('#llm-api-url').focus();
            return false;
        }
        
        if (!$('#llm-api-key').val().trim()) {
            showWarning('请输入大模型API Key');
            $('#llm-api-key').focus();
            return false;
        }
    }
    
    return true;
}

// 格式化星期几显示
function formatWeekdays(weekdays) {
    const dayMap = {
        '0': '周日',
        '1': '周一',
        '2': '周二',
        '3': '周三',
        '4': '周四',
        '5': '周五',
        '6': '周六'
    };
    
    const days = weekdays.split(',');
    return days.map(day => dayMap[day] || day).join('、');
}

// HTML转义
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}