document.addEventListener('DOMContentLoaded', function() {
    // 元素引用
    const taskModal = document.getElementById('task-modal');
    const closeModalBtn = document.getElementById('close-modal-btn');
    const cancelTaskBtn = document.getElementById('cancel-task-btn');
    const addTaskBtn = document.getElementById('add-task-btn');
    const taskForm = document.getElementById('task-form');
    const taskListBody = document.getElementById('task-list-body');
    const logsListBody = document.getElementById('logs-list-body');
    const refreshTasksBtn = document.getElementById('refresh-tasks-btn');
    const taskType = document.getElementById('task-type');
    const customContentSection = document.getElementById('custom-content-section');
    const llmConfigSection = document.getElementById('llm-config-section');
    const gitlabConfigSection = document.getElementById('gitlab-config-section');
    const githubConfigSection = document.getElementById('github-config-section');
    const testConnectionBtn = document.getElementById('test-connection-btn');
    const testConnectionModal = document.getElementById('test-connection-modal');
    const closeTestModalBtn = document.getElementById('close-test-modal-btn');
    const cancelTestBtn = document.getElementById('cancel-test-btn');
    const testConnectionForm = document.getElementById('test-connection-form');
    const taskSearch = document.getElementById('task-search');
    const clearLogsBtn = document.getElementById('clear-logs-btn');
    const totalTasksCard = document.getElementById('total-tasks-card');
    const enabledTasksCard = document.getElementById('enabled-tasks-card');
    const recentStatusText = document.getElementById('recent-status-text');
    const recentStatusTime = document.getElementById('recent-status-time');
    const taskHour = document.getElementById('task-hour');
    const taskMinute = document.getElementById('task-minute');
    const taskSecond = document.getElementById('task-second');
    // 初始化
    loadTasks();
    loadLogs();
    loadDashboardStats();

    // 加载任务列表
    function loadTasks() {
        fetch('/api/tasks')
            .then(response => response.json())
            .then(data => {
                if (data.tasks && data.tasks.length > 0) {
                    const searchTerm = taskSearch.value.toLowerCase();
                    const filteredTasks = data.tasks.filter(task => 
                        task.name.toLowerCase().includes(searchTerm)
                    );
                    
                    taskListBody.innerHTML = '';
                    filteredTasks.forEach(task => {
                        const row = document.createElement('tr');
                        row.className = 'fade-in';
                        
                        // 任务类型显示
                        let typeDisplay = '';
                        let typeClass = '';
                        switch (task.type) {
                            case 'custom':
                                typeDisplay = '自定义消息';
                                typeClass = 'task-type-custom';
                                break;
                            case 'ai_news':
                                typeDisplay = 'AI新闻';
                                typeClass = 'task-type-ai_news';
                                break;
                            case 'llm':
                                typeDisplay = '大模型内容';
                                typeClass = 'task-type-llm';
                                break;
                            case 'gitlab':
                                typeDisplay = 'GitLab事件';
                                typeClass = 'task-type-gitlab';
                                break;
                            case 'github':
                                typeDisplay = 'GitHub事件';
                                typeClass = 'task-type-github';
                                break;
                            default:
                                typeDisplay = '未知类型';
                                typeClass = '';
                        }
                        
                        // 执行时间格式化
                        const cronParts = task.cron_expression.split(':');
                        const timeDisplay = `${cronParts[0].padStart(2, '0')}:${cronParts[1].padStart(2, '0')}:${cronParts[2].padStart(2, '0')}`;
                        
                        // 星期几显示
                        let daysDisplay = '每天';
                        if (task.days_of_week) {
                            const days = task.days_of_week.split(',');
                            const dayNames = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
                            daysDisplay = days.map(day => dayNames[parseInt(day)]).join(',');
                        }
                        
                        // 状态显示
                        const statusDisplay = task.enabled ? 
                            '<span class="inline-flex items-center text-success"><span class="status-indicator status-indicator-success"></span>已启用</span>' : 
                            '<span class="inline-flex items-center text-gray-500"><span class="status-indicator"></span>已禁用</span>';
                        
                        // 创建时间格式化
                        const createdAt = new Date(task.created_at);
                        const dateDisplay = `${createdAt.getFullYear()}-${String(createdAt.getMonth() + 1).padStart(2, '0')}-${String(createdAt.getDate()).padStart(2, '0')}`;
                        
                        row.innerHTML = `
                            <td class="px-6 py-4 whitespace-nowrap">
                                <div class="font-medium text-gray-900">${task.name}</div>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <span class="px-2 py-1 text-xs rounded-full ${typeClass}">${typeDisplay}</span>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <div class="text-sm text-gray-900">${timeDisplay}</div>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <div class="text-sm text-gray-900">${daysDisplay}</div>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                ${statusDisplay}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                ${dateDisplay}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                <button onclick="editTask(${task.id})" class="text-primary hover:text-primary/80 mr-3">
                                    <i class="fa fa-pencil"></i> 编辑
                                </button>
                                <button onclick="toggleTaskStatus(${task.id}, ${!task.enabled})" class="text-warning hover:text-warning/80 mr-3">
                                    <i class="fa fa-power-off"></i> ${task.enabled ? '禁用' : '启用'}
                                </button>
                                <button onclick="deleteTask(${task.id})" class="text-danger hover:text-danger/80">
                                    <i class="fa fa-trash"></i> 删除
                                </button>
                            </td>
                        `;
                        
                        taskListBody.appendChild(row);
                    });
                } else {
                    taskListBody.innerHTML = `
                        <tr>
                            <td colspan="7" class="px-6 py-10 text-center text-gray-500">
                                <div class="flex flex-col items-center justify-center">
                                    <i class="fa fa-calendar-check-o text-4xl mb-3 text-gray-300"></i>
                                    <p>暂无任务，请点击上方"新建任务"按钮创建</p>
                                </div>
                            </td>
                        </tr>
                    `;
                }
            })
            .catch(error => {
                console.error('加载任务失败:', error);
                showToast('加载任务失败，请刷新页面重试', 'error');
            });
    }

    // 加载日志列表
    function loadLogs() {
        fetch('/api/logs')
            .then(response => response.json())
            .then(data => {
                if (data.logs && data.logs.length > 0) {
                    logsListBody.innerHTML = '';
                    data.logs.forEach(log => {
                        const row = document.createElement('tr');
                        row.className = 'fade-in';
                        
                        // 状态显示
                        const statusClass = log.status === '成功' ? 'text-success' : 'text-danger';
                        const statusIcon = log.status === '成功' ? 'fa-check-circle' : 'fa-times-circle';
                        
                        // 执行时间格式化
                        const createdAt = new Date(log.created_at);
                        const timeDisplay = `${createdAt.getFullYear()}-${String(createdAt.getMonth() + 1).padStart(2, '0')}-${String(createdAt.getDate()).padStart(2, '0')} ${String(createdAt.getHours()).padStart(2, '0')}:${String(createdAt.getMinutes()).padStart(2, '0')}:${String(createdAt.getSeconds()).padStart(2, '0')}`;
                        
                        row.innerHTML = `
                            <td class="px-6 py-4 whitespace-nowrap">
                                <div class="text-sm font-medium text-gray-900">${log.task_name || '未知任务'}</div>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <span class="inline-flex items-center ${statusClass}">
                                    <i class="fa ${statusIcon} mr-1"></i> ${log.status}
                                </span>
                            </td>
                            <td class="px-6 py-4 text-sm text-gray-900 max-w-xs truncate" title="${log.message}">
                                ${log.message}
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                ${timeDisplay}
                            </td>
                        `;
                        
                        logsListBody.appendChild(row);
                    });
                } else {
                    logsListBody.innerHTML = `
                        <tr>
                            <td colspan="4" class="px-6 py-10 text-center text-gray-500">
                                <div class="flex flex-col items-center justify-center">
                                    <i class="fa fa-history text-4xl mb-3 text-gray-300"></i>
                                    <p>暂无执行日志</p>
                                </div>
                            </td>
                        </tr>
                    `;
                }
            })
            .catch(error => {
                console.error('加载日志失败:', error);
            });
    }

    // 加载仪表盘统计数据
    function loadDashboardStats() {
        fetch('/api/tasks')
            .then(response => response.json())
            .then(data => {
                if (data.tasks) {
                    const totalTasks = data.tasks.length;
                    const enabledTasks = data.tasks.filter(task => task.enabled).length;
                    
                    // 更新卡片数据
                    totalTasksCard.querySelector('h3').textContent = totalTasks;
                    enabledTasksCard.querySelector('h3').textContent = enabledTasks;
                }
            })
            .catch(error => {
                console.error('加载统计数据失败:', error);
            });
        
        // 加载最近执行状态
        fetch('/api/logs')
            .then(response => response.json())
            .then(data => {
                if (data.logs && data.logs.length > 0) {
                    const latestLog = data.logs[0];
                    recentStatusText.textContent = latestLog.status;
                    recentStatusText.className = latestLog.status === '成功' ? 'text-3xl font-bold text-success' : 'text-3xl font-bold text-danger';
                    
                    const createdAt = new Date(latestLog.created_at);
                    const timeDisplay = `${createdAt.getFullYear()}-${String(createdAt.getMonth() + 1).padStart(2, '0')}-${String(createdAt.getDate()).padStart(2, '0')} ${String(createdAt.getHours()).padStart(2, '0')}:${String(createdAt.getMinutes()).padStart(2, '0')}:${String(createdAt.getSeconds()).padStart(2, '0')}`;
                    recentStatusTime.textContent = timeDisplay;
                }
            })
            .catch(error => {
                console.error('加载最近执行状态失败:', error);
            });
    }

    // 打开新建任务模态框
    addTaskBtn.addEventListener('click', function() {
        document.getElementById('modal-title').textContent = '新建任务';
        document.getElementById('task-id').value = '';
        taskForm.reset();
        toggleTaskTypeSections();
        taskModal.classList.remove('hidden');
    });

    // 关闭任务模态框
    function closeTaskModal() {
        taskModal.classList.add('hidden');
    }

    closeModalBtn.addEventListener('click', closeTaskModal);
    cancelTaskBtn.addEventListener('click', closeTaskModal);

    // 任务类型切换
    taskType.addEventListener('change', toggleTaskTypeSections);

    function toggleTaskTypeSections() {
        const type = taskType.value;
        const aiNewsSection = document.getElementById('ai-news-config-section');
        
        if (type === 'custom') {
            customContentSection.classList.remove('hidden');
            llmConfigSection.classList.add('hidden');
            gitlabConfigSection.classList.add('hidden');
            githubConfigSection.classList.add('hidden');
            if (aiNewsSection) aiNewsSection.classList.add('hidden');
            // 显示时间输入框
            if (timeSection) timeSection.classList.remove('hidden');
        } else if (type === 'llm') {
            customContentSection.classList.add('hidden');
            llmConfigSection.classList.remove('hidden');
            gitlabConfigSection.classList.add('hidden');
            githubConfigSection.classList.add('hidden');
            if (aiNewsSection) aiNewsSection.classList.add('hidden');
            // 显示时间输入框
            if (timeSection) timeSection.classList.remove('hidden');
        } else if (type === 'ai_news' && aiNewsSection) {
            customContentSection.classList.add('hidden');
            llmConfigSection.classList.add('hidden');
            gitlabConfigSection.classList.add('hidden');
            githubConfigSection.classList.add('hidden');
            aiNewsSection.classList.remove('hidden');
            // 显示时间输入框
            if (timeSection) timeSection.classList.remove('hidden');
        } else if (type === 'gitlab') {
            customContentSection.classList.add('hidden');
            llmConfigSection.classList.add('hidden');
            gitlabConfigSection.classList.remove('hidden');
            githubConfigSection.classList.add('hidden');
            if (aiNewsSection) aiNewsSection.classList.add('hidden');
            // 隐藏时间输入框，GitLab任务不需要定时执行
            if (timeSection) timeSection.classList.add('hidden');
        } else if (type === 'github') {
            customContentSection.classList.add('hidden');
            llmConfigSection.classList.add('hidden');
            gitlabConfigSection.classList.add('hidden');
            githubConfigSection.classList.remove('hidden');
            if (aiNewsSection) aiNewsSection.classList.add('hidden');
            // 隐藏时间输入框，GitHub任务不需要定时执行
            if (timeSection) timeSection.classList.add('hidden');
        } else {
            customContentSection.classList.add('hidden');
            llmConfigSection.classList.add('hidden');
            gitlabConfigSection.classList.add('hidden');
            githubConfigSection.classList.add('hidden');
            if (aiNewsSection) aiNewsSection.classList.add('hidden');
            // 显示时间输入框
            if (timeSection) timeSection.classList.remove('hidden');
        }
    }

    // 提交任务表单
    taskForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const taskId = document.getElementById('task-id').value;
        const name = document.getElementById('task-name').value;
        const type = document.getElementById('task-type').value;
        const webhookUrl = document.getElementById('webhook-url').value;
        const enabled = document.getElementById('task-enabled').checked;
        
        // 只有在非GitLab任务类型时才获取时间值
        let hour = '0';
        let minute = '0';
        let second = '0';
        if (type !== 'gitlab') {
            const hourInput = document.getElementById('task-hour');
            const minuteInput = document.getElementById('task-minute');
            const secondInput = document.getElementById('task-second');
            
            hour = hourInput ? hourInput.value : '0';
            minute = minuteInput ? minuteInput.value : '0';
            second = secondInput ? secondInput.value : '0';
        }
        
        // 收集选中的星期几
        const daysOfWeekElements = document.querySelectorAll('input[name="days_of_week"]:checked');
        const daysOfWeek = Array.from(daysOfWeekElements).map(el => el.value).join(',');
        
        // 构建cron表达式，对于GitLab任务，使用默认值
        let cronExpression = `${hour}:${minute}:${second}`;
        if (type === 'gitlab') {
            // GitLab任务不需要精确的cron表达式，使用默认值
            cronExpression = '0:0:0';
        }
        
        // 根据任务类型获取额外数据并进行验证
        let content = '';
        let apiUrl = '';
        let apiKey = '';
        let aiNewsUrl = '';
        let gitlabUrl = '';
        let gitlabToken = '';
        let gitlabProject = '';
        let gitlabEvents = '';
        let githubUrl = '';
        let githubToken = '';
        let githubProject = '';
        let githubEvents = '';
        
        // 表单验证
        if (type === 'custom') {
            content = document.getElementById('task-content').value;
            if (!content.trim()) {
                showToast('请输入消息内容', 'error');
                return;
            }
        } else if (type === 'llm') {
            content = document.getElementById('llm-prompt').value;
            apiUrl = document.getElementById('llm-api-url').value;
            apiKey = document.getElementById('llm-api-key').value;
            
            if (!content.trim()) {
                showToast('请输入提示词', 'error');
                return;
            }
            if (!apiUrl.trim()) {
                showToast('请输入API URL', 'error');
                return;
            }
            if (!apiKey.trim()) {
                showToast('请输入API Key', 'error');
                return;
            }
        } else if (type === 'ai_news') {
            aiNewsUrl = document.getElementById('ai-news-url').value;
            if (!aiNewsUrl.trim()) {
                showToast('请输入60sAPI URL', 'error');
                return;
            }
        } else if (type === 'gitlab') {
            gitlabUrl = document.getElementById('gitlab-url').value;
            gitlabProject = document.getElementById('gitlab-project').value;
            gitlabToken = document.getElementById('gitlab-token').value;
            
            // 收集选中的事件类型
            const gitlabEventsElements = document.querySelectorAll('input[name="gitlab_events"]:checked');
            gitlabEvents = Array.from(gitlabEventsElements).map(el => el.value).join(',');
            
            if (!gitlabProject.trim()) {
                showToast('请输入GitLab项目路径', 'error');
                return;
            }
            if (!gitlabEvents) {
                showToast('请至少选择一种事件类型', 'error');
                return;
            }
        } else if (type === 'github') {
            githubUrl = document.getElementById('github-url').value;
            githubProject = document.getElementById('github-project').value;
            githubToken = document.getElementById('github-token').value;
            
            // 收集选中的事件类型
            const githubEventsElements = document.querySelectorAll('input[name="github_events"]:checked');
            githubEvents = Array.from(githubEventsElements).map(el => el.value).join(',');
            
            if (!githubProject.trim()) {
                showToast('请输入GitHub项目路径', 'error');
                return;
            }
            if (!githubEvents) {
                showToast('请至少选择一种事件类型', 'error');
                return;
            }
        }
        
        // 构建请求数据
        const taskData = {
            name,
            type,
            webhook_url: webhookUrl,
            cron_expression: cronExpression, // 对于GitLab任务，这个值不会被使用
            enabled,
            days_of_week: daysOfWeek
        };
        
        if (content) taskData.content = content;
        if (apiUrl) taskData.api_url = apiUrl;
        if (apiKey) taskData.api_key = apiKey;
        if (aiNewsUrl) taskData.ai_news_url = aiNewsUrl;
        if (gitlabUrl) taskData.gitlab_url = gitlabUrl;
        if (gitlabToken) taskData.gitlab_token = gitlabToken;
        if (gitlabProject) taskData.gitlab_project = gitlabProject;
        if (gitlabEvents) taskData.gitlab_events = gitlabEvents;
        if (githubUrl) taskData.github_url = githubUrl;
        if (githubToken) taskData.github_token = githubToken;
        if (githubProject) taskData.github_project = githubProject;
        if (githubEvents) taskData.github_events = githubEvents;
        
        // 添加新的配置字段
        const modelNameInput = document.getElementById('llm-model-name');
        if (modelNameInput && modelNameInput.value.trim()) {
            taskData.model_name = modelNameInput.value.trim();
        }
        
        // 发送请求
        let url = '/api/tasks';
        let method = 'POST';
        
        if (taskId) {
            url = `/api/tasks/${taskId}`;
            method = 'PUT';
        }
        
        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(taskData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                closeTaskModal();
                loadTasks();
                loadDashboardStats();
                showToast(taskId ? '任务更新成功' : '任务创建成功', 'success');
            } else {
                showToast(data.message || '操作失败', 'error');
            }
        })
        .catch(error => {
            console.error('提交任务失败:', error);
            showToast('网络错误，请稍后重试', 'error');
        });
    });

    // 打开测试连接模态框
    testConnectionBtn.addEventListener('click', function() {
        testConnectionModal.classList.remove('hidden');
    });

    // 关闭测试连接模态框
    function closeTestConnectionModal() {
        testConnectionModal.classList.add('hidden');
    }

    closeTestModalBtn.addEventListener('click', closeTestConnectionModal);
    cancelTestBtn.addEventListener('click', closeTestConnectionModal);

    // 提交测试连接表单
    testConnectionForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const webhookUrl = document.getElementById('test-webhook-url').value;
        const message = document.getElementById('test-message').value;
        
        // 显示加载状态
        const submitBtn = testConnectionForm.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa fa-spinner fa-spin mr-1"></i> 发送中...';
        
        fetch('/api/test_webhook', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ webhook_url: webhookUrl, message: message })
        })
        .then(response => response.json())
        .then(data => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
            
            if (data.success) {
                showToast('测试消息发送成功，请查看飞书群', 'success');
            } else {
                showToast('测试消息发送失败: ' + data.message, 'error');
            }
        })
        .catch(error => {
            console.error('测试连接失败:', error);
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
            showToast('网络错误，请稍后重试', 'error');
        });
    });

    // 刷新任务列表
    refreshTasksBtn.addEventListener('click', function() {
        loadTasks();
        loadDashboardStats();
        showToast('任务列表已刷新', 'info');
    });

    // 搜索任务
    taskSearch.addEventListener('input', function() {
        loadTasks();
    });

    // 清空日志
    clearLogsBtn.addEventListener('click', function() {
        if (confirm('确定要清空所有执行日志吗？此操作不可恢复。')) {
            // 注意：后端没有实现清空日志的API，这里仅做前端提示
            showToast('日志清空功能尚未实现', 'warning');
        }
    });

    // 编辑任务
    window.editTask = function(taskId) {
        fetch(`/api/tasks/${taskId}`)
            .then(response => {
                if (!response.ok) throw new Error('任务不存在');
                return response.json();
            })
            .then(data => {
                if (data.task) {
                    const task = data.task;
                    document.getElementById('modal-title').textContent = '编辑任务';
                    document.getElementById('task-id').value = task.id;
                    document.getElementById('task-name').value = task.name;
                    document.getElementById('task-type').value = task.type;
                    document.getElementById('webhook-url').value = task.webhook_url;
                    document.getElementById('task-enabled').checked = task.enabled;
                    
                    // 解析cron表达式
                    const cronParts = task.cron_expression.split(':');
                    document.getElementById('task-hour').value = cronParts[0];
                    document.getElementById('task-minute').value = cronParts[1];
                    document.getElementById('task-second').value = cronParts[2];
                    
                    // 选中星期几
                    const daysOfWeekElements = document.querySelectorAll('input[name="days_of_week"]');
                    daysOfWeekElements.forEach(el => el.checked = false);
                    
                    if (task.days_of_week) {
                        const days = task.days_of_week.split(',');
                        days.forEach(day => {
                            const element = document.querySelector(`input[name="days_of_week"][value="${day}"]`);
                            if (element) element.checked = true;
                        });
                    }
                    
                    // 根据任务类型填充内容
                    if (task.type === 'custom') {
                        document.getElementById('task-content').value = task.content || '';
                    } else if (task.type === 'llm') {
                        document.getElementById('llm-prompt').value = task.content || '';
                        document.getElementById('llm-api-url').value = task.api_url || '';
                        document.getElementById('llm-api-key').value = task.api_key || '';
                        if (task.model_name) {
                            document.getElementById('llm-model-name').value = task.model_name;
                        }
                    } else if (task.type === 'ai_news') {
                        if (task.ai_news_url) {
                            const aiNewsUrlInput = document.getElementById('ai-news-url');
                            if (aiNewsUrlInput) {
                                aiNewsUrlInput.value = task.ai_news_url;
                            }
                        }
                    } else if (task.type === 'gitlab') {
                        document.getElementById('gitlab-url').value = task.gitlab_url || '';
                        document.getElementById('gitlab-project').value = task.gitlab_project || '';
                        document.getElementById('gitlab-token').value = task.gitlab_token || '';
                        
                        // 选中事件类型
                        const gitlabEventsElements = document.querySelectorAll('input[name="gitlab_events"]');
                        gitlabEventsElements.forEach(el => el.checked = false);
                        
                        if (task.gitlab_events) {
                            const events = task.gitlab_events.split(',');
                            events.forEach(event => {
                                const element = document.querySelector(`input[name="gitlab_events"][value="${event}"]`);
                                if (element) element.checked = true;
                            });
                        }
                    } else if (task.type === 'github') {
                        document.getElementById('github-url').value = task.github_url || '';
                        document.getElementById('github-project').value = task.github_project || '';
                        document.getElementById('github-token').value = task.github_token || '';
                        
                        // 选中事件类型
                        const githubEventsElements = document.querySelectorAll('input[name="github_events"]');
                        githubEventsElements.forEach(el => el.checked = false);
                        
                        if (task.github_events) {
                            const events = task.github_events.split(',');
                            events.forEach(event => {
                                const element = document.querySelector(`input[name="github_events"][value="${event}"]`);
                                if (element) element.checked = true;
                            });
                        }
                    }
                    
                    // 切换显示相应的表单部分
                    toggleTaskTypeSections();
                    
                    // 打开模态框
                    taskModal.classList.remove('hidden');
                }
            })
            .catch(error => {
                console.error('获取任务详情失败:', error);
                showToast('加载任务详情失败', 'error');
            });
    };

    // 切换任务状态
    window.toggleTaskStatus = function(taskId, enable) {
        fetch(`/api/tasks/${taskId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ enabled: enable })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadTasks();
                loadDashboardStats();
                showToast(enable ? '任务已启用' : '任务已禁用', 'success');
            } else {
                showToast('操作失败', 'error');
            }
        })
        .catch(error => {
            console.error('切换任务状态失败:', error);
            showToast('网络错误，请稍后重试', 'error');
        });
    };

    // 删除任务
    window.deleteTask = function(taskId) {
        if (confirm('确定要删除这个任务吗？此操作不可恢复。')) {
            fetch(`/api/tasks/${taskId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadTasks();
                    loadDashboardStats();
                    showToast('任务已删除', 'success');
                } else {
                    showToast('删除失败', 'error');
                }
            })
            .catch(error => {
                console.error('删除任务失败:', error);
                showToast('网络错误，请稍后重试', 'error');
            });
        }
    };

    // 显示提示消息
    function showToast(message, type = 'info') {
        // 检查是否已存在toast，存在则移除
        const existingToast = document.querySelector('.toast-notification');
        if (existingToast) {
            existingToast.remove();
        }
        
        // 创建新的toast
        const toast = document.createElement('div');
        toast.className = `toast-notification fixed bottom-4 right-4 px-4 py-3 rounded-lg shadow-lg z-50 transform transition-all duration-300 translate-y-0 opacity-100 fade-in`;
        
        // 设置toast样式
        let bgColor = 'bg-blue-500';
        let icon = 'fa-info-circle';
        
        switch (type) {
            case 'success':
                bgColor = 'bg-green-500';
                icon = 'fa-check-circle';
                break;
            case 'error':
                bgColor = 'bg-red-500';
                icon = 'fa-times-circle';
                break;
            case 'warning':
                bgColor = 'bg-yellow-500';
                icon = 'fa-exclamation-triangle';
                break;
            default:
                bgColor = 'bg-blue-500';
                icon = 'fa-info-circle';
        }
        
        toast.classList.add(...bgColor.split(' '));
        toast.innerHTML = `
            <div class="flex items-center text-white">
                <i class="fa ${icon} mr-2"></i>
                <span>${message}</span>
            </div>
        `;
        
        // 添加到页面
        document.body.appendChild(toast);
        
        // 3秒后自动消失
        setTimeout(() => {
            toast.classList.remove('translate-y-0', 'opacity-100');
            toast.classList.add('translate-y-10', 'opacity-0');
            
            // 动画结束后移除元素
            setTimeout(() => {
                if (document.body.contains(toast)) {
                    document.body.removeChild(toast);
                }
            }, 300);
        }, 3000);
    }


    // 清空日志
    clearLogsBtn.addEventListener('click', function() {
        if (confirm('确定要清空所有日志吗？此操作不可恢复。')) {
            fetch('/api/clear_logs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadLogs();
                    showToast('日志已清空', 'success');
                } else {
                    showToast('清空日志失败: ' + data.message, 'error');
                }
            })
            .catch(error => {
                console.error('清空日志失败:', error);
                showToast('网络错误，请稍后重试', 'error');
            });
        }
    });

    // 每30秒自动刷新一次任务列表和日志
    setInterval(() => {
        loadTasks();
        loadLogs();
        loadDashboardStats();
    }, 30000);
});