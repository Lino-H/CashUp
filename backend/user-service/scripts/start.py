#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 用户服务启动脚本

提供开发和生产环境的启动选项
"""

import argparse
import asyncio
import sys
import uvicorn
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings
from app.core.logging import setup_logging, get_logger

# 设置日志
setup_logging()
logger = get_logger("startup")


def parse_args():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(
        description="CashUp用户服务启动脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/start.py --dev                    # 开发模式
  python scripts/start.py --prod                   # 生产模式
  python scripts/start.py --host 0.0.0.0 --port 8001  # 自定义主机和端口
  python scripts/start.py --workers 4              # 指定工作进程数
        """
    )
    
    # 运行模式
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--dev",
        action="store_true",
        help="开发模式（自动重载、调试信息）"
    )
    mode_group.add_argument(
        "--prod",
        action="store_true",
        help="生产模式（多进程、优化性能）"
    )
    
    # 服务器配置
    parser.add_argument(
        "--host",
        default=settings.HOST,
        help=f"绑定主机地址（默认: {settings.HOST}）"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.PORT,
        help=f"绑定端口（默认: {settings.PORT}）"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="工作进程数（仅生产模式，默认: 1）"
    )
    
    # 其他选项
    parser.add_argument(
        "--reload",
        action="store_true",
        help="启用自动重载（开发模式默认启用）"
    )
    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error", "critical"],
        default=settings.LOG_LEVEL.lower(),
        help=f"日志级别（默认: {settings.LOG_LEVEL.lower()}）"
    )
    parser.add_argument(
        "--access-log",
        action="store_true",
        help="启用访问日志"
    )
    
    return parser.parse_args()


def get_uvicorn_config(args):
    """
    获取Uvicorn配置
    
    Args:
        args: 命令行参数
    
    Returns:
        dict: Uvicorn配置字典
    """
    config = {
        "app": "main:app",
        "host": args.host,
        "port": args.port,
        "log_level": args.log_level,
        "access_log": args.access_log,
    }
    
    # 开发模式配置
    if args.dev or (not args.prod and settings.ENVIRONMENT == "development"):
        config.update({
            "reload": True,
            "reload_dirs": [str(project_root / "app")],
            "reload_excludes": ["*.pyc", "__pycache__"],
            "log_level": "debug" if args.log_level == "info" else args.log_level,
            "access_log": True,
        })
        logger.info("🔧 使用开发模式配置")
    
    # 生产模式配置
    elif args.prod or settings.ENVIRONMENT == "production":
        config.update({
            "workers": args.workers,
            "worker_class": "uvicorn.workers.UvicornWorker",
            "reload": False,
            "access_log": args.access_log,
        })
        logger.info(f"🚀 使用生产模式配置（{args.workers} 个工作进程）")
    
    # 自定义重载
    if args.reload:
        config["reload"] = True
    
    return config


def check_environment():
    """
    检查运行环境
    """
    logger.info("🔍 检查运行环境...")
    
    # 检查必要的环境变量
    required_vars = ["DATABASE_URL", "SECRET_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not getattr(settings, var, None):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ 缺少必要的环境变量: {', '.join(missing_vars)}")
        logger.error("请检查 .env 文件或环境变量配置")
        sys.exit(1)
    
    # 显示配置信息
    logger.info(f"🌍 环境: {settings.ENVIRONMENT}")
    logger.info(f"🔗 数据库: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'SQLite'}")
    logger.info(f"📡 Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    logger.info(f"🔐 JWT过期时间: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} 分钟")
    
    # 生产环境安全检查
    if settings.ENVIRONMENT == "production":
        logger.info("🔒 执行生产环境安全检查...")
        
        # 检查密钥强度
        if len(settings.SECRET_KEY) < 32:
            logger.warning("⚠️  SECRET_KEY 长度不足，建议使用至少32位的强密钥")
        
        # 检查调试模式
        if settings.DEBUG:
            logger.warning("⚠️  生产环境中启用了调试模式，建议关闭")
        
        # 检查CORS设置
        if "*" in settings.ALLOWED_HOSTS:
            logger.warning("⚠️  CORS设置允许所有来源，建议限制为特定域名")
    
    logger.info("✅ 环境检查完成")


def print_startup_info(args):
    """
    打印启动信息
    
    Args:
        args: 命令行参数
    """
    logger.info("")
    logger.info("🎉 CashUp用户服务启动中...")
    logger.info("")
    logger.info("📋 服务信息:")
    logger.info(f"   名称: CashUp User Service")
    logger.info(f"   版本: 1.0.0")
    logger.info(f"   环境: {settings.ENVIRONMENT}")
    logger.info(f"   地址: http://{args.host}:{args.port}")
    logger.info(f"   文档: http://{args.host}:{args.port}/docs")
    logger.info("")
    
    if args.dev or (not args.prod and settings.ENVIRONMENT == "development"):
        logger.info("🔧 开发模式功能:")
        logger.info("   ✓ 自动重载")
        logger.info("   ✓ 详细日志")
        logger.info("   ✓ 调试信息")
        logger.info("   ✓ 访问日志")
    elif args.prod or settings.ENVIRONMENT == "production":
        logger.info("🚀 生产模式功能:")
        logger.info(f"   ✓ {args.workers} 个工作进程")
        logger.info("   ✓ 性能优化")
        logger.info("   ✓ 安全加固")
    
    logger.info("")
    logger.info("🔗 相关链接:")
    logger.info(f"   API文档: http://{args.host}:{args.port}/docs")
    logger.info(f"   ReDoc文档: http://{args.host}:{args.port}/redoc")
    logger.info(f"   OpenAPI规范: http://{args.host}:{args.port}/openapi.json")
    logger.info(f"   健康检查: http://{args.host}:{args.port}/health")
    logger.info("")


def main():
    """
    主函数
    """
    try:
        # 解析命令行参数
        args = parse_args()
        
        # 检查环境
        check_environment()
        
        # 打印启动信息
        print_startup_info(args)
        
        # 获取Uvicorn配置
        config = get_uvicorn_config(args)
        
        # 启动服务器
        logger.info("🚀 启动HTTP服务器...")
        uvicorn.run(**config)
        
    except KeyboardInterrupt:
        logger.info("\n👋 收到中断信号，正在关闭服务...")
    except Exception as e:
        logger.error(f"❌ 启动失败: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()