import React, { useEffect, useState } from 'react';
import { Card, List, Tag, Typography, Space } from 'antd';
import { createWebSocketManager, getWebSocketUrl } from '../utils/websocketManager';

const { Title } = Typography;

interface NewsItem {
  id: string;
  source?: string;
  title: string;
  summary?: string;
  url: string;
  published_at?: string;
  category?: string;
  sentiment_score?: string;
  sentiment_label?: string;
  symbols?: string[];
}

const NewsPage: React.FC = () => {
  const [items, setItems] = useState<NewsItem[]>([]);

  const load = async () => {
    const resp = await fetch('/api/news?limit=50');
    const data = await resp.json();
    if (data && data.data) setItems(data.data);
  };

  useEffect(() => {
    load();
    const wsUrl = getWebSocketUrl('news', '/ws/news');
    const ws = createWebSocketManager(wsUrl);
    ws.subscribe('news');
    return () => ws.disconnect();
  }, []);

  return (
    <div style={{ padding: 24 }}>
      <Title level={3}>市场新闻与情绪</Title>
      <Card>
        <List
          itemLayout="vertical"
          dataSource={items}
          renderItem={(item) => (
            <List.Item key={item.id}
              extra={
                <Space>
                  {item.sentiment_label && <Tag color={item.sentiment_label === 'positive' ? 'green' : item.sentiment_label === 'negative' ? 'red' : 'gold'}>{item.sentiment_label}</Tag>}
                  {item.category && <Tag>{item.category}</Tag>}
                </Space>
              }
            >
              <List.Item.Meta
                title={<a href={item.url} target="_blank" rel="noreferrer">{item.title}</a>}
                description={<Space wrap>
                  {item.source && <Tag>{item.source}</Tag>}
                  {item.symbols?.map(s => <Tag key={s}>{s}</Tag>)}
                </Space>}
              />
              {item.summary}
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
};

export default NewsPage;