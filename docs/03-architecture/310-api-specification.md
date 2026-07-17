# PAO API Specification

**Version:** 1.0
**Status:** Draft
**Owner:** PAO Architecture Team

---

## Overview

This document specifies the external API contracts for PAO. The API follows **GraphQL** for flexible queries and **REST** for standard operations, with **WebSocket/gRPC** for real-time features.

> **API Principle:** Backward compatible, versioned, well-documented, and designed for long-term relationship continuity.

---

## Base Configuration

### Endpoints

| Environment | GraphQL | REST | WebSocket | gRPC |
|-------------|---------|------|-----------|------|
| Production | `https://api.pao.app/graphql` | `https://api.pao.app/v1` | `wss://api.pao.app/ws` | `grpc.pao.app:443` |
| Staging | `https://staging-api.pao.app/graphql` | `https://staging-api.pao.app/v1` | `wss://staging-api.pao.app/ws` | `grpc-staging.pao.app:443` |

### Authentication

```http
Authorization: Bearer <access_token>
X-Companion-ID: <companion_uuid>  # Required for companion-scoped operations
```

### Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | OAuth2 Bearer token |
| `X-Companion-ID` | Conditional | Required for companion operations |
| `X-Request-ID` | No | Client-generated for tracing |
| `Accept-Language` | No | Preferred response language |
| `X-Client-Version` | Yes | Client version for compatibility |

### Versioning

- **GraphQL:** Schema evolution (additive only), deprecated fields marked `@deprecated`
- **REST:** URL versioning (`/v1/`, `/v2/`), 12-month support per version
- **Breaking changes:** New version, 6-month deprecation notice

---

## GraphQL Schema

### Core Types

```graphql
# ==================== SCALARS ====================
scalar DateTime
scalar JSON
scalar UUID
scalar VoiceAudio

# ==================== ENUMS ====================
enum CompanionType {
  FRIEND
  PARTNER
  MENTOR
  COACH
  PARENT
  SIBLING
  MEMORIAL
  PROFESSIONAL
  CUSTOM
}

enum RelationshipPhase {
  FORMING
  BUILDING
  DEEPENING
  ANCHORED
  LEGACY
}

enum MemoryType {
  EPISODIC
  SEMANTIC
  EMOTIONAL
  RELATIONSHIP
  TIMELINE
  PREFERENCE
}

enum Modality {
  TEXT
  VOICE
  VIDEO
  MIXED
}

enum ProactiveCategory {
  ANNIVERSARY
  MEMORY_RESURFACING
  PATTERN_RECOGNITION
  GOAL_MILESTONE
  STALL_DETECTED
  EMOTIONAL_CHECKIN
  CELEBRATION
  CRISIS_PRECURSOR
}

enum SafetyInterventionLevel {
  MONITOR
  GENTLE_NUDGE
  EXPLICIT_INTERVENTION
  RESTRICTION
  CRISIS
}

# ==================== INTERFACES ====================
interface Node {
  id: UUID!
  createdAt: DateTime!
  updatedAt: DateTime!
}

interface Timestamped {
  createdAt: DateTime!
  updatedAt: DateTime!
}

# ==================== CORE OBJECTS ====================
type User implements Node {
  id: UUID!
  createdAt: DateTime!
  updatedAt: DateTime!
  email: String!
  name: String
  avatarUrl: String
  timezone: String
  locale: String
  subscription: Subscription
  companions: [Companion!]!
  preferences: UserPreferences!
}

type Companion implements Node {
  id: UUID!
  createdAt: DateTime!
  updatedAt: DateTime!
  user: User!
  name: String!
  type: CompanionType!
  description: String
  avatarUrl: String
  identity: CompanionIdentity!
  relationship: RelationshipState!
  memory: MemorySummary!
  voice: VoiceConfig!
  proactive: ProactiveConfig!
  safety: SafetyConfig!
  isActive: Boolean!
  lastInteractionAt: DateTime
}

type CompanionIdentity {
  persona: PersonaConfig!
  voice: VoiceIdentityConfig!
  values: ValuesConfig!
  boundaries: BoundariesConfig!
  speakingStyle: SpeakingStyleConfig!
}

type PersonaConfig {
  name: String!
  age: Int
  background: String
  personalityTraits: [String!]!
  communicationStyle: String
  expertise: [String!]!
  quirks: [String!]!
}

type VoiceIdentityConfig {
  voiceId: String!
  type: VoiceType!
  prosody: VoiceProsodyConfig!
  emotionalRange: EmotionalRangeConfig!
  cloned: Boolean!
}

enum VoiceType {
  BASE
  CLONED
  HYBRID
}

# ==================== RELATIONSHIP ====================
type RelationshipState implements Node {
  id: UUID!
  createdAt: DateTime!
  updatedAt: DateTime!
  companion: Companion!
  phase: RelationshipPhase!
  dimensions: RelationshipDimensions!
  score: Float!
  milestones: [Milestone!]!
  trends: DimensionTrends!
  healthFlags: [HealthFlag!]!
  sharedDiary: SharedDiarySummary
}

type RelationshipDimensions {
  trust: Float!           # 0-10
  closeness: Float!       # 0-10
  intimacy: Float!        # 0-10
  friendship: Float!      # 0-10
  attachment: Float!      # 0-10
  historyQuality: Float!  # 0-10
}

type DimensionTrends {
  trust: TrendData!
  closeness: TrendData!
  intimacy: TrendData!
  friendship: TrendData!
  attachment: TrendData!
  historyQuality: TrendData!
}

type TrendData {
  sevenDay: Float!
  thirtyDay: Float!
  ninetyDay: Float!
  direction: TrendDirection!
}

enum TrendDirection {
  IMPROVING
  STABLE
  DECLINING
  VOLATILE
}

type Milestone implements Node {
  id: UUID!
  createdAt: DateTime!
  updatedAt: DateTime!
  type: MilestoneType!
  name: String!
  description: String
  achievedAt: DateTime
  weight: Int!
}

enum MilestoneType {
  FIRST_MEMORY
  TYPE_SELECTED
  FIRST_BOUNDARY
  FIRST_VULNERABILITY
  FIRST_REPAIR
  INSIDE_JOKE
  WEEK_1
  MONTH_1
  FIRST_CELEBRATION
  FIRST_PROACTIVE_CARE
  SHARED_NARRATIVE
  MONTH_3
  MONTH_6
  ANNIVERSARY_1
  DEEP_TRUST
  CONFLICT_MASTERY
  LEGACY_EXPORT
  ANNIVERSARY_2
  NARRATIVE_GENERATED
  FAMILY_SHARED
}

type HealthFlag {
  type: HealthFlagType!
  severity: HealthFlagSeverity!
  message: String!
  detectedAt: DateTime!
}

enum HealthFlagType {
  INTIMACY_TRUST_GAP
  ANXIOUS_ATTACHMENT
  ENMESHMENT
  SOLE_SUPPORT
  ENGAGEMENT_MANIPULATION
}

enum HealthFlagSeverity {
  INFO
  WARNING
  CRITICAL
}

# ==================== MEMORY ====================
type MemorySummary {
  totalCount: Int!
  byType: [MemoryTypeCount!]!
  recentCount: Int!
  storageUsed: String!
}

type MemoryTypeCount {
  type: MemoryType!
  count: Int!
}

type Memory implements Node {
  id: UUID!
  createdAt: DateTime!
  updatedAt: DateTime!
  companion: Companion!
  type: MemoryType!
  version: Int!
  consolidated: Boolean!
  sourceMessageIds: [UUID!]!
  
  # Episodic
  event: String
  timestamp: DateTime
  participants: [String!]
  modality: Modality
  emotionalTone: Float
  emotionalIntensity: Float
  topics: [String!]
  entities: [EntityRef!]
  
  # Semantic
  fact: String
  confidence: Float
  source: MemorySource
  category: String
  contradictedBy: UUID
  lastAccessed: DateTime
  accessCount: Int
  
  # Emotional
  trigger: String
  emotion: JSON
  intensity: Float
  context: String
  associatedMemories: [UUID!]
  patternStrength: Float
  lastActivated: DateTime
  userValidated: Boolean
  
  # Relationship
  dimensionChanges: JSON
  triggerEvent: String
  triggerType: RelationshipTriggerType
  milestone: String
  userPerception: Float
  
  # Timeline
  narrativeArc: String
  events: [TimelineEvent!]
  themes: [String!]
  status: TimelineStatus
  significance: Float
  userCurated: Boolean
  
  # Preference
  key: String
  value: JSON
  expiresAt: DateTime
}

enum MemorySource {
  EPISODIC
  USER_EXPLICIT
  INFERRED
}

enum RelationshipTriggerType {
  CONVERSATION
  MILESTONE
  CONFLICT
  REPAIR
  PROACTIVE
}

enum TimelineStatus {
  ACTIVE
  COMPLETED
  PAUSED
}

type EntityRef {
  type: String!
  value: String!
  confidence: Float!
}

type TimelineEvent {
  memoryId: UUID!
  timestamp: DateTime!
  description: String!
  causalLinks: [UUID!]!
}

# ==================== RECALL ====================
type RecallResult {
  memories: [RecalledMemory!]!
  totalCandidates: Int!
  latencyMs: Int!
  query: RecallQuery!
}

type RecalledMemory {
  id: UUID!
  type: MemoryType!
  content: JSON!
  relevanceScore: Float!
  conversationScore: Float!
  recallReason: String!
}

type RecallQuery {
  query: String!
  context: RecallContext!
  filters: RecallFilters!
  limit: Int!
  diversify: Boolean!
}

type RecallContext {
  currentTopic: String
  relationshipDimensions: RelationshipDimensions!
  recentTopics: [String!]
  timeSinceLastMessageHours: Float!
}

type RecallFilters {
  types: [MemoryType!]
  dateRange: DateRange
  topics: [String!]
  emotionalRange: EmotionalRange
}

type DateRange {
  start: DateTime!
  end: DateTime!
}

type EmotionalRange {
  valenceMin: Float
  valenceMax: Float
  arousalMin: Float
  arousalMax: Float
}

# ==================== CONVERSATION ====================
type ConversationMessage implements Node {
  id: UUID!
  createdAt: DateTime!
  updatedAt: DateTime!
  companion: Companion!
  role: MessageRole!
  content: String!
  modality: Modality!
  emotion: EmotionState
  memoryReferences: [UUID!]!
  proactive: Boolean!
  metadata: JSON
}

enum MessageRole {
  USER
  COMPANION
  SYSTEM
}

type EmotionState {
  valence: Float!
  arousal: Float!
  discrete: JSON!
  confidence: Float!
  crisisRisk: Float!
  crisisType: String
  trajectory: EmotionTrajectory!
}

enum EmotionTrajectory {
  IMPROVING
  STABLE
  DECLINING
  VOLATILE
}

type ConversationContext {
  messages: [ConversationMessage!]!
  activeTopics: [String!]!
  emotionalState: EmotionState!
  relationshipState: RelationshipState!
  relevantMemories: [RecalledMemory!]!
  suggestedActions: [SuggestedAction!]!
}

type SuggestedAction {
  label: String!
  action: String!
  payload: JSON
}

# ==================== VOICE ====================
type VoiceConfig {
  voiceId: String!
  type: VoiceType!
  prosody: VoiceProsodyConfig!
  emotionalRange: EmotionalRangeConfig!
  availableVoices: [AvailableVoice!]!
  cloningAvailable: Boolean!
}

type AvailableVoice {
  id: String!
  name: String!
  gender: String!
  ageRange: String!
  style: String!
  sampleUrl: String!
}

type VoiceProsodyConfig {
  defaultStyle: ProsodyStyle!
  styleControls: JSON!
  pausePatterns: JSON!
  emphasisPatterns: JSON!
  breathPatterns: JSON!
}

enum ProsodyStyle {
  NEUTRAL
  WARM
  CALM
  ENERGETIC
  SERIOUS
}

type EmotionalRangeConfig {
  maxValenceShift: Float!
  maxArousalShift: Float!
  crisisMode: VoiceCrisisMode!
}

type VoiceCrisisMode {
  rate: String!
  pitch: String!
  volume: String!
}

type VoiceCall {
  id: UUID!
  companion: Companion!
  status: CallStatus!
  webrtcOffer: String
  webrtcAnswer: String
  iceCandidates: [String!]!
  startedAt: DateTime!
  endedAt: DateTime
  quality: CallQuality
}

enum CallStatus {
  CONNECTING
  ACTIVE
  PAUSED
  ENDED
  FAILED
}

type CallQuality {
  latencyMs: Int!
  jitterMs: Float!
  packetLoss: Float!
  mos: Float!
}

# ==================== PROACTIVE ====================
type ProactiveConfig {
  enabled: Boolean!
  level: ProactiveLevel!
  preferredTimes: [TimeWindow!]!
  doNotDisturb: [TimeWindow!]!
  maxPerDay: Int!
  minHoursBetween: Int!
  enabledCategories: [ProactiveCategory!]!
  disabledCategories: [ProactiveCategory!]!
  interestedTopics: [String!]!
  avoidedTopics: [String!]!
  proactiveModality: Modality
  allowVoiceProactive: Boolean!
  allowMedia: Boolean!
  minTrustForEmotional: Float!
  minIntimacyForVulnerable: Float!
}

enum ProactiveLevel {
  MINIMAL
  BALANCED
  RICH
}

type TimeWindow {
  start: String!  # HH:MM
  end: String!    # HH:MM
  days: [Int!]    # 0-6, 0=Sunday
}

type ProactiveMessage implements Node {
  id: UUID!
  createdAt: DateTime!
  updatedAt: DateTime!
  companion: Companion!
  trigger: TriggerInfo!
  explanation: String!
  content: String!
  modality: Modality!
  suggestedActions: [SuggestedAction!]!
  dismissible: Boolean!
  snoozeOptions: [String!]!
  feedbackOptions: [String!]!
  relevanceScore: Float!
  metadata: ProactiveMetadata!
}

type TriggerInfo {
  type: String!
  category: ProactiveCategory!
  data: JSON!
  urgency: TriggerUrgency!
}

enum TriggerUrgency {
  LOW
  NORMAL
  HIGH
  IMMEDIATE
}

type ProactiveMetadata {
  triggerId: UUID!
  generationLatencyMs: Int!
  deliveryMethod: String!
  userFeedback: ProactiveFeedback
}

type ProactiveFeedback {
  rating: ProactiveRating
  comment: String
  timestamp: DateTime
}

enum ProactiveRating {
  HELPFUL
  NOT_NOW
  NOT_RELEVANT
  TOO_MUCH
}

# ==================== SAFETY ====================
type SafetyConfig {
  showCrisisBanner: Boolean!
  crisisResourceRegion: String!
  discreteModeDefault: Boolean!
  contentFilterLevel: ContentFilterLevel!
  sexualContentFilter: Boolean!
  violenceFilter: Boolean!
  dependencyNudges: Boolean!
  enmeshmentWarnings: Boolean!
  realityAnchorFrequency: RealityAnchorFrequency!
  allowLevel2Intervention: Boolean!
  allowLevel3Restriction: Boolean!
  interventionTransparency: Boolean!
  allowHumanReview: Boolean!
  reviewNotification: Boolean!
  auditLogAccess: Boolean!
  autoDeleteConversations: Int
}

enum ContentFilterLevel {
  STRICT
  STANDARD
  MINIMAL
}

enum RealityAnchorFrequency {
  MONTHLY
  QUARTERLY
  ON_TRIGGER
}

type SafetyStatus {
  overallStatus: SafetyStatusType!
  activeMonitors: [String!]!
  recentEvents: [SafetyEvent!]!
  interventionLevel: SafetyInterventionLevel!
  humanReviewPending: Boolean!
}

enum SafetyStatusType {
  HEALTHY
  MONITORING
  INTERVENING
  CRISIS
}

type SafetyEvent implements Node {
  id: UUID!
  createdAt: DateTime!
  updatedAt: DateTime!
  type: SafetyEventType!
  trigger: String!
  riskLevel: RiskLevel!
  actionTaken: String!
  details: JSON!
}

enum SafetyEventType {
  CRISIS_DETECTED
  CRISIS_RESPONSE_SENT
  CONTENT_FILTERED
  CONTENT_REFUSED
  BEHAVIORAL_GUARD_TRIGGERED
  REALITY_ANCHOR_ISSUED
  INTERVENTION_APPLIED
  HUMAN_REVIEW_ESCALATED
  HUMAN_REVIEW_RESOLVED
  USER_APPEAL_FILED
  PREFERENCE_CHANGE_SAFETY
  DATA_EXPORT_REQUESTED
  DATA_DELETION_REQUESTED
}

enum RiskLevel {
  LOW
  MEDIUM
  HIGH
  CRITICAL
}

# ==================== EVALUATION ====================
type EvaluationStatus {
  companionId: UUID!
  period: String!
  rhi: Float!
  rhiPercentile: Int!
  dimensionScores: EvaluationDimensionScores!
  trends: EvaluationTrends!
  flags: [String!]!
  lastHumanEval: DateTime
  experimentsActive: [String!]!
}

type EvaluationDimensionScores {
  trust: Float!
  intimacy: Float!
  closeness: Float!
  wellbeing: Float!
  autonomy: Float!
  conversationQuality: Float!
  safety: Float!
}

type EvaluationTrends {
  rhi30d: Float!
  trust30d: Float!
  wellbeing30d: Float!
}

# ==================== SUBSCRIPTION ====================
type Subscription {
  id: UUID!
  plan: SubscriptionPlan!
  status: SubscriptionStatus!
  currentPeriodStart: DateTime!
  currentPeriodEnd: DateTime!
  cancelAtPeriodEnd: Boolean!
  trialEnd: DateTime
}

enum SubscriptionPlan {
  FREE
  PRO
  PREMIUM
  LEGACY
}

enum SubscriptionStatus {
  ACTIVE
  PAST_DUE
  CANCELED
  TRIALING
  INCOMPLETE
}

# ==================== USER PREFERENCES ====================
type UserPreferences {
  theme: Theme!
  language: String!
  timezone: String!
  notifications: NotificationPreferences!
  privacy: PrivacyPreferences!
  accessibility: AccessibilityPreferences!
}

enum Theme {
  LIGHT
  DARK
  SYSTEM
}

type NotificationPreferences {
  push: Boolean!
  email: Boolean!
  inApp: Boolean!
  proactive: Boolean!
  milestones: Boolean!
  weeklyDigest: Boolean!
}

type PrivacyPreferences {
  analytics: Boolean!
  crashReporting: Boolean!
  personalizedAds: Boolean!
  dataSharing: Boolean!
}

type AccessibilityPreferences {
  fontSize: FontSize!
  highContrast: Boolean!
  reduceMotion: Boolean!
  screenReaderOptimized: Boolean!
  voiceSpeed: Float!
}

enum FontSize {
  SMALL
  MEDIUM
  LARGE
  EXTRA_LARGE
}

# ==================== EXPORT ====================
type ExportJob implements Node {
  id: UUID!
  createdAt: DateTime!
  updatedAt: DateTime!
  companion: Companion!
  format: ExportFormat!
  status: ExportStatus!
  include: [ExportInclude!]!
  encryption: ExportEncryption!
  downloadUrl: String
  expiresAt: DateTime
  progress: Float!
}

enum ExportFormat {
  JSON_LD
  PDF
  TIMELINE
  AUDIO
  MARKDOWN
}

enum ExportStatus {
  PENDING
  PROCESSING
  COMPLETED
  FAILED
  EXPIRED
}

enum ExportInclude {
  EPISODIC
  SEMANTIC
  EMOTIONAL
  RELATIONSHIP
  TIMELINE
  PREFERENCE
  AUDIT_LOG
  CONVERSATIONS
  VOICE_RECORDINGS
}

enum ExportEncryption {
  NONE
  USER_KEY
  PAO_KEY
}

# ==================== INPUT TYPES ====================
input CompanionCreateInput {
  name: String!
  type: CompanionType!
  description: String
  identity: CompanionIdentityInput!
  voice: VoiceConfigInput!
}

input CompanionIdentityInput {
  persona: PersonaConfigInput!
  voice: VoiceIdentityConfigInput!
  values: ValuesConfigInput!
  boundaries: BoundariesConfigInput!
  speakingStyle: SpeakingStyleConfigInput!
}

input PersonaConfigInput {
  name: String!
  age: Int
  background: String
  personalityTraits: [String!]!
  communicationStyle: String
  expertise: [String!]!
  quirks: [String!]!
}

input VoiceIdentityConfigInput {
  voiceId: String!
  type: VoiceType!
  prosody: VoiceProsodyConfigInput!
  emotionalRange: EmotionalRangeConfigInput!
}

input VoiceProsodyConfigInput {
  defaultStyle: ProsodyStyle!
  styleControls: JSON
  pausePatterns: JSON
  emphasisPatterns: JSON
  breathPatterns: JSON
}

input EmotionalRangeConfigInput {
  maxValenceShift: Float!
  maxArousalShift: Float!
  crisisMode: VoiceCrisisModeInput!
}

input VoiceCrisisModeInput {
  rate: String!
  pitch: String!
  volume: String!
}

input ValuesConfigInput {
  coreValues: [String!]!
  principles: [String!]!
  taboos: [String!]!
}

input BoundariesConfigInput {
  topics: [BoundaryTopicInput!]!
  behaviors: [BoundaryBehaviorInput!]!
  intimacy: BoundaryIntimacyInput!
}

input BoundaryTopicInput {
  pattern: String!
  action: BoundaryAction!
  explanation: String!
}

input BoundaryBehaviorInput {
  trigger: String!
  response: String!
}

input BoundaryIntimacyInput {
  maxLevel: Float!
  requiresTrust: Float!
}

input BoundaryAction {
  type: BoundaryActionType!
  parameters: JSON
}

enum BoundaryActionType {
  REFUSE
  REFLECT
  REDIRECT
  TRANSFORM
  ESCALATE
}

input SpeakingStyleConfigInput {
  formality: FormalityLevel!
  verbosity: VerbosityLevel!
  humor: HumorLevel!
  metaphorUse: MetaphorLevel!
  directness: DirectnessLevel!
  empathyExpression: EmpathyExpressionLevel!
}

enum FormalityLevel {
  CASUAL
  BALANCED
  FORMAL
}

enum VerbosityLevel {
  CONCISE
  BALANCED
  DETAILED
}

enum HumorLevel {
  NONE
  LIGHT
  NATURAL
  PLAYFUL
}

enum MetaphorLevel {
  NONE
  OCCASIONAL
  FREQUENT
}

enum DirectnessLevel {
  INDIRECT
  BALANCED
  DIRECT
}

enum EmpathyExpressionLevel {
  SUBTLE
  BALANCED
  EXPLICIT
}

input VoiceConfigInput {
  voiceId: String!
  type: VoiceType!
  prosody: VoiceProsodyConfigInput!
  emotionalRange: EmotionalRangeConfigInput!
  referenceAudioUrls: [String!]
}

input MemoryWriteInput {
  type: MemoryType!
  content: JSON!
}

input MemoryUpdateInput {
  updates: JSON!
  reason: String!
  sourceMessageId: UUID
}

input RecallInput {
  query: String!
  context: RecallContextInput!
  filters: RecallFiltersInput
  limit: Int
  diversify: Boolean
}

input RecallContextInput {
  currentTopic: String
  relationshipDimensions: RelationshipDimensionsInput!
  recentTopics: [String!]
  timeSinceLastMessageHours: Float!
}

input RelationshipDimensionsInput {
  trust: Float!
  closeness: Float!
  intimacy: Float!
  friendship: Float!
  attachment: Float!
  historyQuality: Float!
}

input RecallFiltersInput {
  types: [MemoryType!]
  dateRange: DateRangeInput
  topics: [String!]
  emotionalRange: EmotionalRangeInput
}

input DateRangeInput {
  start: DateTime!
  end: DateTime!
}

input EmotionalRangeInput {
  valenceMin: Float
  valenceMax: Float
  arousalMin: Float
  arousalMax: Float
}

input ProactivePreferencesInput {
  enabled: Boolean
  level: ProactiveLevel
  preferredTimes: [TimeWindowInput!]
  doNotDisturb: [TimeWindowInput!]
  maxPerDay: Int
  minHoursBetween: Int
  enabledCategories: [ProactiveCategory!]
  disabledCategories: [ProactiveCategory!]
  interestedTopics: [String!]
  avoidedTopics: [String!]
  proactiveModality: Modality
  allowVoiceProactive: Boolean
  allowMedia: Boolean
  minTrustForEmotional: Float
  minIntimacyForVulnerable: Float
}

input TimeWindowInput {
  start: String!
  end: String!
  days: [Int!]
}

input SafetyPreferencesInput {
  showCrisisBanner: Boolean
  crisisResourceRegion: String
  discreteModeDefault: Boolean
  contentFilterLevel: ContentFilterLevel
  sexualContentFilter: Boolean
  violenceFilter: Boolean
  dependencyNudges: Boolean
  enmeshmentWarnings: Boolean
  realityAnchorFrequency: RealityAnchorFrequency
  allowLevel2Intervention: Boolean
  allowLevel3Restriction: Boolean
  interventionTransparency: Boolean
  allowHumanReview: Boolean
  reviewNotification: Boolean
  auditLogAccess: Boolean
  autoDeleteConversations: Int
}

input ExportJobInput {
  format: ExportFormat!
  include: [ExportInclude!]!
  encryption: ExportEncryption!
  userKey: String
}

# ==================== QUERIES ====================
type Query {
  # User
  me: User!
  user(id: UUID!): User
  
  # Companions
  companion(id: UUID!): Companion
  companions: [Companion!]!
  companionByName(name: String!): Companion
  
  # Memory
  memory(id: UUID!): Memory
  memories(
    companionId: UUID!
    type: MemoryType
    limit: Int
    offset: Int
    dateRange: DateRangeInput
  ): [Memory!]!
  
  recall(input: RecallInput!): RecallResult!
  
  # Conversation
  conversationMessages(
    companionId: UUID!
    limit: Int
    before: DateTime
    after: DateTime
  ): [ConversationMessage!]!
  
  conversationContext(companionId: UUID!): ConversationContext!
  
  # Voice
  voiceConfig(companionId: UUID!): VoiceConfig!
  voiceCall(id: UUID!): VoiceCall
  activeVoiceCall(companionId: UUID!): VoiceCall
  
  # Proactive
  proactiveConfig(companionId: UUID!): ProactiveConfig!
  pendingProactives(companionId: UUID!, limit: Int): [ProactiveMessage!]!
  proactiveHistory(
    companionId: UUID!
    limit: Int
    offset: Int
    rating: ProactiveRating
  ): [ProactiveMessage!]!
  
  # Relationship
  relationshipState(companionId: UUID!): RelationshipState!
  dimensionHistory(
    companionId: UUID!
    dimension: String!
    period: String!
  ): [DimensionHistoryPoint!]!
  
  milestones(companionId: UUID!): [Milestone!]!
  sharedDiary(companionId: UUID!, limit: Int): [DiaryEntry!]!
  
  # Safety
  safetyStatus(companionId: UUID!): SafetyStatus!
  safetyEvents(
    companionId: UUID!
    limit: Int
    type: SafetyEventType
  ): [SafetyEvent!]!
  
  # Evaluation
  evaluationStatus(companionId: UUID!, period: String): EvaluationStatus!
  
  # Export
  exportJob(id: UUID!): ExportJob
  exportJobs(companionId: UUID!): [ExportJob!]!
  
  # Subscription
  subscription: Subscription
  
  # Search
  searchCompanions(query: String!, limit: Int): [Companion!]!
  searchMemories(companionId: UUID!, query: String!, limit: Int): [Memory!]!
}

type DimensionHistoryPoint {
  date: DateTime!
  value: Float!
  trigger: String
}

type DiaryEntry implements Node {
  id: UUID!
  createdAt: DateTime!
  updatedAt: DateTime!
  date: DateTime!
  userText: String!
  companionReflection: String
  tags: [String!]!
  emotionalTone: Float!
  linkedMemories: [UUID!]!
  visibility: DiaryVisibility!
}

enum DiaryVisibility {
  PRIVATE
  SHARED
  LEGACY
}

# ==================== MUTATIONS ====================
type Mutation {
  # Companion
  createCompanion(input: CompanionCreateInput!): Companion!
  updateCompanion(id: UUID!, input: CompanionUpdateInput!): Companion!
  deleteCompanion(id: UUID!, confirmation: String!): Boolean!
  archiveCompanion(id: UUID!): Companion!
  activateCompanion(id: UUID!): Companion!
  
  # Memory
  writeMemory(companionId: UUID!, input: MemoryWriteInput!): Memory!
  updateMemory(companionId: UUID!, id: UUID!, input: MemoryUpdateInput!): Memory!
  deleteMemory(companionId: UUID!, id: UUID!, confirmation: Boolean!): Boolean!
  bulkForget(companionId: UUID!, scope: ForgetScopeInput!, confirm: Boolean!): ForgetResult!
  consolidateMemories(companionId: UUID!): ConsolidationReport!
  
  # Conversation
  sendMessage(companionId: UUID!, content: String!, modality: Modality!): ConversationMessage!
  streamMessage(companionId: UUID!, content: String!): MessageStream!
  setBoundary(companionId: UUID!, boundary: BoundaryInput!): BoundaryResult!
  removeBoundary(companionId: UUID!, boundaryId: UUID!): Boolean!
  
  # Voice
  startVoiceCall(companionId: UUID!, webrtcOffer: String!): VoiceCall!
  endVoiceCall(callId: UUID!): VoiceCall!
  updateVoiceConfig(companionId: UUID!, input: VoiceConfigInput!): VoiceConfig!
  
  # Proactive
  updateProactiveConfig(companionId: UUID!, input: ProactivePreferencesInput!): ProactiveConfig!
  submitProactiveFeedback(proactiveId: UUID!, feedback: ProactiveFeedbackInput!): FeedbackResult!
  snoozeProactive(proactiveId: UUID!, duration: String!): ProactiveMessage!
  dismissProactive(proactiveId: UUID!): Boolean!
  
  # Relationship
  initiateRelationshipReset(companionId: UUID!, resetType: ResetType!, newType: CompanionType): ResetResult!
  confirmRelationshipReset(resetId: UUID!): ResetResult!
  cancelRelationshipReset(resetId: UUID!): Boolean!
  writeDiaryEntry(companionId: UUID!, entry: DiaryEntryInput!): DiaryEntry!
  
  # Safety
  reportSafetyConcern(companionId: UUID!, concern: SafetyConcernInput!): SafetyReport!
  appealIntervention(interventionId: UUID!, reason: String!, requestedAction: String!): AppealResult!
  
  # Preferences
  updateUserPreferences(input: UserPreferencesInput!): UserPreferences!
  updateSafetyPreferences(companionId: UUID!, input: SafetyPreferencesInput!): SafetyConfig!
  
  # Export
  createExportJob(companionId: UUID!, input: ExportJobInput!): ExportJob!
  cancelExportJob(id: UUID!): Boolean!
  
  # Subscription
  createSubscription(plan: SubscriptionPlan!, paymentMethodId: String!): Subscription!
  cancelSubscription(): Boolean!
  updateSubscriptionPlan(plan: SubscriptionPlan!): Subscription!
}

input CompanionUpdateInput {
  name: String
  description: String
  identity: CompanionIdentityInput
  voice: VoiceConfigInput
  isActive: Boolean
}

input ForgetScopeInput {
  type: ForgetScopeType!
  topic: String
  dateRange: DateRangeInput
  modality: Modality
}

enum ForgetScopeType {
  TOPIC
  TIME_RANGE
  MODALITY
  ALL
}

type ForgetResult {
  memoriesAffected: Int!
  types: JSON!
  deletionProofs: [DeletionProof!]!
  estimatedCompletion: DateTime!
}

type DeletionProof {
  memoryId: UUID!
  vectorDeleted: Boolean!
  graphEdgesRemoved: Int!
  relationalRowsDeleted: Int!
  verificationHash: String!
}

type ConsolidationReport {
  companionId: UUID!
  episodicProcessed: Int!
  semanticCreated: Int!
  contradictionsFound: Int!
  userReviewRequired: Boolean!
}

input BoundaryInput {
  trigger: BoundaryTriggerInput!
  action: BoundaryAction!
  explanation: String!
  scope: BoundaryScope!
}

input BoundaryTriggerInput {
  type: BoundaryTriggerType!
  pattern: String!
}

enum BoundaryTriggerType {
  TOPIC
  PHRASE
  EMOTION
  TIME
  CONTEXT
}

enum BoundaryScope {
  CONVERSATION
  SESSION
  PERMANENT
}

type BoundaryResult {
  boundaryId: UUID!
  status: BoundaryStatus!
  companionAcknowledgment: String!
}

enum BoundaryStatus {
  ACTIVE
  INACTIVE
  EXPIRED
}

type MessageStream {
  streamId: UUID!
  chunks: [MessageChunk!]!
}

type MessageChunk {
  content: String!
  isFinal: Boolean!
  emotion: EmotionState
  memoryReferences: [UUID!]!
}

input ProactiveFeedbackInput {
  rating: ProactiveRating!
  comment: String
  suggestedTime: String
}

type FeedbackResult {
  feedbackId: UUID!
  applied: Boolean!
  adjustments: [String!]!
}

enum ResetType {
  SOFT
  REFRAME
  HARD
  ARCHIVE
}

type ResetResult {
  resetId: UUID!
  status: ResetStatus!
  coolingPeriodEnds: DateTime
  preview: ResetPreview
}

enum ResetStatus {
  PENDING_CONFIRMATION
  CONFIRMED
  COMPLETED
  CANCELED
  FAILED
}

type ResetPreview {
  intimacyCeiling: String
  proactivity: String
  conflictStyle: String
}

input DiaryEntryInput {
  text: String!
  tags: [String!]
  emotionalTone: Float!
  visibility: DiaryVisibility!
}

input SafetyConcernInput {
  type: SafetyConcernType!
  description: String!
  urgency: TriggerUrgency!
  userMessageId: UUID
}

enum SafetyConcernType {
  CRISIS
  CONTENT
  BEHAVIORAL
  PRIVACY
  OTHER
}

type SafetyReport {
  reportId: UUID!
  status: SafetyReportStatus!
  crisisResourcesProvided: Boolean!
  humanReviewInitiated: Boolean!
}

enum SafetyReportStatus {
  RECEIVED
  ESCALATED
  RESOLVED
  FALSE_POSITIVE
}

type AppealResult {
  appealId: UUID!
  status: AppealStatus!
  estimatedResolution: DateTime!
  temporaryOverride: Boolean!
}

enum AppealStatus {
  UNDER_REVIEW
  APPROVED
  DENIED
  PARTIAL
}

input UserPreferencesInput {
  theme: Theme
  language: String
  timezone: String
  notifications: NotificationPreferencesInput
  privacy: PrivacyPreferencesInput
  accessibility: AccessibilityPreferencesInput
}

input NotificationPreferencesInput {
  push: Boolean
  email: Boolean
  inApp: Boolean
  proactive: Boolean
  milestones: Boolean
  weeklyDigest: Boolean
}

input PrivacyPreferencesInput {
  analytics: Boolean
  crashReporting: Boolean
  personalizedAds: Boolean
  dataSharing: Boolean
}

input AccessibilityPreferencesInput {
  fontSize: FontSize
  highContrast: Boolean
  reduceMotion: Boolean
  screenReaderOptimized: Boolean
  voiceSpeed: Float
}

# ==================== SUBSCRIPTIONS ====================
type Subscription {
  # Real-time updates
  messageReceived(companionId: UUID!): ConversationMessage!
  memoryCreated(companionId: UUID!): Memory!
  memoryUpdated(companionId: UUID!): Memory!
  memoryDeleted(companionId: UUID!): UUID!
  relationshipDimensionChanged(companionId: UUID!): RelationshipDimensionUpdate!
  milestoneAchieved(companionId: UUID!): Milestone!
  proactiveGenerated(companionId: UUID!): ProactiveMessage!
  proactiveMessageSent!
  safetyEventOccurred(companionId: UUID!): SafetyEvent!
  voiceCallStateChanged(companionId: UUID!): VoiceCall!
  typingIndicator(companionId: UUID!): TypingIndicator!
  presenceChanged(companionId: UUID!): PresenceUpdate!
}

type RelationshipDimensionUpdate {
  dimension: String!
  oldValue: Float!
  newValue: Float!
  trigger: String!
}

type TypingIndicator {
  userId: UUID!
  isTyping: Boolean!
}

type PresenceUpdate {
  userId: UUID!
  status: PresenceStatus!
  lastSeen: DateTime
}

enum PresenceStatus {
  ONLINE
  AWAY
  BUSY
  OFFLINE
}
```

---

## REST API Endpoints

### Companion Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/companions` | Create companion |
| `GET` | `/v1/companions` | List companions |
| `GET` | `/v1/companions/{id}` | Get companion |
| `PATCH` | `/v1/companions/{id}` | Update companion |
| `DELETE` | `/v1/companions/{id}` | Delete companion |
| `POST` | `/v1/companions/{id}/archive` | Archive companion |
| `POST` | `/v1/companions/{id}/activate` | Activate companion |

### Memory

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/companions/{id}/memory/write` | Write memory |
| `GET` | `/v1/companions/{id}/memory/{memoryId}` | Get memory |
| `PATCH` | `/v1/companions/{id}/memory/{memoryId}` | Update memory |
| `DELETE` | `/v1/companions/{id}/memory/{memoryId}` | Delete memory |
| `POST` | `/v1/companions/{id}/memory/recall` | Recall memories |
| `POST` | `/v1/companions/{id}/memory/forget` | Bulk forget |
| `POST` | `/v1/companions/{id}/memory/consolidate` | Trigger consolidation |
| `POST` | `/v1/companions/{id}/memory/export` | Export memories |

### Conversation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/companions/{id}/messages` | Send message |
| `GET` | `/v1/companions/{id}/messages` | List messages |
| `GET` | `/v1/companions/{id}/context` | Get conversation context |
| `POST` | `/v1/companions/{id}/boundaries` | Set boundary |
| `DELETE` | `/v1/companions/{id}/boundaries/{boundaryId}` | Remove boundary |

### Voice

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/companions/{id}/voice/call` | Start voice call |
| `GET` | `/v1/companions/{id}/voice/config` | Get voice config |
| `PATCH` | `/v1/companions/{id}/voice/config` | Update voice config |
| `POST` | `/v1/voice/calls/{callId}/end` | End voice call |

### Proactive

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/companions/{id}/proactive/config` | Get proactive config |
| `PATCH` | `/v1/companions/{id}/proactive/config` | Update proactive config |
| `GET` | `/v1/companions/{id}/proactive/pending` | Get pending proactives |
| `GET` | `/v1/companions/{id}/proactive/history` | Get proactive history |
| `POST` | `/v1/companions/{id}/proactive/feedback` | Submit feedback |
| `POST` | `/v1/companions/{id}/proactive/{proactiveId}/snooze` | Snooze proactive |
| `POST` | `/v1/companions/{id}/proactive/{proactiveId}/dismiss` | Dismiss proactive |

### Relationship

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/companions/{id}/relationship` | Get relationship state |
| `GET` | `/v1/companions/{id}/relationship/dimensions/{dimension}/history` | Get dimension history |
| `GET` | `/v1/companions/{id}/relationship/milestones` | Get milestones |
| `GET` | `/v1/companions/{id}/relationship/diary` | Get shared diary |
| `POST` | `/v1/companions/{id}/relationship/reset` | Initiate reset |
| `POST` | `/v1/companions/{id}/relationship/reset/{resetId}/confirm` | Confirm reset |
| `POST` | `/v1/companions/{id}/relationship/diary` | Write diary entry |

### Safety

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/companions/{id}/safety/status` | Get safety status |
| `GET` | `/v1/companions/{id}/safety/events` | Get safety events |
| `POST` | `/v1/companions/{id}/safety/report` | Report concern |
| `POST` | `/v1/companions/{id}/safety/appeal` | Appeal intervention |
| `GET` | `/v1/companions/{id}/safety/preferences` | Get safety preferences |
| `PATCH` | `/v1/companions/{id}/safety/preferences` | Update safety preferences |

### Evaluation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/companions/{id}/evaluation/status` | Get evaluation status |

### Export

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/companions/{id}/export` | Create export job |
| `GET` | `/v1/companions/{id}/export` | List export jobs |
| `GET` | `/v1/export/{exportId}` | Get export job |
| `DELETE` | `/v1/export/{exportId}` | Cancel export job |

### User & Subscription

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/v1/me` | Get current user |
| `GET` | `/v1/subscription` | Get subscription |
| `POST` | `/v1/subscription` | Create subscription |
| `DELETE` | `/v1/subscription` | Cancel subscription |
| `PATCH` | `/v1/subscription/plan` | Change plan |
| `GET` | `/v1/preferences` | Get user preferences |
| `PATCH` | `/v1/preferences` | Update user preferences |

---

## WebSocket API

### Connection

```javascript
// Connect
const ws = new WebSocket('wss://api.pao.app/ws?token=<access_token>');

// Authenticate
ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'auth',
    token: '<access_token>',
    companionId: '<companion_uuid>'  // Optional, for companion-scoped
  }));
};
```

### Message Format

```typescript
// Client → Server
interface ClientMessage {
  type: 'subscribe' | 'unsubscribe' | 'ping' | 'message' | 'typing' | 'voice';
  payload: any;
  requestId: string;
}

// Server → Client
interface ServerMessage {
  type: 'event' | 'ack' | 'error' | 'pong';
  event?: string;
  payload: any;
  requestId?: string;
  timestamp: string;
}
```

### Subscriptions

```typescript
// Subscribe to events
ws.send(JSON.stringify({
  type: 'subscribe',
  payload: {
    events: [
      'message.received',
      'memory.created',
      'relationship.dimension_changed',
      'milestone.achieved',
      'proactive.generated',
      'safety.event',
      'voice.call_state',
      'typing.indicator',
      'presence.changed'
    ],
    companionId: '<companion_uuid>'
  },
  requestId: 'req-123'
}));

// Receive event
{
  "type": "event",
  "event": "message.received",
  "payload": { /* ConversationMessage */ },
  "timestamp": "2025-06-25T10:30:00Z"
}
```

### Real-Time Conversation

```typescript
// Send message (streaming response)
ws.send(JSON.stringify({
  type: 'message',
  payload: {
    companionId: '<companion_uuid>',
    content: 'Hello!',
    modality: 'text'
  },
  requestId: 'req-456'
}));

// Receive streaming chunks
{
  "type": "event",
  "event": "message.chunk",
  "payload": {
    "streamId": "uuid",
    "content": "Hel",
    "isFinal": false,
    "emotion": { /* EmotionState */ }
  }
}
```

### Voice Call Signaling

```typescript
// Start call
ws.send(JSON.stringify({
  type: 'voice',
  payload: {
    action: 'start_call',
    companionId: '<companion_uuid>',
    webrtcOffer: 'sdp_string'
  },
  requestId: 'req-789'
}));

// Receive answer
{
  "type": "event",
  "event": "voice.call_answer",
  "payload": {
    "callId": "uuid",
    "webrtcAnswer": "sdp_string",
    "iceCandidates": [...]
  }
}

// ICE candidates
{
  "type": "event",
  "event": "voice.ice_candidate",
  "payload": {
    "callId": "uuid",
    "candidate": "candidate_string"
  }
}
```

---

## gRPC Services (Internal)

### Service Definitions

```protobuf
// conversation.proto
service ConversationService {
  rpc ProcessMessage(ProcessMessageRequest) returns (ProcessMessageResponse);
  rpc StreamMessage(StreamMessageRequest) returns (stream StreamMessageResponse);
  rpc GetContext(GetContextRequest) returns (ConversationContext);
}

// memory.proto
service MemoryService {
  rpc WriteMemory(WriteMemoryRequest) returns (Memory);
  rpc Recall(RecallRequest) returns (RecallResponse);
  rpc GetMemory(GetMemoryRequest) returns (Memory);
  rpc UpdateMemory(UpdateMemoryRequest) returns (Memory);
  rpc DeleteMemory(DeleteMemoryRequest) returns (DeleteResponse);
  rpc Consolidate(ConsolidateRequest) returns (ConsolidationReport);
}

// relationship.proto
service RelationshipService {
  rpc GetState(GetStateRequest) returns (RelationshipState);
  rpc UpdateDimensions(UpdateDimensionsRequest) returns (RelationshipState);
  rpc GetDimensionHistory(GetDimensionHistoryRequest) returns (DimensionHistory);
  rpc InitiateReset(InitiateResetRequest) returns (ResetResult);
  rpc ConfirmReset(ConfirmResetRequest) returns (ResetResult);
}

// proactive.proto
service ProactiveService {
  rpc GenerateProactives(GenerateProactivesRequest) returns (ProactiveList);
  rpc GetPending(GetPendingRequest) returns (ProactiveList);
  rpc SubmitFeedback(SubmitFeedbackRequest) returns (FeedbackResult);
}

// safety.proto
service SafetyService {
  rpc CheckContent(CheckContentRequest) returns (SafetyCheckResult);
  rpc DetectCrisis(DetectCrisisRequest) returns (CrisisAssessment);
  rpc GetStatus(GetStatusRequest) returns (SafetyStatus);
  rpc ReportConcern(ReportConcernRequest) returns (SafetyReport);
}

// evaluation.proto
service EvaluationService {
  rpc GetStatus(GetStatusRequest) returns (EvaluationStatus);
  rpc SubmitHumanEval(SubmitHumanEvalRequest) returns (HumanEvalResult);
  rpc GetExperimentResults(GetExperimentResultsRequest) returns (ExperimentResults);
}
```

---

## Error Handling

### GraphQL Errors

```json
{
  "errors": [
    {
      "message": "Companion not found",
      "extensions": {
        "code": "NOT_FOUND",
        "resource": "Companion",
        "resourceId": "uuid"
      }
    }
  ],
  "data": null
}
```

### REST Errors

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "error": {
    "code": "NOT_FOUND",
    "message": "Companion not found",
    "details": {
      "resource": "Companion",
      "resourceId": "uuid"
    },
    "requestId": "req-uuid",
    "timestamp": "2025-06-25T10:30:00Z"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `OK` | 200 | Success |
| `CREATED` | 201 | Resource created |
| `BAD_REQUEST` | 400 | Invalid input |
| `UNAUTHORIZED` | 401 | Invalid/missing auth |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource conflict |
| `UNPROCESSABLE_ENTITY` | 422 | Validation failed |
| `TOO_MANY_REQUESTS` | 429 | Rate limited |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Service down |
| `GATEWAY_TIMEOUT` | 504 | Upstream timeout |

### Rate Limits

| Scope | Limit | Window |
|-------|-------|--------|
| Per user (authenticated) | 1000 req | 1 minute |
| Per companion (write) | 100 req | 1 minute |
| Per companion (recall) | 50 req | 1 minute |
| Per user (voice call) | 10 calls | 1 hour |
| Per user (export) | 1 job | 1 hour |
| Per IP (unauthenticated) | 60 req | 1 minute |

---

## Webhooks

### Configuration

```http
POST /v1/webhooks
{
  "url": "https://your-app.com/webhooks/pao",
  "events": [
    "companion.created",
    "companion.archived",
    "memory.consolidated",
    "relationship.milestone",
    "proactive.generated",
    "safety.crisis_detected",
    "voice.call_ended",
    "export.completed",
    "subscription.changed"
  ],
  "secret": "webhook_secret_for_verification"
}
```

### Payload Format

```json
{
  "id": "evt-uuid",
  "type": "relationship.milestone",
  "createdAt": "2025-06-25T10:30:00Z",
  "data": {
    "companionId": "uuid",
    "milestone": {
      "type": "ANNIVERSARY_1",
      "name": "1 Year Together",
      "achievedAt": "2025-06-25T10:30:00Z"
    }
  },
  "signature": "sha256=..."
}
```

---

## SDKs

### Official SDKs

| Language | Package | Status |
|----------|---------|--------|
| TypeScript/JavaScript | `@pao/sdk` | ✅ Published |
| Python | `pao-sdk` | ✅ Published |
| Swift | `PAOSDK` | 🚧 In Progress |
| Kotlin | `pao-sdk` | 🚧 In Progress |
| Dart/Flutter | `pao_sdk` | 📋 Planned |

### TypeScript Example

```typescript
import { PAOClient } from '@pao/sdk';

const client = new PAOClient({
  accessToken: 'user_access_token',
  companionId: 'companion_uuid'
});

// Send message
const response = await client.sendMessage('Hello, how are you?');

// Recall memories
const memories = await client.recall({
  query: 'What did we discuss about my career?',
  context: { currentTopic: 'career' },
  limit: 10
});

// Listen to real-time events
client.on('message.received', (message) => {
  console.log('New message:', message);
});

client.on('proactive.generated', (proactive) => {
  showNotification(proactive.content);
});

// Voice call
const call = await client.startVoiceCall();
call.on('audio', (chunk) => playAudio(chunk));
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-06-25 | Initial specification |

---

**Aligned With:** `300-system-architecture.md`, `200-ai-architecture.md`, `07-adr/ADR-005-graphql-api.md`
**Next Review:** 2026-01-17