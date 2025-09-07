import { dataCache, useCache } from '../cache';

// Mock Date.now() for testing time-based operations
const mockDateNow = jest.spyOn(Date, 'now');

describe('DataCache', () => {
  beforeEach(() => {
    dataCache.clear();
    mockDateNow.mockReturnValue(1000000);
  });

  afterEach(() => {
    mockDateNow.mockRestore();
  });

  describe('Basic Operations', () => {
    test('should set and get data', () => {
      dataCache.set('test-key', { value: 'test-data' });
      
      const result = dataCache.get('test-key');
      expect(result).toEqual({ value: 'test-data' });
    });

    test('should return null for non-existent key', () => {
      const result = dataCache.get('non-existent-key');
      expect(result).toBeNull();
    });

    test('should delete data', () => {
      dataCache.set('test-key', { value: 'test-data' });
      dataCache.delete('test-key');
      
      const result = dataCache.get('test-key');
      expect(result).toBeNull();
    });

    test('should clear all data', () => {
      dataCache.set('key1', { value: 'data1' });
      dataCache.set('key2', { value: 'data2' });
      
      expect(dataCache.size()).toBe(2);
      
      dataCache.clear();
      
      expect(dataCache.size()).toBe(0);
    });
  });

  describe('TTL Functionality', () => {
    test('should expire data after TTL', () => {
      dataCache.set('test-key', { value: 'test-data' }, 1000); // 1 second TTL
      
      mockDateNow.mockReturnValue(1000000 + 500); // 500ms later, not expired
      let result = dataCache.get('test-key');
      expect(result).toEqual({ value: 'test-data' });
      
      mockDateNow.mockReturnValue(1000000 + 1500); // 1500ms later, expired
      result = dataCache.get('test-key');
      expect(result).toBeNull();
    });

    test('should not expire data if TTL is not set', () => {
      dataCache.set('test-key', { value: 'test-data' });
      
      mockDateNow.mockReturnValue(1000000 + 100000); // Much later
      const result = dataCache.get('test-key');
      expect(result).toEqual({ value: 'test-data' });
    });
  });

  describe('Key Generation', () => {
    test('should generate correct cache keys', () => {
      const key1 = (dataCache as any).generateKey('/api/users');
      const key2 = (dataCache as any).generateKey('/api/users', { page: 1 });
      const key3 = (dataCache as any).generateKey('/api/users', { page: 2 });
      
      expect(key1).toBe('/api/users');
      expect(key2).toBe('/api_users_{"page":1}');
      expect(key3).toBe('/api_users_{"page":2}');
      
      expect(key2).not.toBe(key3);
    });
  });

  describe('fetchWithCache', () => {
    test('should fetch data from API when not in cache', async () => {
      const mockApiCall = jest.fn().mockResolvedValue({ data: 'fresh-data' });
      
      const result = await dataCache.fetchWithCache('/api/test', mockApiCall);
      
      expect(result).toEqual({ data: 'fresh-data' });
      expect(mockApiCall).toHaveBeenCalledTimes(1);
    });

    test('should return cached data when available', async () => {
      dataCache.set('/api/test', { data: 'cached-data' });
      
      const mockApiCall = jest.fn().mockResolvedValue({ data: 'fresh-data' });
      
      const result = await dataCache.fetchWithCache('/api/test', mockApiCall);
      
      expect(result).toEqual({ data: 'cached-data' });
      expect(mockApiCall).not.toHaveBeenCalled();
    });

    test('should call API with custom TTL', async () => {
      const mockApiCall = jest.fn().mockResolvedValue({ data: 'fresh-data' });
      
      await dataCache.fetchWithCache('/api/test', mockApiCall, { ttl: 2000 });
      
      expect(mockApiCall).toHaveBeenCalledTimes(1);
    });
  });

  describe('batchFetch', () => {
    test('should fetch multiple requests with caching', async () => {
      const mockApiCall1 = jest.fn().mockResolvedValue({ data: 'result1' });
      const mockApiCall2 = jest.fn().mockResolvedValue({ data: 'result2' });
      
      // Pre-populate one request in cache
      dataCache.set('key1', { data: 'cached-result1' });
      
      const requests = [
        { key: 'key1', apiCall: mockApiCall1 },
        { key: 'key2', apiCall: mockApiCall2 }
      ];
      
      const results = await dataCache.batchFetch(requests);
      
      expect(results.get('key1')).toEqual({ data: 'cached-result1' });
      expect(results.get('key2')).toEqual({ data: 'result2' });
      expect(mockApiCall1).not.toHaveBeenCalled();
      expect(mockApiCall2).toHaveBeenCalledTimes(1);
    });
  });

  describe('preload', () => {
    test('should preload multiple endpoints', async () => {
      const mockApiCall1 = jest.fn().mockResolvedValue({ data: 'preloaded1' });
      const mockApiCall2 = jest.fn().mockResolvedValue({ data: 'preloaded2' });
      
      const endpoints = [
        { key: 'preload1', apiCall: mockApiCall1 },
        { key: 'preload2', apiCall: mockApiCall2, ttl: 3000 }
      ];
      
      await dataCache.preload(endpoints);
      
      expect(mockApiCall1).toHaveBeenCalledTimes(1);
      expect(mockApiCall2).toHaveBeenCalledTimes(1);
      
      const result1 = dataCache.get('preload1');
      const result2 = dataCache.get('preload2');
      
      expect(result1).toEqual({ data: 'preloaded1' });
      expect(result2).toEqual({ data: 'preloaded2' });
    });
  });
});

describe('useCache Hook', () => {
  beforeEach(() => {
    dataCache.clear();
  });

  test('should provide cache operations', () => {
    const cache = useCache();
    
    cache.set('test-key', { value: 'test-data' });
    
    const result = cache.get('test-key');
    expect(result).toEqual({ value: 'test-data' });
    
    cache.clear();
    
    const clearedResult = cache.get('test-key');
    expect(clearedResult).toBeNull();
  });

  test('should handle TTL in hook', () => {
    const cache = useCache();
    
    cache.set('test-key', { value: 'test-data' }, 1000);
    
    const result = cache.get('test-key');
    expect(result).toEqual({ value: 'test-data' });
  });
});