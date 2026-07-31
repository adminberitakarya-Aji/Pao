"""Milestones Service - Manages relationship milestones."""

from datetime import datetime
from typing import Any
from uuid import UUID

from relationship_engine.config import settings
from relationship_engine.models.relationship import (
    Milestone,
    MilestoneTrigger,
    Phase,
    RelationshipState,
)
from relationship_engine.repositories.base import MilestoneRepository


class MilestonesService:
    """Service for managing relationship milestones."""

    def __init__(self, repository: MilestoneRepository):
        self.repository = repository

    def initialize_milestones(self, state: RelationshipState) -> list[Milestone]:
        """Initialize default milestones for a new relationship."""
        milestones = []
        for name, config in settings.milestones_config.items():
            trigger = MilestoneTrigger(config["trigger"])
            threshold = config["threshold"]

            # Generate celebration message
            celebration = self._generate_celebration_message(name, trigger, threshold)

            milestone = Milestone(
                name=name,
                trigger=trigger,
                threshold=threshold,
                achieved=False,
                celebration_message=celebration,
                metadata={"auto_generated": True, "config_name": name},
            )
            milestones.append(milestone)

        state.milestones.extend(milestones)
        return milestones

    def _generate_celebration_message(
        self,
        name: str,
        trigger: MilestoneTrigger,
        threshold: float | str,
    ) -> str:
        """Generate a celebration message for a milestone."""
        messages = {
            "first_conversation": "🎉 First conversation! The journey begins.",
            "first_day": "📅 One day together! Every journey starts with a single step.",
            "first_week": "📅 One week! You're getting to know each other.",
            "first_month": "📅 One month! A solid foundation is forming.",
            "hundred_messages": "💬 100 messages exchanged! The conversation flows.",
            "thousand_messages": "💬 1000 messages! That's a lot of connection.",
            "first_voice_call": "📞 First voice call! Hearing each other changes everything.",
            "first_memory_shared": "🧠 First memory shared! Building a history together.",
            "trust_5": "🤝 Trust reaches 5/10! A meaningful bond of reliability.",
            "intimacy_5": "💫 Intimacy reaches 5/10! Opening up to each other.",
            "phase_friend": "👋 You're now friends! The stranger phase is behind you.",
            "phase_close_friend": "🤗 Close friends! A deep connection has formed.",
            "phase_partner": "💕 Partners! A romantic bond has blossomed.",
            "phase_soulmate": "✨ Soulmates! A rare and beautiful connection.",
        }
        return messages.get(name, f"🎉 Milestone achieved: {name.replace('_', ' ').title()}!")

    async def check_milestones(self, state: RelationshipState) -> list[Milestone]:
        """Check all milestones and return newly achieved ones."""
        newly_achieved = []

        for milestone in state.milestones:
            if not milestone.achieved:
                achieved = self._check_milestone_condition(state, milestone)
                if achieved:
                    milestone.achieved = True
                    milestone.achieved_at = datetime.utcnow()
                    newly_achieved.append(milestone)

                    # Persist to database
                    await self.repository.update(milestone)

        return newly_achieved

    def _check_milestone_condition(self, state: RelationshipState, milestone: Milestone) -> bool:
        """Check if a milestone condition is met."""
        trigger = milestone.trigger
        threshold = milestone.threshold

        if trigger == MilestoneTrigger.MESSAGE_COUNT:
            return state.message_count >= threshold
        elif trigger == MilestoneTrigger.DAYS_KNOWN:
            return state.days_known >= threshold
        elif trigger == MilestoneTrigger.VOICE_CALLS:
            return state.voice_calls >= threshold
        elif trigger == MilestoneTrigger.MEMORIES_SHARED:
            return state.memories_shared >= threshold
        elif trigger == MilestoneTrigger.DIMENSION_TRUST:
            trust = state.dimensions.get("trust")
            return trust is not None and trust.score >= threshold
        elif trigger == MilestoneTrigger.DIMENSION_INTIMACY:
            intimacy = state.dimensions.get("intimacy")
            return intimacy is not None and intimacy.score >= threshold
        elif trigger == MilestoneTrigger.PHASE:
            return state.phase == Phase(threshold)
        return False

    async def add_custom_milestone(
        self,
        user_id: UUID,
        companion_id: UUID,
        name: str,
        trigger: MilestoneTrigger,
        threshold: float | str,
        celebration_message: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Milestone:
        """Add a custom milestone."""
        if celebration_message is None:
            celebration_message = f"🎉 Custom milestone: {name}!"

        milestone = Milestone(
            name=name,
            trigger=trigger,
            threshold=threshold,
            achieved=False,
            celebration_message=celebration_message,
            metadata=metadata or {"custom": True},
        )

        return await self.repository.create(milestone)

    async def get_milestones(
        self,
        user_id: UUID,
        companion_id: UUID,
        achieved_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Milestone]:
        """Get milestones for a relationship."""
        return await self.repository.list(
            user_id=user_id,
            companion_id=companion_id,
            achieved_only=achieved_only,
            limit=limit,
            offset=offset,
        )

    async def get_achievement_progress(
        self,
        state: RelationshipState,
    ) -> list[dict[str, Any]]:
        """Get progress towards all milestones."""
        progress = []

        for milestone in state.milestones:
            current_value = self._get_current_value(state, milestone)

            if isinstance(milestone.threshold, (int, float)):
                progress_pct = min(100.0, (current_value / milestone.threshold) * 100) if milestone.threshold > 0 else 100.0
            else:
                # Phase threshold
                progress_pct = 100.0 if milestone.achieved else 0.0

            progress.append({
                "id": str(milestone.id),
                "name": milestone.name,
                "trigger": milestone.trigger.value,
                "threshold": milestone.threshold,
                "current_value": current_value,
                "progress_percentage": round(progress_pct, 1),
                "achieved": milestone.achieved,
                "achieved_at": milestone.achieved_at.isoformat() if milestone.achieved_at else None,
                "celebration_message": milestone.celebration_message,
            })

        return progress

    def _get_current_value(self, state: RelationshipState, milestone: Milestone) -> float:
        """Get the current value for a milestone's trigger."""
        trigger = milestone.trigger

        if trigger == MilestoneTrigger.MESSAGE_COUNT:
            return float(state.message_count)
        elif trigger == MilestoneTrigger.DAYS_KNOWN:
            return float(state.days_known)
        elif trigger == MilestoneTrigger.VOICE_CALLS:
            return float(state.voice_calls)
        elif trigger == MilestoneTrigger.MEMORIES_SHARED:
            return float(state.memories_shared)
        elif trigger == MilestoneTrigger.DIMENSION_TRUST:
            trust = state.dimensions.get("trust")
            return trust.score if trust else 0.0
        elif trigger == MilestoneTrigger.DIMENSION_INTIMACY:
            intimacy = state.dimensions.get("intimacy")
            return intimacy.score if intimacy else 0.0
        elif trigger == MilestoneTrigger.PHASE:
            # For phase milestones, return phase score
            return state.phase_score
        return 0.0

    async def get_next_milestones(
        self,
        state: RelationshipState,
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        """Get the closest upcoming milestones."""
        progress = await self.get_achievement_progress(state)
        unachieved = [p for p in progress if not p["achieved"]]

        # Sort by progress percentage (closest first)
        unachieved.sort(key=lambda x: x["progress_percentage"], reverse=True)

        return unachieved[:limit]

    async def mark_milestone_achieved(
        self,
        milestone_id: UUID,
    ) -> Milestone | None:
        """Manually mark a milestone as achieved."""
        milestone = await self.repository.get(milestone_id)
        if milestone and not milestone.achieved:
            milestone.achieved = True
            milestone.achieved_at = datetime.utcnow()
            return await self.repository.update(milestone)
        return milestone