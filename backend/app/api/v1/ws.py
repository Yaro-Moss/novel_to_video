from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session

from app.core.websocket_manager import manager
from app.core.database import get_db
from app.models.project import Project

router = APIRouter()


@router.websocket("/ws/progress/{project_id}")
async def progress_websocket(websocket: WebSocket, project_id: int):
    """
    WebSocket 实时进度推送
    
    Args:
        websocket: WebSocket 连接
        project_id: 项目ID
    """
    try:
        await websocket.accept()
        
        # 连接管理
        await manager.connect(project_id, websocket)
        
        # 发送连接成功消息
        await websocket.send_json({
            "type": "connected",
            "project_id": project_id,
            "status": "connected"
        })
        
        # 持续接收消息（保持连接活跃）
        while True:
            try:
                data = await websocket.receive_json()
                # 可以在这里处理客户端消息，比如请求当前状态
                if data.get("action") == "get_status":
                    # TODO: 返回当前项目状态
                    pass
            except WebSocketDisconnect:
                break
            except Exception:
                break
                
    except Exception:
        pass
    finally:
        # 断开连接
        manager.disconnect(project_id, websocket)
        try:
            await websocket.close()
        except Exception:
            pass
