import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Layout,
  Card,
  Steps,
  Progress,
  Button,
  Typography,
  Space,
  Alert,
  Tag,
  Divider,
  Spin,
  App,
  Modal,
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  ArrowLeftOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  VideoCameraOutlined,
} from '@ant-design/icons';
import { projectApi } from '../services/api';
import { useProjectProgress } from '../hooks/useProjectProgress';
import type { Project } from '../types/project';

const { Content } = Layout;
const { Title, Text, Paragraph } = Typography;

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { message } = App.useApp();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const projectId = parseInt(id || '0');

  const {
    isConnected,
    currentStep,
    percentage,
    message: progressMessage,
    steps,
    error: progressError,
    isCompleted,
    isFailed,
    reset,
    connect,
  } = useProjectProgress(projectId, false);

  useEffect(() => {
    fetchProject();
  }, [id]);

  const fetchProject = async () => {
    try {
      setLoading(true);
      const response = await projectApi.getDetail(projectId);
      setProject(response.data);

      if (response.data.status === 'processing') {
        reset();
        connect();
      }
    } catch (err) {
      message.error('获取项目信息失败');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'default';
      case 'processing':
        return 'blue';
      case 'completed':
        return 'green';
      case 'failed':
        return 'red';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <ClockCircleOutlined />;
      case 'processing':
        return <Spin size="small" />;
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'failed':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return null;
    }
  };

  const handleStart = async () => {
    try {
      setStarting(true);
      reset();
      connect();
      await projectApi.start(projectId);
      message.success('工作流已启动');
      fetchProject();
    } catch (err: any) {
      message.error(err.response?.data?.detail || '启动失败');
    } finally {
      setStarting(false);
    }
  };

  const handleCancel = async () => {
    try {
      setShowConfirm(false);
      setCancelling(true);
      await projectApi.cancel(projectId);
      message.success('工作流已取消');
      fetchProject();
    } catch (err: any) {
      message.error(err.response?.data?.detail || '取消失败');
    } finally {
      setCancelling(false);
    }
  };

  const handleRetry = async () => {
    try {
      setRetrying(true);
      reset();
      connect();
      await projectApi.retry(projectId);
      message.success('工作流已重试');
      fetchProject();
    } catch (err: any) {
      message.error(err.response?.data?.detail || '重试失败');
    } finally {
      setRetrying(false);
    }
  };

  const getCurrentStepIndex = () => {
    if (!currentStep) {
      const firstIncomplete = steps.findIndex(s => s.status !== 'completed');
      return firstIncomplete === -1 ? steps.length - 1 : firstIncomplete;
    }
    return steps.findIndex(s => s.name === currentStep);
  };

  if (loading) {
    return (
      <Layout className="min-h-screen">
        <Content className="flex items-center justify-center">
          <Spin size="large" />
        </Content>
      </Layout>
    );
  }

  if (!project) {
    return (
      <Layout className="min-h-screen">
        <Content className="flex flex-col items-center justify-center p-8">
          <Alert message="项目不存在" type="error" showIcon />
          <Button className="mt-4" icon={<ArrowLeftOutlined />} onClick={() => navigate('/')}>
            返回项目列表
          </Button>
        </Content>
      </Layout>
    );
  }

  return (
    <Layout className="min-h-screen bg-gray-50">
      <Content className="p-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <Space>
              <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/')}>
                返回
              </Button>
              <Title level={2} style={{ margin: 0 }}>{project.name}</Title>
              <Tag color={getStatusColor(project.status)} icon={getStatusIcon(project.status)}>
                {project.status === 'pending' && '待开始'}
                {project.status === 'processing' && '处理中'}
                {project.status === 'completed' && '已完成'}
                {project.status === 'failed' && '失败'}
              </Tag>
            </Space>
            <Space>
              {isConnected && <Tag color="green">实时连接</Tag>}
              {project.status === 'pending' && (
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  onClick={handleStart}
                  loading={starting}
                >
                  开始生成
                </Button>
              )}
              {project.status === 'processing' && (
                <Button
                  danger
                  icon={<PauseCircleOutlined />}
                  onClick={() => setShowConfirm(true)}
                  loading={cancelling}
                >
                  取消
                </Button>
              )}
              {(project.status === 'failed' || project.status === 'completed') && (
                <Button
                  icon={<ReloadOutlined />}
                  onClick={handleRetry}
                  loading={retrying}
                >
                  重新生成
                </Button>
              )}
              {project.status === 'completed' && (
                <Button
                  type="primary"
                  icon={<VideoCameraOutlined />}
                  onClick={() => navigate(`/project/${projectId}/result`)}
                >
                  查看结果
                </Button>
              )}
            </Space>
          </div>

          {progressError && (
            <Alert
              message="错误"
              description={progressError}
              type="error"
              showIcon
              className="mb-6"
            />
          )}

          <Card className="mb-6">
            <div className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <Text strong>总体进度</Text>
                <Text type="secondary">{Math.round(percentage)}%</Text>
              </div>
              <Progress percent={percentage} status={isCompleted ? 'success' : isFailed ? 'exception' : 'active'} />
              {progressMessage && (
                <Text type="secondary" className="mt-2 block">{progressMessage}</Text>
              )}
            </div>

            <Divider />

            <Steps
              direction="vertical"
              current={getCurrentStepIndex()}
              status={isFailed ? 'error' : undefined}
              items={steps.map((step) => {
                const status = step.status === 'pending' ? 'wait' :
                              step.status === 'running' ? 'process' :
                              step.status === 'completed' ? 'finish' : 'error';

                return {
                  title: step.displayName,
                  description: step.name === currentStep ? progressMessage : undefined,
                  status,
                  subTitle: step.status === 'running' ? `${Math.round(step.percentage)}%` : undefined,
                };
              })}
            />
          </Card>

          <Card title="项目信息">
            <Space direction="vertical" className="w-full">
              <div>
                <Text type="secondary">创建时间：</Text>
                <Text>{new Date(project.created_at).toLocaleString('zh-CN')}</Text>
              </div>
              {project.updated_at && (
                <div>
                  <Text type="secondary">更新时间：</Text>
                  <Text>{new Date(project.updated_at).toLocaleString('zh-CN')}</Text>
                </div>
              )}
            </Space>
          </Card>
        </div>
      </Content>

      <Modal
        title="确认取消"
        open={showConfirm}
        onOk={handleCancel}
        onCancel={() => setShowConfirm(false)}
        okText="确认"
        cancelText="关闭"
        confirmLoading={cancelling}
      >
        <Paragraph>确定要取消当前工作流吗？已完成的步骤将保留。</Paragraph>
      </Modal>
    </Layout>
  );
}
