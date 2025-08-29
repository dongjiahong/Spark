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
import threading
import uuid
import time
import os
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
        获取分页的短文数据（优先显示active状态的study_groups）
        
        Args:
            page: 页码（从1开始）
            per_page: 每页条数
            
        Returns:
            包含短文数据和分页信息的字典
        """
        conn = self.get_database_connection()
        cursor = conn.cursor()
        
        try:
            # 首先查找active状态的study_groups
            cursor.execute("""
                SELECT sg.*, e.* FROM study_groups sg 
                LEFT JOIN essay e ON sg.essay_id = e.id 
                WHERE sg.group_status = 'active' AND e.id IS NOT NULL
                ORDER BY sg.created_date DESC
            """)
            active_groups = cursor.fetchall()
            
            if active_groups and page == 1:
                # 如果有active状态的组且是第一页，优先显示
                essays = active_groups[:per_page]
                total_count = len(active_groups)
                essay_source = "active_groups"
            else:
                # 否则按原来逻辑显示所有essay（包括没有study_group的旧数据）
                cursor.execute("SELECT COUNT(*) FROM essay")
                total_count = cursor.fetchone()[0]
                
                offset = (page - 1) * per_page
                cursor.execute(
                    "SELECT * FROM essay ORDER BY created DESC LIMIT ? OFFSET ?",
                    (per_page, offset)
                )
                essays = cursor.fetchall()
                essay_source = "all_essays"
            
            # 处理短文数据
            essay_data = []
            for essay in essays:
                essay_dict = dict(essay)
                
                # 如果是从 active_groups 来的数据，需要附加 study_group 信息
                if essay_source == "active_groups":
                    study_group_id = essay_dict.get('id')  # study_group id
                    study_group_status = essay_dict.get('group_status')
                    # 重新获取essay数据（因为JOIN后字段名可能冲突）
                    essay_id = essay_dict.get('essay_id')
                    cursor.execute("SELECT * FROM essay WHERE id = ?", (essay_id,))
                    essay_data_raw = cursor.fetchone()
                    if essay_data_raw:
                        essay_dict.update(dict(essay_data_raw))
                        essay_dict['study_group_id'] = study_group_id  # 保持study_group id
                        essay_dict['study_group_status'] = study_group_status
                else:
                    # 检查是否有对应的study_group
                    cursor.execute("SELECT * FROM study_groups WHERE essay_id = ?", (essay_dict['id'],))
                    study_group = cursor.fetchone()
                    if study_group:
                        essay_dict['study_group_id'] = study_group['id']
                        essay_dict['study_group_status'] = study_group['group_status']
                    else:
                        essay_dict['study_group_id'] = None
                        essay_dict['study_group_status'] = None
                
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
                },
                'source': essay_source,
                'has_active_groups': len(active_groups) > 0 if 'active_groups' in locals() else False
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

# 任务状态管理
task_status = {}

class TaskManager:
    """异步任务管理器 - 使用数据库持久化"""
    
    def __init__(self, db_path: str = "toefl_words.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_tasks_table()
        # 启动时清理7天前的旧任务
        self.cleanup_old_tasks(7)
    
    def _init_tasks_table(self):
        """初始化任务表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
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
            conn.commit()
        finally:
            conn.close()
    
    def create_task(self, task_id: str, task_info: Dict[str, Any]):
        """创建新任务"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO tasks (task_id, status, progress, message, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                task_id,
                'running',
                0,
                '任务开始',
                time.time()
            ))
            conn.commit()
        finally:
            conn.close()
    
    def update_task(self, task_id: str, **kwargs):
        """更新任务状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            # 构建更新SQL
            set_clauses = []
            values = []
            
            for key, value in kwargs.items():
                if key in ['status', 'progress', 'message', 'result', 'error', 'completed_at', 'failed_at']:
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
            
            if set_clauses:
                values.append(task_id)
                sql = f"UPDATE tasks SET {', '.join(set_clauses)} WHERE task_id = ?"
                cursor.execute(sql, values)
                conn.commit()
        finally:
            conn.close()
    
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT * FROM tasks WHERE task_id = ?', (task_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()
    
    def complete_task(self, task_id: str, result: Dict[str, Any]):
        """完成任务"""
        self.update_task(task_id, 
            status='completed',
            progress=100,
            message='任务完成',
            result=json.dumps(result) if isinstance(result, dict) else str(result),
            completed_at=time.time()
        )
    
    def fail_task(self, task_id: str, error: str):
        """任务失败"""
        self.update_task(task_id,
            status='failed',
            message=f'任务失败: {error}',
            error=error,
            failed_at=time.time()
        )
    
    def cleanup_old_tasks(self, days_old: int = 7):
        """清理旧任务记录"""
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                DELETE FROM tasks 
                WHERE (completed_at IS NOT NULL AND completed_at < ?) 
                   OR (failed_at IS NOT NULL AND failed_at < ?)
            ''', (cutoff_time, cutoff_time))
            conn.commit()
        finally:
            conn.close()

# 初始化管理器
data_manager = WebDataManager()
task_manager = TaskManager()

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

def async_generate_essay(task_id: str, word_count: int, essay_type: str):
    """异步生成短文的后台任务"""
    try:
        # 更新任务状态
        task_manager.update_task(task_id, progress=25, message='选择单词中...')
        
        # 模拟进度更新
        time.sleep(0.5)
        task_manager.update_task(task_id, progress=50, message='生成学习内容...')
        
        # 执行实际的生成任务
        result = word_manager.generate_learning_session(
            word_count=word_count, 
            essay_type=essay_type
        )
        
        task_manager.update_task(task_id, progress=75, message='创建短文...')
        time.sleep(0.5)
        
        # 完成任务
        task_manager.complete_task(task_id, {
            'success': True,
            'message': f'成功生成包含{word_count}个单词的{essay_type}',
            'essay_id': result.get('essay_id'),
            'words_processed': result.get('words_processed', [])
        })
        
    except Exception as e:
        task_manager.fail_task(task_id, str(e))

@app.route('/api/generate', methods=['POST'])
def generate_new_essay():
    """生成新短文API - 异步模式"""
    if not word_manager:
        return jsonify({'error': '生成功能不可用，请检查business_logic模块'}), 500
    
    try:
        # 获取请求参数
        data = request.get_json() or {}
        word_count = data.get('word_count', 10)  # 默认10个单词
        essay_type = data.get('essay_type', 'story')  # 默认故事类型
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 创建任务
        task_manager.create_task(task_id, {
            'type': 'generate_essay',
            'word_count': word_count,
            'essay_type': essay_type
        })
        
        # 启动后台线程
        thread = threading.Thread(
            target=async_generate_essay,
            args=(task_id, word_count, essay_type)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '任务已启动，正在后台生成...'
        })
    
    except Exception as e:
        return jsonify({'error': f'启动任务失败: {str(e)}'}), 500

@app.route('/api/task/<task_id>')
def get_task_status(task_id: str):
    """获取任务状态API"""
    try:
        task = task_manager.get_task(task_id)
        
        if not task:
            return jsonify({'error': '任务不存在'}), 404
        
        # 解析result JSON字符串
        result = task.get('result')
        if result and isinstance(result, str):
            try:
                result = json.loads(result)
            except:
                pass  # 保持原始字符串
        
        return jsonify({
            'task_id': task_id,
            'status': task.get('status', 'unknown'),
            'progress': task.get('progress', 0),
            'message': task.get('message', ''),
            'result': result,
            'error': task.get('error'),
            'created_at': task.get('created_at'),
            'completed_at': task.get('completed_at'),
            'failed_at': task.get('failed_at')
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

@app.route('/api/study-group/<int:group_id>/complete', methods=['POST'])
def complete_study_group(group_id: int):
    """标记学习组为已完成"""
    try:
        conn = data_manager.get_database_connection()
        cursor = conn.cursor()
        
        # 检查学习组是否存在
        cursor.execute('SELECT * FROM study_groups WHERE id = ?', (group_id,))
        group = cursor.fetchone()
        
        if not group:
            return jsonify({'error': '学习组不存在'}), 404
        
        if group['group_status'] == 'completed':
            return jsonify({'message': '学习组已经是完成状态'}), 200
        
        # 更新学习组状态
        cursor.execute(
            'UPDATE study_groups SET group_status = ?, completed_items = total_items, completed_date = CURRENT_TIMESTAMP WHERE id = ?',
            ('completed', group_id)
        )
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': '学习组已标记为完成',
            'group_id': group_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

@app.route('/api/study-groups/current')
def get_current_study_group():
    """获取当前活跃的学习组"""
    try:
        conn = data_manager.get_database_connection()
        cursor = conn.cursor()
        
        # 查找最新的active状态学习组
        cursor.execute(
            'SELECT * FROM study_groups WHERE group_status = ? ORDER BY created_date DESC LIMIT 1',
            ('active',)
        )
        active_group = cursor.fetchone()
        
        if active_group:
            return jsonify({
                'has_active_group': True,
                'group': dict(active_group)
            })
        else:
            return jsonify({
                'has_active_group': False,
                'group': None
            })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

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

def ensure_database_initialized():
    """确保数据库已初始化"""
    try:
        from init_database import init_database, check_database_integrity
        
        # 检查数据库是否存在
        if not os.path.exists("toefl_words.db"):
            print("⚠️ 数据库文件不存在，正在初始化...")
            init_database()
            return
            
        # 检查必需的表是否存在
        conn = sqlite3.connect("toefl_words.db")
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='study_groups'")
            if not cursor.fetchone():
                print("⚠️ 缺少必需的数据库表，正在更新数据库结构...")
                conn.close()
                init_database()
                return
            print("✅ 数据库结构检查通过")
        finally:
            conn.close()
            
    except ImportError:
        print("⚠️ 无法导入init_database模块，跳过数据库检查")
    except Exception as e:
        print(f"⚠️ 数据库检查出错: {e}")

if __name__ == '__main__':
    print("启动TOEFL单词学习系统Web查看器...")
    
    # 确保数据库已正确初始化
    ensure_database_initialized()
    
    print("访问地址: http://localhost:8080 或 http://127.0.0.1:8080")
    app.run(debug=True, host='0.0.0.0', port=8080)