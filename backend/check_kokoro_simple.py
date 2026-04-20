"""简单的 Kokoro 检查脚本"""
import sys

print("检查 Kokoro TTS 导入...")

try:
    print("  尝试从 kokoro_onnx 导入 Kokoro...")
    from kokoro_onnx import Kokoro
    print("  ✓ 成功导入 Kokoro!")
except ImportError as e:
    print(f"  ✗ 导入失败: {e}")
    print("\n正在尝试导入 kokoro_tts 包...")
    try:
        import kokoro_tts
        print(f"  ✓ kokoro_tts 包存在! 位置: {kokoro_tts.__file__}")
        print("\n让我们查看包的内容...")
        from pathlib import Path
        pkg_dir = Path(kokoro_tts.__file__).parent
        print(f"  包目录: {pkg_dir}")
        print(f"  目录内容: {list(pkg_dir.iterdir())}")
    except Exception as e2:
        print(f"  ✗ 也失败: {e2}")

print("\n检查 soundfile...")
try:
    import soundfile as sf
    print("  ✓ soundfile 导入成功!")
except Exception as e:
    print(f"  ✗ 导入失败: {e}")

print("\n✓ 检查完成!")
