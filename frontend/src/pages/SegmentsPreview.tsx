import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Layout,
  Card,
  Collapse,
  Slider,
  Switch,
  Button,
  Typography,
  Space,
  Statistic,
  Spin,
  App,
} from 'antd';
import { LeftOutlined, ReloadOutlined } from '@ant-design/icons';
import type { SegmentsResponse } from '../types/project';
import { projectApi } from '../services/api';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

export default function SegmentsPreview() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { message } = App.useApp();
  const [loading, setLoading] = useState(false);
  const [segmentsData, setSegmentsData] = useState<SegmentsResponse | null>(null);
  const [minLength, setMinLength] = useState(50);
  const [maxLength, setMaxLength] = useState(500);
  const [detectChapters, setDetectChapters] = useState(true);

  const projectId = parseInt(id || '0', 10);

  const loadSegments = async () => {
    if (!projectId) return;
    
    setLoading(true);
    try {
      const response = await projectApi.getSegments(projectId, {
        min_length: minLength,
        max_length: maxLength,
        detect_chapters: detectChapters,
      });
      setSegmentsData(response.data);
    } catch (error) {
      message.error('加载分段失败');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSegments();
  }, [projectId, minLength, maxLength, detectChapters]);

  const handleReSegment = () => {
    loadSegments();
  };

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
          <Title level={4} className="m-0">分段预览</Title>
        </div>
      </Header>

      <Content className="p-6">
        <div className="max-w-5xl mx-auto">
          <Card className="mb-6">
            <Space direction="vertical" size="large" className="w-full">
              <div className="grid grid-cols-2 gap-4">
                <Statistic
                  title="总段落"
                  value={segmentsData?.total_count || 0}
                />
                <Statistic
                  title="总字符数"
                  value={segmentsData?.total_chars || 0}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <Text strong>最小段落长度</Text>
                  <Slider
                    min={10}
                    max={200}
                    value={minLength}
                    onChange={setMinLength}
                  />
                  <Text type="secondary">{minLength} 字符</Text>
                </div>

                <div>
                  <Text strong>最大段落长度</Text>
                  <Slider
                    min={100}
                    max={2000}
                    value={maxLength}
                    onChange={setMaxLength}
                  />
                  <Text type="secondary">{maxLength} 字符</Text>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <Space>
                  <span>章节检测</span>
                  <Switch
                    checked={detectChapters}
                    onChange={setDetectChapters}
                  />
                </Space>
                <Button
                  type="primary"
                  icon={<ReloadOutlined />}
                  onClick={handleReSegment}
                  loading={loading}
                >
                  重新分段
                </Button>
              </div>
            </Space>
          </Card>

          <Spin spinning={loading}>
            <Collapse
              items={
                segmentsData?.segments.map((segment, index) => ({
                  key: String(index),
                  label: (
                    <Space>
                      <Text strong>段落 {segment.index + 1}</Text>
                      <Text type="secondary">({segment.char_count} 字符)</Text>
                      {segment.chapter_title && (
                        <Text type="success">{segment.chapter_title}</Text>
                      )}
                    </Space>
                  ),
                  children: <Text className="whitespace-pre-wrap">{segment.text}</Text>,
                })) || []
              }
              defaultActiveKey={['0']}
            />
          </Spin>
        </div>
      </Content>
    </Layout>
  );
}
