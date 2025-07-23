"""
Offline satellite data for 3D Satellite Tracker
This file contains sample TLE (Two-Line Element) data for offline operation.
In a real offline setup, you would download fresh TLE data periodically.
"""

# Sample TLE data - These are real satellites but TLE data gets outdated quickly
# For production offline use, download fresh TLE data from https://celestrak.org/
SAMPLE_TLE_DATA = """
ISS (ZARYA)             
1 25544U 98067A   23204.12345678  .00001234  00000-0  12345-4 0  9999
2 25544  51.6461 123.4567   0001234  12.3456 123.4567 15.12345678123456

CALSPHERE 1             
1 00900U 64063C   23204.12345678  .00000123  00000-0  12345-5 0  9999
2 00900  90.2123  45.6789   0012345  67.8901 234.5678 14.12345678987654

CALSPHERE 2             
1 00902U 64063E   23204.12345678  .00000123  00000-0  12345-5 0  9999
2 00902  90.2123  46.7890   0012345  68.9012 235.6789 14.12345678987654

GPS BIIR-2  (PRN 13)    
1 24876U 97035A   23204.12345678  .00000012  00000-0  00000+0 0  9999
2 24876  55.1234 123.4567   0012345  67.8901 234.5678  2.00571234567890

STARLINK-1007           
1 44713U 19074A   23204.12345678  .00001234  00000-0  12345-4 0  9999
2 44713  53.0123 123.4567   0001234  12.3456 123.4567 15.12345678123456

NOAA 15                 
1 25338U 98030A   23204.12345678  .00000123  00000-0  12345-5 0  9999
2 25338  98.7123 123.4567   0012345  67.8901 234.5678 14.12345678987654

GOES 16                 
1 41866U 16071A   23204.12345678  .00000012  00000-0  00000+0 0  9999
2 41866   0.1234 123.4567   0001234  12.3456 123.4567  1.00271234567890

LANDSAT 8               
1 39084U 13008A   23204.12345678  .00000123  00000-0  12345-5 0  9999
2 39084  98.2123 123.4567   0001234  12.3456 123.4567 14.12345678987654

IRIDIUM 33 DEB          
1 24946U 97051C   23204.12345678  .00000123  00000-0  12345-5 0  9999
2 24946  86.4123 123.4567   0012345  67.8901 234.5678 14.12345678987654

COSMOS 2251 DEB         
1 25544U 93036A   23204.12345678  .00000123  00000-0  12345-5 0  9999
2 25544  82.9123 123.4567   0012345  67.8901 234.5678 14.12345678987654
"""

def get_offline_tle_data():
    """Return sample TLE data for offline operation"""
    return SAMPLE_TLE_DATA.strip()

def get_fresh_tle_data_urls():
    """
    URLs to download fresh TLE data when you have internet connection.
    Run this periodically to update your offline data.
    """
    return [
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=tle",
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle",
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle",
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=noaa&FORMAT=tle",
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=goes&FORMAT=tle",
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=resource&FORMAT=tle",
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=sarsat&FORMAT=tle",
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=dmc&FORMAT=tle",
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=tdrss&FORMAT=tle",
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=argos&FORMAT=tle",
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=planet&FORMAT=tle",
        "https://celestrak.org/NORAD/elements/gp.php?GROUP=spire&FORMAT=tle"
    ]

if __name__ == "__main__":
    import requests
    import os
    
    print("🛰️  TLE Data Downloader for Offline Use")
    print("=" * 50)
    
    # Create data directory
    os.makedirs("data", exist_ok=True)
    
    # Download fresh TLE data
    urls = get_fresh_tle_data_urls()
    all_tle_data = []
    
    for i, url in enumerate(urls, 1):
        try:
            print(f"📡 Downloading from source {i}/{len(urls)}...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            all_tle_data.append(response.text)
            print(f"✅ Success: {len(response.text)} characters")
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    # Save to file
    if all_tle_data:
        combined_data = "\n".join(all_tle_data)
        with open("data/offline_tle_data.txt", "w") as f:
            f.write(combined_data)
        print(f"💾 Saved {len(combined_data)} characters to data/offline_tle_data.txt")
        print("✅ Ready for offline use!")
    else:
        print("❌ No data downloaded. Using sample data instead.")