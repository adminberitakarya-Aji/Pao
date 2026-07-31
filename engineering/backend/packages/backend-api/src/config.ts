/** Backend API Configuration - Pydantic-like Settings with Zod */

import { z } from 'zod';
import { config as dotenvConfig } from 'dotenv';

// Load environment variables
dotenvConfig();

const envSchema = z.object({
  // App
  NODE_ENV: z.enum(['development', 'staging', 'production']).default('development'),
  PORT: z.coerce.number().default(3000),
  HOST: z.string().default('0.0.0.0'),
  APP_URL: z.string().url().default('http://localhost:3000'),

  // Database
  DATABASE_URL: z.string().url(),
  DATABASE_POOL_SIZE: z.coerce.number().default(20),
  DATABASE_SSL: z.coerce.boolean().default(false),

  // Redis
  REDIS_URL: z.string().url(),
  REDIS_MAX_RETRIES: z.coerce.number().default(3),

  // Kafka
  KAFKA_BROKERS: z.string().default('localhost:9092'),
  KAFKA_CLIENT_ID: z.string().default('pao-backend-api'),
  KAFKA_CONSUMER_GROUP: z.string().default('pao-backend-api-consumer'),

  // Auth
  JWT_SECRET: z.string().min(32),
  JWT_REFRESH_SECRET: z.string().min(32),
  JWT_ACCESS_TTL: z.string().default('15m'),
  JWT_REFRESH_TTL: z.string().default('30d'),
  JWT_ISSUER: z.string().default('pao-backend'),
  JWT_AUDIENCE: z.string().default('pao-mobile'),

  // OAuth
  GOOGLE_CLIENT_ID: z.string().optional(),
  GOOGLE_CLIENT_SECRET: z.string().optional(),
  APPLE_CLIENT_ID: z.string().optional(),
  APPLE_TEAM_ID: z.string().optional(),
  APPLE_KEY_ID: z.string().optional(),
  APPLE_PRIVATE_KEY: z.string().optional(),

  // AI Engine URLs
  INFERENCE_GATEWAY_URL: z.string().url().default('http://localhost:8000'),
  IDENTITY_ENGINE_URL: z.string().url().default('http://localhost:8003'),
  MEMORY_ENGINE_URL: z.string().url().default('http://localhost:8004'),
  SAFETY_ENGINE_URL: z.string().url().default('http://localhost:8005'),
  RELATIONSHIP_ENGINE_URL: z.string().url().default('http://localhost:8006'),
  EMOTION_ENGINE_URL: z.string().url().default('http://localhost:8007'),
  VOICE_ENGINE_URL: z.string().url().default('http://localhost:8008'),
  PROACTIVE_ENGINE_URL: z.string().url().default('http://localhost:8009'),
  EVALUATION_ENGINE_URL: z.string().url().default('http://localhost:8010'),
  COMPANION_RUNTIME_URL: z.string().url().default('http://localhost:8011'),

  // Stripe
  STRIPE_SECRET_KEY: z.string().optional(),
  STRIPE_WEBHOOK_SECRET: z.string().optional(),
  STRIPE_PRICE_ID_MONTHLY: z.string().optional(),
  STRIPE_PRICE_ID_YEARLY: z.string().optional(),

  // Email
  SENDGRID_API_KEY: z.string().optional(),
  SENDGRID_FROM_EMAIL: z.string().email().optional(),
  SENDGRID_FROM_NAME: z.string().optional().default('PAO'),

  // Push Notifications
  FIREBASE_PROJECT_ID: z.string().optional(),
  FIREBASE_CLIENT_EMAIL: z.string().optional(),
  FIREBASE_PRIVATE_KEY: z.string().optional(),
  WEB_PUSH_VAPID_PUBLIC_KEY: z.string().optional(),
  WEB_PUSH_VAPID_PRIVATE_KEY: z.string().optional(),
  WEB_PUSH_VAPID_SUBJECT: z.string().optional(),

  // LiveKit
  LIVEKIT_API_KEY: z.string().optional(),
  LIVEKIT_API_SECRET: z.string().optional(),
  LIVEKIT_WS_URL: z.string().url().optional(),

  // S3 / Object Storage
  S3_ENDPOINT: z.string().url().optional(),
  S3_REGION: z.string().optional(),
  S3_ACCESS_KEY: z.string().optional(),
  S3_SECRET_KEY: z.string().optional(),
  S3_BUCKET: z.string().optional(),

  // Observability
  OTEL_EXPORTER_OTLP_ENDPOINT: z.string().url().optional(),
  OTEL_SERVICE_NAME: z.string().default('pao-backend-api'),
  LOG_LEVEL: z.enum(['debug', 'info', 'warn', 'error']).default('info'),
  PROMETHEUS_PORT: z.coerce.number().default(9090),

  // Rate Limiting
  RATE_LIMIT_MAX: z.coerce.number().default(100),
  RATE_LIMIT_WINDOW_MS: z.coerce.number().default(60000),

  // CORS
  CORS_ORIGIN: z.string().default('*'),

  // Feature Flags
  ENABLE_VOICE: z.coerce.boolean().default(true),
  ENABLE_PROACTIVE: z.coerce.boolean().default(true),
  ENABLE_MEMORY_BROWSER: z.coerce.boolean().default(true),
});

type Env = z.infer<typeof envSchema>;

let env: Env;

try {
  env = envSchema.parse(process.env);
} catch (error) {
  if (error instanceof z.ZodError) {
    console.error('❌ Invalid environment variables:');
    error.errors.forEach((e) => {
      console.error(`  - ${e.path.join('.')}: ${e.message}`);
    });
  }
  throw error;
}

export const config = {
  app: {
    env: env.NODE_ENV,
    port: env.PORT,
    host: env.HOST,
    url: env.APP_URL,
    isDev: env.NODE_ENV === 'development',
    isProd: env.NODE_ENV === 'production',
  },
  database: {
    url: env.DATABASE_URL,
    poolSize: env.DATABASE_POOL_SIZE,
    ssl: env.DATABASE_SSL,
  },
  redis: {
    url: env.REDIS_URL,
    maxRetries: env.REDIS_MAX_RETRIES,
  },
  kafka: {
    brokers: env.KAFKA_BROKERS.split(','),
    clientId: env.KAFKA_CLIENT_ID,
    consumerGroup: env.KAFKA_CONSUMER_GROUP,
  },
  auth: {
    jwtSecret: env.JWT_SECRET,
    jwtRefreshSecret: env.JWT_REFRESH_SECRET,
    accessTtl: env.JWT_ACCESS_TTL,
    refreshTtl: env.JWT_REFRESH_TTL,
    issuer: env.JWT_ISSUER,
    audience: env.JWT_AUDIENCE,
    google: {
      clientId: env.GOOGLE_CLIENT_ID,
      clientSecret: env.GOOGLE_CLIENT_SECRET,
    },
    apple: {
      clientId: env.APPLE_CLIENT_ID,
      teamId: env.APPLE_TEAM_ID,
      keyId: env.APPLE_KEY_ID,
      privateKey: env.APPLE_PRIVATE_KEY,
    },
  },
  engines: {
    inferenceGateway: env.INFERENCE_GATEWAY_URL,
    identity: env.IDENTITY_ENGINE_URL,
    memory: env.MEMORY_ENGINE_URL,
    safety: env.SAFETY_ENGINE_URL,
    relationship: env.RELATIONSHIP_ENGINE_URL,
    emotion: env.EMOTION_ENGINE_URL,
    voice: env.VOICE_ENGINE_URL,
    proactive: env.PROACTIVE_ENGINE_URL,
    evaluation: env.EVALUATION_ENGINE_URL,
    companionRuntime: env.COMPANION_RUNTIME_URL,
  },
  stripe: {
    secretKey: env.STRIPE_SECRET_KEY,
    webhookSecret: env.STRIPE_WEBHOOK_SECRET,
    priceIdMonthly: env.STRIPE_PRICE_ID_MONTHLY,
    priceIdYearly: env.STRIPE_PRICE_ID_YEARLY,
  },
  email: {
    apiKey: env.SENDGRID_API_KEY,
    fromEmail: env.SENDGRID_FROM_EMAIL,
    fromName: env.SENDGRID_FROM_NAME,
  },
  push: {
    firebase: {
      projectId: env.FIREBASE_PROJECT_ID,
      clientEmail: env.FIREBASE_CLIENT_EMAIL,
      privateKey: env.FIREBASE_PRIVATE_KEY?.replace(/\\n/g, '\n'),
    },
    webPush: {
      vapidPublicKey: env.WEB_PUSH_VAPID_PUBLIC_KEY,
      vapidPrivateKey: env.WEB_PUSH_VAPID_PRIVATE_KEY,
      subject: env.WEB_PUSH_VAPID_SUBJECT,
    },
  },
  livekit: {
    apiKey: env.LIVEKIT_API_KEY,
    apiSecret: env.LIVEKIT_API_SECRET,
    wsUrl: env.LIVEKIT_WS_URL,
  },
  s3: {
    endpoint: env.S3_ENDPOINT,
    region: env.S3_REGION,
    accessKey: env.S3_ACCESS_KEY,
    secretKey: env.S3_SECRET_KEY,
    bucket: env.S3_BUCKET,
  },
  observability: {
    otelEndpoint: env.OTEL_EXPORTER_OTLP_ENDPOINT,
    serviceName: env.OTEL_SERVICE_NAME,
    logLevel: env.LOG_LEVEL,
    prometheusPort: env.PROMETHEUS_PORT,
  },
  rateLimit: {
    max: env.RATE_LIMIT_MAX,
    windowMs: env.RATE_LIMIT_WINDOW_MS,
  },
  cors: {
    origin: env.CORS_ORIGIN,
  },
  features: {
    enableVoice: env.ENABLE_VOICE,
    enableProactive: env.ENABLE_PROACTIVE,
    enableMemoryBrowser: env.ENABLE_MEMORY_BROWSER,
  },
} as const;

export type Config = typeof config;