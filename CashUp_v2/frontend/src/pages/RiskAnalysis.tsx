import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Alert, Spin, Progress, List, Tag, Typography, Divider, Table, Radio } from 'antd';
import { SafetyOutlined, WarningOutlined, ExclamationCircleOutlined, LineChartOutlined, ThunderboltOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';

const { Title, Text, Paragraph } = Typography;
 

interface RiskMetrics {
  overall_risk_score: number;
  market_risk: number;
  credit_risk: number;
  liquidity_risk: number;
  operational_risk: number;
  volatility_risk: number;
  concentration_risk: number;
  correlation_risk: number;
  regulatory_risk: number;
  technological_risk: number;
}

interface RiskAssessment {
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  risk_score: number;
  risk_factors: {
    factor: string;
    level: number;
    description: string;
    mitigation: string;
  }[];
  var_metrics: {
    var_95: number;
    var_99: number;
    var_1d: number;
    var_1w: number;
    var_1m: number;
  };
  stress_test: {
    market_crash: number;
    liquidity_crisis: number;
    credit_event: number;
    system_failure: number;
  };
  portfolio_metrics: {
    sharpe_ratio: number;
    sortino_ratio: number;
    max_drawdown: number;
    calmar_ratio: number;
    beta: number;
    alpha: number;
    information_ratio: number;
  };
  recommendations: {
    risk_level: string;
    actions: string[];
    monitoring: string[];
  };
}

const RiskAnalysis: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(false);
  const [riskData, setRiskData] = useState<{
    score: number;
    metrics: RiskMetrics;
    assessment: RiskAssessment;
    last_updated: string;
  } | null>(null);
  const [timeRange, setTimeRange] = useState('1M');

  const fetchRiskAnalysisCb = React.useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/config/analysis/risk?range=${timeRange}`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const result = await response.json();
        setRiskData(result);
      }
    } catch (error) {
      console.error('获取风险分析数据失败:', error);
    } finally {
      setLoading(false);
    }
  }, [timeRange])

  useEffect(() => {
    if (isAuthenticated) {
      fetchRiskAnalysisCb();
    }
  }, [isAuthenticated, fetchRiskAnalysisCb]);

  const getRiskColor = (score: number) => {
    if (score <= 3) return '#52c41a';
    if (score <= 6) return '#faad14';
    if (score <= 8) return '#ff7875';
    return '#f5222d';
  };

  

  const getRiskLevelText = (level: string) => {
    switch (level) {
      case 'low': return '低风险';
      case 'medium': return '中等风险';
      case 'high': return '高风险';
      case 'critical': return '极高风险';
      default: return '未知风险';
    }
  };

  const getRiskIcon = (score: number) => {
    if (score <= 3) return <SafetyOutlined />;
    if (score <= 6) return <SafetyOutlined />;
    if (score <= 8) return <WarningOutlined />;
    return <ExclamationCircleOutlined />;
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
      <Title level={3}>风险分析</Title>
      <Paragraph>
        综合市场风险、信用风险、流动性风险、操作风险等多维度的专业风险评估和管理建议
      </Paragraph>

      {/* 时间范围选择 */}
      <div style={{ marginBottom: '24px', textAlign: 'center' }}>
        <Radio.Group value={timeRange} onChange={(e) => setTimeRange(e.target.value)} size="large">
          <Radio.Button value="1D">1天</Radio.Button>
          <Radio.Button value="1W">1周</Radio.Button>
          <Radio.Button value="1M">1个月</Radio.Button>
          <Radio.Button value="3M">3个月</Radio.Button>
          <Radio.Button value="1Y">1年</Radio.Button>
        </Radio.Group>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin size="large" />
        </div>
      ) : riskData ? (
        <>
          {/* 总体风险评分 */}
          <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
            <Col span={8}>
              <Card>
                <Statistic
                  title="综合风险评分"
                  value={riskData.score}
                  suffix="/10"
                  valueStyle={{ color: getRiskColor(riskData.score) }}
                  prefix={getRiskIcon(riskData.score)}
                />
                <Progress 
                  percent={riskData.score * 10} 
                  strokeColor={getRiskColor(riskData.score)}
                  showInfo={false}
                />
                <div style={{ marginTop: '8px', textAlign: 'center' }}>
                  <Text strong style={{ color: getRiskColor(riskData.score) }}>
                    {riskData.assessment.risk_level === 'low' ? '低风险' : 
                     riskData.assessment.risk_level === 'medium' ? '中等风险' :
                     riskData.assessment.risk_level === 'high' ? '高风险' : '极高风险'}
                  </Text>
                </div>
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic
                  title="夏普比率"
                  value={riskData.assessment.portfolio_metrics.sharpe_ratio.toFixed(2)}
                  precision={2}
                  valueStyle={{ color: riskData.assessment.portfolio_metrics.sharpe_ratio > 1.5 ? '#52c41a' : riskData.assessment.portfolio_metrics.sharpe_ratio > 1 ? '#faad14' : '#f5222d' }}
                  prefix={<LineChartOutlined />}
                />
                <Text type="secondary">风险调整后收益</Text>
              </Card>
            </Col>
            <Col span={8}>
              <Card>
                <Statistic
                  title="最大回撤"
                  value={(riskData.assessment.portfolio_metrics.max_drawdown * 100).toFixed(2)}
                  suffix="%"
                  valueStyle={{ color: riskData.assessment.portfolio_metrics.max_drawdown < 0.1 ? '#52c41a' : riskData.assessment.portfolio_metrics.max_drawdown < 0.2 ? '#faad14' : '#f5222d' }}
                  prefix={<ThunderboltOutlined />}
                />
                <Text type="secondary">历史最大损失</Text>
              </Card>
            </Col>
          </Row>

          {/* 风险指标 */}
          <Title level={4}>风险指标分析</Title>
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <Card title="市场风险指标" style={{ marginBottom: '16px' }}>
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Text>市场风险: </Text>
                    <Text strong>{riskData.metrics.market_risk.toFixed(2)}</Text>
                  </Col>
                  <Col span={12}>
                    <Text>波动率风险: </Text>
                    <Text strong>{riskData.metrics.volatility_risk.toFixed(2)}</Text>
                  </Col>
                  <Col span={12}>
                    <Text>集中度风险: </Text>
                    <Text strong>{riskData.metrics.concentration_risk.toFixed(2)}</Text>
                  </Col>
                  <Col span={12}>
                    <Text>相关性风险: </Text>
                    <Text strong>{riskData.metrics.correlation_risk.toFixed(2)}</Text>
                  </Col>
                </Row>
              </Card>
            </Col>
            <Col span={12}>
              <Card title="非市场风险指标" style={{ marginBottom: '16px' }}>
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Text>信用风险: </Text>
                    <Text strong>{riskData.metrics.credit_risk.toFixed(2)}</Text>
                  </Col>
                  <Col span={12}>
                    <Text>流动性风险: </Text>
                    <Text strong>{riskData.metrics.liquidity_risk.toFixed(2)}</Text>
                  </Col>
                  <Col span={12}>
                    <Text>操作风险: </Text>
                    <Text strong>{riskData.metrics.operational_risk.toFixed(2)}</Text>
                  </Col>
                  <Col span={12}>
                    <Text>技术风险: </Text>
                    <Text strong>{riskData.metrics.technological_risk.toFixed(2)}</Text>
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>

          {/* 风险因素详细分析 */}
          <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
            <Col span={24}>
              <Card title="风险因素详细分析">
                <Table
                  dataSource={riskData.assessment.risk_factors.map((factor, index) => ({
                    key: index,
                    factor: factor.factor,
                    level: factor.level,
                    description: factor.description,
                    mitigation: factor.mitigation
                  }))}
                  columns={[
                    {
                      title: '风险因素',
                      dataIndex: 'factor',
                      key: 'factor',
                      render: (text: string) => <Text strong>{text}</Text>
                    },
                    {
                      title: '风险等级',
                      dataIndex: 'level',
                      key: 'level',
                      render: (level: number) => (
                        <Tag color={getRiskColor(level)}>
                          {level <= 3 ? '低' : level <= 6 ? '中' : level <= 8 ? '高' : '极'}
                        </Tag>
                      )
                    },
                    {
                      title: '风险描述',
                      dataIndex: 'description',
                      key: 'description',
                    },
                    {
                      title: '缓解措施',
                      dataIndex: 'mitigation',
                      key: 'mitigation',
                    }
                  ]}
                  pagination={false}
                  size="middle"
                  scroll={{ x: 800 }}
                />
              </Card>
            </Col>
          </Row>

          {/* VaR指标 */}
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Card title="风险价值(VaR)指标">
                <Row gutter={[16, 16]}>
                  <Col span={6}>
                    <div style={{ textAlign: 'center' }}>
                      <Statistic
                        title="VaR (95%)"
                        value={`${(riskData.assessment.var_metrics.var_95 * 100).toFixed(2)}%`}
                        valueStyle={{ color: '#1890ff' }}
                      />
                      <Text type="secondary">95%置信度</Text>
                    </div>
                  </Col>
                  <Col span={6}>
                    <div style={{ textAlign: 'center' }}>
                      <Statistic
                        title="VaR (99%)"
                        value={`${(riskData.assessment.var_metrics.var_99 * 100).toFixed(2)}%`}
                        valueStyle={{ color: '#faad14' }}
                      />
                      <Text type="secondary">99%置信度</Text>
                    </div>
                  </Col>
                  <Col span={6}>
                    <div style={{ textAlign: 'center' }}>
                      <Statistic
                        title="1日VaR"
                        value={`${(riskData.assessment.var_metrics.var_1d * 100).toFixed(3)}%`}
                        valueStyle={{ color: '#52c41a' }}
                      />
                      <Text type="secondary">单日风险</Text>
                    </div>
                  </Col>
                  <Col span={6}>
                    <div style={{ textAlign: 'center' }}>
                      <Statistic
                        title="1月VaR"
                        value={`${(riskData.assessment.var_metrics.var_1m * 100).toFixed(2)}%`}
                        valueStyle={{ color: '#f5222d' }}
                      />
                      <Text type="secondary">单月风险</Text>
                    </div>
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>

          {/* 压力测试 */}
          <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
            <Col span={24}>
              <Card title="压力测试">
                <Row gutter={[16, 16]}>
                  <Col span={6}>
                    <div style={{ textAlign: 'center' }}>
                      <Statistic
                        title="市场崩盘"
                        value={`${(riskData.assessment.stress_test.market_crash * 100).toFixed(1)}%`}
                        valueStyle={{ color: riskData.assessment.stress_test.market_crash > 0.2 ? '#f5222d' : '#faad14' }}
                      />
                      <Text type="secondary">潜在损失</Text>
                    </div>
                  </Col>
                  <Col span={6}>
                    <div style={{ textAlign: 'center' }}>
                      <Statistic
                        title="流动性危机"
                        value={`${(riskData.assessment.stress_test.liquidity_crisis * 100).toFixed(1)}%`}
                        valueStyle={{ color: riskData.assessment.stress_test.liquidity_crisis > 0.15 ? '#f5222d' : '#52c41a' }}
                      />
                      <Text type="secondary">流动性风险</Text>
                    </div>
                  </Col>
                  <Col span={6}>
                    <div style={{ textAlign: 'center' }}>
                      <Statistic
                        title="信用事件"
                        value={`${(riskData.assessment.stress_test.credit_event * 100).toFixed(1)}%`}
                        valueStyle={{ color: riskData.assessment.stress_test.credit_event > 0.1 ? '#f5222d' : '#52c41a' }}
                      />
                      <Text type="secondary">信用损失</Text>
                    </div>
                  </Col>
                  <Col span={6}>
                    <div style={{ textAlign: 'center' }}>
                      <Statistic
                        title="系统故障"
                        value={`${(riskData.assessment.stress_test.system_failure * 100).toFixed(1)}%`}
                        valueStyle={{ color: riskData.assessment.stress_test.system_failure > 0.05 ? '#f5222d' : '#52c41a' }}
                      />
                      <Text type="secondary">系统风险</Text>
                    </div>
                  </Col>
                </Row>
              </Card>
            </Col>
          </Row>

          {/* 投资组合指标 */}
          <Row gutter={[16, 16]} style={{ marginBottom: '16px' }}>
            <Col span={24}>
              <Card title="投资组合风险指标">
                <Table
                  dataSource={[
                    {
                      key: '1',
                      metric: '夏普比率',
                      value: riskData.assessment.portfolio_metrics.sharpe_ratio.toFixed(2),
                      benchmark: '1.5',
                      status: riskData.assessment.portfolio_metrics.sharpe_ratio > 1.5 ? '优秀' : 
                              riskData.assessment.portfolio_metrics.sharpe_ratio > 1 ? '良好' : '需改善'
                    },
                    {
                      key: '2',
                      metric: '索提诺比率',
                      value: riskData.assessment.portfolio_metrics.sortino_ratio.toFixed(2),
                      benchmark: '2.0',
                      status: riskData.assessment.portfolio_metrics.sortino_ratio > 2.0 ? '优秀' : 
                              riskData.assessment.portfolio_metrics.sortino_ratio > 1.5 ? '良好' : '需改善'
                    },
                    {
                      key: '3',
                      metric: '最大回撤',
                      value: `${(riskData.assessment.portfolio_metrics.max_drawdown * 100).toFixed(2)}%`,
                      benchmark: '10%',
                      status: riskData.assessment.portfolio_metrics.max_drawdown < 0.1 ? '优秀' : 
                              riskData.assessment.portfolio_metrics.max_drawdown < 0.2 ? '良好' : '需改善'
                    },
                    {
                      key: '4',
                      metric: '卡玛比率',
                      value: riskData.assessment.portfolio_metrics.calmar_ratio.toFixed(2),
                      benchmark: '3.0',
                      status: riskData.assessment.portfolio_metrics.calmar_ratio > 3.0 ? '优秀' : 
                              riskData.assessment.portfolio_metrics.calmar_ratio > 2.0 ? '良好' : '需改善'
                    },
                    {
                      key: '5',
                      metric: '贝塔系数',
                      value: riskData.assessment.portfolio_metrics.beta.toFixed(2),
                      benchmark: '1.0',
                      status: riskData.assessment.portfolio_metrics.beta < 1.2 ? '优秀' : 
                              riskData.assessment.portfolio_metrics.beta < 1.5 ? '良好' : '需改善'
                    },
                    {
                      key: '6',
                      metric: '阿尔法系数',
                      value: `${(riskData.assessment.portfolio_metrics.alpha * 100).toFixed(2)}%`,
                      benchmark: '5%',
                      status: riskData.assessment.portfolio_metrics.alpha > 0.05 ? '优秀' : 
                              riskData.assessment.portfolio_metrics.alpha > 0.02 ? '良好' : '需改善'
                    }
                  ]}
                  columns={[
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
                      title: '基准',
                      dataIndex: 'benchmark',
                      key: 'benchmark',
                    },
                    {
                      title: '状态',
                      dataIndex: 'status',
                      key: 'status',
                      render: (status: string) => {
                        let color = 'default';
                        if (status === '优秀') color = '#52c41a';
                        if (status === '良好') color = '#1890ff';
                        if (status === '需改善') color = '#faad14';
                        return <Tag color={color}>{status}</Tag>;
                      }
                    }
                  ]}
                  pagination={false}
                  size="middle"
                />
              </Card>
            </Col>
          </Row>

          {/* 风险管理建议 */}
          <Divider />
          <Card title="风险管理建议">
            <List
              dataSource={[
                {
                  title: '风险等级评估',
                  description: `当前综合风险等级为${getRiskLevelText(riskData.assessment.risk_level)}，风险评分为${riskData.score}/10。${riskData.assessment.risk_level === 'low' ? '投资组合风险可控，适合长期持有' : riskData.assessment.risk_level === 'medium' ? '投资组合风险适中，建议定期监控' : riskData.assessment.risk_level === 'high' ? '投资组合风险较高，建议调整仓位' : '投资组合风险极高，建议立即采取风险控制措施'}。`
                },
                {
                  title: '建议行动',
                  description: riskData.assessment.recommendations.actions.map((action, index) => 
                    <div key={index} style={{ marginBottom: '8px' }}>
                      {index + 1}. {action}
                    </div>
                  )
                },
                {
                  title: '监控要点',
                  description: riskData.assessment.recommendations.monitoring.map((item, index) => 
                    <div key={index} style={{ marginBottom: '8px' }}>
                      {index + 1}. {item}
                    </div>
                  )
                }
              ]}
              renderItem={(item) => <List.Item><List.Item.Meta title={item.title} description={item.description} /></List.Item>}
            />
          </Card>

          {/* 更新时间 */}
          <Divider />
          <Text type="secondary">
            最后更新时间: {new Date(riskData.last_updated).toLocaleString('zh-CN')}
          </Text>
        </>
      ) : (
        <Card>
          <Alert message="暂无风险分析数据" type="info" showIcon />
        </Card>
      )}
    </div>
  );
};

export default RiskAnalysis;