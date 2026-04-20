import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';
import QueryProvider from './components/QueryProvider';
// 暂时禁用 i18n - 需要安装依赖后启用
// import './i18n';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryProvider>
      <App />
    </QueryProvider>
  </React.StrictMode>
);
