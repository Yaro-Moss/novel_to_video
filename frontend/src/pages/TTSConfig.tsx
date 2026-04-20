import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Layout,
  Card,
  Select,
  Slider,
  Button,
  Typography,
  Space,
  Input,
  App,
  Spin,
  Divider,
} from 'antd';
import { LeftOutlined, SoundOutlined, SaveOutlined } from '@ant-design/icons';
import type { Voice, TTSConfig } from '../types/project';
import { ttsApi, projectApi } from '../services/api';

const { Header, Content } = Layout;
const { Title, Text } = Typography;
const { TextArea } = Input;

export default function TTSConfig() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { message } = App.useApp();
  const audioRef = useRef<HTMLAudioElement | null>(null);
  
  const [loading, setLoading] = useState(false);
  const [voices, setVoices] = useState<Voice[]>([]);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewText, setPreviewText] = useState('这是一个语音合成的测试样例。');
  
  const [config, setConfig] = useState<TTSConfig>({
    voice: 'zh-CN-XiaoxiaoNeural',
    rate: '+0%',
    volume: '+0%',
    pitch: '+0Hz',
  });

  const projectId = parseInt(id || '0', 10);

  const loadVoices = async () => {
    setLoading(true);
    try {
      const response = await ttsApi.getVoices();
      setVoices(response.data.data);
    } catch (error) {
      message.error('加载语音列表失败');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVoices();
  }, []);

  const handlePreview = async () => {
    if (!previewText.trim()) {
      message.warning('请输入预览文本');
      return;
    }
    
    setPreviewLoading(true);
    try {
      const response = await ttsApi.previewTTS({
        text: previewText,
        ...config,
      });
      
      // 创建音频 URL 并播放
      const audioUrl = URL.createObjectURL(new Blob([response.data], { type: 'audio/mpeg' }));
      if (audioRef.current) {
        audioRef.current.src = audioUrl;
        audioRef.current.play();
      }
      message.success('预览播放中...');
    } catch (error) {
      message.error('预览失败');
      console.error(error);
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleSave = async () => {
    if (!projectId) return;
    
    try {
      await projectApi.updateProjectConfig(projectId, {
        tts: config,
      });
      message.success('配置已保存');
    } catch (error) {
      message.error('保存配置失败');
      console.error(error);
    }
  };

  // 语速转换：百分比 <-> 滑块值
  const rateToSlider = (rate: string) => {
    const match = rate.match(/([+-]?\d+)%/);
    if (match) {
      return parseInt(match[1], 10) + 100; // -100% -> 0, 0% -> 100, +100% -> 200
    }
    return 100;
  };

  const sliderToRate = (value: number) => {
    const percent = value - 100;
    return `${percent >= 0 ? '+' : ''}${percent}%`;
  };

  // 音量转换
  const volumeToSlider = (volume: string) => {
    const match = volume.match(/([+-]?\d+)%/);
    if (match) {
      return parseInt(match[1], 10) + 100;
    }
    return 100;
  };

  const sliderToVolume = (value: number) => {
    const percent = value - 100;
    return `${percent >= 0 ? '+' : ''}${percent}%`;
  };

  // 音调转换
  const pitchToSlider = (pitch: string) => {
    const match = pitch.match(/([+-]?\d+)Hz/);
    if (match) {
      return parseInt(match[1], 10) + 100; // -100Hz -> 0, 0Hz -> 100, +100Hz -> 200
    }
    return 100;
  };

  const sliderToPitch = (value: number) => {
    const hz = value - 100;
    return `${hz >= 0 ? '+' : ''}${hz}Hz`;
  };

  const filteredVoices = voices.filter(v => v.language.startsWith('zh'));
  const femaleVoices = filteredVoices.filter(v => v.gender === 'Female');
  const maleVoices = filteredVoices.filter(v => v.gender === 'Male');

  // 构建选项列表
  const voiceOptions = [
    ...(femaleVoices.length > 0 ? [{ value: 'female-group', label: '女声', disabled: true }] : []),
    ...femaleVoices.map(voice => ({ value: voice.id, label: voice.name })),
    ...(maleVoices.length > 0 ? [{ value: 'male-group', label: '男声', disabled: true }] : []),
    ...maleVoices.map(voice => ({ value: voice.id, label: voice.name })),
  ];

  return (
    <Layout className="min-h-screen">
      <Header className="bg-white px-6 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-4">
          <Button
            type="text"
            icon={<LeftOutlined />}
            onClick={() => navigate('/projects')}
          >
            返回
          </Button>
          <Title level={4} className="m-0">TTS 配置</Title>
        </div>
        <Button
          type="primary"
          icon={<SaveOutlined />}
          onClick={handleSave}
        >
          保存配置
        </Button>
      </Header>

      <Content className="p-6">
        <div className="max-w-3xl mx-auto">
          <Spin spinning={loading}>
            <Card className="mb-6">
              <Space direction="vertical" size="large" className="w-full">
                <div>
                  <Text strong>选择语音</Text>
                  <Select
                    style={{ width: '100%', marginTop: '8px' }}
                    value={config.voice}
                    onChange={(value) => setConfig(prev => ({ ...prev, voice: value }))}
                    placeholder="请选择语音"
                    options={voiceOptions}
                  />
                </div>

                <Divider />

                <div>
                  <Text strong>语速: {config.rate}</Text>
                  <Slider
                    min={0}
                    max={200}
                    value={rateToSlider(config.rate)}
                    onChange={(value) => setConfig(prev => ({ ...prev, rate: sliderToRate(value) }))}
                  />
                </div>

                <div>
                  <Text strong>音量: {config.volume}</Text>
                  <Slider
                    min={0}
                    max={200}
                    value={volumeToSlider(config.volume)}
                    onChange={(value) => setConfig(prev => ({ ...prev, volume: sliderToVolume(value) }))}
                  />
                </div>

                <div>
                  <Text strong>音调: {config.pitch}</Text>
                  <Slider
                    min={0}
                    max={200}
                    value={pitchToSlider(config.pitch)}
                    onChange={(value) => setConfig(prev => ({ ...prev, pitch: sliderToPitch(value) }))}
                  />
                </div>
              </Space>
            </Card>

            <Card title="预览">
              <Space direction="vertical" size="middle" className="w-full">
                <TextArea
                  rows={3}
                  value={previewText}
                  onChange={(e) => setPreviewText(e.target.value)}
                  placeholder="输入要预览的文本..."
                  maxLength={500}
                  showCount
                />
                <div className="flex gap-3">
                  <Button
                    type="primary"
                    icon={<SoundOutlined />}
                    onClick={handlePreview}
                    loading={previewLoading}
                    disabled={!previewText.trim()}
                  >
                    试听
                  </Button>
                  <audio ref={audioRef} className="hidden" />
                </div>
              </Space>
            </Card>
          </Spin>
        </div>
      </Content>
    </Layout>
  );
}
