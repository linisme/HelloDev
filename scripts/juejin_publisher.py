#!/usr/bin/env python3
import os
import json
import requests
import markdown
import re
from pathlib import Path
from datetime import datetime

class JuejinPublisher:
    def __init__(self):
        self.session_id = os.getenv('JUEJIN_SESSION_ID')
        self.csrf_token = os.getenv('JUEJIN_CSRF_TOKEN')
        
        if not self.session_id or not self.csrf_token:
            raise ValueError("未设置掘金配置，跳过掘金发布")
        
        self.session = requests.Session()
        self.session.cookies.set('sessionid', self.session_id)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'X-CSRFToken': self.csrf_token,
            'Content-Type': 'application/json'
        })
    
    def process_markdown_content(self, markdown_content, article_dir):
        """处理Markdown内容，转换为掘金格式"""
        # 处理图片路径为绝对URL（如果需要的话）
        def replace_images(match):
            img_alt = match.group(1)
            img_path = match.group(2)
            
            # 如果是相对路径，可能需要转换为绝对URL
            if not img_path.startswith(('http://', 'https://')):
                # 这里可以上传到图床或转换为绝对路径
                # 暂时保持原样
                pass
            
            return f'![{img_alt}]({img_path})'
        
        # 替换图片（如果需要处理的话）
        processed_content = re.sub(r'!\[(.*?)\]\((.*?)\)', replace_images, markdown_content)
        
        return processed_content
    
    def create_draft(self, title, content, tags=None):
        """创建掘金草稿"""
        if tags is None:
            tags = ["技术", "开发", "HelloDev"]
        
        # 掘金API接口（示例，实际API可能不同）
        url = "https://api.juejin.cn/content_api/v1/article/create"
        
        data = {
            "title": title,
            "content": content,
            "cover_image": "",
            "is_gfw": 0,
            "result_type": "markdown",
            "link_url": "",
            "edit_type": 10,
            "html_content": markdown.markdown(content),
            "mark_content": content,
            "tag_ids": [],  # 需要获取标签ID
            "category_id": "6809637767543259144"  # 后端分类ID，需要根据实际情况调整
        }
        
        try:
            response = self.session.post(url, json=data)
            result = response.json()
            
            if result.get('err_no') == 0:
                return result.get('data', {}).get('id')
            else:
                raise Exception(f"创建草稿失败: {result}")
                
        except Exception as e:
            print(f"⚠️  掘金发布暂不可用: {e}")
            return None
    
    def publish_article_from_summary(self, article_path, title):
        """根据摘要信息发布文章到掘金"""
        file_path = Path(article_path)
        article_dir = file_path.parent
        
        # 读取文章内容
        with open(file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # 处理内容
        processed_content = self.process_markdown_content(markdown_content, article_dir)
        
        # 创建草稿
        article_id = self.create_draft(title, processed_content)
        
        if article_id:
            return {
                'article_id': article_id,
                'published_time': datetime.now().isoformat(),
                'platform': 'juejin'
            }
        else:
            raise Exception("掘金发布失败")

def main():
    """主函数"""
    publish_result = {
        'success': False,
        'message': '',
        'details': []
    }
    
    try:
        # 检查摘要文件
        summary_file = Path('config/latest_summary.json')
        if not summary_file.exists():
            publish_result['message'] = "未找到发布摘要文件，跳过掘金发布"
            print(publish_result['message'])
            return
        
        with open(summary_file, 'r', encoding='utf-8') as f:
            summary = json.load(f)
        
        publisher = JuejinPublisher()
        
        success_count = 0
        articles = summary.get('articles', [])
        
        for article in articles:
            try:
                print(f"\n📝 正在发布到掘金: {article['title']}")
                result = publisher.publish_article_from_summary(
                    article['path'], 
                    article['title']
                )
                print(f"✅ 掘金发布成功！article_id: {result['article_id']}")
                publish_result['details'].append({
                    'title': article['title'],
                    'success': True,
                    'article_id': result['article_id']
                })
                success_count += 1
            except Exception as e:
                print(f"❌ 文章 {article['title']} 发布失败: {e}")
                publish_result['details'].append({
                    'title': article['title'],
                    'success': False,
                    'error': str(e)
                })
        
        publish_result['success'] = success_count > 0
        publish_result['message'] = f"成功发布 {success_count}/{len(articles)} 篇文章"
            
    except ValueError as e:
        # 未配置认证信息
        publish_result['message'] = str(e)
        print(f"⏭️ 跳过掘金发布: {e}")
    except Exception as e:
        publish_result['message'] = f"发布失败: {e}"
        print(f"❌ 掘金发布失败: {e}")
    
    finally:
        # 保存发布结果
        result_file = Path('config/juejin_result.json')
        result_file.parent.mkdir(exist_ok=True)
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(publish_result, f, indent=2, ensure_ascii=False)
        
        if not publish_result['success'] and '未配置认证信息' not in publish_result['message']:
            exit(1)

if __name__ == "__main__":
    main()