# Novel to Video (小说转视频)

将小说/叙事文本自动转换为完整视频的全栈 Web 应用。上传 TXT、PDF 或 DOCX 文件，系统自动完成文本导入、智能分段、语音合成、图像生成、视频合成，最终输出一部完整的视频作品。

---

## 功能特点

- **支持多种输入格式**：TXT（自动检测编码）、PDF、DOCX
- **智能文本分段**：自动识别章节标题，支持自定义分段参数
- **双引擎 TTS**：支持 Edge TTS（云端）和 Kokoro TTS（本地/ONNX）
- **多引擎图像生成**：支持 DALL·E 3、火山方舟（doubao-seedream）、Stable Diffusion WebUI
- **提示词增强**：自动将中文提示词翻译为英文，支持多种画面风格
- **视频合成**：支持淡入淡出转场、硬字幕烧录
- **双工作流模式**：简单线程模式（无需 Redis/Celery）和 Celery 分布式模式
- **实时进度推送**：WebSocket 实时推送任务进度
- **用户系统**：JWT 认证、API Key 加密存储
- **国际化**：支持中文和英文界面
- **Docker 部署**：一键启动开发/生产环境

---

## 技术栈

| 层级 | 技术 |
|------|------|
| **后端框架** | FastAPI (Python 3.12) |
| **ORM** | SQLAlchemy 2.0+ |
| **数据库** | PostgreSQL（生产）/ SQLite（开发） |
| **缓存/队列** | Redis |
| **异步任务** | Celery / 内置线程池 |
| **数据库迁移** | Alembic |
| **前端框架** | React 18 + TypeScript 5 |
| **构建工具** | Vite |
| **CSS** | TailwindCSS 3.4 |
| **UI 组件库** | Ant Design 5.12 |
| **数据请求** | TanStack Query (React Query) |
| **状态管理** | Zustand |
| **路由** | React Router v6 |
| **国际化** | react-i18next（中文/英文） |
| **部署** | Docker Compose + Nginx |
| **视频处理** | FFmpeg |
| **测试** | pytest + pytest-asyncio（71 项测试） |

---

## 工作流程

项目使用完整的 6 步骤工作流，每一步都支持自动重试（最多 3 次）：

```
上传文件 → [1. 文本导入] → [2. 智能分段] → [3. 语音合成] → [4. 图像生成] → [5. 视频段合成] → [6. 视频拼接] → 输出视频
```

### 步骤详解

**1. 文本导入（Import）**
- 自动检测文件编码（UTF-8、GBK 等）
- 支持 TXT、PDF、DOCX 格式解析
- 返回纯文本内容和元数据

**2. 智能分段（Segmentation）**
- 正则检测中文章节标题（第X章、Chapter X 等）
- 支持配置最小/最大段落长度
- 自动合并过短段落

**3. 语音合成（TTS）**
- **Edge TTS**：微软云端 TTS，音质高，支持多种语音和语速/音调调节
- **Kokoro TTS**：本地 ONNX 模型，无需网络，完全离线运行
- 批量合成，失败时自动降级为静音音频

**4. 图像生成（Image Generation）**
- **DALL·E 3**：OpenAI 高质量图像生成
- **火山方舟**：doubao-seedream 模型，国内可用
- **Stable Diffusion WebUI**：本地部署，完全免费
- 提示词增强：中文→英文翻译 + 风格修饰词

**5. 视频段合成（Video Segment）**
- 将每段音频 + 对应图像合成为 MP4 视频片段
- FFmpeg 编码，支持淡入淡出效果

**6. 视频拼接（Video Concat）**
- 支持 concat demuxer（快速、不重新编码）和 filter_complex（重新编码保证兼容性）
- 可选的片段间转场效果
- 可选的硬字幕烧录

---

## 快速开始

### 方式一：Docker Compose（推荐）

```bash
# 一键启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 方式二：本地开发

详见 [LOCAL_SETUP.md](LOCAL_SETUP.md)，或使用快捷脚本：

```bash
# 窗口1 - 启动后端
start-backend.bat

# 窗口2 - 启动 Worker（仅 Celery 模式需要）
start-worker.bat

# 窗口3 - 启动前端
start-frontend.bat
```

### 访问应用

| 服务 | 地址 |
|------|------|
| 前端界面 | http://localhost:5173 |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |

---

## 项目结构

```
novel_to_video/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI 入口
│   │   ├── core/
│   │   │   ├── config.py              # 配置管理
│   │   │   ├── database.py            # 数据库连接
│   │   │   ├── security.py            # JWT + 密码加密
│   │   │   ├── logging.py             # 日志配置
│   │   │   └── websocket_manager.py   # WebSocket 连接管理
│   │   ├── api/v1/                    # API 路由
│   │   │   ├── auth.py                # 用户认证
│   │   │   ├── projects.py            # 项目管理 & 工作流控制
│   │   │   ├── tts.py                 # TTS 语音
│   │   │   ├── images.py             # 图像生成
│   │   │   ├── settings.py            # 用户设置
│   │   │   └── ws.py                  # WebSocket 进度推送
│   │   ├── models/                    # 数据模型
│   │   │   ├── user.py
│   │   │   ├── project.py
│   │   │   ├── task.py
│   │   │   ├── api_key.py
│   │   │   └── settings.py
│   │   ├── schemas/                   # Pydantic 请求/响应模型
│   │   ├── services/                  # 业务逻辑
│   │   │   ├── text_import_service.py # 文本导入
│   │   │   ├── segmentation_service.py# 智能分段
│   │   │   ├── tts_service.py         # 语音合成
│   │   │   ├── dalle_service.py       # DALL·E 图像
│   │   │   ├── sd_webui_service.py    # SD WebUI 图像
│   │   │   ├── ark_service.py         # 火山方舟图像
│   │   │   ├── prompt_service.py      # 提示词增强
│   │   │   ├── video_segment_service.py  # 视频段合成
│   │   │   ├── video_concat_service.py   # 视频拼接
│   │   │   ├── subtitle_service.py    # 字幕生成
│   │   │   └── api_key_service.py     # API Key 管理
│   │   └── workers/                   # 工作流引擎
│   │       ├── celery_app.py          # Celery 配置
│   │       ├── tasks.py               # Celery 任务
│   │       └── simple_workflow.py     # 简单线程工作流
│   ├── tests/                         # 71 项 pytest 测试
│   ├── alembic/                       # 数据库迁移
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/                     # 11 个页面
│   │   ├── components/                # 共享组件
│   │   ├── services/api.ts            # API 客户端
│   │   ├── stores/                    # Zustand 状态
│   │   ├── hooks/                     # 自定义 Hooks
│   │   └── i18n/locales/              # 国际化
│   └── Dockerfile
├── docker-compose.yml                 # 开发环境
├── docker-compose.prod.yml            # 生产环境
└── nginx.conf                         # Nginx 反向代理
```

---

## 配置说明

通过环境变量或 `.env` 文件配置，主要配置项：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接 | sqlite:///./novel_to_video.db |
| `REDIS_URL` | Redis 连接 | redis://localhost:6379/0 |
| `WORKFLOW_MODE` | 工作流模式（simple/celery） | simple |
| `OPENAI_API_KEY` | OpenAI API Key | - |
| `ARK_API_KEY` | 火山方舟 API Key | - |
| `SD_WEBUI_URL` | SD WebUI 地址 | http://localhost:7860 |
| `SECRET_KEY` | JWT 密钥 | 自动生成 |
| `STORAGE_DIR` | 文件存储目录 | ./storage |

完整配置项参见 `backend/app/core/config.py`。

---

## 部署

- **Docker 生产部署**：参考 `docker-compose.prod.yml` 和 `DEPLOYMENT.md`
- **Nginx 配置**：`nginx.conf` 已包含反向代理、WebSocket 升级、静态文件服务
- **生产环境变量模板**：`.env.prod.example`

---

## 开发指南

- [DEV_GUIDE.md](DEV_GUIDE.md) — 开发者指南
- [LOCAL_SETUP.md](LOCAL_SETUP.md) — 本地环境搭建
- [SIMPLE_WORKFLOW.md](SIMPLE_WORKFLOW.md) — 简单工作流模式说明
- [KOKORO_TTS_GUIDE.md](KOKORO_TTS_GUIDE.md) — Kokoro TTS 本地部署
- [DEPLOYMENT.md](DEPLOYMENT.md) — 生产部署

---

## 测试

```bash
cd backend
python -m pytest tests/ -v --tb=short
```

包含 71 项测试，覆盖认证、模型、项目 CRUD、工作流、重试机制、导出 API、设置 API。

---

## License

MIT
