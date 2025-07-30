#!/usr/bin/env python3
import json
import os
from pathlib import Path
from datetime import datetime

def update_published_record():
    """更新发布记录"""
    
    # 检查摘要文件
    summary_file = Path('publish_summary.json')
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
    
    for article in summary.get('articles', []):
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
        
        # 标记各平台发布状态
        platforms = ['wechat', 'juejin', 'zhihu']
        for platform in platforms:
            if platform not in published_record[file_key]['platforms']:
                published_record[file_key]['platforms'][platform] = {
                    'published': True,
                    'published_time': current_time,
                    'status': 'success'
                }
    
    # 保存更新后的记录
    published_record_file.parent.mkdir(exist_ok=True)
    with open(published_record_file, 'w', encoding='utf-8') as f:
        json.dump(published_record, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 发布记录已更新，共处理 {len(summary.get('articles', []))} 篇文章")
    
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