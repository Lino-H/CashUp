"""
工具函数模块
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
import json

def setup_logger(name: str) -> logging.Logger:
    """设置日志记录器"""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # 创建控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """获取日志记录器"""
    return setup_logger(name)

def ensure_directory(path: Path) -> Path:
    """确保目录存在"""
    path.mkdir(parents=True, exist_ok=True)
    return path

def save_json(data: dict, file_path: Path) -> bool:
    """保存JSON数据到文件"""
    try:
        ensure_directory(file_path.parent)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        return True
    except Exception as e:
        logging.error(f"保存JSON文件失败: {e}")
        return False

def load_json(file_path: Path) -> Optional[dict]:
    """从文件加载JSON数据"""
    try:
        if not file_path.exists():
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"加载JSON文件失败: {e}")
        return None

def format_timestamp(timestamp: datetime) -> str:
    """格式化时间戳"""
    return timestamp.strftime('%Y-%m-%d %H:%M:%S')

def format_number(number: float, decimals: int = 2) -> str:
    """格式化数字"""
    return f"{number:,.{decimals}f}"

def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """安全除法"""
    try:
        return a / b if b != 0 else default
    except (TypeError, ZeroDivisionError):
        return default

def calculate_percentage(value: float, total: float) -> float:
    """计算百分比"""
    return safe_divide(value * 100, total, 0.0)

def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> tuple[bool, str]:
    """验证密码强度"""
    if len(password) < 6:
        return False, "密码长度不能少于6位"
    
    if len(password) > 50:
        return False, "密码长度不能超过50位"
    
    if not any(c.isupper() for c in password):
        return False, "密码必须包含大写字母"
    
    if not any(c.islower() for c in password):
        return False, "密码必须包含小写字母"
    
    if not any(c.isdigit() for c in password):
        return False, "密码必须包含数字"
    
    return True, "密码强度符合要求"

def truncate_string(text: str, max_length: int = 100) -> str:
    """截断字符串"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def generate_random_string(length: int = 8) -> str:
    """生成随机字符串"""
    import random
    import string
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def hash_string(text: str) -> str:
    """哈希字符串"""
    import hashlib
    return hashlib.sha256(text.encode()).hexdigest()

def is_port_available(port: int) -> bool:
    """检查端口是否可用"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            return result != 0
    except Exception:
        return False