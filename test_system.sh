#!/bin/bash

# CashUp 量化交易系统测试脚本
# 分阶段启动和测试系统

set -e  # 遇到错误立即退出

echo "🚀 开始测试 CashUp 量化交易系统"
echo "======================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker是否运行
check_docker() {
    log_info "检查 Docker 是否运行..."
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker 未运行，请启动 Docker Desktop"
        exit 1
    fi
    log_success "Docker 正在运行"
}

# 检查.env文件
check_env_file() {
    log_info "检查 .env 文件..."
    if [ ! -f ".env" ]; then
        log_error ".env 文件不存在，请创建该文件"
        exit 1
    fi
    log_success ".env 文件存在"
}

# 清理旧容器
cleanup() {
    log_info "清理旧容器..."
    docker-compose down --remove-orphans
    log_success "清理完成"
}

# 阶段1：启动基础设施服务
start_infrastructure() {
    log_info "阶段1：启动基础设施服务 (PostgreSQL, Redis, RabbitMQ)..."
    docker-compose up -d postgres redis rabbitmq
    
    log_info "等待基础设施服务启动..."
    sleep 10
    
    # 检查服务状态
    if docker-compose ps postgres | grep -q "Up"; then
        log_success "PostgreSQL 启动成功"
    else
        log_error "PostgreSQL 启动失败"
        return 1
    fi
    
    if docker-compose ps redis | grep -q "Up"; then
        log_success "Redis 启动成功"
    else
        log_error "Redis 启动失败"
        return 1
    fi
    
    if docker-compose ps rabbitmq | grep -q "Up"; then
        log_success "RabbitMQ 启动成功"
    else
        log_error "RabbitMQ 启动失败"
        return 1
    fi
}

# 阶段2：启动核心服务
start_core_services() {
    log_info "阶段2：启动核心服务..."
    docker-compose up -d user-service exchange-service
    
    log_info "等待核心服务启动..."
    sleep 15
    
    # 检查服务健康状态
    check_service_health "user-service" "8001"
    check_service_health "exchange-service" "8003"
}

# 阶段3：启动业务服务
start_business_services() {
    log_info "阶段3：启动业务服务..."
    docker-compose up -d trading-service market-service strategy-service order-service
    
    log_info "等待业务服务启动..."
    sleep 20
    
    # 检查服务健康状态
    check_service_health "trading-service" "8002"
    check_service_health "market-service" "8005"
    check_service_health "strategy-service" "8004"
    check_service_health "order-service" "8007"
}

# 阶段4：启动支持服务
start_support_services() {
    log_info "阶段4：启动支持服务..."
    docker-compose up -d notification-service config-service monitoring-service
    
    log_info "等待支持服务启动..."
    sleep 15
    
    # 检查服务健康状态
    check_service_health "notification-service" "8006"
    check_service_health "config-service" "8008"
    check_service_health "monitoring-service" "8009"
}

# 阶段5：启动前端服务
start_frontend() {
    log_info "阶段5：启动前端服务..."
    docker-compose up -d frontend
    
    log_info "等待前端服务启动..."
    sleep 10
    
    # 检查前端服务
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        log_success "前端服务启动成功: http://localhost:3000"
    else
        log_warning "前端服务可能需要更多时间启动"
    fi
}

# 检查服务健康状态
check_service_health() {
    local service_name=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    log_info "检查 $service_name 健康状态..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f http://localhost:$port/health > /dev/null 2>&1 || 
           curl -f http://localhost:$port/docs > /dev/null 2>&1 || 
           curl -f http://localhost:$port/ > /dev/null 2>&1; then
            log_success "$service_name 健康检查通过 (端口: $port)"
            return 0
        fi
        
        log_info "$service_name 健康检查失败，重试 $attempt/$max_attempts..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    log_warning "$service_name 健康检查超时，但服务可能仍在启动中"
    return 1
}

# 显示系统状态
show_system_status() {
    log_info "系统状态概览:"
    echo "======================================"
    docker-compose ps
    echo "======================================"
    
    log_info "服务访问地址:"
    echo "🌐 前端应用: http://localhost:3000"
    echo "👤 用户服务: http://localhost:8001/docs"
    echo "📈 交易服务: http://localhost:8002/docs"
    echo "🏦 交易所服务: http://localhost:8003/docs"
    echo "🤖 策略服务: http://localhost:8004/docs"
    echo "📊 行情服务: http://localhost:8005/docs"
    echo "📧 通知服务: http://localhost:8006/docs"
    echo "📋 订单服务: http://localhost:8007/docs"
    echo "⚙️  配置服务: http://localhost:8008/docs"
    echo "📈 监控服务: http://localhost:8009/docs"
    echo "🐰 RabbitMQ管理: http://localhost:15672 (cashup/cashup123)"
}

# 运行完整测试
run_full_test() {
    log_info "开始完整系统测试..."
    
    check_docker
    check_env_file
    cleanup
    
    start_infrastructure || { log_error "基础设施启动失败"; exit 1; }
    start_core_services || { log_error "核心服务启动失败"; exit 1; }
    start_business_services || { log_error "业务服务启动失败"; exit 1; }
    start_support_services || { log_error "支持服务启动失败"; exit 1; }
    start_frontend || { log_error "前端服务启动失败"; exit 1; }
    
    show_system_status
    
    log_success "🎉 CashUp 量化交易系统测试完成！"
    log_info "请访问 http://localhost:3000 查看前端应用"
}

# 快速启动（跳过健康检查）
quick_start() {
    log_info "快速启动所有服务..."
    check_docker
    check_env_file
    cleanup
    
    docker-compose up -d
    
    log_info "等待所有服务启动..."
    sleep 30
    
    show_system_status
    log_success "快速启动完成！"
}

# 主函数
main() {
    case "${1:-full}" in
        "full")
            run_full_test
            ;;
        "quick")
            quick_start
            ;;
        "cleanup")
            cleanup
            ;;
        "status")
            show_system_status
            ;;
        "help")
            echo "用法: $0 [full|quick|cleanup|status|help]"
            echo "  full    - 完整测试（默认）"
            echo "  quick   - 快速启动"
            echo "  cleanup - 清理容器"
            echo "  status  - 显示状态"
            echo "  help    - 显示帮助"
            ;;
        *)
            log_error "未知参数: $1"
            echo "使用 '$0 help' 查看帮助"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"