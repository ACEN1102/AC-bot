import json
import hmac
import hashlib
from datetime import datetime
from utils.logger import logger

def verify_gitlab_signature(token, request_body, signature_header):
    """验证GitLab Webhook签名"""
    logger.info("验证GitLab Webhook签名")
    if not token or not signature_header:
        logger.warning("签名验证失败: 缺少token或signature_header")
        return False
    
    # GitLab签名格式：'sha256=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
    if not signature_header.startswith('sha256='):
        logger.warning(f"签名验证失败: 无效的签名格式: {signature_header}")
        return False
    
    signature = signature_header.split('=')[1]
    expected_signature = hmac.new(
        token.encode('utf-8'),
        request_body,
        hashlib.sha256
    ).hexdigest()
    
    result = hmac.compare_digest(expected_signature, signature)
    if result:
        logger.info("签名验证成功")
    else:
        logger.warning("签名验证失败: 签名不匹配")
    return result

def parse_gitlab_event(event_type, event_data):
    """解析GitLab事件数据"""
    logger.info(f"解析GitLab事件: {event_type}")
    if event_type == 'Push Hook':
        return _parse_push_event(event_data)
    elif event_type == 'Merge Request Hook':
        return _parse_merge_request_event(event_data)
    elif event_type == 'Issue Hook':
        return _parse_issue_event(event_data)
    elif event_type == 'Pipeline Hook':
        return _parse_pipeline_event(event_data)
    elif event_type == 'Tag Push Hook':
        return _parse_tag_push_event(event_data)
    else:
        logger.warning(f"未知GitLab事件类型: {event_type}")
        return f"未知GitLab事件类型: {event_type}", False

def _parse_push_event(event_data):
    """解析Push事件"""
    logger.info("解析GitLab Push事件")
    project_name = event_data.get('project', {}).get('name', '未知项目')
    user_name = event_data.get('user_name', '未知用户')
    ref = event_data.get('ref', '').split('/')[-1]  # 获取分支名
    commits = event_data.get('commits', [])
    commit_count = len(commits)
    compare_url = event_data.get('compare_url', '')
    
    logger.debug(f"Push事件详情: 项目={project_name}, 用户={user_name}, 分支={ref}, 提交数={commit_count}")
    
    # 生成提交信息
    commit_messages = []
    for commit in commits[:5]:  # 只显示最近5个提交
        commit_message = commit.get('message', '').split('\n')[0]  # 只显示第一行
        commit_author = commit.get('author', {}).get('name', '未知作者')
        commit_messages.append(f"  • {commit_author}: {commit_message}")
    
    if commit_count > 5:
        commit_messages.append(f"  • ... 还有 {commit_count - 5} 个提交")
    
    commit_text = '\n'.join(commit_messages)
    
    # 生成飞书消息
    message = f"🚀 **GitLab Push事件**\n"
    message += f"📦 项目: {project_name}\n"
    message += f"👤 用户: {user_name}\n"
    message += f"🌿 分支: {ref}\n"
    message += f"📝 提交: {commit_count} 个新提交\n"
    message += f"📋 提交详情:\n{commit_text}\n"
    message += f"🔗 对比链接: {compare_url}\n"
    message += f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    return message, True

def _parse_merge_request_event(event_data):
    """解析Merge Request事件"""
    logger.info("解析GitLab Merge Request事件")
    project_name = event_data.get('project', {}).get('name', '未知项目')
    user_name = event_data.get('user', {}).get('name', '未知用户')
    merge_request = event_data.get('object_attributes', {})
    
    mr_title = merge_request.get('title', '未命名合并请求')
    mr_state = merge_request.get('state', 'unknown')
    mr_source_branch = merge_request.get('source_branch', '未知源分支')
    mr_target_branch = merge_request.get('target_branch', '未知目标分支')
    mr_url = merge_request.get('url', '')
    mr_action = merge_request.get('action', 'unknown')
    
    logger.debug(f"Merge Request事件详情: 项目={project_name}, 用户={user_name}, 标题={mr_title}, 操作={mr_action}")
    
    # 确定操作类型
    action_text = {}
    if mr_action == 'open':
        action_text = '创建了'
    elif mr_action == 'close':
        action_text = '关闭了'
    elif mr_action == 'merge':
        action_text = '合并了'
    elif mr_action == 'reopen':
        action_text = '重新打开了'
    elif mr_action == 'update':
        action_text = '更新了'
    else:
        action_text = mr_action
    
    # 确定状态文本
    state_text = {}
    if mr_state == 'opened':
        state_text = '🔓 打开'
    elif mr_state == 'merged':
        state_text = '✅ 已合并'
    elif mr_state == 'closed':
        state_text = '❌ 已关闭'
    else:
        state_text = mr_state
    
    # 生成飞书消息
    message = f"🔀 **GitLab Merge Request事件**\n"
    message += f"📦 项目: {project_name}\n"
    message += f"👤 用户: {user_name} {action_text}合并请求\n"
    message += f"📝 标题: {mr_title}\n"
    message += f"🌿 分支: {mr_source_branch} → {mr_target_branch}\n"
    message += f"📊 状态: {state_text}\n"
    message += f"🔗 链接: {mr_url}\n"
    message += f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    return message, True

def _parse_issue_event(event_data):
    """解析Issue事件"""
    logger.info("解析GitLab Issue事件")
    project_name = event_data.get('project', {}).get('name', '未知项目')
    user_name = event_data.get('user', {}).get('name', '未知用户')
    issue = event_data.get('object_attributes', {})
    
    issue_title = issue.get('title', '未命名问题')
    issue_description = issue.get('description', '')[:100] + '...' if len(issue.get('description', '')) > 100 else issue.get('description', '')
    issue_state = issue.get('state', 'unknown')
    issue_url = issue.get('url', '')
    issue_action = issue.get('action', 'unknown')
    
    logger.debug(f"Issue事件详情: 项目={project_name}, 用户={user_name}, 标题={issue_title}, 操作={issue_action}")
    
    # 确定操作类型
    action_text = {}
    if issue_action == 'open':
        action_text = '创建了'
    elif issue_action == 'close':
        action_text = '关闭了'
    elif issue_action == 'reopen':
        action_text = '重新打开了'
    elif issue_action == 'update':
        action_text = '更新了'
    else:
        action_text = issue_action
    
    # 确定状态文本
    state_text = {}
    if issue_state == 'opened':
        state_text = '🔓 打开'
    elif issue_state == 'closed':
        state_text = '❌ 已关闭'
    else:
        state_text = issue_state
    
    # 生成飞书消息
    message = f"📋 **GitLab Issue事件**\n"
    message += f"📦 项目: {project_name}\n"
    message += f"👤 用户: {user_name} {action_text}问题\n"
    message += f"📝 标题: {issue_title}\n"
    message += f"📊 状态: {state_text}\n"
    message += f"📄 描述: {issue_description}\n"
    message += f"🔗 链接: {issue_url}\n"
    message += f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    return message, True

def _parse_pipeline_event(event_data):
    """解析Pipeline事件"""
    logger.info("解析GitLab Pipeline事件")
    project_name = event_data.get('project', {}).get('name', '未知项目')
    user_name = event_data.get('user', {}).get('name', '未知用户')
    pipeline = event_data.get('object_attributes', {})
    
    pipeline_id = pipeline.get('id', 'unknown')
    pipeline_status = pipeline.get('status', 'unknown')
    pipeline_ref = pipeline.get('ref', 'unknown')
    pipeline_url = pipeline.get('url', '')
    
    logger.debug(f"Pipeline事件详情: 项目={project_name}, 用户={user_name}, ID={pipeline_id}, 状态={pipeline_status}")
    
    # 确定状态文本和emoji
    status_info = {
        'success': ('✅ 成功', 'success'),
        'failed': ('❌ 失败', 'failed'),
        'pending': ('⏳ 等待', 'pending'),
        'running': ('🏃 运行中', 'running'),
        'canceled': ('🚫 已取消', 'canceled'),
        'skipped': ('⏭️ 已跳过', 'skipped')
    }
    
    status_text, status_type = status_info.get(pipeline_status, (pipeline_status, 'unknown'))
    
    # 生成飞书消息
    message = f"🔄 **GitLab Pipeline事件**\n"
    message += f"📦 项目: {project_name}\n"
    message += f"👤 用户: {user_name}\n"
    message += f"🌿 分支/标签: {pipeline_ref}\n"
    message += f"📊 Pipeline ID: {pipeline_id}\n"
    message += f"📋 状态: {status_text}\n"
    message += f"🔗 链接: {pipeline_url}\n"
    message += f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    return message, True

def _parse_tag_push_event(event_data):
    """解析Tag Push事件"""
    logger.info("解析GitLab Tag Push事件")
    project_name = event_data.get('project', {}).get('name', '未知项目')
    user_name = event_data.get('user_name', '未知用户')
    ref = event_data.get('ref', '').split('/')[-1]  # 获取标签名
    compare_url = event_data.get('compare_url', '')
    
    logger.debug(f"Tag Push事件详情: 项目={project_name}, 用户={user_name}, 标签={ref}")
    
    # 生成飞书消息
    message = f"🏷️ **GitLab Tag Push事件**\n"
    message += f"📦 项目: {project_name}\n"
    message += f"👤 用户: {user_name}\n"
    message += f"🏷️ 标签: {ref}\n"
    message += f"🔗 对比链接: {compare_url}\n"
    message += f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    return message, True
