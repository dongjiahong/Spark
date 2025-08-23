# TOEFL单词学习系统

这是一个完整的TOEFL单词学习系统，集成了AI大模型、单词学习管理和Anki卡片导出功能。

## 功能特点

### 🤖 AI大模型交互
- 为单词生成详细学习信息（音标、发音分割、词性、翻译、短语、词根词缀、例句）
- 根据选定单词生成记忆友好的短文（童话、故事、新闻、预言）
- 支持OpenAI兼容的API

### 📚 智能业务逻辑
- 优先选择未学习的单词（count=0）
- 自动更新单词学习计数
- 保存学习内容到数据库
- 管理短文和单词关联

### 📱 Anki卡片导出
- **APKG格式导出**（推荐）：一键生成完整的Anki包文件
- **单词卡片**：3种类型
  - 单词识别：看单词想意思
  - 单词拼写：看意思拼单词
  - 反向记忆：看翻译想单词
- **短文卡片**：2种类型
  - 翻译练习：看短文想翻译
  - 反向翻译：看翻译想短文
- **发音功能**：点击音标旁的🇺🇸🇬🇧图标播放美式/英式发音
- 美观的CSS样式和交互设计，内置JavaScript发音功能

## 安装和配置

### 1. 安装依赖
```bash
conda activate python3  # 或你的Python环境
pip install -r requirements.txt
```

依赖包含：
- `python-dotenv`: 环境变量管理
- `requests`: HTTP请求
- `genanki`: Anki包生成

### 2. 配置环境变量
编辑 `.env` 文件：
```env
OPENAI_URL=https://api.openai.com/v1/chat/completions
OPENAI_KEY=your_api_key_here
MODEL=gpt-3.5-turbo
```

### 3. 准备单词数据
确保有 `toefl_words.txt` 文件，每行一个单词。

## 使用方法

### 交互模式（推荐）
```bash
python main.py
```

### 命令行模式
```bash
# 创建学习会话（5个单词，故事类型）
python main.py --mode learn --words 5 --type story

# 导出到Anki（APKG格式）
python main.py --mode export --output anki_export

# 显示统计信息
python main.py --mode stats
```

### 单独使用各模块
```bash
# 测试AI服务
python ai_service.py

# 运行业务逻辑
python business_logic.py

# 导出Anki卡片（APKG格式）
python anki_export.py
```

## 项目结构

```
├── main.py              # 主入口文件
├── ai_service.py        # AI大模型交互
├── business_logic.py    # 业务逻辑管理
├── anki_export.py       # Anki卡片导出（APKG格式）
├── import_words.py      # 单词导入（原始功能）
├── requirements.txt     # Python依赖
├── .env                 # 环境变量配置
├── toefl_words.txt      # 单词文件
├── toefl_words.db       # SQLite数据库
└── anki_export/         # Anki导出目录
    ├── toefl_words_*.apkg    # 单词卡片包
    └── toefl_essays_*.apkg   # 短文卡片包
```

## 数据库结构

### words表
- `id`: 主键
- `word`: 单词
- `count`: 学习次数
- `learn_content`: AI生成的学习内容(JSON格式)
- `created`: 创建时间
- `updated`: 更新时间

### essay表
- `id`: 主键
- `words`: 相关单词列表
- `content`: AI生成的短文内容(JSON格式)
- `created`: 创建时间
- `updated`: 更新时间

## Anki导入说明

### APKG格式（推荐）
1. 运行导出程序生成`.apkg`文件
2. 直接将`.apkg`文件拖拽到Anki中
3. 或者在Anki中选择"文件" > "导入"，选择`.apkg`文件
4. 无需其他配置，样式和发音功能已内置

### 发音功能使用
- 在单词卡片的音标旁点击🇺🇸图标播放美式发音
- 点击🇬🇧图标播放英式发音
- 发音数据来自有道词典API

### ~~CSV格式（已移除）~~
*注：为了更好的用户体验，已移除CSV格式，统一使用APKG格式*

## 短文类型说明

- `story`: 故事 - 生动有趣的叙事
- `fairy_tale`: 童话 - 富有想象力的童话故事
- `news`: 新闻 - 新闻报道格式
- `prophecy`: 预言 - 预言或预测性文本

## 技术特性

### 发音系统
- 基于有道词典API实现
- 支持美式发音（🇺🇸）和英式发音（🇬🇧）
- API地址：`http://dict.youdao.com/dictvoice?type={0|1}&audio={word}`
- 无需额外配置，即开即用

### Anki集成
- 使用`genanki`库生成标准APKG文件
- 内置CSS样式和JavaScript功能
- 支持响应式设计，适配手机和电脑
- 自动生成随机牌组ID，避免冲突

### 数据持久化
- SQLite数据库存储
- JSON格式保存AI生成的学习内容
- 支持增量学习和内容更新

## 注意事项

- 确保API配置正确
- 建议小批量测试后再大量处理
- 定期备份数据库文件
- 发音功能需要网络连接
- APKG文件可直接在Anki中使用，无需额外配置

## 更新日志

### v2.0.0 (2025-08-23)
- ✨ 新增APKG格式导出
- 🔊 集成有道词典发音功能
- 🎨 优化卡片样式设计
- 🗑️ 移除CSV导出格式
- 📱 支持响应式设计

### v1.0.0
- 基础单词学习系统
- AI内容生成
- CSV格式Anki导出
