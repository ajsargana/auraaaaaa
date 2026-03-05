
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

            # ── GOSAT / IBUKI (JAXA carbon) — correct NORAD is 33492 ─────────
            33492: {
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

            # ── KENT RIDGE 1 (Singapore, PSLV-C29 Dec 2015) ──────────────────
            41172: {  # NORAD approximate; distinct from ALSAT-1B (41789)
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

            # ── GPM Core Observatory — correct NORAD 39574 (SMAP is 40376) ──
            39574: {
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

            # ──────────────────────────────────────────────────────────────
            # EXTENDED DATABASE – added 2026-03
            # Sources: ESA, NASA, NOAA, JAXA, ISRO, CMA, ASI, DLR, CSA,
            #          space-track.org estimates, published mission docs.
            # NORADs marked "approx" should be verified on space-track.org.
            # ──────────────────────────────────────────────────────────────

            # ═══════════════ ESA EARTH OBSERVATION ════════════════════════

            # ── CryoSat-2 (ESA Ku-band radar altimeter, ice/ocean) ────────
            36508: {
                'name': 'CRYOSAT-2',
                'fov_modes': {
                    'SAR':   {'swath_width': 1,  'coverage_angle': 0.08},
                    'SARIn': {'swath_width': 15, 'coverage_angle': 1.2},
                },
                'default_swath': 1,
                'sensors': ['SIRAL Ku-band Radar Altimeter (SAR/SARIn/LRM modes)'],
                'sensor_type': 'altimeter',
                'country': 'ESA',
                'altitude_km': 717,
                'launch_date': '2010-04-08',
            },

            # ── ADM-Aeolus (ESA UV wind lidar, decommissioned 2023-07) ────
            43600: {
                'name': 'ADM-AEOLUS',
                'fov_modes': {
                    'ALADIN': {'swath_width': 10, 'coverage_angle': 35.0},
                },
                'default_swath': 10,
                'sensors': ['ALADIN UV Doppler Wind Lidar 355nm (decommissioned 2023-07)'],
                'sensor_type': 'lidar',
                'country': 'ESA',
                'altitude_km': 320,
                'launch_date': '2018-08-22',
            },

            # ── PROBA-V (ESA vegetation monitor, 3-camera wide swath) ─────
            39159: {
                'name': 'PROBA-V',
                'fov_modes': {
                    'VGT': {'swath_width': 2285, 'coverage_angle': 102.0},
                },
                'default_swath': 2285,
                'sensors': ['Vegetation 4-band VNIR/SWIR (100m centre, 300m side)'],
                'sensor_type': 'multispectral',
                'country': 'ESA',
                'altitude_km': 820,
                'launch_date': '2013-05-07',
            },

            # ── PROBA-1 (ESA tech demo, hyperspectral, still operational) ─
            26958: {
                'name': 'PROBA-1',
                'fov_modes': {
                    'CHRIS': {'swath_width': 14, 'coverage_angle': 1.3},
                    'HRC':   {'swath_width': 14, 'coverage_angle': 1.3},
                },
                'default_swath': 14,
                'sensors': ['CHRIS Hyperspectral 18-62 bands 400-1050nm 17m (5 angles)',
                            'HRC 6m PAN'],
                'sensor_type': 'hyperspectral',
                'country': 'ESA',
                'altitude_km': 615,
                'launch_date': '2001-10-22',
            },

            # ── Swarm A / B / C (ESA geomagnetic field constellation) ─────
            39452: {
                'name': 'SWARM-A',
                'fov_modes': {'VFM': {'swath_width': 0, 'coverage_angle': 0}},
                'default_swath': 0,
                'sensors': ['VFM Vector Field Magnetometer, ASM, EFI, GPS'],
                'sensor_type': 'other',
                'country': 'ESA',
                'altitude_km': 460,
                'launch_date': '2013-11-22',
            },
            39451: {
                'name': 'SWARM-B',
                'fov_modes': {'VFM': {'swath_width': 0, 'coverage_angle': 0}},
                'default_swath': 0,
                'sensors': ['VFM Vector Field Magnetometer, ASM, EFI, GPS'],
                'sensor_type': 'other',
                'country': 'ESA',
                'altitude_km': 510,
                'launch_date': '2013-11-22',
            },
            39453: {
                'name': 'SWARM-C',
                'fov_modes': {'VFM': {'swath_width': 0, 'coverage_angle': 0}},
                'default_swath': 0,
                'sensors': ['VFM Vector Field Magnetometer, ASM, EFI, GPS'],
                'sensor_type': 'other',
                'country': 'ESA',
                'altitude_km': 460,
                'launch_date': '2013-11-22',
            },

            # ── EarthCARE (ESA/JAXA cloud+aerosol profiler, 2024) ─────────
            59996: {  # NORAD approx; verify on space-track.org
                'name': 'EARTHCARE',
                'fov_modes': {
                    'MSI': {'swath_width': 150, 'coverage_angle': 10.6},
                    'CPR': {'swath_width': 1,   'coverage_angle': 0.07},
                },
                'default_swath': 150,
                'sensors': ['CPR 94GHz W-band Radar', 'ATLID UV Lidar 355nm',
                            'MSI 7-band 500m', 'BBR Broadband Radiometer'],
                'sensor_type': 'lidar',
                'country': 'ESA/JAXA',
                'altitude_km': 393,
                'launch_date': '2024-05-28',
            },

            # ── Sentinel-1B (ESA C-SAR, FAILED 2022-08-23) ───────────────
            41456: {
                'name': 'SENTINEL-1B',
                'fov_modes': {
                    'IW': {'swath_width': 250, 'coverage_angle': 30.45},
                    'EW': {'swath_width': 400, 'coverage_angle': 45.0},
                },
                'default_swath': 250,
                'sensors': ['C-band SAR (FAILED 2022-08-23)'],
                'sensor_type': 'SAR',
                'country': 'ESA',
                'altitude_km': 693,
                'launch_date': '2016-04-25',
            },

            # ── Sentinel-1C (ESA C-SAR, launched 2024-12-05) ─────────────
            61950: {  # NORAD approx; verify on space-track.org
                'name': 'SENTINEL-1C',
                'fov_modes': {
                    'IW': {'swath_width': 250, 'coverage_angle': 30.45},
                    'EW': {'swath_width': 400, 'coverage_angle': 45.0},
                },
                'default_swath': 250,
                'sensors': ['C-band SAR (replaces Sentinel-1B)'],
                'sensor_type': 'SAR',
                'country': 'ESA',
                'altitude_km': 693,
                'launch_date': '2024-12-05',
            },

            # ── Sentinel-2C (ESA MSI, launched 2024-09-04) ───────────────
            61321: {  # NORAD approx; verify on space-track.org
                'name': 'SENTINEL-2C',
                'fov_modes': {
                    'MSI': {'swath_width': 290, 'coverage_angle': 20.6},
                },
                'default_swath': 290,
                'sensors': ['MSI 13 bands 10/20/60m VNIR-SWIR (replaces Sentinel-2A)'],
                'sensor_type': 'multispectral',
                'country': 'ESA',
                'altitude_km': 786,
                'launch_date': '2024-09-04',
            },

            # ═══════════════ NASA / CNES EARTH SCIENCE ════════════════════

            # ── OCO-2 (NASA CO2 column measurement) ──────────────────────
            40059: {
                'name': 'OCO-2',
                'fov_modes': {
                    'Nadir': {'swath_width': 10.6, 'coverage_angle': 0.86},
                    'Glint': {'swath_width': 10.6, 'coverage_angle': 0.86},
                },
                'default_swath': 10.6,
                'sensors': ['NIR/SWIR Spectrometer 3-ch (O2 A-band, CO2 1.61μm, CO2 2.06μm)'],
                'sensor_type': 'hyperspectral',
                'country': 'NASA',
                'altitude_km': 705,
                'launch_date': '2014-07-02',
            },

            # ── ICESat-2 (NASA photon-counting lidar) ────────────────────
            43613: {
                'name': 'ICESAT-2',
                'fov_modes': {
                    'ATLAS': {'swath_width': 3.3, 'coverage_angle': 0.27},
                },
                'default_swath': 3.3,
                'sensors': ['ATLAS 532nm Photon-counting Lidar (6 beams, 17m footprint, 70cm vert)'],
                'sensor_type': 'lidar',
                'country': 'NASA',
                'altitude_km': 496,
                'launch_date': '2018-09-15',
            },

            # ── GRACE-FO 1 & 2 (NASA/DLR gravity field tandem) ───────────
            43476: {
                'name': 'GRACE-FO-1',
                'fov_modes': {'MWI': {'swath_width': 0, 'coverage_angle': 0}},
                'default_swath': 0,
                'sensors': ['K/Ka-band Microwave Ranging Instrument', 'LRI Laser Interferometer', 'GPS', 'Accelerometer'],
                'sensor_type': 'other',
                'country': 'NASA/DLR',
                'altitude_km': 490,
                'launch_date': '2018-05-22',
            },
            43477: {
                'name': 'GRACE-FO-2',
                'fov_modes': {'MWI': {'swath_width': 0, 'coverage_angle': 0}},
                'default_swath': 0,
                'sensors': ['K/Ka-band Microwave Ranging Instrument', 'LRI Laser Interferometer'],
                'sensor_type': 'other',
                'country': 'NASA/DLR',
                'altitude_km': 490,
                'launch_date': '2018-05-22',
            },

            # ── CloudSat (NASA W-band cloud radar, decommissioned 2023) ──
            29107: {
                'name': 'CLOUDSAT',
                'fov_modes': {
                    'CPR': {'swath_width': 1.4, 'coverage_angle': 0.11},
                },
                'default_swath': 1.4,
                'sensors': ['CPR 94GHz W-band Cloud Profiling Radar (decommissioned 2023-03)'],
                'sensor_type': 'weather',
                'country': 'NASA',
                'altitude_km': 705,
                'launch_date': '2006-04-28',
            },

            # ── CALIPSO (NASA/CNES dual-wavelength lidar, decom. 2023) ───
            29108: {
                'name': 'CALIPSO',
                'fov_modes': {
                    'CALIOP': {'swath_width': 0.1, 'coverage_angle': 0.009},
                    'WFC':    {'swath_width': 61,  'coverage_angle': 5.0},
                },
                'default_swath': 0.1,
                'sensors': ['CALIOP 532/1064nm Lidar', 'IIR 3-band IR Imager',
                            'WFC 645nm Wide-field Camera (decommissioned 2023-08)'],
                'sensor_type': 'lidar',
                'country': 'NASA/CNES',
                'altitude_km': 705,
                'launch_date': '2006-04-28',
            },

            # ── CYGNSS 1-8 (NASA GNSS-R ocean wind constellation) ────────
            42917: {'name': 'CYGNSS-1', 'fov_modes': {'DDMI': {'swath_width': 25, 'coverage_angle': 0}}, 'default_swath': 25, 'sensors': ['DDMI GNSS-R L1 GPS ocean wind'], 'sensor_type': 'weather', 'country': 'NASA', 'altitude_km': 520, 'launch_date': '2016-12-15'},
            42918: {'name': 'CYGNSS-2', 'fov_modes': {'DDMI': {'swath_width': 25, 'coverage_angle': 0}}, 'default_swath': 25, 'sensors': ['DDMI GNSS-R L1 GPS ocean wind'], 'sensor_type': 'weather', 'country': 'NASA', 'altitude_km': 520, 'launch_date': '2016-12-15'},
            42919: {'name': 'CYGNSS-3', 'fov_modes': {'DDMI': {'swath_width': 25, 'coverage_angle': 0}}, 'default_swath': 25, 'sensors': ['DDMI GNSS-R L1 GPS ocean wind'], 'sensor_type': 'weather', 'country': 'NASA', 'altitude_km': 520, 'launch_date': '2016-12-15'},
            42920: {'name': 'CYGNSS-4', 'fov_modes': {'DDMI': {'swath_width': 25, 'coverage_angle': 0}}, 'default_swath': 25, 'sensors': ['DDMI GNSS-R L1 GPS ocean wind'], 'sensor_type': 'weather', 'country': 'NASA', 'altitude_km': 520, 'launch_date': '2016-12-15'},
            42921: {'name': 'CYGNSS-5', 'fov_modes': {'DDMI': {'swath_width': 25, 'coverage_angle': 0}}, 'default_swath': 25, 'sensors': ['DDMI GNSS-R L1 GPS ocean wind'], 'sensor_type': 'weather', 'country': 'NASA', 'altitude_km': 520, 'launch_date': '2016-12-15'},
            42922: {'name': 'CYGNSS-6', 'fov_modes': {'DDMI': {'swath_width': 25, 'coverage_angle': 0}}, 'default_swath': 25, 'sensors': ['DDMI GNSS-R L1 GPS ocean wind'], 'sensor_type': 'weather', 'country': 'NASA', 'altitude_km': 520, 'launch_date': '2016-12-15'},
            42923: {'name': 'CYGNSS-7', 'fov_modes': {'DDMI': {'swath_width': 25, 'coverage_angle': 0}}, 'default_swath': 25, 'sensors': ['DDMI GNSS-R L1 GPS ocean wind'], 'sensor_type': 'weather', 'country': 'NASA', 'altitude_km': 520, 'launch_date': '2016-12-15'},
            42924: {'name': 'CYGNSS-8', 'fov_modes': {'DDMI': {'swath_width': 25, 'coverage_angle': 0}}, 'default_swath': 25, 'sensors': ['DDMI GNSS-R L1 GPS ocean wind'], 'sensor_type': 'weather', 'country': 'NASA', 'altitude_km': 520, 'launch_date': '2016-12-15'},

            # ── TEMPO (NASA air quality GEO – hosted on Intelsat 40E) ────
            56217: {
                'name': 'TEMPO',
                'fov_modes': {
                    'UV-Vis': {'swath_width': 4000, 'coverage_angle': 47.0},
                },
                'default_swath': 4000,
                'sensors': ['UV/Vis/NIR Spectrometer 290-740nm (NO2 O3 SO2 HCHO; 10km GEO)'],
                'sensor_type': 'hyperspectral',
                'country': 'NASA',
                'altitude_km': 35786,
                'launch_date': '2023-04-07',
            },

            # ── PACE (NASA hyperspectral ocean color, launched 2024-02) ──
            58928: {  # NORAD approx; verify on space-track.org
                'name': 'PACE',
                'fov_modes': {
                    'OCI':   {'swath_width': 2663, 'coverage_angle': 116.0},
                    'HARP2': {'swath_width': 3000, 'coverage_angle': 94.0},
                },
                'default_swath': 2663,
                'sensors': ['OCI Hyperspectral 339-900nm+SWIR 1km',
                            'SPEXone Multi-angle Polarimeter 5.4km',
                            'HARP2 Rainbow Polarimeter 3km'],
                'sensor_type': 'hyperspectral',
                'country': 'NASA',
                'altitude_km': 677,
                'launch_date': '2024-02-08',
            },

            # ── SWOT (NASA/CNES Ka-band wide-swath altimeter, 2022) ──────
            54754: {
                'name': 'SWOT',
                'fov_modes': {
                    'KaRIn': {'swath_width': 120, 'coverage_angle': 2.5},
                },
                'default_swath': 120,
                'sensors': ['KaRIn 35.75GHz Ka-band Radar Interferometer (2×50km + 20km gap)'],
                'sensor_type': 'altimeter',
                'country': 'NASA/CNES',
                'altitude_km': 891,
                'launch_date': '2022-12-16',
            },

            # ═══════════════ NOAA SATELLITES ════════════════════════════

            # ── NOAA-15 / 18 / 19 (AVHRR polar orbiters) ────────────────
            25338: {
                'name': 'NOAA-15',
                'fov_modes': {
                    'AVHRR': {'swath_width': 2900, 'coverage_angle': 110.0},
                },
                'default_swath': 2900,
                'sensors': ['AVHRR/3 6-band VIS-TIR 1.1km', 'HIRS/3', 'AMSU-A', 'AMSU-B'],
                'sensor_type': 'weather',
                'country': 'NOAA',
                'altitude_km': 810,
                'launch_date': '1998-05-13',
            },
            28654: {
                'name': 'NOAA-18',
                'fov_modes': {
                    'AVHRR': {'swath_width': 2900, 'coverage_angle': 110.0},
                },
                'default_swath': 2900,
                'sensors': ['AVHRR/3 6-band VIS-TIR 1.1km', 'HIRS/4', 'AMSU-A', 'MHS'],
                'sensor_type': 'weather',
                'country': 'NOAA',
                'altitude_km': 854,
                'launch_date': '2005-05-20',
            },
            # 33591 = NOAA-19 (was incorrectly labelled GOSAT above; GOSAT fixed to 33492)
            33591: {
                'name': 'NOAA-19',
                'fov_modes': {
                    'AVHRR': {'swath_width': 2900, 'coverage_angle': 110.0},
                },
                'default_swath': 2900,
                'sensors': ['AVHRR/3 6-band VIS-TIR 1.1km', 'HIRS/4', 'AMSU-A', 'MHS'],
                'sensor_type': 'weather',
                'country': 'NOAA',
                'altitude_km': 870,
                'launch_date': '2009-02-06',
            },

            # ── NOAA-21 / JPSS-2 (VIIRS, launched 2022-11-10) ────────────
            54234: {
                'name': 'NOAA-21 (JPSS-2)',
                'fov_modes': {
                    'VIIRS': {'swath_width': 3040, 'coverage_angle': 112.0},
                },
                'default_swath': 3040,
                'sensors': ['VIIRS 22-band 375m/750m', 'CrIS 2211-ch Sounder',
                            'ATMS 22-ch Microwave', 'OMPS Ozone', 'CERES'],
                'sensor_type': 'weather',
                'country': 'NOAA/NASA',
                'altitude_km': 824,
                'launch_date': '2022-11-10',
            },

            # ── GOES-16 / 17 / 18 (GOES-R GEO weather) ──────────────────
            41866: {
                'name': 'GOES-16',
                'fov_modes': {
                    'ABI_Full':  {'swath_width': 17400, 'coverage_angle': 17.4},
                    'ABI_CONUS': {'swath_width': 5000,  'coverage_angle': 5.0},
                },
                'default_swath': 17400,
                'sensors': ['ABI 16-band 0.47-13.3μm (0.5/1/2km)',
                            'GLM Geostationary Lightning Mapper', 'EXIS', 'SUVI', 'SEISS', 'MAG'],
                'sensor_type': 'weather',
                'country': 'NOAA',
                'altitude_km': 35786,
                'launch_date': '2016-11-19',
            },
            43226: {
                'name': 'GOES-17',
                'fov_modes': {
                    'ABI_Full': {'swath_width': 17400, 'coverage_angle': 17.4},
                },
                'default_swath': 17400,
                'sensors': ['ABI 16-band (cooling anomaly limits night thermal)', 'GLM', 'EXIS'],
                'sensor_type': 'weather',
                'country': 'NOAA',
                'altitude_km': 35786,
                'launch_date': '2018-03-01',
            },
            51850: {
                'name': 'GOES-18',
                'fov_modes': {
                    'ABI_Full':  {'swath_width': 17400, 'coverage_angle': 17.4},
                    'ABI_CONUS': {'swath_width': 5000,  'coverage_angle': 5.0},
                },
                'default_swath': 17400,
                'sensors': ['ABI 16-band 0.47-13.3μm (0.5/1/2km)',
                            'GLM Lightning Mapper', 'EXIS', 'SEISS', 'MAG'],
                'sensor_type': 'weather',
                'country': 'NOAA',
                'altitude_km': 35786,
                'launch_date': '2022-03-01',
            },

            # ═══════════════ JAXA SATELLITES ════════════════════════════

            # ── GCOM-W / SHIZUKU (JAXA passive microwave radiometer) ─────
            38337: {
                'name': 'GCOM-W (SHIZUKU)',
                'fov_modes': {
                    'AMSR2': {'swath_width': 1450, 'coverage_angle': 74.0},
                },
                'default_swath': 1450,
                'sensors': ['AMSR2 Passive Microwave 6.9-89GHz 7-freq (3-62km res)'],
                'sensor_type': 'weather',
                'country': 'JAXA',
                'altitude_km': 700,
                'launch_date': '2012-05-17',
            },

            # ── GCOM-C / SHIKISAI (JAXA multi-parameter imager) ──────────
            43065: {
                'name': 'GCOM-C (SHIKISAI)',
                'fov_modes': {
                    'SGLI': {'swath_width': 1150, 'coverage_angle': 57.0},
                },
                'default_swath': 1150,
                'sensors': ['SGLI 19-band UV-TIR (250m VNR, 500m-1km IRS, polarization)'],
                'sensor_type': 'multispectral',
                'country': 'JAXA',
                'altitude_km': 798,
                'launch_date': '2017-12-23',
            },

            # ── Himawari-8 & 9 (JMA GEO weather, 16-band AHI) ───────────
            40267: {
                'name': 'HIMAWARI-8',
                'fov_modes': {
                    'AHI_Full': {'swath_width': 14000, 'coverage_angle': 18.0},
                },
                'default_swath': 14000,
                'sensors': ['AHI 16-band 0.47-13.3μm (0.5/1/2km); 10-min full disk'],
                'sensor_type': 'weather',
                'country': 'Japan/JMA',
                'altitude_km': 35786,
                'launch_date': '2014-10-07',
            },
            41836: {
                'name': 'HIMAWARI-9',
                'fov_modes': {
                    'AHI_Full': {'swath_width': 14000, 'coverage_angle': 18.0},
                },
                'default_swath': 14000,
                'sensors': ['AHI 16-band 0.47-13.3μm (0.5/1/2km); primary since Dec 2022'],
                'sensor_type': 'weather',
                'country': 'Japan/JMA',
                'altitude_km': 35786,
                'launch_date': '2016-11-02',
            },

            # ── ALOS-2 (JAXA L-band SAR PALSAR-2) ────────────────────────
            39766: {
                'name': 'ALOS-2',
                'fov_modes': {
                    'Spotlight': {'swath_width': 25,  'coverage_angle': 2.3},
                    'StripMap':  {'swath_width': 70,  'coverage_angle': 6.4},
                    'ScanSAR':   {'swath_width': 350, 'coverage_angle': 32.0},
                },
                'default_swath': 70,
                'sensors': ['PALSAR-2 L-band SAR 1.27GHz (1-100m, fully polarimetric, right/left)'],
                'sensor_type': 'SAR',
                'country': 'JAXA',
                'altitude_km': 628,
                'launch_date': '2014-05-24',
            },

            # ── ALOS-4 (JAXA L-band SAR PALSAR-3, launched 2024-07) ──────
            60042: {  # NORAD approx; verify on space-track.org
                'name': 'ALOS-4',
                'fov_modes': {
                    'Spotlight':  {'swath_width': 28,  'coverage_angle': 2.4},
                    'StripMap':   {'swath_width': 70,  'coverage_angle': 6.0},
                    'ScanSAR':    {'swath_width': 200, 'coverage_angle': 17.2},
                    'UltraWide':  {'swath_width': 500, 'coverage_angle': 43.0},
                },
                'default_swath': 200,
                'sensors': ['PALSAR-3 L-band SAR (1-60m, compact polarimetry, wider swath than PALSAR-2)'],
                'sensor_type': 'SAR',
                'country': 'JAXA',
                'altitude_km': 669,
                'launch_date': '2024-07-01',
            },

            # ═══════════════ ISRO (INDIA) ═══════════════════════════════

            # ── Cartosat-3 (ISRO VHR optical, 0.25m) ────────────────────
            44792: {
                'name': 'CARTOSAT-3',
                'fov_modes': {
                    'PAN': {'swath_width': 16, 'coverage_angle': 1.8},
                    'MS':  {'swath_width': 16, 'coverage_angle': 1.8},
                },
                'default_swath': 16,
                'sensors': ['0.25m PAN, 1m MS 4-band'],
                'sensor_type': 'optical',
                'country': 'India/ISRO',
                'altitude_km': 509,
                'launch_date': '2019-11-27',
            },

            # ── RISAT-2B / BR1 / BR2 (ISRO X-band SAR) ──────────────────
            44233: {
                'name': 'RISAT-2B',
                'fov_modes': {
                    'Spotlight': {'swath_width': 4,  'coverage_angle': 0.41},
                    'Strip':     {'swath_width': 25, 'coverage_angle': 2.58},
                    'ScanSAR':   {'swath_width': 75, 'coverage_angle': 7.75},
                },
                'default_swath': 25,
                'sensors': ['X-band SAR (1m Spotlight, 3m Strip, 9m ScanSAR)'],
                'sensor_type': 'SAR',
                'country': 'India/ISRO',
                'altitude_km': 556,
                'launch_date': '2019-05-22',
            },
            45231: {
                'name': 'RISAT-2BR1',
                'fov_modes': {
                    'Spotlight': {'swath_width': 4,  'coverage_angle': 0.40},
                    'Strip':     {'swath_width': 25, 'coverage_angle': 2.49},
                    'ScanSAR':   {'swath_width': 75, 'coverage_angle': 7.46},
                },
                'default_swath': 25,
                'sensors': ['X-band SAR (0.5m Spotlight, 3m Strip, 9m ScanSAR)'],
                'sensor_type': 'SAR',
                'country': 'India/ISRO',
                'altitude_km': 576,
                'launch_date': '2019-12-11',
            },
            47291: {
                'name': 'RISAT-2BR2',
                'fov_modes': {
                    'Spotlight': {'swath_width': 4,  'coverage_angle': 0.40},
                    'Strip':     {'swath_width': 25, 'coverage_angle': 2.49},
                    'ScanSAR':   {'swath_width': 75, 'coverage_angle': 7.46},
                },
                'default_swath': 25,
                'sensors': ['X-band SAR (0.5m Spotlight, 3m Strip, 9m ScanSAR)'],
                'sensor_type': 'SAR',
                'country': 'India/ISRO',
                'altitude_km': 576,
                'launch_date': '2021-02-28',
            },

            # ── EOS-01 / RISAT-2BR3 (ISRO X-band SAR) ───────────────────
            46915: {
                'name': 'EOS-01 (RISAT-2BR3)',
                'fov_modes': {
                    'Strip':   {'swath_width': 25, 'coverage_angle': 2.49},
                    'ScanSAR': {'swath_width': 75, 'coverage_angle': 7.46},
                },
                'default_swath': 25,
                'sensors': ['X-band SAR (1m Strip, 6m ScanSAR)'],
                'sensor_type': 'SAR',
                'country': 'India/ISRO',
                'altitude_km': 576,
                'launch_date': '2020-11-07',
            },

            # ── EOS-04 / RISAT-1A (ISRO C-band SAR) ─────────────────────
            51657: {
                'name': 'EOS-04 (RISAT-1A)',
                'fov_modes': {
                    'FRS':  {'swath_width': 25,  'coverage_angle': 2.71},
                    'MRS':  {'swath_width': 100, 'coverage_angle': 10.83},
                    'CRS':  {'swath_width': 500, 'coverage_angle': 54.2},
                },
                'default_swath': 100,
                'sensors': ['C-band SAR (3m FRS, 25m MRS, 50m CRS ScanSAR)'],
                'sensor_type': 'SAR',
                'country': 'India/ISRO',
                'altitude_km': 529,
                'launch_date': '2022-02-14',
            },

            # ── Resourcesat-2A (ISRO multispectral) ──────────────────────
            41877: {
                'name': 'RESOURCESAT-2A',
                'fov_modes': {
                    'LISS-IV':  {'swath_width': 23,  'coverage_angle': 1.61},
                    'LISS-III': {'swath_width': 141, 'coverage_angle': 9.88},
                    'AWiFS':    {'swath_width': 740, 'coverage_angle': 51.9},
                },
                'default_swath': 141,
                'sensors': ['LISS-IV 5.8m MS 4-band', 'LISS-III 23.5m', 'AWiFS 56m wide-field'],
                'sensor_type': 'multispectral',
                'country': 'India/ISRO',
                'altitude_km': 817,
                'launch_date': '2016-12-07',
            },

            # ── Oceansat-3 / EOS-06 (ISRO ocean color + scatterometer) ───
            54357: {  # NORAD approx; launched 16 days after NOAA-21 (54234)
                'name': 'OCEANSAT-3 (EOS-06)',
                'fov_modes': {
                    'OCM-3':  {'swath_width': 1400, 'coverage_angle': 117.0},
                    'OSCAT3': {'swath_width': 1800, 'coverage_angle': 130.0},
                },
                'default_swath': 1400,
                'sensors': ['OCM-3 13-band Ocean Color 360m', 'OSCAT-3 Ku-band Scatterometer 25km',
                            'SSTM Thermal IR'],
                'sensor_type': 'multispectral',
                'country': 'India/ISRO',
                'altitude_km': 742,
                'launch_date': '2022-11-26',
            },

            # ── INSAT-3D / 3DR / 3DS (ISRO GEO weather) ─────────────────
            39216: {
                'name': 'INSAT-3D',
                'fov_modes': {
                    'Imager': {'swath_width': 8000, 'coverage_angle': 17.7},
                },
                'default_swath': 8000,
                'sensors': ['Imager 6-band 1km VIS/4km IR', 'Sounder 18-channel'],
                'sensor_type': 'weather',
                'country': 'India/ISRO',
                'altitude_km': 35786,
                'launch_date': '2013-07-26',
            },
            41752: {
                'name': 'INSAT-3DR',
                'fov_modes': {
                    'Imager': {'swath_width': 8000, 'coverage_angle': 17.7},
                },
                'default_swath': 8000,
                'sensors': ['Imager 6-band 1km VIS/4km IR', 'Sounder 18-channel'],
                'sensor_type': 'weather',
                'country': 'India/ISRO',
                'altitude_km': 35786,
                'launch_date': '2016-09-08',
            },
            58958: {  # NORAD approx; verify on space-track.org
                'name': 'INSAT-3DS',
                'fov_modes': {
                    'Imager': {'swath_width': 8000, 'coverage_angle': 17.7},
                },
                'default_swath': 8000,
                'sensors': ['Imager 6-band 1km VIS/4km IR (upgraded from 3DR)', 'Sounder 18-channel'],
                'sensor_type': 'weather',
                'country': 'India/ISRO',
                'altitude_km': 35786,
                'launch_date': '2024-02-17',
            },

            # ── HysIS (ISRO hyperspectral imager) ────────────────────────
            43719: {
                'name': 'HYSI S',
                'fov_modes': {
                    'VNIR': {'swath_width': 30, 'coverage_angle': 2.7},
                    'SWIR': {'swath_width': 30, 'coverage_angle': 2.7},
                },
                'default_swath': 30,
                'sensors': ['VNIR 55-band 400-950nm 30m', 'SWIR 256-band 900-2500nm 30m'],
                'sensor_type': 'hyperspectral',
                'country': 'India/ISRO',
                'altitude_km': 636,
                'launch_date': '2018-11-29',
            },

            # ═══════════════ CHINA – GAOFEN SERIES ══════════════════════

            # ── GAOFEN-5 (China 330-band hyperspectral) ──────────────────
            43461: {
                'name': 'GAOFEN-5',
                'fov_modes': {
                    'AHSI': {'swath_width': 60, 'coverage_angle': 4.9},
                    'VIMS': {'swath_width': 60, 'coverage_angle': 4.9},
                },
                'default_swath': 60,
                'sensors': ['AHSI 330-band Hyperspectral 0.39-2.5μm 30m',
                            'VIMS 20m MS', 'DPC Polarimeter', 'POSP', 'GMI'],
                'sensor_type': 'hyperspectral',
                'country': 'China/CAST',
                'altitude_km': 705,
                'launch_date': '2018-05-09',
            },

            # ── GAOFEN-6 (China wide-field optical + Red-Edge) ───────────
            43484: {
                'name': 'GAOFEN-6',
                'fov_modes': {
                    'PAN': {'swath_width': 9,  'coverage_angle': 0.80},
                    'WFV': {'swath_width': 90, 'coverage_angle': 8.0},
                },
                'default_swath': 90,
                'sensors': ['2m PAN, 8m MS 4-band, 16m WFV 8-band (incl. Red Edge)'],
                'sensor_type': 'multispectral',
                'country': 'China/CAST',
                'altitude_km': 645,
                'launch_date': '2018-06-02',
            },

            # ── GAOFEN-8 (China VHR dual-use optical) ────────────────────
            40890: {
                'name': 'GAOFEN-8',
                'fov_modes': {
                    'PAN': {'swath_width': 15, 'coverage_angle': 1.65},
                },
                'default_swath': 15,
                'sensors': ['~0.5-0.8m PAN (dual-use optical)'],
                'sensor_type': 'optical',
                'country': 'China/CAST',
                'altitude_km': 519,
                'launch_date': '2015-06-26',
            },

            # ── GAOFEN-10 (China VHR optical, 2019 launch) ───────────────
            44710: {
                'name': 'GAOFEN-10',
                'fov_modes': {
                    'PAN': {'swath_width': 15, 'coverage_angle': 1.72},
                },
                'default_swath': 15,
                'sensors': ['~0.5m PAN (dual-use optical; 2016 launch failed, relaunched 2019)'],
                'sensor_type': 'optical',
                'country': 'China/CAST',
                'altitude_km': 500,
                'launch_date': '2019-10-05',
            },

            # ── GAOFEN-11 (China VHR optical) ────────────────────────────
            43637: {
                'name': 'GAOFEN-11',
                'fov_modes': {
                    'PAN': {'swath_width': 15, 'coverage_angle': 1.76},
                },
                'default_swath': 15,
                'sensors': ['~0.5m PAN (dual-use optical)'],
                'sensor_type': 'optical',
                'country': 'China/CAST',
                'altitude_km': 490,
                'launch_date': '2018-07-31',
            },

            # ── GAOFEN-13 (China GEO VHR optical) ────────────────────────
            46551: {
                'name': 'GAOFEN-13',
                'fov_modes': {
                    'GEO_PAN': {'swath_width': 400, 'coverage_angle': 0.64},
                },
                'default_swath': 400,
                'sensors': ['GEO optical ~0.5-1m PAN + MS (geostationary high-res)'],
                'sensor_type': 'optical',
                'country': 'China/CAST',
                'altitude_km': 35786,
                'launch_date': '2020-10-12',
            },

            # ── GAOFEN-14 (China stereo + laser altimeter) ───────────────
            47210: {
                'name': 'GAOFEN-14',
                'fov_modes': {
                    'Stereo': {'swath_width': 27, 'coverage_angle': 3.09},
                },
                'default_swath': 27,
                'sensors': ['0.5m Nadir PAN stereo, 2m MS 4-band, Laser Altimeter'],
                'sensor_type': 'optical',
                'country': 'China/CAST',
                'altitude_km': 500,
                'launch_date': '2021-01-29',
            },

            # ═══════════════ CHINA – FY WEATHER ═════════════════════════

            # ── FY-3D / 3E / 3F (polar-orbit weather imagers) ────────────
            43010: {
                'name': 'FY-3D',
                'fov_modes': {
                    'MERSI-II': {'swath_width': 2900, 'coverage_angle': 110.6},
                },
                'default_swath': 2900,
                'sensors': ['MERSI-II 25-band 250m/1km', 'MWRI Microwave', 'HIRAS Sounder'],
                'sensor_type': 'weather',
                'country': 'China/CMA',
                'altitude_km': 836,
                'launch_date': '2017-11-15',
            },
            49008: {
                'name': 'FY-3E',
                'fov_modes': {
                    'MERSI-LL': {'swath_width': 2900, 'coverage_angle': 110.6},
                },
                'default_swath': 2900,
                'sensors': ['MERSI-LL 6-band low-light 250m/1km (dawn-dusk orbit)', 'MWTS-3', 'MWRI-RM'],
                'sensor_type': 'weather',
                'country': 'China/CMA',
                'altitude_km': 836,
                'launch_date': '2021-07-05',
            },
            57490: {
                'name': 'FY-3F',
                'fov_modes': {
                    'MERSI': {'swath_width': 2900, 'coverage_angle': 110.6},
                },
                'default_swath': 2900,
                'sensors': ['MERSI Enhanced 25+ bands 250m/1km', 'MWTS', 'MWRI-2', 'HIRAS'],
                'sensor_type': 'weather',
                'country': 'China/CMA',
                'altitude_km': 836,
                'launch_date': '2023-08-03',
            },
            56171: {
                'name': 'FY-3G',
                'fov_modes': {
                    'PMR':  {'swath_width': 800,  'coverage_angle': 70.0},
                    'MWRI': {'swath_width': 2300, 'coverage_angle': 100.0},
                },
                'default_swath': 800,
                'sensors': ['PMR Ka+Ku Dual-freq Precipitation Radar 5km',
                            'MWRI-RM 15km@89GHz', 'MERSI', 'HAOC (50deg inclined orbit)'],
                'sensor_type': 'weather',
                'country': 'China/CMA',
                'altitude_km': 407,
                'launch_date': '2023-04-16',
            },

            # ── FY-4A / 4B (GEO imager+sounder) ─────────────────────────
            41882: {
                'name': 'FY-4A',
                'fov_modes': {
                    'AGRI': {'swath_width': 14000, 'coverage_angle': 18.0},
                },
                'default_swath': 14000,
                'sensors': ['AGRI 14-band 0.5-4km 0.47-13.8μm',
                            'GIIRS 1650-ch Sounder', 'LMI Lightning', 'SEP'],
                'sensor_type': 'weather',
                'country': 'China/CMA',
                'altitude_km': 35786,
                'launch_date': '2016-12-11',
            },
            49015: {
                'name': 'FY-4B',
                'fov_modes': {
                    'AGRI': {'swath_width': 14000, 'coverage_angle': 18.0},
                },
                'default_swath': 14000,
                'sensors': ['AGRI 16-band 0.5-2km (enhanced vs 4A)',
                            'GIIRS-B 2000+ ch', 'LMI', 'GHI Solar Irradiance'],
                'sensor_type': 'weather',
                'country': 'China/CMA',
                'altitude_km': 35786,
                'launch_date': '2021-06-03',
            },

            # ═══════════════ CHINA – OCEAN SATELLITES ═══════════════════

            # ── HY-2A / 2C / 2D (China ocean dynamics scatterometer) ─────
            37781: {
                'name': 'HY-2A',
                'fov_modes': {
                    'Scatterometer': {'swath_width': 1700, 'coverage_angle': 130.0},
                    'Radiometer':    {'swath_width': 1600, 'coverage_angle': 120.0},
                },
                'default_swath': 1700,
                'sensors': ['Ku-band Radar Altimeter', 'Ku/C Scatterometer 25km',
                            'SSMR Microwave Radiometer 50km', 'DORIS'],
                'sensor_type': 'altimeter',
                'country': 'China/NSOAS',
                'altitude_km': 963,
                'launch_date': '2011-08-16',
            },
            46114: {
                'name': 'HY-2C',
                'fov_modes': {
                    'Scatterometer': {'swath_width': 1700, 'coverage_angle': 130.0},
                    'Radiometer':    {'swath_width': 1600, 'coverage_angle': 120.0},
                },
                'default_swath': 1700,
                'sensors': ['Ku/C Scatterometer', 'Radar Altimeter', 'Microwave Radiometer', 'DORIS'],
                'sensor_type': 'altimeter',
                'country': 'China/NSOAS',
                'altitude_km': 966,
                'launch_date': '2020-09-21',
            },
            49044: {
                'name': 'HY-2D',
                'fov_modes': {
                    'Scatterometer': {'swath_width': 1700, 'coverage_angle': 130.0},
                    'Radiometer':    {'swath_width': 1600, 'coverage_angle': 120.0},
                },
                'default_swath': 1700,
                'sensors': ['Ku/C Scatterometer', 'Radar Altimeter', 'Microwave Radiometer'],
                'sensor_type': 'altimeter',
                'country': 'China/NSOAS',
                'altitude_km': 966,
                'launch_date': '2021-05-19',
            },

            # ── HY-1C / 1D (China ocean color) ───────────────────────────
            43609: {
                'name': 'HY-1C',
                'fov_modes': {
                    'COCTS': {'swath_width': 2900, 'coverage_angle': 110.0},
                    'CZI':   {'swath_width': 500,  'coverage_angle': 40.0},
                },
                'default_swath': 2900,
                'sensors': ['COCTS 10-band Ocean Color/Thermal 1100m',
                            'CZI Coastal Zone Imager 50m 4-band', 'UVI', 'AIS'],
                'sensor_type': 'multispectral',
                'country': 'China/NSOAS',
                'altitude_km': 780,
                'launch_date': '2018-09-07',
            },
            47232: {
                'name': 'HY-1D',
                'fov_modes': {
                    'COCTS': {'swath_width': 2900, 'coverage_angle': 110.0},
                    'CZI':   {'swath_width': 500,  'coverage_angle': 40.0},
                },
                'default_swath': 2900,
                'sensors': ['COCTS 10-band Ocean Color/Thermal 1100m',
                            'CZI 50m 4-band', 'UVI', 'AIS'],
                'sensor_type': 'multispectral',
                'country': 'China/NSOAS',
                'altitude_km': 780,
                'launch_date': '2020-06-11',
            },

            # ═══════════════ CHINA – CBERS / ZIYUAN / LUTAN ═════════════

            # ── CBERS-4A (China/Brazil multi-sensor) ─────────────────────
            44875: {
                'name': 'CBERS-4A',
                'fov_modes': {
                    'WPM': {'swath_width': 92,  'coverage_angle': 8.38},
                    'MUX': {'swath_width': 90,  'coverage_angle': 8.20},
                    'WFI': {'swath_width': 866, 'coverage_angle': 62.0},
                },
                'default_swath': 92,
                'sensors': ['WPM 2m PAN / 8m MS', 'MUX 16m MS', 'WFI 55m', 'IRS 40m IR'],
                'sensor_type': 'multispectral',
                'country': 'China/Brazil',
                'altitude_km': 628,
                'launch_date': '2019-12-20',
            },

            # ── Ziyuan-3-01 (China stereo mapping) ───────────────────────
            38256: {
                'name': 'ZIYUAN-3-01',
                'fov_modes': {
                    'Nadir': {'swath_width': 51,  'coverage_angle': 4.3},
                    'MS':    {'swath_width': 166, 'coverage_angle': 13.7},
                },
                'default_swath': 51,
                'sensors': ['2.1m Nadir PAN TDI stereo, 3.5m Fwd/Aft PAN, 5.8m MS'],
                'sensor_type': 'optical',
                'country': 'China/SASMAC',
                'altitude_km': 506,
                'launch_date': '2012-01-09',
            },

            # ── Ziyuan-3-03 (China stereo mapping) ───────────────────────
            46699: {
                'name': 'ZIYUAN-3-03',
                'fov_modes': {
                    'Nadir': {'swath_width': 51,  'coverage_angle': 4.3},
                    'MS':    {'swath_width': 166, 'coverage_angle': 13.7},
                },
                'default_swath': 51,
                'sensors': ['2.1m Nadir PAN stereo, 2.7m Fwd/Aft PAN, 5.8m MS'],
                'sensor_type': 'optical',
                'country': 'China/SASMAC',
                'altitude_km': 506,
                'launch_date': '2020-11-06',
            },

            # ── Lutan-1A / 1B (China L-band InSAR pair) ──────────────────
            55678: {
                'name': 'LUTAN-1A',
                'fov_modes': {
                    'Spotlight': {'swath_width': 10,  'coverage_angle': 0.95},
                    'StripMap':  {'swath_width': 30,  'coverage_angle': 2.84},
                    'ScanSAR':   {'swath_width': 100, 'coverage_angle': 9.45},
                },
                'default_swath': 30,
                'sensors': ['L-band SAR InSAR (3m Strip, 5m Strip-II, 15m ScanSAR)'],
                'sensor_type': 'SAR',
                'country': 'China/CAST',
                'altitude_km': 607,
                'launch_date': '2022-01-26',
            },
            55679: {
                'name': 'LUTAN-1B',
                'fov_modes': {
                    'Spotlight': {'swath_width': 10,  'coverage_angle': 0.95},
                    'StripMap':  {'swath_width': 30,  'coverage_angle': 2.84},
                    'ScanSAR':   {'swath_width': 100, 'coverage_angle': 9.45},
                },
                'default_swath': 30,
                'sensors': ['L-band SAR InSAR (flies in formation with Lutan-1A for ground deformation)'],
                'sensor_type': 'SAR',
                'country': 'China/CAST',
                'altitude_km': 607,
                'launch_date': '2022-01-26',
            },

            # ═══════════════ ITALY / GERMANY / SPAIN – SAR ══════════════

            # ── COSMO-SkyMed 1-4 (ASI X-band SAR first generation) ───────
            31598: {
                'name': 'COSMO-SKYMED-1',
                'fov_modes': {
                    'Spotlight':  {'swath_width': 10,  'coverage_angle': 0.93},
                    'StripMap':   {'swath_width': 40,  'coverage_angle': 3.70},
                    'WideRegion': {'swath_width': 100, 'coverage_angle': 9.27},
                    'HugeRegion': {'swath_width': 200, 'coverage_angle': 18.54},
                },
                'default_swath': 40,
                'sensors': ['X-band SAR SAR-2000 (1m Spotlight, 3-15m Strip, 30m Wide, 100m Huge)'],
                'sensor_type': 'SAR',
                'country': 'Italy/ASI',
                'altitude_km': 619,
                'launch_date': '2007-06-08',
            },
            32376: {
                'name': 'COSMO-SKYMED-2',
                'fov_modes': {
                    'Spotlight':  {'swath_width': 10,  'coverage_angle': 0.93},
                    'StripMap':   {'swath_width': 40,  'coverage_angle': 3.70},
                    'WideRegion': {'swath_width': 100, 'coverage_angle': 9.27},
                    'HugeRegion': {'swath_width': 200, 'coverage_angle': 18.54},
                },
                'default_swath': 40,
                'sensors': ['X-band SAR (1m Spotlight, 3-15m Strip)'],
                'sensor_type': 'SAR',
                'country': 'Italy/ASI',
                'altitude_km': 619,
                'launch_date': '2007-12-09',
            },
            33408: {
                'name': 'COSMO-SKYMED-3',
                'fov_modes': {
                    'Spotlight':  {'swath_width': 10,  'coverage_angle': 0.93},
                    'StripMap':   {'swath_width': 40,  'coverage_angle': 3.70},
                    'WideRegion': {'swath_width': 100, 'coverage_angle': 9.27},
                    'HugeRegion': {'swath_width': 200, 'coverage_angle': 18.54},
                },
                'default_swath': 40,
                'sensors': ['X-band SAR (1m Spotlight, 3-15m Strip)'],
                'sensor_type': 'SAR',
                'country': 'Italy/ASI',
                'altitude_km': 619,
                'launch_date': '2008-10-25',
            },
            36599: {
                'name': 'COSMO-SKYMED-4',
                'fov_modes': {
                    'Spotlight':  {'swath_width': 10,  'coverage_angle': 0.93},
                    'StripMap':   {'swath_width': 40,  'coverage_angle': 3.70},
                    'WideRegion': {'swath_width': 100, 'coverage_angle': 9.27},
                    'HugeRegion': {'swath_width': 200, 'coverage_angle': 18.54},
                },
                'default_swath': 40,
                'sensors': ['X-band SAR (1m Spotlight, 3-15m Strip)'],
                'sensor_type': 'SAR',
                'country': 'Italy/ASI',
                'altitude_km': 619,
                'launch_date': '2010-11-06',
            },

            # ── COSMO-SkyMed Second Generation 1 & 2 ─────────────────────
            47390: {
                'name': 'COSMO-SKYMED-SG1',
                'fov_modes': {
                    'StaSpot': {'swath_width': 10,  'coverage_angle': 0.93},
                    'Strip':   {'swath_width': 40,  'coverage_angle': 3.70},
                    'Wide':    {'swath_width': 100, 'coverage_angle': 9.27},
                    'Huge':    {'swath_width': 200, 'coverage_angle': 18.54},
                },
                'default_swath': 40,
                'sensors': ['X-band SAR 2nd Gen (0.35m Staring Spotlight, 1m Spotlight, 3-15m Strip)'],
                'sensor_type': 'SAR',
                'country': 'Italy/ASI',
                'altitude_km': 619,
                'launch_date': '2019-12-18',
            },
            51028: {
                'name': 'COSMO-SKYMED-SG2',
                'fov_modes': {
                    'StaSpot': {'swath_width': 10,  'coverage_angle': 0.93},
                    'Strip':   {'swath_width': 40,  'coverage_angle': 3.70},
                    'Wide':    {'swath_width': 100, 'coverage_angle': 9.27},
                    'Huge':    {'swath_width': 200, 'coverage_angle': 18.54},
                },
                'default_swath': 40,
                'sensors': ['X-band SAR 2nd Gen (0.35m Staring Spotlight, 1m Spotlight, 3-15m Strip)'],
                'sensor_type': 'SAR',
                'country': 'Italy/ASI',
                'altitude_km': 619,
                'launch_date': '2022-07-31',
            },

            # ── TerraSAR-X & TanDEM-X (DLR/Airbus X-band SAR) ───────────
            31698: {
                'name': 'TERRASAR-X',
                'fov_modes': {
                    'StaSpot': {'swath_width': 10,  'coverage_angle': 1.12},
                    'Strip':   {'swath_width': 30,  'coverage_angle': 3.36},
                    'ScanSAR': {'swath_width': 100, 'coverage_angle': 11.2},
                },
                'default_swath': 30,
                'sensors': ['X-band SAR active phased array (0.25m Staring Spotlight, 1m HS, 3m Strip, 18m ScanSAR)'],
                'sensor_type': 'SAR',
                'country': 'Germany/DLR',
                'altitude_km': 514,
                'launch_date': '2007-06-15',
            },
            36605: {
                'name': 'TANDEM-X',
                'fov_modes': {
                    'Strip':   {'swath_width': 30,  'coverage_angle': 3.36},
                    'StaSpot': {'swath_width': 10,  'coverage_angle': 1.12},
                    'ScanSAR': {'swath_width': 100, 'coverage_angle': 11.2},
                },
                'default_swath': 30,
                'sensors': ['X-band SAR InSAR formation (0.25m-18m; 350m-2km from TerraSAR-X for global DEM)'],
                'sensor_type': 'SAR',
                'country': 'Germany/DLR',
                'altitude_km': 514,
                'launch_date': '2010-06-21',
            },

            # ── PAZ (Spain X-band SAR, TSX-identical hardware) ───────────
            43215: {
                'name': 'PAZ',
                'fov_modes': {
                    'StaSpot': {'swath_width': 10,  'coverage_angle': 1.12},
                    'Strip':   {'swath_width': 30,  'coverage_angle': 3.36},
                    'ScanSAR': {'swath_width': 100, 'coverage_angle': 11.2},
                },
                'default_swath': 30,
                'sensors': ['X-band SAR (identical to TerraSAR-X: 0.25m-18m resolution)'],
                'sensor_type': 'SAR',
                'country': 'Spain/Hisdesat',
                'altitude_km': 514,
                'launch_date': '2018-02-22',
            },

            # ═══════════════ CANADA – RADARSAT ══════════════════════════

            # ── RADARSAT-2 (MDA C-band SAR, fully polarimetric) ──────────
            32382: {
                'name': 'RADARSAT-2',
                'fov_modes': {
                    'Spotlight':  {'swath_width': 8,   'coverage_angle': 0.58},
                    'Fine':       {'swath_width': 25,  'coverage_angle': 1.80},
                    'Standard':   {'swath_width': 50,  'coverage_angle': 3.60},
                    'ScanSAR_W':  {'swath_width': 500, 'coverage_angle': 36.0},
                },
                'default_swath': 50,
                'sensors': ['C-band SAR (1m Spotlight, 3m Ultra-Fine, 8m Fine, 25m Std, 100m ScanSAR; fully polarimetric)'],
                'sensor_type': 'SAR',
                'country': 'Canada/MDA',
                'altitude_km': 798,
                'launch_date': '2007-12-14',
            },

            # ── RADARSAT Constellation Mission 2 & 3 ─────────────────────
            44421: {
                'name': 'RCM-2',
                'fov_modes': {
                    'Spotlight': {'swath_width': 5,   'coverage_angle': 0.48},
                    'StripMap':  {'swath_width': 30,  'coverage_angle': 2.90},
                    'MedRes':    {'swath_width': 125, 'coverage_angle': 12.1},
                    'LowNoise':  {'swath_width': 350, 'coverage_angle': 34.0},
                },
                'default_swath': 30,
                'sensors': ['C-band SAR compact polarimetry (1-100m, 5 imaging modes)'],
                'sensor_type': 'SAR',
                'country': 'Canada/MDA/CSA',
                'altitude_km': 592,
                'launch_date': '2019-06-12',
            },
            44422: {
                'name': 'RCM-3',
                'fov_modes': {
                    'Spotlight': {'swath_width': 5,   'coverage_angle': 0.48},
                    'StripMap':  {'swath_width': 30,  'coverage_angle': 2.90},
                    'MedRes':    {'swath_width': 125, 'coverage_angle': 12.1},
                    'LowNoise':  {'swath_width': 350, 'coverage_angle': 34.0},
                },
                'default_swath': 30,
                'sensors': ['C-band SAR compact polarimetry (identical to RCM-2)'],
                'sensor_type': 'SAR',
                'country': 'Canada/MDA/CSA',
                'altitude_km': 592,
                'launch_date': '2019-06-12',
            },

            # ── NovaSAR-1 (SSTL S-band SAR + AIS) ───────────────────────
            43916: {
                'name': 'NOVASAR-1',
                'fov_modes': {
                    'StripMap':  {'swath_width': 20,  'coverage_angle': 1.98},
                    'ScanSAR6':  {'swath_width': 50,  'coverage_angle': 4.94},
                    'ScanSAR20': {'swath_width': 100, 'coverage_angle': 9.88},
                    'Maritime':  {'swath_width': 400, 'coverage_angle': 39.5},
                },
                'default_swath': 20,
                'sensors': ['S-band SAR 3.2GHz HH/HV (6m Strip, 20m ScanSAR, 30m Maritime + AIS)'],
                'sensor_type': 'SAR',
                'country': 'UK/SSTL',
                'altitude_km': 580,
                'launch_date': '2018-09-16',
            },

            # ═══════════════ COMMERCIAL SAR CONSTELLATIONS ══════════════

            # ── ICEYE X-band SAR constellation (Finland) ──────────────────
            44390: {
                'name': 'ICEYE-X2',
                'fov_modes': {
                    'Spotlight': {'swath_width': 5,   'coverage_angle': 0.50},
                    'Strip':     {'swath_width': 30,  'coverage_angle': 3.01},
                    'ScanSAR':   {'swath_width': 100, 'coverage_angle': 10.0},
                },
                'default_swath': 30,
                'sensors': ['X-band SAR (0.5m Spotlight, 3m Strip, 15m ScanSAR)'],
                'sensor_type': 'SAR',
                'country': 'Finland/ICEYE',
                'altitude_km': 570,
                'launch_date': '2019-04-03',
            },
            45429: {
                'name': 'ICEYE-X4',
                'fov_modes': {
                    'Spotlight': {'swath_width': 5,   'coverage_angle': 0.50},
                    'Strip':     {'swath_width': 30,  'coverage_angle': 3.01},
                    'ScanSAR':   {'swath_width': 100, 'coverage_angle': 10.0},
                },
                'default_swath': 30,
                'sensors': ['X-band SAR (0.5m Spotlight, 3m Strip, 15m ScanSAR)'],
                'sensor_type': 'SAR',
                'country': 'Finland/ICEYE',
                'altitude_km': 570,
                'launch_date': '2019-09-03',
            },
            46069: {
                'name': 'ICEYE-X5',
                'fov_modes': {
                    'Spotlight': {'swath_width': 5,   'coverage_angle': 0.50},
                    'Strip':     {'swath_width': 30,  'coverage_angle': 3.01},
                    'ScanSAR':   {'swath_width': 100, 'coverage_angle': 10.0},
                },
                'default_swath': 30,
                'sensors': ['X-band SAR (0.5m Spotlight, 3m Strip, 15m ScanSAR)'],
                'sensor_type': 'SAR',
                'country': 'Finland/ICEYE',
                'altitude_km': 570,
                'launch_date': '2021-01-24',
            },
            47467: {
                'name': 'ICEYE-X6',
                'fov_modes': {
                    'Spotlight': {'swath_width': 5,   'coverage_angle': 0.50},
                    'Strip':     {'swath_width': 30,  'coverage_angle': 3.01},
                    'ScanSAR':   {'swath_width': 100, 'coverage_angle': 10.0},
                },
                'default_swath': 30,
                'sensors': ['X-band SAR (0.5m Spotlight, 3m Strip, 15m ScanSAR)'],
                'sensor_type': 'SAR',
                'country': 'Finland/ICEYE',
                'altitude_km': 570,
                'launch_date': '2021-06-22',
            },
            49055: {
                'name': 'ICEYE-X7',
                'fov_modes': {
                    'Spotlight': {'swath_width': 5,   'coverage_angle': 0.50},
                    'Strip':     {'swath_width': 30,  'coverage_angle': 3.01},
                    'ScanSAR':   {'swath_width': 100, 'coverage_angle': 10.0},
                },
                'default_swath': 30,
                'sensors': ['X-band SAR (0.5m Spotlight, 3m Strip, 15m ScanSAR)'],
                'sensor_type': 'SAR',
                'country': 'Finland/ICEYE',
                'altitude_km': 570,
                'launch_date': '2022-01-13',
            },

            # ── Capella Space X-band SAR (USA) ────────────────────────────
            46502: {
                'name': 'CAPELLA-2',
                'fov_modes': {
                    'Spotlight': {'swath_width': 5,  'coverage_angle': 0.55},
                    'Strip':     {'swath_width': 25, 'coverage_angle': 2.73},
                },
                'default_swath': 25,
                'sensors': ['X-band SAR (0.35-0.5m Sliding Spotlight, 1.5m Strip)'],
                'sensor_type': 'SAR',
                'country': 'USA/Capella Space',
                'altitude_km': 525,
                'launch_date': '2020-08-17',
            },
            48913: {
                'name': 'CAPELLA-3',
                'fov_modes': {
                    'Spotlight': {'swath_width': 5,  'coverage_angle': 0.55},
                    'Strip':     {'swath_width': 25, 'coverage_angle': 2.73},
                },
                'default_swath': 25,
                'sensors': ['X-band SAR (0.35-0.5m Spotlight, 1.5m Strip)'],
                'sensor_type': 'SAR',
                'country': 'USA/Capella Space',
                'altitude_km': 525,
                'launch_date': '2022-01-13',
            },
            51053: {
                'name': 'CAPELLA-4',
                'fov_modes': {
                    'Spotlight': {'swath_width': 5,  'coverage_angle': 0.55},
                    'Strip':     {'swath_width': 25, 'coverage_angle': 2.73},
                },
                'default_swath': 25,
                'sensors': ['X-band SAR (0.35-0.5m Spotlight, 1.5m Strip)'],
                'sensor_type': 'SAR',
                'country': 'USA/Capella Space',
                'altitude_km': 525,
                'launch_date': '2022-05-25',
            },

            # ── Umbra X-band sub-meter SAR (USA) ─────────────────────────
            55268: {
                'name': 'UMBRA-04',
                'fov_modes': {
                    'Spotlight': {'swath_width': 5,  'coverage_angle': 0.55},
                    'Strip':     {'swath_width': 20, 'coverage_angle': 2.19},
                },
                'default_swath': 20,
                'sensors': ['X-band SAR (0.25m Spotlight, 1m Strip; 16cm achievable)'],
                'sensor_type': 'SAR',
                'country': 'USA/Umbra',
                'altitude_km': 520,
                'launch_date': '2023-01-15',
            },
            55847: {
                'name': 'UMBRA-05',
                'fov_modes': {
                    'Spotlight': {'swath_width': 5,  'coverage_angle': 0.55},
                    'Strip':     {'swath_width': 20, 'coverage_angle': 2.19},
                },
                'default_swath': 20,
                'sensors': ['X-band SAR (0.25m Spotlight, 1m Strip)'],
                'sensor_type': 'SAR',
                'country': 'USA/Umbra',
                'altitude_km': 520,
                'launch_date': '2023-04-12',
            },
            57320: {
                'name': 'UMBRA-06',
                'fov_modes': {
                    'Spotlight': {'swath_width': 5,  'coverage_angle': 0.55},
                    'Strip':     {'swath_width': 20, 'coverage_angle': 2.19},
                },
                'default_swath': 20,
                'sensors': ['X-band SAR (0.25m Spotlight, 1m Strip)'],
                'sensor_type': 'SAR',
                'country': 'USA/Umbra',
                'altitude_km': 520,
                'launch_date': '2023-06-12',
            },

            # ═══════════════ COMMERCIAL OPTICAL ═════════════════════════

            # ── WorldView-4 (Maxar, decommissioned 2019) ──────────────────
            41848: {
                'name': 'WORLDVIEW-4',
                'fov_modes': {
                    'Pan': {'swath_width': 13.1, 'coverage_angle': 1.22},
                },
                'default_swath': 13.1,
                'sensors': ['0.31m PAN, 1.24m MS 4-band (GeoEye-2 sensor; CMG failure Jan 2019)'],
                'sensor_type': 'optical',
                'country': 'USA/Maxar',
                'altitude_km': 617,
                'launch_date': '2016-11-11',
            },

            # ── SkySat constellation Gen-1 & Gen-2 (Planet Labs) ─────────
            40896: {
                'name': 'SKYSAT-4',
                'fov_modes': {
                    'Strip': {'swath_width': 2, 'coverage_angle': 0.23},
                },
                'default_swath': 2,
                'sensors': ['0.72m Pan, 1.0m MS 4-band + Video (Gen-1)'],
                'sensor_type': 'optical',
                'country': 'USA/Planet Labs',
                'altitude_km': 500,
                'launch_date': '2016-07-08',
            },
            40898: {
                'name': 'SKYSAT-5',
                'fov_modes': {
                    'Strip': {'swath_width': 2, 'coverage_angle': 0.23},
                },
                'default_swath': 2,
                'sensors': ['0.72m Pan, 1.0m MS 4-band + Video (Gen-1)'],
                'sensor_type': 'optical',
                'country': 'USA/Planet Labs',
                'altitude_km': 500,
                'launch_date': '2016-07-08',
            },
            45261: {
                'name': 'SKYSAT-13',
                'fov_modes': {
                    'Strip': {'swath_width': 2, 'coverage_angle': 0.25},
                },
                'default_swath': 2,
                'sensors': ['0.5m Pan, MS 4-band + Video (Gen-2 50cm)'],
                'sensor_type': 'optical',
                'country': 'USA/Planet Labs',
                'altitude_km': 450,
                'launch_date': '2020-09-03',
            },
            45262: {
                'name': 'SKYSAT-14',
                'fov_modes': {
                    'Strip': {'swath_width': 2, 'coverage_angle': 0.25},
                },
                'default_swath': 2,
                'sensors': ['0.5m Pan, MS 4-band + Video (Gen-2 50cm)'],
                'sensor_type': 'optical',
                'country': 'USA/Planet Labs',
                'altitude_km': 450,
                'launch_date': '2020-09-03',
            },
            47948: {
                'name': 'SKYSAT-21',
                'fov_modes': {
                    'Strip': {'swath_width': 2, 'coverage_angle': 0.25},
                },
                'default_swath': 2,
                'sensors': ['0.5m Pan, MS 4-band + Video (Gen-2 50cm)'],
                'sensor_type': 'optical',
                'country': 'USA/Planet Labs',
                'altitude_km': 450,
                'launch_date': '2021-06-28',
            },

            # ── SuperView-1 01-04 (SpaceTy/SIWEI, China) ─────────────────
            41725: {'name': 'SUPERVIEW-1-01', 'fov_modes': {'Pan': {'swath_width': 12, 'coverage_angle': 1.30}}, 'default_swath': 12, 'sensors': ['0.5m PAN, 2m MS 4-band'], 'sensor_type': 'optical', 'country': 'China/SpaceTy', 'altitude_km': 530, 'launch_date': '2016-12-28'},
            41726: {'name': 'SUPERVIEW-1-02', 'fov_modes': {'Pan': {'swath_width': 12, 'coverage_angle': 1.30}}, 'default_swath': 12, 'sensors': ['0.5m PAN, 2m MS 4-band'], 'sensor_type': 'optical', 'country': 'China/SpaceTy', 'altitude_km': 530, 'launch_date': '2016-12-28'},
            43041: {'name': 'SUPERVIEW-1-03', 'fov_modes': {'Pan': {'swath_width': 12, 'coverage_angle': 1.30}}, 'default_swath': 12, 'sensors': ['0.5m PAN, 2m MS 4-band'], 'sensor_type': 'optical', 'country': 'China/SpaceTy', 'altitude_km': 530, 'launch_date': '2018-01-09'},
            43042: {'name': 'SUPERVIEW-1-04', 'fov_modes': {'Pan': {'swath_width': 12, 'coverage_angle': 1.30}}, 'default_swath': 12, 'sensors': ['0.5m PAN, 2m MS 4-band'], 'sensor_type': 'optical', 'country': 'China/SpaceTy', 'altitude_km': 530, 'launch_date': '2018-01-09'},

            # ── Jilin-1 03 & 04 (Chang Guang Satellite Tech, China) ───────
            41842: {
                'name': 'JILIN-1-03',
                'fov_modes': {
                    'Pan': {'swath_width': 11.6, 'coverage_angle': 1.24},
                },
                'default_swath': 11.6,
                'sensors': ['0.72m Pan, 2.9m MS 4-band + Video 30fps'],
                'sensor_type': 'optical',
                'country': 'China/CGST',
                'altitude_km': 535,
                'launch_date': '2016-11-10',
            },
            41843: {
                'name': 'JILIN-1-04',
                'fov_modes': {
                    'Pan': {'swath_width': 11.6, 'coverage_angle': 1.24},
                },
                'default_swath': 11.6,
                'sensors': ['0.72m Pan, 2.9m MS 4-band + Video 30fps'],
                'sensor_type': 'optical',
                'country': 'China/CGST',
                'altitude_km': 535,
                'launch_date': '2016-11-10',
            },

            # ── BlackSky Global constellation (USA) ───────────────────────
            44499: {
                'name': 'BLACKSKY-GLOBAL-1',
                'fov_modes': {
                    'Pan': {'swath_width': 2, 'coverage_angle': 0.25},
                },
                'default_swath': 2,
                'sensors': ['1.0m Pan, 4m MS 4-band (B G R NIR)'],
                'sensor_type': 'optical',
                'country': 'USA/BlackSky',
                'altitude_km': 450,
                'launch_date': '2019-06-05',
            },
            47699: {
                'name': 'BLACKSKY-GLOBAL-5',
                'fov_modes': {
                    'Pan': {'swath_width': 2, 'coverage_angle': 0.25},
                },
                'default_swath': 2,
                'sensors': ['1.0m Pan, 4m MS 4-band (Gen-2)'],
                'sensor_type': 'optical',
                'country': 'USA/BlackSky',
                'altitude_km': 450,
                'launch_date': '2021-06-13',
            },

            # ── DMC3 / TripleSat 2 & 3 (21AT/SSTL) ──────────────────────
            # Note: DMC3-1 NORAD 40892 conflicts with existing SKYSAT-C1
            40893: {
                'name': 'DMC3-2 (TRIPLESAT-2)',
                'fov_modes': {
                    'Pan': {'swath_width': 23, 'coverage_angle': 2.02},
                },
                'default_swath': 23,
                'sensors': ['1.0m PAN, 4m MS 4-band (PSLV-C28, Jul 2015)'],
                'sensor_type': 'optical',
                'country': 'UK/China (21AT/SSTL)',
                'altitude_km': 651,
                'launch_date': '2015-07-10',
            },
            40894: {
                'name': 'DMC3-3 (TRIPLESAT-3)',
                'fov_modes': {
                    'Pan': {'swath_width': 23, 'coverage_angle': 2.02},
                },
                'default_swath': 23,
                'sensors': ['1.0m PAN, 4m MS 4-band'],
                'sensor_type': 'optical',
                'country': 'UK/China (21AT/SSTL)',
                'altitude_km': 651,
                'launch_date': '2015-07-10',
            },

            # ── NigeriaSat-2 (Nigeria/SSTL DMC) ──────────────────────────
            37791: {
                'name': 'NIGERIASAT-2',
                'fov_modes': {
                    'HR':   {'swath_width': 20,  'coverage_angle': 1.63},
                    'Wide': {'swath_width': 300, 'coverage_angle': 24.5},
                },
                'default_swath': 20,
                'sensors': ['2.5m PAN, 5m MS 4-band, 32m MS 22-band wide-field'],
                'sensor_type': 'optical',
                'country': 'Nigeria/SSTL',
                'altitude_km': 703,
                'launch_date': '2011-08-17',
            },

            # ── RapidEye-3/4/5 (Planet Labs/Germany, decommissioned 2020) ─
            33516: {'name': 'RAPIDEYE-3', 'fov_modes': {'REIS': {'swath_width': 77, 'coverage_angle': 6.4}}, 'default_swath': 77, 'sensors': ['5m MS 5-band Red Edge (decommissioned 2020)'], 'sensor_type': 'multispectral', 'country': 'Germany/Canada', 'altitude_km': 630, 'launch_date': '2008-08-29'},
            33517: {'name': 'RAPIDEYE-4', 'fov_modes': {'REIS': {'swath_width': 77, 'coverage_angle': 6.4}}, 'default_swath': 77, 'sensors': ['5m MS 5-band Red Edge (decommissioned 2020)'], 'sensor_type': 'multispectral', 'country': 'Germany/Canada', 'altitude_km': 630, 'launch_date': '2008-08-29'},
            33518: {'name': 'RAPIDEYE-5', 'fov_modes': {'REIS': {'swath_width': 77, 'coverage_angle': 6.4}}, 'default_swath': 77, 'sensors': ['5m MS 5-band Red Edge (decommissioned 2020)'], 'sensor_type': 'multispectral', 'country': 'Germany/Canada', 'altitude_km': 630, 'launch_date': '2008-08-29'},

            # ── Pleiades NEO-5 & 6 (Airbus, 0.3m, launched 2023-11-02) ───
            54032: {  # NORAD approx; verify on space-track.org
                'name': 'PLEIADES-NEO-5',
                'fov_modes': {
                    'Pan': {'swath_width': 14, 'coverage_angle': 1.30},
                },
                'default_swath': 14,
                'sensors': ['0.3m Pan, 1.2m MS 5-band (B G R Red-Edge NIR)'],
                'sensor_type': 'optical',
                'country': 'France/Airbus',
                'altitude_km': 620,
                'launch_date': '2023-11-02',
            },
            54033: {  # NORAD approx; verify on space-track.org
                'name': 'PLEIADES-NEO-6',
                'fov_modes': {
                    'Pan': {'swath_width': 14, 'coverage_angle': 1.30},
                },
                'default_swath': 14,
                'sensors': ['0.3m Pan, 1.2m MS 5-band (B G R Red-Edge NIR)'],
                'sensor_type': 'optical',
                'country': 'France/Airbus',
                'altitude_km': 620,
                'launch_date': '2023-11-02',
            },

            # ── GOKTURK-1 (Turkey, 0.5m optical) ─────────────────────────
            41788: {
                'name': 'GOKTURK-1',
                'fov_modes': {
                    'Pan': {'swath_width': 20, 'coverage_angle': 1.66},
                },
                'default_swath': 20,
                'sensors': ['0.5m PAN, 2m MS 4-band (Thales Alenia built)'],
                'sensor_type': 'optical',
                'country': 'Turkey',
                'altitude_km': 689,
                'launch_date': '2016-12-05',
            },

            # ── IKONOS (DigitalGlobe/Maxar, first sub-1m commercial, decom. 2015) ─
            25919: {
                'name': 'IKONOS',
                'fov_modes': {
                    'Pan': {'swath_width': 11.3, 'coverage_angle': 0.95},
                },
                'default_swath': 11.3,
                'sensors': ['0.82m PAN, 3.2m MS 4-band (decommissioned 2015; historic first)'],
                'sensor_type': 'optical',
                'country': 'USA/Maxar',
                'altitude_km': 681,
                'launch_date': '1999-09-24',
            },

            # ── NOAA-20 (JPSS-1) – kept for reference ─────────────────────
            # 43013 is correct NORAD for NOAA-20 (JPSS-1), launched 2017-11-18
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
