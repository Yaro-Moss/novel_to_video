import { useNotificationStore } from '../stores/notificationStore';
import type { NotificationType } from '../stores/notificationStore';

// 这个hook可以接受 message 和 notification 实例作为参数
export const useNotification = (messageInstance?: any, notificationInstance?: any) => {
  const { addNotification, removeNotification, clearAll } = useNotificationStore();
  
  // 使用 Ant Design message
  const showMessage = (
    type: NotificationType,
    content: string,
    duration = 3,
  ) => {
    if (messageInstance) {
      messageInstance[type](content, duration);
    }
    return addNotification({
      type,
      message: content,
      duration: duration * 1000,
    });
  };
  
  // 使用 Ant Design notification
  const showNotification = (
    type: NotificationType,
    title: string,
    description?: string,
    duration = 4.5,
  ) => {
    if (notificationInstance) {
      notificationInstance[type]({
        message: title,
        description,
        duration,
        placement: 'topRight',
      });
    }
    return addNotification({
      type,
      message: title,
      description,
      duration: duration * 1000,
    });
  };
  
  // 便捷方法
  const success = (content: string, duration = 3) => showMessage('success', content, duration);
  const error = (content: string, duration = 3) => showMessage('error', content, duration);
  const warning = (content: string, duration = 3) => showMessage('warning', content, duration);
  const info = (content: string, duration = 3) => showMessage('info', content, duration);
  
  // 工作流相关通知
  const workflowSuccess = (projectName: string) => {
    showNotification('success', '工作流完成', `项目 "${projectName}" 已成功处理完成！`);
  };
  
  const workflowError = (projectName: string, errorMsg?: string) => {
    showNotification('error', '工作流失败', errorMsg || `项目 "${projectName}" 处理失败，请重试。`);
  };
  
  const workflowProgress = (step: string) => {
    showMessage('info', `正在执行: ${step}`);
  };
  
  return {
    showMessage,
    showNotification,
    success,
    error,
    warning,
    info,
    workflowSuccess,
    workflowError,
    workflowProgress,
    removeNotification,
    clearAll,
  };
};
