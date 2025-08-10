#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CashUp量化交易系统 - 工具函数

提供通用的工具函数
"""

import json
import yaml
import toml
import configparser
import hashlib
import secrets
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Union, List
from pathlib import Path

from ..models.config import ConfigFormat


def generate_config_id() -> str:
    """
    生成配置ID
    """
    return secrets.token_urlsafe(16)


def generate_hash(data: str) -> str:
    """
    生成数据哈希值
    """
    return hashlib.sha256(data.encode()).hexdigest()


def get_current_timestamp() -> datetime:
    """
    获取当前UTC时间戳
    """
    return datetime.now(timezone.utc)


def format_timestamp(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化时间戳
    """
    return dt.strftime(format_str)


def parse_config_value(
    value: Union[str, Dict, Any],
    format_type: ConfigFormat
) -> Dict[str, Any]:
    """
    解析配置值
    """
    if isinstance(value, dict):
        return value
    
    if not isinstance(value, str):
        raise ValueError(f"无法解析配置值: {type(value)}")
    
    try:
        if format_type == ConfigFormat.JSON:
            return json.loads(value)
        elif format_type == ConfigFormat.YAML:
            return yaml.safe_load(value)
        elif format_type == ConfigFormat.TOML:
            return toml.loads(value)
        elif format_type == ConfigFormat.INI:
            config = configparser.ConfigParser()
            config.read_string(value)
            return {section: dict(config[section]) for section in config.sections()}
        elif format_type == ConfigFormat.ENV:
            # 简单的环境变量格式解析
            result = {}
            for line in value.strip().split('\n'):
                if '=' in line and not line.startswith('#'):
                    key, val = line.split('=', 1)
                    result[key.strip()] = val.strip()
            return result
        else:
            raise ValueError(f"不支持的配置格式: {format_type}")
    except Exception as e:
        raise ValueError(f"解析配置值失败: {str(e)}")


def serialize_config_value(
    value: Dict[str, Any],
    format_type: ConfigFormat
) -> str:
    """
    序列化配置值
    """
    try:
        if format_type == ConfigFormat.JSON:
            return json.dumps(value, ensure_ascii=False, indent=2)
        elif format_type == ConfigFormat.YAML:
            return yaml.dump(value, default_flow_style=False, allow_unicode=True)
        elif format_type == ConfigFormat.TOML:
            return toml.dumps(value)
        elif format_type == ConfigFormat.INI:
            config = configparser.ConfigParser()
            for section, options in value.items():
                config[section] = options
            
            from io import StringIO
            output = StringIO()
            config.write(output)
            return output.getvalue()
        elif format_type == ConfigFormat.ENV:
            lines = []
            for key, val in value.items():
                lines.append(f"{key}={val}")
            return '\n'.join(lines)
        else:
            raise ValueError(f"不支持的配置格式: {format_type}")
    except Exception as e:
        raise ValueError(f"序列化配置值失败: {str(e)}")


def validate_config_key(key: str) -> bool:
    """
    验证配置键格式
    """
    if not key or not key.strip():
        return False
    
    # 配置键只能包含字母、数字、下划线、点号和连字符
    import re
    return bool(re.match(r'^[a-zA-Z0-9._-]+$', key.strip()))


def normalize_config_key(key: str) -> str:
    """
    标准化配置键
    """
    return key.strip().lower()


def deep_merge_dict(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """
    深度合并字典
    """
    result = base.copy()
    
    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dict(result[key], value)
        else:
            result[key] = value
    
    return result


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    扁平化字典
    """
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def unflatten_dict(d: Dict[str, Any], sep: str = '.') -> Dict[str, Any]:
    """
    反扁平化字典
    """
    result = {}
    for key, value in d.items():
        keys = key.split(sep)
        current = result
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
    return result


def mask_sensitive_data(data: Dict[str, Any], sensitive_keys: List[str] = None) -> Dict[str, Any]:
    """
    遮蔽敏感数据
    """
    if sensitive_keys is None:
        sensitive_keys = [
            'password', 'secret', 'key', 'token', 'api_key',
            'private_key', 'access_token', 'refresh_token'
        ]
    
    def mask_value(key: str, value: Any) -> Any:
        if isinstance(value, dict):
            return {k: mask_value(k, v) for k, v in value.items()}
        elif isinstance(value, list):
            return [mask_value(key, item) for item in value]
        elif any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
            return "***MASKED***"
        else:
            return value
    
    return {k: mask_value(k, v) for k, v in data.items()}


def calculate_config_diff(old_config: Dict[str, Any], new_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    计算配置差异
    """
    diff = {
        "added": {},
        "removed": {},
        "modified": {},
        "unchanged": {}
    }
    
    # 扁平化配置以便比较
    old_flat = flatten_dict(old_config)
    new_flat = flatten_dict(new_config)
    
    all_keys = set(old_flat.keys()) | set(new_flat.keys())
    
    for key in all_keys:
        if key not in old_flat:
            diff["added"][key] = new_flat[key]
        elif key not in new_flat:
            diff["removed"][key] = old_flat[key]
        elif old_flat[key] != new_flat[key]:
            diff["modified"][key] = {
                "old": old_flat[key],
                "new": new_flat[key]
            }
        else:
            diff["unchanged"][key] = old_flat[key]
    
    return diff


def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    验证JSON Schema
    """
    try:
        import jsonschema
        jsonschema.validate(data, schema)
        return True, []
    except jsonschema.ValidationError as e:
        return False, [e.message]
    except Exception as e:
        return False, [str(e)]


def sanitize_filename(filename: str) -> str:
    """
    清理文件名
    """
    import re
    # 移除或替换不安全的字符
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # 移除控制字符
    filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)
    # 限制长度
    if len(filename) > 255:
        filename = filename[:255]
    return filename


def generate_backup_filename(config_key: str, timestamp: datetime = None) -> str:
    """
    生成备份文件名
    """
    if timestamp is None:
        timestamp = get_current_timestamp()
    
    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    safe_key = sanitize_filename(config_key)
    return f"config_backup_{safe_key}_{timestamp_str}.json"


def load_file_content(file_path: Union[str, Path]) -> str:
    """
    加载文件内容
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    try:
        return path.read_text(encoding='utf-8')
    except Exception as e:
        raise IOError(f"读取文件失败: {str(e)}")


def save_file_content(file_path: Union[str, Path], content: str) -> None:
    """
    保存文件内容
    """
    path = Path(file_path)
    
    # 确保目录存在
    path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        path.write_text(content, encoding='utf-8')
    except Exception as e:
        raise IOError(f"保存文件失败: {str(e)}")


def get_file_size(file_path: Union[str, Path]) -> int:
    """
    获取文件大小
    """
    path = Path(file_path)
    if not path.exists():
        return 0
    return path.stat().st_size


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"


def is_valid_uuid(uuid_string: str) -> bool:
    """
    验证UUID格式
    """
    try:
        import uuid
        uuid.UUID(uuid_string)
        return True
    except (ValueError, TypeError):
        return False


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    截断字符串
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    安全的JSON解析
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """
    安全的JSON序列化
    """
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return default


def retry_on_exception(max_retries: int = 3, delay: float = 1.0):
    """
    异常重试装饰器
    """
    def decorator(func):
        import asyncio
        import functools
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        await asyncio.sleep(delay * (2 ** attempt))  # 指数退避
                    else:
                        raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time
            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        time.sleep(delay * (2 ** attempt))  # 指数退避
                    else:
                        raise last_exception
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator