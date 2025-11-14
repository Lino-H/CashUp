#!/usr/bin/env python3
"""
核心服务启动脚本
"""

import os
import sys
import uvicorn
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    uvicorn.run(
        "core_service.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )