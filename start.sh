#!/bin/bash
# TOEFL单词学习系统快速启动脚本

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 脚本目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# 显示横幅
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  TOEFL单词学习系统启动脚本${NC}"
echo -e "${BLUE}================================${NC}"

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python3 未安装${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python3 已安装: $(python3 --version)${NC}"

# 检查虚拟环境
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo -e "${GREEN}✓ 虚拟环境已激活: $VIRTUAL_ENV${NC}"
else
    echo -e "${YELLOW}⚠ 建议使用虚拟环境${NC}"
fi

# 检查依赖
echo -e "${BLUE}检查依赖...${NC}"
if ! python3 -c "import flask, dotenv, requests, genanki" 2>/dev/null; then
    echo -e "${YELLOW}⚠ 依赖未完全安装，正在安装...${NC}"
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ 依赖安装失败${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓ 依赖检查通过${NC}"

# 检查环境配置
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ 未找到.env文件${NC}"
    if [ -f ".env.example" ]; then
        echo -e "${BLUE}发现.env.example，是否复制为.env？[y/N]${NC}"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            cp .env.example .env
            echo -e "${GREEN}✓ 已创建.env文件，请编辑配置API凭据${NC}"
        fi
    else
        echo -e "${RED}✗ 请创建.env文件并配置API凭据${NC}"
        exit 1
    fi
fi

# 检查数据库
if [ ! -f "toefl_words.db" ]; then
    echo -e "${YELLOW}⚠ 数据库文件不存在${NC}"
    if [ -f "toefl_words.txt" ]; then
        echo -e "${BLUE}发现单词文件，是否初始化数据库？[y/N]${NC}"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            python3 import_words.py
            echo -e "${GREEN}✓ 数据库已初始化${NC}"
        fi
    fi
fi

# 选择启动模式
echo ""
echo -e "${BLUE}请选择启动模式:${NC}"
echo -e "${GREEN}1)${NC} 开发模式 (Flask开发服务器)"
echo -e "${GREEN}2)${NC} 生产模式 (Gunicorn, 默认4进程)"
echo -e "${GREEN}3)${NC} 生产模式 (Gunicorn, 8进程)"
echo -e "${GREEN}4)${NC} 显示系统状态"
echo -e "${GREEN}q)${NC} 退出"

read -p "选择 [1]: " choice
choice=${choice:-1}

case $choice in
    1)
        echo -e "${GREEN}🚀 启动开发模式...${NC}"
        python3 start.py --dev
        ;;
    2)
        echo -e "${GREEN}🚀 启动生产模式 (4进程)...${NC}"
        python3 start.py --prod --workers 4
        ;;
    3)
        echo -e "${GREEN}🚀 启动生产模式 (8进程)...${NC}"
        python3 start.py --prod --workers 8
        ;;
    4)
        python3 start.py --status
        ;;
    q|Q)
        echo -e "${BLUE}退出${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}无效选择，使用默认开发模式${NC}"
        python3 start.py --dev
        ;;
esac