#!/bin/bash

set -e

echo "========================================"
echo "      ATC Monitor 云端部署脚本"
echo "========================================"
echo ""

LOG_FILE="deploy_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

function info() {
    echo -e "\033[1;34m[$(date +%H:%M:%S)] $1\033[0m"
}

function success() {
    echo -e "\033[1;32m[$(date +%H:%M:%S)] ✅ $1\033[0m"
}

function error() {
    echo -e "\033[1;31m[$(date +%H:%M:%S)] ❌ $1\033[0m"
    exit 1
}

info "阶段1: 环境准备"

info "更新系统..."
sudo apt-get update -y && sudo apt-get upgrade -y

info "安装依赖..."
sudo apt-get install -y docker docker-compose git python3 python3-pip

info "启动Docker服务..."
sudo systemctl enable docker
sudo systemctl start docker

success "环境准备完成"

info "阶段2: 代码部署"

info "创建项目目录..."
sudo mkdir -p /opt/atc_monitor
sudo chown $USER:$USER /opt/atc_monitor

info "克隆代码..."
cd /opt/atc_monitor
git clone . /opt/atc_monitor

info "创建环境配置文件..."
cat > .env << EOF
DB_NAME=atc_monitor
DB_USER=atc_user
DB_PASSWORD=$(openssl rand -hex 16)
DB_ROOT_PASSWORD=$(openssl rand -hex 16)
REDIS_HOST=redis
REDIS_PORT=6379
ORION_HOST=orion
ORION_PORT=1026
NEO4J_USER=neo4j
NEO4J_PASSWORD=$(openssl rand -hex 16)
EOF

success "代码部署完成"

info "阶段3: Docker构建与启动"

info "构建应用镜像..."
cd ACT
docker-compose build --no-cache

info "启动服务..."
docker-compose up -d

info "等待服务启动..."
sleep 60

info "检查容器状态..."
docker-compose ps

success "Docker服务启动完成"

info "阶段4: 数据库初始化"

info "执行数据库迁移..."
docker-compose exec app python manage.py makemigrations
docker-compose exec app python manage.py migrate

info "创建超级用户..."
docker-compose exec app python manage.py createsuperuser --noinput --username admin --email admin@example.com || true

success "数据库初始化完成"

info "阶段5: 健康检查"

info "检查应用健康状态..."
if curl -f http://localhost:8000/api/health/; then
    success "应用健康检查通过"
else
    error "应用健康检查失败"
fi

info "检查Orion-LD..."
if curl -f http://localhost:1026/version; then
    success "Orion-LD检查通过"
else
    error "Orion-LD检查失败"
fi

info "检查Redis..."
if docker-compose exec redis redis-cli ping | grep -q "PONG"; then
    success "Redis检查通过"
else
    error "Redis检查失败"
fi

success "所有健康检查通过"

echo ""
echo "========================================"
echo "         部署完成！"
echo "========================================"
echo ""
echo "访问地址:"
echo "  - 应用: http://$(hostname -I | awk '{print $1}'):8000"
echo "  - Orion-LD: http://$(hostname -I | awk '{print $1}'):1026"
echo "  - Neo4j: http://$(hostname -I | awk '{print $1}'):7474"
echo "  - EMQX: http://$(hostname -I | awk '{print $1}'):18083"
echo ""
echo "日志文件: $LOG_FILE"