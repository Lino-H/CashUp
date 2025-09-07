/**
 * 全局错误边界组件 - 捕获和处理React组件错误
 */

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Result, Button, Typography, Card } from 'antd';

const { Title, Paragraph } = Typography;

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo
    });
  }

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });
  };

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div style={{ padding: '24px', textAlign: 'center' }}>
          <Card>
            <Result
              status="error"
              title="系统出现错误"
              subTitle="很抱歉，系统遇到了一个意外错误。请尝试刷新页面或联系技术支持。"
              extra={[
                <Button type="primary" key="retry" onClick={this.handleReset}>
                  重试
                </Button>,
                <Button key="refresh" onClick={() => window.location.reload()}>
                  刷新页面
                </Button>,
              ]}
            />
            
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div style={{ marginTop: '24px', textAlign: 'left', background: '#f5f5f5', padding: '16px', borderRadius: '4px' }}>
                <Title level={4}>错误详情 (开发模式)</Title>
                <Paragraph>
                  <strong>错误信息:</strong> {this.state.error.message}
                </Paragraph>
                <Paragraph>
                  <strong>错误堆栈:</strong>
                  <pre style={{ background: '#fff', padding: '8px', borderRadius: '4px', overflow: 'auto' }}>
                    {this.state.error.stack}
                  </pre>
                </Paragraph>
                {this.state.errorInfo && (
                  <>
                    <Paragraph>
                      <strong>组件堆栈:</strong>
                      <pre style={{ background: '#fff', padding: '8px', borderRadius: '4px', overflow: 'auto' }}>
                        {this.state.errorInfo.componentStack}
                      </pre>
                    </Paragraph>
                  </>
                )}
              </div>
            )}
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;