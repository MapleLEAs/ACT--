# ATC 监控系统启动脚本
# 一键启动前后端服务

Write-Host "==============================" 
Write-Host "启动 ATC 监控系统（前后端）" 
Write-Host "==============================" 

# 检查 Python 是否安装
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python 版本: $pythonVersion"
}
catch {
    Write-Host "错误：未找到 Python，请先安装 Python 3.9+"
    Read-Host "按任意键退出..."
    exit 1
}

# 检查 Node.js 是否安装
try {
    $nodeVersion = node --version 2>&1
    Write-Host "Node.js 版本: $nodeVersion"
}
catch {
    Write-Host "错误：未找到 Node.js，请先安装 Node.js 16+"
    Read-Host "按任意键退出..."
    exit 1
}

# 获取脚本所在目录
$scriptDir = Split-Path $MyInvocation.MyCommand.Path -Parent

# 后端服务启动命令
$backendCommand = "cd `"$scriptDir\项目后端框架`"; Write-Host '正在启动后端服务...'; python manage.py runserver"

# 前端服务启动命令
$frontendCommand = "cd `"$scriptDir\项目后端框架\frontend`"; Write-Host '正在启动前端服务...'; npm run dev"

# 启动后端服务
Write-Host "启动后端服务..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand

# 启动前端服务
Write-Host "启动前端服务..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand

Write-Host "=============================="
Write-Host "启动完成！"
Write-Host "=============================="
Write-Host "后端服务地址：http://127.0.0.1:8000"
Write-Host "Admin 后台地址：http://127.0.0.1:8000/admin"
Write-Host "前端服务地址：http://localhost:5173"
Write-Host "=============================="
Write-Host "按任意键退出..."

Read-Host