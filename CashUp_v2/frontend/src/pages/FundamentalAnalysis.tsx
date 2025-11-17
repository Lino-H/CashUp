import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Alert, Spin, Progress, List, Tag, Typography, Divider, Table } from 'antd';
import { BarChartOutlined, TrophyOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';

const { Title, Text, Paragraph } = Typography;

interface FundamentalIndicators {
  pe_ratio: number;
  pb_ratio: number;
  roe: number;
  roa: number;
  debt_to_equity: number;
  current_ratio: number;
  quick_ratio: number;
  dividend_yield: number;
  eps: number;
  revenue_growth: number;
  profit_margin: number;
  operating_margin: number;
}

const FundamentalAnalysis: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<{
    score: number;
    indicators: FundamentalIndicators;
    overall_rating: string;
    recommendation: string;
    last_updated: string;
  } | null>(null);

  useEffect(() => {
    if (isAuthenticated) {
      fetchFundamentalAnalysis();
    }
  }, [isAuthenticated]);

  const fetchFundamentalAnalysis = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/config/analysis/fundamental', {
        credentials: 'include'
      });
      
      if (response.ok) {
        const result = await response.json();
        setData(result);
      }
    } catch (error) {
      console.error('获取基础分析数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const getFinancialHealth = (roe: number, roa: number, debt_to_equity: number, current_ratio: number) => {
    const healthScore = (roe * 0.3 + roa * 0.2 + Math.min(current_ratio, 3) * 0.2 + Math.max(0, 10 - debt_to_equity) * 0.3);
    if (healthScore > 8) return { color: '#52c41a', text: '优秀' };
    if (healthScore > 6) return { color: '#1890ff', text: '良好' };
    if (healthScore > 4) return { color: '#faad14', text: '一般' };
    return { color: '#f5222d', text: '需关注' };
  };

  const getValuationStatus = (pe_ratio: number, pb_ratio: number) => {
    if (pe_ratio < 15 && pb_ratio < 1.5) return { color: '#52c41a', text: '被低估' };
    if (pe_ratio > 25 || pb_ratio > 3) return { color: '#f5222d', text: '被高估' };
    return { color: '#faad14', text: '合理' };
  };

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case '强烈买入': return '#52c41a';
      case '买入': return '#52c41a';
      case '持有': return '#faad14';
      case '卖出': return '#f5222d';
      case '强烈卖出': return '#f5222d';
      default: return '#faad14';
    }
  };

  const getRatingColor = (rating: string) => {
    switch (rating) {
      case 'A': return '#52c41a';
      case 'B': return '#1890ff';
      case 'C': return '#faad14';
      case 'D': return '#f5222d';
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
      <Title level={3}>基础分析</Title>
      <Paragraph>
        基于财务指标、估值比率、盈利能力和增长潜力的专业基本面分析
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
                  title="基本面评分"
                  value={data.score}
                  suffix="/100"
                  valueStyle={{ color: '#1890ff' }}
                  prefix={<BarChartOutlined />}
                />
                <Progress percent={data.score} strokeColor="#1890ff" />
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic
                  title="总体评级"
                  value={data.overall_rating}
                  valueStyle={{ color: getRatingColor(data.overall_rating) }}
                  prefix={<TrophyOutlined />}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic
                  title="投资建议"
                  value={data.recommendation}
                  valueStyle={{ color: getRecommendationColor(data.recommendation) }}
                />
              </Card>
            </Col>
          </Row>

          {/* 估值指标 */}
          <Title level={4}>估值指标</Title>
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Card title="估值比率" style={{ marginBottom: '16px' }}>
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Text>市盈率(P/E): </Text>
                    <Text strong>{data.indicators.pe_ratio.toFixed(2)}</Text>
                  </Col>
                  <Col span={12}>
                    <Text>市净率(P/B): </Text>
                    <Text strong>{data.indicators.pb_ratio.toFixed(2)}</Text>
                  </Col>
                  <Col span={12}>
                    <Text>股息率: </Text>
                    <Text strong>{(data.indicators.dividend_yield * 100).toFixed(2)}%</Text>
                  </Col>
                  <Col span={12}>
                    <Text>每股收益: </Text>
                    <Text strong>{data.indicators.eps.toFixed(2)}</Text>
                  </Col>
                </Row>
                <div style={{ marginTop: '8px' }}>
                  <Tag color={getValuationStatus(data.indicators.pe_ratio, data.indicators.pb_ratio).color}>
                    {getValuationStatus(data.indicators.pe_ratio, data.indicators.pb_ratio).text}
                  </Tag>
                </div>
              </Card>
            </Col>
            <Col span={12}>
              <Card title="盈利能力" style={{ marginBottom: '16px' }}>
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Text>净资产收益率(ROE): </Text>
                    <Text strong>{(data.indicators.roe * 100).toFixed(2)}%</Text>
                  </Col>
                  <Col span={12}>
                    <Text>总资产收益率(ROA): </Text>
                    <Text strong>{(data.indicators.roa * 100).toFixed(2)}%</Text>
                  </Col>
                  <Col span={12}>
                    <Text>净利润率: </Text>
                    <Text strong>{(data.indicators.profit_margin * 100).toFixed(2)}%</Text>
                  </Col>
                  <Col span={12}>
                    <Text>营业利润率: </Text>
                    <Text strong>{(data.indicators.operating_margin * 100).toFixed(2)}%</Text>
                  </Col>
                </Row>
                <div style={{ marginTop: '8px' }}>
                  <Tag color={getFinancialHealth(
                    data.indicators.roe, 
                    data.indicators.roa, 
                    data.indicators.debt_to_equity, 
                    data.indicators.current_ratio
                  ).color}>
                    {getFinancialHealth(
                      data.indicators.roe, 
                      data.indicators.roa, 
                      data.indicators.debt_to_equity, 
                      data.indicators.current_ratio
                    ).text}
                  </Tag>
                </div>
              </Card>
            </Col>
          </Row>

          {/* 财务健康度 */}
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Card title="偿债能力">
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Text>资产负债率: </Text>
                    <Text strong>{(data.indicators.debt_to_equity * 100).toFixed(2)}%</Text>
                  </Col>
                  <Col span={12}>
                    <Text>流动比率: </Text>
                    <Text strong>{data.indicators.current_ratio.toFixed(2)}</Text>
                  </Col>
                  <Col span={12}>
                    <Text>速动比率: </Text>
                    <Text strong>{data.indicators.quick_ratio.toFixed(2)}</Text>
                  </Col>
                </Row>
              </Card>
            </Col>
            <Col span={12}>
              <Card title="成长性">
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Text>营收增长率: </Text>
                    <Text strong>{(data.indicators.revenue_growth * 100).toFixed(2)}%</Text>
                  </Col>
                  <Col span={12}>
                    <Text>成长评分: </Text>
                    <Text strong>
                      {Math.min(10, Math.max(0, data.indicators.revenue_growth * 5)).toFixed(1)}/10
                    </Text>
                  </Col>
                </Row>
                <Progress 
                  percent={Math.min(100, data.indicators.revenue_growth * 10)} 
                  strokeColor="#1890ff" 
                  style={{ marginTop: '8px' }}
                />
              </Card>
            </Col>
          </Row>

          {/* 详细指标表格 */}
          <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
            <Col span={24}>
              <Card title="财务指标详细分析">
                <Table
                  dataSource={[
                    {
                      key: '1',
                      indicator: '市盈率(P/E)',
                      value: data.indicators.pe_ratio.toFixed(2),
                      industry: '15.2',
                      status: data.indicators.pe_ratio < 15 ? '偏低' : data.indicators.pe_ratio > 25 ? '偏高' : '正常',
                      recommendation: data.indicators.pe_ratio < 15 ? '积极' : data.indicators.pe_ratio > 25 ? '谨慎' : '中性'
                    },
                    {
                      key: '2',
                      indicator: '净资产收益率',
                      value: `${(data.indicators.roe * 100).toFixed(2)}%`,
                      industry: '12.5%',
                      status: data.indicators.roe > 0.15 ? '优秀' : data.indicators.roe > 0.1 ? '良好' : '一般',
                      recommendation: data.indicators.roe > 0.15 ? '强烈推荐' : data.indicators.roe > 0.1 ? '推荐' : '观望'
                    },
                    {
                      key: '3',
                      indicator: '资产负债率',
                      value: `${(data.indicators.debt_to_equity * 100).toFixed(2)}%`,
                      industry: '45%',
                      status: data.indicators.debt_to_equity < 0.5 ? '健康' : data.indicators.debt_to_equity < 1 ? '中等' : '较高',
                      recommendation: data.indicators.debt_to_equity < 0.5 ? '积极' : data.indicators.debt_to_equity < 1 ? '中性' : '谨慎'
                    },
                    {
                      key: '4',
                      indicator: '流动比率',
                      value: data.indicators.current_ratio.toFixed(2),
                      industry: '2.1',
                      status: data.indicators.current_ratio > 2 ? '优秀' : data.indicators.current_ratio > 1.5 ? '良好' : '偏低',
                      recommendation: data.indicators.current_ratio > 2 ? '积极' : data.indicators.current_ratio > 1.5 ? '中性' : '谨慎'
                    },
                    {
                      key: '5',
                      indicator: '营收增长率',
                      value: `${(data.indicators.revenue_growth * 100).toFixed(2)}%`,
                      industry: '8.3%',
                      status: data.indicators.revenue_growth > 0.15 ? '高增长' : data.indicators.revenue_growth > 0.08 ? '稳定增长' : '低速增长',
                      recommendation: data.indicators.revenue_growth > 0.15 ? '强烈推荐' : data.indicators.revenue_growth > 0.08 ? '推荐' : '观望'
                    }
                  ]}
                  columns={[
                    {
                      title: '指标',
                      dataIndex: 'indicator',
                      key: 'indicator',
                    },
                    {
                      title: '数值',
                      dataIndex: 'value',
                      key: 'value',
                    },
                    {
                      title: '行业平均',
                      dataIndex: 'industry',
                      key: 'industry',
                    },
                    {
                      title: '评估',
                      dataIndex: 'status',
                      key: 'status',
                      render: (status: string) => {
                        let color = 'default';
                        if (status === '优秀' || status === '健康' || status === '偏低' || status === '高增长') color = '#52c41a';
                        if (status === '良好' || status === '中等' || status === '正常' || status === '稳定增长') color = '#1890ff';
                        if (status === '一般' || status === '较高' || status === '偏高') color = '#faad14';
                        return <Tag color={color}>{status}</Tag>;
                      }
                    },
                    {
                      title: '建议',
                      dataIndex: 'recommendation',
                      key: 'recommendation',
                      render: (rec: string) => {
                        let color = 'default';
                        if (rec === '强烈推荐' || rec === '积极' || rec === '推荐') color = '#52c41a';
                        if (rec === '中性' || rec === '观望') color = '#faad14';
                        if (rec === '谨慎') color = '#f5222d';
                        return <Tag color={color}>{rec}</Tag>;
                      }
                    }
                  ]}
                  pagination={false}
                  size="middle"
                />
              </Card>
            </Col>
          </Row>

          {/* 分析建议 */}
          <Divider />
          <Card title="投资建议">
            <List
              dataSource={[
                {
                  title: '估值分析',
                  description: `当前市盈率${data.indicators.pe_ratio.toFixed(2)}，${getValuationStatus(data.indicators.pe_ratio, data.indicators.pb_ratio).text}，建议${data.recommendation === '强烈买入' || data.recommendation === '买入' ? '逢低买入' : data.recommendation === '卖出' || data.recommendation === '强烈卖出' ? '逢高减仓' : '持有观望'}。`
                },
                {
                  title: '财务健康',
                  description: `净资产收益率${(data.indicators.roe * 100).toFixed(2)}%，资产负债率${(data.indicators.debt_to_equity * 100).toFixed(2)}%，${getFinancialHealth(data.indicators.roe, data.indicators.roa, data.indicators.debt_to_equity, data.indicators.current_ratio).text}，财务状况${getFinancialHealth(data.indicators.roe, data.indicators.roa, data.indicators.debt_to_equity, data.indicators.current_ratio).text}。`
                },
                {
                  title: '成长潜力',
                  description: `营收增长率${(data.indicators.revenue_growth * 100).toFixed(2)}%，${data.indicators.revenue_growth > 0.15 ? '高增长潜力，值得关注' : data.indicators.revenue_growth > 0.08 ? '稳定增长，适合长期持有' : '增长放缓，需谨慎评估'}。`
                },
                {
                  title: '风险提示',
                  description: `建议关注行业周期变化、政策环境影响以及公司基本面变化，设置合理的止损点位。`
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
          <Alert message="暂无基础分析数据" type="info" showIcon />
        </Card>
      )}
    </div>
  );
};

export default FundamentalAnalysis;