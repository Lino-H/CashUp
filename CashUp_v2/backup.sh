#!/bin/bash
set -e

echo "💾 CashUp v2.0 数据备份脚本"
echo "================================"

# 创建备份目录
BACKUP_DIR="backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="cashup_backup_${DATE}"

mkdir -p ${BACKUP_DIR}

echo "📅 备份时间: $(date)"
echo "📁 备份目录: ${BACKUP_DIR}/${BACKUP_NAME}"

# 检查容器状态
if ! docker-compose ps | grep -q "cashup_postgres.*Up"; then
    echo "❌ PostgreSQL容器未运行"
    exit 1
fi

# 创建数据库备份
echo "🗄️  备份数据库..."
docker exec cashup_postgres pg_dump -U cashup -d cashup --verbose > ${BACKUP_DIR}/${BACKUP_NAME}.sql

# 备份配置文件
echo "⚙️  备份配置文件..."
mkdir -p ${BACKUP_DIR}/${BACKUP_NAME}_config
cp docker-compose.yml ${BACKUP_DIR}/${BACKUP_NAME}_config/
cp -r scripts/ ${BACKUP_DIR}/${BACKUP_NAME}_config/
cp -r frontend/nginx/ ${BACKUP_DIR}/${BACKUP_NAME}_config/
cp .env ${BACKUP_DIR}/${BACKUP_NAME}_config/ 2>/dev/null || echo "  (未找到.env文件，跳过)"

# 备份用户数据（策略代码等）
echo "📊 备份用户数据..."
if [ -d "strategies" ]; then
    cp -r strategies/ ${BACKUP_DIR}/${BACKUP_NAME}_config/
fi

# 创建压缩包
echo "🗜️  创建压缩包..."
cd ${BACKUP_DIR}
tar -czf ${BACKUP_NAME}.tar.gz ${BACKUP_NAME}.sql ${BACKUP_NAME}_config/
rm -rf ${BACKUP_NAME}.sql ${BACKUP_NAME}_config/
cd ..

# 获取备份文件大小
BACKUP_SIZE=$(du -h ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz | cut -f1)

echo "✅ 备份完成！"
echo "📦 备份文件: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
echo "📏 文件大小: ${BACKUP_SIZE}"
echo ""

# 清理旧备份（保留最近7天）
echo "🧹 清理旧备份文件（保留最近7天）..."
find ${BACKUP_DIR} -name "cashup_backup_*.tar.gz" -mtime +7 -delete 2>/dev/null || true

echo "🎉 备份脚本执行完成！"
echo ""
echo "💡 恢复方法:"
echo "   1. 停止服务: docker-compose down"
echo "   2. 解压备份: tar -xzf ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
echo "   3. 恢复数据库: docker exec -i cashup_postgres psql -U cashup -d cashup < ${BACKUP_NAME}.sql"
echo "   4. 恢复配置文件并重启服务"