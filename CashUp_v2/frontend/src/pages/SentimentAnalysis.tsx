import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Alert, Spin, Progress, List, Tag, Typography, Divider, Timeline } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, EyeOutlined, MessageOutlined, LineChartOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';

const { Title, Text, Paragraph } = Typography;

interface SentimentData {
  overall_score: number;
  market_sentiment: string;
  social_sentiment: string;
  news_sentiment: string;
  analyst_sentiment: string;
  fear_greed_index: number;
  social_media_metrics: {
    mentions: number;
    sentiment_score: number;
    engagement_rate: number;
    positive_mentions: number;
    negative_mentions: number;
    neutral_mentions: number;
  };
  news_metrics: {
    articles_count: number;
    positive_articles: number;
    negative_articles: number;
    neutral_articles: number;
    sentiment_score: number;
  };
  analyst_ratings: {
    strong_buy: number;
    buy: number;
    hold: number;
    sell: number;
    strong_sell: number;
    avg_rating: number;
    target_price: number;
    current_price: number;
    upside_potential: number;
  };
  recent_events: {
    date: string;
    event: string;
    impact: 'positive' | 'negative' | 'neutral';
    sentiment_change: number;
  }[];
}

const SentimentAnalysis: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<{
    score: number;
    sentiment: SentimentData;
    last_updated: string;
  } | null>(null);

  useEffect(() => {
    if (isAuthenticated) {
      fetchSentimentAnalysis();
    }
  }, [isAuthenticated]);

  const fetchSentimentAnalysis = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/config/analysis/sentiment', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const result = await response.json();
        setData(result);
      }
    } catch (error) {
      console.error('获取情绪分析数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case '极度乐观': case '非常乐观': return '#52c41a';
      case '乐观': case '偏乐观': return '#95de64';
      case '中性': return '#faad14';
      case '悲观': case '偏悲观': return '#ff7875';
      case '极度悲观': return '#f5222d';
      default: return '#faad14';
    }
  };

  const getFearGreedColor = (index: number) => {
    if (index > 75) return '#52c41a'; // 贪婪
    if (index > 50) return '#95de64';
    if (index > 25) return '#faad14';
    return '#f5222d'; // 恐惧
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'positive': return '#52c41a';
      case 'negative': return '#f5222d';
      case 'neutral': return '#faad14';
      default: return '#faad14';
    }
  };

  const getRatingText = (rating: number) => {
    if (rating >= 4.5) return '强烈推荐';
    if (rating >= 4.0) return '推荐';
    if (rating >= 3.0) return '中性';
    if (rating >= 2.0) return '卖出';
    return '强烈卖出';
  };

  const getRatingColor = (rating: number) => {
    if (rating >= 4.5) return '#52c41a';
    if (rating >= 4.0) return '#95de64';
    if (rating >= 3.0) return '#faad14';
    if (rating >= 2.0) return '#ff7875';
    return '#f5222d';
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
      <Title level={3}>情绪分析</Title>
      <Paragraph>
        综合市场情绪、社交媒体、新闻媒体和分析师情绪的多维度情绪分析
      </Paragraph>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin size="large" />
        </div>
      ) : data ? (
        <>
          {/* 总体评分 */}
          <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="情绪评分"
                  value={data.score}
                  suffix="/100"
                  valueStyle={{ color: '#1890ff' }}
                  prefix={<ArrowUpOutlined />}
                />
                <Progress percent={data.score} strokeColor="#1890ff" />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="恐惧贪婪指数"
                  value={data.sentiment.fear_greed_index}
                  suffix="/100"
                  valueStyle={{ color: getFearGreedColor(data.sentiment.fear_greed_index) }}
                  prefix={<LineChartOutlined />}
                />
                <Progress 
                  percent={data.sentiment.fear_greed_index} 
                  strokeColor={getFearGreedColor(data.sentiment.fear_greed_index)} 
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="市场情绪"
                  value={data.sentiment.market_sentiment}
                  valueStyle={{ color: getSentimentColor(data.sentiment.market_sentiment) }}
                  prefix={<EyeOutlined />}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="社交情绪"
                  value={data.sentiment.social_sentiment}
                  valueStyle={{ color: getSentimentColor(data.sentiment.social_sentiment) }}
                  prefix={<MessageOutlined />}
                />
              </Card>
            </Col>
          </Row>

          {/* 详细情绪指标 */}
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Card title="社交媒体情绪" style={{ marginBottom: '16px' }}>
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Text>提及次数: </Text>
                    <Text strong>{data.sentiment.social_media_metrics.mentions.toLocaleString()}</Text>
                  </Col>
                  <Col span={12}>
                    <Text>参与率: </Text>
                    <Text strong>{(data.sentiment.social_media_metrics.engagement_rate * 100).toFixed(2)}%</Text>
                  </Col>
                  <Col span={8}>
                    <Text>正面: </Text>
                    <Text strong>{data.sentiment.social_media_metrics.positive_mentions}</Text>
                  </Col>
                  <Col span={8}>
                    <Text>中性: </Text>
                    <Text strong>{data.sentiment.social_media_metrics.neutral_mentions}</Text>
                  </Col>
                  <Col span={8}>
                    <Text>负面: </Text>
                    <Text strong>{data.sentiment.social_media_metrics.negative_mentions}</Text>
                  </Col>
                </Row>
                <div style={{ marginTop: '12px' }}>
                  <Progress 
                    percent={Math.round(data.sentiment.social_media_metrics.sentiment_score * 100)} 
                    strokeColor={getSentimentColor(data.sentiment.social_sentiment)}
                    format={() => `情绪指数: ${(data.sentiment.social_media_metrics.sentiment_score * 100).toFixed(1)}%`}
                  />
                </div>
              </Card>
            </Col>
            <Col span={12}>
              <Card title="新闻媒体情绪" style={{ marginBottom: '16px' }}>
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Text>文章数量: </Text>
                    <Text strong>{data.sentiment.news_metrics.articles_count}</Text>
                  </Col>
                  <Col span={12}>
                    <Text>平均情绪: </Text>
                    <Text strong>{(data.sentiment.news_metrics.sentiment_score * 100).toFixed(1)}%</Text>
                  </Col>
                  <Col span={8}>
                    <Text>正面: </Text>
                    <Text strong>{data.sentiment.news_metrics.positive_articles}</Text>
                  </Col>
                  <Col span={8}>
                    <Text>中性: </Text>
                    <Text strong>{data.sentiment.news_metrics.neutral_articles}</Text>
                  </Col>
                  <Col span={8}>
                    <Text>负面: </Text>
                    <Text strong>{data.sentiment.news_metrics.negative_articles}</Text>
                  </Col>
                </Row>
                <div style={{ marginTop: '12px' }}>
                  <Progress 
                    percent={Math.round(data.sentiment.news_metrics.sentiment_score * 100)} 
                    strokeColor={getSentimentColor(data.sentiment.news_sentiment)}
                    format={() => `新闻情绪: ${(data.sentiment.news_metrics.sentiment_score * 100).toFixed(1)}%`}
                  />
                </div>
              </Card>
            </Col>
          </Row>

          {/* 分析师评级 */}
          <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
            <Col span={24}>
              <Card title="分析师评级">
                <Row gutter={[16, 16]}>
                  <Col span={4}>
                    <div style={{ textAlign: 'center' }}>
                      <Statistic
                        title="强烈买入"
                        value={data.sentiment.analyst_ratings.strong_buy}
                        suffix="家"
                        valueStyle={{ color: '#52c41a' }}
                      />
                    </div>
                  </Col>
                  <Col span={4}>
                    <div style={{ textAlign: 'center' }}>
                      <Statistic
                        title="买入"
                        value={data.sentiment.analyst_ratings.buy}
                        suffix="家"
                        valueStyle={{ color: '#95de64' }}
                      />
                    </div>
                  </Col>
                  <Col span={4}>
                    <div style={{ textAlign: 'center' }}>
                      <Statistic
                        title="持有"
                        value={data.sentiment.analyst_ratings.hold}
                        suffix="家"
                        valueStyle={{ color: '#faad14' }}
                      />
                    </div>
                  </Col>
                  <Col span={4}>
                    <div style={{ textAlign: 'center' }}>
                      <Statistic
                        title="卖出"
                        value={data.sentiment.analyst_ratings.sell}
                        suffix="家"
                        valueStyle={{ color: '#ff7875' }}
                      />
                    </div>
                  </Col>
                  <Col span={4}>
                    <div style={{ textAlign: 'center' }}>
                      <Statistic
                        title="强烈卖出"
                        value={data.sentiment.analyst_ratings.strong_sell}
                        suffix="家"
                        valueStyle={{ color: '#f5222d' }}
                      />
                    </div>
                  </Col>
                  <Col span={4}>
                    <div style={{ textAlign: 'center' }}>
                      <Statistic
                        title="平均评级"
                        value={data.sentiment.analyst_ratings.avg_rating.toFixed(1)}
                        suffix="/5"
                        valueStyle={{ color: getRatingColor(data.sentiment.analyst_ratings.avg_rating) }}
                      />
                    </div>
                  </Col>
                </Row>
                <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
                  <Col span={12}>
                    <div style={{ textAlign: 'center' }}>
                      <Statistic
                        title="目标价格"
                        value={`¥${data.sentiment.analyst_ratings.target_price.toFixed(2)}`}
                        valueStyle={{ color: '#1890ff' }}
                      />
                    </div>
                  </Col>
                  <Col span={12}>
                    <div style={{ textAlign: 'center' }}>
                      <Statistic
                        title="上涨潜力"
                        value={`${data.sentiment.analyst_ratings.upside_potential.toFixed(1)}%`}
                        valueStyle={data.sentiment.analyst_ratings.upside_potential > 0 ? { color: '#52c41a' } : { color: '#f5222d' }}
                        prefix={data.sentiment.analyst_ratings.upside_potential > 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                      />
                    </div>
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>

          {/* 最近事件 */}
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Card title="最近重要事件">
                <Timeline
                  items={data.sentiment.recent_events.map(event => ({
                    color: getImpactColor(event.impact),
                    dot: getImpactColor(event.impact) === '#52c41a' ? 'green' : 
                          getImpactColor(event.impact) === '#f5222d' ? 'red' : 'orange',
                    children: (
                      <div>
                        <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
                          {new Date(event.date).toLocaleDateString('zh-CN')}
                        </div>
                        <div style={{ marginBottom: '4px' }}>{event.event}</div>
                        <div>
                          <Tag color={getImpactColor(event.impact)}>
                            {event.impact === 'positive' ? '正面影响' : 
                             event.impact === 'negative' ? '负面影响' : '中性影响'}
                          </Tag>
                          <Tag color={event.sentiment_change > 0 ? '#52c41a' : event.sentiment_change < 0 ? '#f5222d' : '#faad14'}>
                            情绪变化: {event.sentiment_change > 0 ? '+' : ''}{(event.sentiment_change * 100).toFixed(1)}%
                          </Tag>
                        </div>
                      </div>
                    )
                  }))}
                />
              </Card>
            </Col>
          </Row>

          {/* 分析建议 */}
          <Divider />
          <Card title="情绪分析建议">
            <List
              dataSource={[
                {
                  title: '市场情绪',
                  description: `当前市场情绪为${data.sentiment.market_sentiment}，${data.sentiment.market_sentiment.includes('乐观') ? '投资者信心较强，但需警惕过度乐观风险' : data.sentiment.market_sentiment.includes('悲观') ? '投资者信心不足，可能存在机会' : '市场情绪相对平稳'}。`
                },
                {
                  title: '社交媒体热度',
                  description: `社交媒体提及次数${data.sentiment.social_media_metrics.mentions.toLocaleString()}，参与率${(data.sentiment.social_media_metrics.engagement_rate * 100).toFixed(2)}%，${data.sentiment.social_media_metrics.sentiment_score > 0.6 ? '市场情绪积极' : data.sentiment.social_media_metrics.sentiment_score < 0.4 ? '市场情绪谨慎' : '市场情绪中性'}。`
                },
                {
                  title: '新闻媒体',
                  description: `近期相关新闻${data.sentiment.news_metrics.articles_count}篇，正面新闻占比${(data.sentiment.news_metrics.positive_articles / data.sentiment.news_metrics.articles_count * 100).toFixed(1)}%，新闻整体情绪${data.sentiment.news_sentiment}。`
                },
                {
                  title: '分析师观点',
                  description: `分析师平均评级${getRatingText(data.sentiment.analyst_ratings.avg_rating)}，目标价格¥${data.sentiment.analyst_ratings.target_price.toFixed(2)}，${data.sentiment.analyst_ratings.upside_potential > 10 ? '上涨潜力较大' : data.sentiment.analyst_ratings.upside_potential < -5 ? '下跌风险较高' : '价格相对合理'}。`
                },
                {
                  title: '风险提示',
                  description: `恐惧贪婪指数为${data.sentiment.fear_greed_index}，${data.sentiment.fear_greed_index > 75 ? '市场处于贪婪状态，需警惕回调风险' : data.sentiment.fear_greed_index < 25 ? '市场处于恐惧状态，可能存在机会' : '市场情绪相对平衡'}。`
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
          <Alert message="暂无情绪分析数据" type="info" showIcon />
        </Card>
      )}
    </div>
  );
};

export default SentimentAnalysis;