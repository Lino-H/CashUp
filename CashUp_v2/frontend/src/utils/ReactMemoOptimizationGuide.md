# React.memo 优化指南

## 概述

React.memo 是一个高阶组件，它通过记忆化组件的渲染结果来优化性能。当组件的 props 没有发生变化时，React.memo 会跳过重新渲染，从而提高应用性能。

## 什么时候使用 React.memo

### 推荐使用 React.memo 的情况

1. **纯展示组件**：组件的主要职责是展示数据，没有复杂的内部状态
2. **频繁重新渲染的组件**：当父组件频繁重新渲染时，子组件可能被不必要地重新渲染
3. **大型列表**：特别是大数据量的表格、列表等
4. **性能敏感的组件**：动画、图表等需要高性能的组件
5. **具有复杂计算的组件**：组件需要执行昂贵的计算

### 不推荐使用 React.memo 的情况

1. **经常变化的组件**：组件的 props 频繁变化时，记忆化效果不明显
2. **小型组件**：组件本身渲染开销很小时，优化效果不明显
3. **有内部状态的组件**：组件内部状态频繁变化时，记忆化效果有限
4. **开发中的组件**：开发阶段不建议过早优化

## React.memo 最佳实践

### 1. 优化子组件

```typescript
// 原始组件
const OrderTable = ({ orders, loading }) => {
  // 复杂的渲染逻辑
  return <Table dataSource={orders} loading={loading} />;
};

// 优化后的组件
const OrderTable = React.memo(({ orders, loading }) => {
  // 复杂的渲染逻辑
  return <Table dataSource={orders} loading={loading} />;
});

// 自定义比较函数
const OrderTable = React.memo(({ orders, loading }) => {
  // 复杂的渲染逻辑
  return <Table dataSource={orders} loading={loading} />;
}, (prevProps, nextProps) => {
  // 自定义比较逻辑
  return prevProps.orders === nextProps.orders && prevProps.loading === nextProps.loading;
});
```

### 2. 使用 useMemo 优化复杂计算

```typescript
const OptimizedComponent = ({ data, filter }) => {
  // 使用 useMemo 优化计算结果
  const filteredData = useMemo(() => {
    return data.filter(item => item.category === filter);
  }, [data, filter]);

  // 使用 useMemo 优化渲染元素
  const tableColumns = useMemo(() => [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (price) => `$${price.toFixed(2)}`,
    },
  ], []);

  return (
    <Table columns={tableColumns} dataSource={filteredData} />
  );
};
```

### 3. 使用 useCallback 优化事件处理函数

```typescript
const ParentComponent = () => {
  const [data, setData] = useState([]);

  // 使用 useCallback 避免不必要的重新创建
  const handleDelete = useCallback((id) => {
    setData(prev => prev.filter(item => item.id !== id));
  }, []);

  // 使用 useCallback 优化回调函数
  const handleEdit = useCallback((item) => {
    // 编辑逻辑
  }, []);

  return (
    <div>
      <ChildComponent 
        data={data}
        onDelete={handleDelete}
        onEdit={handleEdit}
      />
    </div>
  );
};
```

### 4. 优化列表渲染

```typescript
// 优化前
const OrderList = ({ orders }) => {
  return (
    <div>
      {orders.map(order => (
        <OrderItem key={order.id} order={order} />
      ))}
    </div>
  );
};

// 优化后
const OrderList = React.memo(({ orders }) => {
  return (
    <div>
      {orders.map(order => (
        <OrderItem key={order.id} order={order} />
      ))}
    </div>
  );
});

// 进一步优化：使用 React.memo 优化子组件
const OrderItem = React.memo(({ order }) => {
  return (
    <div>
      <h3>{order.name}</h3>
      <p>{order.price}</p>
    </div>
  );
});
```

### 5. 优化表格组件

```typescript
const OptimizedTable = ({ data, loading, columns }) => {
  // 使用 useMemo 优化列定义
  const tableColumns = useMemo(() => columns, [columns]);

  // 使用 useMemo 优化数据过滤
  const processedData = useMemo(() => {
    return data.map(item => ({
      ...item,
      formattedPrice: `$${item.price.toFixed(2)}`
    }));
  }, [data]);

  return (
    <Table 
      columns={tableColumns}
      dataSource={processedData}
      loading={loading}
      pagination={false}
    />
  );
};
```

## 性能对比

### 优化前的性能问题

```typescript
// 问题：每次父组件重新渲染，子组件都会重新渲染
const Parent = () => {
  const [count, setCount] = useState(0);
  
  return (
    <div>
      <button onClick={() => setCount(count + 1)}>Increment</button>
      <ChildComponent data={someData} />
    </div>
  );
};

// 问题：每次渲染都会创建新的函数
const ChildComponent = ({ data }) => {
  const handleClick = () => {
    // 处理点击
  };
  
  return (
    <div>
      {data.map(item => (
        <div key={item.id} onClick={handleClick}>
          {item.name}
        </div>
      ))}
    </div>
  );
};
```

### 优化后的性能改进

```typescript
// 优化：使用 React.memo 和 useCallback
const Parent = () => {
  const [count, setCount] = useState(0);
  
  return (
    <div>
      <button onClick={() => setCount(count + 1)}>Increment</button>
      <MemoizedChildComponent data={someData} />
    </div>
  );
};

const MemoizedChildComponent = React.memo(({ data }) => {
  const handleClick = useCallback(() => {
    // 处理点击
  }, []);
  
  return (
    <div>
      {data.map(item => (
        <div key={item.id} onClick={handleClick}>
          {item.name}
        </div>
      ))}
    </div>
  );
});
```

## 注意事项

### 1. 不要过早优化

- 在开发过程中，不要过早使用 React.memo
- 先确定性能瓶颈，再进行优化
- 使用 React DevTools 分析性能

### 2. 避免过度优化

- 不是所有组件都需要 React.memo
- 小组件的优化效果可能不明显
- 过度使用可能导致内存泄漏

### 3. 正确使用依赖项

- 确保 useMemo 和 useCallback 的依赖项正确
- 避免遗漏依赖项导致的问题
- 使用 linter 工具检查依赖项

### 4. 测试优化效果

- 使用 React DevTools 测量性能
- 比较优化前后的渲染次数
- 确保优化确实提升了性能

## 总结

React.memo 是一个强大的性能优化工具，但需要正确使用。遵循以下原则：

1. **识别性能瓶颈**：使用 React DevTools 找出需要优化的组件
2. **合理使用**：在合适的场景使用 React.memo
3. **配合其他优化**：结合 useMemo、useCallback 等钩子
4. **测试验证**：确保优化确实提升了性能
5. **避免过度优化**：不要过早优化，也不要过度优化

通过合理使用 React.memo，可以显著提升 React 应用的性能，特别是在处理大型列表和复杂组件时。