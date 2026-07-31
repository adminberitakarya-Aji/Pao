/** Redis Client Configuration */

import Redis from 'ioredis';
import { config } from './config.js';

// Create Redis client
export const redis = new Redis(config.redis.url, {
  maxRetriesPerRequest: config.redis.maxRetries,
  retryStrategy: (times) => {
    if (times > config.redis.maxRetries) {
      return null; // Stop retrying
    }
    return Math.min(times * 100, 3000);
  },
  lazyConnect: true,
});

// Handle connection events
redis.on('connect', () => {
  console.log('✅ Redis connected');
});

redis.on('error', (err) => {
  console.error('❌ Redis error:', err);
});

redis.on('close', () => {
  console.warn('⚠️ Redis connection closed');
});

redis.on('reconnecting', () => {
  console.log('🔄 Redis reconnecting...');
});

// Health check
export async function checkRedisHealth(): Promise<boolean> {
  try {
    const result = await redis.ping();
    return result === 'PONG';
  } catch (error) {
    console.error('Redis health check failed:', error);
    return false;
  }
}

// Graceful shutdown
export async function closeRedis(): Promise<void> {
  await redis.quit();
}

// Export types
export type RedisClient = Redis;