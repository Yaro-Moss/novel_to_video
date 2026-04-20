# 生产部署指南

本指南介绍如何在生产环境中部署 Novel to Video 应用。

## 前置要求

- Docker 和 Docker Compose 已安装
- 服务器配置建议：至少 4GB RAM，2 核 CPU
- 已配置域名（可选但推荐）

## 快速开始

### 1. 准备环境

```bash
# 复制环境变量模板
cp .env.prod.example .env.prod

# 编辑环境变量，填入实际值
nano .env.prod
```

### 2. 启动生产服务

```bash
# 使用生产配置启动
docker-compose -f docker-compose.prod.yml up -d

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

### 3. 初始化数据库

```bash
# 运行数据库迁移
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

## 服务说明

生产环境包含以下服务：

| 服务 | 端口 | 说明 |
|------|------|------|
| Nginx | 80, 443 | 反向代理和静态文件服务 |
| Frontend | - | React 前端应用 |
| Backend | 8000 | FastAPI 后端 API |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存和 Celery 队列 |
| Celery Worker | - | 异步任务处理 |

## Nginx 配置说明

### 路径代理

- `/` - 前端静态文件
- `/api/` - 后端 API
- `/ws/` - WebSocket 连接
- `/docs` - API 文档
- `/health` - 健康检查

### 文件上传限制

默认限制为 100MB，可在 `nginx.conf` 中修改：
```nginx
client_max_body_size 100M;
```

## 数据持久化

以下数据会持久化保存：

- PostgreSQL 数据：`postgres_data` volume
- Redis 数据：`redis_data` volume
- 上传和生成的文件：`./storage` 目录

## 升级部署

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose -f docker-compose.prod.yml up -d --build

# 运行数据库迁移
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

## 备份和恢复

### 数据库备份

```bash
# 备份 PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U novel2video novel2video > backup.sql
```

### 文件备份

```bash
# 备份存储文件
tar -czf storage_backup.tar.gz ./storage
```

## 监控和日志

### 查看服务状态

```bash
# 所有服务状态
docker-compose -f docker-compose.prod.yml ps

# 特定服务日志
docker-compose -f docker-compose.prod.yml logs -f backend
```

### 健康检查

```bash
# 后端健康检查
curl http://localhost/health
```

## 安全建议

1. **HTTPS 配置**：使用 Let's Encrypt 配置 SSL 证书
2. **防火墙**：只开放必要端口（80, 443）
3. **密码**：使用强密码和密钥
4. **定期更新**：保持系统和依赖库最新
5. **日志监控**：定期检查访问和错误日志

## 故障排查

### 服务无法启动

```bash
# 检查详细日志
docker-compose -f docker-compose.prod.yml logs

# 检查特定服务
docker-compose -f docker-compose.prod.yml logs backend
```

### 数据库连接问题

```bash
# 检查 PostgreSQL 状态
docker-compose -f docker-compose.prod.yml ps postgres

# 测试连接
docker-compose -f docker-compose.prod.yml exec postgres psql -U novel2video -d novel2video
```

## 停止和清理

```bash
# 停止服务
docker-compose -f docker-compose.prod.yml down

# 停止并删除数据（谨慎使用）
docker-compose -f docker-compose.prod.yml down -v
```
