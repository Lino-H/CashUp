import { renderHook, act } from '@testing-library/react';
import { useDebounce, useDebouncedValue } from '../useDebounce';

describe('useDebounce', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test('should debounce callback execution', () => {
    const mockCallback = jest.fn();
    const { result } = renderHook(() => useDebounce(mockCallback, 300));

    // Trigger the debounced function
    act(() => {
      result.current('test-arg');
    });

    // Callback should not have been called yet
    expect(mockCallback).not.toHaveBeenCalled();

    // Fast forward time by 300ms
    act(() => {
      jest.advanceTimersByTime(300);
    });

    // Now callback should have been called
    expect(mockCallback).toHaveBeenCalledTimes(1);
    expect(mockCallback).toHaveBeenCalledWith('test-arg');
  });

  test('should cancel previous timeout when called multiple times', () => {
    const mockCallback = jest.fn();
    const { result } = renderHook(() => useDebounce(mockCallback, 300));

    // Trigger the debounced function multiple times quickly
    act(() => {
      result.current('first-arg');
      result.current('second-arg');
      result.current('third-arg');
    });

    // Callback should not have been called yet
    expect(mockCallback).not.toHaveBeenCalled();

    // Fast forward time by 300ms
    act(() => {
      jest.advanceTimersByTime(300);
    });

    // Callback should only have been called once with the last argument
    expect(mockCallback).toHaveBeenCalledTimes(1);
    expect(mockCallback).toHaveBeenCalledWith('third-arg');
  });

  test('should maintain callback reference', () => {
    const mockCallback = jest.fn();
    const { result, rerender } = renderHook(
      ({ callback, delay }) => useDebounce(callback, delay),
      { initialProps: { callback: mockCallback, delay: 300 } }
    );

    const firstCallback = result.current;

    // Rerender with same callback
    rerender({ callback: mockCallback, delay: 300 });

    // Callback reference should be the same
    expect(result.current).toBe(firstCallback);

    // Rerender with different callback
    const newMockCallback = jest.fn();
    rerender({ callback: newMockCallback, delay: 300 });

    // Callback reference should be different
    expect(result.current).not.toBe(firstCallback);
  });

  test('should handle different delay values', () => {
    const mockCallback = jest.fn();
    const { result } = renderHook(() => useDebounce(mockCallback, 100));

    // Trigger the debounced function
    act(() => {
      result.current('test-arg');
    });

    // Callback should not have been called yet
    expect(mockCallback).not.toHaveBeenCalled();

    // Fast forward time by 50ms (not enough)
    act(() => {
      jest.advanceTimersByTime(50);
    });

    // Callback should still not have been called
    expect(mockCallback).not.toHaveBeenCalled();

    // Fast forward time by another 100ms (total 150ms)
    act(() => {
      jest.advanceTimersByTime(100);
    });

    // Now callback should have been called
    expect(mockCallback).toHaveBeenCalledTimes(1);
    expect(mockCallback).toHaveBeenCalledWith('test-arg');
  });
});

describe('useDebouncedValue', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test('should return debounced value', () => {
    const { result, rerender } = renderHook(({ value, delay }) => useDebouncedValue(value, delay), {
      initialProps: { value: 'initial', delay: 300 }
    });

    expect(result.current).toBe('initial');

    rerender({ value: 'updated', delay: 300 });

    expect(result.current).toBe('initial');

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(result.current).toBe('updated');
  });

  test('should handle multiple value changes', () => {
    const { result, rerender } = renderHook(({ value, delay }) => useDebouncedValue(value, delay), {
      initialProps: { value: 'value1', delay: 300 }
    });

    expect(result.current).toBe('value1');

    rerender({ value: 'value2', delay: 300 });
    rerender({ value: 'value3', delay: 300 });
    rerender({ value: 'value4', delay: 300 });

    expect(result.current).toBe('value1');

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(result.current).toBe('value4');
  });

  test('should reset timeout when delay changes', () => {
    const { result, rerender } = renderHook(({ value, delay }) => useDebouncedValue(value, delay), {
      initialProps: { value: 'initial', delay: 300 }
    });

    rerender({ value: 'updated', delay: 300 });

    rerender({ value: 'updated', delay: 100 });

    act(() => {
      jest.advanceTimersByTime(200);
    });

    expect(result.current).toBe('updated');
  });

  test('should handle different value types', () => {
    const { result, rerender } = renderHook(({ value, delay }) => useDebouncedValue(value, delay), {
      initialProps: { value: 42, delay: 300 }
    });

    expect(result.current).toBe(42);

    rerender({ value: 'test', delay: 300 });

    expect(result.current).toBe(42);

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(result.current).toBe('test');

    rerender({ value: { key: 'value' }, delay: 300 });

    expect(result.current).toBe('test');

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(result.current).toEqual({ key: 'value' });
  });
});
