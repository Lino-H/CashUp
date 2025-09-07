import React, { memo, useMemo } from 'react';
import { Table, Button, Tag, Space, Popconfirm } from 'antd';
import { EyeOutlined, StopOutlined } from '@ant-design/icons';
import { Order } from '../../services/api';
import moment from 'moment';

interface OptimizedOrderTableProps {
  orders: Order[];
  onViewDetail: (order: Order) => void;
  onCancelOrder: (orderId: string) => void;
  loading?: boolean;
}

const OptimizedOrderTable: React.FC<OptimizedOrderTableProps> = memo(({
  orders,
  onViewDetail,
  onCancelOrder,
  loading = false
}) => {
  // 使用useMemo优化列定义，避免每次渲染都重新创建
  const columns = useMemo(() => [
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp: string) => (
        <span>{moment(timestamp).format('HH:mm:ss')}</span>
      ),
      sorter: (a: Order, b: Order) => 
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    },
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
      render: (symbol: string) => (
        <Tag color="green">{symbol}</Tag>
      )
    },
    {
      title: '方向',
      dataIndex: 'side',
      key: 'side',
      render: (side: string) => (
        <Tag color={side === 'buy' ? 'green' : 'red'}>
          {side === 'buy' ? '买入' : '卖出'}
        </Tag>
      )
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag color={type === 'market' ? 'blue' : 'orange'}>
          {type === 'market' ? '市价' : '限价'}
        </Tag>
      )
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => `$${price.toFixed(2)}`,
      sorter: (a: Order, b: Order) => a.price - b.price
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (quantity: number) => quantity.toFixed(4)
    },
    {
      title: '成交数量',
      dataIndex: 'filledQuantity',
      key: 'filledQuantity',
      render: (filledQuantity: number) => filledQuantity.toFixed(4)
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusConfig = {
          pending: { color: 'orange', text: '待成交' },
          filled: { color: 'green', text: '已成交' },
          cancelled: { color: 'red', text: '已取消' },
          failed: { color: 'red', text: '失败' }
        };
        const config = statusConfig[status as keyof typeof statusConfig];
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: '盈亏',
      dataIndex: 'pnl',
      key: 'pnl',
      render: (pnl: number) => (
        <span style={{ color: pnl >= 0 ? '#3f8600' : '#cf1322', fontWeight: 'bold' }}>
          {pnl >= 0 ? '+' : ''}${pnl?.toFixed(2) || '0.00'}
        </span>
      )
    },
    {
      title: '操作',
      key: 'actions',
      render: (text: string, record: Order) => (
        <Space>
          <Button
            type="link"
            icon={<EyeOutlined />}
            onClick={() => onViewDetail(record)}
          >
            详情
          </Button>
          {record.status === 'pending' && (
            <Popconfirm
              title="确定要取消这个订单吗？"
              onConfirm={() => onCancelOrder(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                type="link"
                danger
                icon={<StopOutlined />}
              >
                取消
              </Button>
            </Popconfirm>
          )}
        </Space>
      )
    }
  ], []);

  return (
    <Table
      columns={columns}
      dataSource={orders}
      rowKey="id"
      loading={loading}
      pagination={{
        pageSize: 10,
        showSizeChanger: true,
        showQuickJumper: true,
        showTotal: (total, range) => 
          `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
      }}
      scroll={{ x: 1200 }}
      bordered
      size="middle"
    />
  );
});

export default OptimizedOrderTable;