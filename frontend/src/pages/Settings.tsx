import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Layout,
  Card,
  Form,
  Input,
  Select,
  Button,
  List,
  Typography,
  Space,
  Divider,
  Modal,
  App,
  Spin
} from 'antd';
import {
  ArrowLeftOutlined,
  PlusOutlined,
  DeleteOutlined,
  KeyOutlined
} from '@ant-design/icons';
import { settingsApi, type ApiKeyItem } from '../services/api';

const { Content } = Layout;
const { Title, Text } = Typography;
const { Option } = Select;

export default function Settings() {
  const navigate = useNavigate();
  const { message } = App.useApp();
  const [apiKeys, setApiKeys] = useState<ApiKeyItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [form] = Form.useForm();
  const [deleteConfirm, setDeleteConfirm] = useState<{ visible: boolean; keyId: number }>({
    visible: false,
    keyId: 0
  });

  useEffect(() => {
    fetchApiKeys();
  }, []);

  const fetchApiKeys = async () => {
    try {
      setLoading(true);
      const response = await settingsApi.getApiKeys();
      setApiKeys(response.data);
    } catch (err) {
      message.error('获取 API Key 列表失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      await settingsApi.createApiKey(values);
      message.success('API Key 添加成功');
      form.resetFields();
      fetchApiKeys();
    } catch (err: any) {
      message.error(err.response?.data?.detail || '添加失败');
    }
  };

  const handleDelete = async () => {
    try {
      await settingsApi.deleteApiKey(deleteConfirm.keyId);
      message.success('API Key 删除成功');
      setDeleteConfirm({ visible: false, keyId: 0 });
      fetchApiKeys();
    } catch (err) {
      message.error('删除失败');
    }
  };

  const showDeleteConfirm = (keyId: number) => {
    setDeleteConfirm({ visible: true, keyId });
  };

  return (
    <Layout className="min-h-screen bg-gray-50">
      <Content className="p-6">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <Space>
              <Button icon={<ArrowLeftOutlined />} onClick={() => navigate('/')}>
                返回
              </Button>
              <Title level={2} style={{ margin: 0 }}>设置</Title>
            </Space>
          </div>

          <Card title="API Key 管理" className="mb-6">
            <Form form={form} layout="vertical" onFinish={handleSubmit}>
              <Form.Item
                label="服务提供商"
                name="provider"
                rules={[{ required: true, message: '请选择服务提供商' }]}
              >
                <Select placeholder="请选择">
                  <Option value="openai">OpenAI</Option>
                  <Option value="ark">火山方舟（豆包）</Option>
                  <Option value="sd_webui">Stable Diffusion WebUI</Option>
                </Select>
              </Form.Item>

              <Form.Item
                label="API Key"
                name="api_key"
                rules={[{ required: true, message: '请输入 API Key' }]}
              >
                <Input.Password placeholder="请输入 API Key" />
              </Form.Item>

              <Form.Item>
                <Button type="primary" htmlType="submit" icon={<PlusOutlined />}>
                  添加 API Key
                </Button>
              </Form.Item>
            </Form>

            <Divider />

            <Title level={4}>已保存的 API Keys</Title>
            {loading ? (
              <Spin size="large" className="flex justify-center py-8" />
            ) : (
              <List
                dataSource={apiKeys}
                locale={{ emptyText: '暂无 API Key' }}
                renderItem={(item) => (
                  <List.Item
                    actions={[
                      <Button
                        danger
                        type="text"
                        icon={<DeleteOutlined />}
                        onClick={() => showDeleteConfirm(item.id)}
                      >
                        删除
                      </Button>
                    ]}
                  >
                    <List.Item.Meta
                      avatar={<KeyOutlined style={{ fontSize: '24px' }} />}
                      title={
                        <Space>
                          <Text strong>{item.provider}</Text>
                          <Text type="secondary">{item.masked_key}</Text>
                        </Space>
                      }
                      description={new Date(item.created_at).toLocaleString('zh-CN')}
                    />
                  </List.Item>
                )}
              />
            )}
          </Card>
        </div>
      </Content>

      <Modal
        title="删除 API Key"
        open={deleteConfirm.visible}
        onOk={handleDelete}
        onCancel={() => setDeleteConfirm({ visible: false, keyId: 0 })}
        okText="确认删除"
        cancelText="取消"
        okButtonProps={{ danger: true }}
      >
        <p>确定要删除这个 API Key 吗？此操作不可恢复。</p>
      </Modal>
    </Layout>
  );
}
