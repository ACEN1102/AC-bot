import json
import hmac
import hashlib
from datetime import datetime
from utils.logger import logger

def verify_github_signature(token, request_body, signature_header):
    """验证GitHub Webhook签名"""
    logger.info("验证GitHub Webhook签名")
    
    if not token or not signature_header:
        logger.warning("签名验证失败: 缺少token或signature_header")
        return False
    
    # GitHub使用HMAC签名验证，格式为sha256=xxx
    if not signature_header.startswith('sha256='):
        logger.warning(f"无效的GitHub签名格式: {signature_header}")
        return False
    
    logger.debug("使用HMAC签名验证")
    signature = signature_header.split('=')[1]
    expected_signature = hmac.new(
        token.encode('utf-8'),
        request_body,
        hashlib.sha256
    ).hexdigest()
    
    result = hmac.compare_digest(expected_signature, signature)
    if result:
        logger.info("HMAC签名验证成功")
    else:
        logger.warning("HMAC签名验证失败: 签名不匹配")
    return result

def parse_github_event(event_type, event_data):
    """解析GitHub事件数据"""
    logger.info(f"解析GitHub事件: {event_type}")
    if event_type == 'push':
        return _parse_push_event(event_data)
    elif event_type == 'pull_request':
        return _parse_pull_request_event(event_data)
    elif event_type == 'issues':
        return _parse_issues_event(event_data)
    elif event_type == 'release':
        return _parse_release_event(event_data)
    elif event_type == 'star':
        return _parse_star_event(event_data)
    elif event_type == 'fork':
        return _parse_fork_event(event_data)
    else:
        logger.warning(f"未知GitHub事件类型: {event_type}")
        return f"未知GitHub事件类型: {event_type}", False

def _parse_push_event(event_data):
    """解析Push事件"""
    logger.info("解析GitHub Push事件")
    repository = event_data.get('repository', {})
    project_name = repository.get('name', '未知项目')
    user_name = event_data.get('pusher', {}).get('name', '未知用户')
    ref = event_data.get('ref', '').split('/')[-1]  # 获取分支名
    commits = event_data.get('commits', [])
    commit_count = len(commits)
    compare_url = event_data.get('compare', '')
    
    logger.debug(f"Push事件详情: 项目={project_name}, 用户={user_name}, 分支={ref}, 提交数={commit_count}")
    
    # 生成提交信息，包含每个提交的链接
    commit_messages = []
    for commit in commits[:5]:  # 只显示最近5个提交
        commit_message = commit.get('message', '').split('\n')[0]  # 只显示第一行
        commit_author = commit.get('author', {}).get('name', '未知作者')
        commit_url = commit.get('url', '')
        # 格式化提交信息，包含提交链接
        commit_messages.append(f"  • [{commit_author}]: {commit_message}")
        if commit_url:
            commit_messages.append(f"    🔗 {commit_url}")
    
    if commit_count > 5:
        commit_messages.append(f"  • ... 还有 {commit_count - 5} 个提交")
    
    commit_text = '\n'.join(commit_messages)
    
    # 生成飞书消息
    message = f"🚀 **GitHub Push事件**\n"
    message += f"📦 项目: {project_name}\n"
    message += f"👤 用户: {user_name}\n"
    message += f"🌿 分支: {ref}\n"
    message += f"📝 提交: {commit_count} 个新提交\n"
    if commit_text:
        message += f"📋 提交详情:\n{commit_text}\n"
    if compare_url:
        message += f"🔗 对比链接: {compare_url}\n"
    message += f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    return message, True

def _parse_pull_request_event(event_data):
    """解析Pull Request事件"""
    logger.info("解析GitHub Pull Request事件")
    repository = event_data.get('repository', {})
    project_name = repository.get('name', '未知项目')
    pull_request = event_data.get('pull_request', {})
    user = event_data.get('sender', {})
    user_name = user.get('login', '未知用户')
    
    pr_title = pull_request.get('title', '未命名拉取请求')
    pr_number = pull_request.get('number', 'unknown')
    pr_state = pull_request.get('state', 'unknown')
    pr_action = event_data.get('action', 'unknown')
    pr_source_branch = pull_request.get('head', {}).get('ref', '未知源分支')
    pr_target_branch = pull_request.get('base', {}).get('ref', '未知目标分支')
    pr_url = pull_request.get('html_url', '')
    
    logger.debug(f"Pull Request事件详情: 项目={project_name}, 用户={user_name}, 标题={pr_title}, 操作={pr_action}")
    
    # 确定操作类型
    action_text = {
        'opened': '创建了',
        'closed': '关闭了',
        'merged': '合并了',
        'reopened': '重新打开了',
        'synchronize': '更新了',
        'edited': '编辑了',
        'assigned': '分配了',
        'unassigned': '取消分配了',
        'review_requested': '请求了审查',
        'review_request_removed': '取消了审查请求'
    }.get(pr_action, pr_action)
    
    # 生成飞书消息
    message = f"🔀 **GitHub Pull Request事件**\n"
    message += f"📦 项目: {project_name}\n"
    message += f"👤 用户: {user_name} {action_text}拉取请求\n"
    message += f"📝 标题: #{pr_number} {pr_title}\n"
    message += f"🌿 分支: {pr_source_branch} → {pr_target_branch}\n"
    message += f"📊 状态: {pr_state}\n"
    message += f"🔗 链接: {pr_url}\n"
    message += f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    return message, True

def _parse_issues_event(event_data):
    """解析Issues事件"""
    logger.info("解析GitHub Issues事件")
    repository = event_data.get('repository', {})
    project_name = repository.get('name', '未知项目')
    issue = event_data.get('issue', {})
    user = event_data.get('sender', {})
    user_name = user.get('login', '未知用户')
    
    issue_title = issue.get('title', '未命名问题')
    issue_number = issue.get('number', 'unknown')
    issue_action = event_data.get('action', 'unknown')
    issue_url = issue.get('html_url', '')
    issue_description = issue.get('body', '')[:100] + '...' if len(issue.get('body', '')) > 100 else issue.get('body', '')
    
    logger.debug(f"Issues事件详情: 项目={project_name}, 用户={user_name}, 标题={issue_title}, 操作={issue_action}")
    
    # 确定操作类型
    action_text = {
        'opened': '创建了',
        'closed': '关闭了',
        'reopened': '重新打开了',
        'edited': '编辑了',
        'assigned': '分配了',
        'unassigned': '取消分配了',
        'labeled': '添加了标签',
        'unlabeled': '移除了标签',
        'milestoned': '添加到里程碑',
        'demilestoned': '从里程碑移除'
    }.get(issue_action, issue_action)
    
    # 生成飞书消息
    message = f"📋 **GitHub Issues事件**\n"
    message += f"📦 项目: {project_name}\n"
    message += f"👤 用户: {user_name} {action_text}问题\n"
    message += f"📝 标题: #{issue_number} {issue_title}\n"
    if issue_description:
        message += f"📄 描述: {issue_description}\n"
    message += f"🔗 链接: {issue_url}\n"
    message += f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    return message, True

def _parse_release_event(event_data):
    """解析Release事件"""
    logger.info("解析GitHub Release事件")
    repository = event_data.get('repository', {})
    project_name = repository.get('name', '未知项目')
    release = event_data.get('release', {})
    user = event_data.get('sender', {})
    user_name = user.get('login', '未知用户')
    
    release_tag = release.get('tag_name', 'unknown')
    release_name = release.get('name', release_tag)
    release_action = event_data.get('action', 'published')
    release_url = release.get('html_url', '')
    release_body = release.get('body', '')[:100] + '...' if len(release.get('body', '')) > 100 else release.get('body', '')
    
    logger.debug(f"Release事件详情: 项目={project_name}, 用户={user_name}, 标签={release_tag}, 操作={release_action}")
    
    # 确定操作类型
    action_text = {
        'published': '发布了',
        'edited': '编辑了',
        'deleted': '删除了',
        'prereleased': '预发布了',
        'released': '正式发布了'
    }.get(release_action, release_action)
    
    # 生成飞书消息
    message = f"🏷️ **GitHub Release事件**\n"
    message += f"📦 项目: {project_name}\n"
    message += f"👤 用户: {user_name} {action_text}版本\n"
    message += f"📝 版本名称: {release_name}\n"
    message += f"🏷️ 版本标签: {release_tag}\n"
    if release_body:
        message += f"📄 版本描述: {release_body}\n"
    message += f"🔗 版本链接: {release_url}\n"
    message += f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    return message, True

def _parse_star_event(event_data):
    """解析Star事件"""
    logger.info("解析GitHub Star事件")
    repository = event_data.get('repository', {})
    project_name = repository.get('name', '未知项目')
    user = event_data.get('sender', {})
    user_name = user.get('login', '未知用户')
    
    logger.debug(f"Star事件详情: 项目={project_name}, 用户={user_name}")
    
    # 生成飞书消息
    message = f"⭐ **GitHub Star事件**\n"
    message += f"📦 项目: {project_name}\n"
    message += f"👤 用户: {user_name} 给项目点了Star\n"
    message += f"🔗 项目链接: {repository.get('html_url', '')}\n"
    message += f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    return message, True

def _parse_fork_event(event_data):
    """解析Fork事件"""
    logger.info("解析GitHub Fork事件")
    repository = event_data.get('repository', {})
    project_name = repository.get('name', '未知项目')
    user = event_data.get('sender', {})
    user_name = user.get('login', '未知用户')
    
    logger.debug(f"Fork事件详情: 项目={project_name}, 用户={user_name}")
    
    # 生成飞书消息
    message = f"🍴 **GitHub Fork事件**\n"
    message += f"📦 项目: {project_name}\n"
    message += f"👤 用户: {user_name} Fork了项目\n"
    message += f"🔗 项目链接: {repository.get('html_url', '')}\n"
    message += f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    return message, True
