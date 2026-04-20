import { useState, useEffect, useRef, useCallback } from 'react';

export interface ProgressMessage {
  type: 'connected' | 'progress' | 'step_complete' | 'step_failed';
  project_id: number;
  step_name?: string;
  percentage?: number;
  message?: string;
  status?: string;
  eta?: number;
  error?: string;
  result?: any;
}

export interface Step {
  name: string;
  displayName: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  percentage: number;
}

export const STEPS: Step[] = [
  { name: 'import', displayName: '文本导入', status: 'pending', percentage: 0 },
  { name: 'segmentation', displayName: '智能分段', status: 'pending', percentage: 0 },
  { name: 'tts', displayName: '语音合成', status: 'pending', percentage: 0 },
  { name: 'image', displayName: '图像生成', status: 'pending', percentage: 0 },
  { name: 'video_segment', displayName: '视频段生成', status: 'pending', percentage: 0 },
  { name: 'video_concat', displayName: '视频拼接', status: 'pending', percentage: 0 },
];

export function useProjectProgress(projectId: number, autoConnect: boolean = true) {
  const [isConnected, setIsConnected] = useState(false);
  const [currentStep, setCurrentStep] = useState<string>('');
  const [percentage, setPercentage] = useState<number>(0);
  const [message, setMessage] = useState<string>('');
  const [steps, setSteps] = useState<Step[]>([...STEPS]);
  const [error, setError] = useState<string | null>(null);
  const [isCompleted, setIsCompleted] = useState(false);
  const [isFailed, setIsFailed] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  const getWebSocketUrl = useCallback(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const baseUrl = (import.meta as any).env.VITE_WS_URL || `${protocol}//localhost:8000`;
    return `${baseUrl}/api/v1/ws/progress/${projectId}`;
  }, [projectId]);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const url = getWebSocketUrl();
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data: ProgressMessage = JSON.parse(event.data);
          handleMessage(data);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);

        if (!isCompleted && !isFailed && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          setTimeout(() => {
            connect();
          }, 3000 * reconnectAttemptsRef.current);
        }
      };

      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        setError('连接错误');
      };
    } catch (err) {
      console.error('Failed to connect:', err);
      setError('连接失败');
    }
  }, [getWebSocketUrl, isCompleted, isFailed]);

  const handleMessage = useCallback((data: ProgressMessage) => {
    switch (data.type) {
      case 'connected':
        setIsConnected(true);
        setMessage('已连接');
        break;

      case 'progress':
        if (data.step_name) setCurrentStep(data.step_name);
        if (data.percentage !== undefined) setPercentage(data.percentage);
        if (data.message) setMessage(data.message);

        if (data.step_name) {
          setSteps(prev => prev.map(step => {
            if (step.name === data.step_name) {
              return {
                ...step,
                percentage: data.percentage ?? step.percentage,
                status: (data.status as any) || 'running'
              };
            }
            return step;
          }));
        }
        break;

      case 'step_complete':
        if (data.step_name) {
          setSteps(prev => prev.map(step => {
            if (step.name === data.step_name) {
              return { ...step, status: 'completed', percentage: 100 };
            }
            return step;
          }));
        }
        if (data.step_name === 'video_concat') {
          setIsCompleted(true);
          setPercentage(100);
        }
        break;

      case 'step_failed':
        if (data.step_name) {
          setSteps(prev => prev.map(step => {
            if (step.name === data.step_name) {
              return { ...step, status: 'failed', percentage: 0 };
            }
            return step;
          }));
        }
        if (data.error) setError(data.error);
        setIsFailed(true);
        break;
    }
  }, []);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const reset = useCallback(() => {
    setSteps([...STEPS]);
    setPercentage(0);
    setCurrentStep('');
    setMessage('');
    setError(null);
    setIsCompleted(false);
    setIsFailed(false);
    reconnectAttemptsRef.current = 0;
  }, []);

  useEffect(() => {
    if (autoConnect) {
      connect();
    }
    return () => {
      disconnect();
    };
  }, [connect, disconnect, autoConnect]);

  return {
    isConnected,
    currentStep,
    percentage,
    message,
    steps,
    error,
    isCompleted,
    isFailed,
    connect,
    disconnect,
    reset,
  };
}
