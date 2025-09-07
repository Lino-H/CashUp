/**
 * CSS优化工具类
 * CSS Optimization Utility Class
 */

export class CSSOptimizer {
  /**
   * 最小化CSS样式
   * Minimize CSS styles
   */
  static minifyCSS(css: string): string {
    return css
      // 移除注释
      .replace(/\/\*[\s\S]*?\*\//g, '')
      // 移除多余空格
      .replace(/\s{2,}/g, ' ')
      // 移除换行符
      .replace(/\n/g, '')
      // 移除冒号前的空格
      .replace(/\s*:\s*/g, ':')
      // 移除分号前的空格
      .replace(/\s*;\s*/g, ';')
      // 移除逗号前的空格
      .replace(/\s*,\s*/g, ',')
      // 移除花括号前的空格
      .replace(/\s*{\s*/g, '{')
      .replace(/\s*}\s*/g, '}')
      // 移除属性值前的空格
      .replace(/\s*([>~+])\s*/g, '$1')
      // 移除选择器中的多余空格
      .replace(/\s*([>+~])\s*/g, '$1')
      .replace(/\s*([,>~+])\s*/g, '$1')
      // 清理空规则
      .replace(/;}/g, '}')
      // 清理多余的分号
      .replace(/;+/g, ';')
      // 确保以分号结束
      .replace(/;$/, '');
  }

  /**
   * 生成CSS变量主题
   * Generate CSS variables for theme
   */
  static generateThemeVariables(): string {
    return `
      :root {
        --primary-color: #1890ff;
        --success-color: #52c41a;
        --warning-color: #faad14;
        --error-color: #ff4d4f;
        --text-primary: #333;
        --text-secondary: #666;
        --text-muted: #999;
        --border-color: #d9d9d9;
        --background-color: #fff;
        --shadow-color: rgba(0, 0, 0, 0.1);
        --border-radius: 6px;
        --transition-duration: 0.2s;
        --font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
      }
      
      [data-theme="dark"] {
        --primary-color: #1890ff;
        --success-color: #52c41a;
        --warning-color: #faad14;
        --error-color: #ff4d4f;
        --text-primary: #fff;
        --text-secondary: #ccc;
        --text-muted: #999;
        --border-color: #434343;
        --background-color: #141414;
        --shadow-color: rgba(0, 0, 0, 0.3);
      }
    `;
  }

  /**
   * 生成响应式断点变量
   * Generate responsive breakpoint variables
   */
  static generateResponsiveBreakpoints(): string {
    return `
      :root {
        --breakpoint-xs: 0px;
        --breakpoint-sm: 576px;
        --breakpoint-md: 768px;
        --breakpoint-lg: 992px;
        --breakpoint-xl: 1200px;
        --breakpoint-xxl: 1600px;
        --container-xs: 100%;
        --container-sm: 540px;
        --container-md: 720px;
        --container-lg: 960px;
        --container-xl: 1140px;
        --container-xxl: 1320px;
      }
    `;
  }

  /**
   * 生成优化的滚动条样式
   * Generate optimized scrollbar styles
   */
  static generateScrollbarStyles(): string {
    return `
      ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
      }
      
      ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 3px;
      }
      
      ::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 3px;
        transition: background 0.2s ease;
      }
      
      ::-webkit-scrollbar-thumb:hover {
        background: #555;
      }
      
      ::-webkit-scrollbar-corner {
        background: #f1f1f1;
      }
      
      /* Firefox */
      * {
        scrollbar-width: thin;
        scrollbar-color: #888 #f1f1f1;
      }
    `;
  }

  /**
   * 生成动画关键帧
   * Generate animation keyframes
   */
  static generateAnimations(): string {
    return `
      @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
      }
      
      @keyframes slideIn {
        from { transform: translateY(-10px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
      }
      
      @keyframes slideOut {
        from { transform: translateY(0); opacity: 1; }
        to { transform: translateY(-10px); opacity: 0; }
      }
      
      @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
      }
      
      @keyframes rotate {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }
      
      @keyframes shake {
        0%, 100% { transform: translateX(0); }
        10%, 30%, 50%, 70%, 90% { transform: translateX(-2px); }
        20%, 40%, 60%, 80% { transform: translateX(2px); }
      }
      
      @keyframes bounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-10px); }
        60% { transform: translateY(-5px); }
      }
    `;
  }

  /**
   * 生成优化的字体加载样式
   * Generate optimized font loading styles
   */
  static generateFontLoading(): string {
    return `
      /* 字体优化 */
      @font-face {
        font-family: 'Inter';
        font-style: normal;
        font-weight: 400;
        font-display: swap;
        src: url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
      }
      
      /* 防止字体闪烁 */
      body {
        font-family: var(--font-family);
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        text-rendering: optimizeLegibility;
      }
      
      /* 字体加载优化 */
      .font-loading {
        font-family: system-ui, -apple-system, sans-serif;
      }
    `;
  }

  /**
   * 生成CSS优化报告
   * Generate CSS optimization report
   */
  static generateOptimizationReport(): string {
    return `
      /* CSS优化报告 */
      /* CSS Optimization Report */
      /* Generated: ${new Date().toISOString()} */
      
      /* 优化项目:
       * 1. 移除注释和多余空格
       * 2. 生成CSS变量主题
       * 3. 响应式断点优化
       * 4. 滚动条样式优化
       * 5. 动画关键帧优化
       * 6. 字体加载优化
       */
    `;
  }

  /**
   * 应用所有优化
   * Apply all optimizations
   */
  static applyAllOptimizations(): string {
    return `
      ${this.generateOptimizationReport()}
      ${this.generateThemeVariables()}
      ${this.generateResponsiveBreakpoints()}
      ${this.generateScrollbarStyles()}
      ${this.generateAnimations()}
      ${this.generateFontLoading()}
    `;
  }
}

export default CSSOptimizer;