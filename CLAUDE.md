# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个TOEFL单词学习系统，集成了AI大语言模型、单词学习管理和Anki卡片导出功能。系统使用Python开发，采用SQLite进行数据持久化。

## 核心架构

系统采用模块化架构，职责分离清晰：

- **main.py**: 主入口文件，提供CLI界面和交互模式
- **web_viewer.py**: Flask Web服务器，提供现代化的Web界面浏览单词和短文
- **ai_service.py**: AI模型集成（兼容OpenAI API），生成单词信息和短文
- **business_logic.py**: 核心业务逻辑，处理单词选择、学习进度和数据库管理
- **anki_export.py**: 生成Anki包文件(.apkg)，内嵌CSS样式和发音JavaScript功能
- **import_words.py**: 初始单词导入功能
- **templates/**: Web界面HTML模板
- **static/**: Web界面CSS和JavaScript资源

### 数据库结构

SQLite数据库 (`toefl_words.db`) 包含：
- **words表**: word（单词）, count（学习次数）, learn_content（JSON格式学习内容）, 时间戳
- **essay表**: words（相关单词列表）, content（JSON格式，包含标题、内容、翻译）, 时间戳

### AI集成

系统使用OpenAI兼容API生成：
- 单词学习信息（音标、发音分割、词性、翻译、短语、词根词缀、例句）
- 记忆友好的短文（童话、故事、新闻、预言），融入选定词汇

## 开发命令

### 环境配置
```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑.env文件，设置API凭据：
# OPENAI_URL=https://api.openai.com/v1/chat/completions
# OPENAI_KEY=your_api_key_here
# MODEL=gpt-3.5-turbo
```

### 运行应用

#### Web界面模式（推荐）
```bash
python web_viewer.py
```
访问 http://localhost:8080 使用现代化Web界面：
- 浏览单词和短文内容
- 一键"再来一组"生成新学习内容
- 实时进度显示和统计信息

#### CLI交互模式
```bash
python main.py
```

#### 命令行模式
```bash
# 创建学习会话（5个单词，故事类型）
python main.py --mode learn --words 5 --type story

# 导出到Anki（APKG格式）
python main.py --mode export --output anki_export

# 显示统计信息
python main.py --mode stats

# 直接导出Anki包（独立命令）
python anki_export.py
```

#### 单独模块测试
```bash
# 测试AI服务
python ai_service.py

# 运行业务逻辑
python business_logic.py

# 导入初始单词到数据库
python import_words.py
```

## 核心功能

### AI生成内容
- 单词信息包含音标、发音分割、词性、翻译、短语、词根词缀和例句
- 短文生成4种类型：story（故事）、fairy_tale（童话）、news（新闻）、prophecy（预言）
- 所有内容以JSON格式存储在数据库中

### Anki集成
- 生成完整的.apkg文件，内嵌样式和JavaScript功能
- 单词卡片：识别（单词→意思）、拼写（意思→单词）、反向（翻译→单词）
- 短文卡片：翻译练习（短文→翻译）、反向翻译（翻译→短文）
- 发音功能使用有道词典API（🇺🇸/🇬🇧图标）

### 业务逻辑
- 优先选择未学习的单词（count=0）
- 跟踪学习频率并自动更新
- 管理单词-短文关联
- 提供详细统计信息

## 文件依赖

- **toefl_words.txt**: 源单词列表（每行一个单词）
- **toefl_words.db**: SQLite数据库（自动创建）
- **.env**: 环境配置文件（必需，从.env.example复制）
- **anki_export/**: 生成的.apkg文件目录
- **requirements.txt**: Python依赖列表

## 数据流程

1. 从`toefl_words.txt`导入单词到数据库
2. 业务逻辑选择未学习单词进行处理
3. AI服务生成详细学习内容和短文
4. 内容以JSON格式存储在数据库中
5. Anki导出器创建内嵌样式和发音功能的.apkg文件

## 开发注意事项

### 依赖库
系统主要依赖：
- `python-dotenv`: 环境变量管理
- `requests`: HTTP请求处理
- `genanki`: Anki包生成
- `Flask`: Web界面服务

### API配置
- 所有AI调用需要配置.env文件中的API凭据
- 支持OpenAI兼容的API端点
- 系统会自动重试失败的API调用

### 数据库操作
- 使用SQLite作为本地数据库
- 所有数据库操作使用row_factory以支持字典式访问
- 数据库连接在每个操作后自动关闭

## 重要说明

- 系统需要网络连接用于AI API调用和发音功能
- 所有生成的内容都会缓存在数据库中，避免重复API调用
- 发音系统使用有道词典API端点
- .apkg文件是自包含的，内嵌CSS/JS，可直接导入Anki使用
- Web服务器默认运行在 localhost:8080