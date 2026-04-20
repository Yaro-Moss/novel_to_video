# Kokoro TTS 集成指南

## 概述

项目现在支持两种 TTS（文本转语音）引擎：

1. **Edge TTS** (默认) - 免费、云端、无需安装额外依赖
2. **Kokoro TTS** - 本地、高质量、支持多种语音

## 安装依赖

要使用 Kokoro TTS，需要安装额外的包：

```bash
pip install kokoro-tts soundfile
```

或者使用项目的 requirements.txt（已更新）：

```bash
pip install -r requirements.txt
```

## 配置方法

### 在项目配置中选择引擎

在启动工作流时，通过配置参数指定：

```python
config = {
    "tts": {
        "voice": "af_heart",  # 或其他语音
        "engine": "kokoro"    # 或 "edge" (默认)
    }
}
```

### 可用语音

#### Edge TTS 语音
- `zh-CN-XiaoxiaoNeural` - 晓晓 (女声，默认)
- `zh-CN-YunxiNeural` - 云希 (男声)
- `zh-CN-YunjianNeural` - 云健 (男声)
- `zh-CN-XiaoyiNeural` - 晓伊 (女声)
- 以及更多...

#### Kokoro TTS 语音
- `af_heart` - Kokoro 女声1 (默认)
- `af_bella` - Kokoro 女声2
- `am_adam` - Kokoro 男声1
- `am_michael` - Kokoro 男声2

## 测试

运行测试脚本验证两种引擎：

```bash
cd backend
python test_tts.py
```

## 对比

| 特性 | Edge TTS | Kokoro TTS |
|------|----------|------------|
| 运行位置 | 云端 | 本地 |
| 网络要求 | 需要 | 不需要 |
| 模型大小 | 无需下载 | ~100MB |
| 语音质量 | 好 | 很好 |
| 支持语言 | 多 | 多 |
| 离线使用 | ❌ | ✅ |
| 安装依赖 | edge-tts | kokoro-tts + soundfile |

## 工作原理

1. **懒加载**: Kokoro 模型只在第一次使用时加载
2. **自动回退**: 如果 Kokoro 失败，自动回退到 Edge TTS
3. **音频格式**:
   - Edge TTS: 生成 `.mp3`
   - Kokoro TTS: 生成 `.wav`

## 常见问题

### Q: Kokoro 模型下载慢怎么办？
A: 模型会自动下载并缓存，首次运行较慢，之后很快。

### Q: 两种引擎可以同时使用吗？
A: 可以，但建议选择一种引擎以保持音频格式一致。

### Q: 如何完全禁用 Kokoro？
A: 不安装 kokoro-tts 包即可，系统会自动使用 Edge TTS。

## 示例使用

```python
from app.services.tts_service import TTSService

# 使用 Edge TTS
audio = await TTSService.synthesize(
    "你好世界",
    voice="zh-CN-XiaoxiaoNeural",
    engine="edge"
)

# 使用 Kokoro TTS
audio = await TTSService.synthesize(
    "你好世界",
    voice="af_heart",
    engine="kokoro"
)
```
