"""
Smart Sliding Window Cache Manager

Builds complete 48-hour cache once, then maintains it with efficient sliding window updates.
Adds 2 hours every 1.5 hours, deletes oldest 2 hours = always 48 hours cached.
"""

import gc
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SlidingWindowCache:
    """
    Intelligent sliding window cache manager

    Strategy:
    - First run: Build complete 48-hour cache
    - Maintenance: Every 1.5 hours, delete oldest 2 hours and add newest 2 hours
    - Result: Always have exactly 48 hours of cache with minimal computation
    """

    def __init__(self, position_cache_manager):
        self.pcm = position_cache_manager
        self.cache_days = 2  # Total cache coverage (48 hours)
        self.chunk_hours = 2  # Build 2 hours at a time
        self.slide_interval_hours = 1.5  # Update frequency
        self.batch_size = 10  # Satellites per batch for RAM management (reduced for prototype)

        # Metadata file to track state
        self.metadata_file = Path('cache/sliding_window_metadata.json')
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)

        # Load existing state
        self.metadata = self._load_metadata()
        self.is_initialized = self.metadata.get('initialized', False)
        self.last_slide = None
        if self.metadata.get('last_slide'):
            try:
                self.last_slide = datetime.fromisoformat(self.metadata['last_slide'])
            except:
                pass

    def _load_metadata(self):
        """Load cache metadata"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_metadata(self):
        """Save cache metadata"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")

    def initial_build(self):
        """
        Build complete 48-hour cache (one time only)

        Returns:
            bool: True if successful
        """
        now = datetime.now(timezone.utc)
        end_time = now + timedelta(days=self.cache_days)

        print(f"\n{'='*70}")
        print(f"[INIT] Building initial {self.cache_days}-day cache...")
        print(f"[RANGE] {now.strftime('%b %d, %Y %H:%M UTC')} -> {end_time.strftime('%b %d, %Y %H:%M UTC')}")
        print(f"{'='*70}\n")

        total_hours = self.cache_days * 24
        hours_built = 0
        chunks_completed = 0
        total_chunks = int(total_hours / self.chunk_hours)

        current = now
        while current < end_time:
            chunk_end = min(current + timedelta(hours=self.chunk_hours), end_time)

            # Build this chunk
            try:
                self._build_chunk(current, chunk_end)
                hours_built += self.chunk_hours
                chunks_completed += 1

                # Progress update
                progress = int((hours_built / total_hours) * 100)
                elapsed_str = f"{current.strftime('%b %d %H:%M')} -> {chunk_end.strftime('%b %d %H:%M')}"
                print(f"[PROGRESS] Chunk {chunks_completed}/{total_chunks} | "
                      f"{hours_built}/{total_hours}h ({progress}%) | {elapsed_str}")

            except Exception as e:
                logger.error(f"Error building chunk {current} -> {chunk_end}: {e}")
                # Continue with next chunk

            current = chunk_end

        # Mark as initialized
        self.is_initialized = True
        self.last_slide = datetime.now(timezone.utc)

        # Save metadata
        self.metadata = {
            'initialized': True,
            'cache_days': self.cache_days,
            'last_slide': self.last_slide.isoformat(),
            'initial_build_completed': datetime.now(timezone.utc).isoformat(),
            'total_hours': total_hours
        }
        self._save_metadata()

        print(f"\n{'='*70}")
        print(f"[COMPLETE] {self.cache_days}-day cache ready! ({total_hours} hours)")
        print(f"[NEXT] Spatial index will now build...")
        print(f"{'='*70}\n")

        return True

    def sliding_update(self):
        """
        Sliding window maintenance: Add 2 hours, delete oldest 2 hours

        If cache is too old (gap > 12 hours), triggers full rebuild instead.

        Returns:
            bool: True if update performed
        """
        # If not initialized, do initial build
        if not self.is_initialized:
            logger.info("Cache not initialized, performing initial build...")
            return self.initial_build()

        now = datetime.now(timezone.utc)

        # Check if it's time to slide
        if self.last_slide:
            hours_since_slide = (now - self.last_slide).total_seconds() / 3600
            if hours_since_slide < self.slide_interval_hours:
                logger.debug(f"Not time to slide yet ({hours_since_slide:.1f}h < {self.slide_interval_hours}h)")
                return False

            # CRITICAL: If gap is too large (>12 hours), cache is out of date - do full rebuild
            if hours_since_slide > 12:
                print(f"\n[WARNING] Cache is {hours_since_slide:.1f} hours out of date (last update: {self.last_slide.strftime('%b %d %H:%M')})")
                print(f"[REBUILD] Gap too large, performing full 48-hour rebuild instead of sliding update...")

                # Clear out-of-date cache
                deleted = 0
                for cache_file in self.pcm.cache_dir.glob('sliding_*.npz'):
                    try:
                        cache_file.unlink()
                        deleted += 1
                    except:
                        pass
                print(f"[CLEAN] Removed {deleted} out-of-date files")

                # Reset metadata
                self.is_initialized = False
                self.last_slide = None
                self.metadata = {}
                self._save_metadata()

                # Do full rebuild
                return self.initial_build()

        print(f"\n[MAINTAIN] Sliding window update at {now.strftime('%b %d, %Y %H:%M UTC')}")

        # Calculate time ranges
        cache_start = now  # Current cache starts now
        cache_end = now + timedelta(days=self.cache_days)  # And extends 48 hours

        # Delete oldest chunk (before current time)
        delete_start = now - timedelta(hours=self.chunk_hours)
        delete_end = now
        deleted = self._delete_chunk(delete_start, delete_end)
        print(f"[DELETE] Removed {deleted} old files: "
              f"{delete_start.strftime('%b %d %H:%M')} -> {delete_end.strftime('%b %d %H:%M')}")

        # Add newest chunk (at the end of 48 hours)
        add_start = cache_end
        add_end = cache_end + timedelta(hours=self.chunk_hours)
        try:
            self._build_chunk(add_start, add_end)
            print(f"[BUILD] Added 2 hours: "
                  f"{add_start.strftime('%b %d %H:%M')} -> {add_end.strftime('%b %d %H:%M')}")
        except Exception as e:
            logger.error(f"Error adding new chunk: {e}")

        # Update metadata
        self.last_slide = now
        self.metadata['last_slide'] = now.isoformat()
        self.metadata['last_update'] = now.isoformat()
        self._save_metadata()

        print(f"[COMPLETE] 48-hour cache maintained ({self.cache_days * 24} hours)\n")
        return True

    def _build_chunk(self, start_time: datetime, end_time: datetime):
        """
        Build cache for a time chunk

        Args:
            start_time: Start of chunk
            end_time: End of chunk
        """
        logger.debug(f"Building chunk: {start_time} -> {end_time}")

        # Calculate positions with RAM-friendly batching
        positions_data = self.pcm.calculate_positions_for_satellites(
            self.pcm.priority_satellites,
            start_time,
            end_time,
            batch_size=self.batch_size
        )

        # Save to cache
        saved = 0
        for norad_id in positions_data.keys():
            if self.pcm.save_satellite_cache(norad_id, positions_data, 'sliding'):
                saved += 1

        logger.debug(f"Saved {saved}/{len(positions_data)} satellites")

        # Clear from RAM
        del positions_data
        gc.collect()

    def _delete_chunk(self, start_time: datetime, end_time: datetime) -> int:
        """
        Delete cache files in time range based on data timestamp (not modification time)

        Args:
            start_time: Start of deletion range
            end_time: End of deletion range

        Returns:
            Number of files deleted
        """
        deleted = 0

        try:
            import re
            # Delete cache files with timestamps older than end_time
            # Filename format: sliding_{norad_id}_{YYYYMMDD}_{HH}.npz
            for cache_file in self.pcm.cache_dir.glob('sliding_*.npz'):
                try:
                    # Extract timestamp from filename
                    match = re.search(r'sliding_\d+_(\d{8})_(\d{2})\.npz', cache_file.name)
                    if match:
                        date_str = match.group(1)  # YYYYMMDD
                        hour_str = match.group(2)  # HH

                        # Parse to datetime
                        file_dt = datetime.strptime(f"{date_str}_{hour_str}", "%Y%m%d_%H")
                        file_dt = file_dt.replace(tzinfo=timezone.utc)

                        # Delete if file data is before end_time
                        if file_dt < end_time:
                            cache_file.unlink()
                            deleted += 1

                except Exception as e:
                    logger.debug(f"Error checking/deleting {cache_file.name}: {e}")

        except Exception as e:
            logger.error(f"Error during chunk deletion: {e}")

        return deleted

    def get_status(self):
        """Get current cache status"""
        return {
            'initialized': self.is_initialized,
            'cache_days': self.cache_days,
            'chunk_hours': self.chunk_hours,
            'slide_interval_hours': self.slide_interval_hours,
            'last_slide': self.last_slide.isoformat() if self.last_slide else None,
            'metadata': self.metadata
        }

    def needs_update(self) -> bool:
        """Check if cache needs update"""
        if not self.is_initialized:
            return True

        if not self.last_slide:
            return True

        hours_since_slide = (datetime.now(timezone.utc) - self.last_slide).total_seconds() / 3600
        return hours_since_slide >= self.slide_interval_hours
