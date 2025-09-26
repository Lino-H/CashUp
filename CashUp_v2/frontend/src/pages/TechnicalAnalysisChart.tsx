import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Alert, Spin, Progress, List, Tag, Typography, Divider } from 'antd';
import { LineChartOutlined, BarChartOutlined, RiseOutlined, FallOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';

const { Title, Text, Paragraph } = Typography;

interface TechnicalIndicators {
  ma5: number;
  ma10: number;
  ma20: number;
  ma50: number;
  macd: number;
  signal: number;
  histogram: number;
  rsi: number;
  kdj_k: number;
  kdj_d: number;
  kdj_j: number;
  bb_upper: number;
  bb_middle: number;
  bb_lower: number;
}

const TechnicalAnalysisChart: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<{
    score: number;
    indicators: TechnicalIndicators;
    trend: string;
    signal: string;
    last_updated: string;
  } | null>(null);

  useEffect(() => {
    if (isAuthenticated) {
      fetchTechnicalAnalysis();
    }
  }, [isAuthenticated]);

  const fetchTechnicalAnalysis = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/config/analysis/technical', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const result = await response.json();
        setData(result);
      }
    } catch (error) {
      console.error('获取技术分析数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRSIStatus = (rsi: number) => {
    if (rsi < 30) return { color: '#f5222d', text: '超卖' };
    if (rsi > 70) return { color: '#52c41a', text: '超买' };
    return { color: '#faad14', text: '正常' };
  };

  const getMACDSignal = (histogram: number) => {
    if (histogram > 0) return { color: '#52c41a', text: '多头信号' };
    if (histogram < 0) return { color: '#f5222d', text: '空头信号' };
    return { color: '#faad14', text: '中性' };
  };

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case '买入': return '#52c41a';
      case '卖出': return '#f5222d';
      default: return '#faad14';
    }
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case '上涨': return '#52c41a';
      case '下跌': return '#f5222d';
      default: return '#faad14';
    }
  };

  if (!isAuthenticated) {
    return (
      <Card>
        <Alert message="请先登录" type="warning" showIcon />
      </Card>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <Title level={3}>技术分析</Title>
      <Paragraph>
        基于移动平均线、MACD、RSI、KDJ、布林带等技术指标的专业分析
      </Paragraph>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin size="large" />
        </div>
      ) : data ? (
        <>
          {/* 总体评分 */}
          <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
            <Col span={8}>
              <Card>
                <Statistic
                  title="技术评分"
                  value={data.score}
                  suffix="/100"
                  valueStyle={{ color: '#1890ff' }}
                  prefix={<LineChartOutlined />}
                />
                <Progress percent={data.score} strokeColor="#1890ff" />
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic
                  title="趋势"
                  value={data.trend}
                  valueStyle={{ color: getTrendColor(data.trend) }}
                  prefix={data.trend === '上涨' ? <RiseOutlined /> : <FallOutlined />}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic
                  title="信号"
                  value={data.signal}
                  valueStyle={{ color: getSignalColor(data.signal) }}
                />
              </Card>
            </Col>
          </Row>

          {/* 技术指标 */}
          <Title level={4}>技术指标详情</Title>
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Card title="移动平均线" style={{ marginBottom: '16px' }}>
                <Row gutter={[16, 16]}>
                  <Col span={6}>
                    <Text>MA5: </Text>
                    <Text strong>{data.indicators.ma5.toFixed(2)}</Text>
                  </Col>
                  <Col span={6}>
                    <Text>MA10: </Text>
                    <Text strong>{data.indicators.ma10.toFixed(2)}</Text>
                  </Col>
                  <Col span={6}>
                    <Text>MA20: </Text>
                    <Text strong>{data.indicators.ma20.toFixed(2)}</Text>
                  </Col>
                  <Col span={6}>
                    <Text>MA50: </Text>
                    <Text strong>{data.indicators.ma50.toFixed(2)}</Text>
                  </Col>
                </Row>
              </Card>
            </Col>
            <Col span={12}>
              <Card title="MACD指标" style={{ marginBottom: '16px' }}>
                <Row gutter={[16, 16]}>
                  <Col span={8}>
                    <Text>MACD: </Text>
                    <Text strong>{data.indicators.macd.toFixed(3)}</Text>
                  </Col>
                  <Col span={8}>
                    <Text>Signal: </Text>
                    <Text strong>{data.indicators.signal.toFixed(3)}</Text>
                  </Col>
                  <Col span={8}>
                    <Text>Histogram: </Text>
                    <Text strong>{data.indicators.histogram.toFixed(3)}</Text>
                  </Col>
                </Row>
                <div style={{ marginTop: '8px' }}>
                  <Tag color={getMACDSignal(data.indicators.histogram).color}>
                    {getMACDSignal(data.indicators.histogram).text}
                  </Tag>
                </div>
              </Card>
            </Col>
          </Row>

          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Card title="RSI指标">
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Text>RSI(14): </Text>
                    <Text strong>{data.indicators.rsi.toFixed(2)}</Text>
                  </Col>
                  <Col span={12}>
                    <Tag color={getRSIStatus(data.indicators.rsi).color}>
                      {getRSIStatus(data.indicators.rsi).text}
                    </Tag>
                  </Col>
                </Row>
              </Card>
            </Col>
            <Col span={12}>
              <Card title="KDJ指标">
                <Row gutter={[16, 16]}>
                  <Col span={8}>
                    <Text>K: </Text>
                    <Text strong>{data.indicators.kdj_k.toFixed(2)}</Text>
                  </Col>
                  <Col span={8}>
                    <Text>D: </Text>
                    <Text strong>{data.indicators.kdj_d.toFixed(2)}</Text>
                  </Col>
                  <Col span={8}>
                    <Text>J: </Text>
                    <Text strong>{data.indicators.kdj_j.toFixed(2)}</Text>
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>

          <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
            <Col span={24}>
              <Card title="布林带">
                <Row gutter={[16, 16]}>
                  <Col span={6}>
                    <Text>上轨: </Text>
                    <Text strong>{data.indicators.bb_upper.toFixed(2)}</Text>
                  </Col>
                  <Col span={6}>
                    <Text>中轨: </Text>
                    <Text strong>{data.indicators.bb_middle.toFixed(2)}</Text>
                  </Col>
                  <Col span={6}>
                    <Text>下轨: </Text>
                    <Text strong>{data.indicators.bb_lower.toFixed(2)}</Text>
                  </Col>
                  <Col span={6}>
                    <Text>带宽: </Text>
                    <Text strong>
                      {((data.indicators.bb_upper - data.indicators.bb_lower) / data.indicators.bb_middle * 100).toFixed(2)}%
                    </Text>
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>

          {/* 分析建议 */}
          <Divider />
          <Card title="分析建议">
            <List
              dataSource={[
                {
                  title: '趋势分析',
                  description: `当前价格${data.trend}，建议关注${data.signal === '买入' ? '逢低买入机会' : data.signal === '卖出' ? '逢高减仓' : '观望等待'}。`
                },
                {
                  title: '技术指标确认',
                  description: `RSI指标${getRSIStatus(data.indicators.rsi).text}，MACD${getMACDSignal(data.indicators.histogram).text}，多个指标形成${data.signal === '买入' ? '共振买入信号' : data.signal === '卖出' ? '共振卖出信号' : '分化信号'}。`
                },
                {
                  title: '风险提示',
                  description: `布林带收窄表明波动率降低，市场可能即将选择方向。建议控制仓位，设置止损。`
                }
              ]}
              renderItem={(item) => <List.Item><List.Item.Meta title={item.title} description={item.description} /></List.Item>}
            />
          </Card>

          {/* 更新时间 */}
          <Divider />
          <Text type="secondary">
            最后更新时间: {new Date(data.last_updated).toLocaleString('zh-CN')}
          </Text>
        </>
      ) : (
        <Card>
          <Alert message="暂无技术分析数据" type="info" showIcon />
        </Card>
      )}
    </div>
  );
};

export default TechnicalAnalysisChart;