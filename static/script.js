/**
 * TOEFL单词学习系统 - Web查看器JavaScript
 */

class TOEFLViewer {
    constructor() {
        this.currentPage = 1;
        this.totalPages = 1;
        this.translationVisible = false;
        
        this.init();
    }

    /**
     * 初始化应用
     */
    init() {
        this.bindEvents();
        this.loadStats();
        this.loadPage(1);
    }

    /**
     * 绑定事件
     */
    bindEvents() {
        // 翻译切换按钮
        document.getElementById('toggle-translation').addEventListener('click', () => {
            this.toggleTranslation();
        });

        // 生成新短文按钮
        document.getElementById('generate-btn').addEventListener('click', () => {
            this.generateNewEssay();
        });

        // 分页按钮
        document.getElementById('prev-btn').addEventListener('click', () => {
            if (this.currentPage > 1) {
                this.loadPage(this.currentPage - 1);
            }
        });

        document.getElementById('next-btn').addEventListener('click', () => {
            if (this.currentPage < this.totalPages) {
                this.loadPage(this.currentPage + 1);
            }
        });

        // 重试按钮
        document.getElementById('retry-btn').addEventListener('click', () => {
            this.loadPage(this.currentPage);
        });

        // 键盘导航
        document.addEventListener('keydown', (e) => {
            switch(e.key) {
                case 'ArrowLeft':
                    if (this.currentPage > 1) {
                        this.loadPage(this.currentPage - 1);
                    }
                    break;
                case 'ArrowRight':
                    if (this.currentPage < this.totalPages) {
                        this.loadPage(this.currentPage + 1);
                    }
                    break;
                case ' ':
                    e.preventDefault();
                    this.toggleTranslation();
                    break;
            }
        });
    }

    /**
     * 加载统计信息
     */
    async loadStats() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            
            if (stats.error) {
                console.error('加载统计失败:', stats.error);
                return;
            }

            const statsElement = document.getElementById('stats');
            statsElement.innerHTML = `
                总单词: ${stats.total_words} | 
                已学习: ${stats.learned_words} | 
                未学习: ${stats.unused_words} | 
                短文总数: ${stats.total_essays}
            `;
        } catch (error) {
            console.error('加载统计失败:', error);
        }
    }

    /**
     * 加载指定页面数据
     */
    async loadPage(page) {
        this.showLoading(true);
        this.hideError();

        try {
            const response = await fetch(`/api/essays?page=${page}`);
            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            this.renderData(data);
            this.updatePagination(data.pagination);
            this.currentPage = page;

            this.showLoading(false);
            this.showContent(true);

        } catch (error) {
            console.error('加载数据失败:', error);
            this.showError(error.message);
            this.showLoading(false);
        }
    }

    /**
     * 渲染数据
     */
    renderData(data) {
        if (!data.essays || data.essays.length === 0) {
            this.showError('没有找到数据');
            return;
        }

        const essay = data.essays[0]; // 每页只显示一个短文
        
        // 渲染单词
        this.renderWords(essay.word_details || []);
        
        // 渲染短文
        this.renderEssay(essay);
    }

    /**
     * 渲染单词列表
     */
    renderWords(words) {
        const wordsContainer = document.getElementById('words-list');
        
        if (words.length === 0) {
            wordsContainer.innerHTML = '<p>没有找到相关单词信息</p>';
            return;
        }

        wordsContainer.innerHTML = words.map(word => {
            const learnContent = word.learn_content || {};
            const phonetic = this.formatPhonetic(learnContent.phonetic);
            const translations = learnContent.translations || [];
            const partOfSpeech = learnContent.part_of_speech || [];
            const examples = learnContent.examples || [];
            const commonPhrases = learnContent.common_phrases || [];
            const etymology = learnContent.etymology || {};

            return `
                <div class="word-card">
                    <div class="word-header">
                        <span class="word-text">${word.word}</span>
                        <div class="pronunciation-buttons">
                            ${phonetic ? `<span class="word-phonetic">${phonetic}</span>` : ''}
                            <button class="pronunciation-btn uk-btn" onclick="playPronunciation('${word.word}', 'uk')" title="英式发音">🇬🇧</button>
                            <button class="pronunciation-btn us-btn" onclick="playPronunciation('${word.word}', 'us')" title="美式发音">🇺🇸</button>
                        </div>
                    </div>
                    ${learnContent.pronunciation ? `
                        <div class="word-pronunciation">${learnContent.pronunciation}</div>
                    ` : ''}
                    <div class="word-info">
                        ${partOfSpeech.length > 0 ? `
                            <div class="word-pos">${partOfSpeech.join(', ')}</div>
                        ` : ''}
                        ${translations.length > 0 ? `
                            <div class="word-translations">${translations.join('；')}</div>
                        ` : ''}
                    </div>
                    ${commonPhrases.length > 0 ? `
                        <div class="word-phrases">
                            <div class="section-title">常用短语</div>
                            ${commonPhrases.map(phrase => `
                                <div class="word-phrase">
                                    <span class="phrase-text">${phrase.phrase || ''}</span>
                                    <span class="phrase-translation">${phrase.translation || ''}</span>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                    ${etymology.root || etymology.analysis ? `
                        <div class="word-etymology">
                            <div class="section-title">词根词缀</div>
                            ${etymology.root ? `<div class="etymology-root">词根：${etymology.root}</div>` : ''}
                            ${etymology.analysis ? `<div class="etymology-analysis">${etymology.analysis}</div>` : ''}
                        </div>
                    ` : ''}
                    ${examples.length > 0 ? `
                        <div class="word-examples">
                            <div class="section-title">例句</div>
                            ${examples.slice(0, 2).map(example => `
                                <div class="word-example">
                                    <div class="example-sentence">${example.sentence || ''}</div>
                                    <div class="word-example-translation">${example.translation || ''}</div>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            `;
        }).join('');
    }

    /**
     * 渲染短文
     */
    renderEssay(essay) {
        const essayContent = essay.content || {};
        
        // 标题
        const titleElement = document.getElementById('essay-title');
        titleElement.textContent = essayContent.title || '短文';

        // 英文内容
        const englishElement = document.getElementById('essay-english-content');
        englishElement.textContent = essayContent.english_content || '暂无英文内容';

        // 中文翻译
        const chineseElement = document.getElementById('essay-chinese-content');
        chineseElement.textContent = essayContent.chinese_translation || '暂无中文翻译';

        // 重置翻译状态
        this.translationVisible = false;
        this.updateTranslationButton();
    }

    /**
     * 格式化音标
     */
    formatPhonetic(phonetic) {
        if (!phonetic) return '';
        
        if (typeof phonetic === 'string') {
            return phonetic;
        }
        
        if (typeof phonetic === 'object') {
            const parts = [];
            if (phonetic.UK) parts.push(`英 ${phonetic.UK}`);
            if (phonetic.US) parts.push(`美 ${phonetic.US}`);
            return parts.join(' ');
        }
        
        return '';
    }

    /**
     * 切换翻译显示状态
     */
    toggleTranslation() {
        this.translationVisible = !this.translationVisible;
        
        const translationElement = document.getElementById('essay-chinese-content');
        if (this.translationVisible) {
            translationElement.classList.remove('translation-hidden');
        } else {
            translationElement.classList.add('translation-hidden');
        }

        this.updateTranslationButton();
    }

    /**
     * 更新翻译按钮文本
     */
    updateTranslationButton() {
        const button = document.getElementById('toggle-translation');
        button.textContent = this.translationVisible ? '隐藏' : '显示';
    }

    /**
     * 更新分页信息
     */
    updatePagination(pagination) {
        this.totalPages = pagination.total_pages;
        
        // 更新页码信息
        const pageInfo = document.getElementById('page-info');
        pageInfo.textContent = `第 ${pagination.current_page} 页，共 ${pagination.total_pages} 页`;

        // 更新按钮状态
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');
        
        prevBtn.disabled = !pagination.has_prev;
        nextBtn.disabled = !pagination.has_next;

        // 显示分页控件
        document.getElementById('pagination').style.display = pagination.total_pages > 1 ? 'flex' : 'none';
    }

    /**
     * 显示/隐藏加载状态
     */
    showLoading(show) {
        document.getElementById('loading').style.display = show ? 'flex' : 'none';
    }

    /**
     * 显示/隐藏内容
     */
    showContent(show) {
        document.getElementById('content').style.display = show ? 'block' : 'none';
    }

    /**
     * 显示错误
     */
    showError(message) {
        const errorElement = document.getElementById('error');
        const messageElement = document.getElementById('error-message');
        
        messageElement.textContent = message;
        errorElement.style.display = 'block';
        
        this.showContent(false);
    }

    /**
     * 隐藏错误
     */
    hideError() {
        document.getElementById('error').style.display = 'none';
    }

    /**
     * 生成新短文
     */
    async generateNewEssay() {
        const button = document.getElementById('generate-btn');
        const icon = document.getElementById('generate-icon');
        const text = document.getElementById('generate-text');
        const progressContainer = document.getElementById('progress-container');
        const progressFill = document.getElementById('progress-fill');
        const progressStatus = document.getElementById('progress-status');

        // 禁用按钮并显示进度
        button.disabled = true;
        icon.textContent = '⏳';
        text.textContent = '生成中...';
        progressContainer.style.display = 'flex';
        progressFill.style.width = '0%';
        progressStatus.textContent = '开始生成...';

        try {
            // 模拟进度更新
            const updateProgress = (progress, status) => {
                progressFill.style.width = progress + '%';
                progressStatus.textContent = status;
            };

            updateProgress(25, '选择单词中...');
            await new Promise(resolve => setTimeout(resolve, 500));

            updateProgress(50, '生成学习内容...');
            await new Promise(resolve => setTimeout(resolve, 500));

            updateProgress(75, '创建短文...');

            // 创建带超时的fetch请求
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 300000); // 5分钟超时

            let result;
            try {
                // 发送生成请求
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        word_count: 10,
                        essay_type: 'story'
                    }),
                    signal: controller.signal
                });

                clearTimeout(timeoutId);

                // 检查响应状态和内容类型
                if (!response.ok) {
                    const errorText = await response.text();
                    throw new Error(`服务器错误 ${response.status}: ${errorText}`);
                }

                const contentType = response.headers.get('content-type');
                if (!contentType || !contentType.includes('application/json')) {
                    const errorText = await response.text();
                    throw new Error(`服务器返回非JSON响应，可能是请求超时或服务器错误`);
                }

                result = await response.json();
            } catch (error) {
                clearTimeout(timeoutId);
                if (error.name === 'AbortError') {
                    throw new Error('请求超时（5分钟），请检查网络连接或稍后再试');
                }
                throw error;
            }

            updateProgress(100, '生成完成！');
            await new Promise(resolve => setTimeout(resolve, 500));

            if (result.success) {
                // 重新加载统计信息
                this.loadStats();
                
                // 跳到第一页查看新生成的内容
                this.loadPage(1);
                
                // 显示成功消息
                this.showSuccessMessage(result.message);
            } else {
                throw new Error(result.error || '生成失败');
            }

        } catch (error) {
            console.error('生成新短文失败:', error);
            this.showError(`生成失败: ${error.message}`);
        } finally {
            // 恢复按钮状态
            setTimeout(() => {
                button.disabled = false;
                icon.textContent = '📚';
                text.textContent = '再来一组';
                progressContainer.style.display = 'none';
            }, 1000);
        }
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
        `;
        
        document.body.appendChild(toast);
        
        // 3秒后自动移除
        setTimeout(() => {
            if (document.body.contains(toast)) {
                document.body.removeChild(toast);
            }
        }, 3000);
    }
}

/**
 * 播放单词发音
 * @param {string} word - 单词
 * @param {string} accent - 口音类型 (uk/us)
 */
function playPronunciation(word, accent) {
    try {
        const audio = new Audio();
        // 使用有道词典API
        if (accent === 'uk') {
            audio.src = `https://dict.youdao.com/dictvoice?audio=${encodeURIComponent(word)}&type=1`;
        } else {
            audio.src = `https://dict.youdao.com/dictvoice?audio=${encodeURIComponent(word)}&type=0`;
        }
        
        audio.play().catch(error => {
            console.error('发音播放失败:', error);
            // 如果有道API失败，可以尝试其他发音源
            playFallbackPronunciation(word, accent);
        });
    } catch (error) {
        console.error('发音初始化失败:', error);
    }
}

/**
 * 备用发音播放（当有道API失败时使用）
 * @param {string} word - 单词
 * @param {string} accent - 口音类型
 */
function playFallbackPronunciation(word, accent) {
    try {
        const audio = new Audio();
        // 使用其他发音API作为备用
        audio.src = `https://ssl.gstatic.com/dictionary/static/sounds/oxford/${word}--_${accent === 'uk' ? 'gb' : 'us'}_1.mp3`;
        
        audio.play().catch(error => {
            console.error('备用发音也播放失败:', error);
            // 可以显示一个提示信息
            showPronunciationError(word);
        });
    } catch (error) {
        console.error('备用发音初始化失败:', error);
    }
}

/**
 * 显示发音错误提示
 * @param {string} word - 单词
 */
function showPronunciationError(word) {
    // 创建一个临时提示
    const toast = document.createElement('div');
    toast.className = 'pronunciation-toast';
    toast.textContent = `"${word}" 发音暂时无法播放`;
    toast.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(0,0,0,0.8);
        color: white;
        padding: 10px 20px;
        border-radius: 4px;
        z-index: 10000;
        font-size: 14px;
    `;
    
    document.body.appendChild(toast);
    
    // 3秒后自动移除
    setTimeout(() => {
        if (document.body.contains(toast)) {
            document.body.removeChild(toast);
        }
    }, 3000);
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new TOEFLViewer();
});