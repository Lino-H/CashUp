/**
 * 市场情绪分析组件
 * Market Sentiment Analysis Component
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Row,
  Col,
  Progress,
  Statistic,
  Typography,
  Space,
  Alert,
  Select,
  Radio,
  Button,
  Divider,
  List,
  Tag,
  Tooltip,
  Avatar,
  Rate,
  Badge,
} from 'antd';
import {
  ThunderboltOutlined,
  FireOutlined,
  BullOutlined,
  BearOutlined,
  RiseOutlined,
  FallOutlined,
  WarningOutlined,
  InfoCircleOutlined,
  SendOutlined,
  TwitterOutlined,
  FacebookOutlined,
  TelegramOutlined,
  WechatOutlined,
  GithubOutlined,
  ApiOutlined,
  LineChartOutlined,
  BarChartOutlined,
  PieChartOutlined,
  CommentOutlined,
  HeartOutlined,
  EyeOutlined,
  ShareAltOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  GlobalOutlined,
} from '@ant-design/icons';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  ComposedChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { RadioGroup } = Radio;

// 情绪数据类型定义
export interface SentimentData {
  timestamp: number;
  score: number; // -1 到 1 之间
  confidence: number; // 0 到 1 之间
  category: 'bullish' | 'bearish' | 'neutral';
  source: string;
  text: string;
  symbols: string[];
}

export interface MarketSentiment {
  overall: number; // -1 到 1 之间
  fearGreedIndex: number; // 0 到 100 之间
  socialMedia: {
    twitter: number;
    reddit: number;
    telegram: number;
    wechat: number;
  };
  news: {
    positive: number;
    negative: number;
    neutral: number;
  };
  technical: {
    bullish: number;
    bearish: number;
    neutral: number;
  };
  volume: {
    buy: number;
    sell: number;
    neutral: number;
  };
}

export interface SentimentSource {
  name: string;
  type: 'social' | 'news' | 'technical' | 'volume';
  score: number;
  trend: 'up' | 'down' | 'stable';
  volume: number;
  lastUpdate: number;
}

// 生成模拟情绪数据
const generateMockSentimentData = (): SentimentData[] => {
  const data: SentimentData[] = [];
  const now = Date.now();
  
  for (let i = 30; i >= 0; i--) {
    const timestamp = now - (i * 60 * 60 * 1000); // 每小时一个数据点
    const baseScore = Math.sin(i * 0.2) * 0.3 + Math.random() * 0.4 - 0.2;
    const score = Math.max(-1, Math.min(1, baseScore));
    const confidence = 0.6 + Math.random() * 0.4;
    
    data.push({
      timestamp,
      score,
      confidence,
      category: score > 0.2 ? 'bullish' : score < -0.2 ? 'bearish' : 'neutral',
      source: `Source_${Math.floor(Math.random() * 5) + 1}`,
      text: `市场情绪分析数据点 ${i}`,
      symbols: ['BTC', 'ETH', 'BNB'],
    });
  }
  
  return data;
};

// 生成模拟市场情绪数据
const generateMockMarketSentiment = (): MarketSentiment => {
  const overall = Math.random() * 0.6 - 0.3; // -0.3 到 0.3
  const fearGreedIndex = Math.floor(Math.random() * 100);
  
  return {
    overall,
    fearGreedIndex,
    socialMedia: {
      twitter: Math.random() * 2 - 1,
      reddit: Math.random() * 2 - 1,
      telegram: Math.random() * 2 - 1,
      wechat: Math.random() * 2 - 1,
    },
    news: {
      positive: Math.random() * 100,
      negative: Math.random() * 100,
      neutral: Math.random() * 100,
    },
    technical: {
      bullish: Math.random() * 100,
      bearish: Math.random() * 100,
      neutral: Math.random() * 100,
    },
    volume: {
      buy: Math.random() * 1000,
      sell: Math.random() * 1000,
      neutral: Math.random() * 500,
    },
  };
};

// 情绪来源数据
const sentimentSources: SentimentSource[] = [
  {
    name: 'Twitter',
    type: 'social',
    score: 0.65,
    trend: 'up',
    volume: 1250,
    lastUpdate: Date.now() - 30 * 60 * 1000,
  },
  {
    name: 'Reddit',
    type: 'social',
    score: -0.45,
    trend: 'down',
    volume: 890,
    lastUpdate: Date.now() - 45 * 60 * 1000,
  },
  {
    name: 'Telegram',
    type: 'social',
    score: 0.23,
    trend: 'stable',
    volume: 567,
    lastUpdate: Date.now() - 20 * 60 * 1000,
  },
  {
    name: '财经新闻',
    type: 'news',
    score: 0.78,
    trend: 'up',
    volume: 2341,
    lastUpdate: Date.now() - 15 * 60 * 1000,
  },
  {
    name: '技术分析',
    type: 'technical',
    score: 0.34,
    trend: 'stable',
    volume: 1567,
    lastUpdate: Date.now() - 10 * 60 * 1000,
  },
  {
    name: '交易量',
    type: 'volume',
    score: -0.12,
    trend: 'down',
    volume: 3456,
    lastUpdate: Date.now() - 5 * 60 * 1000,
  },
];

// 情绪颜色映射
const getSentimentColor = (score: number): string => {
  if (score > 0.3) return '#52c41a'; // 强烈看涨 - 绿色
  if (score > 0.1) return '#1890ff'; // 看涨 - 蓝色
  if (score > -0.1) return '#faad14'; // 中性 - 黄色
  if (score > -0.3) return '#fa8c16'; // 看跌 - 橙色
  return '#f5222d'; // 强烈看跌 - 红色
};

// 情绪描述
const getSentimentDescription = (score: number): string => {
  if (score > 0.5) return '极度乐观';
  if (score > 0.3) return '非常乐观';
  if (score > 0.1) return '乐观';
  if (score > -0.1) return '中性';
  if (score > -0.3) return '悲观';
  if (score > -0.5) return '非常悲观';
  return '极度悲观';
};

// 恐慌贪婪指数描述
const getFearGreedDescription = (index: number): string => {
  if (index >= 90) return '极度贪婪';
  if (index >= 75) return '贪婪';
  if (index >= 50) return '中性';
  if (index >= 25) return '恐惧';
  if (index >= 0) return '极度恐惧';
  return '极度恐惧';
};

interface SentimentAnalysisProps {
  symbol?: string;
  timeframe?: string;
  autoRefresh?: boolean;
  onSentimentChange?: (sentiment: MarketSentiment) => void;
}

const SentimentAnalysis: React.FC<SentimentAnalysisProps> = ({
  symbol = 'BTC/USDT',
  timeframe = '1d',
  autoRefresh = true,
  onSentimentChange,
}) => {
  const [sentimentData, setSentimentData] = useState<SentimentData[]>([]);
  const [marketSentiment, setMarketSentiment] = useState<MarketSentiment | null>(null);
  const [selectedTimeframe, setSelectedTimeframe] = useState(timeframe);
  const [selectedSources, setSelectedSources] = useState<string[]>(['all']);
  const [loading, setLoading] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  // 初始化数据
  useEffect(() => {
    const initializeData = async () => {
      setLoading(true);
      try {
        const mockSentimentData = generateMockSentimentData();
        const mockMarketSentiment = generateMockMarketSentiment();
        
        setSentimentData(mockSentimentData);
        setMarketSentiment(mockMarketSentiment);
        onSentimentChange?.(mockMarketSentiment);
      } catch (error) {
        console.error('Failed to initialize sentiment data:', error);
      } finally {
        setLoading(false);
      }
    };

    initializeData();
  }, []);

  // 自动刷新
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      const newData = generateMockSentimentData();
      const newMarketSentiment = generateMockMarketSentiment();
      
      setSentimentData(newData);
      setMarketSentiment(newMarketSentiment);
      onSentimentChange?.(newMarketSentiment);
    }, 30000); // 每30秒刷新一次

    return () => clearInterval(interval);
  }, [autoRefresh, onSentimentChange]);

  // 处理时间周期变化
  const handleTimeframeChange = useCallback((value: string) => {
    setSelectedTimeframe(value);
    // 这里可以根据新的时间周期重新获取数据
    const newData = generateMockSentimentData();
    setSentimentData(newData);
  }, []);

  // 处理来源选择
  const handleSourceChange = useCallback((sources: string[]) => {
    setSelectedSources(sources);
  }, []);

  // 渲染情绪趋势图
  const renderSentimentTrendChart = () => {
    if (!marketSentiment || loading) {
      return (
        <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div>加载中...</div>
        </div>
      );
    }

    const chartData = sentimentData.map(data => ({
      time: new Date(data.timestamp).toLocaleDateString(),
      score: data.score,
      confidence: data.confidence,
    }));

    return (
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis domain={[-1, 1]} />
          <RechartsTooltip />
          <Area 
            type="monotone" 
            dataKey="score" 
            stroke="#1890ff" 
            fill="#1890ff" 
            fillOpacity={0.3}
            name="情绪分数"
          />
          <Area 
            type="monotone" 
            dataKey="confidence" 
            stroke="#52c41a" 
            fill="#52c41a" 
            fillOpacity={0.2}
            name="置信度"
          />
        </AreaChart>
      </ResponsiveContainer>
    );
  };

  // 渲染恐慌贪婪指数
  const renderFearGreedIndex = () => {
    if (!marketSentiment) return null;

    const fearGreedLevel = marketSentiment.fearGreedIndex;
    const description = getFearGreedDescription(fearGreedLevel);

    return (
      <Card title="恐慌贪婪指数" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={12}>
            <Statistic
              title="指数值"
              value={fearGreedLevel}
              suffix="/ 100"
              valueStyle={{ color: getSentimentColor(fearGreedLevel / 100 - 0.5) }}
            />
          </Col>
          <Col span={12}>
            <Statistic
              title="市场状态"
              value={description}
              valueStyle={{ color: getSentimentColor(fearGreedLevel / 100 - 0.5) }}
            />
          </Col>
        </Row>
        <Progress
          percent={fearGreedLevel}
          strokeColor={getSentimentColor(fearGreedLevel / 100 - 0.5)}
          trailColor="#f0f0f0"
        />
      </Card>
    );
  };

  // 渲染社交媒体情绪
  const renderSocialMediaSentiment = () => {
    if (!marketSentiment) return null;

    const socialData = Object.entries(marketSentiment.socialMedia).map(([platform, score]) => ({
      name: platform,
      score,
      color: getSentimentColor(score),
    }));

    return (
      <Card title="社交媒体情绪" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          {socialData.map((item) => (
            <Col span={6} key={item.name}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 24, marginBottom: 8 }}>{item.name}</div>
                <Progress
                  type="circle"
                  percent={Math.abs(item.score) * 50}
                  strokeColor={item.color}
                  trailColor="#f0f0f0"
                  width={60}
                  format={(percent) => `${(item.score * 100).toFixed(0)}`}
                />
                <div style={{ marginTop: 8, fontSize: 12 }}>
                  {item.score > 0 ? '看涨' : '看跌'}
                </div>
              </div>
            </Col>
          ))}
        </Row>
      </Card>
    );
  };

  // 渲染新闻情绪分析
  const renderNewsSentiment = () => {
    if (!marketSentiment) return null;

    const total = marketSentiment.news.positive + marketSentiment.news.negative + marketSentiment.news.neutral;
    const positive = marketSentiment.news.positive;
    const negative = marketSentiment.news.negative;
    const neutral = marketSentiment.news.neutral;

    return (
      <Card title="新闻情绪分析" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={8}>
            <Statistic
              title="正面新闻"
              value={positive}
              suffix={` (${((positive / total) * 100).toFixed(1)}%)`}
              valueStyle={{ color: '#52c41a' }}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="负面新闻"
              value={negative}
              suffix={` (${((negative / total) * 100).toFixed(1)}%)`}
              valueStyle={{ color: '#f5222d' }}
            />
          </Col>
          <Col span={8}>
            <Statistic
              title="中性新闻"
              value={neutral}
              suffix={` (${((neutral / total) * 100).toFixed(1)}%)`}
              valueStyle={{ color: '#faad14' }}
            />
          </Col>
        </Row>
        <Row gutter={16} style={{ marginTop: 16 }}>
          <Col span={24}>
            <ResponsiveContainer width="100%" height={150}>
              <BarChart data={[
                { name: '正面', value: positive, color: '#52c41a' },
                { name: '负面', value: negative, color: '#f5222d' },
                { name: '中性', value: neutral, color: '#faad14' },
              ]}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <RechartsTooltip />
                <Bar dataKey="value" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </Col>
        </Row>
      </Card>
    );
  };

  // 渲染情绪来源列表
  const renderSentimentSources = () => {
    return (
      <Card title="情绪来源" style={{ marginBottom: 16 }}>
        <List
          dataSource={sentimentSources}
          renderItem={(source) => (
            <List.Item>
              <List.Item.Meta
                avatar={
                  <Avatar 
                    style={{ 
                      backgroundColor: getSentimentColor(source.score),
                      color: 'white'
                    }}
                    icon={
                      source.type === 'social' ? <ThunderboltOutlined /> :
                      source.type === 'news' ? <ApiOutlined /> :
                      source.type === 'technical' ? <LineChartOutlined /> :
                      <BarChartOutlined />
                    }
                  />
                }
                title={
                  <Space>
                    <span>{source.name}</span>
                    <Badge 
                      status={source.trend === 'up' ? 'success' : source.trend === 'down' ? 'error' : 'default'}
                      text={source.trend === 'up' ? '上升' : source.trend === 'down' ? '下降' : '稳定'}
                    />
                  </Space>
                }
                description={
                  <Space>
                    <span>情绪分数: {source.score.toFixed(2)}</span>
                    <span>更新时间: {new Date(source.lastUpdate).toLocaleTimeString()}</span>
                  </Space>
                }
              />
              <div style={{ textAlign: 'right' }}>
                <Progress
                  percent={Math.abs(source.score) * 100}
                  strokeColor={getSentimentColor(source.score)}
                  trailColor="#f0f0f0"
                  width={80}
                  format={() => source.score.toFixed(2)}
                />
              </div>
            </List.Item>
          )}
        />
      </Card>
    );
  };

  // 渲染综合情绪雷达图
  const renderSentimentRadar = () => {
    if (!marketSentiment) return null;

    const radarData = [
      { subject: '整体情绪', A: Math.abs(marketSentiment.overall) * 100, fullMark: 100 },
      { subject: '社交媒体', A: Math.abs(marketSentiment.socialMedia.twitter) * 100, fullMark: 100 },
      { subject: '新闻媒体', A: (marketSentiment.news.positive - marketSentiment.news.negative) / 2 + 50, fullMark: 100 },
      { subject: '技术指标', A: marketSentiment.technical.bullish, fullMark: 100 },
      { subject: '交易量', A: (marketSentiment.volume.buy - marketSentiment.volume.sell) / 1000, fullMark: 100 },
    ];

    return (
      <Card title="综合情绪分析">
        <Row gutter={16}>
          <Col span={16}>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={radarData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="subject" />
                <PolarRadiusAxis angle={90} domain={[0, 100]} />
                <Radar
                  name="情绪强度"
                  dataKey="A"
                  stroke="#1890ff"
                  fill="#1890ff"
                  fillOpacity={0.3}
                />
                <RechartsTooltip />
              </RadarChart>
            </ResponsiveContainer>
          </Col>
          <Col span={8}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Alert
                message="整体情绪"
                description={getSentimentDescription(marketSentiment.overall)}
                type={marketSentiment.overall > 0 ? 'success' : 'error'}
                showIcon
              />
              <Alert
                message="市场建议"
                description={
                  marketSentiment.overall > 0.3 ? '建议逢低买入' :
                  marketSentiment.overall < -0.3 ? '建议逢高卖出' :
                  '建议观望等待'
                }
                type="info"
                showIcon
              />
              <Alert
                message="风险等级"
                description={
                  Math.abs(marketSentiment.overall) > 0.5 ? '高风险' :
                  Math.abs(marketSentiment.overall) > 0.3 ? '中等风险' :
                  '低风险'
                }
                type={Math.abs(marketSentiment.overall) > 0.5 ? 'error' : 'warning'}
                showIcon
              />
            </Space>
          </Col>
        </Row>
      </Card>
    );
  };

  return (
    <div style={{ padding: 24 }}>
      {/* 标题和控制 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={16}>
          <Title level={3}>市场情绪分析 - {symbol}</Title>
          <Paragraph type="secondary">
            综合分析市场情绪、社交媒体、新闻媒体和技术指标
          </Paragraph>
        </Col>
        <Col span={8} style={{ textAlign: 'right' }}>
          <Space>
            <Select
              value={selectedTimeframe}
              onChange={handleTimeframeChange}
              style={{ width: 100 }}
            >
              <Option value="1h">1小时</Option>
              <Option value="4h">4小时</Option>
              <Option value="1d">1天</Option>
              <Option value="1w">1周</Option>
              <Option value="1M">1月</Option>
            </Select>
            
            <Button 
              icon={<ThunderboltOutlined />} 
              size="small"
              onClick={() => setShowDetails(!showDetails)}
            >
              {showDetails ? '简化' : '详细'}
            </Button>
            
            <Button icon={<ClockCircleOutlined />} size="small">
              自动刷新
            </Button>
          </Space>
        </Col>
      </Row>

      {/* 恐慌贪婪指数 */}
      {renderFearGreedIndex()}

      {/* 社交媒体情绪 */}
      {renderSocialMediaSentiment()}

      {/* 新闻情绪分析 */}
      {renderNewsSentiment()}

      {/* 情绪趋势图 */}
      <Card title="情绪趋势" style={{ marginBottom: 16 }}>
        {renderSentimentTrendChart()}
      </Card>

      {/* 详细分析 */}
      {showDetails && (
        <>
          {renderSentimentSources()}
          {renderSentimentRadar()}
        </>
      )}

      {/* 投资建议 */}
      <Card title="投资建议" style={{ marginTop: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Alert
            message="情绪总结"
            description={
              marketSentiment?.overall > 0.3 ? '当前市场情绪偏向乐观，投资者信心较强，但需注意过热风险。' :
              marketSentiment?.overall < -0.3 ? '当前市场情绪偏向悲观，投资者较为谨慎，但可能存在机会。' :
              '当前市场情绪相对平衡，建议关注关键数据和市场动向。'
            }
            type="info"
            showIcon
          />
          
          <Alert
            message="操作建议"
            description={
              marketSentiment?.fearGreedIndex > 75 ? '市场极度贪婪，建议谨慎操作，考虑适当减仓。' :
              marketSentiment?.fearGreedIndex < 25 ? '市场极度恐惧，可能存在机会，建议关注。' :
              '市场情绪相对正常，建议按照既定策略操作。'
            }
            type="warning"
            showIcon
          />
          
          <Alert
            message="风险提示"
            description="情绪分析仅供参考，投资决策应结合技术分析、基本面分析等多方面因素。"
            type="error"
            showIcon
          />
        </Space>
      </Card>
    </div>
  );
};

export default SentimentAnalysis;