#!/usr/bin/env python3
"""
自动生成技能进度条的脚本
从 GitHub API 获取语言使用情况并生成可视化进度条
"""

import requests
import os
from collections import defaultdict

def get_language_stats(username, token=None):
    """从 GitHub API 获取用户的语言统计"""
    headers = {}
    if token:
        headers['Authorization'] = f'token {token}'
    
    # 获取用户所有公开仓库
    url = f'https://api.github.com/users/{username}/repos'
    params = {'per_page': 100, 'type': 'owner'}
    
    response = requests.get(url, headers=headers, params=params)
    repos = response.json()
    
    # 统计每种语言的字节数
    language_bytes = defaultdict(int)
    
    for repo in repos:
        if isinstance(repo, dict) and not repo.get('fork', False):
            # 获取每个仓库的语言统计
            lang_url = repo.get('languages_url')
            if lang_url:
                lang_response = requests.get(lang_url, headers=headers)
                if lang_response.status_code == 200:
                    languages = lang_response.json()
                    for lang, bytes_count in languages.items():
                        language_bytes[lang] += bytes_count
    
    # 计算总字节数
    total_bytes = sum(language_bytes.values())
    
    # 计算百分比
    language_percentages = {}
    for lang, bytes_count in language_bytes.items():
        percentage = (bytes_count / total_bytes * 100) if total_bytes > 0 else 0
        language_percentages[lang] = round(percentage, 1)
    
    # 按百分比排序
    sorted_languages = sorted(language_percentages.items(), key=lambda x: x[1], reverse=True)
    
    return sorted_languages

def generate_progress_bar(percentage, length=20):
    """生成 ASCII 进度条"""
    filled = int(length * percentage / 100)
    bar = '█' * filled + '░' * (length - filled)
    return bar

def generate_skills_section(languages, max_items=10):
    """生成技能可视化部分"""
    output = "```ascii\n"
    
    # 只显示前 N 种语言
    for lang, percentage in languages[:max_items]:
        # 语言名称，左对齐，宽度 12
        lang_display = f"{lang:<12}"
        
        # 生成进度条
        bar = generate_progress_bar(percentage, 20)
        
        # 百分比，右对齐
        percent_display = f"{percentage:>3.0f}%"
        
        # 额外的视觉进度条
        extra_bar = generate_progress_bar(percentage, 19)
        
        output += f"{lang_display} {bar}   {percent_display} {extra_bar}\n"
    
    output += "```"
    return output

def update_readme(username, token=None):
    """更新 README 文件中的技能部分"""
    
    # 获取语言统计
    languages = get_language_stats(username, token)
    
    if not languages:
        print("No language data found")
        return
    
    # 生成新的技能部分
    new_skills = generate_skills_section(languages)
    
    # 读取现有 README
    readme_path = 'README.md'
    if not os.path.exists(readme_path):
        print(f"README.md not found")
        return
    
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找并替换技能部分
    start_marker = '## 💡 Skills Proficiency'
    end_marker = '</div>'
    
    start_idx = content.find(start_marker)
    if start_idx == -1:
        print("Skills section not found in README")
        return
    
    # 找到技能部分后的第一个 </div>
    section_start = content.find('```ascii', start_idx)
    section_end = content.find('```', section_start + 8) + 3
    
    if section_start == -1 or section_end == -1:
        print("Could not find skills code block")
        return
    
    # 替换内容
    new_content = content[:section_start] + new_skills + content[section_end:]
    
    # 写回文件
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ Updated skills section with {len(languages)} languages")
    print("\nTop 5 languages:")
    for lang, percentage in languages[:5]:
        print(f"  {lang}: {percentage}%")

if __name__ == '__main__':
    # 从环境变量获取配置
    username = os.environ.get('GITHUB_REPOSITORY_OWNER', 'brans-t')
    token = os.environ.get('GITHUB_TOKEN')
    
    print(f"🔄 Updating skills for user: {username}")
    update_readme(username, token)
