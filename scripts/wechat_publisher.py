#!/usr/bin/env python3
import os
import json
import requests
import markdown
import re
import time
from pathlib import Path
from datetime import datetime

class WeChatPublisher:
    def __init__(self):
        self.app_id = os.getenv('WECHAT_APP_ID')
        self.app_secret = os.getenv('WECHAT_APP_SECRET')
        self.author = os.getenv('AUTHOR_NAME', 'HelloDev Team')
        self.source_url = os.getenv('SOURCE_URL', 'https://hellodev.cc')
        self.access_token = None
        self.access_token_expires = 0
        
        if not self.app_id or not self.app_secret:
            raise ValueError("未设置微信公众号配置")
    
    def get_access_token(self):
        """获取access_token"""
        if self.access_token and time.time() < self.access_token_expires:
            return self.access_token
            
        url = f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={self.app_id}&secret={self.app_secret}"
        response = requests.get(url)
        result = response.json()
        
        if 'access_token' in result:
            self.access_token = result['access_token']
            self.access_token_expires = time.time() + result['expires_in'] - 600
            return self.access_token
        else:
            raise Exception(f"获取access_token失败: {result}")
    
    def upload_image(self, image_path):
        """上传图片到微信服务器"""
        access_token = self.get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/media/uploadimg?access_token={access_token}"
        
        with open(image_path, 'rb') as f:
            files = {'media': (os.path.basename(image_path), f, 'image/jpeg')}
            response = requests.post(url, files=files)
            result = response.json()
            
        if 'errcode' not in result and 'url' in result:
            return result['url']
        else:
            raise Exception(f"图片上传失败: {result}")
    
    def upload_thumb_media(self, image_path):
        """上传缩略图素材"""
        print(f"🔍 开始上传缩略图: {image_path}")
        access_token = self.get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={access_token}&type=thumb"
        
        with open(image_path, 'rb') as f:
            files = {'media': (os.path.basename(image_path), f, 'image/jpeg')}
            response = requests.post(url, files=files)
            result = response.json()
            
        if 'errcode' not in result and 'media_id' in result:
            media_id = result['media_id']
            print(f"✅ 缩略图上传成功，media_id: {media_id}")
            return media_id
        else:
            print(f"❌ 缩略图上传失败: {result}")
            raise Exception(f"缩略图上传失败: {result}")
    
    def get_inline_styles(self):
        """获取内联样式映射（微信公众号不支持style标签）"""
        return {
            'body': 'font-family: -apple-system, BlinkMacSystemFont, "Helvetica Neue", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei UI", "Microsoft YaHei", Arial, sans-serif; font-size: 15px; line-height: 1.75; letter-spacing: 0.5px; color: #333333; word-spacing: 1px;',
            'h1': 'font-size: 20px; font-weight: 600; color: #1a365d; border-bottom: 3px solid #4299e1; padding-bottom: 8px; margin: 32px 0 20px 0; line-height: 1.4; letter-spacing: 0.8px;',
            'h2': 'font-size: 18px; font-weight: 600; color: #2d3748; border-left: 4px solid #4299e1; padding-left: 12px; margin: 28px 0 16px 0; line-height: 1.4; letter-spacing: 0.6px;',
            'h3': 'font-size: 16px; font-weight: 600; color: #e53e3e; margin: 24px 0 12px 0; line-height: 1.4; letter-spacing: 0.4px;',
            'p': 'margin: 20px 0; text-align: justify; line-height: 1.75; letter-spacing: 0.5px; word-spacing: 1px; color: #333333;',
            'ul': 'margin: 20px 0; padding-left: 24px;',
            'ol': 'margin: 20px 0; padding-left: 24px;',
            'li': 'margin: 8px 0; line-height: 1.75; color: #333333; letter-spacing: 0.5px;',
            'blockquote': 'border-left: 4px solid #38b2ac; margin: 24px 0; padding: 16px 20px; background-color: #f0fff4; font-style: italic; color: #2d3748; border-radius: 6px; letter-spacing: 0.3px; line-height: 1.75;',
            'code': 'background-color: #f7fafc; padding: 3px 8px; border-radius: 4px; font-family: "Fira Code", Consolas, Monaco, monospace; color: #e53e3e; font-size: 14px; letter-spacing: 0.2px;',
            'pre': 'background-color: #f7fafc; padding: 20px; border-radius: 8px; overflow-x: auto; border-left: 4px solid #4299e1; margin: 24px 0; line-height: 1.5;',
            'pre code': 'background-color: transparent; padding: 0; color: #333333; font-size: 14px; letter-spacing: 0.2px;',
            'strong': 'color: #1a365d; font-weight: 600; letter-spacing: 0.3px;',
            'em': 'color: #38b2ac; font-style: italic; letter-spacing: 0.2px;',
            'img': 'max-width: 100%; height: auto; border-radius: 8px; margin: 24px 0; box-shadow: 0 2px 12px rgba(0,0,0,0.12); display: block;',
            'table': 'border-collapse: collapse; width: 100%; margin: 24px 0; font-size: 14px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08);',
            'th': 'border: 1px solid #e2e8f0; padding: 12px 16px; text-align: left; background-color: #4299e1; color: white; font-weight: 600;',
            'td': 'border: 1px solid #e2e8f0; padding: 12px 16px; text-align: left; color: #333333; letter-spacing: 0.3px;',
            'hr': 'border: none; height: 1px; background-color: #e2e8f0; margin: 32px 0; border-radius: 1px;'
        }
    
    def apply_inline_styles(self, html):
        """将CSS样式转换为内联样式（微信公众号兼容）"""
        from bs4 import BeautifulSoup
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            styles = self.get_inline_styles()
            
            # 应用样式到各个标签
            for tag_name, style in styles.items():
                if tag_name == 'pre code':
                    # 特殊处理 pre code
                    for pre in soup.find_all('pre'):
                        for code in pre.find_all('code'):
                            code['style'] = style
                else:
                    for tag in soup.find_all(tag_name):
                        tag['style'] = style
            
            # 特殊处理表格奇偶行样式
            for table in soup.find_all('table'):
                rows = table.find_all('tr')
                for i, row in enumerate(rows):
                    if i % 2 == 0 and i > 0:  # 偶数行（跳过表头）
                        row['style'] = 'background-color: #f8f9fa;'
            
            return str(soup)
            
        except ImportError:
            print("⚠️  BeautifulSoup4 未安装，无法应用内联样式")
            return html
        except Exception as e:
            print(f"⚠️  应用内联样式失败: {e}")
            return html
    
    def process_markdown_content(self, markdown_content, article_dir):
        """处理Markdown内容，上传图片并转换HTML"""
        
        def replace_images(match):
            img_alt = match.group(1)
            img_path = match.group(2)
            
            # 处理相对路径
            if not img_path.startswith(('http://', 'https://')):
                full_path = Path(article_dir) / img_path
                if full_path.exists():
                    try:
                        wx_url = self.upload_image(str(full_path))
                        # 使用内联样式
                        img_style = self.get_inline_styles()['img']
                        return f'<img src="{wx_url}" alt="{img_alt}" style="{img_style}">'
                    except Exception as e:
                        print(f"⚠️  图片上传失败 {img_path}: {e}")
                        return f'<p>[图片上传失败: {img_alt}]</p>'
            
            # 使用内联样式
            img_style = self.get_inline_styles()['img']
            return f'<img src="{img_path}" alt="{img_alt}" style="{img_style}">'
        
        # 替换图片
        markdown_content = re.sub(r'!\[(.*?)\]\((.*?)\)', replace_images, markdown_content)
        
        # 转换为HTML
        html = markdown.markdown(
            markdown_content,
            extensions=['codehilite', 'tables', 'toc', 'fenced_code'],
            extension_configs={
                'codehilite': {
                    'css_class': 'highlight',
                    'use_pygments': True
                }
            }
        )
        
        # 应用内联样式（微信公众号兼容）
        html_with_styles = self.apply_inline_styles(html)
        
        # 包装在一个带样式的div中
        body_style = self.get_inline_styles()['body']
        return f'<div style="{body_style}">{html_with_styles}</div>'
    
    def create_draft(self, title, content, author, digest, thumb_media_id, source_url):
        """创建草稿"""
        access_token = self.get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/draft/add?access_token={access_token}"
        
        article_data = {
            "title": title,
            "author": author,
            "digest": digest,
            "content": content,
            "content_source_url": source_url,
            "need_open_comment": 1,
            "only_fans_can_comment": 0
        }
        
        # thumb_media_id 是必填字段
        if not thumb_media_id or not thumb_media_id.strip():
            raise Exception("缩略图 media_id 不能为空")
        
        article_data["thumb_media_id"] = thumb_media_id
        
        data = {"articles": [article_data]}
        
        # 确保正确的编码处理
        json_data = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
        
        headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }
        
        response = requests.post(url, data=json_data.encode('utf-8'), headers=headers)
        result = response.json()
        
        if 'errcode' not in result and 'media_id' in result:
            print(f"✅ 草稿创建成功，media_id: {result['media_id']}")
            return result['media_id']
        else:
            raise Exception(f"创建草稿失败: {result}")
    
    def publish_draft(self, media_id):
        """发布草稿"""
        access_token = self.get_access_token()
        url = f"https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token={access_token}"
        
        data = {"media_id": media_id}
        
        # 确保正确的编码处理
        json_data = json.dumps(data, ensure_ascii=False)
        headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }
        
        response = requests.post(url, data=json_data.encode('utf-8'), headers=headers)
        result = response.json()
        
        if 'errcode' not in result and 'publish_id' in result:
            return result.get('publish_id')
        else:
            raise Exception(f"发布失败: {result}")
    
    def truncate_text(self, text, max_length, field_name="文本"):
        """截断文本到指定长度"""
        if len(text) <= max_length:
            return text
        
        # 截断并添加省略号
        truncated = text[:max_length-3] + "..."
        print(f"⚠️  {field_name}过长已截断: {text[:20]}... -> {truncated}")
        return truncated
    
    def publish_article_from_summary(self, article_path, title):
        """根据摘要信息发布文章"""
        file_path = Path(article_path)
        article_dir = file_path.parent
        
        # 处理标题长度限制
        title = self.truncate_text(title, max_length=24, field_name="标题")
        
        # 读取文章内容
        with open(file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # 处理内容
        html_content = self.process_markdown_content(markdown_content, article_dir)
        
        # 生成摘要
        content_text = re.sub(r'[#*`\[\]()]', '', markdown_content)
        digest = content_text[:100].strip() + "..." if len(content_text) > 100 else content_text
        
        # 限制摘要长度为24个字符
        digest = self.truncate_text(digest, max_length=24, field_name="摘要")
        
        # 查找缩略图
        thumb_media_id = ""
        for thumb_name in ['thumb.jpg', 'thumb.jpeg', 'thumb.png', 'cover.jpg', 'cover.png']:
            thumb_path = article_dir / thumb_name
            if thumb_path.exists():
                try:
                    thumb_media_id = self.upload_thumb_media(str(thumb_path))
                    break
                except Exception as e:
                    print(f"⚠️  缩略图上传失败 {thumb_name}: {e}")
                    continue
        
        if not thumb_media_id:
            # 使用默认缩略图
            default_thumb_path = Path(__file__).parent.parent / 'config' / 'default_thumb.jpg'
            if default_thumb_path.exists():
                try:
                    thumb_media_id = self.upload_thumb_media(str(default_thumb_path))
                except Exception as e:
                    raise Exception(f"默认缩略图上传失败: {e}")
            else:
                raise Exception(f"默认缩略图文件不存在: {default_thumb_path}")
        
        # 创建草稿（仅创建草稿，不自动发布）
        media_id = self.create_draft(
            title=title,
            content=html_content,
            author=self.author,
            digest=digest,
            thumb_media_id=thumb_media_id,
            source_url=self.source_url
        )
        
        print(f"✅ 草稿创建成功，可在微信公众号后台查看 (media_id: {media_id})")
        print("ℹ️  草稿已准备就绪，需要手动在微信公众号后台发布")
        
        return {
            'media_id': media_id,
            'draft_created_time': datetime.now().isoformat(),
            'status': 'draft_created'
        }

def main():
    """主函数 - 与 create_summary.py 配合使用"""
    publish_result = {
        'success': False,
        'message': '',
        'details': []
    }
    
    try:
        publisher = WeChatPublisher()
        
        # 检查标准摘要文件
        summary_file = Path('config/latest_summary.json')
        if summary_file.exists():
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary_data = json.load(f)
            
            articles = summary_data.get('article_info', [])
            # 兼容单个文章和文章列表格式
            if isinstance(articles, dict):
                articles = [articles]
            elif 'articles' in summary_data:
                articles = summary_data['articles']
            
            success_count = 0
            for article in articles:
                try:
                    print(f"\n📝 正在创建草稿: {article['title']}")
                    result = publisher.publish_article_from_summary(
                        article['path'], 
                        article['title']
                    )
                    print(f"✅ 草稿创建成功！media_id: {result['media_id']}")
                    publish_result['details'].append({
                        'title': article['title'],
                        'success': True,
                        'media_id': result['media_id']
                    })
                    success_count += 1
                    time.sleep(3)  # 避免频率限制
                except Exception as e:
                    print(f"❌ 文章 {article['title']} 发布失败: {e}")
                    publish_result['details'].append({
                        'title': article['title'],
                        'success': False,
                        'error': str(e)
                    })
            
            publish_result['success'] = success_count > 0
            publish_result['message'] = f"成功发布 {success_count}/{len(articles)} 篇文章"
        else:
            publish_result['message'] = "未找到发布摘要文件: config/latest_summary.json"
            
    except ValueError as e:
        # 未配置认证信息
        publish_result['message'] = str(e)
        print(f"⏭️ 跳过微信发布: {e}")
    except Exception as e:
        publish_result['message'] = f"发布失败: {e}"
        print(f"❌ 草稿创建失败: {e}")
    
    finally:
        # 保存发布结果
        result_file = Path('config/wechat_result.json')
        result_file.parent.mkdir(exist_ok=True)
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(publish_result, f, indent=2, ensure_ascii=False)
        
        if not publish_result['success'] and '未设置微信公众号配置' not in publish_result['message']:
            exit(1)

if __name__ == "__main__":
    main()