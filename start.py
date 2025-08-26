#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TOEFL单词学习系统启动脚本
支持开发模式和生产模式
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path


def check_dependencies():
    """检查依赖是否安装"""
    try:
        import flask
        import dotenv
        import requests
        import genanki
        print("✓ 核心依赖检查通过")
    except ImportError as e:
        print(f"✗ 依赖检查失败: {e}")
        print("请运行: pip install -r requirements.txt")
        sys.exit(1)


def check_gunicorn():
    """检查Gunicorn是否可用"""
    try:
        import gunicorn
        return True
    except ImportError:
        return False


def start_development():
    """启动开发模式"""
    print("🚀 启动开发模式...")
    print("访问地址: http://localhost:8080")
    print("按 Ctrl+C 停止服务器")
    print("-" * 50)
    
    # 直接运行Flask开发服务器
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    from web_viewer import app
    app.run(debug=True, host='0.0.0.0', port=8080)


def start_production(workers=4, port=8080, host='0.0.0.0'):
    """启动生产模式"""
    if not check_gunicorn():
        print("✗ Gunicorn未安装，自动安装中...")
        subprocess.run([sys.executable, "-m", "pip", "install", "gunicorn>=20.0.0"])
        if not check_gunicorn():
            print("✗ Gunicorn安装失败，请手动安装: pip install gunicorn")
            sys.exit(1)
    
    print("🚀 启动生产模式...")
    print(f"访问地址: http://{host}:{port}")
    print(f"工作进程: {workers}")
    print("按 Ctrl+C 停止服务器")
    print("-" * 50)
    
    # 使用Gunicorn启动
    cmd = [
        "gunicorn",
        "--workers", str(workers),
        "--worker-class", "sync",
        "--worker-connections", "1000",
        "--timeout", "300",  # 5分钟超时，适合AI生成任务
        "--keep-alive", "2",
        "--max-requests", "1000",
        "--max-requests-jitter", "100",
        "--bind", f"{host}:{port}",
        "--access-logfile", "-",
        "--error-logfile", "-",
        "--log-level", "info",
        "web_viewer:app"
    ]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n服务器已停止")


def show_status():
    """显示系统状态"""
    print("📊 TOEFL单词学习系统状态")
    print("=" * 50)
    
    # 检查数据库文件
    db_path = Path("toefl_words.db")
    if db_path.exists():
        size = db_path.stat().st_size
        print(f"✓ 数据库文件: {db_path} ({size} bytes)")
    else:
        print("✗ 数据库文件: 不存在")
    
    # 检查单词文件
    words_path = Path("toefl_words.txt")
    if words_path.exists():
        with open(words_path, 'r', encoding='utf-8') as f:
            word_count = len(f.readlines())
        print(f"✓ 单词文件: {words_path} ({word_count} 个单词)")
    else:
        print("✗ 单词文件: 不存在")
    
    # 检查环境配置
    env_path = Path(".env")
    if env_path.exists():
        print("✓ 环境配置: .env 文件存在")
    else:
        print("✗ 环境配置: .env 文件不存在")
    
    # 检查导出目录
    export_path = Path("anki_export")
    if export_path.exists():
        apkg_files = list(export_path.glob("*.apkg"))
        print(f"✓ Anki导出目录: {len(apkg_files)} 个APKG文件")
    else:
        print("✗ Anki导出目录: 不存在")
    
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="TOEFL单词学习系统启动脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python start.py                    # 开发模式启动
  python start.py --prod             # 生产模式启动
  python start.py --prod --port 9000 # 指定端口的生产模式
  python start.py --status           # 显示系统状态
        """
    )
    
    parser.add_argument('--prod', action='store_true', 
                       help='使用生产模式启动 (Gunicorn)')
    parser.add_argument('--dev', action='store_true', 
                       help='使用开发模式启动 (Flask开发服务器)')
    parser.add_argument('--workers', type=int, default=4, 
                       help='生产模式工作进程数 (默认: 4)')
    parser.add_argument('--port', type=int, default=8080, 
                       help='服务器端口 (默认: 8080)')
    parser.add_argument('--host', default='0.0.0.0', 
                       help='服务器主机 (默认: 0.0.0.0)')
    parser.add_argument('--status', action='store_true', 
                       help='显示系统状态')
    
    args = parser.parse_args()
    
    # 显示状态
    if args.status:
        show_status()
        return
    
    # 检查依赖
    check_dependencies()
    
    # 确定启动模式
    if args.prod:
        start_production(args.workers, args.port, args.host)
    else:
        # 默认开发模式
        start_development()


if __name__ == '__main__':
    main()