"""
测试 TTS 服务 - Edge TTS 和 Kokoro TTS
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.tts_service import TTSService


async def test_edge_tts():
    """测试 Edge TTS"""
    print("\n=== 测试 Edge TTS ===")
    
    try:
        # 获取语音列表
        voices = await TTSService.get_voices(engine=TTSService.TTS_ENGINE_EDGE)
        print(f"找到 {len(voices)} 个语音")
        
        # 测试合成
        test_text = "你好，这是 Edge TTS 的测试语音。"
        output_path = Path("test_edge_output.mp3")
        
        print(f"正在合成: {test_text}")
        result = await TTSService.synthesize_to_file(
            text=test_text,
            output_path=output_path,
            voice="zh-CN-XiaoxiaoNeural",
            engine=TTSService.TTS_ENGINE_EDGE
        )
        
        print(f"✓ 成功生成: {result['file_path']} ({result['file_size']} bytes)")
        return True
    except Exception as e:
        print(f"✗ Edge TTS 测试失败: {e}")
        return False


async def test_kokoro_tts():
    """测试 Kokoro TTS"""
    print("\n=== 测试 Kokoro TTS ===")
    
    try:
        # 检查是否可用
        try:
            from kokoro_onnx import Kokoro
        except ImportError:
            print("⚠ Kokoro TTS 未安装，跳过测试")
            print("  请运行: pip install kokoro-tts soundfile")
            return False
        
        # 获取语音列表
        voices = await TTSService.get_voices(engine=TTSService.TTS_ENGINE_KOKORO)
        print(f"找到 {len(voices)} 个语音")
        for v in voices:
            print(f"  - {v['name']} ({v['id']})")
        
        # 测试合成
        test_text = "你好，这是 Kokoro TTS 的测试语音。"
        output_path = Path("test_kokoro_output.wav")
        
        print(f"\n正在合成: {test_text}")
        print("(第一次可能需要下载模型，请稍候...)")
        result = await TTSService.synthesize_to_file(
            text=test_text,
            output_path=output_path,
            voice="af_heart",
            engine=TTSService.TTS_ENGINE_KOKORO
        )
        
        print(f"✓ 成功生成: {result['file_path']} ({result['file_size']} bytes)")
        return True
    except Exception as e:
        print(f"✗ Kokoro TTS 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    print("=" * 50)
    print("TTS 服务测试")
    print("=" * 50)
    
    # 测试 Edge TTS
    edge_ok = await test_edge_tts()
    
    # 测试 Kokoro TTS
    kokoro_ok = await test_kokoro_tts()
    
    # 总结
    print("\n" + "=" * 50)
    print("测试总结:")
    print(f"  - Edge TTS: {'✓ 通过' if edge_ok else '✗ 失败'}")
    print(f"  - Kokoro TTS: {'✓ 通过' if kokoro_ok else '✗ 失败/跳过'}")
    print("=" * 50)
    
    print("\n提示:")
    print("- 在项目配置中，可以通过 tts.engine 参数选择使用 'edge' 或 'kokoro'")
    print("- Kokoro TTS 在本地运行，质量更高，但需要下载模型")
    print("- Edge TTS 免费且无需安装，但需要网络连接")


if __name__ == "__main__":
    asyncio.run(main())
