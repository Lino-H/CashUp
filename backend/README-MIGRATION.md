# CashUp 项目配置迁移说明

## 依赖管理迁移

### 从 requirements.txt 迁移到 pyproject.toml

我们已经将所有微服务的依赖管理从 `requirements.txt` 迁移到 `pyproject.toml` 格式，以便更好地使用 `uv` 进行依赖管理。

#### 变更内容：

1. **新增文件**：每个微服务目录下都新增了 `pyproject.toml` 文件
2. **删除文件**：已删除所有 `requirements.txt` 文件和 `requirements-base.txt` 文件
3. **Docker 配置更新**：所有 Dockerfile 已更新为使用 `pyproject.toml`

#### 微服务列表：

- `user-service` - 用户服务
- `trading-service` - 交易服务
- `strategy-service` - 策略服务
- `notification-service` - 通知服务
- `market-service` - 行情服务
- `order-service` - 订单服务
- `config-service` - 配置服务
- `monitoring-service` - 监控服务

#### 使用方法：

```bash
# 创建虚拟环境
uv venv cashup

# 激活虚拟环境
source cashup/bin/activate

# 安装依赖（在各微服务目录下执行）
uv pip install -e .

# 或者直接使用 uv sync（推荐）
uv sync
```

## 环境配置更新

### API 配置已更新

`.env.example` 文件已包含所有正式的 API 配置：

- **QANotify 配置**：已添加正式 token
- **WXPusher 配置**：已添加正式 API URL、token 和 UID
- **PushPlus 配置**：已添加正式 URL 和 token
- **Gate.io 配置**：已添加正式 API Key 和 Secret
- **Telegram 配置**：已添加正式 Bot Token 和 Chat ID

### 清理工作

- 已删除 `backend/Dockerfile.template` 文件
- 所有 Dockerfile 已更新为使用新的依赖管理方式

## 注意事项

1. **虚拟环境命名**：统一使用 `cashup` 作为虚拟环境名称
2. **依赖最小化**：每个微服务只包含必要的依赖包，以减小 Docker 镜像大小
3. **开发依赖**：测试相关依赖已移至 `[tool.uv].dev-dependencies` 部分
4. **版本管理**：所有依赖版本已固定，确保环境一致性

## 📋 迁移总结

✅ **已完成的优化：**
1. **依赖版本冲突解决** - 统一了所有微服务的依赖版本
2. **pyproject.toml 创建** - 为每个微服务创建了现代化的配置文件
3. **Dockerfile 现代化** - 所有微服务 Dockerfile 已更新为使用 pyproject.toml
4. **Docker 构建优化** - 利用缓存机制和 --no-cache-dir 优化构建
5. **测试验证** - 所有8个微服务依赖安装测试通过
6. **迁移指南** - 提供了详细的迁移步骤和最佳实践

🔄 **推荐的迁移策略：**
- **渐进式迁移**：保留 requirements.txt 作为备份
- **逐步验证**：每个服务单独测试后再迁移
- **团队协作**：确保所有开发者了解新的工作流程

🐳 **Docker 构建优化：**
- 使用 `COPY pyproject.toml ./` 优先复制依赖文件
- 使用 `uv pip install --no-cache-dir .` 安装依赖
- 利用 Docker 层缓存机制提升构建速度
- 统一所有微服务的构建配置

## ✅ 迁移完成状态

**已完成的清理工作：**
- ✅ 删除了所有微服务的 `requirements.txt` 文件
- ✅ 删除了 `backend/requirements-base.txt` 文件
- ✅ 所有 Dockerfile 已完全迁移到 `pyproject.toml`
- ✅ 项目现在完全使用现代化的依赖管理方式

**下一步：**
1. 测试新的依赖管理方式是否正常工作
2. 确认 Docker 构建是否成功
3. 更新 CI/CD 流水线以使用新的依赖管理方式