/** Shared Error Classes and Types */

import { Result, err, ok } from 'neverthrow';

// ============================================================================
// Base Error Classes
// ============================================================================

export class AppError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly statusCode: number = 500,
    public readonly details?: Record<string, unknown>,
    public readonly cause?: Error
  ) {
    super(message);
    this.name = 'AppError';
    Error.captureStackTrace(this, this.constructor);
  }

  toJSON() {
    return {
      code: this.code,
      message: this.message,
      statusCode: this.statusCode,
      details: this.details,
    };
  }
}

export class ValidationError extends AppError {
  constructor(message: string, public readonly fieldErrors?: Record<string, string[]>) {
    super('VALIDATION_ERROR', message, 400, { fieldErrors });
    this.name = 'ValidationError';
  }
}

export class AuthenticationError extends AppError {
  constructor(message: string = 'Authentication required') {
    super('UNAUTHENTICATED', message, 401);
    this.name = 'AuthenticationError';
  }
}

export class AuthorizationError extends AppError {
  constructor(message: string = 'Insufficient permissions') {
    super('FORBIDDEN', message, 403);
    this.name = 'AuthorizationError';
  }
}

export class NotFoundError extends AppError {
  constructor(resource: string, id?: string) {
    super('NOT_FOUND', `${resource}${id ? ` with id ${id}` : ''} not found`, 404);
    this.name = 'NotFoundError';
  }
}

export class ConflictError extends AppError {
  constructor(message: string) {
    super('CONFLICT', message, 409);
    this.name = 'ConflictError';
  }
}

export class RateLimitError extends AppError {
  constructor(message: string = 'Too many requests', public readonly retryAfter?: number) {
    super('RATE_LIMITED', message, 429, { retryAfter });
    this.name = 'RateLimitError';
  }
}

export class InternalError extends AppError {
  constructor(message: string = 'Internal server error', cause?: Error) {
    super('INTERNAL_ERROR', message, 500, undefined, cause);
    this.name = 'InternalError';
  }
}

export class ExternalServiceError extends AppError {
  constructor(
    public readonly service: string,
    message: string,
    public readonly statusCode: number = 502,
    public readonly cause?: Error
  ) {
    super('EXTERNAL_SERVICE_ERROR', `${service}: ${message}`, statusCode, { service }, cause);
    this.name = 'ExternalServiceError';
  }
}

export class TimeoutError extends AppError {
  constructor(operation: string, timeoutMs: number) {
    super('TIMEOUT', `${operation} timed out after ${timeoutMs}ms`, 504, { operation, timeoutMs });
    this.name = 'TimeoutError';
  }
}

// ============================================================================
// Error Codes
// ============================================================================

export const ErrorCodes = {
  // Auth
  INVALID_CREDENTIALS: 'INVALID_CREDENTIALS',
  TOKEN_EXPIRED: 'TOKEN_EXPIRED',
  TOKEN_INVALID: 'TOKEN_INVALID',
  REFRESH_TOKEN_REVOKED: 'REFRESH_TOKEN_REVOKED',
  ACCOUNT_LOCKED: 'ACCOUNT_LOCKED',
  ACCOUNT_DEACTIVATED: 'ACCOUNT_DEACTIVATED',
  EMAIL_ALREADY_EXISTS: 'EMAIL_ALREADY_EXISTS',
  OAUTH_ERROR: 'OAUTH_ERROR',

  // Validation
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  INVALID_INPUT: 'INVALID_INPUT',
  MISSING_REQUIRED_FIELD: 'MISSING_REQUIRED_FIELD',

  // Resources
  NOT_FOUND: 'NOT_FOUND',
  ALREADY_EXISTS: 'ALREADY_EXISTS',
  CONFLICT: 'CONFLICT',

  // Rate Limiting
  RATE_LIMITED: 'RATE_LIMITED',
  QUOTA_EXCEEDED: 'QUOTA_EXCEEDED',

  // External Services
  EXTERNAL_SERVICE_UNAVAILABLE: 'EXTERNAL_SERVICE_UNAVAILABLE',
  EXTERNAL_SERVICE_TIMEOUT: 'EXTERNAL_SERVICE_TIMEOUT',
  EXTERNAL_SERVICE_ERROR: 'EXTERNAL_SERVICE_ERROR',

  // AI Engines
  ENGINE_UNAVAILABLE: 'ENGINE_UNAVAILABLE',
  ENGINE_TIMEOUT: 'ENGINE_TIMEOUT',
  ENGINE_ERROR: 'ENGINE_ERROR',
  SAFETY_VIOLATION: 'SAFETY_VIOLATION',
  CONTENT_BLOCKED: 'CONTENT_BLOCKED',

  // Database
  DATABASE_ERROR: 'DATABASE_ERROR',
  DATABASE_CONNECTION_FAILED: 'DATABASE_CONNECTION_FAILED',
  MIGRATION_FAILED: 'MIGRATION_FAILED',

  // Internal
  INTERNAL_ERROR: 'INTERNAL_ERROR',
  CONFIGURATION_ERROR: 'CONFIGURATION_ERROR',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR',
} as const;

export type ErrorCode = (typeof ErrorCodes)[keyof typeof ErrorCodes];

// ============================================================================
// Result Helpers
// ============================================================================

export type AppResult<T, E extends AppError = AppError> = Result<T, E>;

export function success<T>(value: T): AppResult<T> {
  return ok(value);
}

export function failure<E extends AppError>(error: E): AppResult<never, E> {
  return err(error);
}

export function fromPromise<T>(
  promise: Promise<T>,
  errorMapper?: (error: unknown) => AppError
): Promise<AppResult<T>> {
  return promise
    .then((value) => ok(value))
    .catch((error) => err(errorMapper ? errorMapper(error) : new InternalError(String(error), error as Error)));
}

export function fromNullable<T>(value: T | null | undefined, error: AppError): AppResult<T> {
  return value != null ? ok(value) : err(error);
}

// ============================================================================
// Error Factory
// ============================================================================

export function createError(code: ErrorCode, message: string, details?: Record<string, unknown>): AppError {
  const statusCodeMap: Record<ErrorCode, number> = {
    INVALID_CREDENTIALS: 401,
    TOKEN_EXPIRED: 401,
    TOKEN_INVALID: 401,
    REFRESH_TOKEN_REVOKED: 401,
    ACCOUNT_LOCKED: 403,
    ACCOUNT_DEACTIVATED: 403,
    EMAIL_ALREADY_EXISTS: 409,
    OAUTH_ERROR: 400,
    VALIDATION_ERROR: 400,
    INVALID_INPUT: 400,
    MISSING_REQUIRED_FIELD: 400,
    NOT_FOUND: 404,
    ALREADY_EXISTS: 409,
    CONFLICT: 409,
    RATE_LIMITED: 429,
    QUOTA_EXCEEDED: 429,
    EXTERNAL_SERVICE_UNAVAILABLE: 503,
    EXTERNAL_SERVICE_TIMEOUT: 504,
    EXTERNAL_SERVICE_ERROR: 502,
    ENGINE_UNAVAILABLE: 503,
    ENGINE_TIMEOUT: 504,
    ENGINE_ERROR: 502,
    SAFETY_VIOLATION: 400,
    CONTENT_BLOCKED: 400,
    DATABASE_ERROR: 500,
    DATABASE_CONNECTION_FAILED: 503,
    MIGRATION_FAILED: 500,
    INTERNAL_ERROR: 500,
    CONFIGURATION_ERROR: 500,
    UNKNOWN_ERROR: 500,
  };

  return new AppError(code, message, statusCodeMap[code] ?? 500, details);
}

// ============================================================================
// Error Handler for Fastify
// ============================================================================

import { FastifyError, FastifyRequest, FastifyReply } from 'fastify';

export function errorHandler(error: FastifyError, request: FastifyRequest, reply: FastifyReply) {
  // Log error
  request.log.error({ err: error }, 'Request error');

  // Handle known AppErrors
  if (error instanceof AppError) {
    return reply.code(error.statusCode).send({
      success: false,
      error: error.toJSON(),
      meta: { requestId: request.id, timestamp: new Date().toISOString() },
    });
  }

  // Handle Zod validation errors
  if (error.name === 'ZodError' && 'errors' in error) {
    const zodError = error as { errors: Array<{ path: (string | number)[]; message: string }> };
    const fieldErrors: Record<string, string[]> = {};

    for (const issue of zodError.errors) {
      const path = issue.path.join('.');
      if (!fieldErrors[path]) fieldErrors[path] = [];
      fieldErrors[path].push(issue.message);
    }

    return reply.code(400).send({
      success: false,
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Invalid request data',
        details: { fieldErrors },
      },
      meta: { requestId: request.id, timestamp: new Date().toISOString() },
    });
  }

  // Handle Fastify validation errors
  if (error.validation) {
    return reply.code(400).send({
      success: false,
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Invalid request',
        details: { validation: error.validation },
      },
      meta: { requestId: request.id, timestamp: new Date().toISOString() },
    });
  }

  // Default internal error
  return reply.code(500).send({
    success: false,
    error: {
      code: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred',
    },
    meta: { requestId: request.id, timestamp: new Date().toISOString() },
  });
}

// ============================================================================
// Async Error Wrapper
// ============================================================================

export function asyncHandler<T extends (...args: unknown[]) => Promise<unknown>>(
  fn: T
): (...args: Parameters<T>) => Promise<void> {
  return async (...args: Parameters<T>) => {
    try {
      await fn(...args);
    } catch (error) {
      // Error will be caught by Fastify's error handler
      throw error;
    }
  };
}