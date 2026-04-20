import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Layout,
  Card,
  Select,
  Button,
  Typography,
  Space,
  App,
  Tabs,
  Input
} from 'antd'
import { LeftOutlined, SaveOutlined, PictureOutlined } from '@ant-design/icons'
import { projectApi } from '../services/api'

const { Header, Content } = Layout
const { Title, Text } = Typography
const { TextArea } = Input

export default function ImageConfig() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { message } = App.useApp()

  const [previewText, setPreviewText] = useState('这是一个美丽的风景')
  const [previewLoading, setPreviewLoading] = useState(false)
  const [activeEngine, setActiveEngine] = useState('ark')

  // DALL-E 配置
  const [dalleConfig, setDalleConfig] = useState({
    size: '1024x1024',
    quality: 'standard',
    style: 'vivid'
  })

  // 火山方舟配置
  const [arkConfig, setArkConfig] = useState({
    size: '1024x1024',
    quality: 'standard',
    style: 'vivid'
  })

  // SD WebUI 配置
  const [sdConfig] = useState({
    negative_prompt: '',
    sampler: 'Euler a',
    steps: 28,
    cfg_scale: 7,
    width: 1024,
    height: 1024,
    seed: -1
  })

  // 提示词配置
  const [promptConfig, setPromptConfig] = useState({
    style: 'anime',
    enhance_style: true
  })

  const handleSave = async () => {
    try {
      if (!id) return
      await projectApi.updateProjectConfig(parseInt(id), {
        image_engine: activeEngine,
        dalle: dalleConfig,
        ark: arkConfig,
        sd_webui: sdConfig,
        prompt: promptConfig
      })
      message.success('配置已保存')
    } catch (error) {
      message.error('保存配置失败')
      console.error(error)
    }
  }

  const handleEnhancePrompt = async () => {
    setPreviewLoading(true)
    try {
      message.info('提示词优化功能开发中')
    } catch (error) {
      message.error('提示词优化失败')
      console.error(error)
    } finally {
      setPreviewLoading(false)
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
          <Title level={4} className="m-0">图像生成配置</Title>
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
          <Card title="图像引擎选择">
            <Tabs
              activeKey={activeEngine}
              onChange={setActiveEngine}
              items={[
                { key: 'dalle', label: 'DALL-E 3' },
                { key: 'ark', label: '火山方舟（豆包）' },
                { key: 'sd_webui', label: 'Stable Diffusion WebUI' }
              ]}
            />
          </Card>

          {activeEngine === 'dalle' && (
            <Card title="DALL-E 配置">
              <Space direction="vertical" size="large" className="w-full">
                <div>
                  <Text strong>图像尺寸</Text>
                  <Select
                    style={{ width: '100%', marginTop: '8px' }}
                    value={dalleConfig.size}
                    onChange={(value) => setDalleConfig(prev => ({ ...prev, size: value }))}
                    options={[
                      { value: '1024x1024', label: '1024x1024' },
                      { value: '1792x1024', label: '1792x1024' },
                      { value: '1024x1792', label: '1024x1792' }
                    ]}
                  />
                </div>

                <div>
                  <Text strong>图像质量</Text>
                  <Select
                    style={{ width: '100%', marginTop: '8px' }}
                    value={dalleConfig.quality}
                    onChange={(value) => setDalleConfig(prev => ({ ...prev, quality: value }))}
                    options={[
                      { value: 'standard', label: '标准' },
                      { value: 'hd', label: '高清' }
                    ]}
                  />
                </div>

                <div>
                  <Text strong>图像风格</Text>
                  <Select
                    style={{ width: '100%', marginTop: '8px' }}
                    value={dalleConfig.style}
                    onChange={(value) => setDalleConfig(prev => ({ ...prev, style: value }))}
                    options={[
                      { value: 'vivid', label: '生动' },
                      { value: 'natural', label: '自然' }
                    ]}
                  />
                </div>
              </Space>
            </Card>
          )}

          {activeEngine === 'ark' && (
            <Card title="火山方舟配置">
              <Space direction="vertical" size="large" className="w-full">
                <div>
                  <Text strong>图像尺寸</Text>
                  <Select
                    style={{ width: '100%', marginTop: '8px' }}
                    value={arkConfig.size}
                    onChange={(value) => setArkConfig(prev => ({ ...prev, size: value }))}
                    options={[
                      { value: '1024x1024', label: '1024x1024' },
                      { value: '768x768', label: '768x768' },
                      { value: '512x512', label: '512x512' }
                    ]}
                  />
                </div>

                <div>
                  <Text strong>图像质量</Text>
                  <Select
                    style={{ width: '100%', marginTop: '8px' }}
                    value={arkConfig.quality}
                    onChange={(value) => setArkConfig(prev => ({ ...prev, quality: value }))}
                    options={[
                      { value: 'standard', label: '标准' },
                      { value: 'hd', label: '高清' }
                    ]}
                  />
                </div>

                <div>
                  <Text strong>图像风格</Text>
                  <Select
                    style={{ width: '100%', marginTop: '8px' }}
                    value={arkConfig.style}
                    onChange={(value) => setArkConfig(prev => ({ ...prev, style: value }))}
                    options={[
                      { value: 'vivid', label: '生动' },
                      { value: 'natural', label: '自然' }
                    ]}
                  />
                </div>
              </Space>
            </Card>
          )}

          <Card title="提示词优化">
            <Space direction="vertical" size="middle" className="w-full">
              <div>
                <Text strong>艺术风格</Text>
                <Select
                  style={{ width: '100%', marginTop: '8px' }}
                  value={promptConfig.style}
                  onChange={(value) => setPromptConfig(prev => ({ ...prev, style: value }))}
                  options={[
                    { value: 'anime', label: '动漫风格' },
                    { value: 'photorealistic', label: '写实风格' },
                    { value: 'cinematic', label: '电影风格' }
                  ]}
                />
              </div>

              <div>
                <Text strong>提示词预览</Text>
                <TextArea
                  rows={3}
                  value={previewText}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setPreviewText(e.target.value)}
                  style={{ marginTop: '8px' }}
                  placeholder="输入要优化的提示词..."
                />
                <Button
                  style={{ marginTop: '8px' }}
                  icon={<PictureOutlined />}
                  onClick={handleEnhancePrompt}
                  loading={previewLoading}
                >
                  优化提示词
                </Button>
              </div>
            </Space>
          </Card>
        </div>
      </Content>
    </Layout>
  )
}
