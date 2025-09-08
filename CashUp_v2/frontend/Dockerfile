FROM node:18-alpine as builder

# 设置工作目录
WORKDIR /app

# 复制package文件
COPY package*.json ./

# 安装依赖（包括开发依赖）
RUN npm ci

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 使用nginx提供静态文件
FROM nginx:alpine

# 复制构建的文件到nginx
COPY --from=builder /app/build /usr/share/nginx/html

# 复制nginx配置
COPY nginx/simple.conf /etc/nginx/nginx.conf

# 暴露端口
EXPOSE 3000

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]