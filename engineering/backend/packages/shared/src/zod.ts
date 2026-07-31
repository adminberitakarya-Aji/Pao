/** Shared Zod Schemas and Validation Helpers */

import { z } from 'zod';
import { ulid } from 'ulid';

// ============================================================================
// Base Types
// ============================================================================

export const ULIDSchema = z.string().length(26).regex(/^[0-9A-HJKMNP-TV-Z]{26}$/);
export type ULID = z.infer<typeof ULIDSchema>;

export const UUIDSchema = z.string().uuid();
export type UUID = z.infer<typeof UUIDSchema>;

export const EmailSchema = z.string().email().max(255);
export type Email = z.infer<typeof EmailSchema>;

export const TimestampSchema = z.string().datetime({ offset: true });
export type Timestamp = z.infer<typeof TimestampSchema>;

export const DateSchema = z.union([z.date(), z.string().datetime({ offset: true })]);
export type DateInput = z.infer<typeof DateSchema>;

// ============================================================================
// Pagination
// ============================================================================

export const PaginationParamsSchema = z.object({
  page: z.coerce.number().int().positive().default(1),
  limit: z.coerce.number().int().positive().max(100).default(20),
  sortBy: z.string().optional(),
  sortOrder: z.enum(['asc', 'desc']).default('desc'),
});

export type PaginationParams = z.infer<typeof PaginationParamsSchema>;

export const PaginatedResponseSchema = <T extends z.ZodTypeAny>(itemSchema: T) =>
  z.object({
    items: z.array(itemSchema),
    pagination: z.object({
      page: z.number().int().positive(),
      limit: z.number().int().positive(),
      total: z.number().int().nonnegative(),
      totalPages: z.number().int().nonnegative(),
      hasNext: z.boolean(),
      hasPrev: z.boolean(),
    }),
  });

export type PaginatedResponse<T> = {
  items: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
    hasNext: boolean;
    hasPrev: boolean;
  };
};

// ============================================================================
// Common Request/Response
// ============================================================================

export const ApiResponseSchema = <T extends z.ZodTypeAny>(dataSchema: T) =>
  z.object({
    success: z.boolean(),
    data: dataSchema.optional(),
    error: z
      .object({
        code: z.string(),
        message: z.string(),
        details: z.record(z.unknown()).optional(),
      })
      .optional(),
    meta: z
      .object({
        requestId: z.string().optional(),
        timestamp: TimestampSchema.optional(),
        version: z.string().optional(),
      })
      .optional(),
  });

export type ApiResponse<T> = {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  };
  meta?: {
    requestId?: string;
    timestamp?: string;
    version?: string;
  };
};

export const ErrorResponseSchema = z.object({
  success: z.literal(false),
  error: z.object({
    code: z.string(),
    message: z.string(),
    details: z.record(z.unknown()).optional(),
  }),
  meta: z
    .object({
      requestId: z.string().optional(),
      timestamp: TimestampSchema.optional(),
    })
    .optional(),
});

// ============================================================================
// User Schemas
// ============================================================================

export const UserTierSchema = z.enum(['free', 'pro', 'premium', 'enterprise']);
export type UserTier = z.infer<typeof UserTierSchema>;

export const UserSettingsSchema = z.object({
  language: z.string().default('en'),
  timezone: z.string().default('UTC'),
  notifications: z
    .object({
      email: z.boolean().default(true),
      push: z.boolean().default(true),
      marketing: z.boolean().default(false),
      proactive: z.boolean().default(true),
    })
    .default({}),
  privacy: z
    .object({
      analytics: z.boolean().default(true),
      crashReporting: z.boolean().default(true),
    })
    .default({}),
  theme: z.enum(['light', 'dark', 'system']).default('system'),
});

export type UserSettings = z.infer<typeof UserSettingsSchema>;

export const UserSchema = z.object({
  id: UUIDSchema,
  email: EmailSchema,
  tier: UserTierSchema.default('free'),
  isActive: z.boolean().default(true),
  settings: UserSettingsSchema.default({}),
  createdAt: TimestampSchema,
  updatedAt: TimestampSchema,
});

export type User = z.infer<typeof UserSchema>;

export const CreateUserSchema = z.object({
  email: EmailSchema,
  password: z.string().min(8).max(128).optional(),
  fullName: z.string().min(1).max(100).optional(),
  oauthProvider: z.enum(['google', 'apple']).optional(),
  oauthSub: z.string().optional(),
});

export type CreateUser = z.infer<typeof CreateUserSchema>;

export const UpdateUserSchema = z.object({
  email: EmailSchema.optional(),
  fullName: z.string().min(1).max(100).optional(),
  tier: UserTierSchema.optional(),
  isActive: z.boolean().optional(),
  settings: UserSettingsSchema.partial().optional(),
});

export type UpdateUser = z.infer<typeof UpdateUserSchema>;

// ============================================================================
// Session Schemas
// ============================================================================

export const SessionSchema = z.object({
  id: ULIDSchema,
  userId: UUIDSchema,
  deviceId: z.string().min(1).max(255),
  deviceName: z.string().max(255).optional(),
  refreshTokenHash: z.string(),
  userAgent: z.string().optional(),
  ipAddress: z.string().max(45).optional(),
  deviceInfo: z.record(z.unknown()).default({}),
  isRevoked: z.boolean().default(false),
  revokedAt: TimestampSchema.nullable().optional(),
  expiresAt: TimestampSchema,
  createdAt: TimestampSchema,
});

export type Session = z.infer<typeof SessionSchema>;

export const CreateSessionSchema = z.object({
  userId: UUIDSchema,
  deviceId: z.string().min(1).max(255),
  deviceName: z.string().max(255).optional(),
  refreshTokenHash: z.string(),
  userAgent: z.string().optional(),
  ipAddress: z.string().max(45).optional(),
  deviceInfo: z.record(z.unknown()).default({}),
  expiresAt: TimestampSchema,
});

export type CreateSession = z.infer<typeof CreateSessionSchema>;

// ============================================================================
// Auth Schemas
// ============================================================================

export const RegisterRequestSchema = z.object({
  email: EmailSchema,
  password: z.string().min(8).max(128),
  fullName: z.string().min(1).max(100).optional(),
});

export type RegisterRequest = z.infer<typeof RegisterRequestSchema>;

export const LoginRequestSchema = z.object({
  email: EmailSchema,
  password: z.string().min(1),
  deviceId: z.string().optional(),
  deviceName: z.string().optional(),
});

export type LoginRequest = z.infer<typeof LoginRequestSchema>;

export const RefreshTokenRequestSchema = z.object({
  refreshToken: z.string().min(1),
});

export type RefreshTokenRequest = z.infer<typeof RefreshTokenRequestSchema>;

export const AuthTokensSchema = z.object({
  accessToken: z.string(),
  refreshToken: z.string(),
  expiresIn: z.number().int().positive(),
  tokenType: z.literal('Bearer'),
});

export type AuthTokens = z.infer<typeof AuthTokensSchema>;

export const JWTPayloadSchema = z.object({
  sub: UUIDSchema,
  email: EmailSchema,
  tier: UserTierSchema,
  iat: z.number().int().positive(),
  exp: z.number().int().positive(),
  type: z.enum(['access', 'refresh']).optional(),
});

export type JWTPayload = z.infer<typeof JWTPayloadSchema>;

// ============================================================================
// Chat/Message Schemas
// ============================================================================

export const MessageRoleSchema = z.enum(['user', 'assistant', 'system', 'tool']);
export type MessageRole = z.infer<typeof MessageRoleSchema>;

export const MessageSchema = z.object({
  id: ULIDSchema,
  conversationId: ULIDSchema,
  role: MessageRoleSchema,
  content: z.string().min(1),
  metadata: z.record(z.unknown()).default({}),
  tokenCount: z.number().int().nonnegative().optional(),
  createdAt: TimestampSchema,
});

export type Message = z.infer<typeof MessageSchema>;

export const ConversationSchema = z.object({
  id: ULIDSchema,
  userId: UUIDSchema,
  title: z.string().max(255).optional(),
  metadata: z.record(z.unknown()).default({}),
  createdAt: TimestampSchema,
  updatedAt: TimestampSchema,
});

export type Conversation = z.infer<typeof ConversationSchema>;

export const ChatRequestSchema = z.object({
  message: z.string().min(1).max(10000),
  conversationId: ULIDSchema.optional(),
  context: z.record(z.unknown()).optional(),
  stream: z.boolean().default(false),
});

export type ChatRequest = z.infer<typeof ChatRequestSchema>;

export const ChatResponseSchema = z.object({
  message: z.string(),
  conversationId: ULIDSchema,
  messageId: ULIDSchema,
  metadata: z.record(z.unknown()).default({}),
});

export type ChatResponse = z.infer<typeof ChatResponseSchema>;

// ============================================================================
// AI Engine Schemas
// ============================================================================

export const EngineHealthSchema = z.object({
  status: z.enum(['healthy', 'degraded', 'unhealthy']),
  service: z.string(),
  version: z.string(),
  timestamp: TimestampSchema,
  checks: z
    .array(
      z.object({
        name: z.string(),
        status: z.enum(['pass', 'warn', 'fail']),
        details: z.record(z.unknown()).optional(),
      })
    )
    .optional(),
});

export type EngineHealth = z.infer<typeof EngineHealthSchema>;

export const SafetyCheckRequestSchema = z.object({
  content: z.string().min(1).max(10000),
  context: z.record(z.unknown()).optional(),
});

export type SafetyCheckRequest = z.infer<typeof SafetyCheckRequestSchema>;

export const SafetyCheckResponseSchema = z.object({
  safe: z.boolean(),
  categories: z.record(z.boolean()),
  reason: z.string().optional(),
  severity: z.enum(['low', 'medium', 'high', 'critical']).optional(),
});

export type SafetyCheckResponse = z.infer<typeof SafetyCheckResponseSchema>;

export const MemorySearchRequestSchema = z.object({
  userId: UUIDSchema,
  query: z.string().min(1).max(1000),
  limit: z.number().int().positive().max(50).default(10),
  threshold: z.number().min(0).max(1).default(0.7),
});

export type MemorySearchRequest = z.infer<typeof MemorySearchRequestSchema>;

export const MemorySearchResponseSchema = z.object({
  results: z.array(
    z.object({
      id: ULIDSchema,
      content: z.string(),
      score: z.number(),
      metadata: z.record(z.unknown()),
      createdAt: TimestampSchema,
    })
  ),
});

export type MemorySearchResponse = z.infer<typeof MemorySearchResponseSchema>;

// ============================================================================
// Validation Helpers
// ============================================================================

export function validateULID(value: string): ULID {
  return ULIDSchema.parse(value);
}

export function generateULID(): ULID {
  return ulid() as ULID;
}

export function validateUUID(value: string): UUID {
  return UUIDSchema.parse(value);
}

export function validateEmail(value: string): Email {
  return EmailSchema.parse(value);
}

export function createPaginationParams(params: Partial<PaginationParams>): PaginationParams {
  return PaginationParamsSchema.parse(params);
}

export function createPaginatedResponse<T>(
  items: T[],
  page: number,
  limit: number,
  total: number
): PaginatedResponse<T> {
  const totalPages = Math.ceil(total / limit);
  return {
    items,
    pagination: {
      page,
      limit,
      total,
      totalPages,
      hasNext: page < totalPages,
      hasPrev: page > 1,
    },
  };
}

// ============================================================================
// Type Guards
// ============================================================================

export function isApiSuccess<T>(response: ApiResponse<T>): response is ApiResponse<T> & { data: T } {
  return response.success === true && response.data !== undefined;
}

export function isApiError(response: ApiResponse<unknown>): response is ApiResponse<never> & { error: NonNullable<ApiResponse<never>['error']> } {
  return response.success === false && response.error !== undefined;
}