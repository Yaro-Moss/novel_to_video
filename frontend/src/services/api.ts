import axios from 'axios';
import type { Project, ProjectListResponse, ProjectUpdateRequest, SegmentsResponse, SegmentsRequest, VoicesResponse, TTSPreviewRequest } from '../types/project';

const API_BASE_URL = 'http://localhost:8000/api/v1';

// 创建 axios 实例
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// 请求拦截器 - 自动添加 Authorization 头
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    // 如果不是 FormData，则设置 Content-Type 为 application/json
    if (!(config.data instanceof FormData)) {
      config.headers['Content-Type'] = 'application/json';
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器 - 处理 401 错误
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem('refreshToken');
      if (refreshToken) {
        try {
          const response = await api.post('/auth/refresh', { refresh_token: refreshToken });
          const { access_token, refresh_token } = response.data;
          
          localStorage.setItem('accessToken', access_token);
          localStorage.setItem('refreshToken', refresh_token);
          
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          // 刷新失败，清除 token 但不立即跳转，避免错误循环
          localStorage.removeItem('accessToken');
          localStorage.removeItem('refreshToken');
          // 只有当当前页面不是登录页时才跳转
          if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
            window.location.href = '/login';
          }
        }
      } else {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        if (window.location.pathname !== '/login' && window.location.pathname !== '/register') {
          window.location.href = '/login';
        }
      }
    }

    return Promise.reject(error);
  }
);

// 认证相关 API
export const authApi = {
  register: (data: { username: string; email: string; password: string }) =>
    api.post('/auth/register', data),
  
  login: (data: { email: string; password: string }) =>
    api.post('/auth/login', data),
  
  refreshToken: (refresh_token: string) =>
    api.post('/auth/refresh', { refresh_token }),
  
  getCurrentUser: () =>
    api.get('/auth/me'),
};

// 项目相关 API
export const projectApi = {
  createProject: (name: string, file: File) => {
    const formData = new FormData();
    formData.append('name', name);
    formData.append('file', file);
    return api.post<Project>('/projects/', formData);
  },
  
  getProjects: (params?: { page?: number; page_size?: number; status?: string; search?: string }) =>
    api.get<ProjectListResponse>('/projects/', { params }),
  
  getDetail: (id: number) =>
    api.get<Project>(`/projects/${id}`),
  
  updateProject: (id: number, data: ProjectUpdateRequest) =>
    api.patch<Project>(`/projects/${id}`, data),
  
  deleteProject: (id: number) =>
    api.delete(`/projects/${id}`),
  
  getSegments: (id: number, params?: SegmentsRequest) =>
    api.get<SegmentsResponse>(`/projects/${id}/segments`, { params }),
  
  updateProjectConfig: (id: number, config: Record<string, any>) =>
    api.patch<Project>(`/projects/${id}/config`, { config }),
  
  start: (id: number, config?: Record<string, any>) =>
    api.post(`/projects/${id}/start`, config || {}),
  
  cancel: (id: number) =>
    api.post(`/projects/${id}/cancel`),
  
  retry: (id: number, config?: Record<string, any>) =>
    api.post(`/projects/${id}/retry`, config || {}),
  
  getStatus: (id: number) =>
    api.get(`/projects/${id}/status`),
  
  getVideo: (id: number) =>
    api.get(`/projects/${id}/video`, { responseType: 'blob' }),
  
  getVideoDownload: (id: number) =>
    api.get(`/projects/${id}/video/download`, { responseType: 'blob' }),
  
  getAssets: (id: number) =>
    api.get(`/projects/${id}/assets`),
};

// TTS API
export const ttsApi = {
  getVoices: () =>
    api.get<VoicesResponse>('/tts/voices'),
  
  previewTTS: (data: TTSPreviewRequest) =>
    api.post('/tts/preview', data, { responseType: 'blob' }),
};

// Settings API
export interface ApiKeyItem {
  id: number;
  provider: string;
  masked_key: string;
  created_at: string;
}

export interface CreateApiKeyRequest {
  provider: string;
  api_key: string;
}

export const settingsApi = {
  getApiKeys: () =>
    api.get<ApiKeyItem[]>('/settings/api-keys'),
  
  createApiKey: (data: CreateApiKeyRequest) =>
    api.post<ApiKeyItem>('/settings/api-keys', data),
  
  deleteApiKey: (id: number) =>
    api.delete(`/settings/api-keys/${id}`),
};

export default api;
