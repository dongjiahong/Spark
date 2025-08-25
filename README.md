# TOEFL单词学习系统

TOEFL单词学习系统，集成AI大模型生成学习内容和Anki卡片导出，支持Web界面和命令行操作。

## 核心功能

- **AI内容生成**：自动生成音标、翻译、短语、词根词缀、例句和记忆短文
- **Web界面**：现代化的Web界面，支持单词浏览和一键生成新内容
- **Anki导出**：生成APKG文件，内置发音功能(🇺🇸🇬🇧)和美观样式
- **智能学习**：优先选择未学习单词，跟踪学习进度

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置API
编辑 `.env` 文件：
```env
OPENAI_URL=https://api.openai.com/v1/chat/completions
OPENAI_KEY=your_api_key_here
MODEL=gpt-3.5-turbo
```

### 3. 准备单词
确保有 `toefl_words.txt` 文件，每行一个单词。

## 使用方法

### Web界面（推荐）
```bash
python web_viewer.py
```
访问 http://localhost:8080，支持：
- 浏览单词和短文
- 一键"再来一组"生成新内容
- 实时进度显示

### 命令行模式
```bash
# 交互模式
python main.py

# 生成学习会话
python main.py --mode learn --words 10 --type story

# 导出Anki包
python anki_export.py
```

## 文件说明

- `web_viewer.py` - Web界面服务器
- `main.py` - 命令行入口
- `ai_service.py` - AI模型接口
- `business_logic.py` - 业务逻辑
- `anki_export.py` - Anki导出
- `templates/` - Web模板
- `static/` - CSS/JS资源

## Anki使用

1. 运行 `python anki_export.py` 生成 `.apkg` 文件
2. 将文件导入Anki
3. 点击🇺🇸🇬🇧播放发音

## 短文类型

- `story` - 故事
- `fairy_tale` - 童话  
- `news` - 新闻
- `prophecy` - 预言
