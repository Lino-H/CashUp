#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
辅助工具函数

提供各种通用的辅助函数。
"""

import uuid
import re
import html
import logging
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Union, Any, Dict, List
import json

logger = logging.getLogger(__name__)


def generate_uuid() -> str:
    """
    生成UUID字符串
    
    Returns:
        str: UUID字符串
    """
    return str(uuid.uuid4())


def format_datetime(
    dt: Optional[datetime], 
    format_str: str = "%Y-%m-%d %H:%M:%S",
    timezone_aware: bool = True
) -> Optional[str]:
    """
    格式化日期时间
    
    Args:
        dt: 日期时间对象
        format_str: 格式字符串
        timezone_aware: 是否包含时区信息
        
    Returns:
        Optional[str]: 格式化后的日期时间字符串
    """
    if dt is None:
        return None
    
    try:
        if timezone_aware and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        return dt.strftime(format_str)
    except Exception as e:
        logger.warning(f"格式化日期时间失败: {e}")
        return None


def parse_datetime(
    dt_str: str, 
    format_str: str = "%Y-%m-%d %H:%M:%S",
    timezone_aware: bool = True
) -> Optional[datetime]:
    """
    解析日期时间字符串
    
    Args:
        dt_str: 日期时间字符串
        format_str: 格式字符串
        timezone_aware: 是否设置时区信息
        
    Returns:
        Optional[datetime]: 解析后的日期时间对象
    """
    if not dt_str:
        return None
    
    try:
        dt = datetime.strptime(dt_str, format_str)
        
        if timezone_aware and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        return dt
    except Exception as e:
        logger.warning(f"解析日期时间失败: {e}")
        return None


def calculate_percentage_change(
    old_value: Union[int, float, Decimal],
    new_value: Union[int, float, Decimal]
) -> Optional[float]:
    """
    计算百分比变化
    
    Args:
        old_value: 旧值
        new_value: 新值
        
    Returns:
        Optional[float]: 百分比变化（小数形式）
    """
    try:
        if old_value == 0:
            return None if new_value == 0 else float('inf')
        
        return float((new_value - old_value) / old_value)
    except Exception as e:
        logger.warning(f"计算百分比变化失败: {e}")
        return None


def round_decimal(
    value: Union[int, float, Decimal],
    decimal_places: int = 2
) -> Decimal:
    """
    四舍五入到指定小数位
    
    Args:
        value: 数值
        decimal_places: 小数位数
        
    Returns:
        Decimal: 四舍五入后的数值
    """
    try:
        decimal_value = Decimal(str(value))
        quantize_exp = Decimal('0.1') ** decimal_places
        return decimal_value.quantize(quantize_exp, rounding=ROUND_HALF_UP)
    except Exception as e:
        logger.warning(f"四舍五入失败: {e}")
        return Decimal('0')


def validate_email(email: str) -> bool:
    """
    验证邮箱地址格式
    
    Args:
        email: 邮箱地址
        
    Returns:
        bool: 是否有效
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_string(text: str, max_length: int = None) -> str:
    """
    清理字符串，移除HTML标签和特殊字符
    
    Args:
        text: 原始字符串
        max_length: 最大长度
        
    Returns:
        str: 清理后的字符串
    """
    if not text:
        return ""
    
    try:
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 解码HTML实体
        text = html.unescape(text)
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text).strip()
        
        # 限制长度
        if max_length and len(text) > max_length:
            text = text[:max_length].rstrip() + "..."
        
        return text
    except Exception as e:
        logger.warning(f"清理字符串失败: {e}")
        return ""


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    安全地解析JSON字符串
    
    Args:
        json_str: JSON字符串
        default: 解析失败时的默认值
        
    Returns:
        Any: 解析后的对象或默认值
    """
    if not json_str:
        return default
    
    try:
        return json.loads(json_str)
    except Exception as e:
        logger.warning(f"解析JSON失败: {e}")
        return default


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """
    安全地序列化为JSON字符串
    
    Args:
        obj: 要序列化的对象
        default: 序列化失败时的默认值
        
    Returns:
        str: JSON字符串或默认值
    """
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)
    except Exception as e:
        logger.warning(f"序列化JSON失败: {e}")
        return default


def deep_merge_dict(dict1: Dict, dict2: Dict) -> Dict:
    """
    深度合并两个字典
    
    Args:
        dict1: 第一个字典
        dict2: 第二个字典
        
    Returns:
        Dict: 合并后的字典
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dict(result[key], value)
        else:
            result[key] = value
    
    return result


def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """
    扁平化嵌套字典
    
    Args:
        d: 嵌套字典
        parent_key: 父键名
        sep: 分隔符
        
    Returns:
        Dict: 扁平化后的字典
    """
    items = []
    
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    
    return dict(items)


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """
    将列表分块
    
    Args:
        lst: 原始列表
        chunk_size: 块大小
        
    Returns:
        List[List]: 分块后的列表
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def remove_duplicates(lst: List, key_func: callable = None) -> List:
    """
    移除列表中的重复项
    
    Args:
        lst: 原始列表
        key_func: 用于确定唯一性的键函数
        
    Returns:
        List: 去重后的列表
    """
    if key_func is None:
        return list(dict.fromkeys(lst))
    
    seen = set()
    result = []
    
    for item in lst:
        key = key_func(item)
        if key not in seen:
            seen.add(key)
            result.append(item)
    
    return result


def retry_on_exception(
    func: callable,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Any:
    """
    在异常时重试函数执行
    
    Args:
        func: 要执行的函数
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff_factor: 退避因子
        exceptions: 要捕获的异常类型
        
    Returns:
        Any: 函数执行结果
        
    Raises:
        Exception: 重试次数用尽后的最后一个异常
    """
    import time
    
    last_exception = None
    current_delay = delay
    
    for attempt in range(max_retries + 1):
        try:
            return func()
        except exceptions as e:
            last_exception = e
            
            if attempt < max_retries:
                logger.warning(
                    f"函数执行失败，{current_delay}秒后重试 "
                    f"(第{attempt + 1}/{max_retries}次): {e}"
                )
                time.sleep(current_delay)
                current_delay *= backoff_factor
            else:
                logger.error(f"函数执行失败，重试次数已用尽: {e}")
    
    raise last_exception


def get_nested_value(data: Dict, key_path: str, default: Any = None, sep: str = '.') -> Any:
    """
    获取嵌套字典中的值
    
    Args:
        data: 嵌套字典
        key_path: 键路径（用分隔符分隔）
        default: 默认值
        sep: 分隔符
        
    Returns:
        Any: 获取到的值或默认值
    """
    try:
        keys = key_path.split(sep)
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    except Exception:
        return default


def set_nested_value(data: Dict, key_path: str, value: Any, sep: str = '.') -> None:
    """
    设置嵌套字典中的值
    
    Args:
        data: 嵌套字典
        key_path: 键路径（用分隔符分隔）
        value: 要设置的值
        sep: 分隔符
    """
    try:
        keys = key_path.split(sep)
        current = data
        
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    except Exception as e:
        logger.warning(f"设置嵌套值失败: {e}")


def is_valid_url(url: str) -> bool:
    """
    验证URL格式
    
    Args:
        url: URL字符串
        
    Returns:
        bool: 是否有效
    """
    if not url:
        return False
    
    pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$'
    return bool(re.match(pattern, url))


def mask_sensitive_data(data: str, mask_char: str = '*', visible_chars: int = 4) -> str:
    """
    遮蔽敏感数据
    
    Args:
        data: 敏感数据
        mask_char: 遮蔽字符
        visible_chars: 可见字符数
        
    Returns:
        str: 遮蔽后的数据
    """
    if not data or len(data) <= visible_chars:
        return mask_char * len(data) if data else ""
    
    visible_part = data[:visible_chars]
    masked_part = mask_char * (len(data) - visible_chars)
    
    return visible_part + masked_part


def calculate_hash(data: str, algorithm: str = 'sha256') -> str:
    """
    计算数据哈希值
    
    Args:
        data: 要计算哈希的数据
        algorithm: 哈希算法
        
    Returns:
        str: 哈希值
    """
    import hashlib
    
    try:
        hash_func = getattr(hashlib, algorithm)
        return hash_func(data.encode('utf-8')).hexdigest()
    except Exception as e:
        logger.warning(f"计算哈希失败: {e}")
        return ""