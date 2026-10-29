import os
import zipfile
import fnmatch
from datetime import datetime

def should_ignore(path, ignore_patterns):
    for pattern in ignore_patterns:
        pattern = pattern.rstrip('/')
        if pattern == path or path.startswith(pattern + '/') or path.startswith(pattern + '\\'):
            return True
        if fnmatch.fnmatch(path, pattern):
            return True
        if fnmatch.fnmatch(os.path.basename(path), pattern):
            return True
    return False

def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(project_root, '..', f'ACT-team-{timestamp}.zip')
    
    ignore_patterns = [
        'node_modules',
        'frontend/node_modules',
        'frontend/.vscode',
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '.git',
        '.gitignore',
        '.env',
        '.env.local',
        '*.log',
        '.vscode',
        '.trae',
        '*.db',
        '*.sqlite3',
        '*.zip',
        'package_deploy.py',
        'package_team.py',
        'repomix-output.xml',
    ]
    
    print(f"使用 {len(ignore_patterns)} 个忽略规则")
    print(f"打包目录: {project_root}")
    print(f"输出文件: {output_file}")
    
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"删除旧文件")
    
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        added_count = 0
        for root, dirs, files in os.walk(project_root):
            dirs[:] = [d for d in dirs if not should_ignore(os.path.relpath(os.path.join(root, d), project_root), ignore_patterns)]
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, project_root)
                
                if should_ignore(rel_path, ignore_patterns):
                    continue
                
                zf.write(file_path, rel_path)
                added_count += 1
                if added_count % 50 == 0:
                    print(f"  已添加 {added_count} 个文件...")
    
    file_size = os.path.getsize(output_file) / 1024 / 1024
    print(f"\n打包完成!")
    print(f"  文件大小: {file_size:.2f} MB")
    print(f"  文件数量: {added_count}")
    print(f"  输出路径: {output_file}")

if __name__ == '__main__':
    main()
