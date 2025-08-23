#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TOEFL单词数据库管理脚本
提供查询、更新、统计等功能
"""

import sqlite3
import argparse
from datetime import datetime


class WordsDatabase:
    """单词数据库管理类"""

    def __init__(self, db_path="toefl_words.db"):
        """
        初始化数据库连接

        Args:
            db_path (str): 数据库文件路径
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

    def search_word(self, word):
        """
        搜索单词

        Args:
            word (str): 要搜索的单词

        Returns:
            dict or None: 单词信息
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM words WHERE word = ?", (word.lower(),))
        result = cursor.fetchone()
        return dict(result) if result else None

    def search_words_like(self, pattern, limit=10):
        """
        模糊搜索单词

        Args:
            pattern (str): 搜索模式
            limit (int): 限制结果数量

        Returns:
            list: 匹配的单词列表
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM words 
            WHERE word LIKE ? 
            ORDER BY word 
            LIMIT ?
        """,
            (f"%{pattern.lower()}%", limit),
        )
        return [dict(row) for row in cursor.fetchall()]

    def update_word_count(self, word, increment=1):
        """
        更新单词计数

        Args:
            word (str): 单词
            increment (int): 增加的计数

        Returns:
            bool: 是否更新成功
        """
        cursor = self.conn.cursor()
        current_time = datetime.now().isoformat()

        cursor.execute(
            """
            UPDATE words 
            SET count = count + ?, updated = ?
            WHERE word = ?
        """,
            (increment, current_time, word.lower()),
        )

        success = cursor.rowcount > 0
        if success:
            self.conn.commit()
        return success

    def get_top_words(self, limit=10):
        """
        获取使用最多的单词

        Args:
            limit (int): 限制结果数量

        Returns:
            list: 单词列表
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM words 
            WHERE count > 0
            ORDER BY count DESC, word ASC
            LIMIT ?
        """,
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_random_words(self, limit=5):
        """
        获取随机单词

        Args:
            limit (int): 限制结果数量

        Returns:
            list: 随机单词列表
        """
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM words 
            ORDER BY RANDOM()
            LIMIT ?
        """,
            (limit,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self):
        """
        获取数据库统计信息

        Returns:
            dict: 统计信息
        """
        cursor = self.conn.cursor()

        # 总单词数
        cursor.execute("SELECT COUNT(*) as total FROM words")
        total = cursor.fetchone()["total"]

        # 有计数的单词数
        cursor.execute("SELECT COUNT(*) as counted FROM words WHERE count > 0")
        counted = cursor.fetchone()["counted"]

        # 总计数
        cursor.execute("SELECT SUM(count) as total_count FROM words")
        total_count = cursor.fetchone()["total_count"] or 0

        # 平均计数
        avg_count = total_count / counted if counted > 0 else 0

        # 最近更新的单词
        cursor.execute(
            """
            SELECT word, count, updated FROM words 
            WHERE count > 0
            ORDER BY updated DESC 
            LIMIT 5
        """
        )
        recent_words = [dict(row) for row in cursor.fetchall()]

        return {
            "total_words": total,
            "words_with_count": counted,
            "total_count": total_count,
            "average_count": round(avg_count, 2),
            "recent_words": recent_words,
        }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="TOEFL单词数据库管理工具")
    parser.add_argument("--db", default="toefl_words.db", help="数据库文件路径")

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 搜索命令
    search_parser = subparsers.add_parser("search", help="搜索单词")
    search_parser.add_argument("word", help="要搜索的单词")

    # 模糊搜索命令
    like_parser = subparsers.add_parser("like", help="模糊搜索单词")
    like_parser.add_argument("pattern", help="搜索模式")
    like_parser.add_parser("--limit", type=int, default=10, help="结果数量限制")

    # 更新计数命令
    count_parser = subparsers.add_parser("count", help="更新单词计数")
    count_parser.add_argument("word", help="要更新的单词")
    count_parser.add_argument("--increment", type=int, default=1, help="增加的计数")

    # 排行榜命令
    top_parser = subparsers.add_parser("top", help="查看使用最多的单词")
    top_parser.add_argument("--limit", type=int, default=10, help="显示数量")

    # 随机单词命令
    random_parser = subparsers.add_parser("random", help="获取随机单词")
    random_parser.add_argument("--limit", type=int, default=5, help="单词数量")

    # 统计命令
    subparsers.add_parser("stats", help="显示数据库统计信息")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        with WordsDatabase(args.db) as db:
            if args.command == "search":
                result = db.search_word(args.word)
                if result:
                    print(f"单词: {result['word']}")
                    print(f"ID: {result['id']}")
                    print(f"计数: {result['count']}")
                    print(f"创建时间: {result['created']}")
                    print(f"更新时间: {result['updated']}")
                else:
                    print(f"未找到单词: {args.word}")

            elif args.command == "like":
                results = db.search_words_like(args.pattern, getattr(args, "limit", 10))
                if results:
                    print(f"找到 {len(results)} 个匹配的单词:")
                    for word_info in results:
                        print(f"  {word_info['word']} (计数: {word_info['count']})")
                else:
                    print(f"未找到匹配 '{args.pattern}' 的单词")

            elif args.command == "count":
                success = db.update_word_count(args.word, args.increment)
                if success:
                    print(f"已更新单词 '{args.word}' 的计数 +{args.increment}")
                    updated_word = db.search_word(args.word)
                    print(f"当前计数: {updated_word['count']}")
                else:
                    print(f"未找到单词: {args.word}")

            elif args.command == "top":
                results = db.get_top_words(args.limit)
                if results:
                    print(f"使用最多的 {len(results)} 个单词:")
                    for i, word_info in enumerate(results, 1):
                        print(
                            f"  {i:2d}. {word_info['word']} (计数: {word_info['count']})"
                        )
                else:
                    print("没有使用过的单词")

            elif args.command == "random":
                results = db.get_random_words(args.limit)
                print(f"随机 {len(results)} 个单词:")
                for word_info in results:
                    print(f"  {word_info['word']} (计数: {word_info['count']})")

            elif args.command == "stats":
                stats = db.get_statistics()
                print("数据库统计信息:")
                print(f"  总单词数: {stats['total_words']}")
                print(f"  有计数的单词数: {stats['words_with_count']}")
                print(f"  总计数: {stats['total_count']}")
                print(f"  平均计数: {stats['average_count']}")

                if stats["recent_words"]:
                    print("\n最近更新的单词:")
                    for word_info in stats["recent_words"]:
                        print(
                            f"  {word_info['word']} (计数: {word_info['count']}, 更新: {word_info['updated']})"
                        )

    except Exception as e:
        print(f"错误: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
