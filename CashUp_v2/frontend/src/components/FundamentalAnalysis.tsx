/**
 * 基本面分析组件
 * Fundamental Analysis Component
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Table,
  Tag,
  Button,
  Space,
  Alert,
  Typography,
  Spin,
  Divider,
  Descriptions,
  List,
  Avatar,
  Rate,
  Tooltip,
} from 'antd';
import {
  DollarCircleOutlined,
  RiseOutlined,
  FallOutlined,
  TrophyOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  BarChartOutlined,
  PieChartOutlined,
  LineChartOutlined,
  ThunderboltOutlined,
  ReloadOutlined,
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;

export interface FundamentalData {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap: number;
  circulatingSupply: number;
  totalSupply: number;
  marketCapDominance: number;
  volume24h: number;
  volumeChange: number;
  allTimeHigh: number;
  allTimeHighDate: string;
  allTimeLow: number;
  allTimeLowDate: string;
  volatility: number;
  sentiment: number;
  fundamentals: {
    pe: number;
    pb: number;
    ps: number;
    dividend: number;
    roe: number;
    roa: number;
    debtToEquity: number;
    currentRatio: number;
    quickRatio: number;
    grossMargin: number;
    operatingMargin: number;
    netMargin: number;
  };
  news: Array<{
    title: string;
    source: string;
    time: string;
    sentiment: 'positive' | 'negative' | 'neutral';
    summary: string;
  }>;
  technicalRating: {
    overall: number;
    trend: number;
    momentum: number;
    volatility: number;
    volume: number;
  };
}

interface FundamentalAnalysisProps {
  symbol: string;
  data?: FundamentalData;
  loading?: boolean;
  onRefresh?: () => void;
  onCompare?: (symbol: string) => void;
}

const FundamentalAnalysis: React.FC<FundamentalAnalysisProps> = ({
  symbol,
  data,
  loading = false,
  onRefresh,
  onCompare,
}) => {
  const [selectedTab, setSelectedTab] = useState<'overview' | 'fundamentals' | 'news' | 'rating'>('overview');

  // 生成模拟数据（实际项目中应该从API获取）
  const fetchFundamentalData = async (): Promise<FundamentalData> => {
    // 这里应该调用真实的基本面分析API
    throw new Error('基本面分析API尚未实现');
  };

  const generateEmptyData = (): FundamentalData => ({
    symbol: 'BTC/USDT',
    name: 'Bitcoin',
    price: 45230.50,
    change: 1250.30,
    changePercent: 2.84,
    volume: 28456789012,
    marketCap: 875432100000000,
    circulatingSupply: 19350000,
    totalSupply: 21000000,
    marketCapDominance: 45.2,
    volume24h: 28456789012,
    volumeChange: 5.67,
    allTimeHigh: 69000,
    allTimeHighDate: '2021-11-10',
    allTimeLow: 65.53,
    allTimeLowDate: '2010-07-17',
    volatility: 0.68,
    sentiment: 0.72,
    fundamentals: {
      pe: 25.8,
      pb: 3.2,
      ps: 8.5,
      dividend: 0,
      roe: 15.6,
      roa: 8.9,
      debtToEquity: 0.15,
      currentRatio: 2.4,
      quickRatio: 2.1,
      grossMargin: 68.5,
      operatingMargin: 45.2,
      netMargin: 38.9,
    },
    news: [
      {
        title: '比特币ETF通过审批，机构投资者大量买入',
        source: '华尔街日报',
        time: '2小时前',
        sentiment: 'positive',
        summary: '美国证券交易委员会批准了比特币ETF产品，预计将吸引大量机构资金流入。'
      },
      {
        title: '机构投资者对比特币兴趣持续升温',
        source: '金融时报',
        time: '4小时前',
        sentiment: 'positive',
        summary: '大型资产管理公司持续增加比特币配置，认为这是对冲通胀的有效工具。'
      },
      {
        title: '监管政策存在不确定性',
        source: '彭博社',
        time: '6小时前',
        sentiment: 'negative',
        summary: '全球各国监管政策仍然存在不确定性，可能影响市场短期走势。'
      }
    ],
    technicalRating: {
      overall: 75,
      trend: 80,
      momentum: 70,
      volatility: 65,
      volume: 85,
    },
  });

  const fundamentalData = data || generateEmptyData();

  // 计算综合评分
  const calculateScore = (data: FundamentalData): number => {
    const { fundamentals, technicalRating, sentiment } = data;
    
    const fundamentalScore = (
      Math.max(0, 100 - fundamentals.pe) * 0.2 +
      Math.min(100, fundamentals.roe * 5) * 0.15 +
      Math.min(100, fundamentals.roa * 10) * 0.1 +
      Math.max(0, 100 - fundamentals.debtToEquity * 200) * 0.15 +
      fundamentals.grossMargin * 0.1 +
      fundamentals.operatingMargin * 0.1 +
      fundamentals.netMargin * 0.1 +
      sentiment * 100 * 0.1
    );
    
    const technicalScore = (
      technicalRating.overall * 0.4 +
      technicalRating.trend * 0.3 +
      technicalRating.momentum * 0.2 +
      technicalRating.volume * 0.1
    );
    
    return Math.round((fundamentalScore + technicalScore) / 2);
  };

  const overallScore = calculateScore(fundamentalData);

  // 基本面数据表格
  const fundamentalColumns = [
    {
      title: '指标',
      dataIndex: 'metric',
      key: 'metric',
    },
    {
      title: '数值',
      dataIndex: 'value',
      key: 'value',
    },
    {
      title: '行业平均',
      dataIndex: 'industryAvg',
      key: 'industryAvg',
    },
    {
      title: '评级',
      dataIndex: 'rating',
      key: 'rating',
      render: (rating: number) => {
        let color = 'default';
        if (rating >= 80) color = 'success';
        else if (rating >= 60) color = 'warning';
        else if (rating >= 40) color = 'processing';
        
        return <Tag color={color}>{rating >= 80 ? '优秀' : rating >= 60 ? '良好' : rating >= 40 ? '一般' : '较差'}</Tag>;
      },
    },
  ];

  const fundamentalDataList = [
    {
      key: 'pe',
      metric: '市盈率 (PE)',
      value: fundamentalData.fundamentals.pe.toFixed(2),
      industryAvg: '25.5',
      rating: fundamentalData.fundamentals.pe < 20 ? 80 : fundamentalData.fundamentals.pe < 30 ? 60 : 40,
    },
    {
      key: 'pb',
      metric: '市净率 (PB)',
      value: fundamentalData.fundamentals.pb.toFixed(2),
      industryAvg: '3.8',
      rating: fundamentalData.fundamentals.pb < 2 ? 85 : fundamentalData.fundamentals.pb < 4 ? 70 : 50,
    },
    {
      key: 'roe',
      metric: '净资产收益率 (ROE)',
      value: `${fundamentalData.fundamentals.roe.toFixed(1)}%`,
      industryAvg: '12.5%',
      rating: fundamentalData.fundamentals.roe > 15 ? 90 : fundamentalData.fundamentals.roe > 10 ? 75 : 60,
    },
    {
      key: 'debt',
      metric: '资产负债率',
      value: `${(fundamentalData.fundamentals.debtToEquity * 100).toFixed(1)}%`,
      industryAvg: '35%',
      rating: fundamentalData.fundamentals.debtToEquity < 0.2 ? 90 : fundamentalData.fundamentals.debtToEquity < 0.4 ? 75 : 60,
    },
    {
      key: 'margin',
      metric: '净利率',
      value: `${fundamentalData.fundamentals.netMargin.toFixed(1)}%`,
      industryAvg: '25%',
      rating: fundamentalData.fundamentals.netMargin > 30 ? 90 : fundamentalData.fundamentals.netMargin > 20 ? 75 : 60,
    },
  ];

  // 市场情绪指标
  const renderSentimentIndicators = () => (
    <Row gutter={[16, 16]}>
      <Col span={8}>
        <Card>
          <Statistic
            title="市场情绪"
            value={fundamentalData.sentiment * 100}
            precision={1}
            suffix="%"
            valueStyle={{ 
              color: fundamentalData.sentiment > 0.7 ? '#52c41a' : 
                     fundamentalData.sentiment > 0.4 ? '#faad14' : '#f5222d' 
            }}
          />
          <Progress percent={fundamentalData.sentiment * 100} 
            strokeColor={fundamentalData.sentiment > 0.7 ? '#52c41a' : 
                        fundamentalData.sentiment > 0.4 ? '#faad14' : '#f5222d'}
          />
        </Card>
      </Col>
      
      <Col span={8}>
        <Card>
          <Statistic
            title="波动率"
            value={fundamentalData.volatility * 100}
            precision={1}
            suffix="%"
            valueStyle={{ 
              color: fundamentalData.volatility > 0.7 ? '#f5222d' : 
                     fundamentalData.volatility > 0.4 ? '#faad14' : '#52c41a' 
            }}
          />
          <Progress percent={fundamentalData.volatility * 100} 
            strokeColor={fundamentalData.volatility > 0.7 ? '#f5222d' : 
                        fundamentalData.volatility > 0.4 ? '#faad14' : '#52c41a'}
          />
        </Card>
      </Col>
      
      <Col span={8}>
        <Card>
          <Statistic
            title="综合评分"
            value={overallScore}
            suffix="/100"
            valueStyle={{ 
              color: overallScore > 80 ? '#52c41a' : 
                     overallScore > 60 ? '#faad14' : '#f5222d' 
            }}
          />
          <Progress percent={overallScore} 
            strokeColor={overallScore > 80 ? '#52c41a' : 
                        overallScore > 60 ? '#faad14' : '#f5222d'}
          />
        </Card>
      </Col>
    </Row>
  );

  // 技术评分雷达图数据
  const ratingData = [
    { subject: '趋势', A: fundamentalData.technicalRating.trend, fullMark: 100 },
    { subject: '动量', A: fundamentalData.technicalRating.momentum, fullMark: 100 },
    { subject: '波动率', A: fundamentalData.technicalRating.volatility, fullMark: 100 },
    { subject: '成交量', A: fundamentalData.technicalRating.volume, fullMark: 100 },
    { subject: '综合', A: fundamentalData.technicalRating.overall, fullMark: 100 },
  ];

  // 渲染新闻列表
  const renderNewsList = () => (
    <List
      itemLayout="horizontal"
      dataSource={fundamentalData.news}
      renderItem={(item, index) => (
        <List.Item>
          <List.Item.Meta
            avatar={
              <Avatar 
                icon={index === 0 ? <ThunderboltOutlined /> : <InfoCircleOutlined />}
                style={{ 
                  backgroundColor: item.sentiment === 'positive' ? '#52c41a' : 
                                   item.sentiment === 'negative' ? '#f5222d' : '#1890ff'
                }}
              />
            }
            title={
              <Space>
                <Text strong>{item.title}</Text>
                <Tag color={item.sentiment === 'positive' ? 'green' : 
                           item.sentiment === 'negative' ? 'red' : 'default'}>
                  {item.sentiment === 'positive' ? '正面' : 
                   item.sentiment === 'negative' ? '负面' : '中性'}
                </Tag>
              </Space>
            }
            description={
              <Space direction="vertical" size="small">
                <Text type="secondary">{item.source} · {item.time}</Text>
                <Paragraph>{item.summary}</Paragraph>
              </Space>
            }
          />
        </List.Item>
      )}
    />
  );

  // 渲染内容面板
  const renderContentPanel = () => {
    switch (selectedTab) {
      case 'overview':
        return (
          <div>
            {renderSentimentIndicators()}
            
            <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
              <Col span={12}>
                <Card title="价格信息">
                  <Descriptions column={2}>
                    <Descriptions.Item label="当前价格">
                      <Text strong>${fundamentalData.price.toLocaleString()}</Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="24h变化">
                      <Text style={{ color: fundamentalData.change > 0 ? '#52c41a' : '#f5222d' }}>
                        {fundamentalData.change > 0 ? '+' : ''}{fundamentalData.change.toFixed(2)} 
                        ({fundamentalData.changePercent > 0 ? '+' : ''}{fundamentalData.changePercent.toFixed(2)}%)
                      </Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="24h成交量">
                      ${(fundamentalData.volume / 1000000).toFixed(1)}M
                    </Descriptions.Item>
                    <Descriptions.Item label="成交量变化">
                      <Text style={{ color: fundamentalData.volumeChange > 0 ? '#52c41a' : '#f5222d' }}>
                        {fundamentalData.volumeChange > 0 ? '+' : ''}{fundamentalData.volumeChange.toFixed(2)}%
                      </Text>
                    </Descriptions.Item>
                    <Descriptions.Item label="市值">
                      ${(fundamentalData.marketCap / 1000000000).toFixed(1)}B
                    </Descriptions.Item>
                    <Descriptions.Item label="流通量">
                      {fundamentalData.circulatingSupply.toLocaleString()}
                    </Descriptions.Item>
                    <Descriptions.Item label="历史最高">
                      ${fundamentalData.allTimeHigh.toLocaleString()}
                    </Descriptions.Item>
                    <Descriptions.Item label="历史最低">
                      ${fundamentalData.allTimeLow.toLocaleString()}
                    </Descriptions.Item>
                  </Descriptions>
                </Card>
              </Col>
              
              <Col span={12}>
                <Card title="市场地位">
                  <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                    <div>
                      <Text>市值 dominance: </Text>
                      <Text strong>{fundamentalData.marketCapDominance.toFixed(1)}%</Text>
                      <Progress percent={fundamentalData.marketCapDominance} size="small" />
                    </div>
                    
                    <div>
                      <Text>市场地位: </Text>
                      <Tag color={fundamentalData.marketCapDominance > 40 ? 'gold' : 
                                 fundamentalData.marketCapDominance > 20 ? 'blue' : 'default'}>
                        {fundamentalData.marketCapDominance > 40 ? '领导者' : 
                         fundamentalData.marketCapDominance > 20 ? '挑战者' : '跟随者'}
                      </Tag>
                    </div>
                    
                    <Alert
                      message="市场地位分析"
                      description="该资产在市场中占据重要地位，具有较高的市值 dominance，是市场的核心资产。"
                      type="info"
                      showIcon
                    />
                  </Space>
                </Card>
              </Col>
            </Row>
          </div>
        );
        
      case 'fundamentals':
        return (
          <Card title="基本面指标">
            <Table
              columns={fundamentalColumns}
              dataSource={fundamentalDataList}
              pagination={false}
              size="middle"
            />
            
            <Divider />
            
            <Row gutter={[16, 16]}>
              <Col span={8}>
                <Card title="盈利能力">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Text>ROE: </Text>
                      <Text strong>{fundamentalData.fundamentals.roe.toFixed(1)}%</Text>
                    </div>
                    <div>
                      <Text>ROA: </Text>
                      <Text strong>{fundamentalData.fundamentals.roa.toFixed(1)}%</Text>
                    </div>
                    <div>
                      <Text>净利率: </Text>
                      <Text strong>{fundamentalData.fundamentals.netMargin.toFixed(1)}%</Text>
                    </div>
                  </Space>
                </Card>
              </Col>
              
              <Col span={8}>
                <Card title="财务健康状况">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Text>资产负债率: </Text>
                      <Text strong>{(fundamentalData.fundamentals.debtToEquity * 100).toFixed(1)}%</Text>
                    </div>
                    <div>
                      <Text>流动比率: </Text>
                      <Text strong>{fundamentalData.fundamentals.currentRatio.toFixed(1)}</Text>
                    </div>
                    <div>
                      <Text>速动比率: </Text>
                      <Text strong>{fundamentalData.fundamentals.quickRatio.toFixed(1)}</Text>
                    </div>
                  </Space>
                </Card>
              </Col>
              
              <Col span={8}>
                <Card title="估值水平">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Text>市盈率: </Text>
                      <Text strong>{fundamentalData.fundamentals.pe.toFixed(2)}</Text>
                    </div>
                    <div>
                      <Text>市净率: </Text>
                      <Text strong>{fundamentalData.fundamentals.pb.toFixed(2)}</Text>
                    </div>
                    <div>
                      <Text>市销率: </Text>
                      <Text strong>{fundamentalData.fundamentals.ps.toFixed(2)}</Text>
                    </div>
                  </Space>
                </Card>
              </Col>
            </Row>
          </Card>
        );
        
      case 'news':
        return (
          <Card title="市场新闻">
            {renderNewsList()}
          </Card>
        );
        
      case 'rating':
        return (
          <Card title="技术评分">
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Card title="各项评分">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Text>趋势评分: </Text>
                      <Text strong>{fundamentalData.technicalRating.trend}/100</Text>
                      <Progress percent={fundamentalData.technicalRating.trend} size="small" />
                    </div>
                    <div>
                      <Text>动量评分: </Text>
                      <Text strong>{fundamentalData.technicalRating.momentum}/100</Text>
                      <Progress percent={fundamentalData.technicalRating.momentum} size="small" />
                    </div>
                    <div>
                      <Text>波动率评分: </Text>
                      <Text strong>{fundamentalData.technicalRating.volatility}/100</Text>
                      <Progress percent={fundamentalData.technicalRating.volatility} size="small" />
                    </div>
                    <div>
                      <Text>成交量评分: </Text>
                      <Text strong>{fundamentalData.technicalRating.volume}/100</Text>
                      <Progress percent={fundamentalData.technicalRating.volume} size="small" />
                    </div>
                  </Space>
                </Card>
              </Col>
              
              <Col span={12}>
                <Card title="投资建议">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Alert
                      message="投资评级"
                      description={overallScore > 80 ? '强烈推荐买入' : 
                                   overallScore > 60 ? '推荐买入' : 
                                   overallScore > 40 ? '中性' : '谨慎'}
                      type={overallScore > 60 ? 'success' : overallScore > 40 ? 'warning' : 'error'}
                      showIcon
                    />
                    <Paragraph>
                      {overallScore > 80 ? '该资产基本面优秀，技术面强劲，具有较高的投资价值。' :
                       overallScore > 60 ? '该资产基本面良好，技术面稳健，适合长期投资。' :
                       overallScore > 40 ? '该资产基本面一般，建议谨慎投资并密切关注市场变化。' :
                       '该资产基本面较弱，建议观望或减持。'}
                    </Paragraph>
                  </Space>
                </Card>
              </Col>
            </Row>
          </Card>
        );
        
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div style={{ padding: 24 }}>
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      {/* 标题和控制 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={16}>
          <Title level={3}>基本面分析 - {symbol}</Title>
          <Paragraph type="secondary">
            深入分析资产基本面、市场情绪和技术指标
          </Paragraph>
        </Col>
        <Col span={8} style={{ textAlign: 'right' }}>
          <Space>
            <Button icon={<ReloadOutlined />} onClick={onRefresh}>
              刷新数据
            </Button>
            <Button icon={<BarChartOutlined />} onClick={() => onCompare?.(symbol)}>
              对比分析
            </Button>
          </Space>
        </Col>
      </Row>

      {/* 标签页 */}
      <Card>
        <Space>
          <Button
            type={selectedTab === 'overview' ? 'primary' : 'default'}
            onClick={() => setSelectedTab('overview')}
          >
            概览
          </Button>
          <Button
            type={selectedTab === 'fundamentals' ? 'primary' : 'default'}
            onClick={() => setSelectedTab('fundamentals')}
          >
            基本面
          </Button>
          <Button
            type={selectedTab === 'news' ? 'primary' : 'default'}
            onClick={() => setSelectedTab('news')}
          >
            新闻
          </Button>
          <Button
            type={selectedTab === 'rating' ? 'primary' : 'default'}
            onClick={() => setSelectedTab('rating')}
          >
            评分
          </Button>
        </Space>

        <Divider />

        {/* 内容面板 */}
        {renderContentPanel()}
      </Card>
    </div>
  );
};

export default FundamentalAnalysis;