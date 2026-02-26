#!/usr/bin/env python3
"""
Force rebuild position cache with fixed altitude calculations
Run this AFTER stopping the server to ensure clean rebuild
"""

import shutil
from pathlib import Path
import sys

print("=" * 60)
print("POSITION CACHE REBUILD SCRIPT")
print("=" * 60)

# 1. Clear old cache
cache_dir = Path('cache/position_cache')
if cache_dir.exists():
    print(f"\n1. Removing old cache directory...")
    try:
        shutil.rmtree(cache_dir)
        print(f"   ✅ Removed: {cache_dir}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print(f"   → Please manually delete: {cache_dir.absolute()}")
        sys.exit(1)
else:
    print(f"\n1. No existing cache found (good!)")

# 2. Create fresh directory
cache_dir.mkdir(parents=True, exist_ok=True)
print(f"   ✅ Created fresh cache directory")

# 3. Clear metadata
metadata_file = Path('cache/cache_metadata.json')
if metadata_file.exists():
    print(f"\n2. Removing old metadata...")
    try:
        metadata_file.unlink()
        print(f"   ✅ Removed: {metadata_file}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ CACHE CLEARED SUCCESSFULLY!")
print("=" * 60)
print("\nNext steps:")
print("1. Start your server: python app.py")
print("2. Wait 5-10 minutes for cache to rebuild")
print("3. Watch for: '✅ Stage 1 complete!'")
print("4. Then spatial index will build automatically")
print("\n" + "=" * 60)
