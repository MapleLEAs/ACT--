#!/bin/bash

set -e

echo "========================================"
echo "      ATC Monitor 重新部署脚本"
echo "========================================"
echo ""

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

function confirm() {
    read -p "$1 (y/N): " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

DATA_RETENTION="yes"

if confirm "是否保留现有数据库数据？"; then
    DATA_RETENTION="yes"
else
    DATA_RETENTION="no"
fi

if [[ "$DATA_RETENTION" == "no" ]]; then
    info "数据清理模式：将删除所有持久化数据"
else
    info "数据保留模式：仅更新应用代码和配置"
fi

info "阶段1: 停止现有服务"
info "停止所有容器..."
docker-compose down

if [[ "$DATA_RETENTION" == "no" ]]; then
    info "清理数据卷..."
    docker-compose down -v
    success "数据卷已清理"
else
    success "数据卷已保留"
fi

info "阶段2: 更新代码"
info "拉取最新代码..."
git pull origin main

info "阶段3: 重新构建镜像"
info "构建应用镜像..."
docker-compose build --no-cache

info "阶段4: 启动服务"
info "启动所有容器..."
docker-compose up -d

info "等待服务启动..."
sleep 60

info "检查容器状态..."
docker-compose ps

success "服务启动完成"

info "阶段5: 数据库迁移"
info "执行数据库迁移..."
docker-compose exec app python manage.py makemigrations
docker-compose exec app python manage.py migrate

success "数据库迁移完成"

info "阶段6: 前端静态资源更新"
info "收集静态文件..."
docker-compose exec app python manage.py collectstatic --noinput

success "静态资源更新完成"

info "阶段7: 健康检查"

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
echo "         重新部署完成！"
echo "========================================"
echo ""
echo "访问地址:"
echo "  - 应用: http://$(hostname -I | awk '{print $1}'):8000"
echo "  - Orion-LD: http://$(hostname -I | awk '{print $1}'):1026"
echo "  - Neo4j: http://$(hostname -I | awk '{print $1}'):7474"
echo "  - EMQX: http://$(hostname -I | awk '{print $1}'):18083"
echo ""
echo "部署模式: 数据${DATA_RETENTION}"