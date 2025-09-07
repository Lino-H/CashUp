/**
 * 性能监控Hook - 监控组件渲染性能
 */

import { useEffect, useRef } from 'react';

interface PerformanceMetrics {
  renderCount: number;
  renderTime: number;
  lastRenderTime: number;
}

export const usePerformanceMonitor = (componentName: string) => {
  const renderCount = useRef(0);
  const lastRenderTime = useRef<number | null>(null);
  const renderTimes = useRef<number[]>([]);

  useEffect(() => {
    const startTime = performance.now();
    
    return () => {
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      
      renderCount.current += 1;
      renderTimes.current.push(renderTime);
      
      // 保持最近10次的渲染时间记录
      if (renderTimes.current.length > 10) {
        renderTimes.current.shift();
      }
      
      lastRenderTime.current = renderTime;
      
      // 如果渲染时间超过16ms (60fps)，发出警告
      if (renderTime > 16) {
        console.warn(
          `[Performance] ${componentName} 渲染时间过长: ${renderTime.toFixed(2)}ms, ` +
          `渲染次数: ${renderCount.current}`
        );
      }
    };
  });

  const getMetrics = (): PerformanceMetrics => ({
    renderCount: renderCount.current,
    renderTime: lastRenderTime.current || 0,
    lastRenderTime: lastRenderTime.current || 0,
  });

  const getAverageRenderTime = (): number => {
    if (renderTimes.current.length === 0) return 0;
    const sum = renderTimes.current.reduce((a, b) => a + b, 0);
    return sum / renderTimes.current.length;
  };

  return {
    getMetrics,
    getAverageRenderTime,
    renderCount: renderCount.current,
  };
};