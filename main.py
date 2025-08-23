#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TOEFL单词学习系统主入口
整合单词学习、短文生成和Anki导出功能
"""

import argparse
import sys
import os
from typing import List, Optional

from business_logic import WordManager
from anki_export import AnkiExporter


def create_learning_session(word_count: int = 5, essay_type: str = "story"):
    """
    创建学习会话

    Args:
        word_count: 选择的单词数量
        essay_type: 短文类型
    """
    print(f"=== 创建学习会话 ===")
    print(f"单词数量: {word_count}")
    print(f"短文类型: {essay_type}")

    manager = WordManager()

    # 显示当前统计
    stats = manager.get_word_stats()
    print(f"\n当前数据库统计:")
    print(f"  总单词数: {stats['total_words']}")
    print(f"  未学习单词: {stats['unused_words']}")
    print(f"  已学习单词: {stats['learned_words']}")
    print(f"  有学习内容: {stats['words_with_content']}")
    print(f"  短文总数: {stats['total_essays']}")

    # 生成学习会话
    session = manager.generate_learning_session(word_count, essay_type)

    if "error" in session:
        print(f"❌ 学习会话生成失败: {session['error']}")
        return False

    print(f"\n✅ 学习会话生成完成!")
    print(f"处理单词: {[w['word'] for w in session['words']]}")

    # 显示短文标题
    if "title" in session["essay"]:
        print(f"生成短文: {session['essay']['title']}")

    return True


def export_to_anki(output_dir: str = "anki_export"):
    """
    导出到Anki APKG格式

    Args:
        output_dir: 输出目录
    """
    print(f"=== 导出到Anki (APKG格式) ===")
    print(f"输出目录: {output_dir}")

    exporter = AnkiExporter()

    try:
        exported_files = exporter.export_all_to_apkg(output_dir)

        print(f"\n✅ 导出完成!")
        for content_type, file_path in exported_files.items():
            if os.path.exists(file_path):
                print(f"  {content_type}: {file_path}")
            else:
                print(f"  {content_type}: {file_path} (文件不存在)")

        print(f"\n📝 使用说明:")
        print(f"1. 直接将APKG文件拖拽到Anki中")
        print(f"2. 或者在Anki中选择 '文件' > '导入' 选择APKG文件")
        print(f"3. 点击音标旁边的🇺🇸🇬🇧图标播放发音")
        print(f"4. 无需其他配置，样式已内置")

        return True

    except Exception as e:
        print(f"❌ 导出失败: {e}")
        return False


def show_stats():
    """显示数据库统计信息"""
    print(f"=== 数据库统计信息 ===")

    manager = WordManager()
    stats = manager.get_word_stats()

    print(f"总单词数: {stats['total_words']}")
    print(f"未学习单词 (count=0): {stats['unused_words']}")
    print(f"已学习单词 (count>0): {stats['learned_words']}")
    print(f"有学习内容的单词: {stats['words_with_content']}")
    print(f"短文总数: {stats['total_essays']}")

    # 计算进度
    if stats["total_words"] > 0:
        learned_percentage = (stats["learned_words"] / stats["total_words"]) * 100
        content_percentage = (stats["words_with_content"] / stats["total_words"]) * 100

        print(f"\n📊 学习进度:")
        print(f"已学习进度: {learned_percentage:.1f}%")
        print(f"内容生成进度: {content_percentage:.1f}%")


def interactive_mode():
    """交互模式"""
    print("=== TOEFL单词学习系统 ===")
    print("欢迎使用TOEFL单词学习系统!")

    while True:
        print(f"\n请选择操作:")
        print(f"1. 创建学习会话")
        print(f"2. 导出到Anki")
        print(f"3. 显示统计信息")
        print(f"4. 退出")

        choice = input("\n请输入选项 (1-4): ").strip()

        if choice == "1":
            # 创建学习会话
            try:
                word_count = int(input("请输入单词数量 (默认5): ") or "5")
            except ValueError:
                word_count = 5

            print("请选择短文类型:")
            print("1. 故事 (story)")
            print("2. 童话 (fairy_tale)")
            print("3. 新闻 (news)")
            print("4. 预言 (prophecy)")

            type_choice = input("请输入类型选项 (1-4, 默认1): ").strip() or "1"
            type_map = {"1": "story", "2": "fairy_tale", "3": "news", "4": "prophecy"}
            essay_type = type_map.get(type_choice, "story")

            create_learning_session(word_count, essay_type)

        elif choice == "2":
            # 导出到Anki
            output_dir = (
                input("请输入输出目录 (默认anki_export): ").strip() or "anki_export"
            )
            export_to_anki(output_dir)

        elif choice == "3":
            # 显示统计信息
            show_stats()

        elif choice == "4":
            print("感谢使用TOEFL单词学习系统!")
            break

        else:
            print("无效选项，请重新输入。")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="TOEFL单词学习系统")
    parser.add_argument(
        "--mode",
        choices=["interactive", "learn", "export", "stats"],
        default="interactive",
        help="运行模式",
    )
    parser.add_argument("--words", type=int, default=5, help="学习的单词数量")
    parser.add_argument(
        "--type",
        choices=["story", "fairy_tale", "news", "prophecy"],
        default="story",
        help="短文类型",
    )
    parser.add_argument("--output", default="anki_export", help="Anki导出目录")

    args = parser.parse_args()

    if args.mode == "interactive":
        interactive_mode()
    elif args.mode == "learn":
        success = create_learning_session(args.words, args.type)
        sys.exit(0 if success else 1)
    elif args.mode == "export":
        success = export_to_anki(args.output)
        sys.exit(0 if success else 1)
    elif args.mode == "stats":
        show_stats()

    return 0


if __name__ == "__main__":
    exit(main())
