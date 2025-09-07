import React, { memo, useMemo } from 'react';
import { Card, Row, Col, Button, Badge, Statistic } from 'antd';
import { 
  PlayCircleOutlined, 
  PauseCircleOutlined, 
  StopOutlined 
} from '@ant-design/icons';
import { Strategy } from '../../services/api';

interface OptimizedStrategyCardProps {
  strategy: Strategy;
  onControlStrategy: (strategyId: string, action: 'start' | 'stop' | 'reload') => void;
}

const OptimizedStrategyCard: React.FC<OptimizedStrategyCardProps> = memo(({
  strategy,
  onControlStrategy
}) => {
  // 使用useMemo优化状态配置，避免每次渲染都重新创建
  const strategyStatusColor = useMemo(() => ({
    running: '#52c41a',
    stopped: '#8c8c8c',
    error: '#ff4d4f',
    paused: '#faad14'
  }), []);

  const strategyStatusText = useMemo(() => ({
    running: '运行中',
    stopped: '已停止',
    error: '错误',
    paused: '暂停'
  }), []);

  // 计算性能数据
  const performanceData = useMemo(() => {
    if (!strategy.performance) return null;
    
    return {
      winRate: strategy.performance.winRate.toFixed(1),
      tradesCount: strategy.performance.tradesCount,
      maxDrawdown: strategy.performance.maxDrawdown.toFixed(2),
      totalPnl: strategy.performance.totalPnl.toFixed(2)
    };
  }, [strategy.performance]);

  return (
    <Card size="small">
      <Row gutter={16}>
        <Col span={8}>
          <div style={{ fontWeight: 'bold' }}>{strategy.name}</div>
          <Badge 
            color={strategyStatusColor[strategy.status]} 
            text={strategyStatusText[strategy.status]}
          />
        </Col>
        <Col span={8}>
          <div style={{ fontSize: 12, color: '#666' }}>类型</div>
          <div>{strategy.type}</div>
        </Col>
        <Col span={8}>
          <div style={{ fontSize: 12, color: '#666' }}>
            {strategy.performance ? '总盈亏' : '状态'}
          </div>
          <div style={{ 
            color: strategy.performance?.totalPnl >= 0 ? '#3f8600' : '#cf1322' 
          }}>
            {strategy.performance ? `$${performanceData?.totalPnl}` : '-'}
          </div>
        </Col>
      </Row>
      
      {performanceData && (
        <Row gutter={16} style={{ marginTop: 8 }}>
          <Col span={6}>
            <div style={{ fontSize: 12, color: '#666' }}>胜率</div>
            <div>{performanceData.winRate}%</div>
          </Col>
          <Col span={6}>
            <div style={{ fontSize: 12, color: '#666' }}>交易次数</div>
            <div>{performanceData.tradesCount}</div>
          </Col>
          <Col span={6}>
            <div style={{ fontSize: 12, color: '#666' }}>最大回撤</div>
            <div>{performanceData.maxDrawdown}%</div>
          </Col>
          <Col span={6}>
            <Button.Group size="small">
              <Button
                icon={strategy.status === 'running' ? 
                  <PauseCircleOutlined /> : 
                  <PlayCircleOutlined />}
                onClick={() => onControlStrategy(
                  strategy.id, 
                  strategy.status === 'running' ? 'stop' : 'start'
                )}
              />
              <Button
                icon={<StopOutlined />}
                onClick={() => onControlStrategy(strategy.id, 'stop')}
              />
            </Button.Group>
          </Col>
        </Row>
      )}
    </Card>
  );
});

export default OptimizedStrategyCard;