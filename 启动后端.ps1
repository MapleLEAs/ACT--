# ATC 监控系统后端启动脚本
# 一键启动后端服务

Write-Host "==============================" 
Write-Host "启动 ATC 监控系统（后端服务）" 
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

# 获取脚本所在目录
$scriptDir = Split-Path $MyInvocation.MyCommand.Path -Parent

# 启动后端服务
Write-Host "启动后端服务..."
$backendPath = Join-Path $scriptDir "项目后端框架"
Set-Location $backendPath
Write-Host "正在启动后端服务..."
python manage.py runserver

Write-Host "=============================="
Write-Host "后端服务已停止"
Write-Host "=============================="
Read-Host "按任意键退出..."
