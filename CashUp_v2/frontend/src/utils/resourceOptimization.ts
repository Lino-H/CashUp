/**
 * 资源优化配置和管理
 * Resource Optimization Configuration and Management
 */

import CSSOptimizer from './cssOptimization';
import ImageOptimizer from './imageOptimization';

export interface ResourceOptimizationConfig {
  // 图片优化配置
  images: {
    quality: number;
    maxWidth: number;
    maxHeight: number;
    format: 'webp' | 'jpeg' | 'png';
    convertToWebp: boolean;
    removeMetadata: boolean;
    enableLazyLoading: boolean;
    enableResponsiveImages: boolean;
    enablePreloading: boolean;
  };
  
  // CSS优化配置
  css: {
    enableMinification: boolean;
    enableVariables: boolean;
    enableResponsiveDesign: boolean;
    enableOptimizedAnimations: boolean;
    enableFontLoading: boolean;
    criticalCSS: string;
  };
  
  // 性能优化配置
  performance: {
    enableCaching: boolean;
    enableCompression: boolean;
    enableCDN: boolean;
    enableGzip: boolean;
    enableBrotli: boolean;
    cacheTTL: number;
  };
  
  // 监控配置
  monitoring: {
    enablePerformanceMonitoring: boolean;
    enableErrorTracking: boolean;
    enableResourceTracking: boolean;
    reportInterval: number;
  };
}

export const DEFAULT_RESOURCE_OPTIMIZATION_CONFIG: ResourceOptimizationConfig = {
  images: {
    quality: 85,
    maxWidth: 1920,
    maxHeight: 1080,
    format: 'webp',
    convertToWebp: true,
    removeMetadata: true,
    enableLazyLoading: true,
    enableResponsiveImages: true,
    enablePreloading: true,
  },
  
  css: {
    enableMinification: true,
    enableVariables: true,
    enableResponsiveDesign: true,
    enableOptimizedAnimations: true,
    enableFontLoading: true,
    criticalCSS: '',
  },
  
  performance: {
    enableCaching: true,
    enableCompression: true,
    enableCDN: true,
    enableGzip: true,
    enableBrotli: false,
    cacheTTL: 7 * 24 * 60 * 60 * 1000, // 7天
  },
  
  monitoring: {
    enablePerformanceMonitoring: true,
    enableErrorTracking: true,
    enableResourceTracking: true,
    reportInterval: 60000, // 1分钟
  },
};

export class ResourceOptimizationManager {
  private config: ResourceOptimizationConfig;
  private performanceMetrics: {
    images: Array<{
      src: string;
      originalSize: number;
      optimizedSize: number;
      compressionRate: number;
      loadTime: number;
    }>;
    css: Array<{
      originalSize: number;
      minifiedSize: number;
      savings: number;
    }>;
    resources: Array<{
      url: string;
      type: 'image' | 'css' | 'js' | 'font';
      size: number;
      loadTime: number;
      cached: boolean;
    }>;
  };

  constructor(config: Partial<ResourceOptimizationConfig> = {}) {
    this.config = {
      ...DEFAULT_RESOURCE_OPTIMIZATION_CONFIG,
      ...config,
    };
    
    this.performanceMetrics = {
      images: [],
      css: [],
      resources: [],
    };
  }

  /**
   * 获取当前配置
   * Get current configuration
   */
  getConfig(): ResourceOptimizationConfig {
    return { ...this.config };
  }

  /**
   * 更新配置
   * Update configuration
   */
  updateConfig(newConfig: Partial<ResourceOptimizationConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * 优化图片
   * Optimize images
   */
  async optimizeImages(files: File[]): Promise<{ optimizedFiles: Blob[]; report: any }> {
    const optimizedFiles: Blob[] = [];
    const report = {
      totalFiles: files.length,
      totalOriginalSize: 0,
      totalOptimizedSize: 0,
      totalCompressionRate: 0,
      fileReports: [] as any[],
    };

    for (const file of files) {
      const startTime = performance.now();
      
      try {
        const optimizedBlob = await ImageOptimizer.optimizeImage(file, {
          quality: this.config.images.quality,
          maxWidth: this.config.images.maxWidth,
          maxHeight: this.config.images.maxHeight,
          format: this.config.images.format,
          convertToWebp: this.config.images.convertToWebp,
          removeMetadata: this.config.images.removeMetadata,
        });

        const loadTime = performance.now() - startTime;
        const originalSize = file.size;
        const optimizedSize = optimizedBlob.size;
        const compressionRate = ImageOptimizer.calculateCompressionRate(originalSize, optimizedSize);

        optimizedFiles.push(optimizedBlob);

        report.totalOriginalSize += originalSize;
        report.totalOptimizedSize += optimizedSize;
        report.fileReports.push({
          fileName: file.name,
          originalSize,
          optimizedSize,
          compressionRate,
          loadTime,
        });

        // 记录性能指标
        this.performanceMetrics.images.push({
          src: file.name,
          originalSize,
          optimizedSize,
          compressionRate,
          loadTime,
        });

      } catch (error) {
        console.error(`Failed to optimize image: ${file.name}`, error);
        optimizedFiles.push(file);
      }
    }

    report.totalCompressionRate = ImageOptimizer.calculateCompressionRate(
      report.totalOriginalSize,
      report.totalOptimizedSize
    );

    return { optimizedFiles, report };
  }

  /**
   * 优化CSS
   * Optimize CSS
   */
  optimizeCSS(css: string): { optimizedCSS: string; report: any } {
    const originalSize = new Blob([css]).size;
    
    if (this.config.css.enableMinification) {
      css = CSSOptimizer.minifyCSS(css);
    }

    if (this.config.css.enableVariables) {
      css = CSSOptimizer.generateThemeVariables() + css;
    }

    if (this.config.css.enableResponsiveDesign) {
      css = CSSOptimizer.generateResponsiveBreakpoints() + css;
    }

    if (this.config.css.enableOptimizedAnimations) {
      css = CSSOptimizer.generateAnimations() + css;
    }

    if (this.config.css.enableFontLoading) {
      css = CSSOptimizer.generateFontLoading() + css;
    }

    const optimizedSize = new Blob([css]).size;
    const savings = originalSize - optimizedSize;
    const compressionRate = (savings / originalSize) * 100;

    // 记录性能指标
    this.performanceMetrics.css.push({
      originalSize,
      minifiedSize: optimizedSize,
      savings,
    });

    return {
      optimizedCSS: css,
      report: {
        originalSize,
        optimizedSize,
        savings,
        compressionRate,
      },
    };
  }

  /**
   * 生成资源优化报告
   * Generate resource optimization report
   */
  generateOptimizationReport(): {
    images: any[];
    css: any[];
    resources: any[];
    summary: {
      totalImageCompression: number;
      totalCSSCompression: number;
      totalResourceSavings: number;
      averageLoadTime: number;
    };
  } {
    const totalImageCompression = this.performanceMetrics.images.reduce(
      (sum, img) => sum + img.compressionRate, 0
    ) / this.performanceMetrics.images.length || 0;

    const totalCSSCompression = this.performanceMetrics.css.reduce(
      (sum, css) => sum + ((css.savings / css.originalSize) * 100), 0
    ) / this.performanceMetrics.css.length || 0;

    const totalResourceSavings = this.performanceMetrics.images.reduce(
      (sum, img) => sum + (img.originalSize - img.optimizedSize), 0
    ) + this.performanceMetrics.css.reduce(
      (sum, css) => sum + css.savings, 0
    );

    const averageLoadTime = this.performanceMetrics.images.reduce(
      (sum, img) => sum + img.loadTime, 0
    ) / this.performanceMetrics.images.length || 0;

    return {
      images: this.performanceMetrics.images,
      css: this.performanceMetrics.css,
      resources: this.performanceMetrics.resources,
      summary: {
        totalImageCompression,
        totalCSSCompression,
        totalResourceSavings,
        averageLoadTime,
      },
    };
  }

  /**
   * 开始性能监控
   * Start performance monitoring
   */
  startPerformanceMonitoring(): void {
    if (!this.config.monitoring.enablePerformanceMonitoring) return;

    const interval = setInterval(() => {
      this.collectPerformanceMetrics();
    }, this.config.monitoring.reportInterval);

    // 保存interval ID以便清理
    (this as any).monitoringInterval = interval;
  }

  /**
   * 停止性能监控
   * Stop performance monitoring
   */
  stopPerformanceMonitoring(): void {
    if ((this as any).monitoringInterval) {
      clearInterval((this as any).monitoringInterval);
      delete (this as any).monitoringInterval;
    }
  }

  /**
   * 收集性能指标
   * Collect performance metrics
   */
  private collectPerformanceMetrics(): void {
    if (this.config.monitoring.enableResourceTracking) {
      // 收集资源加载指标
      const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[];
      
      resources.forEach(resource => {
        if (resource.transferSize > 0) {
          this.performanceMetrics.resources.push({
            url: resource.name,
            type: resource.initiatorType as any,
            size: resource.transferSize,
            loadTime: resource.duration,
            cached: resource.transferSize < resource.decodedBodySize,
          });
        }
      });
    }

    if (this.config.monitoring.enableErrorTracking) {
      // 收集错误指标
      window.addEventListener('error', (event) => {
        console.error('Resource optimization error:', event.error);
      });
    }
  }

  /**
   * 获取当前性能指标
   * Get current performance metrics
   */
  getPerformanceMetrics(): any {
    return this.performanceMetrics;
  }

  /**
   * 清理资源
   * Clean up resources
   */
  cleanup(): void {
    this.stopPerformanceMonitoring();
    
    // 清理内存中的数据
    this.performanceMetrics = {
      images: [],
      css: [],
      resources: [],
    };
  }

  /**
   * 批量优化资源
   * Batch optimize resources
   */
  async batchOptimizeResources(
    images?: File[],
    css?: string,
    jsFiles?: File[]
  ): Promise<{
    optimizedImages?: Blob[];
    optimizedCSS?: string;
    optimizedJS?: Blob[];
    report: any;
  }> {
    const report: any = {
      images: null,
      css: null,
      js: null,
      summary: {},
    };

    if (images && images.length > 0) {
      const { report: imageReport } = await this.optimizeImages(images);
      report.images = imageReport;
    }

    if (css) {
      const { report: cssReport } = this.optimizeCSS(css);
      report.css = cssReport;
    }

    if (jsFiles && jsFiles.length > 0) {
      // JS优化可以在这里添加
      report.js = { files: jsFiles.length };
    }

    return {
      optimizedImages: report.images ? [] : undefined,
      optimizedCSS: report.css ? '' : undefined,
      optimizedJS: report.js ? [] : undefined,
      report,
    };
  }

  /**
   * 检查浏览器支持
   * Check browser support
   */
  checkBrowserSupport(): {
    webp: boolean;
    webpLossless: boolean;
    webpAlpha: boolean;
    jpeg2000: boolean;
    avif: boolean;
  } {
    const canvas = document.createElement('canvas');
    const webpSupport = canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0;
    
    return {
      webp: webpSupport,
      webpLossless: webpSupport,
      webpAlpha: webpSupport,
      jpeg2000: false,
      avif: false,
    };
  }

  /**
   * 获取优化建议
   * Get optimization suggestions
   */
  getOptimizationSuggestions(): string[] {
    const suggestions: string[] = [];
    const browserSupport = this.checkBrowserSupport();

    if (browserSupport.webp && this.config.images.format !== 'webp') {
      suggestions.push('建议使用WebP格式，可以获得更好的压缩效果');
    }

    if (this.config.images.quality > 85) {
      suggestions.push('建议降低图片质量到85以下，可以显著减少文件大小');
    }

    if (this.config.images.maxWidth > 1920) {
      suggestions.push('建议限制图片宽度到1920px以下，可以减少不必要的像素');
    }

    if (!this.config.images.enableLazyLoading) {
      suggestions.push('建议启用懒加载，可以提升首屏加载速度');
    }

    if (!this.config.images.enableResponsiveImages) {
      suggestions.push('建议启用响应式图片，可以根据设备加载不同尺寸的图片');
    }

    if (!this.config.css.enableMinification) {
      suggestions.push('建议启用CSS压缩，可以减少文件大小');
    }

    if (!this.config.performance.enableCaching) {
      suggestions.push('建议启用缓存，可以减少重复请求');
    }

    return suggestions;
  }
}

export default ResourceOptimizationManager;