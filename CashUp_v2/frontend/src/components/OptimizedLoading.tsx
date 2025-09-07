/**
 * 优化的Loading组件 - 减少不必要的重新渲染
 */

import React, { memo } from 'react';
import { Spin, SpinProps } from 'antd';

interface OptimizedLoadingProps extends SpinProps {
  size?: 'small' | 'default' | 'large';
  tip?: string;
  delay?: number;
}

export const OptimizedLoading: React.FC<OptimizedLoadingProps> = memo(({ 
  size = 'default',
  tip = '加载中...',
  delay = 300,
  ...props 
}) => {
  return (
    <Spin 
      size={size}
      tip={tip}
      delay={delay}
      {...props}
    />
  );
});

OptimizedLoading.displayName = 'OptimizedLoading';