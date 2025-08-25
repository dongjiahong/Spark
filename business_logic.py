#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
业务逻辑模块
处理单词选择、学习信息生成、短文创作等核心业务流程
"""

import sqlite3
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from ai_service import AIService


class WordManager:
    """单词管理器"""

    def __init__(self, db_path: str = "toefl_words.db"):
        """
        初始化单词管理器

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.ai_service = AIService()

    def get_database_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使结果可以按列名访问
        return conn

    def select_words(
        self, count: int = 5, prioritize_zero_count: bool = True
    ) -> List[Dict[str, Any]]:
        """
        选择单词进行学习

        Args:
            count: 选择的单词数量
            prioritize_zero_count: 是否优先选择count=0的单词

        Returns:
            List[Dict]: 选中的单词列表
        """
        conn = self.get_database_connection()
        cursor = conn.cursor()

        try:
            if prioritize_zero_count:
                # 首先尝试获取count=0的单词
                cursor.execute(
                    "SELECT * FROM words WHERE count = 0 ORDER BY RANDOM() LIMIT ?",
                    (count,),
                )
                words = cursor.fetchall()

                # 如果count=0的单词不够，再从其他单词中选择
                if len(words) < count:
                    remaining = count - len(words)
                    selected_ids = [w["id"] for w in words]

                    if selected_ids:
                        placeholders = ",".join(["?"] * len(selected_ids))
                        cursor.execute(
                            f"SELECT * FROM words WHERE count > 0 AND id NOT IN ({placeholders}) ORDER BY count ASC, RANDOM() LIMIT ?",
                            selected_ids + [remaining],
                        )
                    else:
                        cursor.execute(
                            "SELECT * FROM words WHERE count > 0 ORDER BY count ASC, RANDOM() LIMIT ?",
                            (remaining,),
                        )

                    additional_words = cursor.fetchall()
                    words.extend(additional_words)
            else:
                # 随机选择单词
                cursor.execute(
                    "SELECT * FROM words ORDER BY RANDOM() LIMIT ?", (count,)
                )
                words = cursor.fetchall()

            # 转换为字典列表
            result = [dict(word) for word in words]
            return result

        finally:
            conn.close()

    def update_word_count(self, word_id: int) -> bool:
        """
        更新单词的count计数

        Args:
            word_id: 单词ID

        Returns:
            bool: 更新是否成功
        """
        conn = self.get_database_connection()
        cursor = conn.cursor()

        try:
            current_time = datetime.now().isoformat()
            cursor.execute(
                "UPDATE words SET count = count + 1, updated = ? WHERE id = ?",
                (current_time, word_id),
            )
            conn.commit()
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            print(f"更新单词count失败: {e}")
            return False
        finally:
            conn.close()

    def save_word_learning_content(
        self, word_id: int, learning_content: Dict[str, Any]
    ) -> bool:
        """
        保存单词的学习内容

        Args:
            word_id: 单词ID
            learning_content: 学习内容字典

        Returns:
            bool: 保存是否成功
        """
        conn = self.get_database_connection()
        cursor = conn.cursor()

        try:
            current_time = datetime.now().isoformat()
            content_json = json.dumps(learning_content, ensure_ascii=False)

            cursor.execute(
                "UPDATE words SET learn_content = ?, updated = ? WHERE id = ?",
                (content_json, current_time, word_id),
            )
            conn.commit()
            return cursor.rowcount > 0

        except sqlite3.Error as e:
            print(f"保存学习内容失败: {e}")
            return False
        finally:
            conn.close()

    def save_essay(
        self, words: List[str], essay_content: Dict[str, str]
    ) -> Optional[int]:
        """
        保存短文到数据库

        Args:
            words: 相关单词列表
            essay_content: 短文内容

        Returns:
            Optional[int]: 短文ID，失败时返回None
        """
        conn = self.get_database_connection()
        cursor = conn.cursor()

        try:
            words_str = ",".join(words)
            content_json = json.dumps(essay_content, ensure_ascii=False)

            cursor.execute(
                "INSERT INTO essay (words, content) VALUES (?, ?)",
                (words_str, content_json),
            )
            conn.commit()
            return cursor.lastrowid

        except sqlite3.Error as e:
            print(f"保存短文失败: {e}")
            return None
        finally:
            conn.close()

    def generate_learning_session(
        self, word_count: int = 5, essay_type: str = "story"
    ) -> Dict[str, Any]:
        """
        生成一个完整的学习会话

        Args:
            word_count: 选择的单词数量
            essay_type: 短文类型

        Returns:
            Dict: 包含单词学习信息和短文的完整会话数据
        """
        print(f"开始生成学习会话，选择 {word_count} 个单词...")

        # 1. 选择单词
        selected_words = self.select_words(word_count)
        if not selected_words:
            return {"error": "没有找到可用的单词"}

        print(f"选中单词: {[w['word'] for w in selected_words]}")

        # 2. 为每个单词生成学习信息
        words_with_content = []
        successful_words = []  # 记录成功生成学习内容的单词
        
        for word_data in selected_words:
            print(f"正在为单词 '{word_data['word']}' 生成学习信息...")

            # 生成学习内容
            learning_content = self.ai_service.generate_word_learning_info(
                word_data["word"]
            )

            # 检查生成是否成功
            if "error" not in learning_content:
                # 成功：保存到数据库并更新count
                save_success = self.save_word_learning_content(word_data["id"], learning_content)
                if save_success:
                    self.update_word_count(word_data["id"])
                    successful_words.append(word_data["word"])
                    print(f"✓ 单词 '{word_data['word']}' 学习信息已生成并保存")
                else:
                    print(f"✗ 单词 '{word_data['word']}' 学习信息保存失败")
                    # 保存失败时将错误信息记录到learning_content
                    learning_content = {"error": "学习内容保存失败"}
            else:
                # 失败：不更新count，保持原状态以便下次重新选择
                print(f"✗ 单词 '{word_data['word']}' 学习信息生成失败: {learning_content.get('error')}")
                print(f"  → 单词状态未更新，下次学习时会重新选择")

            # 添加到结果中（无论成功失败都添加，但失败的包含错误信息）
            word_data_copy = dict(word_data)
            word_data_copy["learning_content"] = learning_content
            words_with_content.append(word_data_copy)

        # 3. 生成短文（只为成功生成学习信息的单词生成短文）
        essay_content = {}
        essay_id = None
        
        if successful_words:
            print(f"正在为成功的单词 {successful_words} 生成{essay_type}...")
            essay_content = self.ai_service.generate_essay(successful_words, essay_type)

            # 保存短文
            if "error" not in essay_content:
                essay_id = self.save_essay(successful_words, essay_content)
                print(f"✓ 短文已保存，ID: {essay_id}")
            else:
                print(f"✗ 短文生成失败: {essay_content.get('error')}")
        else:
            print("没有成功生成学习信息的单词，跳过短文生成")
            essay_content = {"error": "没有可用单词生成短文"}

        return {
            "words": words_with_content,
            "essay": essay_content,
            "essay_id": essay_id,
            "session_summary": {
                "word_count": len(selected_words),
                "successful_words": len(successful_words),
                "essay_type": essay_type,
                "generated_at": datetime.now().isoformat(),
            },
        }

    def get_word_stats(self) -> Dict[str, int]:
        """获取单词统计信息"""
        conn = self.get_database_connection()
        cursor = conn.cursor()

        try:
            # 总单词数
            cursor.execute("SELECT COUNT(*) FROM words")
            total_words = cursor.fetchone()[0]

            # count=0的单词数
            cursor.execute("SELECT COUNT(*) FROM words WHERE count = 0")
            unused_words = cursor.fetchone()[0]

            # 已学习单词数
            cursor.execute("SELECT COUNT(*) FROM words WHERE count > 0")
            learned_words = cursor.fetchone()[0]

            # 有学习内容的单词数
            cursor.execute("SELECT COUNT(*) FROM words WHERE learn_content != '{}'")
            words_with_content = cursor.fetchone()[0]

            # 短文总数
            cursor.execute("SELECT COUNT(*) FROM essay")
            total_essays = cursor.fetchone()[0]

            return {
                "total_words": total_words,
                "unused_words": unused_words,
                "learned_words": learned_words,
                "words_with_content": words_with_content,
                "total_essays": total_essays,
            }

        finally:
            conn.close()


def main():
    """主函数 - 演示业务逻辑使用"""
    try:
        manager = WordManager()

        # 显示统计信息
        stats = manager.get_word_stats()
        print("=== 数据库统计 ===")
        for key, value in stats.items():
            print(f"{key}: {value}")

        print("\n=== 开始学习会话 ===")

        # 生成学习会话
        session = manager.generate_learning_session(word_count=3, essay_type="story")

        if "error" in session:
            print(f"学习会话生成失败: {session['error']}")
            return

        print("\n=== 学习会话完成 ===")
        print(f"处理了 {len(session['words'])} 个单词")

        # 显示单词信息
        for word_data in session["words"]:
            print(f"\n单词: {word_data['word']}")
            if (
                "learning_content" in word_data
                and "error" not in word_data["learning_content"]
            ):
                content = word_data["learning_content"]
                print(f"  音标: {content.get('phonetic', 'N/A')}")
                print(f"  词性: {content.get('part_of_speech', 'N/A')}")
                print(f"  翻译: {content.get('translations', 'N/A')}")

        # 显示短文信息
        if "error" not in session["essay"]:
            essay = session["essay"]
            print(f"\n=== 短文 ===")
            print(f"标题: {essay.get('title', 'N/A')}")
            print(f"内容预览: {essay.get('english_content', '')[:100]}...")

        # 显示最新统计
        new_stats = manager.get_word_stats()
        print(f"\n=== 更新后统计 ===")
        for key, value in new_stats.items():
            print(f"{key}: {value}")

    except Exception as e:
        print(f"执行失败: {e}")


if __name__ == "__main__":
    main()
