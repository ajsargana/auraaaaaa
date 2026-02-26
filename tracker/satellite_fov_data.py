
"""
Earth Observation Satellite Field of View (FOV) Database
Based on accurate satellite data for precise pass predictions
"""

class EarthObservationSatellites:
    def __init__(self):
        self.satellites = self._load_satellite_fov_data()
    
    def _load_satellite_fov_data(self):
        """Load accurate FOV data for Earth observation satellites"""
        return {
            # Sentinel Satellites (ESA) - Updated with correct NORAD IDs
            39634: {  # Sentinel 1A
                'name': 'SENTINEL-1A',
                'fov_modes': {
                    'IW': {'swath_width': 250, 'coverage_angle': 30.45},
                    'EW': {'swath_width': 400, 'coverage_angle': 45.0},
                },
                'default_swath': 250,
                'sensors': ['C-band SAR'],
                'sensor_type': 'SAR',
                'country': 'ESA',
                'altitude_km': 693,
                'launch_date': '2014-04-03',
            },
            40697: {  # Sentinel 2A
                'name': 'SENTINEL-2A',
                'fov_modes': {
                    'MSI': {'swath_width': 290, 'coverage_angle': 20.6},
                },
                'default_swath': 290,
                'sensors': ['MSI 13 bands(VNIR and SWIR)'],
                'sensor_type': 'multispectral',
                'country': 'ESA',
                'altitude_km': 786,
                'launch_date': '2015-06-23',
            },
            42063: {  # Sentinel 2B
                'name': 'SENTINEL-2B',
                'fov_modes': {
                    'MSI': {'swath_width': 290, 'coverage_angle': 20.6},
                },
                'default_swath': 290,
                'sensors': ['MSI 13 bands(VNIR and SWIR)'],
                'sensor_type': 'multispectral',
                'country': 'ESA',
                'altitude_km': 786,
                'launch_date': '2017-03-07',
            },
            41335: {  # Sentinel 3A
                'name': 'SENTINEL-3A',
                'fov_modes': {
                    'OLCI':  {'swath_width': 1270, 'coverage_angle': 68.5},
                    'SLSTR': {'swath_width': 1400, 'coverage_angle': 74.0},
                },
                'default_swath': 1270,
                'sensors': ['OLCI,SLSTR,SRAL'],
                'sensor_type': 'thermal',
                'country': 'ESA',
                'altitude_km': 814,
                'launch_date': '2016-02-16',
            },
            43437: {  # Sentinel 3B
                'name': 'SENTINEL-3B',
                'fov_modes': {
                    'OLCI':  {'swath_width': 1270, 'coverage_angle': 68.5},
                    'SLSTR': {'swath_width': 1400, 'coverage_angle': 74.0},
                },
                'default_swath': 1270,
                'sensors': ['OLCI,SLSTR,SRAL'],
                'sensor_type': 'thermal',
                'country': 'ESA',
                'altitude_km': 814,
                'launch_date': '2018-04-25',
            },
            42969: {  # Sentinel 5P
                'name': 'SENTINEL-5P',
                'fov_modes': {
                    'TROPOMI': {'swath_width': 2600, 'coverage_angle': 77.0},
                },
                'default_swath': 2600,
                'sensors': ['TROPOMI'],
                'sensor_type': 'weather',
                'country': 'ESA',
                'altitude_km': 824,
                'launch_date': '2017-10-13',
            },
            46984: {  # Sentinel 6MF
                'name': 'SENTINEL-6MF',
                'fov_modes': {
                    'Poseidon-4': {'swath_width': 0, 'coverage_angle': 0},
                },
                'default_swath': 0,
                'sensors': ['Poseidon-4 altimeter'],
                'sensor_type': 'lidar',
                'country': 'ESA',
                'altitude_km': 1336,
                'launch_date': '2020-11-21',
            },

            # Landsat Satellites (NASA/USGS)
            39084: {  # Landsat 8
                'name': 'LANDSAT-8',
                'fov_modes': {
                    'OLI': {'swath_width': 185, 'coverage_angle': 15.0},
                },
                'default_swath': 185,
                'sensors': ['OLI,TIRS'],
                'sensor_type': 'multispectral',
                'country': 'NASA',
                'altitude_km': 705,
                'launch_date': '2013-02-11',
            },
            49260: {  # Landsat 9
                'name': 'LANDSAT-9',
                'fov_modes': {
                    'OLI': {'swath_width': 185, 'coverage_angle': 15.0},
                },
                'default_swath': 185,
                'sensors': ['OLI-2,TIRS-2'],
                'sensor_type': 'multispectral',
                'country': 'NASA',
                'altitude_km': 705,
                'launch_date': '2021-09-27',
            },

            # Terra & Aqua (NASA)
            25994: {  # Terra
                'name': 'TERRA',
                'fov_modes': {
                    'MODIS': {'swath_width': 2330, 'coverage_angle': 110.0},
                },
                'default_swath': 2330,
                'sensors': ['MODIS'],
                'sensor_type': 'thermal',
                'country': 'NASA',
                'altitude_km': 705,
                'launch_date': '1999-12-18',
            },
            27424: {  # Aqua
                'name': 'AQUA',
                'fov_modes': {
                    'MODIS': {'swath_width': 2330, 'coverage_angle': 110.0},
                },
                'default_swath': 2330,
                'sensors': ['MODIS'],
                'sensor_type': 'thermal',
                'country': 'NASA',
                'altitude_km': 705,
                'launch_date': '2002-05-04',
            },
            37849: {  # Suomi NPP
                'name': 'SUOMI NPP',
                'fov_modes': {
                    'VIIRS': {'swath_width': 3000, 'coverage_angle': 112.0},
                },
                'default_swath': 3000,
                'sensors': ['VIIRS'],
                'sensor_type': 'thermal',
                'country': 'NASA',
                'altitude_km': 824,
                'launch_date': '2011-10-28',
            },
            43013: {  # NOAA-20 (JPSS-1)
                'name': 'NOAA-20',
                'fov_modes': {
                    'VIIRS': {'swath_width': 3000, 'coverage_angle': 112.0},
                },
                'default_swath': 3000,
                'sensors': ['VIIRS,CrIS,ATMS,OMPS'],
                'sensor_type': 'thermal',
                'country': 'NASA',
                'altitude_km': 824,
                'launch_date': '2017-11-18',
            },

            # WorldView Satellites (Maxar)
            32060: {  # WorldView-1
                'name': 'WORLDVIEW-1',
                'fov_modes': {
                    'Panchromatic': {'swath_width': 17.6, 'coverage_angle': 1.35},
                },
                'default_swath': 17.6,
                'sensors': ['Panchromatic'],
                'sensor_type': 'optical',
                'country': 'US',
                'altitude_km': 496,
                'launch_date': '2007-09-18',
            },
            35946: {  # WorldView-2
                'name': 'WORLDVIEW-2',
                'fov_modes': {
                    'Panchromatic': {'swath_width': 16.4, 'coverage_angle': 1.35},
                },
                'default_swath': 16.4,
                'sensors': ['Panchromatic, 8 band MS'],
                'sensor_type': 'optical',
                'country': 'US',
                'altitude_km': 770,
                'launch_date': '2009-10-08',
            },
            40115: {  # WorldView-3
                'name': 'WORLDVIEW-3',
                'fov_modes': {
                    'Panchromatic': {'swath_width': 13.1, 'coverage_angle': 1.07},
                },
                'default_swath': 13.1,
                'sensors': ['Panchromatic,SWIR,CAVIS'],
                'sensor_type': 'optical',
                'country': 'US',
                'altitude_km': 617,
                'launch_date': '2014-08-13',
            },

            # SPOT Series (France)
            27421: {  # SPOT-5
                'name': 'SPOT-5',
                'fov_modes': {
                    'HRG': {'swath_width': 60, 'coverage_angle': 4.13},
                },
                'default_swath': 60,
                'sensors': ['HRG,HRS,DORIS'],
                'sensor_type': 'optical',
                'country': 'France',
                'altitude_km': 832,
                'launch_date': '2002-05-04',
            },

            # KOMPSAT Series (South Korea)
            40068: {  # KOMPSAT-3A
                'name': 'KOMPSAT-3A',
                'fov_modes': {
                    'AEISS': {'swath_width': 12, 'coverage_angle': 1.0},
                },
                'default_swath': 12,
                'sensors': ['AEISS'],
                'sensor_type': 'optical',
                'country': 'South Korea',
                'altitude_km': 528,
                'launch_date': '2015-03-26',
            },

            # RADARSAT Constellation (Canada)
            43238: {  # RADARSAT Constellation M1
                'name': 'RADARSAT CONSTELLATION M1',
                'fov_modes': {
                    'C-SAR': {'swath_width': 500, 'coverage_angle': 45.0},
                },
                'default_swath': 500,
                'sensors': ['C-band SAR'],
                'sensor_type': 'SAR',
                'country': 'Canada',
                'altitude_km': 592,
                'launch_date': '2019-06-12',
            },

            # Chinese Earth Observation Satellites (old entry 43013 REMOVED – now NOAA-20)
            # GAOFEN-7 correct NORAD is 44231 (see below)
            
            # ── GAOFEN Series (China) ─────────────────────────────────────────
            39232: {
                'name': 'GAOFEN-1',
                'fov_modes': {
                    'PMS': {'swath_width': 60,  'coverage_angle': 4.8},
                    'WFV': {'swath_width': 800, 'coverage_angle': 55.0},
                },
                'default_swath': 800,
                'sensors': ['PAN+MS 4-band', 'WFV 4-band'],
                'sensor_type': 'multispectral',
                'country': 'China',
                'altitude_km': 645,
                'launch_date': '2013-04-26',
            },
            40214: {
                'name': 'GAOFEN-2',
                'fov_modes': {
                    'PMS': {'swath_width': 45, 'coverage_angle': 3.7},
                },
                'default_swath': 45,
                'sensors': ['0.8m PAN, 3.24m MS'],
                'sensor_type': 'optical',
                'country': 'China',
                'altitude_km': 631,
                'launch_date': '2014-08-19',
            },
            41298: {
                'name': 'GAOFEN-3',
                'fov_modes': {
                    'Spotlight': {'swath_width': 10,  'coverage_angle': 1.0},
                    'SCANSAR':   {'swath_width': 500, 'coverage_angle': 50.0},
                    'Standard':  {'swath_width': 30,  'coverage_angle': 3.0},
                },
                'default_swath': 30,
                'sensors': ['C-band SAR'],
                'sensor_type': 'SAR',
                'country': 'China',
                'altitude_km': 755,
                'launch_date': '2016-08-10',
            },
            41315: {
                'name': 'GAOFEN-4',
                'fov_modes': {
                    'PAN': {'swath_width': 400, 'coverage_angle': 1.0},
                },
                'default_swath': 400,
                'sensors': ['50m PAN+MS (GEO)'],
                'sensor_type': 'optical',
                'country': 'China',
                'altitude_km': 35786,
                'launch_date': '2015-12-29',
            },
            44231: {
                'name': 'GAOFEN-7',
                'fov_modes': {
                    'BWD': {'swath_width': 20, 'coverage_angle': 1.6},
                },
                'default_swath': 20,
                'sensors': ['0.8m PAN, 2.6m MS, Laser Altimeter'],
                'sensor_type': 'optical',
                'country': 'China',
                'altitude_km': 506,
                'launch_date': '2019-11-03',
            },
            44528: {
                'name': 'GAOFEN-12',
                'fov_modes': {
                    'Spotlight': {'swath_width': 10,  'coverage_angle': 1.0},
                    'StripMap':  {'swath_width': 50,  'coverage_angle': 4.5},
                    'SCANSAR':   {'swath_width': 300, 'coverage_angle': 30.0},
                },
                'default_swath': 50,
                'sensors': ['X-band SAR'],
                'sensor_type': 'SAR',
                'country': 'China',
                'altitude_km': 600,
                'launch_date': '2019-11-28',
            },

            # ── Pleiades (Airbus) ──────────────────────────────────────────
            38374: {
                'name': 'PLEIADES-1A',
                'fov_modes': {
                    'PMS': {'swath_width': 20, 'coverage_angle': 1.65},
                },
                'default_swath': 20,
                'sensors': ['0.5m PAN, 2m MS 4-band'],
                'sensor_type': 'optical',
                'country': 'France',
                'altitude_km': 694,
                'launch_date': '2011-12-17',
            },
            39144: {
                'name': 'PLEIADES-1B',
                'fov_modes': {
                    'PMS': {'swath_width': 20, 'coverage_angle': 1.65},
                },
                'default_swath': 20,
                'sensors': ['0.5m PAN, 2m MS 4-band'],
                'sensor_type': 'optical',
                'country': 'France',
                'altitude_km': 694,
                'launch_date': '2012-12-02',
            },
            49237: {
                'name': 'PLEIADES NEO-3',
                'fov_modes': {
                    'PMS': {'swath_width': 14, 'coverage_angle': 1.16},
                },
                'default_swath': 14,
                'sensors': ['0.3m PAN, 0.7m MS 6-band'],
                'sensor_type': 'optical',
                'country': 'France',
                'altitude_km': 620,
                'launch_date': '2021-04-29',
            },
            49593: {
                'name': 'PLEIADES NEO-4',
                'fov_modes': {
                    'PMS': {'swath_width': 14, 'coverage_angle': 1.16},
                },
                'default_swath': 14,
                'sensors': ['0.3m PAN, 0.7m MS 6-band'],
                'sensor_type': 'optical',
                'country': 'France',
                'altitude_km': 620,
                'launch_date': '2021-08-17',
            },

            # ── SPOT-6 / SPOT-7 (Airbus) ──────────────────────────────────
            38755: {
                'name': 'SPOT-6',
                'fov_modes': {
                    'PMS': {'swath_width': 60, 'coverage_angle': 4.95},
                },
                'default_swath': 60,
                'sensors': ['1.5m PAN, 6m MS 4-band'],
                'sensor_type': 'optical',
                'country': 'France',
                'altitude_km': 694,
                'launch_date': '2012-09-09',
            },
            40053: {
                'name': 'SPOT-7',
                'fov_modes': {
                    'PMS': {'swath_width': 60, 'coverage_angle': 4.95},
                },
                'default_swath': 60,
                'sensors': ['1.5m PAN, 6m MS 4-band'],
                'sensor_type': 'optical',
                'country': 'France',
                'altitude_km': 694,
                'launch_date': '2014-06-30',
            },

            # ── GeoEye-1 / IKONOS (Maxar) ─────────────────────────────────
            33331: {
                'name': 'GEOEYE-1',
                'fov_modes': {
                    'PAN': {'swath_width': 15.2, 'coverage_angle': 1.28},
                },
                'default_swath': 15.2,
                'sensors': ['0.46m PAN, 1.84m MS 4-band'],
                'sensor_type': 'optical',
                'country': 'US',
                'altitude_km': 681,
                'launch_date': '2008-09-06',
            },

            # ── SkySat (Planet Labs) ───────────────────────────────────────
            40378: {
                'name': 'SKYSAT-A',
                'fov_modes': {
                    'Video': {'swath_width': 2.0, 'coverage_angle': 0.186},
                    'Still': {'swath_width': 8.0, 'coverage_angle': 0.74},
                },
                'default_swath': 8.0,
                'sensors': ['0.5m PAN, 1m MS 5-band, Video'],
                'sensor_type': 'optical',
                'country': 'US',
                'altitude_km': 450,
                'launch_date': '2013-11-21',
            },
            40379: {
                'name': 'SKYSAT-B',
                'fov_modes': {
                    'Video': {'swath_width': 2.0, 'coverage_angle': 0.186},
                    'Still': {'swath_width': 8.0, 'coverage_angle': 0.74},
                },
                'default_swath': 8.0,
                'sensors': ['0.5m PAN, 1m MS 5-band, Video'],
                'sensor_type': 'optical',
                'country': 'US',
                'altitude_km': 450,
                'launch_date': '2014-06-19',
            },
            40892: {
                'name': 'SKYSAT-C1',
                'fov_modes': {
                    'Video': {'swath_width': 2.0, 'coverage_angle': 0.186},
                    'Still': {'swath_width': 8.0, 'coverage_angle': 0.74},
                },
                'default_swath': 8.0,
                'sensors': ['0.72m PAN, 0.9m MS 5-band'],
                'sensor_type': 'optical',
                'country': 'US',
                'altitude_km': 500,
                'launch_date': '2016-09-16',
            },

            # ── Planet Dove / Flock ───────────────────────────────────────
            41168: {
                'name': 'DOVE (FLOCK-1A)',
                'fov_modes': {
                    'PS2': {'swath_width': 24.6, 'coverage_angle': 2.0},
                },
                'default_swath': 24.6,
                'sensors': ['3m MS 4-band'],
                'sensor_type': 'multispectral',
                'country': 'US',
                'altitude_km': 400,
                'launch_date': '2014-02-11',
            },
            43931: {
                'name': 'DOVE (FLOCK-3P)',
                'fov_modes': {
                    'PS2': {'swath_width': 24.6, 'coverage_angle': 2.0},
                },
                'default_swath': 24.6,
                'sensors': ['3m MS 4-band'],
                'sensor_type': 'multispectral',
                'country': 'US',
                'altitude_km': 475,
                'launch_date': '2019-06-12',
            },

            # ── BlackSky ──────────────────────────────────────────────────
            44332: {
                'name': 'BLACKSKY-1',
                'fov_modes': {
                    'PAN': {'swath_width': 4.0, 'coverage_angle': 0.45},
                },
                'default_swath': 4.0,
                'sensors': ['1m PAN+MS 4-band'],
                'sensor_type': 'optical',
                'country': 'US',
                'altitude_km': 450,
                'launch_date': '2019-09-26',
            },

            # ── DEIMOS ────────────────────────────────────────────────────
            35681: {
                'name': 'DEIMOS-1',
                'fov_modes': {
                    'WFI': {'swath_width': 650, 'coverage_angle': 49.0},
                },
                'default_swath': 650,
                'sensors': ['22m MS 3-band (NIR,R,G)'],
                'sensor_type': 'multispectral',
                'country': 'Spain',
                'altitude_km': 662,
                'launch_date': '2009-07-29',
            },
            39977: {
                'name': 'DEIMOS-2',
                'fov_modes': {
                    'PMS': {'swath_width': 12, 'coverage_angle': 1.01},
                },
                'default_swath': 12,
                'sensors': ['0.75m PAN, 1m MS 4-band'],
                'sensor_type': 'optical',
                'country': 'Spain',
                'altitude_km': 620,
                'launch_date': '2014-06-19',
            },

            # ── KOMPSAT-2/3 (Korea) ───────────────────────────────────────
            29268: {
                'name': 'KOMPSAT-2',
                'fov_modes': {
                    'MSC': {'swath_width': 15, 'coverage_angle': 1.28},
                },
                'default_swath': 15,
                'sensors': ['1m PAN, 4m MS 4-band'],
                'sensor_type': 'optical',
                'country': 'South Korea',
                'altitude_km': 685,
                'launch_date': '2006-07-28',
            },
            39204: {
                'name': 'KOMPSAT-3',
                'fov_modes': {
                    'AEISS': {'swath_width': 16, 'coverage_angle': 1.35},
                },
                'default_swath': 16,
                'sensors': ['0.7m PAN, 2.8m MS 4-band'],
                'sensor_type': 'optical',
                'country': 'South Korea',
                'altitude_km': 685,
                'launch_date': '2012-05-18',
            },
            40377: {
                'name': 'KOMPSAT-5',
                'fov_modes': {
                    'Fine':   {'swath_width': 5,   'coverage_angle': 0.45},
                    'Standard':{'swath_width': 30, 'coverage_angle': 2.7},
                    'Wide':   {'swath_width': 100, 'coverage_angle': 9.0},
                },
                'default_swath': 30,
                'sensors': ['X-band SAR'],
                'sensor_type': 'SAR',
                'country': 'South Korea',
                'altitude_km': 550,
                'launch_date': '2013-08-22',
            },

            # ── DubaiSat (UAE) ────────────────────────────────────────────
            35795: {
                'name': 'DUBAISAT-1',
                'fov_modes': {
                    'HRC': {'swath_width': 14, 'coverage_angle': 1.18},
                },
                'default_swath': 14,
                'sensors': ['2.5m PAN, 5m MS 4-band'],
                'sensor_type': 'optical',
                'country': 'UAE',
                'altitude_km': 680,
                'launch_date': '2009-07-29',
            },
            39051: {
                'name': 'DUBAISAT-2',
                'fov_modes': {
                    'HRC': {'swath_width': 12, 'coverage_angle': 1.01},
                },
                'default_swath': 12,
                'sensors': ['1m PAN, 4m MS'],
                'sensor_type': 'optical',
                'country': 'UAE',
                'altitude_km': 620,
                'launch_date': '2013-11-21',
            },

            # ── CartoSat (India) ──────────────────────────────────────────
            28751: {
                'name': 'IRS-P5 (CARTOSAT-1)',
                'fov_modes': {
                    'PAN': {'swath_width': 30, 'coverage_angle': 2.55},
                },
                'default_swath': 30,
                'sensors': ['2.5m Stereo PAN'],
                'sensor_type': 'optical',
                'country': 'India',
                'altitude_km': 618,
                'launch_date': '2005-05-05',
            },
            32783: {
                'name': 'CARTOSAT-2A',
                'fov_modes': {
                    'PAN': {'swath_width': 9.6, 'coverage_angle': 0.89},
                },
                'default_swath': 9.6,
                'sensors': ['0.8m PAN'],
                'sensor_type': 'optical',
                'country': 'India',
                'altitude_km': 635,
                'launch_date': '2008-04-28',
            },
            33403: {
                'name': 'CARTOSAT-2B',
                'fov_modes': {
                    'PAN': {'swath_width': 9.6, 'coverage_angle': 0.89},
                },
                'default_swath': 9.6,
                'sensors': ['0.8m PAN'],
                'sensor_type': 'optical',
                'country': 'India',
                'altitude_km': 635,
                'launch_date': '2010-07-12',
            },
            41599: {
                'name': 'CARTOSAT-2C',
                'fov_modes': {
                    'PAN': {'swath_width': 9.6, 'coverage_angle': 0.89},
                },
                'default_swath': 9.6,
                'sensors': ['0.6m PAN, 2m MS'],
                'sensor_type': 'optical',
                'country': 'India',
                'altitude_km': 505,
                'launch_date': '2016-06-22',
            },

            # ── ResourceSat / LISS (India) ────────────────────────────────
            28051: {
                'name': 'IRS-P6 (RESOURCESAT-1)',
                'fov_modes': {
                    'LISS-III': {'swath_width': 141, 'coverage_angle': 11.9},
                    'LISS-IV':  {'swath_width': 23,  'coverage_angle': 1.96},
                },
                'default_swath': 141,
                'sensors': ['5.8m LISS-III, 5.8m LISS-IV, AWiFS'],
                'sensor_type': 'multispectral',
                'country': 'India',
                'altitude_km': 817,
                'launch_date': '2003-10-17',
            },
            37219: {
                'name': 'RESOURCESAT-2',
                'fov_modes': {
                    'LISS-III': {'swath_width': 141, 'coverage_angle': 11.9},
                    'LISS-IV':  {'swath_width': 23,  'coverage_angle': 1.96},
                    'AWiFS':    {'swath_width': 740, 'coverage_angle': 55.0},
                },
                'default_swath': 141,
                'sensors': ['5.8m LISS-III, 5.8m LISS-IV, AWiFS 56m'],
                'sensor_type': 'multispectral',
                'country': 'India',
                'altitude_km': 817,
                'launch_date': '2011-04-20',
            },

            # ── OceanSat (India) ──────────────────────────────────────────
            35688: {
                'name': 'OCEANSAT-2',
                'fov_modes': {
                    'OCM-2': {'swath_width': 1420, 'coverage_angle': 120.0},
                    'SCAT':  {'swath_width': 1400, 'coverage_angle': 119.0},
                },
                'default_swath': 1420,
                'sensors': ['OCM-2 360m, Scatterometer'],
                'sensor_type': 'optical',
                'country': 'India',
                'altitude_km': 720,
                'launch_date': '2009-09-23',
            },

            # ── HuanJing (China environment) ─────────────────────────────
            33320: {
                'name': 'HUANJING-1A',
                'fov_modes': {
                    'CCD':  {'swath_width': 360, 'coverage_angle': 27.0},
                    'IRS':  {'swath_width': 720, 'coverage_angle': 54.0},
                },
                'default_swath': 720,
                'sensors': ['CCD 30m, IRS 150m, HIS 100m'],
                'sensor_type': 'multispectral',
                'country': 'China',
                'altitude_km': 649,
                'launch_date': '2008-09-06',
            },
            33321: {
                'name': 'HUANJING-1B',
                'fov_modes': {
                    'CCD': {'swath_width': 360, 'coverage_angle': 27.0},
                    'SAR': {'swath_width': 450, 'coverage_angle': 40.0},
                },
                'default_swath': 360,
                'sensors': ['CCD 30m, S-band SAR'],
                'sensor_type': 'multispectral',
                'country': 'China',
                'altitude_km': 649,
                'launch_date': '2008-09-06',
            },

            # ── CBERS-4 (Brazil/China) ────────────────────────────────────
            40178: {
                'name': 'CBERS-4',
                'fov_modes': {
                    'PANMUX': {'swath_width': 90,  'coverage_angle': 7.5},
                    'MUX':    {'swath_width': 120, 'coverage_angle': 9.9},
                    'IRS':    {'swath_width': 120, 'coverage_angle': 9.9},
                    'WFI':    {'swath_width': 866, 'coverage_angle': 62.0},
                },
                'default_swath': 120,
                'sensors': ['5m PAN, 20m MS (MUX), 40m (IRS), 64m (WFI)'],
                'sensor_type': 'multispectral',
                'country': 'Brazil/China',
                'altitude_km': 778,
                'launch_date': '2014-12-07',
            },

            # ── Haiyang (China ocean) ─────────────────────────────────────
            29630: {
                'name': 'HAIYANG-1B',
                'fov_modes': {
                    'COCTS': {'swath_width': 2900, 'coverage_angle': 120.0},
                    'CZI':   {'swath_width': 500,  'coverage_angle': 40.0},
                },
                'default_swath': 2900,
                'sensors': ['COCTS 1100m, CZI 250m'],
                'sensor_type': 'optical',
                'country': 'China',
                'altitude_km': 799,
                'launch_date': '2007-04-11',
            },
            44547: {
                'name': 'HAIYANG-2B',
                'fov_modes': {
                    'Scatterometer': {'swath_width': 1700, 'coverage_angle': 130.0},
                    'Radiometer':    {'swath_width': 1600, 'coverage_angle': 120.0},
                },
                'default_swath': 1700,
                'sensors': ['Microwave Scatterometer, Altimeter, Radiometer'],
                'sensor_type': 'weather',
                'country': 'China',
                'altitude_km': 971,
                'launch_date': '2018-10-25',
            },

            # ── THEOS (Thailand) ──────────────────────────────────────────
            33396: {
                'name': 'THEOS-1',
                'fov_modes': {
                    'PAN': {'swath_width': 22, 'coverage_angle': 1.85},
                    'MS':  {'swath_width': 90, 'coverage_angle': 7.5},
                },
                'default_swath': 90,
                'sensors': ['2m PAN, 15m MS 4-band'],
                'sensor_type': 'optical',
                'country': 'Thailand',
                'altitude_km': 677,
                'launch_date': '2008-10-01',
            },

            # ── ALSAT-1B (Algeria) ────────────────────────────────────────
            41789: {
                'name': 'ALSAT-1B',
                'fov_modes': {
                    'ALITE': {'swath_width': 25, 'coverage_angle': 2.1},
                    'MSI':   {'swath_width': 100,'coverage_angle': 8.4},
                },
                'default_swath': 25,
                'sensors': ['0.5m PAN, 2m MS, Wide MSI'],
                'sensor_type': 'optical',
                'country': 'Algeria',
                'altitude_km': 670,
                'launch_date': '2016-09-26',
            },

            # ── Aura (NASA atmospheric) ───────────────────────────────────
            28376: {
                'name': 'AURA',
                'fov_modes': {
                    'OMI':  {'swath_width': 2600, 'coverage_angle': 114.0},
                    'MLS':  {'swath_width': 0,    'coverage_angle': 0},
                    'HIRDLS':{'swath_width': 0,   'coverage_angle': 0},
                },
                'default_swath': 2600,
                'sensors': ['OMI (UV-Vis), MLS, HIRDLS, TES'],
                'sensor_type': 'hyperspectral',
                'country': 'NASA',
                'altitude_km': 705,
                'launch_date': '2004-07-15',
            },

            # ── SMAP (NASA soil moisture) ─────────────────────────────────
            40376: {
                'name': 'SMAP',
                'fov_modes': {
                    'Radiometer': {'swath_width': 1000, 'coverage_angle': 80.0},
                    'Radar':      {'swath_width': 1000, 'coverage_angle': 80.0},
                },
                'default_swath': 1000,
                'sensors': ['L-band Radiometer, SAR'],
                'sensor_type': 'SAR',
                'country': 'NASA',
                'altitude_km': 685,
                'launch_date': '2015-01-31',
            },

            # ── SMOS (ESA soil/ocean) ─────────────────────────────────────
            36036: {
                'name': 'SMOS',
                'fov_modes': {
                    'MIRAS': {'swath_width': 1050, 'coverage_angle': 80.0},
                },
                'default_swath': 1050,
                'sensors': ['MIRAS L-band Radiometer'],
                'sensor_type': 'weather',
                'country': 'ESA',
                'altitude_km': 763,
                'launch_date': '2009-11-02',
            },

            # ── GOSAT / IBUKI (JAXA carbon) ───────────────────────────────
            33591: {
                'name': 'GOSAT (IBUKI)',
                'fov_modes': {
                    'TANSO-FTS': {'swath_width': 0, 'coverage_angle': 0},
                },
                'default_swath': 10.5,
                'sensors': ['TANSO-FTS, TANSO-CAI (CO2/CH4 monitoring)'],
                'sensor_type': 'hyperspectral',
                'country': 'Japan',
                'altitude_km': 666,
                'launch_date': '2009-01-23',
            },

            # ── SARAL (ISRO/CNES altimetry) ───────────────────────────────
            39086: {
                'name': 'SARAL',
                'fov_modes': {
                    'AltiKa': {'swath_width': 0, 'coverage_angle': 0},
                },
                'default_swath': 0,
                'sensors': ['Ka-band Radar Altimeter AltiKa'],
                'sensor_type': 'lidar',
                'country': 'India/France',
                'altitude_km': 800,
                'launch_date': '2013-02-25',
            },

            # ── Jason-3 (CNES/EUMETSAT/NOAA) ─────────────────────────────
            41240: {
                'name': 'JASON-3',
                'fov_modes': {
                    'POSEIDON-3B': {'swath_width': 0, 'coverage_angle': 0},
                },
                'default_swath': 0,
                'sensors': ['POSEIDON-3B Radar Altimeter'],
                'sensor_type': 'lidar',
                'country': 'International',
                'altitude_km': 1336,
                'launch_date': '2016-01-17',
            },

            # ── ZIYUAN 3-02 (China stereo) ────────────────────────────────
            41384: {
                'name': 'ZIYUAN 3-02',
                'fov_modes': {
                    'TDI-CCD Nadir': {'swath_width': 51, 'coverage_angle': 4.3},
                    'TDI-CCD Fwd':   {'swath_width': 52, 'coverage_angle': 4.4},
                },
                'default_swath': 51,
                'sensors': ['2.1m Nadir PAN, 3.5m MS, Stereo'],
                'sensor_type': 'optical',
                'country': 'China',
                'altitude_km': 506,
                'launch_date': '2016-05-30',
            },

            # ── LAPAN-A3 (Indonesia) ──────────────────────────────────────
            41559: {
                'name': 'LAPAN-A3',
                'fov_modes': {
                    'MEIS': {'swath_width': 100, 'coverage_angle': 8.4},
                },
                'default_swath': 100,
                'sensors': ['4-band MS, Ship AIS'],
                'sensor_type': 'multispectral',
                'country': 'Indonesia',
                'altitude_km': 495,
                'launch_date': '2016-06-22',
            },

            # ── YAOGAN series representative (China military EO) ──────────
            30271: {
                'name': 'YAOGAN-3',
                'fov_modes': {
                    'SAR': {'swath_width': 100, 'coverage_angle': 9.0},
                },
                'default_swath': 100,
                'sensors': ['L-band SAR (estimated)'],
                'sensor_type': 'SAR',
                'country': 'China',
                'altitude_km': 500,
                'launch_date': '2007-11-12',
            },

            # ── KAZEOSAT (Kazakhstan) ─────────────────────────────────────
            39438: {
                'name': 'KAZEOSAT-1',
                'fov_modes': {
                    'HRC': {'swath_width': 15, 'coverage_angle': 1.28},
                    'MRC': {'swath_width': 90, 'coverage_angle': 7.5},
                },
                'default_swath': 15,
                'sensors': ['1m PAN, 4m MS'],
                'sensor_type': 'optical',
                'country': 'Kazakhstan',
                'altitude_km': 700,
                'launch_date': '2014-04-30',
            },
            40938: {
                'name': 'KAZEOSAT-2',
                'fov_modes': {
                    'WFI': {'swath_width': 820, 'coverage_angle': 61.0},
                },
                'default_swath': 820,
                'sensors': ['6.5m MS 4-band WFI'],
                'sensor_type': 'multispectral',
                'country': 'Kazakhstan',
                'altitude_km': 600,
                'launch_date': '2014-04-30',
            },

            # ── VNREDSAT-1 (Vietnam) ──────────────────────────────────────
            39008: {
                'name': 'VNREDSAT-1',
                'fov_modes': {
                    'HRC': {'swath_width': 17.5, 'coverage_angle': 1.47},
                },
                'default_swath': 17.5,
                'sensors': ['2.5m PAN, 10m MS 4-band'],
                'sensor_type': 'optical',
                'country': 'Vietnam',
                'altitude_km': 686,
                'launch_date': '2013-05-07',
            },

            # ── HODOYOSHI (Japan) ─────────────────────────────────────────
            40300: {
                'name': 'HODOYOSHI-3',
                'fov_modes': {
                    'Camera': {'swath_width': 40, 'coverage_angle': 3.5},
                },
                'default_swath': 40,
                'sensors': ['6.7m MS'],
                'sensor_type': 'multispectral',
                'country': 'Japan',
                'altitude_km': 500,
                'launch_date': '2014-06-20',
            },
            40301: {
                'name': 'HODOYOSHI-4',
                'fov_modes': {
                    'Camera': {'swath_width': 100, 'coverage_angle': 8.4},
                },
                'default_swath': 100,
                'sensors': ['45m MS (wide-area)'],
                'sensor_type': 'multispectral',
                'country': 'Japan',
                'altitude_km': 500,
                'launch_date': '2014-06-20',
            },

            # ── ASNARO (Japan) ────────────────────────────────────────────
            40930: {
                'name': 'ASNARO',
                'fov_modes': {
                    'PAN': {'swath_width': 10, 'coverage_angle': 0.93},
                },
                'default_swath': 10,
                'sensors': ['0.5m PAN, 2m MS'],
                'sensor_type': 'optical',
                'country': 'Japan',
                'altitude_km': 504,
                'launch_date': '2014-11-06',
            },

            # ── KENT RIDGE 1 (Singapore) ──────────────────────────────────
            41789: {
                'name': 'KENT RIDGE 1',
                'fov_modes': {
                    'PAN': {'swath_width': 20, 'coverage_angle': 1.9},
                },
                'default_swath': 20,
                'sensors': ['VHR PAN+MS'],
                'sensor_type': 'optical',
                'country': 'Singapore',
                'altitude_km': 550,
                'launch_date': '2015-12-16',
            },

            # ── GOKTURK-2 (Turkey) ────────────────────────────────────────
            38257: {
                'name': 'GOKTURK-2',
                'fov_modes': {
                    'MS': {'swath_width': 26, 'coverage_angle': 2.2},
                },
                'default_swath': 26,
                'sensors': ['2.5m PAN, 5m MS'],
                'sensor_type': 'optical',
                'country': 'Turkey',
                'altitude_km': 686,
                'launch_date': '2012-12-18',
            },

            # ── GPM Core Observatory ──────────────────────────────────────
            40376: {
                'name': 'GPM CORE',
                'fov_modes': {
                    'DPR': {'swath_width': 245, 'coverage_angle': 17.0},
                    'GMI': {'swath_width': 885, 'coverage_angle': 76.0},
                },
                'default_swath': 885,
                'sensors': ['DPR Dual-freq Radar, GMI Microwave Imager'],
                'sensor_type': 'weather',
                'country': 'NASA/JAXA',
                'altitude_km': 407,
                'launch_date': '2014-02-27',
            },

            # ── CARBONITE-1 (Earth-i) ─────────────────────────────────────
            40907: {
                'name': 'CARBONITE-1',
                'fov_modes': {
                    'Video': {'swath_width': 3.0, 'coverage_angle': 0.28},
                },
                'default_swath': 3.0,
                'sensors': ['1m HD Video, MS'],
                'sensor_type': 'optical',
                'country': 'UK',
                'altitude_km': 500,
                'launch_date': '2015-07-08',
            },

            # ── RapidEye (Planet Labs) ────────────────────────────────────
            33514: {
                'name': 'RAPIDEYE-1',
                'fov_modes': {
                    'REIS': {'swath_width': 77, 'coverage_angle': 6.4},
                },
                'default_swath': 77,
                'sensors': ['5m MS 5-band (Red Edge)'],
                'sensor_type': 'multispectral',
                'country': 'Germany/Canada',
                'altitude_km': 630,
                'launch_date': '2008-08-29',
            },
            33515: {
                'name': 'RAPIDEYE-2',
                'fov_modes': {
                    'REIS': {'swath_width': 77, 'coverage_angle': 6.4},
                },
                'default_swath': 77,
                'sensors': ['5m MS 5-band (Red Edge)'],
                'sensor_type': 'multispectral',
                'country': 'Germany/Canada',
                'altitude_km': 630,
                'launch_date': '2008-08-29',
            },

            # ── NOAA-20 (JPSS-1) – fixed NORAD (was duplicate) ───────────
            # 43013 was duplicate above, keeping correct entry below
            # Note: 43013 is NOAA-20 (JPSS-1), launched 2017-11-18
            # The duplicate entries for GAOFEN-7 and DOVE have been
            # given their correct NORAD IDs (44231 and 41168 above).
        }

    # ── Swath Intersection Check ─────────────────────────────────────────────

    def point_in_swath(self, norad_id: int, max_elevation_deg: float,
                       satellite_alt_km: float = None) -> bool:
        """
        Determine whether an observer on the ground falls within the satellite's
        sensor swath during a pass.

        Geometry (nadir-pointing model, conservative for agile sats):
          At maximum elevation θ (degrees), the horizontal distance from the
          observer to the sub-satellite point is approximately:

              cross_track_km ≈ altitude_km / tan(θ)

          The observer is in-swath if cross_track_km ≤ swath_half_width_km.

        Parameters
        ----------
        norad_id          : NORAD catalogue number
        max_elevation_deg : maximum elevation of the pass as seen by observer
        satellite_alt_km  : current satellite altitude (from TLE, optional;
                            falls back to FOV-data altitude or 600 km default)

        Returns
        -------
        bool  – True if observer is plausibly inside the swath, False otherwise.
                Returns True if NORAD ID not in FOV database (safe default).
        """
        import math

        fov_data = self.satellites.get(norad_id)
        if not fov_data:
            return True        # Unknown satellite – don't filter out

        swath_km = fov_data.get('default_swath', 0)

        if swath_km == 0:
            # Nadir-only instrument (altimeter) – only valid if nearly overhead
            return max_elevation_deg >= 85.0

        # Half swath width (one side of ground track)
        half_swath_km = swath_km / 2.0

        # Altitude: prefer live value, then FOV-data value, then LEO default
        alt_km = (satellite_alt_km
                  or fov_data.get('altitude_km')
                  or 600.0)

        if max_elevation_deg <= 0:
            return False

        # Cross-track distance from observer to satellite ground-track
        el_rad = math.radians(max_elevation_deg)
        cross_track_km = alt_km / math.tan(el_rad)

        return cross_track_km <= half_swath_km

    def get_sensor_type(self, norad_id: int) -> str:
        """Return sensor_type string for a NORAD ID, or 'optical' as default."""
        fov_data = self.satellites.get(norad_id)
        if fov_data:
            return fov_data.get('sensor_type', 'optical')
        return 'optical'

    def get_satellite_fov(self, norad_id):
        """Get FOV data for a specific satellite"""
        return self.satellites.get(norad_id)
    
    def is_earth_observation_satellite(self, norad_id):
        """Check if satellite is in our EO database"""
        return norad_id in self.satellites
    
    def calculate_coverage_footprint(self, norad_id, satellite_lat, satellite_lon, satellite_alt):
        """Calculate actual coverage footprint based on FOV and altitude"""
        import math
        
        sat_data = self.get_satellite_fov(norad_id)
        if not sat_data:
            return None
        
        # Get default swath width
        swath_width_km = sat_data['default_swath']
        
        # For nadir-only instruments (like altimeters)
        if swath_width_km == 0:
            return {
                'type': 'nadir_only',
                'footprint_radius': 0.1,  # Very small footprint for nadir instruments
                'swath_width': 0
            }
        
        # Calculate ground footprint based on satellite altitude and FOV
        earth_radius = 6371.0  # km
        
        # Calculate nadir angle for swath edges
        if 'fov_modes' in sat_data:
            # Use the most common mode or first available mode
            mode_key = list(sat_data['fov_modes'].keys())[0]
            coverage_angle = sat_data['fov_modes'][mode_key]['coverage_angle']
        else:
            # Estimate coverage angle from swath width and altitude
            # Using geometry: swath_half_width = altitude * tan(half_angle)
            half_swath = swath_width_km / 2
            half_angle_rad = math.atan(half_swath / satellite_alt)
            coverage_angle = math.degrees(half_angle_rad * 2)
        
        # Calculate actual footprint considering Earth curvature
        # This is more accurate than simple trigonometry
        half_angle_rad = math.radians(coverage_angle / 2)
        
        # Ground range calculation considering Earth curvature
        sin_half_angle = math.sin(half_angle_rad)
        cos_half_angle = math.cos(half_angle_rad)
        
        # Distance from Earth center to satellite
        sat_distance = earth_radius + satellite_alt
        
        # Ground range to swath edge (accounting for Earth curvature)
        ground_range = earth_radius * math.asin(
            (sat_distance * sin_half_angle) / earth_radius
        ) if (sat_distance * sin_half_angle) / earth_radius <= 1.0 else swath_width_km / 2
        
        ground_range_km = ground_range * earth_radius / earth_radius if ground_range < 1 else ground_range
        
        return {
            'type': 'swath',
            'swath_width': swath_width_km,
            'coverage_angle': coverage_angle,
            'ground_range_km': ground_range_km,
            'footprint_radius': swath_width_km / 2,  # Simplified for pass calculations
        }
    
    def get_all_eo_satellites(self):
        """Get all Earth observation satellites in database"""
        return list(self.satellites.keys())
