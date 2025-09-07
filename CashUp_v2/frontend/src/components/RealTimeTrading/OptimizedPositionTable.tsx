import React, { memo, useMemo } from 'react';
import { Table, Tag, Popconfirm, Button } from 'antd';
import { StopOutlined } from '@ant-design/icons';
import { Position } from '../../services/api';

interface OptimizedPositionTableProps {
  positions: Position[];
  onClosePosition: (positionId: string) => void;
  loading?: boolean;
}

const OptimizedPositionTable: React.FC<OptimizedPositionTableProps> = memo(({
  positions,
  onClosePosition,
  loading = false
}) => {
  // 使用useMemo优化列定义，避免每次渲染都重新创建
  const columns = useMemo(() => [
    {
      title: '策略ID',
      dataIndex: 'strategyId',
      key: 'strategyId',
      render: (strategyId: string) => (
        <Tag color="blue">{strategyId}</Tag>
      )
    },
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol: string) => <Tag color="green">{symbol}</Tag>
    },
    {
      title: '方向',
      dataIndex: 'side',
      key: 'side',
      render: (side: string) => (
        <Tag color={side === 'long' ? 'green' : 'red'}>
          {side === 'long' ? '多头' : '空头'}
        </Tag>
      )
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (quantity: number) => quantity.toFixed(4)
    },
    {
      title: '入场价格',
      dataIndex: 'entryPrice',
      key: 'entryPrice',
      render: (price: number) => `$${price.toFixed(2)}`
    },
    {
      title: '当前价格',
      dataIndex: 'currentPrice',
      key: 'currentPrice',
      render: (price: number) => `$${price.toFixed(2)}`
    },
    {
      title: '盈亏',
      dataIndex: 'pnl',
      key: 'pnl',
      render: (pnl: number) => (
        <span style={{ color: pnl >= 0 ? '#3f8600' : '#cf1322', fontWeight: 'bold' }}>
          {pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}
        </span>
      )
    },
    {
      title: '盈亏比例',
      dataIndex: 'pnlPercent',
      key: 'pnlPercent',
      render: (percent: number) => (
        <span style={{ color: percent >= 0 ? '#3f8600' : '#cf1322' }}>
          {percent >= 0 ? '+' : ''}{percent.toFixed(2)}%
        </span>
      )
    },
    {
      title: '保证金',
      dataIndex: 'margin',
      key: 'margin',
      render: (margin: number) => `$${margin.toFixed(2)}`
    },
    {
      title: '杠杆',
      dataIndex: 'leverage',
      key: 'leverage',
      render: (leverage: number) => `${leverage}x`
    },
    {
      title: '操作',
      key: 'actions',
      render: (text: string, record: Position) => (
        <Popconfirm
          title="确定要平仓吗？"
          onConfirm={() => onClosePosition(record.id)}
          okText="确定"
          cancelText="取消"
        >
          <Button
            type="link"
            danger
            icon={<StopOutlined />}
          >
            平仓
          </Button>
        </Popconfirm>
      )
    }
  ], []);

  return (
    <Table
      columns={columns}
      dataSource={positions}
      rowKey="id"
      loading={loading}
      pagination={{
        pageSize: 10,
        showSizeChanger: true,
        showTotal: (total, range) => 
          `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
      }}
      bordered
      size="middle"
    />
  );
});

export default OptimizedPositionTable;