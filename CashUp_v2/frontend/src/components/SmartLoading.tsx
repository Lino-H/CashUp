/**
 * 智能加载组件 - 根据加载状态智能显示内容
 */

import React, { memo, useState, useEffect } from 'react';
import { Spin, Alert, Button, Result } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { OptimizedSkeleton } from './PageSkeleton';
import { useLoading } from '../hooks/useLoading';

interface SmartLoadingProps {
  loading?: boolean;
  error?: string | null;
  data?: any;
  children: React.ReactNode;
  loadingComponent?: React.ReactNode;
  errorComponent?: React.ReactNode;
  emptyComponent?: React.ReactNode;
  skeletonVariant?: 'text' | 'avatar' | 'input' | 'image' | 'button' | 'card' | 'table' | 'list';
  skeletonLines?: number;
  showRetry?: boolean;
  retryText?: string;
  onRetry?: () => void;
  delay?: number;
  minHeight?: string | number;
}

export const SmartLoading: React.FC<SmartLoadingProps> = memo(({
  loading = false,
  error = null,
  data = null,
  children,
  loadingComponent,
  errorComponent,
  emptyComponent,
  skeletonVariant = 'card',
  skeletonLines = 3,
  showRetry = true,
  retryText = '重试',
  onRetry,
  delay = 300,
  minHeight = 200
}) => {
  const [showLoading, setShowLoading] = useState(false);
  const [hasData, setHasData] = useState(false);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    
    if (loading) {
      timer = setTimeout(() => {
        setShowLoading(true);
      }, delay);
    } else {
      setShowLoading(false);
    }

    return () => {
      if (timer) {
        clearTimeout(timer);
      }
    };
  }, [loading, delay]);

  useEffect(() => {
    if (data !== null && data !== undefined) {
      setHasData(true);
    }
  }, [data]);

  const handleRetry = () => {
    if (onRetry) {
      onRetry();
    }
  };

  // 加载状态
  if (loading && showLoading) {
    if (loadingComponent) {
      return <>{loadingComponent}</>;
    }
    
    return (
      <div style={{ minHeight, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <OptimizedSkeleton 
          variant={skeletonVariant}
          lines={skeletonLines}
          loading={true}
        />
      </div>
    );
  }

  // 错误状态
  if (error) {
    if (errorComponent) {
      return <>{errorComponent}</>;
    }
    
    return (
      <div style={{ minHeight, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Result
          status="error"
          title="加载失败"
          subTitle={error}
          extra={showRetry && [
            <Button key="retry" type="primary" icon={<ReloadOutlined />} onClick={handleRetry}>
              {retryText}
            </Button>
          ]}
        />
      </div>
    );
  }

  // 空数据状态
  if (!hasData && emptyComponent) {
    return <>{emptyComponent}</>;
  }

  // 正常状态
  return <>{children}</>;
});

SmartLoading.displayName = 'SmartLoading';

// 高级智能加载组件 - 集成useLoading Hook
interface AdvancedSmartLoadingProps {
  useLoadingHook: ReturnType<typeof useLoading>;
  children: React.ReactNode;
  loadingComponent?: React.ReactNode;
  errorComponent?: React.ReactNode;
  emptyComponent?: React.ReactNode;
  skeletonVariant?: 'text' | 'avatar' | 'input' | 'image' | 'button' | 'card' | 'table' | 'list';
  skeletonLines?: number;
  showRetry?: boolean;
  retryText?: string;
  delay?: number;
  minHeight?: string | number;
  emptyDataMessage?: string;
}

export const AdvancedSmartLoading: React.FC<AdvancedSmartLoadingProps> = memo(({
  useLoadingHook,
  children,
  loadingComponent,
  errorComponent,
  emptyComponent,
  skeletonVariant = 'card',
  skeletonLines = 3,
  showRetry = true,
  retryText = '重试',
  delay = 300,
  minHeight = 200,
  emptyDataMessage = '暂无数据'
}) => {
  const { loading, error, data, execute } = useLoadingHook;

  const isEmpty = data === null || data === undefined || 
    (Array.isArray(data) && data.length === 0) ||
    (typeof data === 'object' && Object.keys(data).length === 0);

  const defaultEmptyComponent = (
    <div style={{ minHeight, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Result
        status="info"
        title={emptyDataMessage}
        extra={showRetry && [
          <Button key="retry" type="primary" icon={<ReloadOutlined />} onClick={() => execute(() => Promise.resolve(data))}>
            {retryText}
          </Button>
        ]}
      />
    </div>
  );

  return (
    <SmartLoading
      loading={loading}
      error={error}
      data={data}
      emptyComponent={isEmpty ? (emptyComponent || defaultEmptyComponent) : undefined}
      loadingComponent={loadingComponent}
      errorComponent={errorComponent}
      skeletonVariant={skeletonVariant}
      skeletonLines={skeletonLines}
      showRetry={showRetry}
      retryText={retryText}
      onRetry={() => execute(() => Promise.resolve(data))}
      delay={delay}
      minHeight={minHeight}
    >
      {children}
    </SmartLoading>
  );
});

AdvancedSmartLoading.displayName = 'AdvancedSmartLoading';