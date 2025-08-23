#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI服务模块 - 与大模型交互
提供单词学习信息生成和短文生成功能
"""

import requests
import json
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class AIService:
    """AI服务类，用于与大模型交互"""

    def __init__(self):
        """初始化AI服务"""
        self.api_url = os.getenv("OPENAI_URL")
        self.api_key = os.getenv("OPENAI_KEY")
        self.model = os.getenv("MODEL")

        if not all([self.api_url, self.api_key, self.model]):
            raise ValueError("请在.env文件中配置OPENAI_URL、OPENAI_KEY和MODEL")

    def _make_request(
        self, messages: List[Dict[str, str]], max_tokens: int = 2000
    ) -> str:
        """
        向AI服务发送请求

        Args:
            messages: 对话消息列表
            max_tokens: 最大token数

        Returns:
            str: AI回复内容

        Raises:
            Exception: 请求失败时抛出异常
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }

        try:
            response = requests.post(
                self.api_url, headers=headers, json=data, timeout=30
            )
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except requests.exceptions.RequestException as e:
            raise Exception(f"AI服务请求失败: {e}")
        except KeyError as e:
            raise Exception(f"AI服务响应格式错误: {e}")

    def generate_word_learning_info(self, word: str) -> Dict[str, Any]:
        """
        为单词生成学习信息

        Args:
            word: 要学习的单词

        Returns:
            Dict: 包含学习信息的字典
        """
        prompt = f"""请为单词"{word}"生成完整的学习信息，以JSON格式返回，包含以下字段：

1. phonetic: 音标（英式和美式）
2. pronunciation: 发音分割（用小圆点分隔，如con·tem·po·rary）
3. part_of_speech: 词性（可能有多个）
4. translations: 常用翻译（2-3个最常用的中文释义）
5. common_phrases: 常用短语（1-3个带中文翻译）
6. etymology: 词根词缀分析
7. examples: 例句（2个句子，每个都要有中文翻译）

请确保返回的是有效的JSON格式，便于解析。"""

        messages = [
            {
                "role": "system",
                "content": "你是一个专业的英语教学助手，擅长生成详细的单词学习资料。",
            },
            {"role": "user", "content": prompt},
        ]

        try:
            response = self._make_request(messages)
            # 尝试解析JSON
            learning_info = json.loads(response)
            return learning_info
        except json.JSONDecodeError:
            # 如果JSON解析失败，返回错误信息
            return {"error": "无法解析AI返回的JSON格式", "raw_response": response}

    def generate_essay(
        self, words: List[str], essay_type: str = "story"
    ) -> Dict[str, str]:
        """
        根据选择的单词生成短文和翻译

        Args:
            words: 要包含的单词列表
            essay_type: 短文类型（童话、故事、新闻、预言）

        Returns:
            Dict: 包含英文短文和中文翻译的字典
        """
        type_mapping = {
            "fairy_tale": "童话故事",
            "story": "故事",
            "news": "新闻报道",
            "prophecy": "预言",
        }

        chinese_type = type_mapping.get(essay_type, "故事")
        words_str = "、".join(words)

        prompt = f"""请创作一篇{chinese_type}，要求：

1. 必须包含以下单词：{words_str}
2. 文章要简短易记（30-150词），适合背诵，文章尽可能简短
3. 每个单词都要有记忆点，在文中的使用要生动有趣
4. 情节要有趣且容易记忆
5. 语言要地道自然

请用以下JSON格式返回：
{{
    "title": "标题",
    "english_content": "英文正文",
    "chinese_translation": "中文翻译"
}}

确保返回有效的JSON格式。"""

        messages = [
            {
                "role": "system",
                "content": f"你是一个创意写作专家，擅长创作有趣且易于记忆的{chinese_type}。",
            },
            {"role": "user", "content": prompt},
        ]

        try:
            response = self._make_request(messages, max_tokens=1500)
            essay_data = json.loads(response)
            return essay_data
        except json.JSONDecodeError:
            return {"error": "无法解析AI返回的JSON格式", "raw_response": response}


def test_ai_service():
    """测试AI服务功能"""
    try:
        ai = AIService()

        print("测试单词学习信息生成...")
        word_info = ai.generate_word_learning_info("contemporary")
        print(f"单词信息: {json.dumps(word_info, ensure_ascii=False, indent=2)}")

        print("\n测试短文生成...")
        essay = ai.generate_essay(["contemporary", "adventure", "mysterious"], "story")
        print(f"短文: {json.dumps(essay, ensure_ascii=False, indent=2)}")

    except Exception as e:
        print(f"测试失败: {e}")


if __name__ == "__main__":
    test_ai_service()
