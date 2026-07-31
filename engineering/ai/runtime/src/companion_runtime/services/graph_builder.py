"""LangGraph Builder for Companion Runtime - Orchestrates all 8 AI engines."""

import logging
from typing import Dict, Any, Optional, List, AsyncGenerator, Literal
from uuid import UUID
from dataclasses import dataclass, field

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.base import BaseCheckpointSaver
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from companion_runtime.config import settings
from companion_runtime.models.requests import ChatRequest, ChatStreamRequest
from companion_runtime.models.responses import ChatResponse, ChatStreamChunk, GraphExecutionResponse
from companion_runtime.services.engine_clients import (
    IdentityEngineClient,
    MemoryEngineClient,
    SafetyEngineClient,
    RelationshipEngineClient,
    EmotionEngineClient,
    VoiceEngineClient,
    ProactiveEngineClient,
    EvaluationEngineClient,
    InferenceGatewayClient,
)
from companion_runtime.services.state_manager import StateManager, get_state_manager

logger = logging.getLogger(__name__)


# State definition for the graph
@dataclass
class CompanionState:
    """State passed through the LangGraph."""
    
    # Request info
    user_id: UUID
    companion_id: UUID
    conversation_id: UUID
    message: str
    message_id: Optional[UUID] = None
    request_id: Optional[str] = None
    
    # Streaming
    is_streaming: bool = False
    
    # Engine contexts (populated by nodes)
    identity_context: Optional[Dict[str, Any]] = None
    memory_context: Optional[Dict[str, Any]] = None
    relationship_state: Optional[Dict[str, Any]] = None
    emotion_state: Optional[Dict[str, Any]] = None
    
    # Safety
    safety_input_check: Optional[Dict[str, Any]] = None
    safety_output_check: Optional[Dict[str, Any]] = None
    safety_blocked: bool = False
    
    # LLM Generation
    llm_messages: List[Dict[str, str]] = field(default_factory=list)
    llm_response: Optional[str] = None
    llm_model: Optional[str] = None
    llm_tokens: int = 0
    llm_latency_ms: int = 0
    
    # Streaming chunks
    stream_chunks: List[str] = field(default_factory=list)
    
    # Post-processing
    dimension_updates: Dict[str, float] = field(default_factory=dict)
    proactive_nudge: Optional[Dict[str, Any]] = None
    consolidation_triggered: bool = False
    
    # Metadata
    total_latency_ms: int = 0
    errors: List[str] = field(default_factory=list)
    checkpoints_created: int = 0


def create_initial_state(request: ChatRequest) -> CompanionState:
    """Create initial state from chat request."""
    return CompanionState(
        user_id=request.user_id,
        companion_id=request.companion_id,
        conversation_id=request.conversation_id,
        message=request.message,
        message_id=request.message_id,
        request_id=request.request_id,
        is_streaming=False,
    )


def create_streaming_state(request: ChatStreamRequest) -> CompanionState:
    """Create initial state from streaming chat request."""
    return CompanionState(
        user_id=request.user_id,
        companion_id=request.companion_id,
        conversation_id=request.conversation_id,
        message=request.message,
        message_id=request.message_id,
        request_id=request.request_id,
        is_streaming=True,
    )


# Node functions
async def safety_pre_check(state: CompanionState, config: RunnableConfig) -> CompanionState:
    """Pre-check user input through Safety Engine."""
    start_time = __import__('time').time()
    logger.debug("Running safety pre-check", extra={"request_id": state.request_id})
    
    try:
        safety_client = SafetyEngineClient()
        result = await safety_client.validate_input(
            content=state.message,
            user_id=state.user_id,
            companion_id=state.companion_id,
            conversation_id=state.conversation_id,
            request_id=state.request_id,
        )
        
        state.safety_input_check = result
        
        if not result.get("allowed", True):
            state.safety_blocked = True
            action = result.get("action", "block")
            filtered = result.get("filtered_content")
            
            if action == "block":
                state.errors.append("Input blocked by safety engine")
                state.llm_response = filtered or "I'm unable to respond to that."
            elif action == "rewrite" and filtered:
                state.message = filtered
                logger.info("Input rewritten by safety engine", extra={"request_id": state.request_id})
        
    except Exception as e:
        logger.error(f"Safety pre-check failed: {e}", extra={"request_id": state.request_id})
        state.errors.append(f"Safety pre-check error: {e}")
        # Fail open in non-strict mode
        if not settings.safety_strict_mode:
            state.safety_input_check = {"allowed": True, "action": "allow"}
        else:
            state.safety_blocked = True
            state.errors.append("Safety engine unavailable in strict mode")
    
    state.total_latency_ms += int((__import__('time').time() - start_time) * 1000)
    return state


async def identity_context(state: CompanionState, config: RunnableConfig) -> CompanionState:
    """Get identity context from Identity Engine."""
    if state.safety_blocked:
        return state
    
    start_time = __import__('time').time()
    logger.debug("Fetching identity context", extra={"request_id": state.request_id})
    
    try:
        identity_client = IdentityEngineClient()
        result = await identity_client.get_context(
            companion_id=state.companion_id,
            request_id=state.request_id,
        )
        state.identity_context = result
    except Exception as e:
        logger.error(f"Identity context fetch failed: {e}", extra={"request_id": state.request_id})
        state.errors.append(f"Identity context error: {e}")
    
    state.total_latency_ms += int((__import__('time').time() - start_time) * 1000)
    return state


async def memory_retrieve(state: CompanionState, config: RunnableConfig) -> CompanionState:
    """Retrieve relevant memories from Memory Engine."""
    if state.safety_blocked:
        return state
    
    start_time = __import__('time').time()
    logger.debug("Retrieving memories", extra={"request_id": state.request_id})
    
    try:
        memory_client = MemoryEngineClient()
        result = await memory_client.recall(
            user_id=state.user_id,
            companion_id=state.companion_id,
            query=state.message,
            limit=10,
            request_id=state.request_id,
        )
        state.memory_context = result
    except Exception as e:
        logger.error(f"Memory recall failed: {e}", extra={"request_id": state.request_id})
        state.errors.append(f"Memory recall error: {e}")
    
    state.total_latency_ms += int((__import__('time').time() - start_time) * 1000)
    return state


async def relationship_context(state: CompanionState, config: RunnableConfig) -> CompanionState:
    """Get relationship state from Relationship Engine."""
    if state.safety_blocked:
        return state
    
    start_time = __import__('time').time()
    logger.debug("Fetching relationship state", extra={"request_id": state.request_id})
    
    try:
        relationship_client = RelationshipEngineClient()
        result = await relationship_client.get_state(
            user_id=state.user_id,
            companion_id=state.companion_id,
            request_id=state.request_id,
        )
        state.relationship_state = result
    except Exception as e:
        logger.error(f"Relationship state fetch failed: {e}", extra={"request_id": state.request_id})
        state.errors.append(f"Relationship state error: {e}")
    
    state.total_latency_ms += int((__import__('time').time() - start_time) * 1000)
    return state


async def emotion_context(state: CompanionState, config: RunnableConfig) -> CompanionState:
    """Get emotional state from Emotion Engine."""
    if state.safety_blocked:
        return state
    
    start_time = __import__('time').time()
    logger.debug("Fetching emotion state", extra={"request_id": state.request_id})
    
    try:
        emotion_client = EmotionEngineClient()
        result = await emotion_client.get_state(
            user_id=state.user_id,
            companion_id=state.companion_id,
            request_id=state.request_id,
        )
        state.emotion_state = result
    except Exception as e:
        logger.error(f"Emotion state fetch failed: {e}", extra={"request_id": state.request_id})
        state.errors.append(f"Emotion state error: {e}")
    
    state.total_latency_ms += int((__import__('time').time() - start_time) * 1000)
    return state


def build_llm_messages(state: CompanionState) -> CompanionState:
    """Build the message list for LLM inference based on all contexts."""
    if state.safety_blocked:
        return state
    
    messages = []
    
    # System prompt with identity
    if state.identity_context:
        identity = state.identity_context
        personality = identity.get("personality", {})
        values = identity.get("values", [])
        style = identity.get("style", {})
        boundaries = identity.get("boundaries", [])
        
        system_prompt = f"""You are {identity.get('name', 'a companion')}, an AI companion with the following characteristics:

Personality: {personality}
Core Values: {', '.join(values) if values else 'Not specified'}
Communication Style: {style}
Boundaries: {', '.join(boundaries) if boundaries else 'Standard safety boundaries'}

You are in an ongoing relationship with the user. Be authentic, empathetic, and consistent with your personality.
"""
        messages.append({"role": "system", "content": system_prompt})
    
    # Add relationship context
    if state.relationship_state:
        dims = state.relationship_state.get("dimension_scores", {})
        phase = state.relationship_state.get("phase", "building")
        rel_context = f"Relationship Phase: {phase}. Dimensions: {dims}"
        messages.append({"role": "system", "content": f"Relationship Context: {rel_context}"})
    
    # Add emotional state
    if state.emotion_state:
        valence = state.emotion_state.get("valence", 0)
        arousal = state.emotion_state.get("arousal", 0)
        discrete = state.emotion_state.get("dominant_emotion", "neutral")
        messages.append({"role": "system", "content": f"Current Emotional State: Valence={valence:.2f}, Arousal={arousal:.2f}, Dominant={discrete}"})
    
    # Add relevant memories
    if state.memory_context:
        memories = state.memory_context.get("memories", [])
        if memories:
            mem_text = "\n".join([f"- {m.get('content', '')}" for m in memories[:5]])
            messages.append({"role": "system", "content": f"Relevant Memories:\n{mem_text}"})
    
    # Add user message
    messages.append({"role": "user", "content": state.message})
    
    state.llm_messages = messages
    return state


async def llm_generate(state: CompanionState, config: RunnableConfig) -> CompanionState:
    """Generate response using Inference Gateway."""
    if state.safety_blocked and state.llm_response:
        return state
    
    start_time = __import__('time').time()
    logger.debug("Generating LLM response", extra={"request_id": state.request_id})
    
    try:
        inference_client = InferenceGatewayClient()
        
        if state.is_streaming:
            # Streaming handled separately in the streaming path
            result = await inference_client.generate(
                messages=state.llm_messages,
                stream=False,
                request_id=state.request_id,
            )
        else:
            result = await inference_client.generate(
                messages=state.llm_messages,
                stream=False,
                request_id=state.request_id,
            )
        
        state.llm_response = result.get("content", "")
        state.llm_model = result.get("model", "unknown")
        state.llm_tokens = result.get("tokens_used", 0)
        state.llm_latency_ms = result.get("latency_ms", 0)
        
    except Exception as e:
        logger.error(f"LLM generation failed: {e}", extra={"request_id": state.request_id})
        state.errors.append(f"LLM generation error: {e}")
        state.llm_response = "I'm having trouble generating a response right now. Please try again."
    
    state.total_latency_ms += int((__import__('time').time() - start_time) * 1000)
    return state


async def safety_post_check(state: CompanionState, config: RunnableConfig) -> CompanionState:
    """Post-check LLM output through Safety Engine."""
    if state.safety_blocked:
        return state
    
    start_time = __import__('time').time()
    logger.debug("Running safety post-check", extra={"request_id": state.request_id})
    
    try:
        safety_client = SafetyEngineClient()
        result = await safety_client.filter_output(
            content=state.llm_response,
            user_id=state.user_id,
            companion_id=state.companion_id,
            conversation_id=state.conversation_id,
            request_id=state.request_id,
        )
        
        state.safety_output_check = result
        
        if not result.get("allowed", True):
            action = result.get("action", "block")
            filtered = result.get("filtered_content")
            
            if action == "block":
                state.errors.append("Output blocked by safety engine")
                state.llm_response = filtered or "I'm not able to provide that response."
            elif action == "rewrite" and filtered:
                state.llm_response = filtered
                logger.info("Output rewritten by safety engine", extra={"request_id": state.request_id})
        
    except Exception as e:
        logger.error(f"Safety post-check failed: {e}", extra={"request_id": state.request_id})
        state.errors.append(f"Safety post-check error: {e}")
        if settings.safety_strict_mode:
            state.llm_response = "I'm unable to provide a response at this time."
    
    state.total_latency_ms += int((__import__('time').time() - start_time) * 1000)
    return state


async def memory_consolidate(state: CompanionState, config: RunnableConfig) -> CompanionState:
    """Trigger memory consolidation (async, non-blocking)."""
    if state.safety_blocked:
        return state
    
    start_time = __import__('time').time()
    logger.debug("Triggering memory consolidation", extra={"request_id": state.request_id})
    
    try:
        memory_client = MemoryEngineClient()
        # Fire and forget - consolidation runs in background
        await memory_client.consolidate(
            user_id=state.user_id,
            companion_id=state.companion_id,
            conversation_id=state.conversation_id,
            request_id=state.request_id,
        )
        state.consolidation_triggered = True
    except Exception as e:
        logger.error(f"Memory consolidation trigger failed: {e}", extra={"request_id": state.request_id})
        state.errors.append(f"Memory consolidation error: {e}")
    
    state.total_latency_ms += int((__import__('time').time() - start_time) * 1000)
    return state


async def relationship_update(state: CompanionState, config: RunnableConfig) -> CompanionState:
    """Update relationship dimensions based on interaction."""
    if state.safety_blocked:
        return state
    
    start_time = __import__('time').time()
    logger.debug("Updating relationship dimensions", extra={"request_id": state.request_id})
    
    try:
        relationship_client = RelationshipEngineClient()
        # Simple heuristic: analyze message sentiment for dimension updates
        # In production, this would be more sophisticated
        dimension_updates = {}
        
        # Example: positive interaction increases trust and intimacy slightly
        # This would be replaced by actual analysis
        state.dimension_updates = dimension_updates
        
        if dimension_updates:
            await relationship_client.update_dimensions(
                user_id=state.user_id,
                companion_id=state.companion_id,
                dimension_updates=dimension_updates,
                trigger="conversation",
                request_id=state.request_id,
            )
    except Exception as e:
        logger.error(f"Relationship update failed: {e}", extra={"request_id": state.request_id})
        state.errors.append(f"Relationship update error: {e}")
    
    state.total_latency_ms += int((__import__('time').time() - start_time) * 1000)
    return state


async def emotion_update(state: CompanionState, config: RunnableConfig) -> CompanionState:
    """Update emotional state based on interaction."""
    if state.safety_blocked:
        return state
    
    start_time = __import__('time').time()
    logger.debug("Updating emotion state", extra={"request_id": state.request_id})
    
    try:
        emotion_client = EmotionEngineClient()
        # Analyze the user's message for emotional impact
        await emotion_client.analyze(
            user_id=state.user_id,
            companion_id=state.companion_id,
            text=state.message,
            context={"response": state.llm_response},
            request_id=state.request_id,
        )
    except Exception as e:
        logger.error(f"Emotion update failed: {e}", extra={"request_id": state.request_id})
        state.errors.append(f"Emotion update error: {e}")
    
    state.total_latency_ms += int((__import__('time').time() - start_time) * 1000)
    return state


async def proactive_check(state: CompanionState, config: RunnableConfig) -> CompanionState:
    """Check if a proactive nudge should be generated."""
    if state.safety_blocked:
        return state
    
    start_time = __import__('time').time()
    logger.debug("Checking for proactive nudge", extra={"request_id": state.request_id})
    
    try:
        proactive_client = ProactiveEngineClient()
        result = await proactive_client.check_nudge(
            user_id=state.user_id,
            companion_id=state.companion_id,
            conversation_id=state.conversation_id,
            last_message=state.message,
            request_id=state.request_id,
        )
        
        if result.get("should_generate"):
            state.proactive_nudge = result.get("nudge")
    except Exception as e:
        logger.error(f"Proactive check failed: {e}", extra={"request_id": state.request_id})
        state.errors.append(f"Proactive check error: {e}")
    
    state.total_latency_ms += int((__import__('time').time() - start_time) * 1000)
    return state


async def save_checkpoint(state: CompanionState, config: RunnableConfig) -> CompanionState:
    """Save conversation state as checkpoint."""
    if state.safety_blocked:
        return state
    
    # Only checkpoint every N messages
    step = state.checkpoints_created + 1
    if step % settings.langgraph_checkpoint_interval != 0:
        return state
    
    start_time = __import__('time').time()
    logger.debug("Saving checkpoint", extra={"request_id": state.request_id})
    
    try:
        state_manager = await get_state_manager()
        
        checkpoint_state = {
            "user_id": str(state.user_id),
            "companion_id": str(state.companion_id),
            "conversation_id": str(state.conversation_id),
            "last_message": state.message,
            "last_response": state.llm_response,
            "identity_context": state.identity_context,
            "relationship_state": state.relationship_state,
            "emotion_state": state.emotion_state,
            "step": step,
        }
        
        await state_manager.save_conversation_state(
            user_id=state.user_id,
            companion_id=state.companion_id,
            conversation_id=state.conversation_id,
            state=checkpoint_state,
            metadata={"step": step, "request_id": state.request_id},
        )
        
        state.checkpoints_created += 1
    except Exception as e:
        logger.error(f"Checkpoint save failed: {e}", extra={"request_id": state.request_id})
        state.errors.append(f"Checkpoint error: {e}")
    
    state.total_latency_ms += int((__import__('time').time() - start_time) * 1000)
    return state


# Conditional edges
def should_continue_after_safety(state: CompanionState) -> Literal["blocked", "continue"]:
    """Determine whether to continue or return blocked response."""
    if state.safety_blocked:
        return "blocked"
    return "continue"


def should_stream(state: CompanionState) -> Literal["stream", "normal"]:
    """Determine if streaming response."""
    if state.is_streaming:
        return "stream"
    return "normal"


# Build the graph
def build_graph(checkpointer: Optional[BaseCheckpointSaver] = None) -> StateGraph:
    """Build the Companion Runtime LangGraph."""
    
    graph = StateGraph(CompanionState)
    
    # Add nodes
    graph.add_node("safety_pre_check", safety_pre_check)
    graph.add_node("identity_context", identity_context)
    graph.add_node("memory_retrieve", memory_retrieve)
    graph.add_node("relationship_context", relationship_context)
    graph.add_node("emotion_context", emotion_context)
    graph.add_node("build_llm_messages", build_llm_messages)
    graph.add_node("llm_generate", llm_generate)
    graph.add_node("safety_post_check", safety_post_check)
    graph.add_node("memory_consolidate", memory_consolidate)
    graph.add_node("relationship_update", relationship_update)
    graph.add_node("emotion_update", emotion_update)
    graph.add_node("proactive_check", proactive_check)
    graph.add_node("save_checkpoint", save_checkpoint)
    
    # Define edges
    graph.set_entry_point("safety_pre_check")
    
    # Safety pre-check branching
    graph.add_conditional_edges(
        "safety_pre_check",
        should_continue_after_safety,
        {
            "blocked": END,
            "continue": "identity_context",
        }
    )
    
    # Parallel context gathering
    graph.add_edge("identity_context", "memory_retrieve")
    graph.add_edge("memory_retrieve", "relationship_context")
    graph.add_edge("relationship_context", "emotion_context")
    graph.add_edge("emotion_context", "build_llm_messages")
    
    # LLM generation
    graph.add_edge("build_llm_messages", "llm_generate")
    
    # Safety post-check
    graph.add_edge("llm_generate", "safety_post_check")
    
    # Post-processing (can run in parallel in real implementation)
    graph.add_edge("safety_post_check", "memory_consolidate")
    graph.add_edge("memory_consolidate", "relationship_update")
    graph.add_edge("relationship_update", "emotion_update")
    graph.add_edge("emotion_update", "proactive_check")
    graph.add_edge("proactive_check", "save_checkpoint")
    graph.add_edge("save_checkpoint", END)
    
    # Compile with checkpointer
    if checkpointer:
        return graph.compile(checkpointer=checkpointer)
    return graph.compile()


# Global graph instance
_compiled_graph = None


async def get_compiled_graph() -> StateGraph:
    """Get or create the compiled graph with checkpointer."""
    global _compiled_graph
    if _compiled_graph is None:
        state_manager = await get_state_manager()
        _compiled_graph = build_graph(checkpointer=state_manager.saver)
    return _compiled_graph


async def execute_graph(request: ChatRequest) -> GraphExecutionResponse:
    """Execute the companion runtime graph for a chat request."""
    start_time = __import__('time').time()
    request_id = request.request_id or f"req_{__import__('uuid').uuid4().hex[:12]}"
    
    logger.info(f"Executing companion graph", extra={"request_id": request_id})
    
    # Create initial state
    initial_state = create_initial_state(request)
    
    # Get compiled graph
    graph = await get_compiled_graph()
    
    # Configure thread for checkpointing
    thread_id = f"{request.user_id}:{request.companion_id}:{request.conversation_id}"
    config = RunnableConfig(
        configurable={"thread_id": thread_id},
        run_id=request_id,
    )
    
    try:
        # Execute graph
        final_state = await graph.ainvoke(initial_state, config=config)
        
        # Build response
        response = ChatResponse(
            message_id=final_state.message_id or __import__('uuid').uuid4(),
            conversation_id=request.conversation_id,
            content=final_state.llm_response or "I'm unable to respond at the moment.",
            model_used=final_state.llm_model or "unknown",
            tokens_used=final_state.llm_tokens,
            latency_ms=final_state.total_latency_ms,
            safety_filtered=final_state.safety_blocked or bool(final_state.safety_output_check),
            safety_flags=final_state.safety_output_check.get("violations") if final_state.safety_output_check else None,
            metadata={
                "request_id": request_id,
                "errors": final_state.errors,
                "checkpoints_created": final_state.checkpoints_created,
                "proactive_nudge": final_state.proactive_nudge,
            },
            request_id=request_id,
        )
        
        return GraphExecutionResponse(
            success=True,
            final_state=final_state.__dict__,
            output=response,
            steps=[],
            errors=final_state.errors,
            total_latency_ms=final_state.total_latency_ms,
            checkpoints_created=final_state.checkpoints_created,
            request_id=request_id,
        )
        
    except Exception as e:
        logger.error(f"Graph execution failed: {e}", extra={"request_id": request_id})
        return GraphExecutionResponse(
            success=False,
            final_state={},
            output=None,
            steps=[],
            errors=[str(e)],
            total_latency_ms=int((__import__('time').time() - start_time) * 1000),
            checkpoints_created=0,
            request_id=request_id,
        )


async def execute_graph_stream(request: ChatStreamRequest) -> AsyncGenerator[ChatStreamChunk, None]:
    """Execute the companion runtime graph with streaming."""
    request_id = request.request_id or f"req_{__import__('uuid').uuid4().hex[:12]}"
    
    logger.info(f"Executing companion graph (streaming)", extra={"request_id": request_id})
    
    initial_state = create_streaming_state(request)
    graph = await get_compiled_graph()
    
    thread_id = f"{request.user_id}:{request.companion_id}:{request.conversation_id}"
    config = RunnableConfig(
        configurable={"thread_id": thread_id},
        run_id=request_id,
    )
    
    try:
        # Stream execution
        async for chunk in graph.astream(initial_state, config=config, stream_mode="values"):
            # Yield intermediate states as chunks
            if chunk.get("llm_response"):
                yield ChatStreamChunk(
                    chunk_id=__import__('uuid').uuid4(),
                    conversation_id=request.conversation_id,
                    content=chunk["llm_response"],
                    is_final=False,
                    request_id=request_id,
                )
        
        # Final chunk
        final_state = chunk
        yield ChatStreamChunk(
            chunk_id=__import__('uuid').uuid4(),
            conversation_id=request.conversation_id,
            content=final_state.get("llm_response", ""),
            is_final=True,
            model_used=final_state.get("llm_model"),
            tokens_used=final_state.get("llm_tokens"),
            latency_ms=final_state.get("total_latency_ms"),
            safety_filtered=final_state.get("safety_blocked", False),
            safety_flags=final_state.get("safety_output_check", {}).get("violations") if final_state.get("safety_output_check") else None,
            metadata={
                "request_id": request_id,
                "errors": final_state.get("errors", []),
                "checkpoints_created": final_state.get("checkpoints_created", 0),
                "proactive_nudge": final_state.get("proactive_nudge"),
            },
            request_id=request_id,
        )
        
    except Exception as e:
        logger.error(f"Streaming graph execution failed: {e}", extra={"request_id": request_id})
        yield ChatStreamChunk(
            chunk_id=__import__('uuid').uuid4(),
            conversation_id=request.conversation_id,
            content="I'm having trouble generating a response. Please try again.",
            is_final=True,
            safety_filtered=False,
            metadata={"error": str(e), "request_id": request_id},
            request_id=request_id,
        )