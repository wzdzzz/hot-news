#!/bin/bash
# 腾讯云一键部署脚本 - 热点新闻聚合系统
# 用法: sudo bash deploy.sh
# 前提: 代码已克隆到 /opt/hot-news
# 注意: 与 fabric-lead-finder (80端口) 共存，本项目使用 7777 端口

set -e

APP_DIR="/opt/hot-news"

echo "===== 热点新闻聚合系统 - 部署开始 ====="

# ---- 1. 系统依赖 ----
echo "[1/8] 安装系统依赖..."
apt-get update -qq
apt-get install -y python3 python3-venv python3-pip nginx git curl
# 安装 Node.js 20.x（用于构建前端）
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi
echo "  -> 系统依赖安装完成 (Node $(node --version), Python $(python3 --version))"

# ---- 2. 确认代码 ----
echo "[2/8] 检查代码..."
if [ ! -f "$APP_DIR/requirements.txt" ]; then
    echo "  错误: 代码未部署到 $APP_DIR"
    echo "  请先执行: git clone <仓库地址> $APP_DIR"
    exit 1
fi
if [ ! -f "$APP_DIR/config.yaml" ]; then
    echo "  错误: 缺少 config.yaml 配置文件"
    exit 1
fi
cd "$APP_DIR"
echo "  -> 代码就绪"

# ---- 3. 创建必要目录 ----
echo "[3/8] 创建数据和日志目录..."
mkdir -p "$APP_DIR/data"
mkdir -p "$APP_DIR/logs"
echo "  -> 目录创建完成"

# ---- 4. Python 虚拟环境 ----
echo "[4/8] 创建 Python 虚拟环境..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "  -> Python 依赖安装完成"

# ---- 5. 构建前端 ----
echo "[5/8] 构建前端..."
cd "$APP_DIR/frontend"
npm install --production=false -q
npx tsc -b && npx vite build
cd "$APP_DIR"
echo "  -> 前端构建完成"

# ---- 6. systemd 服务 ----
echo "[6/8] 配置 systemd 服务..."
cat > /etc/systemd/system/hot-news.service <<'SERVICEEOF'
[Unit]
Description=Hot News Scraper - 热点新闻聚合系统
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/hot-news
ExecStart=/opt/hot-news/venv/bin/python /opt/hot-news/run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICEEOF

systemctl daemon-reload
systemctl enable hot-news
echo "  -> systemd 服务已配置"

# ---- 7. Nginx 反向代理 (端口 7777) ----
echo "[7/8] 配置 Nginx (端口 7777)..."
cat > /etc/nginx/sites-available/hot-news <<'NGINXEOF'
server {
    listen 7777;
    server_name _;

    # 前端静态文件
    location / {
        root /opt/hot-news/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8111;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Swagger 文档代理
    location /docs {
        proxy_pass http://127.0.0.1:8111;
        proxy_set_header Host $host;
    }
    location /openapi.json {
        proxy_pass http://127.0.0.1:8111;
        proxy_set_header Host $host;
    }
}
NGINXEOF

ln -sf /etc/nginx/sites-available/hot-news /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t
echo "  -> Nginx 配置完成 (监听端口 7777)"

# ---- 8. 启动服务 ----
echo "[8/8] 启动服务..."
systemctl reload nginx
systemctl restart hot-news

# ---- 验证 ----
sleep 3
if systemctl is-active --quiet hot-news; then
    echo "  -> 服务运行正常"
else
    echo "  -> 服务启动失败，查看日志: journalctl -u hot-news -n 50"
    exit 1
fi

echo ""
echo "====================================="
echo "  部署完成！"
echo "  访问地址: http://$(curl -s ifconfig.me 2>/dev/null || echo '服务器IP'):7777"
echo "  API 文档: http://$(curl -s ifconfig.me 2>/dev/null || echo '服务器IP'):7777/docs"
echo ""
echo "  常用命令:"
echo "    查看日志: journalctl -u hot-news -f"
echo "    重启服务: systemctl restart hot-news"
echo "    服务状态: systemctl status hot-news"
echo "    应用日志: tail -f /opt/hot-news/logs/app.log"
echo ""
echo "  注意: 请确保腾讯云安全组已放行 7777 端口"
echo "====================================="
