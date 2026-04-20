export interface Project {
  id: number;
  user_id: number;
  name: string;
  input_file: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  config: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ProjectListResponse {
  items: Project[];
  total: number;
  page: number;
  page_size: number;
}

export interface ProjectCreateRequest {
  name: string;
  file: File;
}

export interface ProjectUpdateRequest {
  name?: string;
  config?: Record<string, any>;
}

// 分段相关类型
export interface Segment {
  index: number;
  text: string;
  char_count: number;
  chapter_title?: string;
}

export interface SegmentsResponse {
  segments: Segment[];
  total_count: number;
  total_chars: number;
}

export interface SegmentsRequest {
  min_length?: number;
  max_length?: number;
  detect_chapters?: boolean;
}

// TTS 相关类型
export interface Voice {
  id: string;
  name: string;
  gender: string;
  language: string;
  preview?: any;
}

export interface VoicesResponse {
  success: boolean;
  data: Voice[];
  total: number;
}

export interface TTSConfig {
  voice: string;
  rate: string;
  volume: string;
  pitch: string;
}

export interface TTSPreviewRequest {
  text: string;
  voice: string;
  rate: string;
  volume: string;
  pitch: string;
}
