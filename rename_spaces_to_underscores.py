import os
import sys
import re
import unicodedata

def clean_filename(name):
    """
    智能清理文件名中的不规范字符
    
    Args:
        name: 原始文件名
    
    Returns:
        清理后的文件名
    """
    # 分离文件扩展名
    name_parts = name.rsplit('.', 1)
    filename = name_parts[0]
    extension = name_parts[1] if len(name_parts) > 1 else ""
    
    # 1. 替换空格为下划线
    filename = filename.replace(' ', '_')
    
    # 2. 替换Windows不允许的特殊字符
    windows_forbidden = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
    for char in windows_forbidden:
        filename = filename.replace(char, '')
    
    # 3. 智能处理括号
    # 保留括号内的内容，但移除括号本身
    brackets_mapping = {
        '(': ')', '[': ']', '{': '}', '（': '）', '【': '】', '「': '」', '『': '』'
    }
    
    for open_bracket, close_bracket in brackets_mapping.items():
        # 查找所有括号对并提取内容
        pattern = f'\\{open_bracket}([^{open_bracket}{close_bracket}]*)\\{close_bracket}'
        if open_bracket in '（【「『':  # 处理中文括号
            pattern = f'{open_bracket}([^{open_bracket}{close_bracket}]*){close_bracket}'
        
        # 使用正则表达式查找并替换所有匹配的括号对
        def bracket_replace(match):
            inner_content = match.group(1)
            return '_' + inner_content if inner_content else ''
        
        filename = re.sub(pattern, bracket_replace, filename)
    
    # 4. 更智能地处理其他字符
    char_mapping = {
        '%': 'percent',
        '&': 'and',
        '$': 'dollar',
        '#': 'hash',
        '@': 'at',
        '!': '',
        '+': 'plus',
        '=': 'equals',
        ';': '',
        ',': '',
        ''': '',  # 智能单引号
        ''': '',  # 智能单引号
        '"': '',  # 智能双引号
        '"': '',  # 智能双引号
        '…': '',  # 省略号
        '—': '-',  # 破折号转连字符
        '–': '-',  # 短破折号转连字符
    }
    
    for char, replacement in char_mapping.items():
        filename = filename.replace(char, '_' + replacement + '_' if replacement else '')
    
    # 5. 标准化Unicode字符（例如将重音字符转换为基本ASCII）
    filename = unicodedata.normalize('NFKD', filename).encode('ASCII', 'ignore').decode('ASCII')
    
    # 6. 处理连续的下划线
    filename = re.sub('_+', '_', filename)
    
    # 7. 移除开头和结尾的点和下划线
    filename = filename.strip('._')
    
    # 8. 确保文件名不为空
    if not filename:
        filename = "renamed_file"
    
    # 组合文件名和扩展名
    return filename + ('.' + extension if extension else '')

def rename_files_and_dirs(start_path, dry_run=False):
    """
    递归遍历目录，智能清理文件和文件夹名称
    
    Args:
        start_path: 起始目录路径
        dry_run: 是否只模拟而不实际重命名
    """
    changes = []
    
    # 遍历所有文件和文件夹
    for root, dirs, files in os.walk(start_path, topdown=False):
        # 先处理文件
        for name in files:
            new_name = clean_filename(name)
            if new_name != name:
                old_path = os.path.join(root, name)
                new_path = os.path.join(root, new_name)
                changes.append((old_path, new_path))
                
                if not dry_run:
                    try:
                        os.rename(old_path, new_path)
                        print(f"已重命名文件: {old_path} -> {new_path}")
                    except Exception as e:
                        print(f"重命名文件 {old_path} 时出错: {e}")
        
        # 再处理文件夹
        for name in dirs:
            new_name = clean_filename(name)
            if new_name != name:
                old_path = os.path.join(root, name)
                new_path = os.path.join(root, new_name)
                changes.append((old_path, new_path))
                
                if not dry_run:
                    try:
                        os.rename(old_path, new_path)
                        print(f"已重命名文件夹: {old_path} -> {new_path}")
                    except Exception as e:
                        print(f"重命名文件夹 {old_path} 时出错: {e}")
    
    return changes

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='智能重命名文件和文件夹，清理特殊字符')
    parser.add_argument('path', nargs='?', default='.', help='要处理的目录路径（默认为当前目录）')
    parser.add_argument('--dry-run', action='store_true', help='只显示将要重命名的文件，不实际执行重命名')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.path):
        print(f"错误: 路径 '{args.path}' 不存在")
        sys.exit(1)
    
    print(f"开始处理目录: {os.path.abspath(args.path)}")
    
    if args.dry_run:
        print("模拟运行模式（不会实际重命名文件）:")
        changes = rename_files_and_dirs(args.path, dry_run=True)
        for old_path, new_path in changes:
            print(f"将重命名: {old_path} -> {new_path}")
        print(f"共有 {len(changes)} 个文件/文件夹需要重命名")
    else:
        rename_files_and_dirs(args.path)
        print("处理完成")
