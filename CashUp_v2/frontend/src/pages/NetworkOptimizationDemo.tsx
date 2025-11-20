import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Button, Input, Space, Statistic, Progress, Table, Typography, Switch, InputNumber, Tag } from 'antd';
import { networkOptimizationManager } from '../utils/networkOptimization';
import {
  ReloadOutlined,
  DownloadOutlined,
  CheckCircleOutlined,
  SyncOutlined,
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

// 模拟API请求函数
const mockApiRequest = (delay: number = 1000): Promise<string> => {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(`API Response ${Date.now()}`);
    }, delay);
  });
};


const NetworkOptimizationDemo: React.FC = () => {
  const [config, setConfig] = useState({
    cacheEnabled: true,
    cacheFirst: true,
    deduplicationEnabled: true,
    staleWhileRevalidate: true,
    cacheTTL: 5 * 60 * 1000,
    deduplicationTimeout: 30 * 1000,
    maxConcurrent: 10,
  });

  const [metrics, setMetrics] = useState(networkOptimizationManager.getMetrics());
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [testUrl, setTestUrl] = useState('/api/test');
  const [testParams, setTestParams] = useState('{}');

  // 定期更新指标
  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(networkOptimizationManager.getMetrics());
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // 处理配置更改
  const handleConfigChange = (key: string, value: any) => {
    const newConfig = { ...config, [key]: value };
    setConfig(newConfig);
    
    networkOptimizationManager.updateConfig({
      cache: {
        enabled: newConfig.cacheEnabled,
        defaultTTL: newConfig.cacheTTL,
        maxSize: 50 * 1024 * 1024,
        maxEntries: 1000,
        compression: true,
      },
      deduplication: {
        enabled: newConfig.deduplicationEnabled,
        timeout: newConfig.deduplicationTimeout,
        maxConcurrent: newConfig.maxConcurrent,
        deduplicationWindow: 5 * 60 * 1000,
        maxRetries: 3,
      },
      cacheFirst: newConfig.cacheFirst,
      networkFirst: !newConfig.cacheFirst,
      staleWhileRevalidate: newConfig.staleWhileRevalidate,
    });
  };

  // 单个请求测试
  const handleSingleRequest = async () => {
    setLoading(true);
    try {
      const params = testParams ? JSON.parse(testParams) : undefined;
      
      const startTime = Date.now();
      const result = await networkOptimizationManager.optimizedRequest(
        'GET',
        testUrl,
        () => mockApiRequest(1000),
        params
      );
      const endTime = Date.now();
      
      setResults(prev => [...prev, {
        key: Date.now(),
        type: 'Single Request',
        url: testUrl,
        params: JSON.stringify(params),
        result: result.substring(0, 50) + '...',
        responseTime: endTime - startTime,
        status: 'success',
      }]);
    } catch (error) {
      setResults(prev => [...prev, {
        key: Date.now(),
        type: 'Single Request',
        url: testUrl,
        params: JSON.stringify(testParams),
        result: (error as any).message,
        responseTime: 0,
        status: 'error',
      }]);
    } finally {
      setLoading(false);
    }
  };

  // 并发请求测试
  const handleConcurrentRequests = async () => {
    setLoading(true);
    try {
      const requests = Array.from({ length: 5 }, (_, i) => ({
        method: 'GET' as const,
        url: `${testUrl}?id=${i}`,
        requestFn: () => mockApiRequest(500 + Math.random() * 1000),
        params: { id: i },
      }));

      const startTime = Date.now();
      const results = await networkOptimizationManager.batchRequest(requests);
      const endTime = Date.now();

      setResults(prev => [
        ...prev,
        ...results.map((result, index) => ({
          key: Date.now() + index,
          type: 'Concurrent Request',
          url: `${testUrl}?id=${index}`,
          params: JSON.stringify({ id: index }),
          result: result.success ? result.data?.substring(0, 50) + '...' : result.error?.message,
          responseTime: endTime - startTime,
          status: result.success ? 'success' : 'error',
        }))
      ]);
    } finally {
      setLoading(false);
    }
  };

  // 预加载测试
  const handlePreload = async () => {
    setLoading(true);
    try {
      const items = Array.from({ length: 3 }, (_, i) => ({
        method: 'GET' as const,
        url: `${testUrl}?preload=${i}`,
        requestFn: () => mockApiRequest(1000),
        params: { preload: i },
      }));

      await networkOptimizationManager.preloadCache(items);
      setResults(prev => [...prev, {
        key: Date.now(),
        type: 'Preload',
        url: 'Multiple URLs',
        params: 'preload items',
        result: 'Preload completed successfully',
        responseTime: 0,
        status: 'success',
      }]);
    } catch (error) {
      setResults(prev => [...prev, {
        key: Date.now(),
        type: 'Preload',
        url: 'Multiple URLs',
        params: 'preload items',
        result: (error as any).message,
        responseTime: 0,
        status: 'error',
      }]);
    } finally {
      setLoading(false);
    }
  };

  // 清空缓存
  const handleClearCache = async () => {
    try {
      await networkOptimizationManager.clearCache();
      setResults(prev => [...prev, {
        key: Date.now(),
        type: 'Clear Cache',
        url: 'N/A',
        params: 'N/A',
        result: 'Cache cleared successfully',
        responseTime: 0,
        status: 'success',
      }]);
    } catch (error) {
      setResults(prev => [...prev, {
        key: Date.now(),
        type: 'Clear Cache',
        url: 'N/A',
        params: 'N/A',
        result: (error as any).message,
        responseTime: 0,
        status: 'error',
      }]);
    }
  };

  // 模拟表格列
  const columns = [
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => <Tag>{type}</Tag>,
    },
    {
      title: 'URL',
      dataIndex: 'url',
      key: 'url',
    },
    {
      title: '参数',
      dataIndex: 'params',
      key: 'params',
      ellipsis: true,
    },
    {
      title: '结果',
      dataIndex: 'result',
      key: 'result',
      ellipsis: true,
    },
    {
      title: '响应时间',
      dataIndex: 'responseTime',
      key: 'responseTime',
      render: (time: number) => (
        <span className={time > 1000 ? 'text-red-500' : 'text-green-500'}>
          {time}ms
        </span>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'success' ? 'green' : 'red'}>
          {status}
        </Tag>
      ),
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      {/* 标题 */}
      <Title level={2}>网络优化演示</Title>
      <Paragraph type="secondary">
        演示缓存、请求去重等网络优化功能
      </Paragraph>

      {/* 配置面板 */}
      <Card title="配置面板" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          <Col span={8}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text>启用缓存:</Text>
              <Switch
                checked={config.cacheEnabled}
                onChange={(checked) => handleConfigChange('cacheEnabled', checked)}
              />
              
              <Text>缓存优先:</Text>
              <Switch
                checked={config.cacheFirst}
                onChange={(checked) => handleConfigChange('cacheFirst', checked)}
              />
              
              <Text>启用请求去重:</Text>
              <Switch
                checked={config.deduplicationEnabled}
                onChange={(checked) => handleConfigChange('deduplicationEnabled', checked)}
              />
              
              <Text>后台刷新:</Text>
              <Switch
                checked={config.staleWhileRevalidate}
                onChange={(checked) => handleConfigChange('staleWhileRevalidate', checked)}
              />
            </Space>
          </Col>

          <Col span={8}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text>缓存 TTL (ms):</Text>
              <InputNumber
                value={config.cacheTTL}
                onChange={(value) => handleConfigChange('cacheTTL', value)}
                style={{ width: '100%' }}
                min={1000}
                step={1000}
              />
              
              <Text>去重超时 (ms):</Text>
              <InputNumber
                value={config.deduplicationTimeout}
                onChange={(value) => handleConfigChange('deduplicationTimeout', value)}
                style={{ width: '100%' }}
                min={1000}
                step={1000}
              />
              
              <Text>最大并发数:</Text>
              <InputNumber
                value={config.maxConcurrent}
                onChange={(value) => handleConfigChange('maxConcurrent', value)}
                style={{ width: '100%' }}
                min={1}
                max={50}
              />
            </Space>
          </Col>

          <Col span={8}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text>测试 URL:</Text>
              <Input
                value={testUrl}
                onChange={(e) => setTestUrl(e.target.value)}
                placeholder="输入测试 URL"
              />
              
              <Text>测试参数 (JSON):</Text>
              <TextArea
                value={testParams}
                onChange={(e) => setTestParams(e.target.value)}
                placeholder='{"key": "value"}'
                rows={3}
              />
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 性能指标 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="缓存命中率"
              value={metrics.cache.hitRate}
              precision={2}
              suffix="%"
              valueStyle={{ color: '#1890ff' }}
            />
            <Progress
              percent={metrics.cache.hitRate}
              strokeColor="#1890ff"
              size="small"
            />
          </Card>
        </Col>

        <Col span={6}>
          <Card>
            <Statistic
              title="请求去重率"
              value={metrics.deduplication.totalRequests > 0 ? 
                (metrics.deduplication.deduplicatedRequests / metrics.deduplication.totalRequests) * 100 : 0}
              precision={2}
              suffix="%"
              valueStyle={{ color: '#52c41a' }}
            />
            <Progress
              percent={metrics.deduplication.totalRequests > 0 ? 
                (metrics.deduplication.deduplicatedRequests / metrics.deduplication.totalRequests) * 100 : 0}
              strokeColor="#52c41a"
              size="small"
            />
          </Card>
        </Col>

        <Col span={6}>
          <Card>
            <Statistic
              title="平均响应时间"
              value={metrics.performance.averageResponseTime}
              precision={2}
              suffix="ms"
              valueStyle={{ color: '#faad14' }}
            />
            <Text type="secondary">
              网络: {metrics.performance.networkLoadTime}ms
            </Text>
          </Card>
        </Col>

        <Col span={6}>
          <Card>
            <Statistic
              title="并发请求数"
              value={metrics.deduplication.concurrentRequests}
              valueStyle={{ color: '#722ed1' }}
            />
            <Text type="secondary">
              总请求: {metrics.performance.totalRequests}
            </Text>
          </Card>
        </Col>
      </Row>

      {/* 测试按钮 */}
      <Card title="测试功能" style={{ marginBottom: 24 }}>
        <Space>
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            onClick={handleSingleRequest}
            loading={loading}
          >
            单个请求
          </Button>
          
          <Button
            icon={<SyncOutlined />}
            onClick={handleConcurrentRequests}
            loading={loading}
          >
            并发请求
          </Button>
          
          <Button
            icon={<DownloadOutlined />}
            onClick={handlePreload}
            loading={loading}
          >
            预加载
          </Button>
          
          <Button
            icon={<CheckCircleOutlined />}
            onClick={handleClearCache}
            loading={loading}
          >
            清空缓存
          </Button>
        </Space>
      </Card>

      {/* 结果表格 */}
      {results.length > 0 && (
        <Card title="请求结果">
          <Table
            columns={columns}
            dataSource={results}
            pagination={{ pageSize: 10 }}
            scroll={{ x: 800 }}
          />
        </Card>
      )}

      {/* 使用说明 */}
      <Card title="使用说明">
        <Title level={4}>1. 缓存优化</Title>
        <Paragraph>
          - <strong>缓存优先</strong>: 优先从缓存获取数据，减少网络请求
          - <strong>缓存TTL</strong>: 设置缓存过期时间，确保数据新鲜度
          - <strong>后台刷新</strong>: 在返回缓存数据的同时，后台刷新最新数据
        </Paragraph>

        <Title level={4} style={{ marginTop: 16 }}>2. 请求去重</Title>
        <Paragraph>
          - <strong>去重机制</strong>: 相同请求不会重复发送，避免资源浪费
          - <strong>并发控制</strong>: 限制最大并发请求数，防止浏览器过载
          - <strong>超时重试</strong>: 自动重试失败的请求，提高成功率
        </Paragraph>

        <Title level={4} style={{ marginTop: 16 }}>3. 性能监控</Title>
        <Paragraph>
          - <strong>实时指标</strong>: 监控缓存命中率、响应时间等关键指标
          - <strong>结果追踪</strong>: 记录每个请求的详细信息和性能数据
          - <strong>配置调整</strong>: 实时调整优化策略，找到最佳性能平衡
        </Paragraph>
      </Card>
    </div>
  );
};

export default NetworkOptimizationDemo;
