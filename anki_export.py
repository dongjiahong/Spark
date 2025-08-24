#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Anki导出模块
将单词学习信息和短文导出为Anki卡片
"""

import sqlite3
import json
import csv
import os
import re
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from html import escape
import genanki


class AnkiExporter:
    """Anki导出器"""

    def __init__(self, db_path: str = "toefl_words.db"):
        """
        初始化Anki导出器

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path

        # 定义Anki卡片模型
        self.word_model = self._create_word_model()
        self.essay_model = self._create_essay_model()

    def _create_word_model(self) -> genanki.Model:
        """创建单词卡片模型"""
        return genanki.Model(
            1607392319,  # 模型ID
            "TOEFL Word Model",
            fields=[
                {"name": "Word"},
                {"name": "Content"},
                {"name": "CardType"},
            ],
            templates=[
                {
                    "name": "Word Recognition",
                    "qfmt": """
                        <div class="card-front word-recognition">
                            <h2 class="word">{{Word}}</h2>
                            <div class="hint">请回想这个单词的意思</div>
                        </div>
                    """,
                    "afmt": """
                        <div class="card-back">
                            <h2 class="word">{{Word}}</h2>
                            {{Content}}
                        </div>
                    """,
                },
            ],
            css=self._get_card_css(),
        )

    def _create_essay_model(self) -> genanki.Model:
        """创建短文卡片模型"""
        return genanki.Model(
            1607392320,  # 模型ID
            "TOEFL Essay Model",
            fields=[
                {"name": "Title"},
                {"name": "EnglishContent"},
                {"name": "ChineseContent"},
                {"name": "CardType"},
                {"name": "Words"},
            ],
            templates=[
                {
                    "name": "Essay Translation",
                    "qfmt": """
                        <div class="card-front essay-translation">
                            <h3>{{Title}}</h3>
                            <div class="english-text">{{EnglishContent}}</div>
                            {{#Words}}
                            <div class="essay-words">
                                <strong>相关单词:</strong> {{Words}}
                            </div>
                            {{/Words}}
                            <div class="hint">请翻译这段英文</div>
                        </div>
                    """,
                    "afmt": """
                        <div class="card-back">
                            <h3>{{Title}}</h3>
                            <div class="translation-pair">
                                <div class="english">
                                    <h4>英文原文:</h4>
                                    <p>{{EnglishContent}}</p>
                                </div>
                                <div class="chinese">
                                    <h4>中文翻译:</h4>
                                    <p>{{ChineseContent}}</p>
                                </div>
                            </div>
                            {{#Words}}
                            <div class="essay-words">
                                <strong>相关单词:</strong> {{Words}}
                            </div>
                            {{/Words}}
                        </div>
                    """,
                },
                {
                    "name": "Essay Reverse",
                    "qfmt": """
                        <div class="card-front essay-reverse">
                            <h3>{{Title}}</h3>
                            <div class="chinese-text">{{ChineseContent}}</div>
                            {{#Words}}
                            <div class="essay-words">
                                <strong>相关单词:</strong> {{Words}}
                            </div>
                            {{/Words}}
                            <div class="hint">请根据中文翻译回想英文原文</div>
                        </div>
                    """,
                    "afmt": """
                        <div class="card-back">
                            <h3>{{Title}}</h3>
                            <div class="translation-pair">
                                <div class="chinese">
                                    <h4>中文翻译:</h4>
                                    <p>{{ChineseContent}}</p>
                                </div>
                                <div class="english">
                                    <h4>英文原文:</h4>
                                    <p>{{EnglishContent}}</p>
                                </div>
                            </div>
                            {{#Words}}
                            <div class="essay-words">
                                <strong>相关单词:</strong> {{Words}}
                            </div>
                            {{/Words}}
                        </div>
                    """,
                },
            ],
            css=self._get_card_css(),
        )

    def _get_card_css(self) -> str:
        """获取卡片CSS样式"""
        return """
/* TOEFL单词卡片 - 极简设计 */

.card {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    line-height: 1.5;
    color: #333;
    padding: 20px;
    max-width: 600px;
    margin: 0 auto;
}

/* 正面卡片 */
.card-front {
    text-align: center;
    padding: 40px 20px;
}

.word {
    font-size: 2.5em;
    font-weight: 300;
    color: #2c3e50;
    margin-bottom: 20px;
    letter-spacing: 1px;
}

.hint {
    color: #666;
    font-size: 16px;
    margin-top: 30px;
}

/* 背面卡片内容 */
.card-back {
    padding: 20px;
}

.word-content {
    line-height: 1.6;
}

.word-content > div {
    margin-bottom: 15px;
}

.word-content > div:last-child {
    margin-bottom: 0;
}

/* 音标和词性行 */
.phonetic-line {
    font-size: 18px;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 1px solid #eee;
}

.phonetic {
    color: #e74c3c;
    font-family: 'Times New Roman', serif;
    font-size: 18px;
    margin-right: 15px;
}

.pos {
    color: #7f8c8d;
    font-style: italic;
    font-size: 16px;
    font-weight: 500;
}

.pronunciation {
    color: #9b59b6;
    font-size: 14px;
    margin-left: 10px;
}

/* 翻译 */
.meanings {
    font-size: 20px;
    font-weight: 500;
    color: #2c3e50;
    margin-bottom: 20px;
    line-height: 1.4;
}

/* 词根 */
.etymology {
    color: #666;
    font-size: 14px;
    font-style: italic;
    margin-bottom: 15px;
    padding-left: 10px;
    border-left: 2px solid #ddd;
}

.etymology::before {
    content: "词根: ";
    color: #7f8c8d;
    font-weight: 500;
    font-style: normal;
}

/* 短语 */
.phrases {
    font-size: 16px;
    color: #555;
    margin-bottom: 15px;
}

.phrases::before {
    content: "短语: ";
    color: #7f8c8d;
    font-weight: 500;
}

.phrase-item {
    margin-bottom: 8px;
}

.phrase-item:last-child {
    margin-bottom: 0;
}

/* 例句 */
.examples {
    font-size: 15px;
    color: #555;
    line-height: 1.6;
}

.examples::before {
    content: "例句:";
    color: #7f8c8d;
    font-weight: 500;
    display: block;
    margin-bottom: 8px;
}

.example-item {
    margin-bottom: 8px;
}

.example-item:last-child {
    margin-bottom: 0;
}

.examples small {
    color: #888;
    font-size: 13px;
    display: block;
    margin-top: 2px;
    margin-bottom: 0;
}

/* 错误信息 */
.error {
    color: #e74c3c;
    text-align: center;
    padding: 20px;
    font-style: italic;
}

/* 拼写卡片 */
.spelling-hint {
    padding: 30px;
    text-align: center;
    border: 2px dashed #ddd;
    border-radius: 8px;
}

.meaning {
    font-size: 24px;
    color: #2c3e50;
    margin: 20px 0;
    font-weight: 500;
}

.spelling-answer {
    background: linear-gradient(135deg, #3498db, #2980b9);
    color: white;
    padding: 20px;
    border-radius: 8px;
    text-align: center;
    font-size: 2.2em;
    font-weight: 300;
    letter-spacing: 2px;
}

/* 反向卡片 */
.chinese-meaning {
    font-size: 28px;
    color: #2c3e50;
    text-align: center;
    padding: 30px;
    border: 2px solid #ecf0f1;
    border-radius: 8px;
    margin: 20px 0;
}

.reverse-answer {
    background: linear-gradient(135deg, #3498db, #2980b9);
    color: white;
    padding: 20px;
    border-radius: 8px;
    text-align: center;
    font-size: 2.2em;
    font-weight: 300;
    letter-spacing: 2px;
}

/* 短文卡片 */
.english-text, .chinese-text {
    padding: 20px;
    line-height: 1.8;
    font-size: 16px;
    border-left: 3px solid #3498db;
    margin: 20px 0;
}

.translation-pair > div {
    margin-bottom: 20px;
    padding: 15px;
    border-radius: 5px;
}

.english {
    border-left: 3px solid #3498db;
}

.chinese {
    border-left: 3px solid #f39c12;
}

/* 填空卡片 */
.cloze-text {
    padding: 20px;
    line-height: 1.8;
    font-size: 16px;
    border-left: 3px solid #e74c3c;
    margin: 20px 0;
}

.blank {
    display: inline-block;
    min-width: 80px;
    height: 20px;
    border-bottom: 2px solid #e74c3c;
    margin: 0 3px;
}

.word-bank {
    padding: 15px;
    border-left: 3px solid #17a2b8;
    margin-top: 20px;
    font-size: 14px;
    color: #666;
}

.complete-text {
    padding: 20px;
    line-height: 1.8;
    border-left: 3px solid #28a745;
    margin: 20px 0;
}

.blanked-words {
    padding: 15px;
    border-left: 3px solid #ffc107;
    margin-top: 20px;
    font-weight: 500;
    color: #856404;
}

/* 响应式 */
@media (max-width: 768px) {
    .card {
        padding: 15px;
    }
    
    .word {
        font-size: 2em;
    }
    
    .meanings {
        font-size: 18px;
    }
    
    .card-front {
        padding: 30px 15px;
    }
}
"""

    def get_database_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _format_learning_content(self, content: Dict[str, Any], word: str = "") -> str:
        """
        格式化学习内容为HTML - 极简干净设计

        Args:
            content: 学习内容字典
            word: 单词（用于发音功能）

        Returns:
            str: 格式化的HTML内容
        """
        if not content or "error" in content:
            return "<div class='error'>学习内容生成失败</div>"

        sections = []

        # 1. 音标和词性行（保留音标，删除发音功能）
        phonetic_line = []

        # 处理音标
        if "phonetic" in content:
            phonetic = content["phonetic"]
            if isinstance(phonetic, dict):
                # 从字典中提取音标
                phonetic_parts = []
                if "UK" in phonetic and phonetic["UK"]:
                    phonetic_parts.append(f"英 {phonetic['UK']}")
                if "US" in phonetic and phonetic["US"]:
                    phonetic_parts.append(f"美 {phonetic['US']}")
                if phonetic_parts:
                    phonetic_text = " ".join(phonetic_parts)
                    phonetic_line.append(
                        f'<span class="phonetic">{escape(phonetic_text)}</span>'
                    )
            elif isinstance(phonetic, str) and phonetic.strip():
                clean_phonetic = phonetic.strip("{}").strip()
                if clean_phonetic:
                    phonetic_line.append(
                        f'<span class="phonetic">{escape(clean_phonetic)}</span>'
                    )

        # 处理词性
        if "part_of_speech" in content:
            pos = content["part_of_speech"]
            if isinstance(pos, list):
                pos_clean = [
                    p.strip("{}").strip() for p in pos if p.strip("{}").strip()
                ]
                if pos_clean:
                    phonetic_line.append(
                        f'<span class="pos">{escape(" ".join(pos_clean))}</span>'
                    )
            elif isinstance(pos, str) and pos.strip():
                pos_clean = pos.strip("{}").strip()
                if pos_clean:
                    phonetic_line.append(
                        f'<span class="pos">{escape(pos_clean)}</span>'
                    )

        # 处理发音提示（圆点分割的单词发音）
        if "pronunciation" in content:
            pronunciation_text = (
                content["pronunciation"].strip("{}").strip()
                if isinstance(content["pronunciation"], str)
                else str(content["pronunciation"])
            )
            if pronunciation_text:
                phonetic_line.append(
                    f'<span class="pronunciation">{escape(pronunciation_text)}</span>'
                )

        if phonetic_line:
            sections.append(
                f'<div class="phonetic-line">{" ".join(phonetic_line)}</div>'
            )

        # 2. 翻译
        if "translations" in content:
            translations = content["translations"]
            if isinstance(translations, list):
                clean_translations = [
                    str(t).strip("{}").strip()
                    for t in translations
                    if str(t).strip("{}").strip()
                ]
                if clean_translations:
                    sections.append(
                        f'<div class="meanings">{escape(" / ".join(clean_translations))}</div>'
                    )
            elif isinstance(translations, str) and translations.strip():
                clean_trans = translations.strip("{}").strip()
                if clean_trans:
                    sections.append(
                        f'<div class="meanings">{escape(clean_trans)}</div>'
                    )

        # 3. 词根词缀（如果有）
        if "etymology" in content and content["etymology"]:
            etymology = str(content["etymology"]).strip("{}").strip()
            if etymology:
                sections.append(f'<div class="etymology">{escape(etymology)}</div>')

        # 4. 短语
        if "common_phrases" in content:
            phrases = content["common_phrases"]
            if isinstance(phrases, list):
                phrase_items = []
                for phrase_item in phrases:
                    if isinstance(phrase_item, dict):
                        # 从字典中提取短语和翻译
                        phrase_text = phrase_item.get("phrase", "").strip()
                        translation = phrase_item.get("translation", "").strip()
                        if phrase_text:
                            if translation:
                                phrase_items.append(f"{phrase_text} {translation}")
                            else:
                                phrase_items.append(phrase_text)
                    elif isinstance(phrase_item, str):
                        clean_phrase = phrase_item.strip("{}").strip()
                        if clean_phrase:
                            phrase_items.append(clean_phrase)

                if phrase_items:
                    # 为每个短语添加单独的div包装，便于控制间距（和例句逻辑一样）
                    phrase_divs = []
                    for item in phrase_items:
                        phrase_divs.append(f'<div class="phrase-item">{item}</div>')
                    phrases_html = "".join(phrase_divs)
                    sections.append(f'<div class="phrases">{phrases_html}</div>')

        # 5. 例句
        if "examples" in content:
            examples = content["examples"]
            if isinstance(examples, list):
                example_items = []
                for example_item in examples[:2]:  # 只显示前2个例句
                    if isinstance(example_item, dict):
                        # 从字典中提取例句和翻译
                        sentence = example_item.get("sentence", "").strip()
                        translation = example_item.get("translation", "").strip()
                        if sentence:
                            if translation:
                                example_items.append(
                                    f"{sentence}<br><small>{translation}</small>"
                                )
                            else:
                                example_items.append(sentence)
                    elif isinstance(example_item, str):
                        clean_example = example_item.strip("{}").strip()
                        if clean_example:
                            example_items.append(clean_example)

                if example_items:
                    # 为每个例句添加单独的div包装，便于控制间距
                    example_divs = []
                    for item in example_items:
                        example_divs.append(f'<div class="example-item">{item}</div>')
                    examples_html = "".join(example_divs)
                    sections.append(f'<div class="examples">{examples_html}</div>')

        return f'<div class="word-content">{"".join(sections)}</div>'

    def _create_word_recognition_card(
        self, word: str, content: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        创建单词识别卡片（看单词想意思）

        Args:
            word: 单词
            content: 学习内容

        Returns:
            Dict: 卡片数据
        """
        front = f"""
        <div class="card-front word-recognition">
            <h2 class="word">{escape(word)}</h2>
            <div class="hint">请回想这个单词的意思</div>
        </div>
        """

        back = f"""
        <div class="card-back">
            <h2 class="word">{escape(word)}</h2>
            {self._format_learning_content(content)}
        </div>
        """

        return {
            "front": front.strip(),
            "back": back.strip(),
            "tags": "word-recognition toefl",
            "type": "word_recognition",
        }

    def _create_essay_translation_card(
        self, essay_data: Dict[str, Any], essay_id: int, words: List[str] = None
    ) -> Dict[str, str]:
        """
        创建短文翻译卡片（看短文想翻译）

        Args:
            essay_data: 短文数据
            essay_id: 短文ID
            words: 相关单词列表

        Returns:
            Dict: 卡片数据
        """
        english_content = essay_data.get("english_content", "")
        chinese_translation = essay_data.get("chinese_translation", "")
        title = essay_data.get("title", f"Essay {essay_id}")

        # 添加单词信息
        words_info = ""
        if words:
            words_info = f"""
            <div class="essay-words">
                <strong>相关单词:</strong> {', '.join([escape(w) for w in words])}
            </div>
            """

        front = f"""
        <div class="card-front essay-translation">
            <h3>{escape(title)}</h3>
            <div class="english-text">{escape(english_content)}</div>
            {words_info}
            <div class="hint">请翻译这篇短文</div>
        </div>
        """

        back = f"""
        <div class="card-back">
            <h3>{escape(title)}</h3>
            <div class="translation-pair">
                <div class="english">
                    <h4>英文原文:</h4>
                    <p>{escape(english_content)}</p>
                </div>
                <div class="chinese">
                    <h4>中文翻译:</h4>
                    <p>{escape(chinese_translation)}</p>
                </div>
            </div>
            {words_info}
        </div>
        """

        return {
            "front": front.strip(),
            "back": back.strip(),
            "tags": "essay-translation toefl",
            "type": "essay_translation",
        }

    def _create_essay_reverse_card(
        self, essay_data: Dict[str, Any], essay_id: int, words: List[str] = None
    ) -> Dict[str, str]:
        """
        创建短文反向卡片（看翻译想短文）

        Args:
            essay_data: 短文数据
            essay_id: 短文ID
            words: 相关单词列表

        Returns:
            Dict: 卡片数据
        """
        english_content = essay_data.get("english_content", "")
        chinese_translation = essay_data.get("chinese_translation", "")
        title = essay_data.get("title", f"Essay {essay_id}")

        # 添加单词信息
        words_info = ""
        if words:
            words_info = f"""
            <div class="essay-words">
                <strong>相关单词:</strong> {', '.join([escape(w) for w in words])}
            </div>
            """

        front = f"""
        <div class="card-front essay-reverse">
            <h3>{escape(title)}</h3>
            <div class="chinese-text">{escape(chinese_translation)}</div>
            {words_info}
            <div class="hint">请根据中文翻译回想英文原文</div>
        </div>
        """

        back = f"""
        <div class="card-back">
            <h3>{escape(title)}</h3>
            <div class="translation-pair">
                <div class="chinese">
                    <h4>中文翻译:</h4>
                    <p>{escape(chinese_translation)}</p>
                </div>
                <div class="english">
                    <h4>英文原文:</h4>
                    <p>{escape(english_content)}</p>
                </div>
            </div>
            {words_info}
        </div>
        """

        return {
            "front": front.strip(),
            "back": back.strip(),
            "tags": "essay-reverse toefl",
            "type": "essay_reverse",
        }

    def _create_essay_cloze_card(
        self, essay_data: Dict[str, Any], words: List[str], essay_id: int
    ) -> Dict[str, str]:
        """
        创建短文填空卡片

        Args:
            essay_data: 短文数据
            words: 要挖空的单词列表
            essay_id: 短文ID

        Returns:
            Dict: 卡片数据
        """
        english_content = essay_data.get("english_content", "")
        title = essay_data.get("title", f"Essay {essay_id}")

        # 创建挖空版本
        cloze_content = english_content
        blanked_words = []

        for word in words:
            # 使用正则表达式找到单词（忽略大小写，考虑词边界）
            pattern = r"\b" + re.escape(word) + r"\b"
            matches = list(re.finditer(pattern, cloze_content, re.IGNORECASE))

            if matches:
                # 只替换第一个出现的单词
                match = matches[0]
                original_word = match.group()
                blank = f"<span class='blank'>______</span>"
                cloze_content = (
                    cloze_content[: match.start()]
                    + blank
                    + cloze_content[match.end() :]
                )
                blanked_words.append(original_word)

        front = f"""
        <div class="card-front essay-cloze">
            <h3>{escape(title)} - 填空练习</h3>
            <div class="cloze-text">{cloze_content}</div>
            <div class="hint">请填入空白处的单词</div>
            <div class="word-bank">
                <strong>词库:</strong> {', '.join([escape(w) for w in words])}
            </div>
        </div>
        """

        back = f"""
        <div class="card-back">
            <h3>{escape(title)} - 完整版本</h3>
            <div class="complete-text">{escape(english_content)}</div>
            <div class="blanked-words">
                <strong>填空答案:</strong> {', '.join([escape(w) for w in blanked_words])}
            </div>
        </div>
        """

        return {
            "front": front.strip(),
            "back": back.strip(),
            "tags": "essay-cloze toefl",
            "type": "essay_cloze",
        }

    def export_words_to_anki(
        self, word_ids: Optional[List[int]] = None, output_file: str = None
    ) -> str:
        """
        导出单词到Anki CSV格式

        Args:
            word_ids: 要导出的单词ID列表，None表示导出所有有学习内容的单词
            output_file: 输出文件路径

        Returns:
            str: 导出文件路径
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"anki_words_{timestamp}.csv"

        conn = self.get_database_connection()
        cursor = conn.cursor()

        try:
            # 构建查询
            if word_ids:
                placeholders = ",".join(["?"] * len(word_ids))
                query = f"SELECT * FROM words WHERE id IN ({placeholders}) AND learn_content != '{{}}'"
                cursor.execute(query, word_ids)
            else:
                cursor.execute("SELECT * FROM words WHERE learn_content != '{}'")

            words = cursor.fetchall()

            if not words:
                raise ValueError("没有找到可导出的单词")

            # 准备CSV数据
            cards = []

            for word_row in words:
                word = word_row["word"]
                try:
                    content = json.loads(word_row["learn_content"])
                except json.JSONDecodeError:
                    print(f"跳过单词 {word}，学习内容JSON格式错误")
                    continue

                # 只创建单词识别卡片
                cards.append(self._create_word_recognition_card(word, content))

            # 写入CSV文件
            with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = ["front", "back", "tags", "type"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for card in cards:
                    writer.writerow(card)

            print(f"成功导出 {len(words)} 个单词的 {len(cards)} 张卡片到 {output_file}")
            return output_file

        finally:
            conn.close()

    def export_essays_to_anki(
        self, essay_ids: Optional[List[int]] = None, output_file: str = None
    ) -> str:
        """
        导出短文到Anki CSV格式

        Args:
            essay_ids: 要导出的短文ID列表，None表示导出所有短文
            output_file: 输出文件路径

        Returns:
            str: 导出文件路径
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"anki_essays_{timestamp}.csv"

        conn = self.get_database_connection()
        cursor = conn.cursor()

        try:
            # 构建查询
            if essay_ids:
                placeholders = ",".join(["?"] * len(essay_ids))
                query = f"SELECT * FROM essay WHERE id IN ({placeholders})"
                cursor.execute(query, essay_ids)
            else:
                cursor.execute("SELECT * FROM essay")

            essays = cursor.fetchall()

            if not essays:
                raise ValueError("没有找到可导出的短文")

            # 准备CSV数据
            cards = []

            for essay_row in essays:
                essay_id = essay_row["id"]
                words = essay_row["words"].split(",")

                try:
                    content = json.loads(essay_row["content"])
                except json.JSONDecodeError:
                    print(f"跳过短文 {essay_id}，内容JSON格式错误")
                    continue

                # 为每篇短文创建三种卡片
                cards.append(
                    self._create_essay_translation_card(content, essay_id, words)
                )
                cards.append(self._create_essay_reverse_card(content, essay_id, words))
                cards.append(self._create_essay_cloze_card(content, words, essay_id))

            # 写入CSV文件
            with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = ["front", "back", "tags", "type"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for card in cards:
                    writer.writerow(card)

            print(
                f"成功导出 {len(essays)} 篇短文的 {len(cards)} 张卡片到 {output_file}"
            )
            return output_file

        finally:
            conn.close()

    def export_all_to_anki(self, output_dir: str = "anki_export") -> Dict[str, str]:
        """
        导出所有内容到Anki

        Args:
            output_dir: 输出目录

        Returns:
            Dict[str, str]: 导出文件路径字典
        """
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 导出单词
        words_file = os.path.join(output_dir, f"toefl_words_{timestamp}.csv")
        words_exported = self.export_words_to_anki(output_file=words_file)

        # 导出短文
        essays_file = os.path.join(output_dir, f"toefl_essays_{timestamp}.csv")
        essays_exported = self.export_essays_to_anki(output_file=essays_file)

        # 创建CSS样式文件
        css_file = os.path.join(output_dir, f"anki_styles_{timestamp}.css")
        self._create_css_file(css_file)

        return {"words": words_exported, "essays": essays_exported, "css": css_file}

    def export_words_to_apkg(
        self, word_ids: Optional[List[int]] = None, output_file: str = None
    ) -> str:
        """
        导出单词到Anki APKG格式

        Args:
            word_ids: 要导出的单词ID列表，None表示导出所有有学习内容的单词
            output_file: 输出文件路径

        Returns:
            str: 导出文件路径
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"toefl_words_{timestamp}.apkg"

        conn = self.get_database_connection()
        cursor = conn.cursor()

        try:
            # 构建查询
            if word_ids:
                placeholders = ",".join(["?"] * len(word_ids))
                query = f"SELECT * FROM words WHERE id IN ({placeholders}) AND learn_content != '{{}}'"
                cursor.execute(query, word_ids)
            else:
                cursor.execute("SELECT * FROM words WHERE learn_content != '{}'")

            words = cursor.fetchall()

            if not words:
                raise ValueError("没有找到可导出的单词")

            # 创建Anki牌组
            deck = genanki.Deck(
                random.randint(1 << 30, 1 << 31), "TOEFL单词学习"  # 随机deck ID
            )

            # 为每个单词创建三种卡片
            for word_row in words:
                word = word_row["word"]
                try:
                    content = json.loads(word_row["learn_content"])
                except json.JSONDecodeError:
                    print(f"跳过单词 {word}，学习内容JSON格式错误")
                    continue

                # 格式化学习内容
                formatted_content = self._format_learning_content(content, word)

                # 只创建单词识别卡片
                note1 = genanki.Note(
                    model=self.word_model,
                    fields=[word, formatted_content, "recognition"],
                    tags=["word-recognition", "toefl"],
                )
                deck.add_note(note1)

            # 生成APKG文件
            package = genanki.Package(deck)
            package.write_to_file(output_file)

            print(f"成功导出 {len(words)} 个单词到 {output_file}")
            return output_file

        finally:
            conn.close()

    def export_essays_to_apkg(
        self, essay_ids: Optional[List[int]] = None, output_file: str = None
    ) -> str:
        """
        导出短文到Anki APKG格式

        Args:
            essay_ids: 要导出的短文ID列表，None表示导出所有短文
            output_file: 输出文件路径

        Returns:
            str: 导出文件路径
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"toefl_essays_{timestamp}.apkg"

        conn = self.get_database_connection()
        cursor = conn.cursor()

        try:
            # 构建查询
            if essay_ids:
                placeholders = ",".join(["?"] * len(essay_ids))
                query = f"SELECT * FROM essay WHERE id IN ({placeholders})"
                cursor.execute(query, essay_ids)
            else:
                cursor.execute("SELECT * FROM essay")

            essays = cursor.fetchall()

            if not essays:
                raise ValueError("没有找到可导出的短文")

            # 创建Anki牌组
            deck = genanki.Deck(
                random.randint(1 << 30, 1 << 31), "TOEFL短文学习"  # 随机deck ID
            )

            # 为每篇短文创建卡片
            for essay_row in essays:
                essay_id = essay_row["id"]
                words = essay_row["words"].split(",")

                try:
                    content = json.loads(essay_row["content"])
                except json.JSONDecodeError:
                    print(f"跳过短文 {essay_id}，内容JSON格式错误")
                    continue

                english_content = content.get("english_content", "")
                chinese_translation = content.get("chinese_translation", "")
                title = content.get("title", f"Essay {essay_id}")

                # 翻译卡片
                note1 = genanki.Note(
                    model=self.essay_model,
                    fields=[
                        title,
                        english_content,
                        chinese_translation,
                        "translation",
                        ",".join(words),
                    ],
                    tags=["essay-translation", "toefl"],
                )
                deck.add_note(note1)

                # 反向卡片
                note2 = genanki.Note(
                    model=self.essay_model,
                    fields=[
                        title,
                        english_content,
                        chinese_translation,
                        "reverse",
                        ",".join(words),
                    ],
                    tags=["essay-reverse", "toefl"],
                )
                deck.add_note(note2)

            # 生成APKG文件
            package = genanki.Package(deck)
            package.write_to_file(output_file)

            print(f"成功导出 {len(essays)} 篇短文到 {output_file}")
            return output_file

        finally:
            conn.close()

    def export_all_to_apkg(self, output_dir: str = "anki_export") -> Dict[str, str]:
        """
        导出所有内容到Anki APKG格式

        Args:
            output_dir: 输出目录

        Returns:
            Dict[str, str]: 导出文件路径字典
        """
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 导出单词
        words_file = os.path.join(output_dir, f"toefl_words_{timestamp}.apkg")
        words_exported = self.export_words_to_apkg(output_file=words_file)

        # 导出短文
        essays_file = os.path.join(output_dir, f"toefl_essays_{timestamp}.apkg")
        essays_exported = self.export_essays_to_apkg(output_file=essays_file)

        return {"words": words_exported, "essays": essays_exported}

    def _create_css_file(self, css_file: str) -> None:
        """创建Anki卡片的CSS样式文件"""
        css_content = """
/* TOEFL单词学习卡片样式 - 融合布局版 */

.card {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    line-height: 1.5;
    margin: 15px;
    padding: 20px;
    background: #f8f9fa;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

/* 正面卡片样式 */
.card-front {
    text-align: center;
    padding: 25px 20px;
}

.card-front h2, .card-front h3 {
    color: #2c3e50;
    margin-bottom: 15px;
}

.word {
    font-size: 2.5em;
    font-weight: bold;
    color: #3498db;
    margin-bottom: 15px;
}

.hint {
    color: #7f8c8d;
    font-style: italic;
    margin-top: 15px;
    font-size: 1.0em;
}

/* 背面卡片样式 */
.card-back {
    padding: 20px;
}

.word-content {
    background: white;
    padding: 20px;
    border-radius: 8px;
    border-left: 4px solid #3498db;
}

/* 单词信息头部 - 音标、发音、词性一行显示 */
.word-header {
    background: #f0f8ff;
    padding: 12px 18px;
    border-radius: 6px;
    margin-bottom: 15px;
    font-size: 1.0em;
    border-left: 4px solid #3498db;
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 20px;
}

.phonetic-info {
    display: flex;
    align-items: center;
    gap: 10px;
}

.phonetic-text {
    font-family: 'Lucida Sans Unicode', sans-serif;
    color: #e74c3c;
    font-weight: bold;
    font-size: 1.2em;
}

.pronunciation-btn {
    background: none;
    border: none;
    font-size: 1.0em;
    cursor: pointer;
    padding: 3px 5px;
    border-radius: 3px;
    transition: background-color 0.2s;
}

.pronunciation-btn:hover {
    background-color: #e0e0e0;
}

.pronunciation-btn:active {
    background-color: #d0d0d0;
}

.pronunciation-info {
    color: #9b59b6;
    font-weight: 600;
}

.pos-info {
    color: #f39c12;
    font-weight: 700;
    background: #fff3cd;
    padding: 4px 10px;
    border-radius: 4px;
    font-size: 0.9em;
}

/* 内容区域样式 */
.word-content > div {
    margin-bottom: 12px;
    line-height: 1.6;
}

.word-content > div:last-child {
    margin-bottom: 0;
}

.translations {
    background: #f8f9fa;
    padding: 12px;
    border-radius: 5px;
    border-left: 4px solid #28a745;
}

.translations strong {
    color: #28a745;
    margin-right: 10px;
}

.phrases {
    background: #fff3cd;
    padding: 12px;
    border-radius: 5px;
    border-left: 4px solid #ffc107;
}

.phrases strong {
    color: #856404;
    margin-right: 10px;
}

.etymology {
    background: #e7f3ff;
    padding: 12px;
    border-radius: 5px;
    border-left: 4px solid #007bff;
}

.etymology strong {
    color: #004085;
    margin-right: 10px;
}

.examples {
    background: #f0f0f0;
    padding: 12px;
    border-radius: 5px;
    border-left: 4px solid #6c757d;
}

.examples strong {
    color: #495057;
    margin-right: 10px;
}

/* 拼写卡片特殊样式 */
.spelling-hint {
    background: #fff3cd;
    padding: 20px;
    border-radius: 8px;
    border: 2px dashed #ffc107;
}

.meaning {
    font-size: 1.4em;
    color: #856404;
    margin: 15px 0;
}

.spelling-answer {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    border-radius: 8px;
    text-align: center;
}

/* 反向卡片样式 */
.chinese-meaning {
    font-size: 1.6em;
    color: #e74c3c;
    padding: 20px;
    background: #fdedec;
    border-radius: 8px;
    margin: 20px 0;
}

.reverse-answer {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    border-radius: 8px;
    text-align: center;
}

/* 短文卡片样式 */
.english-text, .chinese-text {
    background: white;
    padding: 20px;
    border-radius: 8px;
    border-left: 4px solid #3498db;
    margin: 20px 0;
    line-height: 1.8;
}

.translation-pair {
    margin-top: 20px;
}

.translation-pair > div {
    margin-bottom: 20px;
    padding: 15px;
    border-radius: 8px;
}

.english {
    background: #e8f4fd;
    border-left: 4px solid #3498db;
}

.chinese {
    background: #fef9e7;
    border-left: 4px solid #f1c40f;
}

/* 填空卡片样式 */
.cloze-text {
    background: white;
    padding: 20px;
    border-radius: 8px;
    border-left: 4px solid #e74c3c;
    margin: 20px 0;
    line-height: 1.8;
    font-size: 1.1em;
}

.blank {
    background: #f8d7da;
    padding: 2px 8px;
    border-radius: 4px;
    border: 2px dashed #dc3545;
    font-weight: bold;
    color: #721c24;
}

.word-bank {
    background: #d1ecf1;
    padding: 15px;
    border-radius: 8px;
    border-left: 4px solid #17a2b8;
    margin-top: 20px;
}

.complete-text {
    background: #d4edda;
    padding: 20px;
    border-radius: 8px;
    border-left: 4px solid #28a745;
    margin: 20px 0;
    line-height: 1.8;
}

.blanked-words {
    background: #fff3cd;
    padding: 15px;
    border-radius: 8px;
    border-left: 4px solid #ffc107;
    margin-top: 20px;
    font-weight: bold;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .card {
        margin: 10px;
        padding: 15px;
    }
    
    .word {
        font-size: 2em;
    }
    
    .card-front {
        padding: 20px 15px;
    }
    
    .word-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 10px;
    }
}
"""

        with open(css_file, "w", encoding="utf-8") as f:
            f.write(css_content)

        print(f"CSS样式文件已创建: {css_file}")


def main():
    """主函数 - 演示Anki导出功能"""
    try:
        exporter = AnkiExporter()

        print("=== Anki APKG导出 ===")

        # 直接导出APKG格式
        exported_files = exporter.export_all_to_apkg()

        print(f"\n=== 导出完成 ===")
        for content_type, file_path in exported_files.items():
            print(f"{content_type}: {file_path}")

        print(f"\n📝 使用说明:")
        print(f"1. 直接将APKG文件拖拽到Anki中")
        print(f"2. 或者在Anki中选择 '文件' > '导入' 选择APKG文件")
        print(f"3. 点击音标旁边的🇺🇸🇬🇧图标播放发音")
        print(f"4. 无需其他配置，样式已内置")

    except Exception as e:
        print(f"导出失败: {e}")


if __name__ == "__main__":
    main()
