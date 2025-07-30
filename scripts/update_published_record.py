#!/usr/bin/env python3
import json
import os
from pathlib import Path
from datetime import datetime

def check_platform_publish_results():
    """检查各平台的实际发布结果"""
    results = {}
    
    # 检查是否存在发布结果文件
    result_files = {
        'wechat': Path('config/wechat_result.json'),
        'juejin': Path('config/juejin_result.json'), 
        'zhihu': Path('config/zhihu_result.json')
    }
    
    for platform, result_file in result_files.items():
        if result_file.exists():
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    result_data = json.load(f)
                    results[platform] = {
                        'success': result_data.get('success', False),
                        'message': result_data.get('message', '')
                    }
                # 处理完后删除结果文件
                result_file.unlink()
            except Exception as e:
                results[platform] = {
                    'success': False,
                    'message': f'读取发布结果失败: {e}'
                }
        else:
            # 如果没有结果文件，说明该平台被跳过了
            results[platform] = {
                'success': False,
                'message': '未配置认证信息，跳过发布'
            }
    
    return results

def update_published_record():
    """更新发布记录"""
    
    # 检查摘要文件
    summary_file = Path('config/latest_summary.json')
    if not summary_file.exists():
        print("未找到发布摘要文件")
        return
    
    # 加载摘要信息
    with open(summary_file, 'r', encoding='utf-8') as f:
        summary = json.load(f)
    
    # 加载现有发布记录
    published_record_file = Path('config/published.json')
    if published_record_file.exists():
        with open(published_record_file, 'r', encoding='utf-8') as f:
            published_record = json.load(f)
    else:
        published_record = {}
    
    # 更新记录
    current_time = datetime.now().isoformat()
    
    # 兼容不同的数据格式
    articles = []
    if 'articles' in summary:
        articles = summary['articles']
    elif 'article_info' in summary:
        articles = [summary['article_info']]
    
    processed_count = 0
    for article in articles:
        file_key = str(Path(article['path']).relative_to('articles'))
        
        # 如果记录不存在，创建新记录
        if file_key not in published_record:
            published_record[file_key] = {}
        
        # 更新基本信息
        published_record[file_key].update({
            'title': article['title'],
            'content_hash': article.get('content_hash', ''),
            'last_updated': current_time,
            'platforms': published_record[file_key].get('platforms', {})
        })
        
        # 检查实际发布状态
        platform_results = check_platform_publish_results()
        
        # 更新各平台发布状态
        platforms = ['wechat', 'juejin', 'zhihu']
        for platform in platforms:
            if platform not in published_record[file_key]['platforms']:
                published_record[file_key]['platforms'][platform] = {}
            
            # 根据实际发布结果更新状态
            if platform in platform_results:
                published_record[file_key]['platforms'][platform].update({
                    'published': platform_results[platform]['success'],
                    'published_time': current_time if platform_results[platform]['success'] else None,
                    'status': 'success' if platform_results[platform]['success'] else 'skipped',
                    'message': platform_results[platform].get('message', '')
                })
            else:
                # 默认为跳过状态
                published_record[file_key]['platforms'][platform].update({
                    'published': False,
                    'published_time': None,
                    'status': 'skipped',
                    'message': '未配置相关认证信息'
                })
        
        processed_count += 1
        print(f"  📝 已更新: {article['title']}")
    
    # 保存更新后的记录
    published_record_file.parent.mkdir(exist_ok=True)
    with open(published_record_file, 'w', encoding='utf-8') as f:
        json.dump(published_record, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 发布记录已更新，共处理 {processed_count} 篇文章")
    
    # 清理临时文件
    if summary_file.exists():
        summary_file.unlink()
        print("📄 已清理临时摘要文件")

def main():
    """主函数"""
    try:
        update_published_record()
    except Exception as e:
        print(f"❌ 更新发布记录失败: {e}")
        exit(1)

if __name__ == "__main__":
    main()