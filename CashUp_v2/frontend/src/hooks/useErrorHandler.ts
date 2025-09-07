/**
 * 全局错误处理Hook - 统一处理API调用错误
 */

import { useCallback } from 'react';
import { message } from 'antd';
import { handleApiError } from '../services/api';

export const useErrorHandler = () => {
  const handleError = useCallback((error: any, customMessage?: string) => {
    const errorMessage = customMessage || handleApiError(error);
    
    // 显示错误消息
    message.error(errorMessage);
    
    // 在开发模式下输出详细错误信息
    if (process.env.NODE_ENV === 'development') {
      console.error('Error details:', error);
    }
    
    return errorMessage;
  }, []);

  const handleApiCall = useCallback(async <T>(
    apiCall: () => Promise<T>,
    errorMessage?: string
  ): Promise<T | null> => {
    try {
      const result = await apiCall();
      return result;
    } catch (error) {
      handleError(error, errorMessage);
      return null;
    }
  }, [handleError]);

  return {
    handleError,
    handleApiCall
  };
};

export default useErrorHandler;