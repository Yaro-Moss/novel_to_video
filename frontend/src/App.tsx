import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, App as AntdApp } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import Layout from './components/Layout';
import Login from './pages/Login';
import Register from './pages/Register';
import ProjectList from './pages/ProjectList';
import ProjectCreate from './pages/ProjectCreate';
import ProjectDetail from './pages/ProjectDetail';
import VideoResult from './pages/VideoResult';
import Settings from './pages/Settings';
import SegmentsPreview from './pages/SegmentsPreview';
import TTSConfig from './pages/TTSConfig';
import ImageConfig from './pages/ImageConfig';
import VideoConfig from './pages/VideoConfig';
import { useAuthStore } from './stores/authStore';
import { useThemeStore } from './stores/themeStore';
import { lightTheme, darkTheme } from './theme';
// 暂时禁用 i18n - 需要安装依赖后启用
// import { useTranslation } from 'react-i18next';

interface ProtectedRouteProps {
  children: React.ReactNode;
  useLayout?: boolean;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  useLayout = true
}) => {
  const { isAuthenticated } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (useLayout) {
    return <Layout>{children}</Layout>;
  }

  return <>{children}</>;
};

function App() {
  const { themeMode } = useThemeStore();
  // 暂时禁用 i18n - 需要安装依赖后启用
  // const { i18n } = useTranslation();

  const getAntdLocale = () => {
    // 暂时固定为中文
    return zhCN;
    // 暂时禁用 i18n - 需要安装依赖后启用
    // const lang = i18n.language;
    // if (lang === 'zh-CN') return zhCN;
    // return enUS;
  };

  return (
    <ConfigProvider
      theme={themeMode === 'dark' ? darkTheme : lightTheme}
      locale={getAntdLocale()}
    >
      <AntdApp> {/* 添加 Antd App 组件 */}
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/" element={
              <ProtectedRoute useLayout={false}>
                <Navigate to="/projects" replace />
              </ProtectedRoute>
            } />
            <Route path="/projects" element={
              <ProtectedRoute>
                <ProjectList />
              </ProtectedRoute>
            } />
            <Route path="/projects/create" element={
              <ProtectedRoute>
                <ProjectCreate />
              </ProtectedRoute>
            } />
            <Route path="/project/:id" element={
              <ProtectedRoute>
                <ProjectDetail />
              </ProtectedRoute>
            } />
            <Route path="/project/:id/result" element={
              <ProtectedRoute>
                <VideoResult />
              </ProtectedRoute>
            } />
            <Route path="/settings" element={
              <ProtectedRoute>
                <Settings />
              </ProtectedRoute>
            } />
            <Route path="/projects/:id/segments" element={
              <ProtectedRoute>
                <SegmentsPreview />
              </ProtectedRoute>
            } />
            <Route path="/projects/:id/tts" element={
              <ProtectedRoute>
                <TTSConfig />
              </ProtectedRoute>
            } />
            <Route path="/projects/:id/image" element={
              <ProtectedRoute>
                <ImageConfig />
              </ProtectedRoute>
            } />
            <Route path="/projects/:id/video" element={
              <ProtectedRoute>
                <VideoConfig />
              </ProtectedRoute>
            } />
          </Routes>
        </Router>
      </AntdApp>
    </ConfigProvider>
  );
}

export default App;
