import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Layout,
  Card,
  Select,
  Slider,
  Button,
  Typography,
  Space,
  App,
  Switch
} from 'antd'
import { LeftOutlined, SaveOutlined } from '@ant-design/icons'
import { projectApi } from '../services/api'

const { Header, Content } = Layout
const { Title, Text } = Typography

export default function VideoConfig() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { message } = App.useApp()

  // 字幕配置
  const [subtitleConfig, setSubtitleConfig] = useState({
    enabled: true,
    font_name: 'Microsoft YaHei',
    font_size: 24,
    font_color: 'white',
    position: 'bottom',
    border_color: 'black',
    border_width: 2
  })

  // 视频配置
  const [videoConfig, setVideoConfig] = useState({
    resolution: '1080p',
    fps: 24,
    fade_in: 0.5,
    fade_out: 0.5,
    burn_subtitles: true
  })

  const handleSave = async () => {
    try {
      if (!id) return
      await projectApi.updateProjectConfig(parseInt(id), {
        subtitle: subtitleConfig,
        video: videoConfig
      })
      message.success('配置已保存')
    } catch (error) {
      message.error('保存配置失败')
      console.error(error)
    }
  }

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
          <Title level={4} className="m-0">视频合成配置</Title>
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
        <div className="max-w-3xl mx-auto space-y-6">
          <Card title="字幕配置">
            <Space direction="vertical" size="large" className="w-full">
              <div className="flex items-center justify-between">
                <span>启用字幕</span>
                <Switch
                  checked={subtitleConfig.enabled}
                  onChange={(checked) => setSubtitleConfig(prev => ({ ...prev, enabled: checked }))}
                />
              </div>

              <div>
                <Text strong>字体</Text>
                <Select
                  style={{ width: '100%', marginTop: '8px' }}
                  value={subtitleConfig.font_name}
                  onChange={(value) => setSubtitleConfig(prev => ({ ...prev, font_name: value }))}
                  options={[
                    { value: 'Microsoft YaHei', label: '微软雅黑' },
                    { value: 'SimHei', label: '黑体' },
                    { value: 'SimSun', label: '宋体' },
                    { value: 'Arial', label: 'Arial' }
                  ]}
                />
              </div>

              <div>
                <Text strong>字体大小: {subtitleConfig.font_size}</Text>
                <Slider
                  min={12}
                  max={48}
                  value={subtitleConfig.font_size}
                  onChange={(value) => setSubtitleConfig(prev => ({ ...prev, font_size: value }))}
                />
              </div>

              <div>
                <Text strong>字体颜色</Text>
                <Select
                  style={{ width: '100%', marginTop: '8px' }}
                  value={subtitleConfig.font_color}
                  onChange={(value) => setSubtitleConfig(prev => ({ ...prev, font_color: value }))}
                  options={[
                    { value: 'white', label: '白色' },
                    { value: 'yellow', label: '黄色' },
                    { value: 'red', label: '红色' },
                    { value: 'black', label: '黑色' }
                  ]}
                />
              </div>

              <div>
                <Text strong>字幕位置</Text>
                <Select
                  style={{ width: '100%', marginTop: '8px' }}
                  value={subtitleConfig.position}
                  onChange={(value) => setSubtitleConfig(prev => ({ ...prev, position: value }))}
                  options={[
                    { value: 'top', label: '顶部' },
                    { value: 'center', label: '中间' },
                    { value: 'bottom', label: '底部' }
                  ]}
                />
              </div>

              <div>
                <Text strong>边框宽度: {subtitleConfig.border_width}</Text>
                <Slider
                  min={0}
                  max={5}
                  value={subtitleConfig.border_width}
                  onChange={(value) => setSubtitleConfig(prev => ({ ...prev, border_width: value }))}
                />
              </div>
            </Space>
          </Card>

          <Card title="视频配置">
            <Space direction="vertical" size="large" className="w-full">
              <div>
                <Text strong>分辨率</Text>
                <Select
                  style={{ width: '100%', marginTop: '8px' }}
                  value={videoConfig.resolution}
                  onChange={(value) => setVideoConfig(prev => ({ ...prev, resolution: value }))}
                  options={[
                    { value: '720p', label: '720p (1280x720)' },
                    { value: '1080p', label: '1080p (1920x1080)' },
                    { value: '4k', label: '4K (3840x2160)' }
                  ]}
                />
              </div>

              <div>
                <Text strong>帧率: {videoConfig.fps} fps</Text>
                <Slider
                  min={24}
                  max={60}
                  step={6}
                  value={videoConfig.fps}
                  onChange={(value) => setVideoConfig(prev => ({ ...prev, fps: value }))}
                />
              </div>

              <div>
                <Text strong>淡入时长: {videoConfig.fade_in}s</Text>
                <Slider
                  min={0}
                  max={3}
                  step={0.1}
                  value={videoConfig.fade_in}
                  onChange={(value) => setVideoConfig(prev => ({ ...prev, fade_in: value }))}
                />
              </div>

              <div>
                <Text strong>淡出时长: {videoConfig.fade_out}s</Text>
                <Slider
                  min={0}
                  max={3}
                  step={0.1}
                  value={videoConfig.fade_out}
                  onChange={(value) => setVideoConfig(prev => ({ ...prev, fade_out: value }))}
                />
              </div>

              <div className="flex items-center justify-between">
                <span>烧录字幕到视频</span>
                <Switch
                  checked={videoConfig.burn_subtitles}
                  onChange={(checked) => setVideoConfig(prev => ({ ...prev, burn_subtitles: checked }))}
                />
              </div>
            </Space>
          </Card>
        </div>
      </Content>
    </Layout>
  )
}