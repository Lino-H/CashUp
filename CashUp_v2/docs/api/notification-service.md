# 通知服务 API 文档

## 服务概述

**服务名称**: Notification Service  
**服务端口**: 8004  
**服务地址**: http://localhost:8004  
**API文档**: http://localhost:8004/docs  
**健康检查**: http://localhost:8004/health  

## 主要功能

- 消息通知
- 邮件发送
- 短信发送
- Webhook推送
- 通知模板管理
- 通知历史记录

## 接口列表

### 1. 通知发送接口

#### 1.1 发送邮件通知
- **接口地址**: `POST /api/notifications/email`
- **功能描述**: 发送邮件通知
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "to": ["user@example.com"],
  "subject": "交易完成通知",
  "body": "您的交易已成功完成",
  "template": "trade_completed",
  "data": {
    "symbol": "BTC/USDT",
    "side": "buy",
    "quantity": 0.001,
    "price": 30000.0,
    "pnl": 1.0
  },
  "priority": "normal"
}
```
- **响应示例**:
```json
{
  "id": "email_123",
  "type": "email",
  "status": "sent",
  "to": ["user@example.com"],
  "subject": "交易完成通知",
  "sent_at": "2023-01-01T00:00:00Z",
  "message_id": "smtp_message_123"
}
```
- **状态码**: 200 (发送成功), 400 (参数错误), 401 (认证失败), 500 (发送失败)

#### 1.2 发送短信通知
- **接口地址**: `POST /api/notifications/sms`
- **功能描述**: 发送短信通知
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "to": ["+8613800138000"],
  "content": "您的交易已成功完成：BTC/USDT买入0.001个",
  "template": "trade_completed",
  "data": {
    "symbol": "BTC/USDT",
    "side": "buy",
    "quantity": 0.001
  },
  "priority": "normal"
}
```
- **响应示例**:
```json
{
  "id": "sms_123",
  "type": "sms",
  "status": "sent",
  "to": ["+8613800138000"],
  "content": "您的交易已成功完成：BTC/USDT买入0.001个",
  "sent_at": "2023-01-01T00:00:00Z",
  "message_id": "sms_message_123"
}
```
- **状态码**: 200 (发送成功), 400 (参数错误), 401 (认证失败), 500 (发送失败)

#### 1.3 发送Webhook通知
- **接口地址**: `POST /api/notifications/webhook`
- **功能描述**: 发送Webhook通知
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "url": "https://example.com/webhook",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer webhook_token"
  },
  "data": {
    "event": "trade_completed",
    "timestamp": "2023-01-01T00:00:00Z",
    "payload": {
      "symbol": "BTC/USDT",
      "side": "buy",
      "quantity": 0.001,
      "price": 30000.0
    }
  },
  "retries": 3
}
```
- **响应示例**:
```json
{
  "id": "webhook_123",
  "type": "webhook",
  "status": "sent",
  "url": "https://example.com/webhook",
  "response_code": 200,
  "sent_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (发送成功), 400 (参数错误), 401 (认证失败), 500 (发送失败)

#### 1.4 发送站内消息
- **接口地址**: `POST /api/notifications/internal`
- **功能描述**: 发送站内消息
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "user_ids": [1, 2, 3],
  "title": "系统维护通知",
  "content": "系统将于今晚22:00-23:00进行维护",
  "type": "system",
  "priority": "high",
  "expires_at": "2023-01-02T00:00:00Z"
}
```
- **响应示例**:
```json
{
  "id": "internal_123",
  "type": "internal",
  "status": "delivered",
  "user_ids": [1, 2, 3],
  "title": "系统维护通知",
  "content": "系统将于今晚22:00-23:00进行维护",
  "delivered_at": "2023-01-01T00:00:00Z",
  "read_count": 0
}
```
- **状态码**: 200 (发送成功), 400 (参数错误), 401 (认证失败)

### 2. 通知模板接口

#### 2.1 获取模板列表
- **接口地址**: `GET /api/templates`
- **功能描述**: 获取通知模板列表
- **请求参数**:
  - `skip`: 跳过记录数 (默认: 0)
  - `limit`: 限制记录数 (默认: 100)
  - `type`: 模板类型筛选 (可选: email, sms, webhook, internal)
  - `category`: 分类筛选 (可选)
  - `search`: 搜索关键词 (可选)
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "templates": [
    {
      "id": 1,
      "name": "trade_completed",
      "title": "交易完成通知",
      "type": "email",
      "category": "trading",
      "subject": "您的交易已成功完成",
      "body": "尊敬的用户，您的交易已成功完成：\n交易对：{{symbol}}\n方向：{{side}}\n数量：{{quantity}}\n价格：{{price}}\n盈亏：{{pnl}}",
      "variables": ["symbol", "side", "quantity", "price", "pnl"],
      "is_system": true,
      "created_at": "2023-01-01T00:00:00Z",
      "updated_at": "2023-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```
- **状态码**: 200 (成功), 401 (认证失败)

#### 2.2 获取模板详情
- **接口地址**: `GET /api/templates/{template_id}`
- **功能描述**: 获取指定模板详情
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "id": 1,
  "name": "trade_completed",
  "title": "交易完成通知",
  "type": "email",
  "category": "trading",
  "subject": "您的交易已成功完成",
  "body": "尊敬的用户，您的交易已成功完成：\n交易对：{{symbol}}\n方向：{{side}}\n数量：{{quantity}}\n价格：{{price}}\n盈亏：{{pnl}}",
  "html_body": "<html><body><h3>您的交易已成功完成</h3><p>交易对：{{symbol}}</p><p>方向：{{side}}</p><p>数量：{{quantity}}</p><p>价格：{{price}}</p><p>盈亏：{{pnl}}</p></body></html>",
  "variables": [
    {
      "name": "symbol",
      "type": "string",
      "description": "交易对",
      "required": true
    },
    {
      "name": "side",
      "type": "string",
      "description": "买卖方向",
      "required": true
    }
  ],
  "is_system": true,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (成功), 401 (认证失败), 404 (模板不存在)

#### 2.3 创建模板
- **接口地址**: `POST /api/templates`
- **功能描述**: 创建新模板
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "name": "custom_alert",
  "title": "自定义告警",
  "type": "email",
  "category": "alert",
  "subject": "系统告警：{{alert_type}}",
  "body": "检测到{{alert_type}}告警：\n时间：{{timestamp}}\n详情：{{details}}",
  "variables": ["alert_type", "timestamp", "details"],
  "is_system": false
}
```
- **响应示例**:
```json
{
  "id": 2,
  "name": "custom_alert",
  "title": "自定义告警",
  "type": "email",
  "category": "alert",
  "subject": "系统告警：{{alert_type}}",
  "body": "检测到{{alert_type}}告警：\n时间：{{timestamp}}\n详情：{{details}}",
  "variables": ["alert_type", "timestamp", "details"],
  "is_system": false,
  "created_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 201 (创建成功), 400 (参数错误), 401 (认证失败), 409 (模板已存在)

#### 2.4 更新模板
- **接口地址**: `PUT /api/templates/{template_id}`
- **功能描述**: 更新模板
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "title": "更新后的告警标题",
  "subject": "系统告警：{{alert_type}} - 优先级：{{priority}}",
  "body": "检测到{{alert_type}}告警：\n时间：{{timestamp}}\n优先级：{{priority}}\n详情：{{details}}"
}
```
- **响应示例**:
```json
{
  "id": 2,
  "name": "custom_alert",
  "title": "更新后的告警标题",
  "type": "email",
  "category": "alert",
  "subject": "系统告警：{{alert_type}} - 优先级：{{priority}}",
  "body": "检测到{{alert_type}}告警：\n时间：{{timestamp}}\n优先级：{{priority}}\n详情：{{details}}",
  "variables": ["alert_type", "timestamp", "priority", "details"],
  "is_system": false,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (更新成功), 400 (参数错误), 401 (认证失败), 404 (模板不存在)

#### 2.5 删除模板
- **接口地址**: `DELETE /api/templates/{template_id}`
- **功能描述**: 删除模板
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "message": "模板删除成功"
}
```
- **状态码**: 200 (删除成功), 401 (认证失败), 404 (模板不存在)

#### 2.6 渲染模板
- **接口地址**: `POST /api/templates/{template_id}/render`
- **功能描述**: 渲染模板
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "data": {
    "symbol": "BTC/USDT",
    "side": "buy",
    "quantity": 0.001,
    "price": 30000.0,
    "pnl": 1.0
  }
}
```
- **响应示例**:
```json
{
  "template_id": 1,
  "subject": "您的交易已成功完成",
  "body": "尊敬的用户，您的交易已成功完成：\n交易对：BTC/USDT\n方向：buy\n数量：0.001\n价格：30000.0\n盈亏：1.0",
  "html_body": "<html><body><h3>您的交易已成功完成</h3><p>交易对：BTC/USDT</p><p>方向：buy</p><p>数量：0.001</p><p>价格：30000.0</p><p>盈亏：1.0</p></body></html>",
  "rendered_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (渲染成功), 400 (参数错误), 401 (认证失败), 404 (模板不存在)

### 3. 通知历史接口

#### 3.1 获取通知历史
- **接口地址**: `GET /api/notifications`
- **功能描述**: 获取通知发送历史
- **请求参数**:
  - `skip`: 跳过记录数 (默认: 0)
  - `limit`: 限制记录数 (默认: 100)
  - `type`: 通知类型筛选 (可选: email, sms, webhook, internal)
  - `status`: 状态筛选 (可选: sent, failed, pending)
  - `start_date`: 开始时间 (可选)
  - `end_date`: 结束时间 (可选)
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "notifications": [
    {
      "id": "email_123",
      "type": "email",
      "status": "sent",
      "recipient": "user@example.com",
      "subject": "交易完成通知",
      "template": "trade_completed",
      "priority": "normal",
      "sent_at": "2023-01-01T00:00:00Z",
      "delivered_at": "2023-01-01T00:00:01Z",
      "read_at": null,
      "error": null
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```
- **状态码**: 200 (成功), 401 (认证失败)

#### 3.2 获取通知详情
- **接口地址**: `GET /api/notifications/{notification_id}`
- **功能描述**: 获取指定通知详情
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "id": "email_123",
  "type": "email",
  "status": "sent",
  "recipient": "user@example.com",
  "subject": "交易完成通知",
  "content": "尊敬的用户，您的交易已成功完成：\n交易对：BTC/USDT\n方向：buy\n数量：0.001\n价格：30000.0\n盈亏：1.0",
  "template": "trade_completed",
  "template_data": {
    "symbol": "BTC/USDT",
    "side": "buy",
    "quantity": 0.001,
    "price": 30000.0,
    "pnl": 1.0
  },
  "priority": "normal",
  "sent_at": "2023-01-01T00:00:00Z",
  "delivered_at": "2023-01-01T00:00:01Z",
  "read_at": null,
  "error": null,
  "retry_count": 0,
  "metadata": {
    "message_id": "smtp_message_123",
    "server_response": "250 OK"
  }
}
```
- **状态码**: 200 (成功), 401 (认证失败), 404 (通知不存在)

#### 3.3 重试发送通知
- **接口地址**: `POST /api/notifications/{notification_id}/retry`
- **功能描述**: 重试发送失败的通知
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "id": "email_123",
  "type": "email",
  "status": "retrying",
  "retry_count": 1,
  "last_retry_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (重试开始), 400 (通知不可重试), 401 (认证失败), 404 (通知不存在)

### 4. 通知设置接口

#### 4.1 获取通知设置
- **接口地址**: `GET /api/settings`
- **功能描述**: 获取用户通知设置
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "user_id": 1,
  "email_notifications": {
    "enabled": true,
    "trade_completed": true,
    "risk_alert": true,
    "system_error": true,
    "daily_report": false
  },
  "sms_notifications": {
    "enabled": false,
    "trade_completed": false,
    "risk_alert": true,
    "system_error": true
  },
  "webhook_notifications": {
    "enabled": true,
    "url": "https://example.com/webhook",
    "events": ["trade_completed", "risk_alert"]
  },
  "internal_notifications": {
    "enabled": true,
    "desktop": true,
    "sound": true
  },
  "quiet_hours": {
    "enabled": true,
    "start": "22:00",
    "end": "08:00"
  },
  "frequency_limits": {
    "max_per_hour": 10,
    "max_per_day": 50
  }
}
```
- **状态码**: 200 (成功), 401 (认证失败)

#### 4.2 更新通知设置
- **接口地址**: `PUT /api/settings`
- **功能描述**: 更新用户通知设置
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "email_notifications": {
    "enabled": true,
    "trade_completed": true,
    "risk_alert": true,
    "system_error": true,
    "daily_report": true
  },
  "sms_notifications": {
    "enabled": true,
    "trade_completed": false,
    "risk_alert": true,
    "system_error": true
  },
  "quiet_hours": {
    "enabled": false,
    "start": "22:00",
    "end": "08:00"
  }
}
```
- **响应示例**:
```json
{
  "user_id": 1,
  "email_notifications": {
    "enabled": true,
    "trade_completed": true,
    "risk_alert": true,
    "system_error": true,
    "daily_report": true
  },
  "sms_notifications": {
    "enabled": true,
    "trade_completed": false,
    "risk_alert": true,
    "system_error": true
  },
  "webhook_notifications": {
    "enabled": true,
    "url": "https://example.com/webhook",
    "events": ["trade_completed", "risk_alert"]
  },
  "internal_notifications": {
    "enabled": true,
    "desktop": true,
    "sound": true
  },
  "quiet_hours": {
    "enabled": false,
    "start": "22:00",
    "end": "08:00"
  },
  "frequency_limits": {
    "max_per_hour": 10,
    "max_per_day": 50
  },
  "updated_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (更新成功), 400 (参数错误), 401 (认证失败)

### 5. 站内消息接口

#### 5.1 获取站内消息
- **接口地址**: `GET /api/messages`
- **功能描述**: 获取用户站内消息
- **请求参数**:
  - `skip`: 跳过记录数 (默认: 0)
  - `limit`: 限制记录数 (默认: 100)
  - `status`: 状态筛选 (可选: unread, read, archived)
  - `type`: 消息类型筛选 (可选: system, trading, alert)
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "messages": [
    {
      "id": "msg_123",
      "title": "系统维护通知",
      "content": "系统将于今晚22:00-23:00进行维护",
      "type": "system",
      "priority": "high",
      "status": "unread",
      "created_at": "2023-01-01T00:00:00Z",
      "expires_at": "2023-01-02T00:00:00Z"
    }
  ],
  "total": 1,
  "unread_count": 1,
  "skip": 0,
  "limit": 100
}
```
- **状态码**: 200 (成功), 401 (认证失败)

#### 5.2 标记消息为已读
- **接口地址**: `PUT /api/messages/{message_id}/read`
- **功能描述**: 标记消息为已读
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "id": "msg_123",
  "title": "系统维护通知",
  "content": "系统将于今晚22:00-23:00进行维护",
  "type": "system",
  "priority": "high",
  "status": "read",
  "read_at": "2023-01-01T00:00:00Z",
  "created_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (标记成功), 401 (认证失败), 404 (消息不存在)

#### 5.3 删除消息
- **接口地址**: `DELETE /api/messages/{message_id}`
- **功能描述**: 删除消息
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "message": "消息删除成功"
}
```
- **状态码**: 200 (删除成功), 401 (认证失败), 404 (消息不存在)

### 6. 系统监控接口

#### 6.1 健康检查
- **接口地址**: `GET /health`
- **功能描述**: 系统健康检查
- **响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2023-01-01T00:00:00Z",
  "version": "2.0.0",
  "components": {
    "database": "connected",
    "redis": "connected",
    "email_service": "connected",
    "sms_service": "connected",
    "webhook_service": "running"
  },
  "queue_status": {
    "pending": 0,
    "processing": 0,
    "failed": 0,
    "total_processed": 1000
  },
  "service_status": {
    "email": "healthy",
    "sms": "healthy",
    "webhook": "healthy"
  }
}
```
- **状态码**: 200 (健康), 503 (服务异常)

#### 6.2 获取通知统计
- **接口地址**: `GET /api/statistics`
- **功能描述**: 获取通知发送统计
- **请求参数**:
  - `start_date`: 开始时间 (可选)
  - `end_date`: 结束时间 (可选)
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "period": {
    "start_date": "2023-01-01T00:00:00Z",
    "end_date": "2023-01-31T23:59:59Z"
  },
  "total_sent": 1500,
  "total_failed": 50,
  "success_rate": 96.7,
  "by_type": {
    "email": {
      "sent": 800,
      "failed": 20,
      "success_rate": 97.5
    },
    "sms": {
      "sent": 400,
      "failed": 15,
      "success_rate": 96.3
    },
    "webhook": {
      "sent": 300,
      "failed": 15,
      "success_rate": 95.0
    }
  },
  "by_template": {
    "trade_completed": 500,
    "risk_alert": 300,
    "system_error": 100
  },
  "delivery_times": {
    "average": 2.5,
    "min": 0.5,
    "max": 10.0
  }
}
```
- **状态码**: 200 (成功), 401 (认证失败)

## 错误处理

所有接口返回的错误格式：

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": {}
  }
}
```

常见错误码：
- `UNAUTHORIZED`: 认证失败
- `FORBIDDEN`: 权限不足
- `NOT_FOUND`: 资源不存在
- `VALIDATION_ERROR`: 参数验证失败
- `TEMPLATE_NOT_FOUND`: 模板不存在
- `NOTIFICATION_NOT_FOUND`: 通知不存在
- `MESSAGE_NOT_FOUND`: 消息不存在
- `EMAIL_SEND_FAILED`: 邮件发送失败
- `SMS_SEND_FAILED`: 短信发送失败
- `WEBHOOK_SEND_FAILED`: Webhook发送失败
- `INVALID_RECIPIENT`: 无效的接收者
- `TEMPLATE_RENDER_ERROR`: 模板渲染错误
- `RATE_LIMIT_EXCEEDED`: 发送频率限制
- `QUOTA_EXCEEDED`: 配额超出
- `SERVICE_UNAVAILABLE`: 服务不可用
- `INTERNAL_ERROR`: 服务器内部错误

## 认证方式

使用Bearer Token认证：

```http
Authorization: Bearer <access_token>
```

Token通过核心服务登录接口获取。