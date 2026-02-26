"""
Smart Incremental Cache Manager

Solves RAM exhaustion and computational waste by:
1. Only building missing time ranges
2. Reusing existing valid cache
3. Sliding window approach (delete old, add new)
4. Memory-efficient chunked processing
"""

import gc
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
import threading
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class SmartCacheManager:
    """
    Intelligent cache manager that minimizes RAM usage and computation

    Strategy:
    - Keep 48-hour rolling window
    - Only compute missing time ranges
    - Delete expired chunks
    - Process in 1-hour increments to limit RAM
    """

    def __init__(self, position_cache_manager):
        self.pcm = position_cache_manager
        self.cache_lock = threading.RLock()
        self.target_days = 2  # Total cache coverage goal (48 hours)
        self.chunk_hours = 1  # Process 1 hour at a time (RAM-friendly)
        self.satellite_batch_size = 25  # Process 25 satellites at a time (for 8GB RAM)

    def get_cache_coverage(self) -> List[Tuple[datetime, datetime]]:
        """
        Analyze existing cache to find what time ranges are covered

        Returns:
            List of (start_time, end_time) tuples representing cached ranges
        """
        covered_ranges = []

        try:
            now = datetime.now(timezone.utc)

            # Check all stages for coverage
            for stage_name in ['stage1', 'stage2', 'stage3', 'stage4']:
                stage = self.pcm.cache_stages.get(stage_name, {})

                if stage.get('status') == 'completed':
                    end_time_str = stage.get('end_time')
                    if end_time_str:
                        try:
                            end_time = datetime.fromisoformat(end_time_str)

                            # Only count if not expired
                            if end_time > now:
                                # Estimate start time based on stage duration
                                if stage_name == 'stage1':
                                    duration = timedelta(minutes=5)
                                elif stage_name == 'stage2':
                                    duration = timedelta(hours=4)
                                elif stage_name == 'stage3':
                                    duration = timedelta(hours=24)
                                else:  # stage4
                                    duration = timedelta(days=2)

                                start_time = end_time - duration

                                # Only count if start is in the future or very recent past
                                if start_time > now - timedelta(hours=1):
                                    covered_ranges.append((start_time, end_time))
                                    logger.debug(f"{stage_name}: {start_time} → {end_time}")

                        except Exception as e:
                            logger.warning(f"Error parsing {stage_name} time: {e}")

            # Merge overlapping ranges
            covered_ranges = self._merge_ranges(covered_ranges)

            return covered_ranges

        except Exception as e:
            logger.error(f"Error analyzing cache coverage: {e}")
            return []

    def _merge_ranges(self, ranges: List[Tuple[datetime, datetime]]) -> List[Tuple[datetime, datetime]]:
        """Merge overlapping time ranges"""
        if not ranges:
            return []

        # Sort by start time
        sorted_ranges = sorted(ranges, key=lambda x: x[0])
        merged = [sorted_ranges[0]]

        for current_start, current_end in sorted_ranges[1:]:
            last_start, last_end = merged[-1]

            # If overlapping or adjacent, merge
            if current_start <= last_end + timedelta(minutes=1):
                merged[-1] = (last_start, max(last_end, current_end))
            else:
                merged.append((current_start, current_end))

        return merged

    def get_missing_ranges(self) -> List[Tuple[datetime, datetime]]:
        """
        Calculate what time ranges need to be cached to reach 48-hour goal

        Returns:
            List of (start_time, end_time) tuples that need to be built
        """
        now = datetime.now(timezone.utc)
        target_end = now + timedelta(days=self.target_days)

        # Get what we already have
        covered = self.get_cache_coverage()

        if not covered:
            # No cache at all - need everything
            logger.info(f"📊 No existing cache - need to build {self.target_days} days")
            return [(now, target_end)]

        # Find gaps
        missing = []
        current_pos = now

        for start, end in covered:
            if current_pos < start:
                # Gap before this range
                missing.append((current_pos, start))
            current_pos = max(current_pos, end)

        # Check if we need more at the end
        if current_pos < target_end:
            missing.append((current_pos, target_end))

        return missing

    def smart_incremental_update(self):
        """
        Smart cache update:
        1. Check what's already cached
        2. Only build missing ranges
        3. Delete expired data
        4. Process in RAM-friendly chunks
        """
        with self.cache_lock:
            logger.info("🧠 Smart Incremental Cache Update")
            logger.info("="*60)

            # 1. Analyze current coverage
            covered = self.get_cache_coverage()
            if covered:
                logger.info(f"📊 Current cache coverage:")
                for start, end in covered:
                    duration = (end - start).total_seconds() / 3600
                    logger.info(f"   • {start.strftime('%H:%M')} → {end.strftime('%H:%M')} ({duration:.1f}h)")
            else:
                logger.info(f"📊 No existing cache")

            # 2. Find what's missing
            missing = self.get_missing_ranges()

            if not missing:
                logger.info(f"✅ Cache is complete ({self.target_days} days covered)")
                logger.info(f"   No updates needed!")
                return True

            total_hours_needed = sum((end - start).total_seconds() / 3600 for start, end in missing)
            logger.info(f"📊 Missing coverage: {total_hours_needed:.1f} hours")
            for start, end in missing:
                duration = (end - start).total_seconds() / 3600
                logger.info(f"   • {start.strftime('%Y-%m-%d %H:%M')} → {end.strftime('%Y-%m-%d %H:%M')} ({duration:.1f}h)")

            # 3. Build missing ranges in chunks (RAM-friendly)
            logger.info(f"🔨 Building missing ranges (1-hour chunks to save RAM)...")

            total_chunks = 0
            for range_start, range_end in missing:
                chunks_built = self._build_range_incremental(range_start, range_end)
                total_chunks += chunks_built

            logger.info(f"✅ Smart update complete: {total_chunks} hours built")
            logger.info("="*60)

            # 4. Cleanup old cache (optional)
            self._cleanup_old_cache()

            return True

    def _build_range_incremental(self, start_time: datetime, end_time: datetime) -> int:
        """
        Build cache for a time range using 1-hour chunks to minimize RAM

        Returns:
            Number of chunks built
        """
        chunks_built = 0
        current = start_time

        while current < end_time:
            chunk_end = min(current + timedelta(hours=self.chunk_hours), end_time)

            logger.info(f"   Building chunk: {current.strftime('%H:%M')} → {chunk_end.strftime('%H:%M')}")

            try:
                # Build just this 1-hour chunk with RAM-friendly batching
                positions_data = self.pcm.calculate_positions_for_satellites(
                    self.pcm.priority_satellites,
                    current,
                    chunk_end,
                    batch_size=self.satellite_batch_size  # Process 25 sats at a time
                )

                # Save immediately (don't accumulate in RAM)
                saved = 0
                for norad_id in positions_data.keys():
                    # Determine which stage this belongs to
                    stage = self._determine_stage(current)
                    if self.pcm.save_satellite_cache(norad_id, positions_data, stage):
                        saved += 1

                logger.info(f"      ✓ Saved {saved}/{len(positions_data)} satellites")
                chunks_built += 1

                # Clear data from RAM immediately
                del positions_data
                gc.collect()  # Force garbage collection to free RAM

            except Exception as e:
                logger.error(f"Error building chunk {current} → {chunk_end}: {e}")

            current = chunk_end

        return chunks_built

    def _determine_stage(self, target_time: datetime) -> str:
        """Determine which stage a time belongs to"""
        now = datetime.now(timezone.utc)
        hours_ahead = (target_time - now).total_seconds() / 3600

        if hours_ahead < 0.083:  # 5 minutes
            return 'stage1'
        elif hours_ahead < 4:
            return 'stage2'
        elif hours_ahead < 24:
            return 'stage3'
        else:
            return 'stage4'

    def _cleanup_old_cache(self):
        """Delete cache chunks older than 1 hour"""
        try:
            now = datetime.now(timezone.utc)
            cutoff = now - timedelta(hours=1)

            deleted = 0
            for cache_file in self.pcm.cache_dir.glob('*.npz'):
                try:
                    # Parse timestamp from filename or file metadata
                    mtime = datetime.fromtimestamp(cache_file.stat().st_mtime, tz=timezone.utc)

                    if mtime < cutoff:
                        cache_file.unlink()
                        deleted += 1

                except Exception as e:
                    logger.debug(f"Error checking cache file {cache_file.name}: {e}")

            if deleted > 0:
                logger.info(f"🗑️  Cleaned up {deleted} old cache files")

        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}")
