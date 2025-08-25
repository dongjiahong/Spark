#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网页查看器
提供web界面查看数据库中的单词和短文数据
"""

from flask import Flask, render_template, jsonify, request
import sqlite3
import json
import math
from typing import Dict, Any, List, Optional

app = Flask(__name__)

class WebDataManager:
    """Web数据管理器"""
    
    def __init__(self, db_path: str = "toefl_words.db"):
        self.db_path = db_path
    
    def get_database_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_essays_with_pagination(self, page: int = 1, per_page: int = 1) -> Dict[str, Any]:
        """
        获取分页的短文数据
        
        Args:
            page: 页码（从1开始）
            per_page: 每页条数
            
        Returns:
            包含短文数据和分页信息的字典
        """
        conn = self.get_database_connection()
        cursor = conn.cursor()
        
        try:
            # 获取总数
            cursor.execute("SELECT COUNT(*) FROM essay")
            total_count = cursor.fetchone()[0]
            
            # 计算偏移量
            offset = (page - 1) * per_page
            
            # 获取短文数据（按时间倒序）
            cursor.execute(
                "SELECT * FROM essay ORDER BY created DESC LIMIT ? OFFSET ?",
                (per_page, offset)
            )
            essays = cursor.fetchall()
            
            # 处理短文数据
            essay_data = []
            for essay in essays:
                essay_dict = dict(essay)
                
                # 解析JSON内容
                try:
                    essay_dict['content'] = json.loads(essay_dict['content'])
                except json.JSONDecodeError:
                    essay_dict['content'] = {}
                
                # 获取相关单词的详细信息
                word_list = essay_dict['words'].split(',')
                word_details = self.get_words_details(word_list)
                essay_dict['word_details'] = word_details
                
                essay_data.append(essay_dict)
            
            # 计算分页信息
            total_pages = math.ceil(total_count / per_page)
            
            return {
                'essays': essay_data,
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total_count': total_count,
                    'total_pages': total_pages,
                    'has_prev': page > 1,
                    'has_next': page < total_pages,
                    'prev_page': page - 1 if page > 1 else None,
                    'next_page': page + 1 if page < total_pages else None
                }
            }
            
        finally:
            conn.close()
    
    def get_words_details(self, word_list: List[str]) -> List[Dict[str, Any]]:
        """
        获取单词的详细信息
        
        Args:
            word_list: 单词列表
            
        Returns:
            单词详细信息列表
        """
        if not word_list:
            return []
        
        conn = self.get_database_connection()
        cursor = conn.cursor()
        
        try:
            # 构建占位符
            placeholders = ','.join(['?'] * len(word_list))
            
            cursor.execute(
                f"SELECT * FROM words WHERE word IN ({placeholders})",
                word_list
            )
            words = cursor.fetchall()
            
            word_details = []
            for word in words:
                word_dict = dict(word)
                
                # 解析学习内容JSON
                try:
                    learn_content = json.loads(word_dict['learn_content'])
                    word_dict['learn_content'] = learn_content
                except json.JSONDecodeError:
                    word_dict['learn_content'] = {}
                
                word_details.append(word_dict)
            
            # 按原始单词列表顺序排序
            sorted_details = []
            for word in word_list:
                for detail in word_details:
                    if detail['word'] == word:
                        sorted_details.append(detail)
                        break
            
            return sorted_details
            
        finally:
            conn.close()

# 初始化数据管理器
data_manager = WebDataManager()

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

@app.route('/api/essays')
def get_essays():
    """获取短文数据API"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 1, type=int)
    
    try:
        data = data_manager.get_essays_with_pagination(page, per_page)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """获取统计信息API"""
    conn = data_manager.get_database_connection()
    cursor = conn.cursor()
    
    try:
        # 获取基本统计
        cursor.execute("SELECT COUNT(*) FROM words")
        total_words = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM words WHERE count = 0")
        unused_words = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM words WHERE count > 0")
        learned_words = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM essay")
        total_essays = cursor.fetchone()[0]
        
        return jsonify({
            'total_words': total_words,
            'unused_words': unused_words,
            'learned_words': learned_words,
            'total_essays': total_essays
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

if __name__ == '__main__':
    print("启动TOEFL单词学习系统Web查看器...")
    print("访问地址: http://localhost:8080 或 http://127.0.0.1:8080")
    app.run(debug=True, host='0.0.0.0', port=8080)