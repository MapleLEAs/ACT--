"""
ATC监控系统 - 测试套件运行脚本

运行所有测试：python tests/run_tests.py --all
运行单元测试：python tests/run_tests.py --unit
运行集成测试：python tests/run_tests.py --integration
运行压力测试：python tests/run_tests.py --stress
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

def run_command(command, description):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"命令: {command}")
    print()
    
    result = subprocess.run(
        command,
        shell=True,
        capture_output=False, # 让输出直接显示在终端
        text=True,
        cwd=BASE_DIR
    )
    
    return result.returncode == 0

def run_unit_tests():
    """运行单元测试"""
    print("\n" + "="*60)
    print("🧪 运行单元测试")
    print("="*60)
    
    success = run_command(
        "python manage.py test monitor.tests --verbosity=2",
        "Django单元测试"
    )
    
    return success

def run_integration_tests():
    """运行集成测试"""
    print("\n" + "="*60)
    print("🔗 运行集成测试")
    print("="*60)
    
    success = run_command(
        "python manage.py test tests.integration_tests --verbosity=2",
        "Django集成测试"
    )
    
    return success

def run_stress_tests():
    """运行压力测试"""
    print("\n" + "="*60)
    print("⚡ 运行压力测试")
    print("="*60)
    
    success = run_command(
        "python tests/stress_test.py",
        "API压力测试"
    )
    
    return success

def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("🚀 运行完整测试套件")
    print("="*60)
    
    results = {
        '单元测试': run_unit_tests(),
        '集成测试': run_integration_tests(),
        '压力测试': run_stress_tests()
    }
    
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)
    for name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{name}: {status}")
    print("="*60)
    
    return all(results.values())

def main():
    parser = argparse.ArgumentParser(description='ATC监控系统测试运行工具')
    parser.add_argument('--unit', action='store_true', help='运行单元测试')
    parser.add_argument('--integration', action='store_true', help='运行集成测试')
    parser.add_argument('--stress', action='store_true', help='运行压力测试')
    parser.add_argument('--all', action='store_true', help='运行所有测试')
    
    args = parser.parse_args()
    
    # 如果没有指定任何参数，默认显示帮助
    if not any(vars(args).values()):
        parser.print_help()
        return

    if args.all:
        run_all_tests()
    else:
        if args.unit:
            run_unit_tests()
        if args.integration:
            run_integration_tests()
        if args.stress:
            run_stress_tests()

if __name__ == '__main__':
    main()
