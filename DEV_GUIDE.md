# Novel to Video - 开发指南

> 本文档是项目的核心参考，包含架构、进度、API 设计和会话衔接信息。
> 新会话开始时，阅读此文档 + `progress.md` + `feature_list.json` 即可恢复上下文。

---

## 一、项目概述

**Novel to Video** 是一个将小说文本自动转换为视频的 Web 应用。用户上传 TXT 文件后，系统自动完成：文本分段 → TTS 语音合成 → AI 图像生成 → 视频段合成 → 视频拼接，最终输出完整视频。

### 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| ORM | SQLAlchemy |
| 数据库 | PostgreSQL |
| 缓存/队列 | Redis |
| 异步任务 | Celery |
| 数据库迁移 | Alembic |
| 测试 | pytest |
| 前端框架 | React 18 + TypeScript 5 |
| 构建工具 | Vite |
| 样式 | TailwindCSS 3.4 + Ant Design 5.12 |
| 数据请求 | React Query (TanStack Query) |
| 状态管理 | Zustand |
| 路由 | React Router |
| 国际化 | react-i18next |

---

## 二、项目结构

```
novel_to_video/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── api/v1/              # 路由层
│   │   │   ├── auth.py          # 认证 API
│   │   │   ├── projects.py      # 项目管理 API
│   │   │   ├── tts.py           # TTS 配置 API
│   │   │   ├── images.py        # 图像生成 API
│   │   │   ├── settings.py      # 设置 API
│   │   │   └── ws.py            # WebSocket
│   │   ├── models/              # SQLAlchemy 模型
│   │   │   ├── user.py          # User, ApiKey
│   │   │   ├── project.py       # Project
│   │   │   ├── task.py          # Task (含 retry_count)
│   │   │   └── settings.py      # Settings
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── services/            # 业务逻辑层
│   │   │   ├── text_import_service.py
│   │   │   ├── segmentation_service.py
│   │   │   └── tts_service.py
│   │   ├── workers/             # Celery 任务
│   │   │   ├── celery_app.py
│   │   │   └── tasks.py         # 6 步骤工作流
│   │   └── core/                # 配置/安全/依赖
│   │       ├── config.py        # Pydantic Settings
│   │       └── security.py      # JWT + bcrypt
│   ├── tests/                   # pytest 测试 (71 个用例)
│   ├── alembic/                 # 数据库迁移
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/          # 通用组件
│   │   ├── pages/               # 11 个页面
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   ├── ProjectList.tsx
│   │   │   ├── ProjectCreate.tsx
│   │   │   ├── ProjectDetail.tsx
│   │   │   ├── VideoResult.tsx
│   │   │   ├── Settings.tsx
│   │   │   ├── SegmentsPreview.tsx
│   │   │   ├── TTSConfig.tsx
│   │   │   ├── ImageConfig.tsx
│   │   │   └── VideoConfig.tsx
│   │   ├── services/api.ts      # Axios 实例 + 拦截器
│   │   ├── stores/              # Zustand 状态管理
│   │   │   ├── authStore.ts
│   │   │   ├── themeStore.ts
│   │   │   └── notificationStore.ts
│   │   ├── hooks/               # 自定义 Hooks
│   │   │   ├── useNotification.ts
│   │   │   ├── useProjectProgress.ts
│   │   │   └── useProjects.ts
│   │   ├── i18n/                # 国际化 (zh-CN, en-US)
│   │   ├── theme/               # 主题 (light/dark)
│   │   ├── types/project.ts     # TypeScript 类型
│   │   ├── App.tsx              # 路由 + 权限守卫 + 主题
│   │   └── main.tsx             # QueryProvider + i18n
│   └── package.json
├── docker-compose.yml           # 开发环境
├── docker-compose.prod.yml      # 生产环境
├── nginx.conf                   # 生产 Nginx 反向代理
├── feature_list.json            # 60 个功能清单及状态
├── progress.md                  # 开发进度日志
└── start-*.bat                  # 启动脚本
```

---

## 三、API 接口设计

### 认证
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/auth/register | 用户注册 |
| POST | /api/v1/auth/login | 用户登录 |
| POST | /api/v1/auth/refresh | 刷新 Token |
| GET | /api/v1/auth/me | 获取当前用户 |

### 项目管理
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/projects | 创建项目（上传 TXT） |
| GET | /api/v1/projects | 项目列表（分页/筛选/搜索） |
| GET | /api/v1/projects/{id} | 项目详情 |
| DELETE | /api/v1/projects/{id} | 删除项目 |
| PATCH | /api/v1/projects/{id}/config | 更新项目配置 |
| GET | /api/v1/projects/{id}/segments | 分段预览 |
| GET | /api/v1/projects/{id}/status | 项目状态查询 |

### 工作流控制
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/projects/{id}/start | 启动工作流 |
| POST | /api/v1/projects/{id}/cancel | 取消工作流 |
| POST | /api/v1/projects/{id}/retry | 重试工作流 |
| POST | /api/v1/projects/{id}/retry-step | 重试单个步骤 |

### 结果与导出
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/projects/{id}/video | 流式返回视频 |
| GET | /api/v1/projects/{id}/assets | 产出文件列表 |
| POST | /api/v1/projects/{id}/export | 创建导出任务 |
| GET | /api/v1/projects/{id}/export/{eid}/status | 导出状态 |
| GET | /api/v1/projects/{id}/export/{eid}/download | 下载导出 |

### TTS
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/tts/voices | 语音列表 |
| POST | /api/v1/tts/preview | 试听 |

### 设置
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/settings | 获取用户配置 |
| PATCH | /api/v1/settings | 更新配置 |
| POST | /api/v1/settings/api-keys | 添加 API Key |
| GET | /api/v1/settings/api-keys | Key 列表（脱敏） |

### WebSocket
| 路径 | 说明 |
|------|------|
| WS /api/v1/ws/progress/{id} | 实时进度推送 |

---

## 四、工作流引擎

6 步骤流水线（Celery 异步执行）：

1. **导入文本** — TextImportService，自动编码检测（UTF-8/GBK）
2. **智能分段** — SegmentationService，支持章节检测和参数配置
3. **TTS 语音合成** — TTSService (Edge TTS)，批量合成 + 进度回调
4. **图像生成** — ImageService (DALL-E) / SDWebUIService，提示词优化
5. **视频段合成** — VideoSegmentService，图片+音频→MP4
6. **视频拼接** — VideoConcatService，多段拼接为最终视频

错误处理：自动重试最多 3 次，间隔递增（1s/3s/5s），支持手动重试单个步骤。

---

## 五、开发进度

### 功能完成情况：60/60 (100%)

| 类别 | 数量 | 状态 |
|------|------|------|
| infrastructure (基础设施) | 12 | ✅ 全部完成 |
| auth (用户认证) | 5 | ✅ 全部完成 |
| project (项目管理) | 8 | ✅ 全部完成 |
| core (核心引擎) | 4 | ✅ 全部完成 |
| tts (语音合成) | 3 | ✅ 全部完成 |
| image (图像生成) | 4 | ✅ 全部完成 |
| video (视频处理) | 4 | ✅ 全部完成 |
| workflow (工作流) | 6 | ✅ 全部完成 |
| result (结果展示) | 5 | ✅ 全部完成 |
| settings (设置) | 3 | ✅ 全部完成 |
| frontend_infra (前端基础设施) | 6 | ✅ 全部完成 |

### 测试覆盖
- 后端：71 个 pytest 测试用例，全部通过
- 前端：npm run build 构建通过

### 关键里程碑
- Session 0: 项目初始化，创建 60 个功能清单
- Session 1-2: FEAT-001~002 项目骨架搭建
- Session 3: FEAT-003 数据库模型定义
- Session 2 (续): FEAT-004~010 配置管理 + 认证系统
- Session 3 (续): FEAT-011~020 项目管理 + 核心引擎 + TTS
- Session 4: FEAT-031~032 Celery 工作流集成
- Session 4 (续): FEAT-051~055 测试框架 + 主题国际化
- Session 1 (新): FEAT-056 错误处理和重试策略
- Session 2 (新): FEAT-057 全局配置 API
- Session 2 (续): FEAT-058 通知系统
- Session 3 (续): FEAT-059 批量导出 API
- Session 4 (续): FEAT-060 Nginx 生产部署

---

## 六、会话衔接指南

新会话开始时，按以下步骤恢复上下文：

1. **阅读本文档** — 了解项目架构和 API 设计
2. **阅读 `progress.md`** — 了解最近 3 个会话的工作内容
3. **阅读 `feature_list.json`** — 确认各功能状态（passes/blocked）
4. **运行 `git log --oneline -10`** — 查看最近提交
5. **确认应用能正常运行** — 启动前后端验证

### 当前状态
- 所有 60 个功能已完成
- 项目可通过 `docker-compose up` 一键启动
- 后端测试全部通过，前端构建正常

### 下一步建议
1. 配置 HTTPS（推荐 Let's Encrypt）
2. 配置备份策略
3. 配置监控和日志收集
4. 性能优化和压力测试
5. 用户文档和使用指南

---

## 七、本地开发启动

```bash
# 后端
cd novel_to_video/backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd novel_to_video/frontend
npm install
npm run dev

# Celery Worker
cd novel_to_video/backend
celery -A app.workers.celery_app worker --loglevel=info --pool=solo

# Docker 一键启动
cd novel_to_video
docker-compose up -d
```

### 环境变量
- 后端：参考 `backend/.env.example`
- 前端：参考 `frontend/.env.example`
- 生产：参考 `.env.prod.example`
