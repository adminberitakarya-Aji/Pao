/** Kafka Client Configuration */

import { Kafka, Producer, Consumer, EachMessagePayload, logLevel } from 'kafkajs';
import { config } from './config.js';

// Create Kafka client
export const kafka = new Kafka({
  clientId: config.kafka.clientId,
  brokers: config.kafka.brokers,
  logLevel: logLevel.INFO,
  retry: {
    initialRetryTime: 100,
    retries: 8,
  },
});

// Create producer
export const producer: Producer = kafka.producer({
  allowAutoCreateTopics: true,
  transactionTimeout: 30000,
});

// Create consumer
export function createConsumer(groupId: string = config.kafka.consumerGroup): Consumer {
  return kafka.consumer({ groupId });
}

// Topics
export const topics = {
  // User events
  userCreated: 'pao.user.created',
  userUpdated: 'pao.user.updated',
  userDeleted: 'pao.user.deleted',
  userTierChanged: 'pao.user.tier_changed',

  // Session events
  sessionCreated: 'pao.session.created',
  sessionRevoked: 'pao.session.revoked',

  // Chat/Conversation events
  messageCreated: 'pao.message.created',
  conversationCreated: 'pao.conversation.created',
  conversationUpdated: 'pao.conversation.updated',

  // AI Engine events
  emotionAnalyzed: 'pao.emotion.analyzed',
  voiceProcessed: 'pao.voice.processed',
  proactiveTriggered: 'pao.proactive.triggered',
  evaluationCompleted: 'pao.evaluation.completed',

  // Notification events
  notificationCreated: 'pao.notification.created',
  pushNotificationSent: 'pao.push.sent',
  emailSent: 'pao.email.sent',

  // Billing events
  subscriptionCreated: 'pao.subscription.created',
  subscriptionUpdated: 'pao.subscription.updated',
  subscriptionCancelled: 'pao.subscription.cancelled',
  paymentSucceeded: 'pao.payment.succeeded',
  paymentFailed: 'pao.payment.failed',
} as const;

export type Topic = typeof topics[keyof typeof topics];

// Producer functions
export async function connectProducer(): Promise<void> {
  await producer.connect();
  console.log('✅ Kafka producer connected');
}

export async function disconnectProducer(): Promise<void> {
  await producer.disconnect();
  console.log('✅ Kafka producer disconnected');
}

export async function sendMessage<T extends Topic>(
  topic: T,
  key: string,
  value: Record<string, unknown>
): Promise<void> {
  await producer.send({
    topic,
    messages: [
      {
        key,
        value: JSON.stringify(value),
        headers: {
          'content-type': 'application/json',
          'timestamp': Date.now().toString(),
        },
      },
    ],
  });
}

// Consumer handler type
export type MessageHandler = (payload: EachMessagePayload) => Promise<void>;

// Run consumer with handlers
export async function runConsumer(
  consumer: Consumer,
  handlers: Map<Topic, MessageHandler>
): Promise<void> {
  await consumer.connect();
  console.log('✅ Kafka consumer connected');

  // Subscribe to all topics
  await consumer.subscribe({ topics: Object.values(topics), fromBeginning: false });

  await consumer.run({
    eachMessage: async (payload) => {
      const topic = payload.topic as Topic;
      const handler = handlers.get(topic);

      if (handler) {
        try {
          await handler(payload);
        } catch (error) {
          console.error(`Error processing message from ${topic}:`, error);
          // In production, send to dead letter queue
        }
      }
    },
  });
}

export async function disconnectConsumer(consumer: Consumer): Promise<void> {
  await consumer.disconnect();
  console.log('✅ Kafka consumer disconnected');
}

// Health check
export async function checkKafkaHealth(): Promise<boolean> {
  try {
    const admin = kafka.admin();
    await admin.connect();
    const metadata = await admin.fetchTopicMetadata({ topics: ['__consumer_offsets'] });
    await admin.disconnect();
    return metadata.topics.length > 0;
  } catch (error) {
    console.error('Kafka health check failed:', error);
    return false;
  }
}