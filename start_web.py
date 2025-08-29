#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web服务启动脚本
自动处理数据库初始化并启动Web服务
"""

import os
import sys
import subprocess

def main():
    print("🚀 TOEFL单词学习系统启动器")
    print("=" * 40)
    
    # 检查是否存在数据库文件
    if not os.path.exists("toefl_words.db"):
        print("📋 首次运行，需要初始化数据库...")
        
        # 运行数据库初始化
        try:
            subprocess.run([sys.executable, "init_database.py"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"❌ 数据库初始化失败: {e}")
            return
        except FileNotFoundError:
            print("❌ 找不到init_database.py文件")
            return
    else:
        print("📋 数据库文件已存在，检查表结构...")
        
        # 运行快速检查
        try:
            from init_database import check_database_integrity
            if not check_database_integrity():
                print("⚠️ 数据库完整性检查失败，重新初始化...")
                subprocess.run([sys.executable, "init_database.py"], check=True)
        except ImportError:
            print("⚠️ 无法导入数据库检查模块，直接启动服务...")
        except Exception as e:
            print(f"⚠️ 数据库检查出错: {e}")
    
    print("\n🌐 启动Web服务器...")
    print("=" * 40)
    
    # 启动Web服务
    try:
        subprocess.run([sys.executable, "web_viewer.py"])
    except KeyboardInterrupt:
        print("\n\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 启动Web服务失败: {e}")

if __name__ == "__main__":
    main()