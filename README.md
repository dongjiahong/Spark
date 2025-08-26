# TOEFL单词学习系统

TOEFL单词学习系统，集成AI大模型生成学习内容和Anki卡片导出，支持现代化Web界面和命令行操作。

## 核心功能

- **AI内容生成**：自动生成音标、翻译、短语、词根词缀、例句和记忆短文
- **异步处理**：后台异步生成内容，前端实时显示进度，不再阻塞
- **Web界面**：现代化响应式界面，支持单词浏览和一键生成新内容
- **Anki导出**：生成APKG文件，内置发音功能(🇺🇸🇬🇧)和美观样式
- **智能学习**：优先选择未学习单词，跟踪学习进度
- **生产就绪**：支持Gunicorn生产部署，多进程处理

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

## 启动方法

### 🚀 快速启动（推荐）
```bash
./start.sh
```
交互式启动脚本，自动检查依赖并提供启动选项。

### 🔧 手动启动

#### Web界面 - 开发模式
```bash
python start.py
# 或
python start.py --dev
```

#### Web界面 - 生产模式
```bash
python start.py --prod --workers 4
```

#### 传统方式
```bash
# Web界面（Flask开发服务器）
python web_viewer.py

# 命令行交互模式
python main.py

# 直接生成学习会话
python main.py --mode learn --words 10 --type story
```

### 📊 系统状态检查
```bash
python start.py --status
```

## Web界面功能

访问 http://localhost:8080 体验：
- **浏览模式**：查看已生成的单词和短文内容
- **异步生成**：点击"再来一组"后台生成，前端显示实时进度
- **键盘导航**：左右箭头翻页，空格键显示/隐藏翻译
- **发音功能**：点击🇺🇸🇬🇧图标播放单词发音
- **Anki管理**：查看和导出Anki卡片预览

## 命令行模式
```bash
# 交互模式
python main.py

# 生成学习会话
python main.py --mode learn --words 10 --type story

# 导出Anki包
python anki_export.py
```

## 技术架构

### 后端异步处理
- **任务管理器**：`TaskManager` 类管理异步任务状态
- **后台线程**：生成任务在独立线程中执行，不阻塞Web请求
- **实时状态**：通过轮询API `/api/task/<task_id>` 获取进度
- **容错处理**：支持任务超时、重试和错误恢复

### 生产部署特性
- **Gunicorn**：多进程WSGI服务器，支持并发处理
- **长超时**：300秒超时设置，适合AI生成任务
- **健康检查**：自动重启异常进程
- **访问日志**：完整的请求和错误日志

## 文件结构

```
spark/
├── start.py              # 统一启动脚本
├── start.sh              # 交互式启动脚本
├── web_viewer.py         # Web界面服务器（异步任务支持）
├── main.py               # 命令行入口
├── ai_service.py         # AI模型接口
├── business_logic.py     # 业务逻辑
├── anki_export.py        # Anki导出功能
├── import_words.py       # 单词导入工具
├── requirements.txt      # 项目依赖（含Gunicorn）
├── .env                  # 环境配置文件
├── toefl_words.txt       # 源单词列表
├── toefl_words.db        # SQLite数据库
├── templates/            # Web模板文件
│   ├── index.html        # 主页面
│   └── anki_manager.html # Anki管理页面
├── static/               # 前端资源
│   ├── script.js         # JavaScript（异步轮询逻辑）
│   └── style.css         # 样式文件
└── anki_export/          # Anki包导出目录
```

## Anki使用

### 方式一：Web界面导出（推荐）
1. 访问 http://localhost:8080
2. 点击"Anki管理"按钮
3. 预览卡片内容，选择导出类型
4. 下载生成的 `.apkg` 文件

### 方式二：命令行导出
```bash
python anki_export.py
```

### 导入Anki
1. 将生成的 `.apkg` 文件导入Anki
2. 卡片包含美观样式和发音功能
3. 点击🇺🇸🇬🇧播放单词发音

## 短文类型

系统支持4种短文类型，AI会根据类型生成相应风格的内容：
- `story` - 故事类，适合记忆情节
- `fairy_tale` - 童话类，生动有趣
- `news` - 新闻类，贴近现实
- `prophecy` - 预言类，神秘风格

## 日志查看
```bash
# 查看详细错误信息
python start.py --prod 2>&1 | tee app.log
```

## 重置数据
```bash
# 删除数据库重新开始
rm toefl_words.db
python import_words.py
```
