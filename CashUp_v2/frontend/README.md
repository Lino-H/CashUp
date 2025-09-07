# CashUp 前端应用

## 环境配置

### 开发环境

1. 复制环境变量文件（如果需要）：
```bash
cp .env.example .env
```

2. 确保后端服务正在运行：
```bash
# 核心服务 (端口 8001)
cd ../core-service && python main.py

# 交易引擎 (端口 8002)
cd ../trading-engine && python main.py

# 策略平台 (端口 8003)
cd ../strategy-platform && python main.py

# 通知服务 (端口 8004)
cd ../notification-service && python main.py
```

3. 启动开发服务器：
```bash
npm start
```

### 生产环境

1. 修改 `.env` 文件为生产环境配置：
```bash
# API服务地址配置 - 生产环境
REACT_APP_API_URL=http://localhost:8001/api/v1
REACT_APP_TRADING_URL=http://localhost:8002/api/v1
REACT_APP_STRATEGY_URL=http://localhost:8003/api/v1
REACT_APP_NOTIFICATION_URL=http://localhost:8004/api/v1

# 生产环境配置
NODE_ENV=production
```

2. 构建生产版本：
```bash
npm run build
```

3. 部署到生产服务器：
```bash
# 使用Docker部署
cd ..
./deploy.sh
```

## 环境变量说明

### 环境变量
- `REACT_APP_API_URL` - 核心服务API地址
- `REACT_APP_TRADING_URL` - 交易引擎API地址
- `REACT_APP_STRATEGY_URL` - 策略平台API地址
- `REACT_APP_NOTIFICATION_URL` - 通知服务API地址
- `NODE_ENV` - 运行环境 (development/production)

### 开发环境默认值
- `REACT_APP_API_URL=http://localhost:8001`
- `REACT_APP_TRADING_URL=http://localhost:8002`
- `REACT_APP_STRATEGY_URL=http://localhost:8003`
- `REACT_APP_NOTIFICATION_URL=http://localhost:8004`
- `NODE_ENV=development`

### 生产环境默认值
- `REACT_APP_API_URL=https://api.cashup.com/api/v1`
- `REACT_APP_TRADING_URL=https://api.cashup.com/api/v1`
- `REACT_APP_STRATEGY_URL=https://api.cashup.com/api/v1`
- `REACT_APP_NOTIFICATION_URL=https://api.cashup.com/api/v1`
- `NODE_ENV=production`

## CORS 配置

### 开发环境
后端服务允许所有来源：`*`

### 生产环境
后端服务只允许特定域名：
- `https://cashup.com`
- `https://www.cashup.com`

## 部署说明

### Docker 部署
使用 `docker-compose.prod.yml` 进行生产环境部署：

```bash
# 构建并启动服务
docker-compose -f docker-compose.prod.yml up -d

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 停止服务
docker-compose -f docker-compose.prod.yml down
```

### 传统部署
1. 构建前端应用：
```bash
npm run build
```

2. 将 `build` 目录中的文件部署到Web服务器

3. 确保后端API服务在生产环境中运行，并配置正确的CORS策略

## 故障排除

### CORS 错误
确保后端服务配置了正确的CORS策略，允许前端域名访问。

### API 连接错误
检查环境变量中的API地址是否正确，确保后端服务正在运行。

### 生产环境构建失败
确保所有依赖项都已安装：
```bash
npm install
```

## 开发工具

- **React Developer Tools** - React组件调试
- **Redux DevTools** - 状态管理调试
- **Chrome DevTools** - 网络请求和性能分析