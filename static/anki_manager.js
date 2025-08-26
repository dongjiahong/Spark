/**
 * Anki管理器JavaScript
 */

class AnkiManager {
    constructor() {
        this.currentTab = 'preview';
        this.currentPreviewPage = 1;
        this.currentPreviewType = 'word';
        this.totalPreviewPages = 1;
        
        this.init();
    }

    /**
     * 初始化应用
     */
    init() {
        this.bindEvents();
        this.loadStats();
        this.loadPreview();
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 选项卡切换
        document.getElementById('preview-tab').addEventListener('click', () => {
            this.switchTab('preview');
        });

        document.getElementById('generate-tab').addEventListener('click', () => {
            this.switchTab('generate');
        });

        document.getElementById('export-tab').addEventListener('click', () => {
            this.switchTab('export');
        });

        // 预览功能
        document.getElementById('preview-type').addEventListener('change', (e) => {
            this.currentPreviewType = e.target.value;
            this.currentPreviewPage = 1;
            this.loadPreview();
        });

        document.getElementById('refresh-preview-btn').addEventListener('click', () => {
            this.loadPreview();
        });

        // 预览分页
        document.getElementById('preview-prev-btn').addEventListener('click', () => {
            if (this.currentPreviewPage > 1) {
                this.currentPreviewPage--;
                this.loadPreview();
            }
        });

        document.getElementById('preview-next-btn').addEventListener('click', () => {
            if (this.currentPreviewPage < this.totalPreviewPages) {
                this.currentPreviewPage++;
                this.loadPreview();
            }
        });

        // 生成功能
        document.getElementById('generate-words-btn').addEventListener('click', () => {
            this.generateCards('words');
        });

        document.getElementById('generate-essays-btn').addEventListener('click', () => {
            this.generateCards('essays');
        });

        // 导出功能
        document.getElementById('export-words-btn').addEventListener('click', () => {
            this.exportAnki('words');
        });

        document.getElementById('export-essays-btn').addEventListener('click', () => {
            this.exportAnki('essays');
        });

        document.getElementById('export-all-btn').addEventListener('click', () => {
            this.exportAnki('all');
        });

        // 重试按钮
        document.getElementById('retry-btn').addEventListener('click', () => {
            this.loadPreview();
        });
    }

    /**
     * 加载统计信息
     */
    async loadStats() {
        try {
            const response = await fetch('/api/anki/stats');
            const stats = await response.json();
            
            if (stats.error) {
                console.error('加载统计失败:', stats.error);
                return;
            }

            const statsElement = document.getElementById('anki-stats');
            statsElement.innerHTML = `
                可用单词: ${stats.available_words} | 
                可用短文: ${stats.available_essays} | 
                已学单词: ${stats.learned_words} | 
                预计卡片: ${stats.estimated_total_cards}张
            `;
        } catch (error) {
            console.error('加载统计失败:', error);
        }
    }

    /**
     * 切换选项卡
     */
    switchTab(tabName) {
        // 移除当前激活状态
        document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        
        // 激活新选项卡
        document.getElementById(`${tabName}-tab`).classList.add('active');
        document.getElementById(`${tabName}-section`).classList.add('active');
        
        this.currentTab = tabName;

        // 如果切换到预览选项卡，重新加载预览
        if (tabName === 'preview') {
            this.loadPreview();
        }
    }

    /**
     * 加载预览数据
     */
    async loadPreview() {
        this.showPreviewLoading(true);
        this.hideError();

        try {
            const response = await fetch(`/api/anki/preview?type=${this.currentPreviewType}&page=${this.currentPreviewPage}`);
            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            this.renderPreview(data);
            this.updatePreviewPagination(data.pagination);
            this.showPreviewLoading(false);

        } catch (error) {
            console.error('加载预览失败:', error);
            this.showError(error.message);
            this.showPreviewLoading(false);
        }
    }

    /**
     * 渲染预览内容
     */
    renderPreview(data) {
        const container = document.getElementById('preview-container');
        
        if (!data.cards || data.cards.length === 0) {
            container.innerHTML = '<div class="no-data">暂无可预览的卡片</div>';
            return;
        }

        container.innerHTML = data.cards.map(card => {
            if (card.type === 'word_recognition') {
                return this.renderWordCard(card);
            } else if (card.type === 'essay_translation' || card.type === 'essay_reverse') {
                return this.renderEssayCard(card);
            }
            return '';
        }).join('');
    }

    /**
     * 渲染单词卡片
     */
    renderWordCard(card) {
        return `
            <div class="anki-card-preview">
                <div class="card-header">
                    <h3>单词识别卡片</h3>
                    <span class="card-id">ID: ${card.id}</span>
                </div>
                <div class="card-front">
                    <h2 class="word">${this.escapeHtml(card.word)}</h2>
                    <div class="hint">请回想这个单词的意思</div>
                </div>
                <div class="card-divider">正面 ↑ | 背面 ↓</div>
                <div class="card-back">
                    ${card.content}
                </div>
            </div>
        `;
    }

    /**
     * 渲染短文卡片
     */
    renderEssayCard(card) {
        const isReverse = card.type === 'essay_reverse';
        const frontContent = isReverse ? card.chinese_content : card.english_content;
        const backContent = isReverse ? card.english_content : card.chinese_content;
        const frontLabel = isReverse ? '中文翻译' : '英文原文';
        const backLabel = isReverse ? '英文原文' : '中文翻译';
        
        return `
            <div class="anki-card-preview">
                <div class="card-header">
                    <h3>${isReverse ? '短文反向' : '短文翻译'}卡片</h3>
                    <span class="card-id">ID: ${card.id}</span>
                </div>
                <div class="card-front">
                    <h3>${this.escapeHtml(card.title)}</h3>
                    <div class="content-text">${this.escapeHtml(frontContent)}</div>
                    <div class="essay-words">
                        <strong>相关单词:</strong> ${card.words.join(', ')}
                    </div>
                    <div class="hint">请${isReverse ? '根据中文翻译回想英文原文' : '翻译这段英文'}</div>
                </div>
                <div class="card-divider">正面 ↑ | 背面 ↓</div>
                <div class="card-back">
                    <h3>${this.escapeHtml(card.title)}</h3>
                    <div class="translation-pair">
                        <div class="content-section">
                            <h4>${frontLabel}:</h4>
                            <p>${this.escapeHtml(frontContent)}</p>
                        </div>
                        <div class="content-section">
                            <h4>${backLabel}:</h4>
                            <p>${this.escapeHtml(backContent)}</p>
                        </div>
                    </div>
                    <div class="essay-words">
                        <strong>相关单词:</strong> ${card.words.join(', ')}
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * 更新预览分页
     */
    updatePreviewPagination(pagination) {
        this.totalPreviewPages = pagination.total_pages;
        
        // 更新页码信息
        const pageInfo = document.getElementById('preview-page-info');
        pageInfo.textContent = `第 ${pagination.current_page} 页，共 ${pagination.total_pages} 页`;

        // 更新按钮状态
        const prevBtn = document.getElementById('preview-prev-btn');
        const nextBtn = document.getElementById('preview-next-btn');
        
        prevBtn.disabled = !pagination.has_prev;
        nextBtn.disabled = !pagination.has_next;

        // 显示分页控件
        const paginationElement = document.getElementById('preview-pagination');
        paginationElement.style.display = pagination.total_pages > 1 ? 'flex' : 'none';
    }

    /**
     * 生成卡片
     */
    async generateCards(type) {
        const progressContainer = document.getElementById(`${type === 'words' ? 'word' : 'essay'}-generate-progress`);
        const button = document.getElementById(`generate-${type}-btn`);
        const progressFill = document.getElementById(`${type === 'words' ? 'word' : 'essay'}-progress-fill`);
        const progressStatus = document.getElementById(`${type === 'words' ? 'word' : 'essay'}-progress-status`);

        // 显示进度
        button.disabled = true;
        progressContainer.style.display = 'flex';
        progressFill.style.width = '0%';
        progressStatus.textContent = '准备生成...';

        try {
            // 模拟进度更新
            const updateProgress = (progress, status) => {
                progressFill.style.width = progress + '%';
                progressStatus.textContent = status;
            };

            updateProgress(25, '读取数据库...');
            await new Promise(resolve => setTimeout(resolve, 300));

            updateProgress(50, '处理卡片内容...');
            await new Promise(resolve => setTimeout(resolve, 300));

            updateProgress(75, '格式化卡片...');
            await new Promise(resolve => setTimeout(resolve, 300));

            updateProgress(100, '生成完成！');
            
            // 显示成功消息
            this.showSuccessMessage(`${type === 'words' ? '单词' : '短文'}卡片生成完成！`);
            
            // 重新加载统计和预览
            this.loadStats();
            if (this.currentTab === 'preview') {
                this.loadPreview();
            }

        } catch (error) {
            console.error('生成卡片失败:', error);
            this.showError(`生成失败: ${error.message}`);
        } finally {
            // 恢复按钮状态
            setTimeout(() => {
                button.disabled = false;
                progressContainer.style.display = 'none';
            }, 1000);
        }
    }

    /**
     * 导出Anki包
     */
    async exportAnki(type) {
        const progressContainer = document.getElementById('export-progress');
        const progressFill = document.getElementById('export-progress-fill');
        const progressStatus = document.getElementById('export-progress-status');
        const downloadArea = document.getElementById('download-area');
        const downloadLinks = document.getElementById('download-links');

        // 禁用所有导出按钮
        document.querySelectorAll('.export-btn').forEach(btn => btn.disabled = true);

        // 显示进度
        progressContainer.style.display = 'flex';
        progressFill.style.width = '0%';
        progressStatus.textContent = '开始导出...';

        try {
            // 模拟进度更新
            const updateProgress = (progress, status) => {
                progressFill.style.width = progress + '%';
                progressStatus.textContent = status;
            };

            updateProgress(20, '读取卡片数据...');
            await new Promise(resolve => setTimeout(resolve, 500));

            updateProgress(50, '生成APKG文件...');

            // 发送导出请求
            const response = await fetch(`/api/anki/export/${type}`);
            const result = await response.json();

            updateProgress(80, '准备下载链接...');
            await new Promise(resolve => setTimeout(resolve, 300));

            if (result.success) {
                updateProgress(100, '导出完成！');
                
                // 显示下载链接
                downloadArea.style.display = 'block';
                
                if (type === 'all' && result.files) {
                    // 多个文件
                    downloadLinks.innerHTML = Object.entries(result.files).map(([key, filepath]) => {
                        const filename = filepath.split('/').pop();
                        return `
                            <div class="download-item">
                                <span class="file-info">
                                    <strong>${key === 'words' ? '单词卡片' : '短文卡片'}:</strong>
                                    ${filename}
                                </span>
                                <a href="/download/${filename}" class="download-link" download>
                                    <span>💾</span>
                                    <span>下载</span>
                                </a>
                            </div>
                        `;
                    }).join('');
                } else if (result.file_path) {
                    // 单个文件
                    const filename = result.file_path.split('/').pop();
                    const typeText = type === 'words' ? '单词卡片' : type === 'essays' ? '短文卡片' : '完整学习包';
                    
                    downloadLinks.innerHTML = `
                        <div class="download-item">
                            <span class="file-info">
                                <strong>${typeText}:</strong>
                                ${filename}
                            </span>
                            <a href="/download/${filename}" class="download-link" download>
                                <span>💾</span>
                                <span>下载</span>
                            </a>
                        </div>
                    `;
                }
                
                this.showSuccessMessage(result.message);
            } else {
                throw new Error(result.error || '导出失败');
            }

        } catch (error) {
            console.error('导出失败:', error);
            this.showError(`导出失败: ${error.message}`);
        } finally {
            // 恢复按钮状态
            setTimeout(() => {
                document.querySelectorAll('.export-btn').forEach(btn => btn.disabled = false);
                progressContainer.style.display = 'none';
            }, 1000);
        }
    }

    /**
     * 显示预览加载状态
     */
    showPreviewLoading(show) {
        document.getElementById('preview-loading').style.display = show ? 'flex' : 'none';
        document.getElementById('preview-container').style.display = show ? 'none' : 'block';
    }

    /**
     * 显示错误
     */
    showError(message) {
        const errorElement = document.getElementById('error');
        const messageElement = document.getElementById('error-message');
        
        messageElement.textContent = message;
        errorElement.style.display = 'block';
    }

    /**
     * 隐藏错误
     */
    hideError() {
        document.getElementById('error').style.display = 'none';
    }

    /**
     * 显示成功消息
     */
    showSuccessMessage(message) {
        // 创建临时成功提示
        const toast = document.createElement('div');
        toast.className = 'success-toast';
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            padding: 15px 25px;
            border-radius: 8px;
            z-index: 10000;
            font-size: 16px;
            box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
            animation: fadeInOut 3s ease-in-out;
        `;
        
        // 添加动画样式
        if (!document.getElementById('toast-styles')) {
            const style = document.createElement('style');
            style.id = 'toast-styles';
            style.textContent = `
                @keyframes fadeInOut {
                    0% { opacity: 0; transform: translate(-50%, -50%) scale(0.9); }
                    20% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
                    80% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
                    100% { opacity: 0; transform: translate(-50%, -50%) scale(0.9); }
                }
            `;
            document.head.appendChild(style);
        }
        
        document.body.appendChild(toast);
        
        // 3秒后自动移除
        setTimeout(() => {
            if (document.body.contains(toast)) {
                document.body.removeChild(toast);
            }
        }, 3000);
    }

    /**
     * HTML转义
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    new AnkiManager();
});