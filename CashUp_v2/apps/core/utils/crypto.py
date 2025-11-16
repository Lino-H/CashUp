"""
密钥加密工具
函数集注释：
- encrypt_str: 使用应用 SECRET_KEY 派生的 Fernet 密钥加密字符串
- decrypt_str: 使用应用 SECRET_KEY 派生的 Fernet 密钥解密字符串
"""

import base64
import hashlib
from typing import Optional

from cryptography.fernet import Fernet
from config.settings import settings


def _get_fernet() -> Fernet:
    sk = settings.SECRET_KEY or "cashup-default-secret"
    dk = hashlib.sha256(sk.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(dk)
    return Fernet(key)


def encrypt_str(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    f = _get_fernet()
    token = f.encrypt(value.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_str(token: Optional[str]) -> Optional[str]:
    if token is None:
        return None
    f = _get_fernet()
    data = f.decrypt(token.encode("utf-8"))
    return data.decode("utf-8")