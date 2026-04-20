# 简单工作流模式（无 Redis/Celery）

## 什么是简单工作流模式？

简单工作流模式使用后台线程代替 Celery + Redis 来处理任务，不需要安装 Redis！

---

## 如何切换到简单工作流模式？

### 方法一：修改 API（临时方案）

编辑 `backend/app/api/v1/projects.py`，替换以下内容：

**原内容（完整版）：**
```python
from app.workers.tasks import start_full_workflow, import_text_task
from app.workers.celery_app import celery_app
```

**替换为（简单版）：**
```python
from app.workers.simple_workflow import start_simple_workflow, cancel_simple_workflow, is_workflow_running
```

同时需要修改 `start_workflow`、`cancel_workflow`、`retry_workflow` 等函数，使用简单工作流的调用方式。

### 方法二：我们准备好的版本

实际上，我们已经有完整的 `simple_workflow.py` 实现！你可以：

1. 查看 git 历史，恢复到简单工作流版本
2. 或者，创建一个配置文件来选择使用哪个工作流

---

## 简单工作流 vs 完整版对比

| 功能 | 简单工作流 | 完整版 |
|------|-----------|-------|
| 需要 Redis | ❌ | ✅ |
| 需要 Celery | ❌ | ✅ |
| 任务队列 | ❌ | ✅ |
| 自动重试 | ✅ | ✅ |
| 进度通知 | ✅ | ✅ |
| 可扩展性 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 适合场景 | 单用户/开发 | 生产/多用户 |

---

## 什么时候用哪个？

**使用简单工作流的情况：**
- 你只是想快速测试功能
- 你不想安装 Redis
- 单用户使用场景
- 本地开发和调试

**使用完整版的情况：**
- 生产环境
- 多用户场景
- 需要任务队列管理
- 需要更好的扩展性

---

## 快速测试简单工作流

如果你想试试简单工作流，我可以帮你快速切换！
