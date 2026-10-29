# ATC 监控系统前端启动脚本
# 一键启动前端服务

Write-Host "==============================" 
Write-Host "启动 ATC 监控系统（前端服务）" 
Write-Host "==============================" 

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

# 启动前端服务
Write-Host "启动前端服务..."
$frontendPath = Join-Path $scriptDir "项目后端框架\frontend"
Set-Location $frontendPath
Write-Host "正在启动前端服务..."
npm run dev

Write-Host "=============================="
Write-Host "前端服务已停止"
Write-Host "=============================="
Read-Host "按任意键退出..."
