#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TOEFL单词表导入SQLite数据库脚本
处理toefl_words.txt文件，将单词导入到SQLite数据库中
"""

import sqlite3
import os
from datetime import datetime


def create_database(db_path="toefl_words.db"):
    """
    创建SQLite数据库和words表

    Args:
        db_path (str): 数据库文件路径

    Returns:
        sqlite3.Connection: 数据库连接对象
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建words表
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE NOT NULL,
            count INTEGER DEFAULT 0,
            created DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    # 创建索引以提高查询性能
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_word ON words(word)")

    conn.commit()
    return conn


def import_words_from_file(file_path, db_conn):
    """
    从文件导入单词到数据库

    Args:
        file_path (str): 单词文件路径
        db_conn (sqlite3.Connection): 数据库连接对象

    Returns:
        tuple: (成功导入数量, 跳过数量, 总行数)
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"单词文件不存在: {file_path}")

    cursor = db_conn.cursor()
    success_count = 0
    skip_count = 0
    total_lines = 0

    current_time = datetime.now().isoformat()

    print(f"开始导入单词文件: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            total_lines += 1
            word = line.strip()

            # 跳过空行
            if not word:
                skip_count += 1
                continue

            # 清理单词（移除多余空格，转为小写）
            word = word.lower().strip()

            # 跳过非字母字符开头的行
            if not word.isalpha():
                skip_count += 1
                print(f"跳过非单词行 {line_num}: '{word}'")
                continue

            try:
                # 尝试插入单词，如果已存在则跳过
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO words (word, count, created, updated)
                    VALUES (?, 0, ?, ?)
                """,
                    (word, current_time, current_time),
                )

                if cursor.rowcount > 0:
                    success_count += 1
                    if success_count % 100 == 0:
                        print(f"已导入 {success_count} 个单词...")
                else:
                    skip_count += 1

            except sqlite3.Error as e:
                print(f"导入单词 '{word}' 时出错: {e}")
                skip_count += 1

    db_conn.commit()
    return success_count, skip_count, total_lines


def get_database_stats(db_conn):
    """
    获取数据库统计信息

    Args:
        db_conn (sqlite3.Connection): 数据库连接对象

    Returns:
        dict: 统计信息
    """
    cursor = db_conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM words")
    total_words = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM words WHERE count > 0")
    words_with_count = cursor.fetchone()[0]

    cursor.execute("SELECT MIN(created), MAX(created) FROM words")
    date_range = cursor.fetchone()

    return {
        "total_words": total_words,
        "words_with_count": words_with_count,
        "earliest_created": date_range[0],
        "latest_created": date_range[1],
    }


def main():
    """主函数"""
    # 配置
    words_file = "toefl_words.txt"
    db_file = "toefl_words.db"

    try:
        # 创建数据库
        print("创建/连接数据库...")
        conn = create_database(db_file)

        # 显示导入前统计
        stats_before = get_database_stats(conn)
        print(f"\n导入前数据库统计:")
        print(f"  总单词数: {stats_before['total_words']}")

        # 导入单词
        success, skipped, total = import_words_from_file(words_file, conn)

        # 显示导入结果
        print(f"\n导入完成!")
        print(f"  总行数: {total}")
        print(f"  成功导入: {success}")
        print(f"  跳过: {skipped}")

        # 显示导入后统计
        stats_after = get_database_stats(conn)
        print(f"\n导入后数据库统计:")
        print(f"  总单词数: {stats_after['total_words']}")
        print(
            f"  新增单词数: {stats_after['total_words'] - stats_before['total_words']}"
        )

        # 显示一些示例单词
        cursor = conn.cursor()
        cursor.execute("SELECT word, created FROM words ORDER BY id LIMIT 5")
        sample_words = cursor.fetchall()
        print(f"\n示例单词:")
        for word, created in sample_words:
            print(f"  {word} (创建时间: {created})")

        print(f"\n数据库文件已保存为: {db_file}")

    except Exception as e:
        print(f"错误: {e}")
        return 1

    finally:
        if "conn" in locals():
            conn.close()

    return 0


if __name__ == "__main__":
    exit(main())
