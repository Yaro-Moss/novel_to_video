# 本地开发环境快速启动指南

## 前置要求

1. **Python 3.8+**
2. **Node.js 18+**
3. **Redis**（用于 Celery 消息队列）

---

## 快速启动（完整流程）

### 1. 安装 Redis（Windows）

#### 方法一：使用 Docker（推荐）
```bash
docker run -d -p 6379:6379 redis
```

#### 方法二：使用 Memurai（Windows 上的 Redis 兼容版本）
下载并安装：https://www.memurai.com/get-memurai

#### 方法三：使用 Redis for Windows（已不再更新，但可使用）
下载：https://github.com/microsoftarchive/redis/releases

启动 Redis：
```bash
# 进入 Redis 安装目录
redis-server
```

### 2. 初始化后端

```bash
cd backend
pip install -r requirements.txt

# 初始化数据库（会创建 SQLite 数据库）
python init_db.py
```

### 3. 启动服务（需要三个命令行窗口）

**窗口1 - 启动 Redis**（已用 docker 或 memurai 启动的可跳过）：
```bash
redis-server
```

**窗口2 - 启动 Celery Worker**（处理异步任务）：
```bash
cd backend
python -m celery -A app.workers.celery_app worker --loglevel=INFO --concurrency=1 --pool=solo
```

**窗口3 - 启动 FastAPI 后端**：
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**窗口4 - 启动前端**：
```bash
cd frontend
npm install  # 首次运行
npm run dev
```

---

## 使用便捷脚本（Windows）

我们提供了 `.bat` 脚本简化启动流程：

1. **启动后端**（会自动初始化数据库）：
   ```
   start-backend.bat
   ```

2. **启动 Worker**：
   ```
   start-worker.bat
   ```

3. **启动前端**：
   ```
   start-frontend.bat
   ```

---

## 使用 Docker Compose（最简单）

如果你有 Docker，这是最简单的方式！

```bash
# 一键启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

## 访问应用

- **前端**：http://localhost:5173
- **后端 API**：http://localhost:8000
- **API 文档**：http://localhost:8000/docs

---

## 配置 API Key

1. 注册/登录账号
2. 进入"设置"或"API Key"页面
3. 添加你的 OpenAI/火山方舟/Stable Diffusion 等 API Key

---

## 工作流说明

项目使用完整的 6 步骤工作流：

1. **Import** - 导入文本
2. **Segmentation** - 智能分段
3. **TTS** - 语音合成
4. **Image Generation** - 图像生成
5. **Video Segments** - 视频段生成
6. **Video Concat** - 视频拼接

所有步骤都支持自动重试，任务失败后会自动重试最多 3 次。
