/**
 * 骨架屏组件 - 优化加载状态显示
 */

import React, { memo } from 'react';
import { Skeleton, SkeletonProps } from 'antd';

interface OptimizedSkeletonProps extends SkeletonProps {
  variant?: 'text' | 'avatar' | 'input' | 'image' | 'button' | 'card' | 'table' | 'list';
  lines?: number;
  width?: string | number;
  height?: string | number;
}

export const OptimizedSkeleton: React.FC<OptimizedSkeletonProps> = memo(({
  variant = 'text',
  lines = 1,
  width,
  height,
  loading = true,
  children,
  ...props
}) => {
  if (!loading) {
    return <>{children}</>;
  }

  const renderSkeleton = () => {
    switch (variant) {
      case 'avatar':
        return <Skeleton.Avatar active {...props} />;
      
      case 'input':
        return <Skeleton.Input active style={{ width, height }} {...props} />;
      
      case 'image':
        return <Skeleton.Image style={{ width, height }} {...props} />;
      
      case 'button':
        return <Skeleton.Button active style={{ width, height }} {...props} />;
      
      case 'card':
        return (
          <div style={{ padding: 16 }}>
            <Skeleton active paragraph={{ rows: 3 }} {...props} />
          </div>
        );
      
      case 'table':
        return (
          <div style={{ padding: 16 }}>
            <Skeleton active 
              title={{ width: '30%' }}
              paragraph={{ 
                rows: 5, 
                width: Array.from({ length: 5 }, (_, i) => 
                  i === 0 ? '60%' : `${Math.floor(Math.random() * 40 + 60)}%`
                )
              }} 
              {...props} 
            />
          </div>
        );
      
      case 'list':
        return (
          <div style={{ padding: 16 }}>
            {Array.from({ length: lines }).map((_, index) => (
              <div key={index} style={{ marginBottom: 16 }}>
                <Skeleton active 
                  avatar
                  title={{ width: `${Math.floor(Math.random() * 30 + 40)}%` }}
                  paragraph={{ rows: 1, width: `${Math.floor(Math.random() * 50 + 30)}%` }}
                />
              </div>
            ))}
          </div>
        );
      
      default: // text
        if (lines === 1) {
          return <Skeleton active title={false} paragraph={{ rows: 1, width }} {...props} />;
        }
        return (
          <div>
            <Skeleton active 
              title={false} 
              paragraph={{ 
                rows: lines, 
                width: Array.from({ length: lines }, () => 
                  typeof width === 'string' ? width : `${Math.floor(Math.random() * 30 + 70)}%`
                )
              }} 
              {...props} 
            />
          </div>
        );
    }
  };

  return renderSkeleton();
});

OptimizedSkeleton.displayName = 'OptimizedSkeleton';

// 页面级骨架屏
interface PageSkeletonProps {
  sections?: Array<{
    type: 'header' | 'stats' | 'chart' | 'table' | 'form';
    height?: string | number;
  }>;
}

export const PageSkeleton: React.FC<PageSkeletonProps> = memo(({ 
  sections = [
    { type: 'header' },
    { type: 'stats' },
    { type: 'chart' },
    { type: 'table' }
  ]
}) => {
  return (
    <div style={{ padding: 24 }}>
      {sections.map((section, index) => (
        <div key={index} style={{ marginBottom: 24 }}>
          {section.type === 'header' && (
            <div style={{ marginBottom: 24 }}>
              <Skeleton active title={{ width: '30%' }} paragraph={{ rows: 1, width: '60%' }} />
            </div>
          )}
          
          {section.type === 'stats' && (
            <div style={{ marginBottom: 24 }}>
              <div style={{ display: 'flex', gap: 16, marginBottom: 16 }}>
                {Array.from({ length: 4 }).map((_, i) => (
                  <div key={i} style={{ flex: 1 }}>
                    <Skeleton active paragraph={{ rows: 2, width: ['80%', '60%'] }} />
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {section.type === 'chart' && (
            <div style={{ marginBottom: 24, height: (section as any).height || 300 }}>
              <Skeleton active paragraph={{ rows: 8, width: Array.from({ length: 8 }, () => `${Math.floor(Math.random() * 30 + 70)}%`) }} />
            </div>
          )}
          
          {section.type === 'table' && (
            <div style={{ marginBottom: 24 }}>
              <OptimizedSkeleton variant="table" lines={5} />
            </div>
          )}
          
          {section.type === 'form' && (
            <div style={{ marginBottom: 24 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                {Array.from({ length: 6 }).map((_, i) => (
                  <div key={i}>
                    <Skeleton active paragraph={{ rows: 1, width: '80%' }} />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
});

PageSkeleton.displayName = 'PageSkeleton';