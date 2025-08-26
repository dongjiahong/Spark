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

# 动态导入业务逻辑模块
try:
    from business_logic import WordManager
    word_manager = WordManager()
except ImportError:
    word_manager = None
    print("警告: 无法导入business_logic模块，生成功能将不可用")

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

@app.route('/api/generate', methods=['POST'])
def generate_new_essay():
    """生成新短文API"""
    if not word_manager:
        return jsonify({'error': '生成功能不可用，请检查business_logic模块'}), 500
    
    try:
        # 获取请求参数
        data = request.get_json() or {}
        word_count = data.get('word_count', 10)  # 默认10个单词
        essay_type = data.get('essay_type', 'story')  # 默认故事类型
        
        # 生成新的学习会话
        result = word_manager.generate_learning_session(
            word_count=word_count, 
            essay_type=essay_type
        )
        
        return jsonify({
            'success': True,
            'message': f'成功生成包含{word_count}个单词的{essay_type}',
            'essay_id': result.get('essay_id'),
            'words_processed': result.get('words_processed', [])
        })
    
    except Exception as e:
        return jsonify({'error': f'生成失败: {str(e)}'}), 500

@app.route('/api/generate/progress')
def get_generation_progress():
    """获取生成进度API（简化版本，实际可能需要更复杂的状态管理）"""
    # 这里返回模拟的进度信息，实际项目中可能需要Redis等来管理状态
    return jsonify({
        'progress': 100,  # 百分比
        'status': '完成',
        'current_step': '短文生成完成',
        'total_steps': 4
    })

@app.route('/anki')
def anki_manager():
    """Anki管理页面"""
    return render_template('anki_manager.html')

@app.route('/api/anki/stats')
def get_anki_stats():
    """获取Anki相关统计信息API"""
    conn = data_manager.get_database_connection()
    cursor = conn.cursor()
    
    try:
        # 获取基本统计
        cursor.execute("SELECT COUNT(*) FROM words WHERE learn_content != '{}'")
        available_words = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM essay")
        available_essays = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM words WHERE count > 0 AND learn_content != '{}'")
        learned_words = cursor.fetchone()[0]
        
        # 估算可生成的卡片数量
        word_cards = available_words  # 每个单词1张卡片
        essay_cards = available_essays * 2  # 每篇短文2张卡片（翻译+反向）
        total_cards = word_cards + essay_cards
        
        return jsonify({
            'available_words': available_words,
            'available_essays': available_essays,
            'learned_words': learned_words,
            'estimated_word_cards': word_cards,
            'estimated_essay_cards': essay_cards,
            'estimated_total_cards': total_cards
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/anki/preview')
def get_anki_preview():
    """获取Anki卡片预览数据API"""
    card_type = request.args.get('type', 'word')  # word 或 essay
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)  # 预览每页显示5个
    
    try:
        if card_type == 'word':
            return get_word_cards_preview(page, per_page)
        elif card_type == 'essay':
            return get_essay_cards_preview(page, per_page)
        else:
            return jsonify({'error': '不支持的卡片类型'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_word_cards_preview(page: int, per_page: int):
    """获取单词卡片预览"""
    conn = data_manager.get_database_connection()
    cursor = conn.cursor()
    
    try:
        # 获取总数
        cursor.execute("SELECT COUNT(*) FROM words WHERE learn_content != '{}'")
        total_count = cursor.fetchone()[0]
        
        if total_count == 0:
            return jsonify({
                'cards': [],
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total_count': 0,
                    'total_pages': 0,
                    'has_prev': False,
                    'has_next': False
                }
            })
        
        # 计算分页
        offset = (page - 1) * per_page
        total_pages = math.ceil(total_count / per_page)
        
        # 获取单词数据
        cursor.execute(
            "SELECT * FROM words WHERE learn_content != '{}' ORDER BY created DESC LIMIT ? OFFSET ?",
            (per_page, offset)
        )
        words = cursor.fetchall()
        
        # 动态导入AnkiExporter
        try:
            from anki_export import AnkiExporter
            exporter = AnkiExporter()
        except ImportError:
            return jsonify({'error': 'AnkiExporter模块不可用'}), 500
        
        cards = []
        for word_row in words:
            word = word_row["word"]
            try:
                content = json.loads(word_row["learn_content"])
                formatted_content = exporter._format_learning_content(content, word)
                cards.append({
                    'id': word_row['id'],
                    'word': word,
                    'content': formatted_content,
                    'type': 'word_recognition'
                })
            except json.JSONDecodeError:
                continue
        
        return jsonify({
            'cards': cards,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_prev': page > 1,
                'has_next': page < total_pages
            }
        })
        
    finally:
        conn.close()

def get_essay_cards_preview(page: int, per_page: int):
    """获取短文卡片预览"""
    conn = data_manager.get_database_connection()
    cursor = conn.cursor()
    
    try:
        # 获取总数
        cursor.execute("SELECT COUNT(*) FROM essay")
        total_count = cursor.fetchone()[0]
        
        if total_count == 0:
            return jsonify({
                'cards': [],
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total_count': 0,
                    'total_pages': 0,
                    'has_prev': False,
                    'has_next': False
                }
            })
        
        # 计算分页
        offset = (page - 1) * per_page
        total_pages = math.ceil(total_count / per_page)
        
        # 获取短文数据
        cursor.execute(
            "SELECT * FROM essay ORDER BY created DESC LIMIT ? OFFSET ?",
            (per_page, offset)
        )
        essays = cursor.fetchall()
        
        cards = []
        for essay_row in essays:
            essay_id = essay_row["id"]
            words = essay_row["words"].split(",")
            
            try:
                content = json.loads(essay_row["content"])
                
                # 创建翻译卡片预览
                cards.append({
                    'id': f'essay_{essay_id}_translation',
                    'title': content.get("title", f"Essay {essay_id}"),
                    'english_content': content.get("english_content", ""),
                    'chinese_content': content.get("chinese_translation", ""),
                    'words': words,
                    'type': 'essay_translation'
                })
                
                # 创建反向卡片预览
                cards.append({
                    'id': f'essay_{essay_id}_reverse',
                    'title': content.get("title", f"Essay {essay_id}"),
                    'english_content': content.get("english_content", ""),
                    'chinese_content': content.get("chinese_translation", ""),
                    'words': words,
                    'type': 'essay_reverse'
                })
                
            except json.JSONDecodeError:
                continue
        
        return jsonify({
            'cards': cards,
            'pagination': {
                'current_page': page,
                'per_page': per_page,
                'total_count': total_count * 2,  # 每篇短文有2张卡片
                'total_pages': math.ceil(total_count * 2 / per_page),
                'has_prev': page > 1,
                'has_next': page < math.ceil(total_count * 2 / per_page)
            }
        })
        
    finally:
        conn.close()

@app.route('/api/anki/export/<export_type>')
def export_anki_file(export_type):
    """导出Anki文件API"""
    try:
        # 动态导入AnkiExporter
        from anki_export import AnkiExporter
        exporter = AnkiExporter()
        
        if export_type == 'words':
            file_path = exporter.export_words_to_apkg()
        elif export_type == 'essays':
            file_path = exporter.export_essays_to_apkg()
        elif export_type == 'all':
            files = exporter.export_all_to_apkg()
            # 返回所有文件的信息
            return jsonify({
                'success': True,
                'files': files,
                'message': '成功导出所有内容'
            })
        else:
            return jsonify({'error': '不支持的导出类型'}), 400
        
        return jsonify({
            'success': True,
            'file_path': file_path,
            'download_url': f'/download/{file_path.split("/")[-1]}',
            'message': f'成功导出{export_type}内容'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """下载文件API"""
    try:
        from flask import send_file
        import os
        
        # 检查文件是否存在
        if os.path.exists(filename):
            return send_file(filename, as_attachment=True)
        
        # 检查anki_export目录
        anki_export_path = os.path.join('anki_export', filename)
        if os.path.exists(anki_export_path):
            return send_file(anki_export_path, as_attachment=True)
        
        # 检查当前目录
        current_path = os.path.join('.', filename)
        if os.path.exists(current_path):
            return send_file(current_path, as_attachment=True)
        
        return jsonify({'error': '文件不存在'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("启动TOEFL单词学习系统Web查看器...")
    print("访问地址: http://localhost:8080 或 http://127.0.0.1:8080")
    app.run(debug=True, host='0.0.0.0', port=8080)