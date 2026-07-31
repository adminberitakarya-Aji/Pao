"""Relationship Engine Worker - Background tasks for diary generation, milestone checking, etc."""

import asyncio
import logging
import signal
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from relationship_engine.config import settings
from relationship_engine.repositories.postgres import (
    create_engine_and_session,
    PostgresRelationshipRepository,
    PostgresMilestoneRepository,
    PostgresDiaryRepository,
    PostgresStateTransitionRepository,
)
from relationship_engine.services.relationship_service import RelationshipService
from relationship_engine.models.relationship import RelationshipState

logger = logging.getLogger(__name__)


class RelationshipWorker:
    """Background worker for relationship engine tasks."""

    def __init__(self, concurrency: int = 2):
        self.concurrency = concurrency
        self.running = False
        self.tasks: list[asyncio.Task] = []
        self.session_factory = None
        self.engine = None
        self.service: Optional[RelationshipService] = None

    async def start(self):
        """Start the worker."""
        logger.info("Starting Relationship Engine Worker...")

        # Initialize database
        self.engine, self.session_factory = await create_engine_and_session()

        # Create repositories
        relationship_repo = PostgresRelationshipRepository(self.session_factory)
        milestone_repo = PostgresMilestoneRepository(self.session_factory)
        diary_repo = PostgresDiaryRepository(self.session_factory)
        transition_repo = PostgresStateTransitionRepository(self.session_factory)

        # Create service
        self.service = RelationshipService(
            relationship_repo=relationship_repo,
            milestone_repo=milestone_repo,
            diary_repo=diary_repo,
            transition_repo=transition_repo,
        )

        self.running = True

        # Start background tasks
        self.tasks = [
            asyncio.create_task(self._diary_generation_loop()),
            asyncio.create_task(self._milestone_check_loop()),
            asyncio.create_task(self._daily_decay_loop()),
            asyncio.create_task(self._cleanup_loop()),
        ]

        logger.info(f"Worker started with {self.concurrency} concurrent tasks")

        # Wait for all tasks
        await asyncio.gather(*self.tasks, return_exceptions=True)

    async def stop(self):
        """Stop the worker gracefully."""
        logger.info("Stopping Relationship Engine Worker...")
        self.running = False

        # Cancel all tasks
        for task in self.tasks:
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)

        # Close database connections
        if self.engine:
            await self.engine.dispose()

        logger.info("Worker stopped")

    async def _diary_generation_loop(self):
        """Periodically generate diary entries for active relationships."""
        while self.running:
            try:
                await self._generate_diary_entries()
            except Exception as e:
                logger.error(f"Error in diary generation loop: {e}")

            # Wait before next run (every 6 hours)
            await asyncio.sleep(6 * 3600)

    async def _milestone_check_loop(self):
        """Periodically check milestones for all relationships."""
        while self.running:
            try:
                await self._check_all_milestones()
            except Exception as e:
                logger.error(f"Error in milestone check loop: {e}")

            # Wait before next run (every hour)
            await asyncio.sleep(3600)

    async def _daily_decay_loop(self):
        """Apply daily decay to relationship dimensions."""
        while self.running:
            try:
                await self._apply_daily_decay()
            except Exception as e:
                logger.error(f"Error in daily decay loop: {e}")

            # Wait until next day (run at midnight UTC)
            now = datetime.utcnow()
            tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            wait_seconds = (tomorrow - now).total_seconds()
            await asyncio.sleep(wait_seconds)

    async def _cleanup_loop(self):
        """Periodic cleanup tasks."""
        while self.running:
            try:
                await self._cleanup_old_data()
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

            # Wait 24 hours
            await asyncio.sleep(24 * 3600)

    async def _generate_diary_entries(self):
        """Generate diary entries for relationships with recent activity."""
        logger.info("Starting diary generation...")

        # Get all active relationships (interacted in last 7 days)
        cutoff = datetime.utcnow() - timedelta(days=7)
        
        async with self.session_factory() as session:
            from sqlalchemy import select
            from relationship_engine.repositories.postgres import RelationshipModel
            
            # Query relationships with recent activity
            query = select(RelationshipModel).where(
                RelationshipModel.last_interaction_at >= cutoff
            )
            result = await session.execute(query)
            relationships = result.scalars().all()

        for rel_model in relationships:
            try:
                # Get full state
                state = await self.service.relationship_repo.get(
                    rel_model.user_id, rel_model.companion_id
                )
                if not state:
                    continue

                # Generate weekly summary (last 7 days)
                period_end = datetime.utcnow()
                period_start = period_end - timedelta(days=7)

                entry = await self.service.generate_diary_entry(
                    user_id=state.user_id,
                    companion_id=state.companion_id,
                    period_start=period_start,
                    period_end=period_end,
                )

                if entry:
                    logger.info(
                        f"Generated diary entry for {state.user_id}:{state.companion_id} - {entry.entry.title}"
                    )

            except Exception as e:
                logger.error(
                    f"Failed to generate diary for {rel_model.user_id}:{rel_model.companion_id}: {e}"
                )

        logger.info("Diary generation complete")

    async def _check_all_milestones(self):
        """Check milestones for all active relationships."""
        logger.info("Starting milestone check...")

        async with self.session_factory() as session:
            from sqlalchemy import select
            from relationship_engine.repositories.postgres import RelationshipModel
            
            query = select(RelationshipModel)
            result = await session.execute(query)
            relationships = result.scalars().all()

        for rel_model in relationships:
            try:
                state = await self.service.relationship_repo.get(
                    rel_model.user_id, rel_model.companion_id
                )
                if not state:
                    continue

                # Check milestones (this is also done on dimension updates)
                new_milestones = await self.service.milestones_service.check_milestones(state)
                
                if new_milestones:
                    logger.info(
                        f"New milestones for {state.user_id}:{state.companion_id}: "
                        f"{[m.name for m in new_milestones]}"
                    )

            except Exception as e:
                logger.error(
                    f"Failed to check milestones for {rel_model.user_id}:{rel_model.companion_id}: {e}"
                )

        logger.info("Milestone check complete")

    async def _apply_daily_decay(self):
        """Apply daily decay to all relationship dimensions."""
        logger.info("Applying daily decay...")

        async with self.session_factory() as session:
            from sqlalchemy import select
            from relationship_engine.repositories.postgres import RelationshipModel
            
            query = select(RelationshipModel)
            result = await session.execute(query)
            relationships = result.scalars().all()

        for rel_model in relationships:
            try:
                state = await self.service.relationship_repo.get(
                    rel_model.user_id, rel_model.companion_id
                )
                if not state:
                    continue

                # Apply decay
                updated = self.service.dimensions_service.apply_daily_decay(state, days=1)
                
                if updated:
                    await self.service.relationship_repo.update(state)
                    logger.debug(
                        f"Applied decay to {state.user_id}:{state.companion_id} "
                        f"({len(updated)} dimensions updated)"
                    )

            except Exception as e:
                logger.error(
                    f"Failed to apply decay for {rel_model.user_id}:{rel_model.companion_id}: {e}"
                )

        logger.info("Daily decay complete")

    async def _cleanup_old_data(self):
        """Clean up old data based on retention policies."""
        logger.info("Running cleanup...")

        # Clean up old state transitions (keep last 100 per relationship)
        # This would be implemented with a raw SQL query for efficiency
        # For now, just log
        logger.info("Cleanup complete")


async def main():
    """Main entry point for the worker."""
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    worker = RelationshipWorker(concurrency=settings.worker_concurrency)

    # Handle shutdown signals
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(worker.stop()))

    try:
        await worker.start()
    except Exception as e:
        logger.exception(f"Worker failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())