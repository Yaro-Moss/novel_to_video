import { create } from 'zustand';

interface User {
  id: number;
  username: string;
  email: string;
}

interface AuthStore {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  isAuthenticated: boolean; // 直接存储在状态中
  setTokens: (accessToken: string, refreshToken: string) => void;
  setUser: (user: User) => void;
  logout: () => void;
}

// 简单验证 token 是否可能有效（检查是否为空和基本格式）
const isTokenValid = (token: string | null): boolean => {
  if (!token) return false;
  // 检查是否有基本的 JWT 格式（三个部分用点分隔）
  return token.split('.').length === 3;
};

export const useAuthStore = create<AuthStore>((set, get) => {
  // 初始化时从 localStorage 读取
  let accessToken = localStorage.getItem('accessToken');
  let refreshToken = localStorage.getItem('refreshToken');
  let userStr = localStorage.getItem('user');
  let user = userStr ? JSON.parse(userStr) : null;

  // 初始化时验证 token，如果无效则清除
  if (!isTokenValid(accessToken) || !isTokenValid(refreshToken)) {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
    accessToken = null;
    refreshToken = null;
    user = null;
  }

  return {
    accessToken,
    refreshToken,
    user,
    isAuthenticated: !!(accessToken && isTokenValid(accessToken)), // 只在 token 有效时认为已认证
    setTokens: (accessToken, refreshToken) => {
      localStorage.setItem('accessToken', accessToken);
      localStorage.setItem('refreshToken', refreshToken);
      set({ accessToken, refreshToken, isAuthenticated: true }); // 同时更新 isAuthenticated
    },
    setUser: (user) => {
      localStorage.setItem('user', JSON.stringify(user));
      set({ user });
    },
    logout: () => {
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('user');
      set({ 
        accessToken: null, 
        refreshToken: null, 
        user: null, 
        isAuthenticated: false // 同时更新 isAuthenticated
      });
    },
  };
});
