/** Backend API Main Entry Point - Fastify Application */

import Fastify, { FastifyInstance, FastifyRequest, FastifyReply } from 'fastify';
import { config } from './config.js';
import { db, pool, checkDatabaseHealth, closeDatabase } from './database.js';
import { redis, checkRedisHealth, closeRedis } from './redis.js';
import { kafka, producer, connectProducer, disconnectProducer, checkKafkaHealth, topics } from './kafka.js';
import { users, sessions } from './models/index.js';
import { eq, and, gt, desc } from 'drizzle-orm';
import { z } from 'zod';
import bcrypt from 'bcryptjs';
import { ulid } from 'ulid';
import jwt from 'jsonwebtoken';
import { register } from 'prom-client';

// Initialize metrics
const metricsRegister = register;
metricsRegister.setDefaultLabels({ app: 'pao-backend-api' });

// Create Fastify instance
export const app: FastifyInstance = Fastify({
  logger: {
    level: config.observability.logLevel,
    transport: config.app.isDev ? {
      target: 'pino-pretty',
      options: { colorize: true, translateTime: 'HH:MM:ss Z', ignore: 'pid,hostname' },
    } : undefined,
  },
  ajv: {
    customOptions: { strict: false },
  },
});

// Register plugins
async function registerPlugins(): Promise<void> {
  // CORS
  await app.register(import('@fastify/cors'), {
    origin: config.cors.origin,
    credentials: true,
  });

  // Helmet
  await app.register(import('@fastify/helmet'), {
    contentSecurityPolicy: config.app.isProd,
  });

  // Rate limiting
  await app.register(import('@fastify/rate-limit'), {
    max: config.rateLimit.max,
    timeWindow: config.rateLimit.windowMs,
    hook: 'onRequest',
  });

  // JWT
  await app.register(import('@fastify/jwt'), {
    secret: config.auth.jwtSecret,
    sign: {
      issuer: config.auth.issuer,
      audience: config.auth.audience,
    },
    verify: {
      issuer: config.auth.issuer,
      audience: config.auth.audience,
    },
  });

  // Swagger
  await app.register(import('@fastify/swagger'), {
    openapi: {
      info: {
        title: 'PAO Backend API',
        description: 'Backend API for PAO AI Companion',
        version: '1.0.0',
      },
      components: {
        securitySchemes: {
          bearerAuth: { type: 'http', scheme: 'bearer', bearerFormat: 'JWT' },
        },
      },
      security: [{ bearerAuth: [] }],
    },
  });

  await app.register(import('@fastify/swagger-ui'), {
    routePrefix: '/docs',
    uiConfig: { docExpansion: 'list', deepLinking: true },
  });

  // Sensible (error handling)
  await app.register(import('@fastify/sensible'));
}

// Authentication decorators
declare module 'fastify' {
  interface FastifyRequest {
    user?: UserTokenPayload;
    session?: SessionTokenPayload;
  }
}

interface UserTokenPayload {
  sub: string;
  email: string;
  tier: string;
  iat: number;
  exp: number;
}

interface SessionTokenPayload {
  sub: string;
  userId: string;
  deviceId: string;
  iat: number;
  exp: number;
}

// Auth hooks
async function authenticate(request: FastifyRequest, reply: FastifyReply): Promise<void> {
  try {
    const payload = await request.jwtVerify<UserTokenPayload>();
    request.user = payload;
  } catch (err) {
    reply.code(401).send({ error: 'Unauthorized', message: 'Invalid or expired token' });
  }
}

async function authenticateSession(request: FastifyRequest, reply: FastifyReply): Promise<void> {
  const authHeader = request.headers.authorization;
  if (!authHeader?.startsWith('Bearer ')) {
    return reply.code(401).send({ error: 'Unauthorized', message: 'Missing session token' });
  }

  const sessionToken = authHeader.slice(7);
  try {
    const payload = jwt.verify(sessionToken, config.auth.jwtSecret) as SessionTokenPayload;
    
    // Verify session exists and is valid
    const session = await db.query.sessions.findFirst({
      where: and(
        eq(sessions.id, payload.sub),
        eq(sessions.userId, payload.userId),
        eq(sessions.deviceId, payload.deviceId),
        gt(sessions.expiresAt, new Date()),
        eq(sessions.revokedAt, null)
      ),
    });

    if (!session) {
      return reply.code(401).send({ error: 'Unauthorized', message: 'Session invalid or expired' });
    }

    request.session = payload;
  } catch (err) {
    return reply.code(401).send({ error: 'Unauthorized', message: 'Invalid session token' });
  }
}

// Auth routes
async function authRoutes(): Promise<void> {
  // Register
  app.post('/api/v1/auth/register', {
    schema: {
      body: z.object({
        email: z.string().email(),
        password: z.string().min(8).max(128),
        fullName: z.string().min(1).max(100).optional(),
      }),
      response: {
        201: z.object({
          user: z.object({ id: z.string().uuid(), email: z.string().email(), tier: z.string() }),
          accessToken: z.string(),
          refreshToken: z.string(),
        }),
        400: z.object({ error: z.string(), message: z.string() }),
        409: z.object({ error: z.string(), message: z.string() }),
      },
    },
  }, async (request, reply) => {
    const { email, password, fullName } = request.body as { email: string; password: string; fullName?: string };

    // Check if user exists
    const existing = await db.query.users.findFirst({ where: eq(users.email, email) });
    if (existing) {
      return reply.code(409).send({ error: 'Conflict', message: 'Email already registered' });
    }

    // Hash password
    const passwordHash = await bcrypt.hash(password, 12);

    // Create user
    const [user] = await db.insert(users).values({
      email,
      passwordHash,
      tier: 'free',
    }).returning();

    // Generate tokens
    const accessToken = app.jwt.sign({ sub: user.id, email: user.email, tier: user.tier });
    const refreshToken = app.jwt.sign({ sub: user.id, type: 'refresh' }, { expiresIn: config.auth.refreshTtl });

    // Store refresh token in Redis
    await redis.setex(`refresh:${user.id}:${refreshToken}`, 60 * 60 * 24 * 30, 'valid');

    return reply.code(201).send({ user: { id: user.id, email: user.email, tier: user.tier }, accessToken, refreshToken });
  });

  // Login
  app.post('/api/v1/auth/login', {
    schema: {
      body: z.object({
        email: z.string().email(),
        password: z.string(),
        deviceId: z.string().optional(),
        deviceName: z.string().optional(),
      }),
      response: {
        200: z.object({
          user: z.object({ id: z.string().uuid(), email: z.string().email(), tier: z.string() }),
          accessToken: z.string(),
          refreshToken: z.string(),
        }),
        401: z.object({ error: z.string(), message: z.string() }),
      },
    },
  }, async (request, reply) => {
    const { email, password, deviceId, deviceName } = request.body as { email: string; password: string; deviceId?: string; deviceName?: string };

    const user = await db.query.users.findFirst({ where: eq(users.email, email) });
    if (!user || !user.passwordHash) {
      return reply.code(401).send({ error: 'Unauthorized', message: 'Invalid credentials' });
    }

    const valid = await bcrypt.compare(password, user.passwordHash);
    if (!valid) {
      return reply.code(401).send({ error: 'Unauthorized', message: 'Invalid credentials' });
    }

    if (!user.isActive) {
      return reply.code(401).send({ error: 'Unauthorized', message: 'Account deactivated' });
    }

    const accessToken = app.jwt.sign({ sub: user.id, email: user.email, tier: user.tier });
    const refreshToken = app.jwt.sign({ sub: user.id, type: 'refresh' }, { expiresIn: config.auth.refreshTtl });

    // Store refresh token
    await redis.setex(`refresh:${user.id}:${refreshToken}`, 60 * 60 * 24 * 30, 'valid');

    // Create session if device info provided
    if (deviceId) {
      const sessionId = ulid();
      const expiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000); // 30 days
      
      await db.insert(sessions).values({
        id: sessionId,
        userId: user.id,
        deviceId,
        deviceName: deviceName || 'Unknown Device',
        expiresAt,
      });
    }

    return { user: { id: user.id, email: user.email, tier: user.tier }, accessToken, refreshToken };
  });

  // Refresh token
  app.post('/api/v1/auth/refresh', {
    schema: {
      body: z.object({ refreshToken: z.string() }),
      response: {
        200: z.object({ accessToken: z.string(), refreshToken: z.string() }),
        401: z.object({ error: z.string(), message: z.string() }),
      },
    },
  }, async (request, reply) => {
    const { refreshToken } = request.body as { refreshToken: string };

    try {
      const payload = app.jwt.verify(refreshToken) as { sub: string; type: string };
      
      if (payload.type !== 'refresh') {
        return reply.code(401).send({ error: 'Unauthorized', message: 'Invalid token type' });
      }

      // Check if refresh token is valid in Redis
      const valid = await redis.get(`refresh:${payload.sub}:${refreshToken}`);
      if (!valid) {
        return reply.code(401).send({ error: 'Unauthorized', message: 'Refresh token revoked' });
      }

      const user = await db.query.users.findFirst({ where: eq(users.id, payload.sub) });
      if (!user || !user.isActive) {
        return reply.code(401).send({ error: 'Unauthorized', message: 'User not found or inactive' });
      }

      const newAccessToken = app.jwt.sign({ sub: user.id, email: user.email, tier: user.tier });
      const newRefreshToken = app.jwt.sign({ sub: user.id, type: 'refresh' }, { expiresIn: config.auth.refreshTtl });

      // Rotate refresh token
      await redis.del(`refresh:${user.id}:${refreshToken}`);
      await redis.setex(`refresh:${user.id}:${newRefreshToken}`, 60 * 60 * 24 * 30, 'valid');

      return { accessToken: newAccessToken, refreshToken: newRefreshToken };
    } catch (err) {
      return reply.code(401).send({ error: 'Unauthorized', message: 'Invalid refresh token' });
    }
  });

  // Logout
  app.post('/api/v1/auth/logout', { preHandler: authenticate }, async (request, reply) => {
    const authHeader = request.headers.authorization;
    if (authHeader?.startsWith('Bearer ')) {
      const token = authHeader.slice(7);
      try {
        const payload = app.jwt.verify(token) as { sub: string };
        await redis.del(`refresh:${payload.sub}:${token}`);
      } catch {}
    }
    return { success: true };
  });

  // Get current user
  app.get('/api/v1/auth/me', { preHandler: authenticate }, async (request, reply) => {
    const user = await db.query.users.findFirst({ 
      where: eq(users.id, request.user!.sub),
      columns: { id: true, email: true, tier: true, isActive: true, createdAt: true, settingsJson: true },
    });
    return { user };
  });
}

// Health check routes
async function healthRoutes(): Promise<void> {
  app.get('/health', async () => {
    const [dbHealthy, redisHealthy, kafkaHealthy] = await Promise.all([
      checkDatabaseHealth(),
      checkRedisHealth(),
      checkKafkaHealth(),
    ]);

    return {
      status: dbHealthy && redisHealthy && kafkaHealthy ? 'healthy' : 'degraded',
      timestamp: new Date().toISOString(),
      services: {
        database: dbHealthy ? 'healthy' : 'unhealthy',
        redis: redisHealthy ? 'healthy' : 'unhealthy',
        kafka: kafkaHealthy ? 'healthy' : 'unhealthy',
      },
      version: '1.0.0',
    };
  });

  app.get('/health/live', async () => ({ status: 'alive', timestamp: new Date().toISOString() }));

  app.get('/health/ready', async () => {
    const [dbHealthy, redisHealthy] = await Promise.all([checkDatabaseHealth(), checkRedisHealth()]);
    if (!dbHealthy || !redisHealthy) {
      return { status: 'not ready', timestamp: new Date().toISOString() };
    }
    return { status: 'ready', timestamp: new Date().toISOString() };
  });

  // Metrics endpoint
  app.get('/metrics', async (request, reply) => {
    reply.header('Content-Type', metricsRegister.contentType);
    return metricsRegister.metrics();
  });
}

// AI Engine client
const engineClient = {
  async call(engineUrl: string, path: string, method: 'GET' | 'POST' = 'GET', body?: unknown) {
    const url = `${engineUrl}${path}`;
    const response = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!response.ok) {
      throw new Error(`Engine call failed: ${response.status} ${response.statusText}`);
    }
    return response.json();
  },

  // Companion Runtime
  async chat(userId: string, message: string, context?: Record<string, unknown>) {
    return this.call(config.engines.companionRuntime, '/api/v1/chat', 'POST', { userId, message, context });
  },

  // Identity Engine
  async getProfile(userId: string) {
    return this.call(config.engines.identity, `/api/v1/users/${userId}/profile`);
  },

  // Memory Engine
  async searchMemory(userId: string, query: string, limit = 10) {
    return this.call(config.engines.memory, '/api/v1/search', 'POST', { userId, query, limit });
  },

  // Safety Engine
  async checkSafety(content: string) {
    return this.call(config.engines.safety, '/api/v1/check', 'POST', { content });
  },

  // Emotion Engine
  async analyzeEmotion(text: string, audioUrl?: string) {
    return this.call(config.engines.emotion, '/api/v1/analyze', 'POST', { text, audioUrl });
  },

  // Voice Engine
  async textToSpeech(text: string, voice?: string) {
    return this.call(config.engines.voice, '/api/v1/tts', 'POST', { text, voice });
  },

  // Proactive Engine
  async getProactiveSuggestions(userId: string) {
    return this.call(config.engines.proactive, `/api/v1/users/${userId}/suggestions`);
  },
};

// Chat routes
async function chatRoutes(): Promise<void> {
  app.post('/api/v1/chat', { preHandler: authenticate }, async (request, reply) => {
    const { message, context } = request.body as { message: string; context?: Record<string, unknown> };
    const userId = request.user!.sub;

    // Safety check
    const safety = await engineClient.checkSafety(message);
    if (!safety.safe) {
      return reply.code(400).send({ error: 'Content blocked', reason: safety.reason });
    }

    // Get proactive context if enabled
    let proactiveContext = {};
    if (config.features.enableProactive) {
      const suggestions = await engineClient.getProactiveSuggestions(userId);
      proactiveContext = { suggestions };
    }

    // Get memory context
    const memoryContext = await engineClient.searchMemory(userId, message, 5);

    // Call companion runtime
    const response = await engineClient.chat(userId, message, {
      ...context,
      memory: memoryContext,
      proactive: proactiveContext,
    });

    // Emit event to Kafka
    await producer.send({
      topic: topics.messageCreated,
      messages: [{
        key: userId,
        value: JSON.stringify({ userId, message, response: response.message, timestamp: new Date().toISOString() }),
      }],
    });

    return response;
  });

  app.get('/api/v1/chat/history', { preHandler: authenticate }, async (request, reply) => {
    // Implementation for chat history
    return { messages: [] };
  });
}

// User routes
async function userRoutes(): Promise<void> {
  app.get('/api/v1/users/profile', { preHandler: authenticate }, async (request) => {
    const profile = await engineClient.getProfile(request.user!.sub);
    return profile;
  });

  app.patch('/api/v1/users/profile', { preHandler: authenticate }, async (request, reply) => {
    // Update profile
    return { success: true };
  });

  app.get('/api/v1/users/sessions', { preHandler: authenticate }, async (request) => {
    const userSessions = await db.query.sessions.findMany({
      where: and(eq(sessions.userId, request.user!.sub), eq(sessions.revokedAt, null)),
      orderBy: (sessions, { desc }) => [desc(sessions.createdAt)],
    });
    return { sessions: userSessions };
  });

  app.delete('/api/v1/users/sessions/:sessionId', { preHandler: authenticate }, async (request, reply) => {
    const { sessionId } = request.params as { sessionId: string };
    await db.update(sessions).set({ revokedAt: new Date() }).where(and(eq(sessions.id, sessionId), eq(sessions.userId, request.user!.sub)));
    return { success: true };
  });
}

// Initialize all routes
async function initializeRoutes(): Promise<void> {
  await registerPlugins();
  await authRoutes();
  await healthRoutes();
  await chatRoutes();
  await userRoutes();

  // 404 handler
  app.setNotFoundHandler(async (request, reply) => {
    reply.code(404).send({ error: 'Not Found', message: `Route ${request.method} ${request.url} not found` });
  });
}

// Start server
export async function start(): Promise<void> {
  try {
    await initializeRoutes();
    await connectProducer();

    // Connect database
    await pool.connect();
    console.log('✅ Database connected');

    // Connect Redis
    await redis.connect();
    console.log('✅ Redis connected');

    // Start server
    await app.listen({ port: config.app.port, host: config.app.host });
    console.log(`🚀 Server running at http://${config.app.host}:${config.app.port}`);
    console.log(`📚 API Docs at http://${config.app.host}:${config.app.port}/docs`);
  } catch (err) {
    console.error('Failed to start server:', err);
    process.exit(1);
  }
}

// Graceful shutdown
export async function shutdown(): Promise<void> {
  console.log('🛑 Shutting down...');
  
  await Promise.all([
    closeDatabase(),
    closeRedis(),
    disconnectProducer(),
    app.close(),
  ]);
  
  console.log('✅ Shutdown complete');
}

// Handle signals
process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);

// Start if run directly
if (import.meta.url === `file://${process.argv[1]}`) {
  start();
}