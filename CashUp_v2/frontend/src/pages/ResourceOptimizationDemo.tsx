import React, { useState } from 'react';
import { Card, Row, Col, Button, Upload, Space, Alert, Statistic, Progress, Typography } from 'antd';
import OptimizedImage from '../components/OptimizedImage';
import ResourceOptimizationManager from '../utils/resourceOptimization';
import ResourceOptimizationMonitor from '../components/ResourceOptimizationMonitor';
import {
  UploadOutlined,
  PictureOutlined,
  EyeOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;
const { Dragger } = Upload;

const ResourceOptimizationDemo: React.FC = () => {
  const [selectedImages, setSelectedImages] = useState<File[]>([]);
  const [optimizedImages, setOptimizedImages] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<any>(null);
  const [manager] = useState(new ResourceOptimizationManager());

  // 处理文件上传
  const handleUpload = (info: any) => {
    if (info.file.status === 'done') {
      setSelectedImages(info.file.originFileList);
    }
  };

  // 优化图片
  const handleOptimizeImages = async () => {
    if (selectedImages.length === 0) return;

    setLoading(true);
    try {
      const { optimizedFiles, report: optimizationReport } = await manager.optimizeImages(selectedImages);
      
      // 转换优化后的图片为DataURL
      const dataUrls = await Promise.all(
        optimizedFiles.map(blob => URL.createObjectURL(blob))
      );
      
      setOptimizedImages(dataUrls);
      setReport(optimizationReport);
    } catch (error) {
      console.error('图片优化失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 重置
  const handleReset = () => {
    setSelectedImages([]);
    setOptimizedImages([]);
    setReport(null);
    // 清理旧的URL
    optimizedImages.forEach(url => URL.revokeObjectURL(url));
  };

  // 获取优化建议
  const suggestions = manager.getOptimizationSuggestions();

  return (
    <div style={{ padding: 24 }}>
      {/* 标题 */}
      <Title level={2}>资源优化演示</Title>
      <Paragraph type="secondary">
        演示图片优化、CSS优化等资源优化功能
      </Paragraph>

      {/* 资源优化监控 */}
      <Card title="资源优化监控" style={{ marginBottom: 24 }}>
        <ResourceOptimizationMonitor 
          config={{
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
              cacheTTL: 7 * 24 * 60 * 60 * 1000,
            },
            monitoring: {
              enablePerformanceMonitoring: true,
              enableErrorTracking: true,
              enableResourceTracking: true,
              reportInterval: 60000,
            },
          }}
        />
      </Card>

      {/* 图片上传和优化 */}
      <Card title="图片优化演示" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          <Col span={12}>
            <Title level={4}>上传图片</Title>
            <Dragger
              multiple
              beforeUpload={() => false}
              onChange={handleUpload}
              showUploadList={false}
            >
              <p className="ant-upload-drag-icon">
                <UploadOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">支持JPG、PNG、WebP格式</p>
            </Dragger>

            {selectedImages.length > 0 && (
              <div style={{ marginTop: 16 }}>
                <Text>已选择 {selectedImages.length} 个文件</Text>
                <div style={{ marginTop: 8 }}>
                  {selectedImages.map((file, index) => (
                    <div key={index} style={{ 
                      padding: 8, 
                      margin: 4, 
                      backgroundColor: '#f5f5f5', 
                      borderRadius: 4 
                    }}>
                      <Text>{file.name}</Text>
                      <Text type="secondary">({(file.size / 1024).toFixed(2)} KB)</Text>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <Space style={{ marginTop: 16 }}>
              <Button 
                type="primary" 
                icon={<PictureOutlined />}
                onClick={handleOptimizeImages}
                loading={loading}
                disabled={selectedImages.length === 0}
              >
                优化图片
              </Button>
              <Button onClick={handleReset}>
                重置
              </Button>
            </Space>
          </Col>

          <Col span={12}>
            <Title level={4}>优化结果</Title>
            {report && (
              <div>
                <div style={{ marginBottom: 16 }}>
                  <Statistic
                    title="压缩率"
                    value={report.totalCompressionRate}
                    suffix="%"
                    precision={1}
                    valueStyle={{ color: '#1890ff' }}
                  />
                </div>
                
                <div style={{ marginBottom: 16 }}>
                  <Progress
                    percent={report.totalCompressionRate}
                    strokeColor="#1890ff"
                    format={(percent) => `${percent}%`}
                  />
                </div>

                <div style={{ marginBottom: 16 }}>
                  <Text strong>原始大小: {(report.totalOriginalSize / 1024).toFixed(2)} KB</Text>
                  <Text strong style={{ marginLeft: 16 }}>优化后: {(report.totalOptimizedSize / 1024).toFixed(2)} KB</Text>
                  <Text strong style={{ marginLeft: 16 }}>节省: {((report.totalOriginalSize - report.totalOptimizedSize) / 1024).toFixed(2)} KB</Text>
                </div>

                <div>
                  <Title level={5}>文件详情:</Title>
                  {report.fileReports.map((file: any, index: number) => (
                    <div key={index} style={{ marginBottom: 8 }}>
                      <Text>{file.fileName}</Text>
                      <div>
                        <Progress
                          percent={file.compressionRate}
                          size="small"
                          strokeColor={file.compressionRate > 50 ? '#52c41a' : '#faad14'}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Col>
        </Row>
      </Card>

      {/* 优化建议 */}
      {suggestions.length > 0 && (
        <Card title="优化建议" style={{ marginBottom: 24 }}>
          <Alert
            message="发现优化机会"
            description={
              <ul>
                {suggestions.map((suggestion, index) => (
                  <li key={index}>{suggestion}</li>
                ))}
              </ul>
            }
            type="info"
            showIcon
          />
        </Card>
      )}

      {/* 优化后的图片展示 */}
      {optimizedImages.length > 0 && (
        <Card title="优化后的图片" style={{ marginBottom: 24 }}>
          <Row gutter={[16, 16]}>
            {optimizedImages.map((src, index) => (
              <Col key={index} span={8}>
                <Card>
                  <div style={{ textAlign: 'center' }}>
                    <OptimizedImage
                      src={src}
                      alt={`优化后的图片 ${index + 1}`}
                      width={200}
                      height={200}
                      style={{ 
                        width: '100%', 
                        height: 200, 
                        objectFit: 'cover',
                        borderRadius: 8 
                      }}
                    />
                    <div style={{ marginTop: 8 }}>
                      <Space>
                        <Button 
                          type="primary" 
                          icon={<EyeOutlined />}
                          onClick={() => window.open(src, '_blank')}
                        >
                          查看
                        </Button>
                        <Button 
                          type="dashed"
                          icon={<CheckCircleOutlined />}
                          onClick={() => {
                            const link = document.createElement('a');
                            link.href = src;
                            link.download = `optimized-${index + 1}.webp`;
                            link.click();
                          }}
                        >
                          下载
                        </Button>
                      </Space>
                    </div>
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        </Card>
      )}

      {/* 使用示例 */}
      <Card title="使用示例">
        <Title level={4}>1. 基础图片优化</Title>
        <Paragraph>
          使用<code>OptimizedImage</code>组件来自动优化图片
        </Paragraph>
        
        <pre style={{ 
          background: '#f5f5f5', 
          padding: 16, 
          borderRadius: 4,
          fontSize: 12 
        }}>
{`<OptimizedImage
  src="/path/to/image.jpg"
  alt="描述文字"
  width={300}
  height={200}
  quality={85}
  maxWidth={800}
  maxHeight={600}
/>`}
        </pre>

        <Title level={4} style={{ marginTop: 24 }}>2. 图片批量优化</Title>
        <Paragraph>
          使用<code>OptimizedImageBatch</code>组件批量优化图片
        </Paragraph>
        
        <pre style={{ 
          background: '#f5f5f5', 
          padding: 16, 
          borderRadius: 4,
          fontSize: 12 
        }}>
{`<OptimizedImageBatch
  images={[
    { src: "/path/to/image1.jpg", alt: "图片1" },
    { src: "/path/to/image2.jpg", alt: "图片2" },
    { src: "/path/to/image3.jpg", alt: "图片3" },
  ]}
  onAllLoaded={() => console.log('所有图片加载完成')}
  onError={(index, error) => console.error('图片加载失败:', index, error)}
/>`}
        </pre>

        <Title level={4} style={{ marginTop: 24 }}>3. CSS优化</Title>
        <Paragraph>
          使用<code>optimizeCSS</code>函数来优化CSS代码
        </Paragraph>
        
        <pre style={{ 
          background: '#f5f5f5', 
          padding: 16, 
          borderRadius: 4,
          fontSize: 12 
        }}>
{`import { ResourceOptimizationManager } from './utils/resourceOptimization';

const manager = new ResourceOptimizationManager();
const { optimizedCSS, report } = manager.optimizeCSS(cssString);

console.log('优化后的CSS:', optimizedCSS);
console.log('压缩率:', report.compressionRate + '%');`}
        </pre>
      </Card>
    </div>
  );
};

export default ResourceOptimizationDemo;