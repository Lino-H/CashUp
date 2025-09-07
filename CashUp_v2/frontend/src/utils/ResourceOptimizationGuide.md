# 资源优化指南
# Resource Optimization Guide

## 概述

资源优化是前端性能优化的重要组成部分，包括图片、CSS、JavaScript等静态资源的优化。通过合理的资源优化，可以显著提升页面加载速度，减少带宽消耗，改善用户体验。

## 图片优化

### 图片格式选择

#### 1. WebP 格式
- **优点**: 最好的压缩比，支持透明度
- **兼容性**: 现代浏览器支持良好
- **使用场景**: 适合大多数图片资源

```typescript
// 检查WebP支持
const supportsWebp = document.createElement('canvas').toDataURL('image/webp').indexOf('data:image/webp') === 0;

if (supportsWebp) {
  // 使用WebP格式
  const optimizedImage = await ImageOptimizer.optimizeImage(file, {
    format: 'webp',
    quality: 85,
  });
}
```

#### 2. JPEG 格式
- **优点**: 适合照片类图片
- **缺点**: 不支持透明度
- **使用场景**: 照片、复杂图像

```typescript
// 优化JPEG图片
const optimizedImage = await ImageOptimizer.optimizeImage(file, {
  format: 'jpeg',
  quality: 85,
});
```

#### 3. PNG 格式
- **优点**: 支持透明度，无损压缩
- **缺点**: 文件较大
- **使用场景**: 需要透明度的图标、logo

```typescript
// 优化PNG图片
const optimizedImage = await ImageOptimizer.optimizeImage(file, {
  format: 'png',
  quality: 90,
});
```

#### 4. AVIF 格式
- **优点**: 最新的压缩格式，压缩效果最好
- **兼容性**: 支持有限
- **使用场景**: 对性能要求极高的场景

### 图片压缩策略

#### 1. 质量压缩
- **高质量**: 90-100%（适合产品图片）
- **中等质量**: 70-85%（适合一般图片）
- **低质量**: 50-70%（适合背景图片）

```typescript
// 根据场景选择质量
const getOptimalQuality = (type: 'product' | 'general' | 'background'): number => {
  switch (type) {
    case 'product': return 95;
    case 'general': return 85;
    case 'background': return 70;
    default: return 85;
  }
};
```

#### 2. 尺寸压缩
- 根据设备分辨率选择合适的尺寸
- 使用响应式图片技术

```typescript
// 生成响应式图片
const responsiveImages = await ImageOptimizer.generateResponsiveImages(file, [
  320,   // 手机
  640,   // 平板
  1024,  // 笔记本
  1920,  // 桌面
]);
```

### 懒加载实现

#### 1. 原生懒加载
```html
<img 
  src="placeholder.jpg" 
  data-src="real-image.jpg" 
  loading="lazy" 
  alt="Description"
/>
```

#### 2. Intersection Observer 实现
```typescript
const lazyLoadImages = () => {
  const images = document.querySelectorAll('img[data-src]');
  
  const imageObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target as HTMLImageElement;
        img.src = img.dataset.src!;
        img.removeAttribute('data-src');
        observer.unobserve(img);
      }
    });
  });

  images.forEach(img => imageObserver.observe(img));
};
```

### 图片预加载

#### 1. 预加载重要图片
```typescript
const preloadImportantImages = (urls: string[]) => {
  urls.forEach(url => {
    const link = document.createElement('link');
    link.rel = 'preload';
    link.as = 'image';
    link.href = url;
    document.head.appendChild(link);
  });
};
```

#### 2. 预加载策略
- 首屏图片立即加载
- 次屏图片延迟加载
- 预加载下一页图片

## CSS 优化

### CSS 压缩

#### 1. 移除不必要的内容
```typescript
// CSS 压缩函数
const minifyCSS = (css: string): string => {
  return css
    .replace(/\/\*[\s\S]*?\*\//g, '')  // 移除注释
    .replace(/\s{2,}/g, ' ')            // 移除多余空格
    .replace(/\n/g, '')                 // 移除换行符
    .replace(/\s*:\s*/g, ':')           // 移除冒号前空格
    .replace(/\s*;\s*/g, ';')           // 移除分号前空格
    .replace(/\s*,\s*/g, ',')           // 移除逗号前空格
    .replace(/\s*{\s*/g, '{')           // 移除花括号前空格
    .replace(/\s*}\s*/g, '}')           // 移除花括号后空格
    .replace(/;}/g, '}')                // 清理空规则
    .replace(/;+/g, ';')                // 清理多余分号
    .replace(/;$/, '');                 // 移除末尾分号
};
```

#### 2. CSS 优化工具
- **CSSNano**: 最小化CSS
- **PurgeCSS**: 移除未使用的CSS
- **Clean-CSS**: 压缩CSS

### CSS 变量和主题系统

#### 1. 设计CSS变量
```css
:root {
  /* 颜色系统 */
  --color-primary: #1890ff;
  --color-secondary: #52c41a;
  --color-warning: #faad14;
  --color-error: #ff4d4f;
  
  /* 间距系统 */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  
  /* 字体系统 */
  --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  --font-size-sm: 14px;
  --font-size-base: 16px;
  --font-size-lg: 18px;
  
  /* 圆角系统 */
  --border-radius-sm: 4px;
  --border-radius-base: 6px;
  --border-radius-lg: 8px;
}
```

#### 2. 主题切换
```typescript
// 主题切换功能
const toggleTheme = (theme: 'light' | 'dark') => {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
};

// 初始化主题
const initTheme = () => {
  const savedTheme = localStorage.getItem('theme') || 'light';
  toggleTheme(savedTheme);
};
```

### 响应式CSS优化

#### 1. 移动优先设计
```css
/* 移动端优先 */
.container {
  width: 100%;
  padding: 1rem;
}

@media (min-width: 768px) {
  .container {
    max-width: 720px;
    margin: 0 auto;
  }
}

@media (min-width: 1024px) {
  .container {
    max-width: 960px;
  }
}
```

#### 2. 使用CSS Grid和Flexbox
```css
/* Grid布局 */
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

/* Flexbox布局 */
.flex {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
```

## 性能优化策略

### 缓存策略

#### 1. 浏览器缓存
```http
# 强缓存
Cache-Control: max-age=31536000
Expires: Wed, 21 Dec 2023 12:00:00 GMT

# 协商缓存
ETag: "abc123"
Last-Modified: Wed, 21 Dec 2023 12:00:00 GMT
```

#### 2. Service Worker缓存
```typescript
// Service Worker缓存策略
const CACHE_NAME = 'cache-v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/static/css/main.css',
  '/static/js/main.js',
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});
```

### 代码分割

#### 1. 动态导入
```typescript
// 按需加载组件
const LazyComponent = React.lazy(() => import('./Component'));

// 使用Suspense
<Suspense fallback={<div>Loading...</div>}>
  <LazyComponent />
</Suspense>
```

#### 2. 路由级分割
```typescript
// React Router动态导入
const Home = React.lazy(() => import('./pages/Home'));
const About = React.lazy(() => import('./pages/About'));

<Routes>
  <Route path="/" element={<Home />} />
  <Route path="/about" element={<About />} />
</Routes>
```

### 资源预加载

#### 1. 关键资源预加载
```html
<!-- 关键CSS预加载 -->
<link rel="preload" href="critical.css" as="style">

<!-- 关键JS预加载 -->
<link rel="preload" href="critical.js" as="script">

<!-- 字体预加载 -->
<link rel="preload" href="font.woff2" as="font" type="font/woff2" crossorigin>
```

#### 2. 预连接
```html
<!-- DNS预解析 -->
<link rel="dns-prefetch" href="https://api.example.com">

<!-- 预连接 -->
<link rel="preconnect" href="https://cdn.example.com">
```

## 监控和分析

### 性能指标

#### 1. Core Web Vitals
```typescript
// 获取LCP (Largest Contentful Paint)
const getLCP = () => {
  return new Promise(resolve => {
    new PerformanceObserver((entryList) => {
      const entries = entryList.getEntries();
      const lastEntry = entries[entries.length - 1];
      resolve(lastEntry.startTime);
    }).observe({ entryTypes: ['largest-contentful-paint'] });
  });
};

// 获取FID (First Input Delay)
const getFID = () => {
  return new Promise(resolve => {
    new PerformanceObserver((entryList) => {
      const entries = entryList.getEntries();
      const firstEntry = entries[0];
      resolve(firstEntry.processingStart - firstEntry.startTime);
    }).observe({ entryTypes: ['first-input'] });
  });
};
```

#### 2. 资源加载监控
```typescript
// 监控资源加载
const monitorResourceLoading = () => {
  const resources = performance.getEntriesByType('resource');
  
  resources.forEach(resource => {
    console.log({
      url: resource.name,
      type: resource.initiatorType,
      size: resource.transferSize,
      loadTime: resource.duration,
      cached: resource.transferSize < resource.decodedBodySize,
    });
  });
};
```

### 性能优化建议

#### 1. 图片优化检查清单
- [ ] 使用WebP格式
- [ ] 压缩图片质量
- [ ] 适当调整图片尺寸
- [ ] 启用懒加载
- [ ] 使用响应式图片
- [ ] 添加alt文本
- [ ] 使用CDN

#### 2. CSS优化检查清单
- [ ] 压缩CSS文件
- [ ] 移除未使用的CSS
- [ ] 使用CSS变量
- [ ] 优化选择器
- [ ] 减少重绘和回流
- [ ] 使用CSS Grid和Flexbox

#### 3. JavaScript优化检查清单
- [ ] 代码分割
- [ ] 懒加载
- [ ] 缓存策略
- [ ] 减少包大小
- [ ] 使用Tree Shaking
- [ ] 优化第三方库

## 工具和库

### 构建工具
- **Webpack**: 模块打包工具
- **Vite**: 快速构建工具
- **Rollup**: 库打包工具
- **Parcel**: 零配置构建工具

### 优化插件
- **image-webpack-loader**: 图片优化
- **css-minimizer-webpack-plugin**: CSS压缩
- **terser-webpack-plugin**: JavaScript压缩
- **purgecss-webpack-plugin**: 移除未使用的CSS

### 监控工具
- **Lighthouse**: 性能审计工具
- **WebPageTest**: 性能测试工具
- **Chrome DevTools**: 开发者工具
- **Performance API**: 性能监控API

## 最佳实践

### 1. 优化策略
- **优先级优化**: 先优化影响最大的资源
- **渐进式优化**: 持续监控和改进
- **用户感知优化**: 优先优化首屏加载
- **跨设备优化**: 确保在不同设备上都有良好表现

### 2. 性能目标
- **LCP**: < 2.5秒
- **FID**: < 100毫秒
- **CLS**: < 0.1
- **FCP**: < 1.8秒
- **TTFB**: < 600毫秒

### 3. 持续优化
- 定期进行性能审计
- 监控关键指标
- A/B测试优化效果
- 收集用户反馈

## 总结

资源优化是一个持续的过程，需要结合多种技术和策略。通过合理的图片优化、CSS优化、缓存策略和性能监控，可以显著提升网站性能，改善用户体验。记住，优化应该是数据驱动的，通过监控和分析来指导优化方向。

---

*本指南将根据技术的发展持续更新，建议定期查阅最新版本。*