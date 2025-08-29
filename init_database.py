#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
确保所有必需的表都存在，用于在新机器或环境上启动应用前运行
"""

import sqlite3
import os
from pathlib import Path

def init_database(db_path: str = "toefl_words.db"):
    """
    初始化数据库，创建所有必需的表
    
    Args:
        db_path: 数据库文件路径
    """
    print(f"正在初始化数据库: {db_path}")
    
    # 确保数据库目录存在
    db_dir = Path(db_path).parent
    if db_dir != Path('.'):
        db_dir.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. 创建words表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT UNIQUE NOT NULL,
                count INTEGER DEFAULT 0,
                learn_content TEXT DEFAULT '{}',
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✓ words表检查完成")
        
        # 2. 创建essay表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS essay (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                words TEXT NOT NULL,
                content TEXT NOT NULL,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✓ essay表检查完成")
        
        # 3. 创建study_groups表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_ids TEXT NOT NULL,
                essay_id INTEGER,
                group_status TEXT DEFAULT 'active',
                total_items INTEGER DEFAULT 0,
                completed_items INTEGER DEFAULT 0,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_date TIMESTAMP,
                FOREIGN KEY (essay_id) REFERENCES essay (id)
            )
        ''')
        print("✓ study_groups表检查完成")
        
        # 4. 创建learning_progress表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                study_group_id INTEGER NOT NULL,
                word_id INTEGER,
                essay_id INTEGER,
                progress_status TEXT DEFAULT 'pending',
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (study_group_id) REFERENCES study_groups (id),
                FOREIGN KEY (word_id) REFERENCES words (id),
                FOREIGN KEY (essay_id) REFERENCES essay (id)
            )
        ''')
        print("✓ learning_progress表检查完成")
        
        # 5. 创建study_sessions表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_type TEXT DEFAULT 'learning',
                word_count INTEGER DEFAULT 0,
                essay_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''')
        print("✓ study_sessions表检查完成")
        
        # 6. 创建tasks表（用于异步任务管理）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                progress INTEGER DEFAULT 0,
                message TEXT,
                result TEXT,
                error TEXT,
                created_at REAL NOT NULL,
                completed_at REAL,
                failed_at REAL
            )
        ''')
        print("✓ tasks表检查完成")
        
        # 7. 创建migration_history表（用于追踪数据库版本）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS migration_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT NOT NULL,
                description TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✓ migration_history表检查完成")
        
        # 8. 创建索引以提升查询性能
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_words_word ON words (word)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_words_count ON words (count)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_essay_created ON essay (created)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_study_groups_status ON study_groups (group_status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_study_groups_created ON study_groups (created_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status)')
        print("✓ 数据库索引检查完成")
        
        # 提交所有更改
        conn.commit()
        
        # 显示数据库统计信息
        print("\n=== 数据库统计 ===")
        
        # 检查各表的记录数量
        tables = ['words', 'essay', 'study_groups', 'learning_progress', 'study_sessions', 'tasks']
        for table in tables:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            print(f"{table}: {count} 条记录")
        
        print(f"\n✅ 数据库初始化完成！数据库文件: {os.path.abspath(db_path)}")
        
    except sqlite3.Error as e:
        print(f"❌ 数据库初始化失败: {e}")
        raise
    finally:
        conn.close()

def check_database_integrity(db_path: str = "toefl_words.db"):
    """
    检查数据库完整性
    
    Args:
        db_path: 数据库文件路径
    """
    if not os.path.exists(db_path):
        print(f"⚠️ 数据库文件不存在: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查数据库完整性
        cursor.execute('PRAGMA integrity_check')
        result = cursor.fetchone()[0]
        
        if result == 'ok':
            print("✅ 数据库完整性检查通过")
            return True
        else:
            print(f"❌ 数据库完整性检查失败: {result}")
            return False
    except sqlite3.Error as e:
        print(f"❌ 数据库完整性检查出错: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("TOEFL单词学习系统 - 数据库初始化脚本")
    print("=" * 50)
    
    # 初始化数据库
    init_database()
    
    # 检查数据库完整性
    print("\n正在检查数据库完整性...")
    check_database_integrity()
    
    print("\n🎉 初始化完成！你现在可以安全地启动web服务器了:")
    print("python web_viewer.py")