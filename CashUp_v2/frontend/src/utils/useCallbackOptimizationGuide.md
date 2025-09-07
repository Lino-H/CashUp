# useCallback 优化指南

## 概述

useCallback 是 React 提供的一个钩子，用于缓存函数实例。当组件重新渲染时，useCallback 可以确保函数引用保持不变，从而避免不必要的子组件重新渲染。

## 什么时候使用 useCallback

### 推荐使用 useCallback 的情况

1. **传递给子组件的回调函数**：当函数作为 props 传递给子组件时
2. **事件处理函数**：点击、输入等事件处理函数
3. **自定义 Hook**：创建自定义 Hook 时
4. **依赖项列表中的函数**：当函数作为 useEffect 或 useMemo 的依赖项时
5. **性能敏感的组件**：需要避免不必要的重新渲染的组件

### 不推荐使用 useCallback 的情况

1. **简单的内联函数**：函数逻辑简单且不频繁重新渲染
2. **开发阶段**：在开发阶段，过早优化会增加复杂性
3. **函数经常变化**：如果函数依赖项经常变化，缓存效果不明显

## useCallback 最佳实践

### 1. 基本用法

```typescript
import React, { useState, useCallback } from 'react';

const ParentComponent = () => {
  const [count, setCount] = useState(0);
  
  // 使用 useCallback 缓存函数
  const handleClick = useCallback(() => {
    console.log('Button clicked', count);
    setCount(count + 1);
  }, [count]); // 依赖项数组

  return (
    <div>
      <button onClick={handleClick}>Click me</button>
      <ChildComponent onClick={handleClick} />
    </div>
  );
};

const ChildComponent = React.memo(({ onClick }) => {
  return <button onClick={onClick}>Child Button</button>;
});
```

### 2. 复杂回调函数

```typescript
const UserProfile = ({ userId }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);

  // 复杂的异步函数
  const fetchUser = useCallback(async (id) => {
    setLoading(true);
    try {
      const response = await api.getUser(id);
      setUser(response);
    } catch (error) {
      console.error('Failed to fetch user:', error);
    } finally {
      setLoading(false);
    }
  }, []); // 不依赖任何状态

  // 表单提交处理
  const handleSubmit = useCallback(async (formData) => {
    try {
      await api.updateUser(userId, formData);
      message.success('Profile updated successfully');
    } catch (error) {
      console.error('Failed to update profile:', error);
      message.error('Failed to update profile');
    }
  }, [userId]); // 依赖 userId

  return (
    <div>
      {loading ? <Spin /> : (
        <Form onFinish={handleSubmit}>
          {/* 表单内容 */}
        </Form>
      )}
    </div>
  );
};
```

### 3. 事件处理函数

```typescript
const ShoppingList = () => {
  const [items, setItems] = useState([]);
  const [newItem, setNewItem] = useState('');

  // 输入变化处理
  const handleInputChange = useCallback((e) => {
    setNewItem(e.target.value);
  }, []);

  // 添加物品
  const handleAddItem = useCallback(() => {
    if (newItem.trim()) {
      setItems(prev => [...prev, newItem.trim()]);
      setNewItem('');
    }
  }, [newItem]);

  // 删除物品
  const handleDeleteItem = useCallback((index) => {
    setItems(prev => prev.filter((_, i) => i !== index));
  }, []);

  // 清空列表
  const handleClearAll = useCallback(() => {
    setItems([]);
  }, []);

  return (
    <div>
      <input
        type="text"
        value={newItem}
        onChange={handleInputChange}
        placeholder="Add new item"
      />
      <button onClick={handleAddItem}>Add</button>
      <ul>
        {items.map((item, index) => (
          <li key={index}>
            {item}
            <button onClick={() => handleDeleteItem(index)}>Delete</button>
          </li>
        ))}
      </ul>
      <button onClick={handleClearAll}>Clear All</button>
    </div>
  );
};
```

### 4. 自定义 Hook 中的 useCallback

```typescript
// 自定义 Hook
const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async (url, options = {}) => {
    setLoading(true);
    try {
      const response = await fetch(url, options);
      const data = await response.json();
      return data;
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const postData = useCallback(async (url, data) => {
    setLoading(true);
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      return await response.json();
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading,
    error,
    fetchData,
    postData,
  };
};

// 使用自定义 Hook
const UserProfile = ({ userId }) => {
  const { loading, error, fetchData } = useApi();

  const [user, setUser] = useState(null);

  useEffect(() => {
    if (userId) {
      fetchData(`/api/users/${userId}`)
        .then(data => setUser(data));
    }
  }, [userId, fetchData]);

  if (loading) return <Spin />;
  if (error) return <Error message={error.message} />;
  if (!user) return null;

  return <div>{user.name}</div>;
};
```

### 5. 表单处理中的 useCallback

```typescript
const LoginForm = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  // 表单提交处理
  const handleSubmit = useCallback(async (values) => {
    setLoading(true);
    try {
      const response = await api.login(values);
      // 处理登录成功
      message.success('Login successful');
      form.resetFields();
    } catch (error) {
      message.error('Login failed');
    } finally {
      setLoading(false);
    }
  }, [form]); // 依赖 form 实例

  // 重置表单
  const handleReset = useCallback(() => {
    form.resetFields();
  }, [form]);

  return (
    <Form
      form={form}
      onFinish={handleSubmit}
      onReset={handleReset}
    >
      <Form.Item
        name="username"
        rules={[{ required: true }]}
      >
        <Input placeholder="Username" />
      </Form.Item>
      <Form.Item
        name="password"
        rules={[{ required: true }]}
      >
        <Input.Password placeholder="Password" />
      </Form.Item>
      <Form.Item>
        <Space>
          <Button type="primary" htmlType="submit" loading={loading}>
            Login
          </Button>
          <Button htmlType="reset">
            Reset
          </Button>
        </Space>
      </Form.Item>
    </Form>
  );
};
```

### 6. 复杂组件中的 useCallback

```typescript
const Dashboard = () => {
  const [data, setData] = useState([]);
  const [filters, setFilters] = useState({});
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10 });

  // 获取数据
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.getData({
        ...filters,
        page: pagination.current,
        pageSize: pagination.pageSize,
      });
      setData(response.data);
      setPagination(prev => ({
        ...prev,
        total: response.total,
      }));
    } catch (error) {
      message.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  }, [filters, pagination]);

  // 处理筛选变化
  const handleFilterChange = useCallback((newFilters) => {
    setFilters(newFilters);
    setPagination(prev => ({ ...prev, current: 1 })); // 重置到第一页
  }, []);

  // 处理分页变化
  const handlePaginationChange = useCallback((newPagination) => {
    setPagination(newPagination);
  }, []);

  // 刷新数据
  const handleRefresh = useCallback(() => {
    fetchData();
  }, [fetchData]);

  // 使用 useEffect 在依赖项变化时获取数据
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <div>
      <FilterBar 
        filters={filters}
        onFilterChange={handleFilterChange}
        onRefresh={handleRefresh}
      />
      <DataTable
        data={data}
        loading={loading}
        pagination={pagination}
        onPaginationChange={handlePaginationChange}
      />
    </div>
  );
};
```

## useCallback 与 useMemo 的区别

### useCallback

```typescript
// 缓存函数
const memoizedCallback = useCallback(() => {
  doSomething(a, b);
}, [a, b]);
```

### useMemo

```typescript
// 缓存计算结果
const memoizedValue = useMemo(() => {
  return computeExpensiveValue(a, b);
}, [a, b]);
```

## 性能对比

### 优化前的问题

```typescript
// 问题：每次渲染都创建新函数
const Parent = () => {
  const [count, setCount] = useState(0);
  
  const handleClick = () => {
    console.log('Clicked', count);
  };

  return (
    <div>
      <button onClick={() => setCount(count + 1)}>Increment</button>
      <ChildComponent onClick={handleClick} />
    </div>
  );
};

// 问题：ChildComponent 会频繁重新渲染
const ChildComponent = ({ onClick }) => {
  return <button onClick={onClick}>Child Button</button>;
};
```

### 优化后的改进

```typescript
// 优化：使用 useCallback 缓存函数
const Parent = () => {
  const [count, setCount] = useState(0);
  
  const handleClick = useCallback(() => {
    console.log('Clicked', count);
  }, [count]); // 只有 count 变化时才重新创建

  return (
    <div>
      <button onClick={() => setCount(count + 1)}>Increment</button>
      <MemoizedChildComponent onClick={handleClick} />
    </div>
  );
};

// 优化：使用 React.memo 避免不必要的重新渲染
const MemoizedChildComponent = React.memo(({ onClick }) => {
  return <button onClick={onClick}>Child Button</button>;
});
```

## 注意事项

### 1. 正确设置依赖项

```typescript
// 错误：遗漏依赖项
const Component = ({ data }) => {
  const handleClick = useCallback(() => {
    console.log(data.id); // data 没有在依赖项中
  }, []); // 应该包含 data

  return <button onClick={handleClick}>Click</button>;
};

// 正确：包含所有依赖项
const Component = ({ data }) => {
  const handleClick = useCallback(() => {
    console.log(data.id);
  }, [data]); // 包含 data

  return <button onClick={handleClick}>Click</button>;
};
```

### 2. 避免过度优化

```typescript
// 不必要的优化：简单的函数
const SimpleComponent = () => {
  const handleClick = useCallback(() => {
    console.log('Simple click');
  }, []); // 简单函数不需要 useCallback

  return <button onClick={handleClick}>Click</button>;
};

// 推荐：直接使用内联函数
const SimpleComponent = () => {
  return (
    <button onClick={() => console.log('Simple click')}>
      Click
    </button>
  );
};
```

### 3. 使用 linter 工具

```json
// .eslintrc.json
{
  "rules": {
    "react-hooks/exhaustive-deps": "warn"
  }
}
```

## 总结

useCallback 是一个强大的性能优化工具，但需要正确使用：

1. **识别性能瓶颈**：找出不必要的重新渲染
2. **合理使用**：在合适的场景使用 useCallback
3. **正确设置依赖项**：确保包含所有必要的依赖
4. **避免过度优化**：不要过早优化，也不要过度优化
5. **测试验证**：确保优化确实提升了性能

通过合理使用 useCallback，可以显著提升 React 应用的性能，特别是在处理复杂交互和大型应用时。