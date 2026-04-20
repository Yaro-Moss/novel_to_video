"""检查 Kokoro TTS 是否可用"""
import sys
import importlib.util

print("=" * 50)
print("检查 Kokoro TTS 安装")
print("=" * 50)

# 检查 kokoro 包
try:
    print("\n1. 检查 kokoro 包...")
    import kokoro
    print("   ✓ kokoro 导入成功")
    print(f"   位置: {kokoro.__file__}")
except ImportError as e:
    print(f"   ✗ kokoro 导入失败: {e}")
    print("\n尝试通过 pip install kokoro-tts 重新安装")
    sys.exit(1)

# 检查 soundfile
try:
    print("\n2. 检查 soundfile 包...")
    import soundfile as sf
    print("   ✓ soundfile 导入成功")
except ImportError as e:
    print(f"   ✗ soundfile 导入失败: {e}")
    print("\n尝试通过 pip install soundfile 重新安装")
    sys.exit(1)

# 尝试简单使用
try:
    print("\n3. 尝试初始化 Kokoro...")
    print("   (第一次可能需要下载模型)")
    from kokoro import Kokoro
    k = Kokoro()
    print("   ✓ Kokoro 初始化成功!")
    
    print("\n4. 获取可用语音...")
    voices = list(k.voices.keys())
    print(f"   ✓ 找到 {len(voices)} 个语音:")
    for v in voices[:8]:
        print(f"      - {v}")
    if len(voices) > 8:
        print(f"      ... 还有 {len(voices) - 8} 个")
        
    print("\n" + "=" * 50)
    print("✓ Kokoro TTS 检查完成!")
    print("=" * 50)
        
except Exception as e:
    print(f"   ✗ Kokoro 初始化失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
