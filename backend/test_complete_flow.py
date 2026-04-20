"""测试完整的小说转视频流程"""
import sys
import requests
from pathlib import Path
import time

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

BASE_URL = "http://localhost:8000/api/v1"

# 测试用户信息
TEST_USERNAME = "testuser"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "testpass123"

# PDF 文件路径
PDF_PATH = Path("C:/Users/GodPrograms/Downloads/老藤筐里的时光.pdf")

def print_separator(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def test_register():
    """注册测试用户"""
    print_separator("1. 注册测试用户")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={
                "username": TEST_USERNAME,
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )
        if response.status_code == 200:
            print("✓ 注册成功")
            return response.json()
        elif response.status_code == 400 and "已存在" in response.json().get("detail", ""):
            print("⚠ 用户已存在，尝试登录")
            return None
        else:
            print(f"✗ 注册失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"✗ 注册异常: {e}")
        return None

def test_login():
    """登录"""
    print_separator("2. 登录")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": TEST_PASSWORD
            }
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 登录成功")
            return data["access_token"]
        else:
            print(f"✗ 登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"✗ 登录异常: {e}")
        return None

def test_create_project(token):
    """创建项目"""
    print_separator("3. 创建项目")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # 准备文件
        with open(PDF_PATH, "rb") as f:
            files = {"file": ("老藤筐里的时光.pdf", f, "application/pdf")}
            data = {"name": "测试项目 - 老藤筐里的时光"}
            
            response = requests.post(
                f"{BASE_URL}/projects/",
                headers=headers,
                files=files,
                data=data
            )
        
        if response.status_code == 201:
            project = response.json()
            print(f"✓ 项目创建成功！项目ID: {project['id']}")
            return project["id"]
        else:
            print(f"✗ 创建项目失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"✗ 创建项目异常: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_get_project(token, project_id):
    """获取项目信息"""
    print_separator("4. 获取项目信息")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/projects/{project_id}",
            headers=headers
        )
        if response.status_code == 200:
            project = response.json()
            print(f"✓ 项目信息获取成功")
            print(f"  - 项目名: {project['name']}")
            print(f"  - 状态: {project['status']}")
            print(f"  - 输入文件: {project['input_file']}")
            return project
        else:
            print(f"✗ 获取项目失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"✗ 获取项目异常: {e}")
        return None

def test_get_segments(token, project_id):
    """获取分段信息"""
    print_separator("5. 获取分段预览")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/projects/{project_id}/segments",
            headers=headers
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 分段获取成功")
            print(f"  - 总段数: {data['total_count']}")
            print(f"  - 总字符: {data['total_chars']}")
            if data['segments']:
                print(f"  - 第一段预览: {data['segments'][0]['text'][:50]}...")
            return data
        else:
            print(f"✗ 获取分段失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"✗ 获取分段异常: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_start_workflow(token, project_id):
    """启动工作流"""
    print_separator("6. 启动工作流")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            f"{BASE_URL}/projects/{project_id}/start",
            headers=headers,
            json={}
        )
        if response.status_code == 202:
            print("✓ 工作流启动成功")
            return True
        else:
            print(f"✗ 启动工作流失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ 启动工作流异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_monitor_status(token, project_id):
    """监控状态"""
    print_separator("7. 监控工作流状态")
    headers = {"Authorization": f"Bearer {token}"}
    
    max_wait = 600  # 最多等待10分钟
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(
                f"{BASE_URL}/projects/{project_id}/status",
                headers=headers
            )
            if response.status_code == 200:
                status = response.json()
                print(f"\n  状态: {status['status']}")
                print(f"  当前步骤: {status['current_step']}")
                print(f"  进度: {status['percentage']:.1f}%")
                print(f"  耗时: {status['elapsed_time']:.1f}s" if status['elapsed_time'] else "")
                
                if status['tasks']:
                    print("\n  任务详情:")
                    for task in status['tasks']:
                        print(f"    - {task['step_name']}: {task['status']}")
                        if task.get('error'):
                            print(f"      错误: {task['error']}")
                
                if status['status'] in ["completed", "failed"]:
                    return status
            
            time.sleep(5)
            
        except Exception as e:
            print(f"  查询状态异常: {e}")
            time.sleep(5)
    
    print("\n✗ 等待超时")
    return None

def main():
    print("=== 小说转视频完整流程测试 ===\n")
    
    # 检查 PDF 文件
    if not PDF_PATH.exists():
        print(f"✗ PDF 文件不存在: {PDF_PATH}")
        return
    
    # 注册或登录
    test_register()
    token = test_login()
    if not token:
        print("✗ 无法获取 token，测试终止")
        return
    
    # 创建项目
    project_id = test_create_project(token)
    if not project_id:
        print("✗ 无法创建项目，测试终止")
        return
    
    # 获取项目信息
    test_get_project(token, project_id)
    
    # 获取分段
    segments = test_get_segments(token, project_id)
    
    print_separator("测试完成（前几步）")
    print("✓ PDF导入和分段测试完成！")
    if segments:
        print(f"  共 {segments['total_count']} 个段落")
    print("\n下一步可以在浏览器中继续测试。")

if __name__ == "__main__":
    main()
