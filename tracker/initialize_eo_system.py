"""
Initialize Earth Observation Satellite System

Run this script once to:
1. Initialize EO satellite database with default configurations
2. Download JPL ephemeris data for solar calculations
"""

import logging
from pathlib import Path
from eo_satellite_database import EOSatelliteDatabase
from skyfield.api import load

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    print("\n" + "="*70)
    print("EARTH OBSERVATION SYSTEM INITIALIZATION")
    print("="*70 + "\n")

    # Step 1: Initialize EO Satellite Database
    print("[1/2] Initializing EO Satellite Database...")
    try:
        eo_db = EOSatelliteDatabase('eo_satellites.json')

        if len(eo_db.satellites) == 0:
            print("   No satellites found, creating default database...")
            count = eo_db.initialize_default_satellites()
            print(f"   ✅ Created {count} EO satellite configurations")
        else:
            print(f"   ✅ Database already exists with {len(eo_db.satellites)} satellites")

    except Exception as e:
        print(f"   ❌ Error initializing EO database: {e}")
        return False

    # Step 2: Download JPL Ephemeris Data
    print("\n[2/2] Downloading JPL Ephemeris Data (de421.bsp)...")
    try:
        ephemeris_file = Path('de421.bsp')

        if ephemeris_file.exists():
            print(f"   ✅ Ephemeris file already exists ({ephemeris_file.stat().st_size / 1024 / 1024:.1f} MB)")
        else:
            print("   📥 Downloading from JPL (this may take a minute)...")
            ephemeris = load('de421.bsp')
            print(f"   ✅ Downloaded successfully ({ephemeris_file.stat().st_size / 1024 / 1024:.1f} MB)")

    except Exception as e:
        print(f"   ❌ Error downloading ephemeris data: {e}")
        print("   Note: Day/night calculations will be disabled without ephemeris data")

    print("\n" + "="*70)
    print("INITIALIZATION COMPLETE!")
    print("="*70)
    print("\nYou can now:")
    print("  1. Start the Flask app: python app.py")
    print("  2. Select an EO satellite to see coverage visualization")
    print("  3. Toggle 'Coverage Swath' or 'Ground Swath' buttons")
    print("\nEO Satellites Available:")
    print("  - Landsat 8/9 (open data, 15m resolution, 185km swath)")
    print("  - Sentinel-1 A/B (SAR, open data, 5m resolution, 250km swath)")
    print("  - Sentinel-2 A/B (optical, open data, 10m resolution, 290km swath)")
    print("  - Sentinel-3 A/B (optical, open data, 300m resolution, 1270km swath)")
    print("  - WorldView-2/3 (commercial, sub-meter resolution)")
    print("  - Pleiades 1A/1B (commercial, 0.5m resolution)")
    print("  - Terra/Aqua (MODIS, open data, 250m resolution, 2330km swath)")
    print("  - And more...\n")

    return True


if __name__ == '__main__':
    success = main()
    if not success:
        print("\n[ERROR] Initialization failed. Please check the errors above.")
        exit(1)
