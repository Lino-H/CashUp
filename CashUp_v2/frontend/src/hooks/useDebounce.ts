/**
 * 防抖Hook - 减少频繁操作导致的重新渲染
 */

import { useCallback, useRef, useState, useEffect } from 'react';

export const useDebounce = <T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T => {
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  return useCallback(
    ((...args: Parameters<T>) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = setTimeout(() => {
        callback(...args);
      }, delay);
    }) as T,
    [callback, delay]
  );
};

export const useDebouncedValue = <T>(value: T, delay: number): T => {
  const [debouncedValue, setDebouncedValue] = useState(value);
  const debouncedSet = useDebounce(setDebouncedValue, delay);

  useEffect(() => {
    debouncedSet(value);
  }, [value, debouncedSet]);

  return debouncedValue;
};