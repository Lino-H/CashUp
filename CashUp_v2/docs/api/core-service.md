# 核心服务 API 文档

## 服务概述

**服务名称**: Core Service  
**服务端口**: 8001  
**服务地址**: http://localhost:8001  
**API文档**: http://localhost:8001/docs  
**健康检查**: http://localhost:8001/health  

## 主要功能

- 用户认证和授权
- 用户管理
- 配置管理
- 系统监控
- 数据库操作

## 接口列表

### 1. 认证接口

#### 1.1 用户登录
- **接口地址**: `POST /api/auth/login`
- **功能描述**: 用户登录认证
- **请求参数**:
```json
{
  "username": "string",
  "password": "string"
}
```
- **响应示例**:
```json
{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "username": "string",
    "email": "string",
    "role": "admin"
  }
}
```
- **状态码**: 200 (成功), 401 (认证失败), 400 (参数错误)

#### 1.2 用户注册
- **接口地址**: `POST /api/auth/register`
- **功能描述**: 新用户注册
- **请求参数**:
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "full_name": "string",
  "phone": "string"
}
```
- **响应示例**:
```json
{
  "id": 1,
  "username": "string",
  "email": "string",
  "full_name": "string",
  "phone": "string",
  "role": "user",
  "is_active": true,
  "created_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 201 (创建成功), 400 (参数错误), 409 (用户已存在)

#### 1.3 用户登出
- **接口地址**: `POST /api/auth/logout`
- **功能描述**: 用户登出
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "message": "登出成功"
}
```
- **状态码**: 200 (成功), 401 (认证失败)

### 2. 用户管理接口

#### 2.1 获取用户列表
- **接口地址**: `GET /api/users/`
- **功能描述**: 获取用户列表（管理员权限）
- **请求参数**:
  - `skip`: 跳过记录数 (默认: 0)
  - `limit`: 限制记录数 (默认: 100)
  - `search`: 搜索关键词 (可选)
  - `role`: 用户角色筛选 (可选)
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "users": [
    {
      "id": 1,
      "username": "admin",
      "email": "admin@cashup.com",
      "full_name": "系统管理员",
      "role": "admin",
      "is_active": true,
      "created_at": "2023-01-01T00:00:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 100
}
```
- **状态码**: 200 (成功), 401 (认证失败), 403 (权限不足)

#### 2.2 获取用户详情
- **接口地址**: `GET /api/users/{user_id}`
- **功能描述**: 获取指定用户详情
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@cashup.com",
  "full_name": "系统管理员",
  "phone": "13800138000",
  "avatar": "https://example.com/avatar.jpg",
  "timezone": "Asia/Shanghai",
  "language": "zh-CN",
  "theme": "light",
  "role": "admin",
  "is_active": true,
  "is_verified": true,
  "last_login": "2023-01-01T12:00:00Z",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (成功), 401 (认证失败), 403 (权限不足), 404 (用户不存在)

#### 2.3 创建用户
- **接口地址**: `POST /api/users/`
- **功能描述**: 创建新用户（管理员权限）
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "full_name": "string",
  "phone": "string",
  "role": "user"
}
```
- **响应示例**:
```json
{
  "id": 2,
  "username": "string",
  "email": "string",
  "full_name": "string",
  "phone": "string",
  "role": "user",
  "is_active": true,
  "created_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 201 (创建成功), 400 (参数错误), 401 (认证失败), 403 (权限不足), 409 (用户已存在)

#### 2.4 更新用户
- **接口地址**: `PUT /api/users/{user_id}`
- **功能描述**: 更新用户信息
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "full_name": "string",
  "phone": "string",
  "timezone": "Asia/Shanghai",
  "language": "zh-CN",
  "theme": "light"
}
```
- **响应示例**:
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@cashup.com",
  "full_name": "string",
  "phone": "string",
  "timezone": "Asia/Shanghai",
  "language": "zh-CN",
  "theme": "light",
  "role": "admin",
  "is_active": true,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (更新成功), 400 (参数错误), 401 (认证失败), 403 (权限不足), 404 (用户不存在)

#### 2.5 删除用户
- **接口地址**: `DELETE /api/users/{user_id}`
- **功能描述**: 删除用户（管理员权限）
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "message": "用户删除成功"
}
```
- **状态码**: 200 (删除成功), 401 (认证失败), 403 (权限不足), 404 (用户不存在)

### 3. 当前用户接口

#### 3.1 获取当前用户信息
- **接口地址**: `GET /api/users/me`
- **功能描述**: 获取当前登录用户信息
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@cashup.com",
  "full_name": "系统管理员",
  "phone": "13800138000",
  "avatar": "https://example.com/avatar.jpg",
  "timezone": "Asia/Shanghai",
  "language": "zh-CN",
  "theme": "light",
  "role": "admin",
  "is_active": true,
  "is_verified": true,
  "last_login": "2023-01-01T12:00:00Z",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (成功), 401 (认证失败)

#### 3.2 更新当前用户信息
- **接口地址**: `PUT /api/users/me`
- **功能描述**: 更新当前用户信息
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "full_name": "string",
  "phone": "string",
  "timezone": "Asia/Shanghai",
  "language": "zh-CN",
  "theme": "light"
}
```
- **响应示例**:
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@cashup.com",
  "full_name": "string",
  "phone": "string",
  "timezone": "Asia/Shanghai",
  "language": "zh-CN",
  "theme": "light",
  "role": "admin",
  "is_active": true,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (更新成功), 400 (参数错误), 401 (认证失败)

#### 3.3 修改密码
- **接口地址**: `POST /api/users/me/change-password`
- **功能描述**: 修改当前用户密码
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "old_password": "string",
  "new_password": "string"
}
```
- **响应示例**:
```json
{
  "message": "密码修改成功"
}
```
- **状态码**: 200 (修改成功), 400 (原密码错误), 401 (认证失败)

### 4. 配置管理接口

#### 4.1 获取配置列表
- **接口地址**: `GET /api/config/`
- **功能描述**: 获取配置列表
- **请求参数**:
  - `skip`: 跳过记录数 (默认: 0)
  - `limit`: 限制记录数 (默认: 100)
  - `category`: 配置分类筛选 (可选)
  - `search`: 搜索关键词 (可选)
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "configs": [
    {
      "id": 1,
      "key": "system_name",
      "value": "CashUp v2",
      "description": "系统名称",
      "category": "system",
      "data_type": "string",
      "is_system": true,
      "is_encrypted": false,
      "user_id": null,
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

#### 4.2 获取配置详情
- **接口地址**: `GET /api/config/{config_id}`
- **功能描述**: 获取指定配置详情
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "id": 1,
  "key": "system_name",
  "value": "CashUp v2",
  "description": "系统名称",
  "category": "system",
  "data_type": "string",
  "is_system": true,
  "is_encrypted": false,
  "user_id": null,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (成功), 401 (认证失败), 403 (权限不足), 404 (配置不存在)

#### 4.3 创建配置
- **接口地址**: `POST /api/config/`
- **功能描述**: 创建新配置
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "key": "string",
  "value": "string",
  "description": "string",
  "category": "user",
  "data_type": "string",
  "is_system": false,
  "is_encrypted": false
}
```
- **响应示例**:
```json
{
  "id": 2,
  "key": "string",
  "value": "string",
  "description": "string",
  "category": "user",
  "data_type": "string",
  "is_system": false,
  "is_encrypted": false,
  "user_id": 1,
  "created_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 201 (创建成功), 400 (参数错误), 401 (认证失败), 403 (权限不足), 409 (配置键已存在)

#### 4.4 更新配置
- **接口地址**: `PUT /api/config/{config_id}`
- **功能描述**: 更新配置
- **请求头**: `Authorization: Bearer <token>`
- **请求参数**:
```json
{
  "value": "string",
  "description": "string"
}
```
- **响应示例**:
```json
{
  "id": 1,
  "key": "system_name",
  "value": "string",
  "description": "string",
  "category": "system",
  "data_type": "string",
  "is_system": true,
  "is_encrypted": false,
  "user_id": null,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (更新成功), 400 (参数错误), 401 (认证失败), 403 (权限不足), 404 (配置不存在)

#### 4.5 删除配置
- **接口地址**: `DELETE /api/config/{config_id}`
- **功能描述**: 删除配置
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "message": "配置删除成功"
}
```
- **状态码**: 200 (删除成功), 401 (认证失败), 403 (权限不足), 404 (配置不存在)

#### 4.6 根据键获取配置
- **接口地址**: `GET /api/config/by-key/{key}`
- **功能描述**: 根据配置键获取配置
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "id": 1,
  "key": "system_name",
  "value": "CashUp v2",
  "description": "系统名称",
  "category": "system",
  "data_type": "string",
  "is_system": true,
  "is_encrypted": false,
  "user_id": null,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```
- **状态码**: 200 (成功), 401 (认证失败), 403 (权限不足), 404 (配置不存在)

### 5. 系统监控接口

#### 5.1 健康检查
- **接口地址**: `GET /health`
- **功能描述**: 系统健康检查
- **响应示例**:
```json
{
  "status": "healthy",
  "timestamp": "2023-01-01T00:00:00Z",
  "version": "2.0.0",
  "database": "connected",
  "redis": "connected"
}
```
- **状态码**: 200 (健康), 503 (服务异常)

#### 5.2 系统信息
- **接口地址**: `GET /api/system/info`
- **功能描述**: 获取系统信息
- **请求头**: `Authorization: Bearer <token>`
- **响应示例**:
```json
{
  "version": "2.0.0",
  "name": "CashUp v2",
  "description": "量化交易系统",
  "environment": "development",
  "start_time": "2023-01-01T00:00:00Z",
  "uptime": 3600,
  "components": {
    "database": "connected",
    "redis": "connected",
    "core_service": "running",
    "trading_engine": "connected",
    "strategy_platform": "connected",
    "notification_service": "connected"
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
- `INTERNAL_ERROR`: 服务器内部错误

## 认证方式

使用Bearer Token认证：

```http
Authorization: Bearer <access_token>
```

Token通过登录接口获取，有效期1小时。