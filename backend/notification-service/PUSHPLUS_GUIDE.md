# PushPlus 通知服务集成指南

## 📋 概述

PushPlus 是一个简单易用的微信消息推送服务，支持多种消息格式和群组推送。本指南详细介绍如何在 CashUp notification-service 中集成和使用 PushPlus。

## 🚀 快速开始

### 1. 获取 PushPlus Token

1. 访问 [PushPlus 官网](http://www.pushplus.plus/)
2. 使用微信扫码登录
3. 复制你的 token
4. 在项目的 `.env` 文件中配置：

```bash
PUSHPLUS_TOKEN=你的pushplus_token
```

### 2. 配置通知渠道

在 notification-service 中配置 PushPlus 渠道：

```python
# 渠道配置
channel_config = {
    "token": "your_pushplus_token",
    "topic": "your_topic_code"  # 可选，群组编码
}
```

### 3. 发送消息

```python
# 使用 SenderService 发送消息
result = await sender_service._send_pushplus(channel, notification, content)
```

## 🎨 支持的消息格式

### HTML 格式

```html
<h2>🚀 CashUp量化交易系统</h2>
<p><strong>订单状态:</strong> 执行成功</p>
<div style="background-color: #f0f8ff; padding: 10px;">
    <p>✅ 买入 BTCUSDT</p>
    <p>💰 价格: $50,000</p>
</div>
```

### Markdown 格式

```markdown
# 🚀 CashUp量化交易系统

## 📊 交易信息
- **合约**: BTCUSDT
- **方向**: 买入开仓
- **价格**: $50,000

> 交易执行成功
```

### JSON 格式

```json
{
  "system": "CashUp量化交易系统",
  "type": "订单通知",
  "data": {
    "symbol": "BTCUSDT",
    "side": "BUY",
    "price": 50000
  }
}
```

## 🔧 API 接口详情

### 请求地址
```
POST http://www.pushplus.plus/send
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| token | string | 是 | 用户令牌 |
| title | string | 是 | 消息标题 |
| content | string | 是 | 消息内容 |
| template | string | 否 | 消息模板，默认html |
| topic | string | 否 | 群组编码 |

### 响应格式

```json
{
  "code": 200,
  "msg": "执行成功",
  "data": "消息ID"
}
```

## 📱 在 notification-service 中的实现

### _send_pushplus 方法

```python
async def _send_pushplus(
    self, 
    channel: NotificationChannel, 
    notification: Notification, 
    content: Dict[str, Any]
) -> Dict[str, Any]:
    """
    发送PushPlus通知
    
    Args:
        channel: 通知渠道
        notification: 通知对象
        content: 发送内容
        
    Returns:
        Dict[str, Any]: 发送结果
    """
    # 获取配置
    token = channel.config.get('token')
    if not token:
        raise NotificationSendError("PushPlus token not configured")
    
    topic = channel.config.get('topic')  # 可选的群组编码
    
    # 准备消息内容
    title = content.get('subject', notification.title)
    message_content = content.get('content', notification.content)
    
    # 自动检测模板格式
    if message_content.strip().startswith('<') and message_content.strip().endswith('>'):
        template = "html"
    elif any(marker in message_content for marker in ['#', '**', '- [', '> ']):
        template = "markdown"
    else:
        template = "html"
    
    # 构建请求数据
    data = {
        "token": token,
        "title": title,
        "content": message_content,
        "template": template
    }
    
    if topic:
        data["topic"] = topic
    
    try:
        # 发送请求
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://www.pushplus.plus/send",
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                result = await response.json()
                
                if response.status == 200 and result.get("code") == 200:
                    return {
                        "message_id": result.get("data"),
                        "details": {
                            "template": template,
                            "topic": topic,
                            "response_msg": result.get("msg")
                        }
                    }
                else:
                    raise NotificationSendError(
                        f"PushPlus API error: {result.get('msg', 'Unknown error')}"
                    )
                    
    except aiohttp.ClientError as e:
        raise NotificationSendError(f"PushPlus request failed: {str(e)}")
    except Exception as e:
        raise NotificationSendError(f"PushPlus send failed: {str(e)}")
```

## 🧪 测试验证

### 运行测试脚本

```bash
# 运行完整的PushPlus测试
python pushplus_requests_test.py
```

### 测试结果示例

```
🚀 开始PushPlus API测试 (使用requests)
============================================================

✅ PUSHPLUS_TOKEN已配置: 60ad54690c...

=== 测试PushPlus HTML消息 ===
✅ HTML消息发送成功
   消息ID: 9ebdce1e933f42bca34da1d29b197600
   响应: 执行成功

=== 测试PushPlus Markdown消息 ===
✅ Markdown消息发送成功
   消息ID: 52633323e86b434f9f4e2e30814e50a7
   响应: 执行成功

=== 测试PushPlus JSON消息 ===
✅ JSON消息发送成功
   消息ID: c785d78fe8ce471ba938700b76add1f0
   响应: 执行成功

总体结果: 3/4 测试通过
🎉 PushPlus API基本功能测试通过！
```

## 📊 使用场景

### 1. 交易订单通知

```python
# HTML格式的订单通知
title = "📊 CashUp订单通知"
content = """
<h3>✅ 订单执行成功</h3>
<p><strong>合约:</strong> BTCUSDT</p>
<p><strong>方向:</strong> 买入开仓</p>
<p><strong>价格:</strong> $50,000</p>
<p><strong>数量:</strong> 0.1 BTC</p>
<p><strong>时间:</strong> 2024-01-15 14:30:00</p>
"""
```

### 2. 价格预警通知

```python
# Markdown格式的价格预警
title = "📈 CashUp价格预警"
content = """
# 🚨 价格预警触发

**BTCUSDT** 价格突破关键阻力位

## 📊 当前信息
- **当前价格**: $52,000
- **预警价格**: $50,000
- **涨幅**: +4.00%

> 💡 建议关注后续走势，考虑调整仓位
"""
```

### 3. 系统状态通知

```python
# JSON格式的系统状态
title = "🔔 CashUp系统状态"
content = json.dumps({
    "system": "CashUp量化交易系统",
    "timestamp": "2024-01-15T14:30:00Z",
    "status": {
        "trading_engine": "正常",
        "risk_management": "正常",
        "notification_service": "正常"
    },
    "metrics": {
        "active_strategies": 5,
        "daily_trades": 23,
        "system_uptime": "99.9%"
    }
}, ensure_ascii=False, indent=2)
```

## ⚠️ 注意事项

### 1. 频率限制
- PushPlus 有发送频率限制
- 建议在批量发送时添加适当的延迟
- 测试时每次发送间隔至少1秒

### 2. 消息长度
- 标题建议不超过100字符
- 内容建议不超过4096字符
- 过长的消息可能被截断

### 3. 模板选择
- HTML: 支持丰富的样式和格式
- Markdown: 简洁易读，支持基本格式
- JSON: 适合结构化数据展示

### 4. 群组推送
- 需要先创建群组并获取群组编码
- 群组编码配置在 `topic` 参数中
- 不配置 `topic` 则发送到个人

## 🔍 故障排查

### 常见错误

1. **Token 无效**
   ```
   错误: PushPlus API error: token无效
   解决: 检查 .env 文件中的 PUSHPLUS_TOKEN 配置
   ```

2. **网络连接失败**
   ```
   错误: PushPlus request failed: Connection timeout
   解决: 检查网络连接，确认防火墙设置
   ```

3. **服务端验证错误**
   ```
   错误: 服务端验证错误
   解决: 检查消息内容格式，避免特殊字符
   ```

### 调试建议

1. 使用测试脚本验证基本功能
2. 检查日志输出，确认请求参数
3. 测试不同的消息格式和长度
4. 确认 token 和群组编码的有效性

## 📚 相关资源

- [PushPlus 官网](http://www.pushplus.plus/)
- [PushPlus API 文档](http://www.pushplus.plus/doc/)
- [notification-service 项目文档](./README.md)

## 🎯 总结

PushPlus 集成为 CashUp 量化交易系统提供了可靠的微信消息推送能力：

✅ **已实现功能**
- 支持 HTML、Markdown、JSON 三种消息格式
- 自动检测消息格式并选择合适的模板
- 支持个人和群组消息推送
- 完整的错误处理和日志记录
- 异步发送，不阻塞主流程

✅ **测试验证**
- 基本 API 调用功能正常
- 多种消息格式发送成功
- 集成逻辑测试通过
- 错误处理机制有效

🚀 **使用建议**
- 配置合适的发送频率限制
- 根据消息类型选择合适的格式
- 定期检查 token 有效性
- 监控发送成功率和错误日志