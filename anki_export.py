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
                {
                    "name": "Word Spelling",
                    "qfmt": """
                        <div class="card-front word-spelling">
                            <div class="spelling-hint">
                                <div class="meaning">{{Content}}</div>
                                <div class="hint">请拼写出这个单词</div>
                            </div>
                        </div>
                    """,
                    "afmt": """
                        <div class="card-back">
                            <div class="spelling-answer">
                                <h2 class="word">{{Word}}</h2>
                            </div>
                            {{Content}}
                        </div>
                    """,
                },
                {
                    "name": "Word Reverse",
                    "qfmt": """
                        <div class="card-front word-reverse">
                            <div class="chinese-meaning">{{Content}}</div>
                            <div class="hint">请说出对应的英文单词</div>
                        </div>
                    """,
                    "afmt": """
                        <div class="card-back">
                            <div class="reverse-answer">
                                <h2 class="word">{{Word}}</h2>
                            </div>
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
/* TOEFL单词学习卡片样式 - 紧凑版 */

.card {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    line-height: 1.4;
    margin: 8px;
    padding: 12px;
    background: #f8f9fa;
    border-radius: 6px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.1);
}

/* 正面卡片样式 */
.card-front {
    text-align: center;
    padding: 15px 10px;
}

.card-front h2, .card-front h3 {
    color: #2c3e50;
    margin-bottom: 10px;
    font-size: 1.3em;
}

.word {
    font-size: 2.0em;
    font-weight: bold;
    color: #3498db;
    margin-bottom: 8px;
}

.hint {
    color: #7f8c8d;
    font-style: italic;
    margin-top: 10px;
    font-size: 0.9em;
}

/* 背面卡片样式 */
.card-back {
    padding: 12px;
}

.word-content {
    background: white;
    padding: 12px;
    border-radius: 6px;
    border-left: 3px solid #3498db;
}

.word-content > div {
    margin-bottom: 8px;
    padding: 4px 0;
    border-bottom: 1px solid #ecf0f1;
    font-size: 0.9em;
}

.word-content > div:last-child {
    border-bottom: none;
}

.phonetic {
    font-family: 'Lucida Sans Unicode', sans-serif;
    color: #e74c3c;
    font-size: 1.0em;
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.pronunciation-buttons {
    margin-left: 8px;
}

.pronunciation-btn {
    background: none;
    border: none;
    font-size: 1.0em;
    cursor: pointer;
    margin: 0 2px;
    padding: 3px;
    border-radius: 2px;
    transition: background-color 0.2s;
}

.pronunciation-btn:hover {
    background-color: #f0f0f0;
}

.pronunciation-btn:active {
    background-color: #ddd;
}

.pronunciation {
    color: #9b59b6;
    font-weight: bold;
    font-size: 0.9em;
}

.pos {
    color: #f39c12;
    font-weight: bold;
    font-size: 0.9em;
}

.translations ul, .phrases ul, .examples ol {
    margin: 6px 0;
    padding-left: 16px;
}

.translations li, .phrases li, .examples li {
    margin: 3px 0;
    color: #2c3e50;
    font-size: 0.9em;
}

/* 拼写卡片特殊样式 */
.spelling-hint {
    background: #fff3cd;
    padding: 15px;
    border-radius: 6px;
    border: 2px dashed #ffc107;
}

.meaning {
    font-size: 1.2em;
    color: #856404;
    margin: 10px 0;
}

.spelling-answer {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 15px;
    border-radius: 6px;
    text-align: center;
}

/* 反向卡片样式 */
.chinese-meaning {
    font-size: 1.3em;
    color: #e74c3c;
    padding: 15px;
    background: #fdedec;
    border-radius: 6px;
    margin: 15px 0;
}

.reverse-answer {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 15px;
    border-radius: 6px;
    text-align: center;
}

/* 短文卡片样式 - 紧凑版 */
.english-text, .chinese-text {
    background: white;
    padding: 12px;
    border-radius: 6px;
    border-left: 3px solid #3498db;
    margin: 12px 0;
    line-height: 1.5;
    font-size: 0.95em;
}

.translation-pair {
    margin-top: 12px;
}

.translation-pair > div {
    margin-bottom: 12px;
    padding: 10px;
    border-radius: 6px;
}

.english {
    background: #e8f4fd;
    border-left: 3px solid #3498db;
}

.chinese {
    background: #fef9e7;
    border-left: 3px solid #f1c40f;
}

/* 填空卡片样式 */
.cloze-text {
    background: white;
    padding: 12px;
    border-radius: 6px;
    border-left: 3px solid #e74c3c;
    margin: 12px 0;
    line-height: 1.5;
    font-size: 0.95em;
}

.blank {
    background: #f8d7da;
    padding: 2px 6px;
    border-radius: 3px;
    border: 2px dashed #dc3545;
    font-weight: bold;
    color: #721c24;
}

.word-bank {
    background: #d1ecf1;
    padding: 10px;
    border-radius: 6px;
    border-left: 3px solid #17a2b8;
    margin-top: 12px;
    font-size: 0.9em;
}

.complete-text {
    background: #d4edda;
    padding: 12px;
    border-radius: 6px;
    border-left: 3px solid #28a745;
    margin: 12px 0;
    line-height: 1.5;
    font-size: 0.95em;
}

.blanked-words {
    background: #fff3cd;
    padding: 10px;
    border-radius: 6px;
    border-left: 3px solid #ffc107;
    margin-top: 12px;
    font-weight: bold;
    font-size: 0.9em;
}

/* 文章相关单词显示 */
.essay-words {
    background: #e7f3ff;
    padding: 10px;
    border-radius: 6px;
    border-left: 3px solid #007bff;
    margin: 12px 0;
    font-size: 0.9em;
    color: #0056b3;
}

.essay-words strong {
    color: #004085;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .card {
        margin: 5px;
        padding: 10px;
    }
    
    .word {
        font-size: 1.8em;
    }
    
    .card-front {
        padding: 15px 10px;
    }
}

<script>
function playPronunciation(word, type) {
    // type: 0=美式发音, 1=英式发音
    const url = 'http://dict.youdao.com/dictvoice?type=' + type + '&audio=' + encodeURIComponent(word);
    const audio = new Audio(url);
    audio.play().catch(function(error) {
        console.log('发音播放失败:', error);
    });
}
</script>
"""

    def get_database_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _format_learning_content(self, content: Dict[str, Any], word: str = "") -> str:
        """
        格式化学习内容为HTML

        Args:
            content: 学习内容字典
            word: 单词（用于发音功能）

        Returns:
            str: 格式化的HTML内容
        """
        if not content or "error" in content:
            return "<div>学习内容生成失败</div>"

        html_parts = []

        # 音标（带发音功能）
        if "phonetic" in content:
            phonetic_text = escape(str(content["phonetic"]))
            if word:
                # 添加美式和英式发音图标
                pronunciation_html = f"""
                <div class='phonetic'>
                    <strong>音标:</strong> {phonetic_text}
                    <span class="pronunciation-buttons">
                        <button class="pronunciation-btn" onclick="playPronunciation('{word}', 0)" title="美式发音">🇺🇸</button>
                        <button class="pronunciation-btn" onclick="playPronunciation('{word}', 1)" title="英式发音">🇬🇧</button>
                    </span>
                </div>
                """
            else:
                pronunciation_html = f"<div class='phonetic'><strong>音标:</strong> {phonetic_text}</div>"
            html_parts.append(pronunciation_html)

        # 发音分割
        if "pronunciation" in content:
            html_parts.append(
                f"<div class='pronunciation'><strong>发音:</strong> {escape(str(content['pronunciation']))}</div>"
            )

        # 词性
        if "part_of_speech" in content:
            pos = content["part_of_speech"]
            if isinstance(pos, list):
                pos_str = ", ".join(pos)
            else:
                pos_str = str(pos)
            html_parts.append(
                f"<div class='pos'><strong>词性:</strong> {escape(pos_str)}</div>"
            )

        # 翻译
        if "translations" in content:
            translations = content["translations"]
            if isinstance(translations, list):
                trans_html = (
                    "<ul>"
                    + "".join([f"<li>{escape(str(t))}</li>" for t in translations])
                    + "</ul>"
                )
            else:
                trans_html = escape(str(translations))
            html_parts.append(
                f"<div class='translations'><strong>常用翻译:</strong><br>{trans_html}</div>"
            )

        # 常用短语
        if "common_phrases" in content:
            phrases = content["common_phrases"]
            if isinstance(phrases, list):
                phrases_html = (
                    "<ul>"
                    + "".join([f"<li>{escape(str(p))}</li>" for p in phrases])
                    + "</ul>"
                )
            else:
                phrases_html = escape(str(phrases))
            html_parts.append(
                f"<div class='phrases'><strong>常用短语:</strong><br>{phrases_html}</div>"
            )

        # 词根词缀
        if "etymology" in content:
            html_parts.append(
                f"<div class='etymology'><strong>词根词缀:</strong> {escape(str(content['etymology']))}</div>"
            )

        # 例句
        if "examples" in content:
            examples = content["examples"]
            if isinstance(examples, list):
                examples_html = (
                    "<ol>"
                    + "".join([f"<li>{escape(str(ex))}</li>" for ex in examples])
                    + "</ol>"
                )
            else:
                examples_html = escape(str(examples))
            html_parts.append(
                f"<div class='examples'><strong>例句:</strong><br>{examples_html}</div>"
            )

        return '<div class="word-content">' + "<br>".join(html_parts) + "</div>"

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

    def _create_word_spelling_card(
        self, word: str, content: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        创建单词拼写卡片

        Args:
            word: 单词
            content: 学习内容

        Returns:
            Dict: 卡片数据
        """
        # 获取主要翻译作为提示
        hint = "英语单词"
        if "translations" in content:
            translations = content["translations"]
            if isinstance(translations, list) and translations:
                hint = str(translations[0])
            elif isinstance(translations, str):
                hint = translations

        front = f"""
        <div class="card-front word-spelling">
            <div class="spelling-hint">
                <h3>请拼写这个单词:</h3>
                <div class="meaning">{escape(hint)}</div>
                <div class="phonetic">{escape(str(content.get('phonetic', '')))}</div>
            </div>
        </div>
        """

        back = f"""
        <div class="card-back">
            <h2 class="word spelling-answer">{escape(word)}</h2>
            {self._format_learning_content(content)}
        </div>
        """

        return {
            "front": front.strip(),
            "back": back.strip(),
            "tags": "word-spelling toefl",
            "type": "word_spelling",
        }

    def _create_word_reverse_card(
        self, word: str, content: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        创建反向单词卡片（看翻译想单词）

        Args:
            word: 单词
            content: 学习内容

        Returns:
            Dict: 卡片数据
        """
        # 获取翻译作为正面
        translations_text = "英语单词"
        if "translations" in content:
            translations = content["translations"]
            if isinstance(translations, list):
                translations_text = " / ".join([str(t) for t in translations])
            else:
                translations_text = str(translations)

        front = f"""
        <div class="card-front word-reverse">
            <h3>这个中文意思对应的英语单词是:</h3>
            <div class="chinese-meaning">{escape(translations_text)}</div>
            <div class="hint">请回想对应的英语单词</div>
        </div>
        """

        back = f"""
        <div class="card-back">
            <h2 class="word reverse-answer">{escape(word)}</h2>
            {self._format_learning_content(content)}
        </div>
        """

        return {
            "front": front.strip(),
            "back": back.strip(),
            "tags": "word-reverse toefl",
            "type": "word_reverse",
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

                # 为每个单词创建三种卡片
                cards.append(self._create_word_recognition_card(word, content))
                cards.append(self._create_word_spelling_card(word, content))
                cards.append(self._create_word_reverse_card(word, content))

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

                # 单词识别卡片
                note1 = genanki.Note(
                    model=self.word_model,
                    fields=[word, formatted_content, "recognition"],
                    tags=["word-recognition", "toefl"],
                )
                deck.add_note(note1)

                # 拼写卡片 - 只显示主要翻译
                main_translation = self._get_main_translation(content)
                note2 = genanki.Note(
                    model=self.word_model,
                    fields=[word, main_translation, "spelling"],
                    tags=["word-spelling", "toefl"],
                )
                deck.add_note(note2)

                # 反向卡片 - 只显示主要翻译
                note3 = genanki.Note(
                    model=self.word_model,
                    fields=[word, main_translation, "reverse"],
                    tags=["word-reverse", "toefl"],
                )
                deck.add_note(note3)

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

    def _get_main_translation(self, content: Dict[str, Any]) -> str:
        """
        获取主要翻译内容

        Args:
            content: 学习内容字典

        Returns:
            str: 主要翻译
        """
        if "translations" in content:
            translations = content["translations"]
            if isinstance(translations, list) and translations:
                return escape(str(translations[0]))
            elif isinstance(translations, str):
                return escape(translations)

        return "无翻译信息"

    def _create_css_file(self, css_file: str) -> None:
        """创建Anki卡片的CSS样式文件"""
        css_content = """
/* TOEFL单词学习卡片样式 */

.card {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    line-height: 1.6;
    margin: 20px;
    padding: 20px;
    background: #f8f9fa;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

/* 正面卡片样式 */
.card-front {
    text-align: center;
    padding: 30px 20px;
}

.card-front h2, .card-front h3 {
    color: #2c3e50;
    margin-bottom: 20px;
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
    margin-top: 20px;
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

.word-content > div {
    margin-bottom: 15px;
    padding: 8px 0;
    border-bottom: 1px solid #ecf0f1;
}

.word-content > div:last-child {
    border-bottom: none;
}

.phonetic {
    font-family: 'Lucida Sans Unicode', sans-serif;
    color: #e74c3c;
    font-size: 1.1em;
}

.pronunciation {
    color: #9b59b6;
    font-weight: bold;
}

.pos {
    color: #f39c12;
    font-weight: bold;
}

.translations ul, .phrases ul, .examples ol {
    margin: 10px 0;
    padding-left: 20px;
}

.translations li, .phrases li, .examples li {
    margin: 5px 0;
    color: #2c3e50;
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
