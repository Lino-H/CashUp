#!/bin/bash

# 批量更新微服务Dockerfile
services=("strategy-service" "market-service" "notification-service" "order-service" "config-service" "monitoring-service")

for service in "${services[@]}"; do
    echo "Updating $service/Dockerfile..."
    cp Dockerfile.template "$service/Dockerfile"
done

echo "All Dockerfiles updated!"