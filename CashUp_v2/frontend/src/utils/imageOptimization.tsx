/**
 * 图片优化工具类
 * Image Optimization Utility Class
 */

export class ImageOptimizer {
  /**
   * 图片配置选项
   * Image configuration options
   */
  private static readonly DEFAULT_OPTIONS = {
    quality: 85,
    maxWidth: 1920,
    maxHeight: 1080,
    format: 'webp',
    compressionLevel: 6,
    convertToWebp: true,
    removeMetadata: true,
  };

  /**
   * 优化图片
   * Optimize image
   */
  static async optimizeImage(
    file: File,
    options: Partial<typeof ImageOptimizer.DEFAULT_OPTIONS> = {}
  ): Promise<Blob> {
    const config = { ...ImageOptimizer.DEFAULT_OPTIONS, ...options };

    return new Promise((resolve, reject) => {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      const img = new Image();

      img.onload = () => {
        // 计算缩放后的尺寸
        let { width, height } = img;
        
        if (width > config.maxWidth || height > config.maxHeight) {
          const ratio = Math.min(
            config.maxWidth / width,
            config.maxHeight / height
          );
          width *= ratio;
          height *= ratio;
        }

        // 设置canvas尺寸
        canvas.width = width;
        canvas.height = height;

        // 绘制图片
        if (ctx) {
          ctx.drawImage(img, 0, 0, width, height);
        }

        // 转换为Blob
        canvas.toBlob(
          (blob) => {
            if (blob) {
              resolve(blob);
            } else {
              reject(new Error('Failed to optimize image'));
            }
          },
          `image/${config.format}`,
          config.quality / 100
        );
      };

      img.onerror = () => {
        reject(new Error('Failed to load image'));
      };

      img.src = URL.createObjectURL(file);
    });
  }

  /**
   * 批量优化图片
   * Batch optimize images
   */
  static async optimizeImages(
    files: File[],
    options: Partial<typeof ImageOptimizer.DEFAULT_OPTIONS> = {}
  ): Promise<Blob[]> {
    const promises = files.map(file => this.optimizeImage(file, options));
    return Promise.all(promises);
  }

  /**
   * 生成不同尺寸的图片
   * Generate responsive images
   */
  static generateResponsiveImages(
    file: File,
    sizes: number[] = [320, 640, 1024, 1920]
  ): Promise<{ size: number; blob: Blob }[]> {
    const promises = sizes.map(size => 
      this.optimizeImage(file, { maxWidth: size, maxHeight: size })
        .then(blob => ({ size, blob }))
    );

    return Promise.all(promises);
  }

  /**
   * 生成图片的懒加载属性
   * Generate lazy loading attributes for image
   */
  static generateLazyLoadingAttributes(
    src: string,
    options: {
      alt?: string;
      className?: string;
      style?: React.CSSProperties;
      placeholder?: string;
    } = {}
  ): React.ImgHTMLAttributes<HTMLImageElement> {
    const { alt = '', className = '', style = {}, placeholder = '' } = options;

    return {
      src,
      alt,
      className,
      style,
      loading: 'lazy',
      decoding: 'async',
      fetchPriority: 'low',
      // 添加占位符
      ...(placeholder && { placeholder: 'blur' }),
    };
  }

  /**
   * 生成图片的srcset
   * Generate srcset for responsive images
   */
  static generateSrcset(sizes: { width: number; url: string }[]): string {
    return sizes
      .map(({ width, url }) => `${url} ${width}w`)
      .join(', ');
  }

  /**
   * 生成图片的sizes属性
   * Generate sizes attribute for responsive images
   */
  static generateSizes(breakpoints: string[]): string {
    return breakpoints.join(', ');
  }

  /**
   * 获取图片基本信息
   * Get image basic information
   */
  static async getImageInfo(file: File): Promise<{
    width: number;
    height: number;
    format: string;
    size: number;
    aspectRatio: number;
  }> {
    return new Promise((resolve, reject) => {
      const img = new Image();
      
      img.onload = () => {
        resolve({
          width: img.width,
          height: img.height,
          format: file.type.split('/')[1],
          size: file.size,
          aspectRatio: img.width / img.height,
        });
      };

      img.onerror = () => {
        reject(new Error('Failed to load image'));
      };

      img.src = URL.createObjectURL(file);
    });
  }

  /**
   * 验证图片格式
   * Validate image format
   */
  static isValidImageFormat(file: File): boolean {
    const validFormats = [
      'image/jpeg',
      'image/png',
      'image/webp',
      'image/gif',
      'image/avif',
    ];

    return validFormats.includes(file.type);
  }

  /**
   * 计算图片压缩率
   * Calculate image compression rate
   */
  static calculateCompressionRate(originalSize: number, compressedSize: number): number {
    return ((originalSize - compressedSize) / originalSize) * 100;
  }

  /**
   * 生成图片优化报告
   * Generate image optimization report
   */
  static generateOptimizationReport(
    originalFiles: File[],
    optimizedBlobs: Blob[]
  ): {
    totalOriginalSize: number;
    totalOptimizedSize: number;
    totalCompressionRate: number;
    fileReports: Array<{
      fileName: string;
      originalSize: number;
      optimizedSize: number;
      compressionRate: number;
    }>;
  } {
    const totalOriginalSize = originalFiles.reduce((sum, file) => sum + file.size, 0);
    const totalOptimizedSize = optimizedBlobs.reduce((sum, blob) => sum + blob.size, 0);
    const totalCompressionRate = this.calculateCompressionRate(
      totalOriginalSize,
      totalOptimizedSize
    );

    const fileReports = originalFiles.map((file, index) => ({
      fileName: file.name,
      originalSize: file.size,
      optimizedSize: optimizedBlobs[index].size,
      compressionRate: this.calculateCompressionRate(
        file.size,
        optimizedBlobs[index].size
      ),
    }));

    return {
      totalOriginalSize,
      totalOptimizedSize,
      totalCompressionRate,
      fileReports,
    };
  }

  /**
   * 创建优化的图片组件
   * Create optimized image component
   */
  static createOptimizedImage(
    src: string,
    alt: string = '',
    options: {
      width?: number;
      height?: number;
      className?: string;
      style?: React.CSSProperties;
      placeholder?: string;
      sizes?: string;
      srcset?: string;
    } = {}
  ): React.ReactElement {
    const {
      width,
      height,
      className = '',
      style = {},
      placeholder,
      sizes,
      srcset,
    } = options;

    const imgProps = this.generateLazyLoadingAttributes(src, {
      alt,
      className,
      style,
      placeholder,
    });

    return (
      <img
        {...imgProps}
        alt={alt}
        width={width}
        height={height}
        sizes={sizes}
        srcSet={srcset}
      />
    );
  }

  /**
   * 预加载图片
   * Preload images
   */
  static preloadImages(urls: string[]): Promise<void[]> {
    const promises = urls.map(url => {
      return new Promise<void>((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve();
        img.onerror = () => reject(new Error(`Failed to load image: ${url}`));
        img.src = url;
      });
    });

    return Promise.all(promises);
  }

  /**
   * 图片格式转换
   * Convert image format
   */
  static async convertImageFormat(
    file: File,
    targetFormat: 'webp' | 'jpeg' | 'png',
    quality: number = 85
  ): Promise<Blob> {
    return this.optimizeImage(file, {
      format: targetFormat,
      quality,
    });
  }

  /**
   * 生成图片的Base64数据
   * Generate Base64 data for image
   */
  static async toBase64(file: File): Promise<string> {
    const optimizedBlob = await this.optimizeImage(file, {
      format: 'webp',
      quality: 80,
    });

    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(reader.result as string);
      reader.onerror = () => reject(new Error('Failed to read image'));
      reader.readAsDataURL(optimizedBlob);
    });
  }
}

export default ImageOptimizer