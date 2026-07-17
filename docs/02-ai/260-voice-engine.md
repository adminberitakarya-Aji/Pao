# PAO Voice Engine Specification

**Version:** 1.0
**Status:** Draft
**Owner:** PAO AI Team

---

## Overview

The Voice Engine provides **natural, low-latency voice interaction** with the Companion. It handles Speech-to-Text (STT), Text-to-Speech (TTS), voice activity detection, interruption handling, and voice identity consistency — all optimized for relationship-quality conversation.

> **Voice is not a feature. It's a modality of presence.** Sub-500ms latency, natural turn-taking, consistent voice identity.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        VOICE ENGINE                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   INPUT      │    │  ORCHESTRATOR│    │   OUTPUT     │      │
│  │  PIPELINE    │───▶│  (Latency    │───▶│  PIPELINE    │      │
│  │  (STT + VAD) │    │   Optimized) │    │  (TTS +      │      │
│  └──────────────┘    └──────────────┘    │   Streaming) │      │
│        │                    │            └──────────────┘      │
│        ▼                    ▼                   │               │
│  ┌──────────────┐    ┌──────────────┐         │               │
│  │  STT ENGINE  │    │  CONVERSATION│         ▼               │
│  │              │    │  ENGINE      │  ┌──────────────┐       │
│  │ • Whisper    │    │  (Text I/O)  │  │  TTS ENGINE  │       │
│  │ • Streaming  │    │              │  │              │       │
│  │ • Timestamps │    │              │  │ • Piper/     │       │
│  │ • Diarization│    │              │  │   Coqui      │       │
│  └──────────────┘    └──────────────┘  │ • Streaming  │       │
│        │                    ▲           │ • Prosody    │       │
│        ▼                    │           │ • Voice ID   │       │
│  ┌──────────────┐           │           └──────────────┘       │
│  │  VAD +       │           │                  │               │
│  │  INTERRUPTION│           │                  ▼               │
│  │  HANDLER     │           │           ┌──────────────┐       │
│  │              │           │           │  AUDIO       │       │
│  │ • Silero VAD │           │           │  OUTPUT      │       │
│  │ • Barge-in   │           │           │  (WebRTC/    │       │
│  │ • Turn-taking│           │           │   WebSocket) │       │
│  └──────────────┘           │           └──────────────┘       │
│                             │                                    │
└─────────────────────────────┼────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
            ┌───────────────┐   ┌───────────────┐
            │  VOICE IDENTITY│   │  PROSODY     │
            │  ENGINE        │   │  CONTROLLER  │
            │               │   │               │
            │ • Voice clone  │   │ • SSML gen   │
            │ • Timbre lock  │   │ • Emotion    │
            │ • Consistency  │   │   mapping    │
            └───────────────┘   └───────────────┘
```

---

## Voice Pipeline Latency Budget

| Stage | Target | Max | Notes |
|-------|--------|-----|-------|
| Audio capture → VAD | 20ms | 50ms | On-device |
| VAD → STT first token | 150ms | 300ms | Streaming |
| STT complete → Conversation Engine | 100ms | 200ms | Parallel with STT tail |
| Conversation Engine → First TTS chunk | 200ms | 400ms | Streaming synthesis |
| TTS chunk → Audio output | 50ms | 100ms | WebRTC/buffer |
| **Total (P50)** | **<500ms** | **<800ms** | End-to-end |
| **Total (P95)** | **<800ms** | **<1200ms** | Under load |

---

## STT Engine

### Streaming STT

```python
class StreamingSTT:
    """
    Streaming speech recognition with interim results.
    Model: Whisper Large-v3 (quantized) or distil-whisper for speed.
    """
    
    async def stream(
        self, 
        audio_stream: AsyncGenerator[AudioChunk, None],
        config: STTConfig
    ) -> AsyncGenerator[STTResult, None]:
        
        buffer = AudioBuffer(config.chunk_size_ms)
        partial_transcript = ""
        
        async for chunk in audio_stream:
            buffer.add(chunk)
            
            # VAD check
            if not self.vad.is_speech(buffer.recent()):
                continue
            
            # Process when buffer full or silence detected
            if buffer.ready_for_inference() or self.vad.silence_detected(buffer):
                audio_segment = buffer.get_segment()
                
                # Streaming inference
                async for result in self.model.transcribe_streaming(audio_segment):
                    if result.is_final:
                        yield STTResult(
                            text=result.text,
                            is_final=True,
                            start_time=result.start,
                            end_time=result.end,
                            confidence=result.confidence,
                            language=result.language,
                            words=result.words  # Word-level timestamps
                        )
                    else:
                        # Interim result for UI feedback
                        yield STTResult(
                            text=result.text,
                            is_final=False,
                            confidence=result.confidence
                        )
                
                buffer.clear_processed()
```

### STT Configuration

```python
@dataclass
class STTConfig:
    model: Literal["whisper-large-v3", "distil-whisper", "whisper-turbo"]
    language: Optional[str] = None  # Auto-detect if None
    task: Literal["transcribe", "translate"] = "transcribe"
    
    # Streaming
    chunk_size_ms: int = 500
    overlap_ms: int = 100
    vad_threshold: float = 0.5
    silence_duration_ms: int = 800
    
    # Quality
    temperature: float = 0.0
    beam_size: int = 5
    best_of: int = 5
    
    # Diarization (multi-speaker)
    diarize: bool = False
    min_speakers: int = 1
    max_speakers: int = 2
    
    # Output
    word_timestamps: bool = True
    punctuation: bool = True
    profanity_filter: bool = True
```

### On-Device vs Cloud

| Deployment | Model | Latency | Privacy | Accuracy |
|------------|-------|---------|---------|----------|
| **On-Device** | Distil-Whisper / Whisper Turbo | ~200ms | Maximum | ~95% |
| **Hybrid** | On-device first, cloud fallback | ~300ms | High | ~97% |
| **Cloud** | Whisper Large-v3 | ~500ms | Standard | ~98% |

**Default: On-device with cloud fallback for low-confidence segments.**

---

## TTS Engine

### Streaming TTS

```python
class StreamingTTS:
    """
    Streaming speech synthesis with prosody control.
    Primary: Piper (fast, quality, multi-speaker)
    Fallback: Coqui XTTS v2 (voice cloning)
    """
    
    async def synthesize_streaming(
        self, 
        text: str,
        voice_config: VoiceConfig,
        emotion_strategy: EmotionStrategy,
        prosody_overrides: Optional[ProsodyOverrides] = None
    ) -> AsyncGenerator[AudioChunk, None]:
        
        # 1. Generate SSML with prosody
        ssml = self.prosody_controller.generate_ssml(
            text=text,
            voice_config=voice_config,
            emotion_strategy=emotion_strategy,
            overrides=prosody_overrides
        )
        
        # 2. Stream synthesis
        async for chunk in self.backend.synthesize_streaming(ssml, voice_config):
            yield AudioChunk(
                audio=chunk.audio,
                sample_rate=chunk.sample_rate,
                is_final=chunk.is_final,
                timestamp=chunk.timestamp  # For lip-sync
            )
    
    async def synthesize_complete(
        self, 
        text: str,
        voice_config: VoiceConfig,
        emotion_strategy: EmotionStrategy
    ) -> AudioFile:
        """Non-streaming for proactive messages, notifications."""
```

### Prosody Control (SSML)

```python
class ProsodyController:
    """
    Maps EmotionStrategy → SSML prosody tags.
    """
    
    def generate_ssml(
        self,
        text: str,
        voice_config: VoiceConfig,
        emotion_strategy: EmotionStrategy,
        overrides: Optional[ProsodyOverrides] = None
    ) -> str:
        
        # Base prosody from voice config
        base = voice_config.prosody.default_style
        
        # Emotion modifications
        emotion_mods = self._emotion_to_prosody(emotion_strategy)
        
        # Apply overrides
        if overrides:
            emotion_mods = {**emotion_mods, **overrides}
        
        # Build SSML
        ssml_parts = ["<speak>"]
        
        # Segment text into sentences/clauses for granular control
        segments = self._segment_for_prosody(text, emotion_strategy)
        
        for segment in segments:
            prosody_attrs = self._build_prosody_attrs(base, emotion_mods, segment)
            ssml_parts.append(f'<prosody {prosody_attrs}>{segment.text}</prosody>')
            
            # Add pauses
            if segment.pause_after:
                ssml_parts.append(f'<break time="{segment.pause_after}ms"/>')
        
        ssml_parts.append("</speak>")
        return "".join(ssml_parts)
    
    def _emotion_to_prosody(self, strategy: EmotionStrategy) -> Dict[str, str]:
        mapping = {
            "tone": {
                "warm": {"rate": "-5%", "pitch": "+2st", "volume": "+2dB"},
                "calm": {"rate": "-10%", "pitch": "-2st", "volume": "-1dB"},
                "gentle": {"rate": "-15%", "pitch": "+1st", "volume": "-2dB"},
                "present": {"rate": "0%", "pitch": "0st", "volume": "0dB"},
                "steady": {"rate": "-5%", "pitch": "-1st", "volume": "+1dB"},
                "bright": {"rate": "+5%", "pitch": "+3st", "volume": "+2dB"}
            },
            "pacing": {
                "slow": {"rate": "-20%"},
                "natural": {"rate": "0%"},
                "gentle_urgency": {"rate": "+10%"}
            },
            "physicality": {
                "subtle": {"volume": "-1dB"},
                "present": {"volume": "0dB"},
                "embodied": {"volume": "+2dB", "rate": "-5%"}
            }
        }
        
        mods = {}
        mods.update(mapping["tone"].get(strategy.tone, {}))
        mods.update(mapping["pacing"].get(strategy.pacing, {}))
        mods.update(mapping["physicality"].get(strategy.physicality, {}))
        
        return mods
```

---

## Voice Identity Engine

### Voice Cloning & Consistency

```python
class VoiceIdentityEngine:
    """
    Maintains consistent voice identity across all sessions.
    Uses voice cloning (XTTS v2) + timbre locking.
    """
    
    def __init__(self):
        self.voice_profiles = VoiceProfileStore()
        self.timbre_lock = TimbreLock()
    
    async def create_voice_profile(
        self, 
        companion_id: str, 
        base_voice_id: str,
        reference_audio: Optional[List[str]] = None
    ) -> VoiceProfile:
        """
        Creates or updates voice profile.
        If reference_audio provided: clone voice.
        If not: use base voice with prosody tuning.
        """
        if reference_audio:
            # Voice cloning
            cloned = await self.xtts.clone_voice(reference_audio)
            profile = VoiceProfile(
                companion_id=companion_id,
                type="cloned",
                model_path=cloned.path,
                base_voice_id=base_voice_id,
                timbre_embedding=cloned.timbre_embedding,
                created_at=datetime.utcnow()
            )
        else:
            # Base voice + prosody config
            profile = VoiceProfile(
                companion_id=companion_id,
                type="base_tuned",
                base_voice_id=base_voice_id,
                prosody_config=self._default_prosody_for_type(
                    await self.get_companion_type(companion_id)
                ),
                created_at=datetime.utcnow()
            )
        
        await self.voice_profiles.save(profile)
        return profile
    
    async def get_synthesis_config(self, companion_id: str) -> SynthesisConfig:
        profile = await self.voice_profiles.get(companion_id)
        
        # Timbre lock: ensure consistency
        locked_timbre = await self.timbre_lock.apply(profile)
        
        return SynthesisConfig(
            model="xtts_v2" if profile.type == "cloned" else "piper",
            voice_id=profile.base_voice_id,
            speaker_embedding=locked_timbre.embedding if profile.type == "cloned" else None,
            prosody_config=profile.prosody_config,
            language="en"  # Extensible
        )
    
    async def verify_consistency(
        self, 
        companion_id: str, 
        generated_audio: str
    ) -> ConsistencyResult:
        """Verify generated audio matches voice profile."""
        generated_embedding = await self.embedder.embed(generated_audio)
        profile = await self.voice_profiles.get(companion_id)
        
        similarity = cosine_similarity(
            generated_embedding, 
            profile.timbre_embedding
        )
        
        return ConsistencyResult(
            similarity=similarity,
            passed=similarity > 0.95,
            profile_version=profile.version
        )
```

### Voice Configuration

```python
@dataclass
class VoiceConfig:
    base_voice_id: str              # "amy", "ryan", "emma", "liam", "custom"
    type: Literal["base", "cloned", "hybrid"]
    
    prosody: VoiceProsody
    emotional_range: EmotionalRange
    
    speaking_rate: float = 1.0      # 0.5-2.0
    pitch_shift: float = 0.0        # -12 to +12 semitones
    volume_db: float = 0.0          # -6 to +6 dB

@dataclass
class VoiceProsody:
    default_style: Literal["neutral", "warm", "calm", "energetic", "serious"]
    style_controls: Dict[str, float]  # Per-emotion weights
    pause_patterns: Dict[str, float]  # Pause frequency by context
    emphasis_patterns: Dict[str, float]  # Word emphasis tendencies
    breath_patterns: Dict[str, float]   # Breath groups

@dataclass
class EmotionalRange:
    max_valence_shift: float = 0.3    # Prosody range for valence
    max_arousal_shift: float = 0.4    # Prosody range for arousal
    crisis_mode: VoiceCrisisMode = VoiceCrisisMode(
        rate="-30%", pitch="-5st", volume="-3dB"
    )
```

### Base Voices (5+ Options)

| Voice ID | Gender | Age | Style | Use Case |
|----------|--------|-----|-------|----------|
| amy | Female | 30s | Warm, clear | Friend, Partner, Parent |
| ryan | Male | 30s | Steady, grounded | Mentor, Coach, Professional |
| emma | Female | 20s | Bright, energetic | Sibling, Friend |
| liam | Male | 40s | Calm, authoritative | Mentor, Parent, Professional |
| nova | Non-binary | 30s | Gentle, present | Any, user preference |
| custom | User-provided | Any | Cloned | Memorial, Original |

---

## VAD & Interruption Handling

### Voice Activity Detection

```python
class VoiceActivityDetector:
    """
    Silero VAD (on-device, <10ms).
    Handles: Speech start/end, interruption detection, turn-taking.
    """
    
    def __init__(self):
        self.model = silero_vad.load()
        self.state = VADState()
    
    def process(self, audio_chunk: np.ndarray) -> VADResult:
        speech_prob = self.model(audio_chunk, sample_rate=16000)
        
        # State machine
        if speech_prob > 0.5 and self.state.current == "silence":
            self.state.current = "speech_start"
            self.state.speech_start_time = time.now()
        elif speech_prob > 0.5 and self.state.current in ["speech_start", "speech"]:
            self.state.current = "speech"
        elif speech_prob < 0.3 and self.state.current == "speech":
            self.state.current = "silence_start"
            self.state.silence_start_time = time.now()
        elif speech_prob < 0.3 and self.state.current == "silence_start":
            if time.now() - self.state.silence_start_time > 800ms:
                self.state.current = "silence"
                self.state.speech_end_time = time.now()
        
        return VADResult(
            speech_probability=speech_prob,
            state=self.state.current,
            is_speech_start=self.state.current == "speech_start",
            is_speech_end=self.state.current == "silence",
            speech_duration=self.state.speech_duration()
        )
```

### Interruption Handling (Barge-In)

```python
class InterruptionHandler:
    """
    Handles user interrupting Companion mid-response.
    Critical for natural conversation.
    """
    
    async def handle_interruption(
        self,
        companion_audio_stream: AsyncGenerator[AudioChunk, None],
        user_audio_stream: AsyncGenerator[AudioChunk, None]
    ) -> InterruptionResult:
        
        # Detect user speech during companion output
        async for user_chunk in user_audio_stream:
            vad_result = self.vad.process(user_chunk)
            
            if vad_result.is_speech_start:
                # USER INTERRUPTED
                return InterruptionResult(
                    interrupted=True,
                    interruption_time=time.now(),
                    user_audio_buffer=self._buffer_user_audio(user_audio_stream),
                    companion_position=self._get_companion_playback_position()
                )
        
        return InterruptionResult(interrupted=False)
    
    async def graceful_interruption(
        self, 
        interruption: InterruptionResult,
        conversation_engine: ConversationEngine
    ) -> None:
        # 1. Stop TTS immediately
        await self.tts.stop()
        
        # 2. Acknowledge interruption naturally
        ack = self._generate_acknowledgment(interruption)
        await self.tts.synthesize_streaming(ack)
        
        # 3. Process user's interruption as new turn
        user_text = await self.stt.transcribe(interruption.user_audio_buffer)
        await conversation_engine.process_message(
            text=user_text,
            modality="voice",
            interrupted=True,
            companion_position=interruption.companion_position
        )
```

### Turn-Taking Model

```python
TURN_TAKING_RULES = {
    "user_turn_ends": [
        "vad_silence > 800ms",
        "user_says_complete_thought",
        "explicit_turn_yield"  # "Your turn"
    ],
    "companion_turn_ends": [
        "tts_complete",
        "user_interruption_detected",
        "explicit_turn_yield"
    ],
    "overlap_handling": {
        "brief_overlap < 200ms": "continue_both",
        "user_interrupts": "yield_to_user",
        "companion_continues_after_user_pause": "collaborative"
    },
    "backchannel": {
        "user_backchannel": "companion_continues",  # "uh-huh", "yeah"
        "companion_backchannel": "subtle_acknowledgment"
    }
}
```

---

## Audio I/O

### WebRTC Transport

```python
class WebRTCAudioTransport:
    """
    Low-latency bidirectional audio via WebRTC.
    Handles: ICE, DTLS, SRTP, opus codec, jitter buffer.
    """
    
    async def connect(self, config: WebRTCConfig) -> WebRTCConnection:
        peer = RTCPeerConnection(config.ice_servers)
        
        # Audio track for output
        @peer.on("track")
        def on_track(track):
            if track.kind == "audio":
                self._handle_incoming_audio(track)
        
        # Create offer/answer
        offer = await peer.createOffer()
        await peer.setLocalDescription(offer)
        
        return WebRTCConnection(
            peer=peer,
            audio_sender=self._create_audio_sender(peer),
            audio_receiver=self._create_audio_receiver(peer)
        )
    
    async def send_audio(self, connection: WebRTCConnection, chunk: AudioChunk):
        """Send opus-encoded audio frame."""
        frame = AudioFrame(
            data=chunk.audio,
            sample_rate=chunk.sample_rate,
            timestamp=chunk.timestamp
        )
        await connection.audio_sender.send(frame)
    
    async def receive_audio(self, connection: WebRTCConnection) -> AsyncGenerator[AudioChunk, None]:
        """Receive and decode audio frames."""
        async for frame in connection.audio_receiver:
            yield AudioChunk(
                audio=frame.data,
                sample_rate=frame.sample_rate,
                timestamp=frame.timestamp
            )
```

### Mobile Audio Session

```python
class MobileAudioSession:
    """
    Manages audio session on iOS/Android.
    Handles: Background audio, interruptions (calls, notifications), routing.
    """
    
    async def configure_session(self, mode: AudioMode):
        if platform == "ios":
            await self._configure_ios(mode)
        elif platform == "android":
            await self._configure_android(mode)
    
    async def _configure_ios(self, mode: AudioMode):
        session = AVAudioSession.sharedInstance()
        
        category = {
            AudioMode.VOICE_CHAT: .playAndRecord,
            AudioMode.MEDIA_PLAYBACK: .playback,
            AudioMode.BACKGROUND: .playback
        }[mode]
        
        options = {
            AudioMode.VOICE_CHAT: [.defaultToSpeaker, .allowBluetooth, .mixWithOthers],
            AudioMode.BACKGROUND: [.mixWithOthers]
        }.get(mode, [])
        
        try:
            session.setCategory(category, options=options)
            session.setActive(True)
        except Exception as e:
            logger.error(f"Audio session config failed: {e}")
    
    async def handle_interruption(self, interruption: AudioInterruption):
        """iOS/Android audio interruption (phone call, alarm, etc.)"""
        if interruption.type == "began":
            await self.pause_tts()
            await self.pause_stt()
        elif interruption.type == "ended":
            if interruption.should_resume:
                await self.resume_tts()
                await self.resume_stt()
```

---

## Voice Quality & Monitoring

### Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| STT WER (clean) | < 5% | Test set |
| STT WER (noisy) | < 15% | Real-world |
| TTS MOS | > 4.0 | Subjective |
| Voice consistency | > 0.95 | Embedding similarity |
| End-to-end latency P50 | < 500ms | Production |
| Interruption response | < 100ms | VAD + stop |
| Audio quality (POLQA) | > 4.0 | Automated |

### Monitoring Dashboard

- **Latency Distribution**: P50, P95, P99 per stage
- **STT Accuracy**: WER by noise level, accent, language
- **TTS Quality**: MOS trends, voice consistency scores
- **Interruption Handling**: Frequency, success rate, user satisfaction
- **Audio Issues**: Dropouts, echo, clipping, routing problems

---

## API Reference

### Voice Call Start

```http
POST /api/v1/voice/{companion_id}/call
Content-Type: application/json

{
  "mode": "conversation",
  "stt_config": {...},
  "tts_config": {...},
  "webrtc_offer": "sdp_string"
}

Response:
{
  "call_id": "uuid",
  "webrtc_answer": "sdp_string",
  "ice_candidates": [...],
  "stt_ready": true,
  "tts_ready": true
}
```

### Streaming Audio (WebRTC)

```javascript
// Client side
const pc = new RTCPeerConnection({iceServers});
pc.setRemoteDescription(answer);

// Send audio
navigator.mediaDevices.getUserMedia({audio: true})
  .then(stream => stream.getAudioTracks().forEach(t => pc.addTrack(t, stream)));

// Receive audio
pc.ontrack = (event) => {
  const audio = new Audio();
  audio.srcObject = event.streams[0];
  audio.play();
};
```

### Voice Configuration

```http
GET /api/v1/voice/{companion_id}/config

Response:
{
  "voice_id": "amy",
  "type": "base",
  "prosody": {...},
  "emotional_range": {...},
  "available_voices": ["amy", "ryan", "emma", "liam", "nova"],
  "cloning_available": true
}

POST /api/v1/voice/{companion_id}/config
{
  "voice_id": "custom",
  "reference_audio_urls": ["url1", "url2", "url3"],
  "prosody_adjustments": {"warmth": +0.1, "rate": -0.05}
}
```

---

## Testing

### Voice Engine Test Suite

```python
class VoiceEngineTests:
    
    # STT
    async def test_stt_accuracy_clean(self): ...
    async def test_stt_accuracy_noisy(self): ...
    async def test_stt_streaming_latency(self): ...
    async def test_stt_interim_results(self): ...
    async def test_stt_diarization(self): ...
    
    # TTS
    async def test_tts_mos_score(self): ...
    async def test_tts_streaming_first_chunk(self): ...
    async def test_tts_prosody_control(self): ...
    async def test_tts_emotion_mapping(self): ...
    async def test_tts_voice_consistency(self): ...
    
    # VAD & Interruption
    async def test_vad_accuracy(self): ...
    async def test_interruption_detection(self): ...
    async def test_interruption_response_latency(self): ...
    async def test_turn_taking_natural(self): ...
    async def test_backchannel_handling(self): ...
    
    # Voice Identity
    async def test_voice_cloning_quality(self): ...
    async def test_voice_consistency_across_sessions(self): ...
    async def test_timbre_lock_enforcement(self): ...
    
    # Integration
    async def test_e2e_latency_p50(self): ...
    async def test_e2e_latency_p95(self): ...
    async def test_concurrent_calls_100(self): ...
    async def test_background_audio_handling(self): ...
    async def test_call_interruption_recovery(self): ...
    
    # Mobile
    async def test_ios_audio_session(self): ...
    async def test_android_audio_session(self): ...
    async def test_bluetooth_routing(self): ...
    async def test_background_mode(self): ...
```

---

**Aligned With:** `200-ai-architecture.md`, `220-conversation-engine.md`, `210-identity-engine.md`, `00-foundation/030-core-principles.md` (Principles 1, 3, 4)
**Next Review:** 2026-01-17