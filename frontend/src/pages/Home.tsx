import { Layout, Typography, Button, Card } from 'antd';
import { useAuthStore } from '../stores/authStore';
import { useNavigate } from 'react-router-dom';

const { Header, Content } = Layout;
const { Title, Text } = Typography;

export default function Home() {
  const { user, logout, isAuthenticated } = useAuthStore();
  const navigate = useNavigate();

  if (!isAuthenticated) {
    navigate('/login');
    return null;
  }

  return (
    <Layout className="min-h-screen">
      <Header className="bg-white shadow-sm px-6 flex justify-between items-center">
        <Title level={4} className="!m-0">Novel to Video</Title>
        <div className="flex items-center gap-4">
          <Text>欢迎, {user?.username}!</Text>
          <Button onClick={logout}>退出</Button>
        </div>
      </Header>
      <Content className="p-6">
        <Card className="text-center py-12">
          <Title level={2}>项目开发进行中...</Title>
          <Text type="secondary">感谢您使用 Novel to Video！</Text>
        </Card>
      </Content>
    </Layout>
  );
}
