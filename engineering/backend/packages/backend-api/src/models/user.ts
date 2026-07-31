/** User Model - SQL Schema using Drizzle ORM */

import { pgTable, uuid, varchar, text, timestamp, boolean, jsonb, index, uniqueIndex } from 'drizzle-orm/pg-core';
import { createInsertSchema, createSelectSchema } from 'drizzle-zod';
import { z } from 'zod';

export const users = pgTable('users', {
  id: uuid('id').primaryKey().defaultRandom(),
  email: varchar('email', { length: 255 }).notNull(),
  passwordHash: varchar('password_hash', { length: 255 }),
  oauthSub: varchar('oauth_sub', { length: 255 }),
  oauthProvider: varchar('oauth_provider', { length: 50 }),
  isActive: boolean('is_active').default(true).notNull(),
  tier: varchar('tier', { length: 50 }).default('free').notNull(),
  settingsJson: jsonb('settings_json').default({}).notNull(),
  createdAt: timestamp('created_at', { withTimezone: true }).defaultNow().notNull(),
  updatedAt: timestamp('updated_at', { withTimezone: true }).defaultNow().notNull(),
}, (table) => ({
  emailIdx: uniqueIndex('users_email_idx').on(table.email),
  oauthIdx: uniqueIndex('users_oauth_idx').on(table.oauthProvider, table.oauthSub),
  tierIdx: index('users_tier_idx').on(table.tier),
  activeIdx: index('users_active_idx').on(table.isActive),
}));

export const insertUserSchema = createInsertSchema(users);
export const selectUserSchema = createSelectSchema(users);

export type User = z.infer<typeof selectUserSchema>;
export type NewUser = z.infer<typeof insertUserSchema>;

// User settings schema
export const userSettingsSchema = z.object({
  language: z.string().default('en'),
  timezone: z.string().default('UTC'),
  notifications: z.object({
    email: z.boolean().default(true),
    push: z.boolean().default(true),
    marketing: z.boolean().default(false),
    proactive: z.boolean().default(true),
  }).default({}),
  privacy: z.object({
    analytics: z.boolean().default(true),
    crashReporting: z.boolean().default(true),
  }).default({}),
  theme: z.enum(['light', 'dark', 'system']).default('system'),
});

export type UserSettings = z.infer<typeof userSettingsSchema>;