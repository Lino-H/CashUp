"""
基础功能测试
"""

import pytest

def test_basic_functionality():
    """测试基础功能"""
    assert 1 + 1 == 2
    assert "hello" == "hello"

def test_imports():
    """测试导入"""
    import sys
    assert sys.version_info >= (3, 6)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
