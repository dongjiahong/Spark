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

            return `
                <div class="word-card">
                    <div class="word-header">
                        <span class="word-text">${word.word}</span>
                        ${phonetic ? `<span class="word-phonetic">${phonetic}</span>` : ''}
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
                    ${examples.length > 0 ? `
                        <div class="word-examples">
                            ${examples.slice(0, 2).map(example => `
                                <div class="word-example">
                                    <div>${example.sentence || ''}</div>
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
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new TOEFLViewer();
});