/** Database Seeding Script */

import { config } from '../config.js';
import { db, pool } from '../database.js';
import { users, sessions } from '../models/index.js';
import { eq } from 'drizzle-orm';
import bcrypt from 'bcryptjs';
import { ulid } from 'ulid';

async function seed(): Promise<void> {
  console.log('🌱 Starting database seed...');

  try {
    // Check if users already exist
    const existingUsers = await db.select().from(users).limit(1);
    if (existingUsers.length > 0) {
      console.log('✅ Database already seeded, skipping...');
      return;
    }

    // Create demo users
    const demoUsers = [
      {
        email: 'demo@pao.ai',
        password: 'demo123456',
        fullName: 'Demo User',
        tier: 'pro' as const,
      },
      {
        email: 'admin@pao.ai',
        password: 'admin123456',
        fullName: 'Admin User',
        tier: 'enterprise' as const,
      },
      {
        email: 'free@pao.ai',
        password: 'free123456',
        fullName: 'Free User',
        tier: 'free' as const,
      },
    ];

    for (const userData of demoUsers) {
      const passwordHash = await bcrypt.hash(userData.password, 12);

      const [user] = await db.insert(users).values({
        email: userData.email,
        passwordHash,
        tier: userData.tier,
        settingsJson: {
          language: 'en',
          timezone: 'UTC',
          notifications: {
            email: true,
            push: true,
            marketing: false,
            proactive: true,
          },
          privacy: {
            analytics: true,
            crashReporting: true,
          },
          theme: 'system',
        },
      }).returning();

      console.log(`✅ Created user: ${user.email} (${user.tier})`);

      // Create a demo session
      const sessionId = ulid();
      const expiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000);

      await db.insert(sessions).values({
        id: sessionId,
        userId: user.id,
        deviceId: 'demo-device',
        deviceName: 'Demo Device',
        refreshTokenHash: 'demo-hash',
        userAgent: 'Demo Script',
        ipAddress: '127.0.0.1',
        expiresAt,
      });

      console.log(`✅ Created session for: ${user.email}`);
    }

    console.log('🎉 Database seed completed successfully!');
  } catch (error) {
    console.error('❌ Seed failed:', error);
    throw error;
  } finally {
    await pool.end();
  }
}

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  seed().catch(() => process.exit(1));
}

export { seed };