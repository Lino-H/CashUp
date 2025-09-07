/**
 * 优化的Card组件 - 减少不必要的重新渲染
 */

import React, { memo } from 'react';
import { Card, CardProps } from 'antd';

interface OptimizedCardProps extends CardProps {
  memoKey?: string;
}

export const OptimizedCard: React.FC<OptimizedCardProps> = memo(({ 
  children,
  memoKey,
  ...props 
}) => {
  return (
    <Card {...props}>
      {children}
    </Card>
  );
}, (prevProps, nextProps) => {
  // 自定义比较函数，只有在特定属性变化时才重新渲染
  const keysToCompare: (keyof OptimizedCardProps)[] = ['title', 'extra', 'loading', 'memoKey'];
  return keysToCompare.every(key => 
    prevProps[key] === nextProps[key]
  );
});

OptimizedCard.displayName = 'OptimizedCard';