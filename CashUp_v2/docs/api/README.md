# API 接口文档总览

## 概述

CashUp v2 量化交易系统采用微服务架构，包含4个核心服务，每个服务提供专门的API接口。本文档提供了所有服务的接口地址、功能说明和出入参示例。

## 服务架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Core Service │    │ Trading Engine │    │Strategy Platform│    │Notification Svc│
│     (8001)     │    │     (8002)     │    │     (8003)     │    │     (8004)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         └───────────────────────┼───────────────────────┼───────────────────────┘
                                 │                       │
         ┌───────────────────────┼───────────────────────┼───────────────────────┐
         │                   Frontend (3000)             │                       │
         │                   Nginx (80/443)             │                       │
         └───────────────────────────────────────────────────────────────────────┘
```

## 服务列表

### 1. 核心服务 (Core Service)
- **端口**: 8001
- **地址**: http://localhost:8001
- **文档**: [core-service.md](./core-service.md)
- **功能**: 用户认证、用户管理、配置管理、系统监控

### 2. 交易引擎 (Trading Engine)
- **端口**: 8002
- **地址**: http://localhost:8002
- **文档**: [trading-engine.md](./trading-engine.md)
- **功能**: 交易所管理、订单管理、持仓管理、交易执行、风险控制

### 3. 策略平台 (Strategy Platform)
- **端口**: 8003
- **地址**: http://localhost:8003
- **文档**: [strategy-platform.md](./strategy-platform.md)
- **功能**: 策略管理、回测引擎、数据管理、性能分析

### 4. 通知服务 (Notification Service)
- **端口**: 8004
- **地址**: http://localhost:8004
- **文档**: [notification-service.md](./notification-service.md)
- **功能**: 消息通知、邮件发送、短信发送、Webhook推送

## 访问地址

### 直接访问
- 核心服务: http://localhost:8001
- 交易引擎: http://localhost:8002
- 策略平台: http://localhost:8003
- 通知服务: http://localhost:8004

### 通过Nginx反向代理
- Web界面: http://localhost:80
- API接口: http://localhost:80/api/
- WebSocket: http://localhost:80/ws/

### API文档
- 核心服务文档: http://localhost:8001/docs
- 交易引擎文档: http://localhost:8002/docs
- 策略平台文档: http://localhost:8003/docs
- 通知服务文档: http://localhost:8004/docs

### 健康检查
- 核心服务: http://localhost:8001/health
- 交易引擎: http://localhost:8002/health
- 策略平台: http://localhost:8003/health
- 通知服务: http://localhost:8004/health

## 认证方式

所有API接口使用Bearer Token认证：

```http
Authorization: Bearer <access_token>
```

Token获取流程：
1. 调用核心服务登录接口获取Token
2. 在后续请求的Header中携带Token
3. Token有效期1小时，过期需重新获取

## 通用错误格式

所有接口返回的错误格式统一：

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": {}
  }
}
```

## 通用状态码

- `200`: 请求成功
- `201`: 创建成功
- `400`: 请求参数错误
- `401`: 认证失败
- `403`: 权限不足
- `404`: 资源不存在
- `409`: 资源冲突
- `422`: 数据验证失败
- `500`: 服务器内部错误
- `503`: 服务不可用

## 接口规范

### 请求参数规范
- 使用JSON格式传输数据
- 时间格式使用ISO 8601标准
- 金额使用字符串类型避免精度问题
- 分页参数使用`skip`和`limit`

### 响应数据规范
- 列表接口返回分页信息
- 包含时间戳字段
- 数值类型统一使用字符串
- 错误信息包含详细描述

### 数据验证
- 所有输入参数都经过验证
- 必填字段不能为空
- 数据类型和格式必须正确
- 业务规则验证

## 安全要求

### 认证安全
- 使用HTTPS传输
- Token定期刷新
- 敏感操作需要二次验证

### 数据安全
- 敏感数据加密存储
- 用户隐私保护
- 操作日志记录

### 访问控制
- 基于角色的权限控制
- 用户只能访问自己的数据
- 管理员具有全部权限

## 性能优化

### 缓存策略
- Redis缓存热点数据
- API响应缓存
- 静态资源缓存

### 限流措施
- API调用频率限制
- 并发请求限制
- 资源使用限制

### 监控告警
- 系统性能监控
- 错误率监控
- 响应时间监控

## 使用示例

### 获取Token
```bash
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### 调用API
```bash
curl -X GET http://localhost:8001/api/users/me \
  -H "Authorization: Bearer <token>"
```

### WebSocket连接
```javascript
const ws = new WebSocket('ws://localhost:8002/ws');
ws.onmessage = (event) => {
  console.log(JSON.parse(event.data));
};
```

## 最佳实践

1. **错误处理**: 妥善处理各种错误情况
2. **重试机制**: 对失败请求进行适当重试
3. **资源清理**: 及时释放不再需要的资源
4. **日志记录**: 记录重要操作和错误信息
5. **性能优化**: 合理使用缓存和批量操作

## 版本管理

API版本通过URL路径管理：
- 当前版本: `/api/v1/`
- 未来版本: `/api/v2/`

版本更新时会保持向后兼容性，并提供迁移指南。

## 支持与反馈

如遇API使用问题，请：
1. 查看对应服务的详细文档
2. 检查错误信息和日志
3. 联系技术支持团队

---

*本文档最后更新时间：2023-01-01*