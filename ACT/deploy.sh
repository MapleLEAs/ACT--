#!/bin/bash
set -e

echo "=========================================="
echo "ACT 监控系统部署脚本"
echo "=========================================="

ACT_DIR="/opt/ACT"

echo "[1/6] 更新系统依赖..."
apt-get update && apt-get install -y \
    docker.io \
    docker-compose \
    python3-pip \
    nginx \
    gcc \
    g++ \
    make \
    git \
    npm

echo "[2/6] 创建项目目录..."
mkdir -p $ACT_DIR

echo "[3/6] 解压部署包..."
cd /opt
unzip -o ACT-deploy-*.zip -d $ACT_DIR

echo "[4/6] 进入项目目录..."
cd $ACT_DIR

echo "[5/6] 构建前端..."
cd frontend
npm install
npm run build
cd ..

echo "[6/6] 启动 Docker Compose 服务..."
docker-compose -f docker-compose.prod.yml up -d --build

echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  Web界面: http://<服务器IP>"
echo "  Django管理后台: http://<服务器IP>/admin"
echo "  Neo4j Web界面: http://<服务器IP>:7474"
echo "  EMQX管理后台: http://<服务器IP>:18083"
echo ""
echo "超级管理员账号:"
echo "  用户名: admin"
echo "  密码: admin123"
echo ""
echo "服务状态查看:"
echo "  docker-compose -f docker-compose.prod.yml ps"
echo "  docker-compose -f docker-compose.prod.yml logs app"