# 使用nginx提供静态文件
FROM nginx:alpine

# 复制本地构建的文件到nginx
COPY build /usr/share/nginx/html

# 复制nginx配置
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动nginx
CMD ["nginx", "-g", "daemon off;"]