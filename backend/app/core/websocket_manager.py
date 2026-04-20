
"""
WebSocket 连接管理器
用于管理实时进度推送
"""

import asyncio
import json
from typing import Dict, Set
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}
        self.connection_locks: Dict[int, asyncio.Lock] = {}

    async def connect(self, project_id: int, websocket: WebSocket):
        """连接 WebSocket"""
        if project_id not in self.connection_locks:
            self.connection_locks[project_id] = asyncio.Lock()
        
        async with self.connection_locks[project_id]:
            if project_id not in self.active_connections:
                self.active_connections[project_id] = set()
            self.active_connections[project_id].add(websocket)

    def disconnect(self, project_id: int, websocket: WebSocket):
        """断开 WebSocket"""
        if project_id in self.active_connections:
            self.active_connections[project_id].discard(websocket)
            if not self.active_connections[project_id]:
                del self.active_connections[project_id]

    async def send_personal_message(self, message: dict, project_id: int):
        """发送消息给特定项目的所有连接"""
        if project_id not in self.active_connections:
            return
        
        # 创建一个列表来记录需要断开的连接
        to_disconnect = []
        
        for connection in self.active_connections[project_id]:
            try:
                await connection.send_json(message)
            except Exception:
                to_disconnect.append(connection)
        
        # 清理断开的连接
        for connection in to_disconnect:
            self.disconnect(project_id, connection)

    async def broadcast(self, message: dict):
        """广播消息给所有连接"""
        for project_id in list(self.active_connections.keys()):
            await self.send_personal_message(message, project_id)


manager = ConnectionManager()


async def send_progress_update(project_id: int, step_name: str, percentage: float, message: str, status: str = "running", eta: float = None):
    """
    发送进度更新
    
    Args:
        project_id: 项目ID
        step_name: 步骤名称
        percentage: 进度百分比
        message: 消息
        status: 状态
        eta: 预估剩余时间（秒）
    """
    progress_data = {
        "type": "progress",
        "project_id": project_id,
        "step_name": step_name,
        "percentage": percentage,
        "message": message,
        "status": status,
        "eta": eta
    }
    
    try:
        await manager.send_personal_message(progress_data, project_id)
    except Exception:
        pass  # 发送失败不影响工作流继续


async def send_step_complete(project_id: int, step_name: str, result: dict = None):
    """发送步骤完成消息"""
    complete_data = {
        "type": "step_complete",
        "project_id": project_id,
        "step_name": step_name,
        "status": "completed",
        "result": result
    }
    
    try:
        await manager.send_personal_message(complete_data, project_id)
    except Exception:
        pass


async def send_step_failed(project_id: int, step_name: str, error: str):
    """发送步骤失败消息"""
    failed_data = {
        "type": "step_failed",
        "project_id": project_id,
        "step_name": step_name,
        "status": "failed",
        "error": error
    }
    
    try:
        await manager.send_personal_message(failed_data, project_id)
    except Exception:
        pass

