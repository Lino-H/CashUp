import React, { useState, useEffect, useCallback } from 'react';
import { Card, Row, Col, Statistic, Progress, Table, Button, Badge, Alert, Space, Modal, Typography } from 'antd';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import ResourceOptimizationManager, { ResourceOptimizationConfig } from '../utils/resourceOptimization';

const { Title, Text, Paragraph } = Typography;
const { Option } = require('antd');

interface ResourceOptimizationMonitorProps {
  config?: Partial<ResourceOptimizationConfig>;
  visible?: boolean;
  onClose?: () => void;
}

const ResourceOptimizationMonitor: React.FC<ResourceOptimizationMonitorProps> = ({
  config,
  visible = true,
  onClose,
}) => {
  const [manager, setManager] = useState<ResourceOptimizationManager | null>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [chartData, setChartData] = useState<any[]>([]);

  // 初始化资源优化管理器
  useEffect(() => {
    const newManager = new ResourceOptimizationManager(config);
    setManager(newManager);
    
    // 开始性能监控
    newManager.startPerformanceMonitoring();
    
    // 定期更新指标
    const interval = setInterval(() => {
      updateMetrics();
    }, 5000);

    // 获取优化建议
    setSuggestions(newManager.getOptimizationSuggestions());

    return () => {
      clearInterval(interval);
      newManager.cleanup();
    };
  }, [config]);

  // 更新指标
  const updateMetrics = useCallback(() => {
    if (!manager) return;

    const performanceMetrics = manager.getPerformanceMetrics();
    const report = manager.generateOptimizationReport();
    
    setMetrics({
      performanceMetrics,
      report,
    });

    // 更新图表数据
    const now = new Date().toLocaleTimeString();
    const newChartData = {
      time: now,
      imageCompression: report.summary.totalImageCompression || 0,
      cssCompression: report.summary.totalCSSCompression || 0,
      resourceSavings: report.summary.totalResourceSavings || 0,
      averageLoadTime: report.summary.averageLoadTime || 0,
    };

    setChartData(prev => {
      const newData = [...prev, newChartData];
      // 只保留最近20个数据点
      return newData.slice(-20);
    });
  }, [manager]);

  // 手动刷新数据
  const handleRefresh = useCallback(() => {
    setLoading(true);
    updateMetrics();
    setTimeout(() => setLoading(false), 1000);
  }, [updateMetrics]);

  // 更新配置
  const handleConfigChange = useCallback((newConfig: Partial<ResourceOptimizationConfig>) => {
    if (manager) {
      manager.updateConfig(newConfig);
      setSuggestions(manager.getOptimizationSuggestions());
    }
  }, [manager]);

  // 如果不可见，不渲染组件
  if (!visible) return null;

  const columns = [
    {
      title: '资源类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Badge 
          color={type === 'image' ? 'blue' : type === 'css' ? 'green' : 'orange'}
          text={type.toUpperCase()}
        />
      ),
    },
    {
      title: 'URL',
      dataIndex: 'url',
      key: 'url',
      ellipsis: true,
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      render: (size: number) => `${(size / 1024).toFixed(2)} KB`,
    },
    {
      title: '加载时间',
      dataIndex: 'loadTime',
      key: 'loadTime',
      render: (loadTime: number) => `${loadTime.toFixed(2)} ms`,
    },
    {
      title: '缓存状态',
      dataIndex: 'cached',
      key: 'cached',
      render: (cached: boolean) => (
        <Badge color={cached ? 'green' : 'red'} text={cached ? '已缓存' : '未缓存'} />
      ),
    },
  ];

  if (!metrics) {
    return (
      <div style={{ padding: 24 }}>
        <Card loading />
      </div>
    );
  }

  const { report } = metrics;

  return (
    <div style={{ padding: 24 }}>
      {/* 标题和控制 */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={3}>资源优化监控</Title>
          <Text type="secondary">实时监控资源优化性能指标</Text>
        </Col>
        <Col>
          <Space>
            <Button type="primary" onClick={handleRefresh} loading={loading}>
              刷新数据
            </Button>
            <Button onClick={() => handleConfigChange({})}>
              配置设置
            </Button>
          </Space>
        </Col>
      </Row>

      {/* 概览统计 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="图片压缩率"
              value={report.summary.totalImageCompression}
              suffix="%"
              precision={1}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="CSS压缩率"
              value={report.summary.totalCSSCompression}
              suffix="%"
              precision={1}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="资源节省"
              value={report.summary.totalResourceSavings}
              suffix="KB"
              precision={2}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="平均加载时间"
              value={report.summary.averageLoadTime}
              suffix="ms"
              precision={2}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

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

      {/* 性能趋势图表 */}
      <Card title="性能趋势" style={{ marginBottom: 24 }}>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="imageCompression"
              stroke="#1890ff"
              name="图片压缩率 (%)"
            />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="cssCompression"
              stroke="#52c41a"
              name="CSS压缩率 (%)"
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="averageLoadTime"
              stroke="#722ed1"
              name="平均加载时间 (ms)"
            />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      {/* 资源使用分布 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card title="资源类型分布">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={[
                    { name: '图片', value: metrics.performanceMetrics.images.length || 0 },
                    { name: 'CSS', value: metrics.performanceMetrics.css.length || 0 },
                    { name: 'JS', value: metrics.performanceMetrics.resources.filter((r: any) => r.type === 'js').length || 0 },
                    { name: '字体', value: metrics.performanceMetrics.resources.filter((r: any) => r.type === 'font').length || 0 },
                  ]}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  fill="#8884d8"
                >
                  <Cell fill="#1890ff" />
                  <Cell fill="#52c41a" />
                  <Cell fill="#faad14" />
                  <Cell fill="#722ed1" />
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="资源大小分布">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={metrics.performanceMetrics.resources.slice(0, 10)}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="url" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="size" fill="#1890ff" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* 资源详情表格 */}
      <Card title="资源详情">
        <Table
          columns={columns}
          dataSource={metrics.performanceMetrics.resources}
          rowKey="url"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
          }}
          scroll={{ x: 800 }}
          bordered
        />
      </Card>

      {/* 配置模态框 */}
      <Modal
        title="资源优化配置"
        open={false}
        onCancel={onClose}
        footer={null}
        width={600}
      >
        <div>
          <Title level={4}>图片优化配置</Title>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div>
              <Text>图片质量: {manager?.getConfig().images.quality}%</Text>
              <Progress 
                percent={manager?.getConfig().images.quality} 
                strokeColor="#1890ff" 
              />
            </div>
            <div>
              <Text>最大宽度: {manager?.getConfig().images.maxWidth}px</Text>
            </div>
            <div>
              <Text>最大高度: {manager?.getConfig().images.maxHeight}px</Text>
            </div>
          </Space>
        </div>
      </Modal>
    </div>
  );
};

export default ResourceOptimizationMonitor;
