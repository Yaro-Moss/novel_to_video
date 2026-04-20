import { useState } from 'react';
import { Form, Input, Button, Card, Typography, App } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { useAuthStore } from '../stores/authStore';

const { Title, Text } = Typography;

export default function Login() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { setTokens, setUser } = useAuthStore();
  const { message } = App.useApp(); // 使用 App.useApp() 获取 message

  const onFinish = async (values: { email: string; password: string }) => {
    setLoading(true);
    try {
      const response = await api.post('/auth/login', values);
      const { access_token, refresh_token } = response.data;
      
      setTokens(access_token, refresh_token);
      
      // 获取用户信息
      const userResponse = await api.get('/auth/me', {
        headers: { Authorization: `Bearer ${access_token}` }
      });
      setUser(userResponse.data);
      
      message.success('登录成功！');
      navigate('/projects'); // 直接跳转到项目列表页
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '登录失败';
      message.error(typeof errorMessage === 'string' ? errorMessage : '登录失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md shadow-lg">
        <div className="text-center mb-6">
          <Title level={2} className="mb-2">Novel to Video</Title>
          <Text type="secondary">欢迎回来！请登录您的账户</Text>
        </div>
        
        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          layout="vertical"
        >
          <Form.Item
            name="email"
            label="邮箱"
            rules={[
              { required: true, message: '请输入邮箱地址' },
              { type: 'email', message: '请输入有效的邮箱地址' }
            ]}
          >
            <Input prefix={<UserOutlined />} placeholder="请输入邮箱" size="large" />
          </Form.Item>

          <Form.Item
            name="password"
            label="密码"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password prefix={<LockOutlined />} placeholder="请输入密码" size="large" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block size="large">
              登录
            </Button>
          </Form.Item>
        </Form>

        <div className="text-center">
          <Text>
            还没有账户？ <Link to="/register">立即注册</Link>
          </Text>
        </div>
      </Card>
    </div>
  );
}
