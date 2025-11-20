import React, { useState, useEffect, useRef, forwardRef } from 'react';
import ImageOptimizer from '../utils/imageOptimization';

interface OptimizedImageProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  className?: string;
  style?: React.CSSProperties;
  placeholder?: string;
  sizes?: string;
  srcSet?: string;
  quality?: number;
  maxWidth?: number;
  maxHeight?: number;
  lazy?: boolean;
  onLoad?: () => void;
  onError?: (error: Error) => void;
  onLoadStart?: () => void;
  onLoadEnd?: () => void;
  objectFit?: 'cover' | 'contain' | 'fill' | 'none' | 'scale-down';
  objectPosition?: string;
  decoding?: 'sync' | 'async' | 'auto';
  fetchPriority?: 'high' | 'low' | 'auto';
  ariaLabel?: string;
  role?: string;
}

const OptimizedImage = forwardRef<HTMLImageElement, OptimizedImageProps>(({
  src,
  alt,
  width,
  height,
  className = '',
  style = {},
  placeholder,
  sizes,
  srcSet,
  quality = 85,
  maxWidth = 1920,
  maxHeight = 1080,
  lazy = true,
  onLoad,
  onError,
  onLoadStart,
  onLoadEnd,
  objectFit = 'cover',
  objectPosition = 'center',
  decoding = 'async',
  fetchPriority = 'auto',
  ariaLabel,
  role = 'img',
  ...props
}, ref) => {
  const [imageSrc, setImageSrc] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<boolean>(false);
  const [optimized, setOptimized] = useState<boolean>(false);
  // 使用转发的 ref，无需本地副本
  
  // 合并ref
  const combinedRef = (node: HTMLImageElement) => {
    if (typeof ref === 'function') {
      ref(node);
    } else if (ref) {
      ref.current = node;
    }
  };

  useEffect(() => {
    if (!src) {
      setLoading(false);
      return;
    }

    const loadImage = async () => {
      onLoadStart?.();
      setLoading(true);
      setError(false);

      try {
        // 如果是外部URL，直接使用
        if (src.startsWith('http') || src.startsWith('data:')) {
          setImageSrc(src);
          setOptimized(false);
          return;
        }

        // 本地图片优化
        const response = await fetch(src);
        const blob = await response.blob();
        const file = new File([blob], 'image', { type: blob.type, lastModified: Date.now() });
        
        // 优化图片
        const optimizedBlob = await ImageOptimizer.optimizeImage(file, {
          quality,
          maxWidth,
          maxHeight,
        });
        
        // 转换为DataURL
        const optimizedUrl = URL.createObjectURL(optimizedBlob);
        setImageSrc(optimizedUrl);
        setOptimized(true);
        
        // 清理旧的URL
        return () => {
          URL.revokeObjectURL(optimizedUrl);
        };
      } catch (err) {
        console.error('Failed to optimize image:', err);
        setImageSrc(src);
        setOptimized(false);
        setError(true);
      } finally {
        setLoading(false);
        onLoadEnd?.();
      }
    };

    loadImage();
  }, [src, quality, maxWidth, maxHeight]);

  const handleLoad = () => {
    setLoading(false);
    onLoad?.();
  };

  const handleError = (err: React.SyntheticEvent<HTMLImageElement, Event>) => {
    setLoading(false);
    setError(true);
    onError?.(new Error('Image failed to load'));
  };

  // 生成响应式srcSet
  const generateResponsiveSrcSet = () => {
    if (!src || src.startsWith('http') || src.startsWith('data:')) {
      return srcSet;
    }

    const sizes = [320, 640, 1024, 1920];
    return sizes
      .map(size => `${src}?width=${size} ${size}w`)
      .join(', ');
  };

  // 生成响应式sizes
  const generateResponsiveSizes = () => {
    return sizes || '(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw';
  };

  const imageProps: React.ImgHTMLAttributes<HTMLImageElement> = {
    src: imageSrc,
    alt,
    width,
    height,
    className: `${className} ${loading ? 'loading' : ''} ${error ? 'error' : ''}`,
    style: {
      ...style,
      objectFit,
      objectPosition,
      opacity: loading ? 0 : 1,
      transition: 'opacity 0.3s ease',
    },
    // placeholder 属性非标准 img 属性，保留在容器层
    sizes: generateResponsiveSizes(),
    srcSet: generateResponsiveSrcSet(),
    loading: lazy ? 'lazy' : 'eager',
    decoding,
    fetchPriority,
    'aria-label': ariaLabel || alt,
    role,
    onLoad: handleLoad,
    onError: handleError,
    ...props,
  };

  // 添加加载状态样式
  const loadingStyles = {
    position: 'absolute' as const,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#f5f5f5',
    zIndex: 1,
  };

  return (
    <div className={`optimized-image-container ${className}`} style={{ position: 'relative', width, height }}>
      <img {...imageProps} ref={combinedRef} />
      
      {loading && (
        <div className="optimized-image-loading" style={loadingStyles}>
          <div className="loading-spinner" />
        </div>
      )}
      
      {error && (
        <div className="optimized-image-error" style={loadingStyles}>
          <div className="error-placeholder">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <span>图片加载失败</span>
          </div>
        </div>
      )}
      
      {optimized && !loading && !error && (
        <div className="optimized-image-badge" style={{
          position: 'absolute',
          top: 8,
          right: 8,
          backgroundColor: 'rgba(76, 175, 80, 0.9)',
          color: 'white',
          padding: '2px 6px',
          borderRadius: '4px',
          fontSize: '10px',
          fontWeight: '500',
          zIndex: 2,
        }}>
          已优化
        </div>
      )}
    </div>
  );
});

OptimizedImage.displayName = 'OptimizedImage';

// 预加载组件
interface OptimizedImagePreloaderProps {
  src: string;
  quality?: number;
  maxWidth?: number;
  maxHeight?: number;
  onLoad?: () => void;
  onError?: (error: Error) => void;
}

export const OptimizedImagePreloader: React.FC<OptimizedImagePreloaderProps> = ({
  src,
  quality = 85,
  maxWidth = 1920,
  maxHeight = 1080,
  onLoad,
  onError,
}) => {
  const [loaded, setLoaded] = useState<boolean>(false);
  const [error, setError] = useState<boolean>(false);

  useEffect(() => {
    const preloadImage = async () => {
      if (!src || loaded) return;

      try {
        const response = await fetch(src);
        const blob = await response.blob();
        const file = new File([blob], 'image', { type: blob.type, lastModified: Date.now() });
        
        const optimizedBlob = await ImageOptimizer.optimizeImage(file, {
          quality,
          maxWidth,
          maxHeight,
        });
        
        // 创建Image对象来预加载
        const img = new Image();
        img.onload = () => {
          setLoaded(true);
          onLoad?.();
        };
        img.onerror = () => {
          setError(true);
          onError?.(new Error('Failed to preload image'));
        };
        img.src = URL.createObjectURL(optimizedBlob);
      } catch (err) {
        setError(true);
        onError?.(err as Error);
      }
    };

    preloadImage();
  }, [src, quality, maxWidth, maxHeight, loaded, onLoad, onError]);

  return null;
};

// 图片批量优化组件
interface OptimizedImageBatchProps {
  images: Array<{
    src: string;
    alt: string;
    width?: number;
    height?: number;
    className?: string;
    style?: React.CSSProperties;
    quality?: number;
    maxWidth?: number;
    maxHeight?: number;
  }>;
  onAllLoaded?: () => void;
  onError?: (index: number, error: Error) => void;
  loadingComponent?: React.ReactNode;
}

export const OptimizedImageBatch: React.FC<OptimizedImageBatchProps> = ({
  images,
  onAllLoaded,
  onError,
  loadingComponent,
}) => {
  const [loadedCount, setLoadedCount] = useState<number>(0);
  const [errorCount, setErrorCount] = useState<number>(0);

  useEffect(() => {
    if (loadedCount === images.length && images.length > 0) {
      onAllLoaded?.();
    }
  }, [loadedCount, images.length, onAllLoaded]);

  const handleImageLoad = () => {
    setLoadedCount(prev => prev + 1);
  };

  const handleImageError = (index: number, error: Error) => {
    setErrorCount(prev => prev + 1);
    onError?.(index, error);
  };

  const allProcessed = loadedCount + errorCount === images.length;

  return (
    <div className="optimized-image-batch">
      {loadingComponent && !allProcessed && (
        <div className="batch-loading">
          {loadingComponent}
        </div>
      )}
      
      <div className="batch-progress">
        <span>加载进度: {loadedCount}/{images.length}</span>
        <span>错误: {errorCount}</span>
      </div>
      
      {images.map((image, index) => (
        <OptimizedImagePreloader
          key={index}
          src={image.src}
          quality={image.quality}
          maxWidth={image.maxWidth}
          maxHeight={image.maxHeight}
          onLoad={handleImageLoad}
          onError={(error) => handleImageError(index, error)}
        />
      ))}
    </div>
  );
};

export default OptimizedImage;
