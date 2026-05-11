
async function fetchWithRetry(url, options = {}, maxRetries = 3) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            const response = await fetch(url, options);
            if (response.status === 503 && attempt < maxRetries) {
                const delay = Math.pow(2, attempt) * 500;
                console.warn(`503 on ${url}, retry ${attempt}/${maxRetries} in ${delay}ms`);
                await new Promise(r => setTimeout(r, delay));
                continue;
            }
            return response;
        } catch (error) {
            if (attempt < maxRetries) {
                const delay = Math.pow(2, attempt) * 500;
                console.warn(`Fetch error on ${url}, retry ${attempt}/${maxRetries} in ${delay}ms`);
                await new Promise(r => setTimeout(r, delay));
                continue;
            }
            throw error;
        }
    }
}

// Global function for closing details panel (for compatibility with inline onclick handlers)
function closeDetailsPanel() {
    if (window.satelliteViewer && window.satelliteViewer.closeDetailsPanel) {
        window.satelliteViewer.closeDetailsPanel();
    } else {
        // Fallback if satelliteViewer not available
        const panel = document.getElementById('satelliteDetailsPanel');
        if (panel) {
            panel.classList.add('fade-out');
            panel.classList.remove('show');

            // Hide panel after animation completes
            setTimeout(() => {
                if (panel.classList.contains('fade-out')) {
                    panel.style.display = 'none';
                    panel.classList.remove('fade-out');
                }
            }, 300);
        }
    }
}

// Global function for showing details panel (for compatibility)
function showDetailsPanel() {
    const panel = document.getElementById('satelliteDetailsPanel');
    if (panel) {
        panel.style.display = 'block';
        panel.classList.remove('fade-out');
        // Force reflow to ensure display change takes effect
        panel.offsetHeight;
        panel.classList.add('show');
    }
}


class SatelliteViewer {
    constructor() {
        this.viewer = null;
        this.satellites = new Map();
        this.airplanes = new Map();
        this.satelliteEntities = new Map();
        this.airplaneEntities = new Map();
        this.orbitEntities = new Map();
        this.coverageSwathEntities = new Map();
        this.groundSwathEntity = null;
        this.groundSwathUpdateInterval = null;
        this.selectedSatellite = null;
        this.selectedAirplane = null;
        this.userLocation = { lat: 0, lon: 0, alt: 0 };
        this.categories = {};
        this.showOrbits = false;
        this.showCoverageSwath = false;
        this.showGroundSwath = false;
        this.showGroundTracks = false;
        this.starlinkVisible = false; // hidden by default to reduce rendering load
        this.trackingMode = true;
        this.currentMode = 'satellites'; // 'satellites' or 'airplanes'
        this.updateInterval = null;
        this.groundTrackEntities = new Map();
        this.nadirEntities = new Map();
        this.groundCircleEntities = new Map();
        this.realTimeUpdateInterval = null;
        this.satelliteTrackingInterval = null;
        this.preferences = {};
        this.clickTimeout = null;
        this.userLocationMarker = null;
        // Initialize satellite filter module
        this.satelliteFilter = null; // Will be initialized after construction

        // Performance optimizations for smooth movement
        // IMPORTANT: This MUST match the backend cache interval (10s) to avoid interpolation jumps
        this.updateRate = 1000; // 1 second for real-time smoothness
        this.maxVisibleSatellites = 2500; // Reduced for faster initial load
        this.lodDistance = 10000000; // Level of detail distance
        this.initialLoadBatchSize = 50; // Load satellites in batches initially

        // Initialize modules after construction
        this.passFilter = new PassFilter(this);
        this.satelliteFilter = new SatelliteFilter(this);
        this.motionControl = new MotionControl(this);
        this.satelliteSearch = new SatelliteSearch(this);
        this.satelliteWorkflow = new SatelliteWorkflow(this); // New workflow manager
        this.weatherModule = null; // Will be initialized after Cesium viewer is ready

        // Multi-processing and web worker support
        this.processingWorkers = [];
        this.maxWorkers = Math.min(navigator.hardwareConcurrency || 4, 8);
        this.workerPool = [];
        this.isMultiProcessingEnabled = true;

        console.log(`🔧 Multi-processing enabled with ${this.maxWorkers} workers`)

        this.init();
    }

    async init() {
        try {
            console.log('Initializing SatelliteViewer...');
            this.showLoadingIndicator('Initializing 3D viewer...');

            await this.initializeCesium();
            this.showLoadingIndicator('Setting up controls...');

            this.setupEventListeners();
            this.showLoadingIndicator('Loading preferences...');

            await this.loadUserPreferences();
            this.showLoadingIndicator('Loading categories...');

            await this.loadSatellites();
            this.showLoadingIndicator('Starting updates...');

            this.startAutoUpdate();
            this.setupGeolocation();

            // Ensure initial status is displayed correctly
            this.updateStatus(this.satellites.size, new Date().toISOString());
            this.updateConnectionStatus('Connected', 'success');

            this.hideLoadingIndicator();
            console.log('SatelliteViewer initialization complete');
        } catch (error) {
            console.error('Error initializing SatelliteViewer:', error);
            this.hideLoadingIndicator();
            this.showError('Failed to initialize satellite viewer: ' + error.message);
            this.updateConnectionStatus('Disconnected', 'danger');
        }
    }

    async initializeCesium() {
        // Add missing CSS styles for cloud legend
        this.addRequiredCSS();

        // Wait for Cesium to be fully loaded
        await this.waitForCesium();

        console.log('Initializing Cesium...');

        // No Cesium Ion token needed — we use our own cached tile proxy
        // (old Ion token was blocked with 403; Ion is not required for our tile sources)
        Cesium.Ion.defaultAccessToken = '';

        try {
            // Build layer picker using our local caching proxy only.
            // Ion's default list is bypassed entirely to avoid 403 errors.
            const _tileProvider = (providerKey, credit, maxLevel = 19) =>
                new Cesium.UrlTemplateImageryProvider({
                    url: `/tiles/${providerKey}/{z}/{x}/{y}/`,
                    credit,
                    maximumLevel: maxLevel,
                    minimumLevel: 0,
                });

            const imageryViewModels = [
                // ── Street / road maps ───────────────────────────────────
                new Cesium.ProviderViewModel({
                    name: 'Street Map',
                    tooltip: 'ESRI World Street Map — roads, cities, labels',
                    iconUrl: Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/openStreetMap.png'),
                    creationFunction: () => _tileProvider('esri-street', 'Tiles © ESRI'),
                }),
                new Cesium.ProviderViewModel({
                    name: 'OpenStreetMap',
                    tooltip: 'OpenStreetMap — community-maintained world map (direct tiles)',
                    iconUrl: Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/openStreetMap.png'),
                    creationFunction: () => new Cesium.OpenStreetMapImageryProvider({
                        url: 'https://tile.openstreetmap.org/',
                        fileExtension: 'png',
                        maximumLevel: 19,
                        credit: new Cesium.Credit('© <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors', true),
                    }),
                }),
                new Cesium.ProviderViewModel({
                    name: 'Topo Map',
                    tooltip: 'ESRI World Topographic Map — elevation contours and terrain',
                    iconUrl: Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/openStreetMap.png'),
                    creationFunction: () => _tileProvider('esri-topo', 'Tiles © ESRI'),
                }),
                new Cesium.ProviderViewModel({
                    name: 'OpenTopoMap',
                    tooltip: 'OpenTopoMap — detailed hiking and relief map',
                    iconUrl: Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/openStreetMap.png'),
                    creationFunction: () => _tileProvider('opentopomap', '© OpenTopoMap contributors', 17),
                }),
                // ── Satellite / imagery ──────────────────────────────────
                new Cesium.ProviderViewModel({
                    name: 'Satellite Imagery',
                    tooltip: 'ESRI World Imagery — high-resolution aerial photography',
                    iconUrl: Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/bingAerial.png'),
                    creationFunction: () => _tileProvider('esri-imagery', 'Tiles © ESRI'),
                }),
                new Cesium.ProviderViewModel({
                    name: 'Earth from Space',
                    tooltip: 'NASA MODIS Terra — true-colour daytime Earth composite from satellite',
                    iconUrl: Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/bingAerial.png'),
                    creationFunction: () => _tileProvider('nasa-day', 'NASA GIBS / MODIS Terra', 9),
                }),
                new Cesium.ProviderViewModel({
                    name: 'Ocean',
                    tooltip: 'ESRI Ocean Base — ocean floor bathymetry depth shading',
                    iconUrl: Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/bingAerial.png'),
                    creationFunction: () => _tileProvider('esri-ocean', 'Tiles © ESRI'),
                }),
                new Cesium.ProviderViewModel({
                    name: 'Physical Map',
                    tooltip: 'ESRI World Physical — natural terrain colours, no borders or labels',
                    iconUrl: Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/bingAerial.png'),
                    creationFunction: () => _tileProvider('esri-physical', 'Tiles © ESRI'),
                }),
                // ── Dark / minimal ───────────────────────────────────────
                new Cesium.ProviderViewModel({
                    name: 'Voyager',
                    tooltip: 'CartoDB Voyager — polished mid-tone design, roads without the noise',
                    iconUrl: Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/openStreetMap.png'),
                    creationFunction: () => _tileProvider('carto-voyager', 'Tiles © CartoDB'),
                }),
                new Cesium.ProviderViewModel({
                    name: 'OSM Humanitarian',
                    tooltip: 'OpenStreetMap Humanitarian — warm palette used in disaster and aid mapping',
                    iconUrl: Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/openStreetMap.png'),
                    creationFunction: () => _tileProvider('osm-hot', '© OpenStreetMap / HOT'),
                }),
                new Cesium.ProviderViewModel({
                    name: 'Shaded Relief',
                    tooltip: 'ESRI World Shaded Relief — pure terrain shading, no labels',
                    iconUrl: Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/bingAerial.png'),
                    creationFunction: () => _tileProvider('esri-relief', 'Tiles © ESRI'),
                }),
                new Cesium.ProviderViewModel({
                    name: 'National Geographic',
                    tooltip: 'ESRI NatGeo World Map — cartographic style as seen in National Geographic',
                    iconUrl: Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/openStreetMap.png'),
                    creationFunction: () => _tileProvider('esri-natgeo', 'Tiles © ESRI / National Geographic'),
                }),
                // ── Dark / minimal ───────────────────────────────────────
                new Cesium.ProviderViewModel({
                    name: 'Dark Matter',
                    tooltip: 'CartoDB Dark Matter — high-contrast dark theme',
                    iconUrl: Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/openStreetMap.png'),
                    creationFunction: () => _tileProvider('carto-dark', 'Tiles © CartoDB'),
                }),
                new Cesium.ProviderViewModel({
                    name: 'Dark Gray Canvas',
                    tooltip: 'ESRI Dark Gray Canvas — minimal dark basemap for data overlays',
                    iconUrl: Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/openStreetMap.png'),
                    creationFunction: () => _tileProvider('esri-dark', 'Tiles © ESRI'),
                }),
                new Cesium.ProviderViewModel({
                    name: 'Light (CartoDB)',
                    tooltip: 'CartoDB Positron — clean minimal light theme',
                    iconUrl: Cesium.buildModuleUrl('Widgets/Images/ImageryProviders/openStreetMap.png'),
                    creationFunction: () => _tileProvider('carto-light', 'Tiles © CartoDB'),
                }),
            ];

            this.viewer = new Cesium.Viewer('cesiumContainer', {
                // Performance optimizations
                terrainProvider: new Cesium.EllipsoidTerrainProvider(),
                imageryProvider: false,          // let the picker control the base layer
                imageryProviderViewModels: imageryViewModels,
                selectedImageryProviderViewModel: imageryViewModels[1],  // OSM as default
                baseLayerPicker: true,
                geocoder: false,
                homeButton: true,
                sceneModePicker: false,
                navigationHelpButton: false,
                animation: false,
                timeline: false,
                fullscreenButton: true,
                vrButton: false,
                creditContainer: document.createElement('div'),
                // Enhanced performance settings
                requestRenderMode: false, // Continuous rendering for smooth animation
                maximumRenderTimeChange: 1000 / 10, // Target 10fps for smooth movement
            });

            console.log('Cesium viewer created successfully');

            // Set near/far parameters for better satellite rendering
            this.viewer.scene.camera.frustum.near = 0.1;
            this.viewer.scene.camera.frustum.far = 50000000000.0;

            // Performance optimizations
            this.viewer.scene.globe.enableLighting = true;
            this.viewer.scene.globe.maximumScreenSpaceError = 2;
            this.viewer.scene.globe.tileCacheSize = 100;

            // Enhanced atmosphere and lighting
            this.viewer.scene.skyAtmosphere.show = true;
            this.viewer.scene.sun.show = true;
            this.viewer.scene.moon.show = true;
            this.viewer.scene.skyBox.show = true;

            // Add cloud cover and enhanced atmosphere
            await this.setupCloudCover();

            // Manual cloud testing - don't auto-enable
            console.log('Cloud system ready. Click the cloud button to test.');

            // Set initial camera position for better Earth view
            this.viewer.camera.setView({
                destination: Cesium.Cartesian3.fromDegrees(0, 0, 150000000),
                orientation: {
                    heading: 0.0,
                    pitch: -Cesium.Math.PI_OVER_TWO,
                    roll: 0.0
                }
            });

            // Enable real-time clock with controlled speed
            this.viewer.clock.shouldAnimate = true;
            this.viewer.clock.multiplier = 1;

            // Set up optimized click handler
            this.viewer.cesiumWidget.screenSpaceEventHandler.setInputAction(
                this.onEntityClick.bind(this),
                Cesium.ScreenSpaceEventType.LEFT_CLICK
            );

            // Remove loading overlay if it exists
            const loadingOverlay = document.querySelector('.loading-overlay');
            if (loadingOverlay) {
                loadingOverlay.style.display = 'none';
            }

            // Initialize weather module after Cesium viewer is ready
            this.weatherModule = new WeatherModule(this.viewer);

            console.log('Cesium initialization complete');

        } catch (error) {
            console.error('Error creating Cesium viewer:', error);
            throw new Error('Failed to initialize Cesium viewer: ' + error.message);
        }
    }

    async waitForCesium() {
        // Wait for Cesium to be fully loaded with timeout
        return new Promise((resolve, reject) => {
            let attempts = 0;
            const maxAttempts = 50; // 5 seconds max wait time

            const checkCesium = () => {
                attempts++;

                if (typeof Cesium !== 'undefined' && Cesium.Viewer) {
                    console.log('✅ Cesium loaded successfully');
                    resolve();
                } else if (attempts >= maxAttempts) {
                    reject(new Error('Cesium library failed to load after 5 seconds. Please check your internet connection or refresh the page.'));
                } else {
                    console.log(`⏳ Waiting for Cesium... (${attempts}/${maxAttempts})`);
                    setTimeout(checkCesium, 100);
                }
            };

            checkCesium();
        });
    }

    addRequiredCSS() {
        // Add missing CSS styles for cloud legend and other components
        if (!document.getElementById('satelliteViewerCSS')) {
            const style = document.createElement('style');
            style.id = 'satelliteViewerCSS';
            style.textContent = `
                .cloud-legend {
                    position: fixed;
                    top: 80px;
                    left: 20px;
                    background: linear-gradient(135deg, rgba(26, 26, 46, 0.95) 0%, rgba(12, 12, 12, 0.95) 100%);
                    border: 1px solid rgba(100, 181, 246, 0.3);
                    border-radius: 10px;
                    padding: 15px;
                    max-width: 300px;
                    color: white;
                    font-size: 12px;
                    backdrop-filter: blur(10px);
                    z-index: 1000;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                }

                .legend-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 10px;
                    padding-bottom: 8px;
                    border-bottom: 1px solid rgba(100, 181, 246, 0.2);
                }

                .legend-header h6 {
                    margin: 0;
                    color: #64b5f6;
                    font-weight: 600;
                }

                .legend-content {
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                }

                .legend-item {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }

                .legend-color {
                    width: 16px;
                    height: 16px;
                    border-radius: 3px;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }

                .legend-footer {
                    margin-top: 10px;
                    padding-top: 8px;
                    border-top: 1px solid rgba(100, 181, 246, 0.2);
                    display: flex;
                    flex-direction: column;
                    gap: 4px;
                }

                .legend-footer small {
                    color: #94a3b8;
                    font-size: 10px;
                }

                @media (max-width: 768px) {
                    .cloud-legend {
                        top: calc(var(--navbar-height, 60px) + 10px);
                        left: 10px;
                        max-width: calc(100vw - 70px);
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }

    async setupCloudCover() {
        try {
            console.log('Setting up enhanced atmosphere...');

            // Enhanced atmosphere settings only - no geometric clouds
            const scene = this.viewer.scene;
            const skyAtmosphere = scene.skyAtmosphere;

            // Configure atmospheric scattering for better visual effect
            skyAtmosphere.hueShift = 0.1;
            skyAtmosphere.saturationShift = 0.2;
            skyAtmosphere.brightnessShift = 0.1;

            // Enhanced lighting for better atmosphere visibility
            scene.globe.enableLighting = true;
            scene.globe.dynamicAtmosphereLighting = true;
            scene.globe.dynamicAtmosphereLightingFromSun = true;

            // Better fog and atmospheric effects
            scene.fog.enabled = true;
            scene.fog.density = 0.00015;
            scene.fog.screenSpaceErrorFactor = 2.0;

            console.log('Atmosphere setup complete - no geometric clouds');
        } catch (error) {
            console.error('Error setting up atmosphere:', error);
        }
    }



    async loadUserPreferences() {
        try {
            const response = await fetchWithRetry('/api/user/preferences');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success && data.preferences) {
                this.preferences = data.preferences;
                this.userLocation = this.preferences.location || { lat: 0, lon: 0, alt: 0 };
                this.updateRate = (this.preferences.update_interval || 1000) * 10;

                // Update UI safely
                const latElement = document.getElementById('latitude');
                const lonElement = document.getElementById('longitude');
                const altElement = document.getElementById('altitude');

                if (latElement) latElement.value = this.userLocation.lat;
                if (lonElement) lonElement.value = this.userLocation.lon;
                if (altElement) altElement.value = this.userLocation.alt;
            } else {
                // Set defaults
                this.userLocation = { lat: 0, lon: 0, alt: 0 };
                this.updateRate = 30000; // 30 seconds default
            }
        } catch (error) {
            console.warn('Could not load user preferences, using defaults:', error);
            this.userLocation = { lat: 0, lon: 0, alt: 0 };
            this.updateRate = 30000; // 30 seconds default
        }
    }

    async saveUserPreferences() {
        try {
            await fetchWithRetry('/api/user/preferences', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(this.preferences)
            });
        } catch (error) {
            console.warn('Could not save user preferences:', error);
        }
    }

    setupEventListeners() {
        // Helper to safely add event listeners with null checks
        const safeAddEvent = (id, event, handler) => {
            const el = document.getElementById(id);
            if (el) {
                el.addEventListener(event, handler);
            } else {
                console.warn(`⚠️ Element #${id} not found in DOM`);
            }
        };

        // Enhanced event listeners with performance considerations
        safeAddEvent('refreshBtn', 'click', () => this.refreshData());

        // Set up close panel button handler
        safeAddEvent('closePanelBtn', 'click', () => this.closeDetailsPanel());

        // Location dropdown options
        safeAddEvent('inputCoordinatesBtn', 'click', () => {
            const modal = new bootstrap.Modal(document.getElementById('coordinatesModal'));
            modal.show();
        });

        safeAddEvent('searchByNameBtn', 'click', () => {
            const modal = new bootstrap.Modal(document.getElementById('searchLocationModal'));
            modal.show();
        });

        safeAddEvent('selectOnGlobeBtn', 'click', () => this.enableGlobeSelection());
        safeAddEvent('getCurrentLocationBtn', 'click', () => this.getCurrentLocation());

        // Mode switching buttons
        safeAddEvent('satelliteModeBtn', 'click', () => this.switchToSatelliteMode());
        safeAddEvent('airplaneModeBtn', 'click', () => this.switchToAirplaneMode());

        safeAddEvent('homeBtn', 'click', () => this.resetView());
        safeAddEvent('trackingBtn', 'click', () => this.toggleTracking());
        safeAddEvent('orbitsBtn', 'click', () => this.toggleOrbits());
        safeAddEvent('groundTracksBtn', 'click', () => this.toggleGroundTracks());
        safeAddEvent('coverageSwathBtn', 'click', () => this.toggleCoverageSwath());
        safeAddEvent('groundSwathBtn', 'click', () => this.toggleGroundSwath());
        safeAddEvent('motionControlBtn', 'click', () => this.motionControl.toggleMotionControl());

        // Speed control slider
        safeAddEvent('speedControlSlider', 'input', (e) => {
            this.motionControl.setMotionSpeed(parseInt(e.target.value));
        });

        // Speed control buttons
        safeAddEvent('decreaseSpeedBtn', 'click', () => this.motionControl.adjustSpeed(-1));
        safeAddEvent('increaseSpeedBtn', 'click', () => this.motionControl.adjustSpeed(1));

        // Weather toggle button
        safeAddEvent('weatherToggleBtn', 'click', () => {
            if (this.weatherModule) {
                this.weatherModule.toggle();
            }
        });

        safeAddEvent('saveCoordinatesBtn', 'click', () => this.saveCoordinates());

        // Add cleanup event listeners for coordinates modal
        const coordinatesModal = document.getElementById('coordinatesModal');
        if (coordinatesModal) {
            coordinatesModal.addEventListener('hidden.bs.modal', () => {
                this.cleanupCoordinatesModal();
            });
        }

        safeAddEvent('searchLocationBtn', 'click', () => this.searchLocationByName());

        // Add cleanup event listeners for search location modal
        const searchLocationModal = document.getElementById('searchLocationModal');
        if (searchLocationModal) {
            searchLocationModal.addEventListener('hidden.bs.modal', () => {
                this.cleanupSearchLocationModal();
            });
        }

        // Time-based pass filter functionality
        safeAddEvent('applyPassFilterBtn', 'click', async () => {
            await this.passFilter.applyTimeBasedPassFilter();
        });

        safeAddEvent('clearPassFilterBtn', 'click', () => {
            this.passFilter.clearPassFilter();
        });

    }

    setupGeolocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    this.userLocation = {
                        lat: position.coords.latitude,
                        lon: position.coords.longitude,
                        alt: position.coords.altitude || 0
                    };

                    // Add user location marker on globe
                    this.addUserLocationMarker();

                    // Update preferences
                    this.preferences.location = this.userLocation;
                    this.saveUserPreferences();

                    // Update form fields if they exist
                    const latField = document.getElementById('latitude');
                    const lonField = document.getElementById('longitude');
                    const altField = document.getElementById('altitude');

                    if (latField) latField.value = this.userLocation.lat;
                    if (lonField) lonField.value = this.userLocation.lon;
                    if (altField) altField.value = this.userLocation.alt;

                    console.log('User location set:', this.userLocation);
                },
                (error) => {
                    console.warn('Geolocation failed:', error);
                    // Set default location to prevent errors
                    this.userLocation = { lat: 0, lon: 0, alt: 0 };
                },
                {
                    enableHighAccuracy: false,
                    timeout: 10000,
                    maximumAge: 600000 // 10 minutes
                }
            );
        } else {
            console.warn('Geolocation not supported');
            this.userLocation = { lat: 0, lon: 0, alt: 0 };
        }
    }







    async loadSatellites() {
        try {
            console.log('🛰️ Fetching satellite data from API...');
            const response = await fetchWithRetry('/api/satellites');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('📡 API Response:', {
                success: data.success,
                satelliteCount: data.satellites?.length || 0,
                hasData: !!data.satellites
            });

            if (data.success && data.satellites && data.satellites.length > 0) {
                // Efficient satellite data update with position interpolation
                const isFirstLoad = this.satellites.size === 0;

                // Store current search state before updating - be more thorough
                const currentSearchQuery = this.satelliteSearch ? this.satelliteSearch.currentQuery : '';
                const hasActiveSearch = currentSearchQuery && currentSearchQuery.length > 0;
                const isSelectingFromSearch = this.satelliteSearch && this.satelliteSearch.isSelectingFromSearch;

                console.log(`🔍 Auto-update - Search active: ${hasActiveSearch}, Query: "${currentSearchQuery}", Selecting: ${isSelectingFromSearch}`);

                // Use backend timestamp for accurate position extrapolation
                const backendTimestamp = data.timestamp ? new Date(data.timestamp).getTime() : Date.now();

                // Store the backend timestamp ISO string for orbit calculations
                this.backendTimestampISO = data.timestamp;

                // Update satellite data with smooth transitions
                const newSatellites = new Map();
                data.satellites.forEach(sat => {
                    // Validate satellite data
                    if (!sat.norad_id || typeof sat.latitude !== 'number' || typeof sat.longitude !== 'number') {
                        console.warn('Invalid satellite data:', sat);
                        return;
                    }

                    // Use velocity from backend if available
                    if (sat.velocity) {
                        sat.velocity = {
                            latitude: sat.velocity.latitude,
                            longitude: sat.velocity.longitude,
                            altitude: sat.velocity.altitude
                        };
                    } else {
                        sat.velocity = { latitude: 0, longitude: 0, altitude: 0 };
                    }

                    // Use backend timestamp as the base for extrapolation
                    // This ensures accurate position calculation from the moment data was computed
                    sat.lastUpdateTime = backendTimestamp;

                    newSatellites.set(sat.norad_id, sat);
                });

                this.satellites = newSatellites;
                console.log(`✅ Loaded ${newSatellites.size} valid satellites`);

                if (this.currentMode === 'satellites') {
                    // Always update positions for smooth motion
                    this.updateSatellitePositions();

                    // On first load, immediately fetch again to establish velocity
                    if (isFirstLoad) {
                        console.log('📍 Fetching immediate follow-up for velocity...');
                        setTimeout(() => {
                            this.loadSatellites();
                        }, 100); // Immediate follow-up (100ms) for velocity
                    }

                    console.log(`🎯 Rendering satellites, first load: ${isFirstLoad}`);
                    this.renderSatellites();

                    // Restore search filter if it was active and not in the middle of selection
                    if (hasActiveSearch && this.satelliteSearch && !isSelectingFromSearch) {
                        console.log(`🔍 Restoring search filter: "${currentSearchQuery}"`);
                        this.satelliteSearch.applySearchFilter(currentSearchQuery);
                    } else if (isSelectingFromSearch) {
                        console.log(`🔍 Skipping search filter restoration - selection in progress`);
                    }

                    // Update all status elements
                    this.updateStatus(newSatellites.size, data.timestamp);
                    this.updateConnectionStatus('Connected', 'success');

                    // Note: Orbit paths are NOT refreshed here to avoid recreating them every 10-15 seconds
                    // Orbits are only created when: 1) orbit toggle is turned ON, or 2) a new satellite is selected

                    console.log(`📊 Updated UI status: ${newSatellites.size} satellites visible`);
                }
            } else {
                console.error('❌ Failed to load satellites:', data);
                this.showError(data.error || 'Failed to load satellite data');
                this.updateConnectionStatus('No Data', 'warning');
            }
        } catch (error) {
            console.error('💥 Error loading satellites:', error);
            this.showError(`Network error: ${error.message}`);
            this.updateConnectionStatus('Disconnected', 'danger');
        }
    }

    async loadAirplanes() {
        try {
            console.log('✈️ Fetching airplane data from OpenSky API...');
            this.showLoadingIndicator('Loading airplanes from OpenSky...');

            const response = await fetchWithRetry('/api/airplanes');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('✈️ OpenSky API Response:', {
                success: data.success,
                airplaneCount: data.airplanes?.length || 0,
                hasData: !!data.airplanes
            });

            if (data.success && data.airplanes && data.airplanes.length > 0) {
                // Update airplane data
                const newAirplanes = new Map();
                data.airplanes.forEach(airplane => {
                    // Validate airplane data
                    if (!airplane.icao24 || typeof airplane.latitude !== 'number' || typeof airplane.longitude !== 'number') {
                        console.warn('Invalid airplane data:', airplane);
                        return;
                    }

                    newAirplanes.set(airplane.icao24, airplane);
                });

                this.airplanes = newAirplanes;
                console.log(`✅ Loaded ${newAirplanes.size} valid airplanes`);

                if (this.currentMode === 'airplanes') {
                    this.renderAirplanes();

                    // Update all status elements for airplane mode
                    this.updateStatus(newAirplanes.size, data.timestamp);
                    this.updateConnectionStatus('Connected', 'success');

                    console.log(`📊 Updated UI status: ${newAirplanes.size} airplanes visible`);
                }
            } else {
                console.error('❌ Failed to load airplanes:', data);
                this.showError(data.error || 'Failed to load airplane data');
                this.updateConnectionStatus('No Data', 'warning');
            }
        } catch (error) {
            console.error('💥 Error loading airplanes:', error);
            this.showError(`Network error: ${error.message}`);
            this.updateConnectionStatus('Disconnected', 'danger');
        } finally {
            this.hideLoadingIndicator();
        }
    }

    updateConnectionStatus(text, type) {
        const statusElement = document.getElementById('connectionStatus');
        if (statusElement) {
            statusElement.textContent = text;
            statusElement.className = `badge bg-${type} ms-auto`;
        }
    }

    updateStatus(satelliteCount, timestamp) {
        // Update satellite count
        const countElement = document.getElementById('count');
        if (countElement) {
            countElement.textContent = satelliteCount || this.satellites.size;
        }

        // Update last updated timestamp
        const lastUpdateElement = document.getElementById('lastUpdate');
        if (lastUpdateElement && timestamp) {
            const updateTime = new Date(timestamp);
            lastUpdateElement.textContent = `Last updated: ${updateTime.toLocaleTimeString()}`;
        }

        // Update tracking mode display
        const trackingModeElement = document.getElementById('trackingMode');
        if (trackingModeElement) {
            const icon = this.currentMode === 'satellites' ? 'fas fa-satellite' : 'fas fa-plane';
            const modeText = this.currentMode === 'satellites' ? 'Satellite Mode' : 'Airplane Mode';
            trackingModeElement.innerHTML = `<i class="${icon} me-1"></i>${modeText}`;
        }

        // Check if priority satellites are loaded
        const prioritySatellites = ['LANDSAT', 'SENTINEL', 'WORLDVIEW'];
        let hasPrioritySatellites = false;

        this.satellites.forEach(satellite => {
            if (prioritySatellites.some(prefix => satellite.name.toUpperCase().includes(prefix))) {
                hasPrioritySatellites = true;
            }
        });

        const priorityStatusElement = document.getElementById('prioritySatsStatus');
        if (priorityStatusElement && hasPrioritySatellites) {
            priorityStatusElement.style.display = 'inline-block';
        }

        console.log(`📊 Status updated: ${satelliteCount} satellites, timestamp: ${timestamp}`);
    }

    updateSatellitePositions() {
        // Update positions of existing entities without recreating them
        this.satelliteEntities.forEach((entity, noradId) => {
            const satellite = this.satellites.get(noradId);
            if (satellite && entity.position) {
                // Force position update for smooth motion
                if (entity.position._callback) {
                    entity.position._callback();
                }
                // Also update any visualization entities
                entity._updateCallback?.();
            }
        });

        // Force viewer to re-render
        this.viewer.scene.requestRender();
    }

    renderSatellites() {
        if (!this.viewer || !this.viewer.entities) {
            console.warn('❌ Viewer not ready for satellite rendering');
            return;
        }

        console.log(`🎯 Rendering ${this.satellites.size} satellites`);

        // If we have no entities yet, create them all first
        if (this.satelliteEntities.size === 0) {
            this.createAllSatelliteEntities();
        }

        // Check if search is active before applying filters
        const hasActiveSearch = this.satelliteSearch &&
            this.satelliteSearch.currentQuery &&
            this.satelliteSearch.currentQuery.length > 0;

        if (hasActiveSearch) {
            // If search is active, apply search filter instead of regular filters
            console.log(`🔍 Search active, preserving search filter: "${this.satelliteSearch.currentQuery}"`);
            this.satelliteSearch.applySearchFilter(this.satelliteSearch.currentQuery);
        } else {
            // Apply current filters using satellite filter module only if no search is active
            if (this.satelliteFilter) {
                this.satelliteFilter.applyCurrentFilters();
            }
        }

        console.log(`✅ Satellites rendered with current filters`);
        this.viewer.scene.requestRender();
    }





    createAllSatelliteEntities() {
        console.log(`🔨 Creating entities for ${this.satellites.size} satellites`);

        let createdCount = 0;
        this.satellites.forEach((satellite, noradId) => {

            // CRITICAL FIX: Skip if entity already exists to prevent duplicates
            if (this.satelliteEntities.has(noradId)) {
                // Verify the entity still exists in viewer
                const existingEntity = this.satelliteEntities.get(noradId);
                if (this.viewer.entities.contains(existingEntity)) {
                    return; // Entity exists and is valid, skip creation
                } else {
                    // Entity was removed from viewer but still in map, clean it up
                    this.satelliteEntities.delete(noradId);
                }
            }

            // Validate satellite position data
            if (typeof satellite.latitude !== 'number' || typeof satellite.longitude !== 'number' ||
                typeof satellite.altitude !== 'number' || isNaN(satellite.latitude) ||
                isNaN(satellite.longitude) || isNaN(satellite.altitude)) {
                return;
            }

            // Additional validation for extreme values
            if (Math.abs(satellite.latitude) > 90 || Math.abs(satellite.longitude) > 180 || satellite.altitude < 0) {
                return;
            }

            // Dynamic position with real-time velocity-based movement
            // Uses exponential smoothing to prevent jumps when new data arrives
            let lastRenderedPos = null;
            let lastRenderedTime = null;

            const position = new Cesium.CallbackProperty((time, result) => {
                const currentSat = this.satellites.get(noradId);
                if (!currentSat) {
                    return Cesium.Cartesian3.fromDegrees(
                        satellite.longitude,
                        satellite.latitude,
                        satellite.altitude * 1000,
                        Cesium.Ellipsoid.WGS84,
                        result
                    );
                }

                const now = Date.now();
                const timeSinceUpdate = (now - currentSat.lastUpdateTime) / 1000; // seconds

                // Use velocity to calculate expected position
                const velocity = currentSat.velocity || { latitude: 0, longitude: 0, altitude: 0 };

                let targetLat = currentSat.latitude + (velocity.latitude * timeSinceUpdate);
                let targetLon = currentSat.longitude + (velocity.longitude * timeSinceUpdate);
                let targetAlt = currentSat.altitude + (velocity.altitude * timeSinceUpdate);

                // Handle longitude wrapping
                if (targetLon > 180) targetLon -= 360;
                if (targetLon < -180) targetLon += 360;

                // Clamp latitude
                targetLat = Math.max(-90, Math.min(90, targetLat));
                targetAlt = Math.max(0, targetAlt);

                // Smooth transition when new data arrives
                if (lastRenderedPos && lastRenderedTime && (now - lastRenderedTime) < 100) {
                    // Blend old and new positions over 100ms to prevent jumps
                    const blendFactor = (now - lastRenderedTime) / 100;
                    targetLat = lastRenderedPos.lat + (targetLat - lastRenderedPos.lat) * blendFactor;
                    targetLon = lastRenderedPos.lon + (targetLon - lastRenderedPos.lon) * blendFactor;
                    targetAlt = lastRenderedPos.alt + (targetAlt - lastRenderedPos.alt) * blendFactor;
                }

                // Store for next frame
                lastRenderedPos = { lat: targetLat, lon: targetLon, alt: targetAlt };
                lastRenderedTime = now;

                return Cesium.Cartesian3.fromDegrees(
                    targetLon,
                    targetLat,
                    targetAlt * 1000,
                    Cesium.Ellipsoid.WGS84,
                    result
                );
            }, false);

            // Starlink hidden by default
            const isStarlink = satellite.category === 'starlink' ||
                satellite.name.toUpperCase().includes('STARLINK');

            const entity = this.viewer.entities.add({
                id: `satellite_${noradId}`,
                name: satellite.name,
                position: position,
                point: {
                    pixelSize: 3,
                    color: Cesium.Color.fromCssColorString(satellite.color || '#64b5f6'),
                    outlineColor: Cesium.Color.WHITE,
                    outlineWidth: 0.1,
                    heightReference: Cesium.HeightReference.NONE,
                    show: !isStarlink,
                    disableDepthTestDistance: 0
                },
                label: {
                    text: satellite.name,
                    font: '12pt Arial',
                    fillColor: Cesium.Color.RED,
                    outlineColor: Cesium.Color.GOLD,
                    outlineWidth: 2,
                    style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                    pixelOffset: new Cesium.Cartesian2(0, -25),
                    show: false,
                    scaleByDistance: new Cesium.NearFarScalar(1.5e6, 1.0, 1.5e7, 0.5)
                },
                path: {
                    show: false,
                    leadTime: 3600,
                    trailTime: 900,
                    width: 3,
                    resolution: 60,
                    material: new Cesium.PolylineGlowMaterialProperty({
                        glowPower: 0.4,
                        color: Cesium.Color.fromCssColorString(satellite.color).withAlpha(0.8)
                    })
                },
                satelliteData: satellite
            });

            this.satelliteEntities.set(noradId, entity);
            createdCount++;
        });

        console.log(`🔨 Created ${createdCount} satellite entities`);

        // Enable proper depth testing and lighting for realistic rendering
        try {
            this.viewer.scene.globe.enableLighting = true;
            this.viewer.scene.globe.depthTestAgainstTerrain = true;
        } catch (error) {
            console.warn('Error setting globe properties:', error);
        }
    }

    onEntityClick(event) {
        const pickedObject = this.viewer.scene.pick(event.position);

        if (Cesium.defined(pickedObject)) {
            console.log(`🖱️ Entity clicked in ${this.currentMode} mode:`, pickedObject.id);

            if (this.currentMode === 'satellites' && pickedObject.id.satelliteData) {
                this.onSatelliteClick(event);
            } else if (this.currentMode === 'airplanes' && pickedObject.id.airplaneData) {
                this.onAirplaneClick(event);
            } else {
                console.log('🖱️ Clicked entity does not match current mode or has no data');
            }
        } else {
            if (this.currentMode === 'satellites') {
                this.deselectSatellite();
            } else if (this.currentMode === 'airplanes') {
                this.deselectAirplane();
            }
        }
    }

    onSatelliteClick(event) {
        const pickedObject = this.viewer.scene.pick(event.position);

        if (Cesium.defined(pickedObject) && pickedObject.id.satelliteData) {
            const satellite = pickedObject.id.satelliteData;

            // Clear any existing click timeout
            if (this.clickTimeout) {
                clearTimeout(this.clickTimeout);
                this.clickTimeout = null;

                // This is a double click - enable continuous tracking using workflow
                this.satelliteWorkflow.executeSatelliteSelectionWorkflow(satellite.norad_id, true, 'doubleclick');
                return;
            }

            // This might be a single click - wait to see if double click follows
            this.clickTimeout = setTimeout(() => {
                this.clickTimeout = null;
                // Single click - focus but don't track continuously using workflow
                this.satelliteWorkflow.executeSatelliteSelectionWorkflow(satellite.norad_id, false, 'click');
            }, 300);

        } else {
            this.deselectSatellite();
        }
    }

    async selectSatellite(noradId, enableTracking = false) {
        // Use the new workflow system for consistent satellite selection
        const result = await this.satelliteWorkflow.executeSatelliteSelectionWorkflow(noradId, enableTracking, 'manual');

        // Ensure coverage swath is shown if toggled on
        if (this.showCoverageSwath) {
            this.showCoverageSwathPath(noradId);
        }

        return result;
    }



    clearSatelliteVisualizations(noradId) {
        // Stop satellite tracking
        if (this.satelliteTrackingInterval) {
            clearInterval(this.satelliteTrackingInterval);
            this.satelliteTrackingInterval = null;
        }

        // Clear nadir line
        this.clearNadirLine();

        // Clear ground track circle
        this.clearGroundTrackCircle();

        // Clear future ground track
        this.clearFutureGroundTrack();

        // Clear orbit path
        this.clearOrbitPath(noradId);

        // Clear coverage swath
        this.clearCoverageSwath(noradId);

        // Stop animated ground swath
        this.stopGroundSwathAnimation();

        // Clear ground track
        this.clearSelectedGroundTrack();

        // Stop real-time updates
        this.stopRealTimeDetailsUpdates();
    }

    startRealTimeDetailsUpdates(noradId) {
        // Clear any existing interval
        this.stopRealTimeDetailsUpdates();

        // Update details every 10 seconds for reasonable real-time feel
        this.realTimeUpdateInterval = setInterval(async () => {
            if (this.selectedSatellite === noradId) {
                // Only update details if the panel is currently visible
                const panel = document.getElementById('satelliteDetailsPanel');
                if (panel && panel.classList.contains('show')) {
                    await this.loadSatelliteDetails(noradId);
                }
            }
        }, 10000);
    }

    stopRealTimeDetailsUpdates() {
        if (this.realTimeUpdateInterval) {
            clearInterval(this.realTimeUpdateInterval);
            this.realTimeUpdateInterval = null;
        }
    }

    closeDetailsPanel() {
        const panel = document.getElementById('satelliteDetailsPanel');
        if (panel) {
            panel.classList.add('fade-out');
            panel.classList.remove('show');

            // Hide panel after animation completes
            setTimeout(() => {
                if (panel.classList.contains('fade-out')) {
                    panel.style.display = 'none';
                    panel.classList.remove('fade-out');
                }
            }, 300);
        }
    }

    deselectSatellite() {
        if (this.selectedSatellite) {
            this.clearSatelliteVisualizations(this.selectedSatellite);
        }

        // Disable motion control if active
        if (this.motionControl.motionControlEnabled) {
            this.motionControl.disableMotionControl();
            const motionBtn = document.getElementById('motionControlBtn');
            if (motionBtn) {
                motionBtn.classList.remove('active');
                motionBtn.innerHTML = '<i class="fas fa-route"></i> Motion Control';
            }
        }

        this.selectedSatellite = null;

        // Reset past passes state
        this.passFilter.showingPastPasses = false;

        // Hide past passes info
        const pastPassesInfo = document.getElementById('pastPassesInfo');
        if (pastPassesInfo) {
            pastPassesInfo.style.display = 'none';
        }

        // Hide the sliding panel with animation
        this.closeDetailsPanel();

        this.updateSatelliteSelection();
    }

    updateSatelliteSelection() {
        this.satelliteEntities.forEach((entity, noradId) => {
            const isSelected = noradId === this.selectedSatellite;

            // Enhanced selection appearance with smaller sizes
            entity.point.pixelSize = isSelected ? 6 : 3;
            entity.point.outlineWidth = isSelected ? 0.8 : 0.3;

            // Preserve label visibility for selected satellite
            if (isSelected) {
                entity.label.show = true;
                entity.point.color = Cesium.Color.YELLOW;
                entity.point.outlineColor = Cesium.Color.WHITE;
            } else {
                entity.label.show = false;
                const sat = this.satellites.get(noradId);
                if (sat) {
                    entity.point.color = Cesium.Color.fromCssColorString(sat.color);
                    entity.point.outlineColor = Cesium.Color.WHITE;
                }
            }
        });
    }

    async loadSatelliteDetails(noradId) {
        try {
            // Include user location for signal strength calculation
            const url = `/api/satellite/${noradId}?lat=${this.userLocation.lat}&lon=${this.userLocation.lon}&alt=${this.userLocation.alt}`;
            const response = await fetchWithRetry(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success && data.satellite) {
                // Also fetch EO metadata if available
                let eoMetadata = null;
                try {
                    const eoResponse = await fetchWithRetry(`/api/satellite/${noradId}/eo-metadata`);
                    const eoData = await eoResponse.json();
                    if (eoData.success && eoData.is_eo_satellite) {
                        eoMetadata = eoData.metadata;
                    }
                } catch (eoError) {
                    // Not an EO satellite, that's OK
                    console.log(`Satellite ${noradId} is not an EO satellite`);
                }

                this.renderSatelliteDetails(data.satellite, eoMetadata);
            } else {
                console.warn('Failed to load satellite details:', data);
                document.getElementById('satelliteInfo').style.display = 'none';
            }
        } catch (error) {
            console.error('Error loading satellite details:', error);
            document.getElementById('satelliteInfo').style.display = 'none';
        }
    }

    renderSatelliteDetails(satellite, eoMetadata = null) {
        const container = document.getElementById('satelliteDetails');

        // Get signal strength color based on percentage
        const getSignalColor = (percentage) => {
            if (percentage >= 70) return 'text-success';
            if (percentage >= 40) return 'text-warning';
            return 'text-danger';
        };

        const signalColor = getSignalColor(satellite.signal?.strength_percentage || 0);

        container.innerHTML = `
            <div class="satellite-header mb-3">
                <strong class="text-info">${satellite.name}</strong>
            </div>

            <!-- Signal Information -->
            ${satellite.signal ? `
            <div class="satellite-section mb-3">
                <h6 class="text-primary mb-2">
                    <i class="fas fa-wifi me-2"></i>Signal Strength
                </h6>
                <div class="row g-2">
                    <div class="col-6"><small class="text-muted">Strength:</small></div>
                    <div class="col-6"><small class="${signalColor}">${satellite.signal.strength_percentage.toFixed(1)}% (${satellite.signal.strength_dbm} dBm)</small></div>
                    <div class="col-6"><small class="text-muted">Distance:</small></div>
                    <div class="col-6"><small class="text-info">${satellite.signal.distance_km.toFixed(1)} km</small></div>
                    <div class="col-6"><small class="text-muted">Elevation:</small></div>
                    <div class="col-6"><small class="text-success">${satellite.signal.elevation_deg.toFixed(1)}°</small></div>
                    <div class="col-6"><small class="text-muted">Azimuth:</small></div>
                    <div class="col-6"><small class="text-warning">${satellite.signal.azimuth_deg.toFixed(1)}°</small></div>
                    <div class="col-6"><small class="text-muted">Frequency:</small></div>
                    <div class="col-6"><small class="text-cyan">${satellite.signal.frequency_mhz.toFixed(1)} MHz</small></div>
                    <div class="col-6"><small class="text-muted">Path Loss:</small></div>
                    <div class="col-6"><small class="text-secondary">${satellite.signal.path_loss_db.toFixed(1)} dB</small></div>
                </div>
            </div>
            ` : ''}

            <!-- Earth Observation Information -->
            ${eoMetadata ? `
            <div class="satellite-section mb-3">
                <h6 class="text-info mb-2">
                    <i class="fas fa-camera me-2"></i>Earth Observation
                </h6>
                <div class="row g-2">
                    <div class="col-6"><small class="text-muted">Constellation:</small></div>
                    <div class="col-6"><small class="text-success">${eoMetadata.constellation}</small></div>
                    <div class="col-6"><small class="text-muted">Operator:</small></div>
                    <div class="col-6"><small class="text-info">${eoMetadata.operator}</small></div>
                    <div class="col-6"><small class="text-muted">Sensor Type:</small></div>
                    <div class="col-6"><small class="text-primary">${eoMetadata.sensor_type.toUpperCase()}</small></div>
                    <div class="col-6"><small class="text-muted">Resolution:</small></div>
                    <div class="col-6"><small class="text-warning">${eoMetadata.spatial_res_m}m</small></div>
                    <div class="col-6"><small class="text-muted">Swath Width:</small></div>
                    <div class="col-6"><small class="text-cyan">${eoMetadata.swath_km} km</small></div>
                    <div class="col-6"><small class="text-muted">Data Access:</small></div>
                    <div class="col-6"><small class="${eoMetadata.data_access === 'open' ? 'text-success' : 'text-warning'}">${eoMetadata.data_access.toUpperCase()}</small></div>
                    ${eoMetadata.tasking ? `
                    <div class="col-6"><small class="text-muted">Tasking:</small></div>
                    <div class="col-6"><small class="text-success">✓ Available</small></div>
                    ` : ''}
                </div>
            </div>
            ` : ''}

            <!-- Orbit Information -->
            <div class="satellite-section mb-3">
                <h6 class="text-warning mb-2">
                    <i class="fas fa-circle-notch me-2"></i>Orbit
                </h6>
                <div class="row g-2">
                    <div class="col-6"><small class="text-muted">Altitude:</small></div>
                    <div class="col-6"><small class="text-success">${satellite.orbit.altitude.toFixed(1)} km</small></div>
                    <div class="col-6"><small class="text-muted">Inclination:</small></div>
                    <div class="col-6"><small class="text-info">${satellite.orbit.inclination.toFixed(2)}°</small></div>
                    <div class="col-6"><small class="text-muted">Period:</small></div>
                    <div class="col-6"><small class="text-primary">${satellite.orbit.period.toFixed(1)} min</small></div>
                    <div class="col-6"><small class="text-muted">Velocity:</small></div>
                    <div class="col-6"><small class="text-warning">${satellite.orbit.velocity.toFixed(2)} km/s</small></div>
                    <div class="col-6"><small class="text-muted">Orbit Type:</small></div>
                    <div class="col-6"><small class="text-cyan">${satellite.orbit.orbit_type}</small></div>
                </div>
            </div>

            <!-- Position Information -->
            <div class="satellite-section mb-3">
                <h6 class="text-success mb-2">
                    <i class="fas fa-map-marker-alt me-2"></i>Position
                </h6>
                <div class="row g-2">
                    <div class="col-6"><small class="text-muted">Latitude:</small></div>
                    <div class="col-6"><small class="text-success">${satellite.position.latitude.toFixed(4)}°</small></div>
                    <div class="col-6"><small class="text-muted">Longitude:</small></div>
                    <div class="col-6"><small class="text-success">${satellite.position.longitude.toFixed(4)}°</small></div>
                    <div class="col-6"><small class="text-muted">Country:</small></div>
                    <div class="col-6"><small class="text-info">${satellite.position.country}</small></div>
                    <div class="col-6"><small class="text-muted">Visibility:</small></div>
                    <div class="col-6"><small class="text-warning">${satellite.position.visibility}</small></div>
                </div>
            </div>

            <!-- Technical Information -->
            <div class="satellite-section">
                <h6 class="text-cyan mb-2">
                    <i class="fas fa-cog me-2"></i>Technical
                </h6>
                <div class="row g-2">
                    <div class="col-6"><small class="text-muted">NORAD ID:</small></div>
                    <div class="col-6"><small class="text-white">${satellite.technical.norad_id}</small></div>
                    <div class="col-6"><small class="text-muted">Launch Date:</small></div>
                    <div class="col-6"><small class="text-primary">${satellite.technical.launch_date}</small></div>
                    <div class="col-6"><small class="text-muted">Type:</small></div>
                    <div class="col-6"><small class="text-info">${satellite.technical.type}</small></div>
                    <div class="col-6"><small class="text-muted">Agency:</small></div>
                    <div class="col-6"><small class="text-warning">${satellite.technical.agency}</small></div>
                    <div class="col-6"><small class="text-muted">Status:</small></div>
                    <div class="col-6"><small class="text-success">${satellite.technical.status}</small></div>
                </div>
            </div>
            <div class="d-flex justify-content-start mt-3 gap-2">
                        ${this.isISS(satellite) ? `
                            <button class="btn btn-primary btn-sm" onclick="showISSVideo()">
                                <i class="fas fa-video"></i> Live Video
                            </button>
                        ` : ''}
                        ${this.isEarthObservationSatellite(satellite.technical.norad_id) ? `
                            <div class="btn-group" role="group">
                                <button type="button" class="btn btn-success btn-sm dropdown-toggle" data-bs-toggle="dropdown" aria-expanded="false">
                                    <i class="fas fa-images"></i> Imagery
                                </button>
                                <ul class="dropdown-menu dropdown-menu-dark">
                                    ${this.getImageryLinks(satellite.technical.norad_id, satellite.name).map((link, index) => `
                                        <li>
                                            <a class="dropdown-item ${link.available ? 'text-success' : 'text-warning'}" 
                                               href="${link.url}" target="_blank" rel="noopener noreferrer">
                                                ${link.name}
                                                ${link.available ? '<i class="fas fa-external-link-alt ms-1"></i>' : '<small class="text-muted">(Limited)</small>'}
                                            </a>
                                        </li>
                                    `).join('')}
                                </ul>
                            </div>
                        ` : ''}
                        <button class="btn btn-warning btn-sm" id="pastPassesBtn" onclick="satelliteViewer.passFilter.togglePastPasses()">
                            <i class="fas fa-history"></i> Past Passes
                        </button>
                        </div>
        `;

        // Only show the panel if it's not already visible (initial selection)
        const panel = document.getElementById('satelliteDetailsPanel');
        if (panel && !panel.classList.contains('show') && typeof window.showDetailsPanel === 'function') {
            window.showDetailsPanel();
        }
    }

    clearSelectedGroundTrack() {
        if (this.selectedSatellite) {
            const swathEntity = this.groundTrackEntities.get(`swath_${this.selectedSatellite}`);
            const centerEntity = this.groundTrackEntities.get(`center_${this.selectedSatellite}`);
            const currentEntity = this.groundTrackEntities.get(`current_${this.selectedSatellite}`);
            const futureSwathEntity = this.groundTrackEntities.get(`future_swath_${this.selectedSatellite}`);
            const futureCenterEntity = this.groundTrackEntities.get(`future_center_${this.selectedSatellite}`);

            if (swathEntity) {
                this.viewer.entities.remove(swathEntity);
                this.groundTrackEntities.delete(`swath_${this.selectedSatellite}`);
            }
            if (centerEntity) {
                this.viewer.entities.remove(centerEntity);
                this.groundTrackEntities.delete(`center_${this.selectedSatellite}`);
            }
            if (currentEntity) {
                this.viewer.entities.remove(currentEntity);
                this.groundTrackEntities.delete(`current_${this.selectedSatellite}`);
            }
            if (futureSwathEntity) {
                this.viewer.entities.remove(futureSwathEntity);
                this.groundTrackEntities.delete(`future_swath_${this.selectedSatellite}`);
            }
            if (futureCenterEntity) {
                this.viewer.entities.remove(futureCenterEntity);
                this.groundTrackEntities.delete(`future_center_${this.selectedSatellite}`);
            }
        }
    }

    clearSelectedOrbit() {
        if (this.selectedSatellite) {
            const orbitEntity = this.orbitEntities.get(this.selectedSatellite);
            if (orbitEntity) {
                this.viewer.entities.remove(orbitEntity);
                this.orbitEntities.delete(this.selectedSatellite);
            }
        }
    }

    async loadPassPredictions(noradId) {
        if (!this.userLocation.lat && !this.userLocation.lon) {
            console.log('User location not set, skipping pass predictions');
            return;
        }

        try {
            // Include current motion control time for accurate pass calculations
            let timeOffset = 0;
            if (this.motionControl.motionControlEnabled && this.motionControl.orbitTimeData && this.motionControl.currentOrbitTimeIndex < this.motionControl.orbitTimeData.length) {
                const currentMotionTime = this.motionControl.orbitTimeData[this.motionControl.currentOrbitTimeIndex];
                const realTime = Date.now();
                timeOffset = Math.round((currentMotionTime - realTime) / 1000); // offset in seconds
            }

            const response = await fetchWithRetry(`/api/satellite/${noradId}/passes?lat=${this.userLocation.lat}&lon=${this.userLocation.lon}&alt=${this.userLocation.alt}&time_offset=${timeOffset}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success && data.passes) {
                this.displayPassPredictions(data.passes, noradId, data.is_earth_observation, data.fov_info, data.pass_calculation);
            } else {
                console.warn('Failed to load pass predictions:', data);
            }
        } catch (error) {
            console.error('Error loading pass predictions:', error);
        }
    }

    displayPassPredictions(passes, noradId, isEarthObservation = false, fovInfo = null, calculationType = 'Standard') {
        const passInfo = document.getElementById('passInfo');
        if (!passInfo) return;

        // Clear existing content
        const headerText = isEarthObservation ? 'Coverage Pass Predictions' : 'Overhead Passes';
        const headerIcon = isEarthObservation ? 'fas fa-satellite' : 'fas fa-crosshairs';

        passInfo.innerHTML = `
            <h6 class="text-info mb-3">
                <i class="${headerIcon} me-2"></i>${headerText}
                ${isEarthObservation ? '<span class="badge bg-success ms-2">EO Satellite</span>' : ''}
            </h6>
        `;

        // Add FOV information for Earth observation satellites
        if (isEarthObservation && fovInfo) {
            const fovInfoDiv = document.createElement('div');
            fovInfoDiv.className = 'alert alert-info mb-3';
            fovInfoDiv.innerHTML = `
                <div class="row">
                    <div class="col-12">
                        <strong>Field of View Information:</strong><br>
                        <small>Swath Width: ${fovInfo.default_swath || 'N/A'} km</small><br>
                        <small>Sensors: ${fovInfo.sensors ? fovInfo.sensors.join(', ') : 'N/A'}</small><br>
                        <small>Country: ${fovInfo.country || 'N/A'}</small><br>
                        <small>Calculation Type: ${calculationType}</small>
                    </div>
                </div>
            `;
            passInfo.appendChild(fovInfoDiv);
        }

        if (!passes || passes.length === 0) {
            const noPassesMsg = isEarthObservation ?
                'No coverage opportunities in the next 7 days based on satellite FOV.' :
                'No overhead passes in the next 7 days for your location.';
            passInfo.innerHTML += `<p class="text-muted">${noPassesMsg}</p>`;
            return;
        }

        // Create tabs for each pass
        const navTabs = document.createElement('ul');
        navTabs.className = 'nav nav-tabs';
        navTabs.id = 'passNavTabs';
        navTabs.setAttribute('role', 'tablist');

        const tabContent = document.createElement('div');
        tabContent.className = 'tab-content';
        tabContent.id = 'passTabContent';

        passes.forEach((pass, index) => {
            const passDate = new Date(pass.rise_time);
            const tabId = `pass-${noradId}-${index}`;
            const paneId = `pane-${noradId}-${index}`;

            // Create tab
            const tabItem = document.createElement('li');
            tabItem.className = 'nav-item';
            tabItem.setAttribute('role', 'presentation');

            const tabLink = document.createElement('button');
            tabLink.className = `nav-link ${index === 0 ? 'active' : ''}`;
            tabLink.id = tabId;
            tabLink.setAttribute('data-bs-toggle', 'tab');
            tabLink.setAttribute('data-bs-target', `#${paneId}`);
            tabLink.setAttribute('type', 'button');
            tabLink.setAttribute('role', 'tab');
            tabLink.setAttribute('aria-controls', paneId);
            tabLink.setAttribute('aria-selected', index === 0 ? 'true' : 'false');

            const tabText = isEarthObservation ? `Coverage ${index + 1}` : `Pass ${index + 1}`;
            tabLink.textContent = tabText;

            tabItem.appendChild(tabLink);
            navTabs.appendChild(tabItem);

            // Create tab pane
            const tabPane = document.createElement('div');
            tabPane.className = `tab-pane fade ${index === 0 ? 'show active' : ''}`;
            tabPane.id = paneId;
            tabPane.setAttribute('role', 'tabpanel');
            tabPane.setAttribute('aria-labelledby', tabId);

            // Format times
            const riseTime = new Date(pass.rise_time);
            const setTime = new Date(pass.set_time);
            const culminationTime = new Date(pass.culmination_time);

            // Enhanced display for Earth observation satellites
            let additionalInfo = '';
            if (isEarthObservation && pass.sensors) {
                additionalInfo = `
                    <div class="row mb-2">
                        <div class="col-12">
                            <small class="text-muted">Sensors:</small><br>
                            <small class="text-info">${pass.sensors.join(', ')}</small>
                        </div>
                    </div>
                `;
            }

            if (pass.swath_width) {
                additionalInfo += `
                    <div class="row mb-2">
                        <div class="col-6">
                            <small class="text-muted">Swath Width:</small><br>
                            <small class="text-success">${pass.swath_width} km</small>
                        </div>
                        <div class="col-6">
                            <small class="text-muted">Coverage Type:</small><br>
                            <small class="text-warning">${pass.coverage_type || 'Standard'}</small>
                        </div>
                    </div>
                `;
            }

            const startLabel = isEarthObservation ? 'Coverage Start:' : 'Overhead Start:';
            const endLabel = isEarthObservation ? 'Coverage End:' : 'Overhead End:';

            tabPane.innerHTML = `
                <div class="pass-item mt-3">
                    <div class="row mb-2">
                        <div class="col-6">
                            <small class="text-muted">${startLabel}</small><br>
                            <small class="text-primary">${riseTime.toLocaleDateString()} ${riseTime.toLocaleTimeString()}</small>
                        </div>
                        <div class="col-6">
                            <small class="text-muted">${endLabel}</small><br>
                            <small class="text-primary">${setTime.toLocaleDateString()} ${setTime.toLocaleTimeString()}</small>
                        </div>
                    </div>
                    <div class="row mb-2">
                        <div class="col-6">
                            <small class="text-muted">Max Elevation:</small><br>
                            <small class="text-success">${pass.max_elevation}°</small>
                        </div>
                        <div class="col-6">
                            <small class="text-muted">Duration:</small><br>
                            <small class="text-info">${pass.duration_minutes} min</small>
                        </div>
                    </div>
                    ${additionalInfo}
                    <div class="row mb-2">
                        <div class="col-6">
                            <small class="text-muted">Start Az:</small><br>
                            <small class="text-primary">${pass.rise_azimuth?.toFixed(1)}°</small>
                        </div>
                        <div class="col-6">
                            <small class="text-muted">End Az:</small><br>
                            <small class="text-primary">${pass.set_azimuth?.toFixed(1)}°</small>
                        </div>
                    </div>
                    ${pass.min_distance ? `
                        <div class="row mt-2">
                            <div class="col-6">
                                <small class="text-muted">Min Distance:</small><br>
                                <small class="text-success">${pass.min_distance} km</small>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Overhead Threshold:</small><br>
                                <small class="text-info">${pass.overhead_threshold_km} km</small>
                            </div>
                        </div>
                    ` : ''}
                    ${pass.calculation_method ? `
                        <div class="row mt-2">
                            <div class="col-12">
                                <small class="text-muted">Method:</small><br>
                                <small class="badge bg-info">${pass.calculation_method}</small>
                            </div>
                        </div>
                    ` : ''}
                    ${pass.pass_type ? `
                        <div class="row mt-2">
                            <div class="col-12">
                                <small class="text-muted">Pass Type:</small><br>
                                <small class="badge bg-primary">${pass.pass_type}</small>
                            </div>
                        </div>
                    ` : ''}
                </div>
            `;

            tabContent.appendChild(tabPane);
        });

        passInfo.appendChild(navTabs);
        passInfo.appendChild(tabContent);
    }



    focusOnSatellite(noradId) {
        const satellite = this.satellites.get(noradId);
        if (!satellite) {
            console.warn(`❌ Cannot focus on satellite ${noradId} - not found`);
            return;
        }

        console.log(`🎯 Focusing on satellite: ${satellite.name} at ${satellite.latitude.toFixed(4)}, ${satellite.longitude.toFixed(4)}, ${satellite.altitude.toFixed(1)}km`);

        // Calculate proper viewing distance based on satellite altitude
        const satelliteAltitude = parseFloat(satellite.altitude) * 1000; // Convert km to meters
        const viewingDistance = Math.max(satelliteAltitude * 3, 2000000); // Better distance calculation

        const destination = Cesium.Cartesian3.fromDegrees(
            parseFloat(satellite.longitude),
            parseFloat(satellite.latitude),
            viewingDistance
        );

        // Enhanced camera positioning
        this.viewer.camera.flyTo({
            destination: destination,
            orientation: {
                heading: 0.0,
                pitch: -Cesium.Math.PI_OVER_TWO, // Better viewing angle
                roll: 0.0
            },
            duration: 2.5, // Slightly longer for smoother movement
            easingFunction: Cesium.EasingFunction.CUBIC_IN_OUT,
            complete: () => {
                console.log(`✅ Camera focus completed for ${satellite.name}`);

                // Force scene update to ensure proper rendering
                this.viewer.scene.requestRender();

                // Ensure satellite is visible and highlighted after focus
                const entity = this.satelliteEntities.get(noradId);
                if (entity && entity.point) {
                    entity.point.show = true;
                    entity.point.pixelSize = 6;
                    entity.point.color = Cesium.Color.YELLOW;
                    entity.label.show = true;
                }
            }
        });
    }

    trackSatellite(noradId) {
        // Clear any existing tracking interval
        if (this.satelliteTrackingInterval) {
            clearInterval(this.satelliteTrackingInterval);
        }

        // Initial focus on satellite in space
        this.focusOnSatellite(noradId);

        // Set up continuous tracking of satellite in space
        this.satelliteTrackingInterval = setInterval(() => {
            if (this.selectedSatellite === noradId && this.trackingMode) {
                const satellite = this.satellites.get(noradId);
                if (satellite) {
                    // Track the actual satellite position in space, not ground track
                    const satellitePosition = Cesium.Cartesian3.fromDegrees(
                        parseFloat(satellite.longitude),
                        parseFloat(satellite.latitude),
                        parseFloat(satellite.altitude) * 1000 // Convert km to meters for satellite altitude
                    );

                    // Calculate a viewing position that's offset from the satellite
                    const offset = Cesium.Cartesian3.fromDegrees(
                        parseFloat(satellite.longitude),
                        parseFloat(satellite.latitude),
                        (parseFloat(satellite.altitude) + 2000) * 1000 // 2000km above satellite
                    );

                    // Use setView for smooth continuous tracking of the satellite
                    this.viewer.camera.setView({
                        destination: offset,
                        orientation: {
                            heading: 0.0,
                            pitch: -Cesium.Math.PI_OVER_TWO, // Look down at an angle
                            roll: 0.0
                        }
                    });
                }
            }
        }, 5000); // Update camera position every 5 seconds for smooth tracking
    }







    async showOrbitPath(noradId) {
        try {
            // Use the same backend timestamp that satellite positions use
            const timestampParam = this.backendTimestampISO ? `&timestamp=${encodeURIComponent(this.backendTimestampISO)}` : '';
            const response = await fetchWithRetry(`/api/satellite/${noradId}/orbit?duration=3${timestampParam}`);
            const data = await response.json();

            if (data.success && data.orbit_points.length > 0) {
                this.renderOrbitPath(noradId, data.orbit_points);
            }
        } catch (error) {
            console.error('Error loading orbit path:', error);
        }
    }

    renderOrbitPath(noradId, orbitPoints) {
        // Remove existing orbit for this satellite
        this.clearOrbitPath(noradId);

        if (orbitPoints.length < 2) return;

        const positions = [];
        orbitPoints.forEach(point => {
            positions.push(Cesium.Cartesian3.fromDegrees(
                point.longitude,
                point.latitude,
                point.altitude * 1000
            ));
        });

        const satellite = this.satellites.get(noradId);
        const color = satellite ? satellite.color : '#FFFF00';

        const orbitEntity = this.viewer.entities.add({
            id: `orbit_${noradId}`,
            polyline: {
                positions: positions,
                width: 3,
                material: new Cesium.PolylineGlowMaterialProperty({
                    glowPower: 0.3,
                    color: Cesium.Color.fromCssColorString(color).withAlpha(0.8)
                }),
                clampToGround: false
            }
        });

        this.orbitEntities.set(noradId, orbitEntity);
    }

    clearOrbitPath(noradId) {
        const orbitEntity = this.orbitEntities.get(noradId);
        if (orbitEntity) {
            this.viewer.entities.remove(orbitEntity);
            this.orbitEntities.delete(noradId);
        }
    }

    renderNadirLine(noradId) {
        this.clearNadirLine();

        const satellite = this.satellites.get(noradId);
        if (!satellite) return;

        const color = satellite ? satellite.color : '#64b5f6';

        // Get accurate FOV data for this satellite
        const fovData = this.getFOVDataForSatellite(noradId);

        // Create dynamic nadir line that updates with satellite position
        const nadirLine = this.viewer.entities.add({
            id: `nadir_line_${noradId}`,
            polyline: {
                positions: new Cesium.CallbackProperty(() => {
                    const currentSat = this.satellites.get(noradId);
                    if (currentSat) {
                        const groundPos = Cesium.Cartesian3.fromDegrees(
                            currentSat.longitude,
                            currentSat.latitude,
                            0
                        );
                        const satPos = Cesium.Cartesian3.fromDegrees(
                            currentSat.longitude,
                            currentSat.latitude,
                            currentSat.altitude * 1000
                        );
                        return [groundPos, satPos];
                    }
                    return [];
                }, false),
                width: 3,
                material: new Cesium.PolylineGlowMaterialProperty({
                    glowPower: 0.4,
                    color: Cesium.Color.fromCssColorString(color).withAlpha(0.9)
                }),
                clampToGround: false
            }
        });

        // Create accurate FOV circle that accounts for look angles and real FOV data
        const fovCircle = this.viewer.entities.add({
            id: `fov_circle_${noradId}`,
            position: new Cesium.CallbackProperty(() => {
                const currentSat = this.satellites.get(noradId);
                if (currentSat) {
                    return Cesium.Cartesian3.fromDegrees(
                        currentSat.longitude,
                        currentSat.latitude,
                        0
                    );
                }
                return Cesium.Cartesian3.fromDegrees(
                    satellite.longitude,
                    satellite.latitude,
                    0
                );
            }, false),
            ellipse: {
                semiMajorAxis: new Cesium.CallbackProperty(() => {
                    const currentSat = this.satellites.get(noradId);
                    if (currentSat) {
                        return this.calculateAccurateFOVRadius(noradId, currentSat.altitude);
                    }
                    return this.calculateAccurateFOVRadius(noradId, satellite.altitude);
                }, false),
                semiMinorAxis: new Cesium.CallbackProperty(() => {
                    const currentSat = this.satellites.get(noradId);
                    if (currentSat) {
                        return this.calculateAccurateFOVRadius(noradId, currentSat.altitude);
                    }
                    return this.calculateAccurateFOVRadius(noradId, satellite.altitude);
                }, false),
                material: new Cesium.ColorMaterialProperty(
                    Cesium.Color.fromCssColorString(color).withAlpha(0.25)
                ),
                outline: true,
                outlineColor: Cesium.Color.fromCssColorString(color).withAlpha(0.8),
                height: 0,
                rotation: new Cesium.CallbackProperty(() => {
                    // Rotation based on satellite orbital direction for realism
                    const currentSat = this.satellites.get(noradId);
                    if (currentSat) {
                        // Calculate orbital direction based on inclination and longitude change
                        return Math.atan2(currentSat.latitude, currentSat.longitude) + Math.PI / 2;
                    }
                    return 0;
                }, false)
            }
        });

        this.nadirEntities.set(`line_${noradId}`, nadirLine);
        this.nadirEntities.set(`circle_${noradId}`, fovCircle);
    }

    getFOVDataForSatellite(noradId) {
        // FOV database for known Earth observation satellites
        const fovDatabase = {
            // Sentinel satellites
            39634: { swath_width: 250, look_angle: 30.45 }, // Sentinel-1A
            42063: { swath_width: 290, look_angle: 20.6 },  // Sentinel-2A
            43437: { swath_width: 290, look_angle: 20.6 },  // Sentinel-2B
            43485: { swath_width: 1270, look_angle: 68.5 }, // Sentinel-3A
            44427: { swath_width: 1270, look_angle: 68.5 }, // Sentinel-3B
            43564: { swath_width: 2600, look_angle: 77.0 }, // Sentinel-5P

            // Landsat satellites
            39084: { swath_width: 185, look_angle: 15.0 },  // Landsat-8
            49260: { swath_width: 185, look_angle: 15.0 },  // Landsat-9

            // Terra & Aqua (MODIS)
            25994: { swath_width: 2330, look_angle: 110.0 }, // Terra
            27424: { swath_width: 2330, look_angle: 110.0 }, // Aqua

            // WorldView satellites
            32060: { swath_width: 17.6, look_angle: 1.35 }, // WorldView-1
            35946: { swath_width: 16.4, look_angle: 1.35 }, // WorldView-2
            40115: { swath_width: 13.1, look_angle: 1.07 }, // WorldView-3

            // NOAA satellites (AVHRR)
            33591: { swath_width: 2900, look_angle: 112.0 }, // NOAA-19
            43013: { swath_width: 3000, look_angle: 112.0 }, // NOAA-20
        };

        return fovDatabase[noradId] || { swath_width: 300, look_angle: 30 }; // Default FOV
    }

    calculateAccurateFOVRadius(noradId, altitude_km) {
        const fovData = this.getFOVDataForSatellite(noradId);
        const earth_radius = 6371.0; // km
        const altitude = altitude_km;

        // For nadir-only instruments
        if (fovData.swath_width === 0) {
            return 1000; // 1km radius for nadir-only
        }

        // Calculate ground footprint using look angle and satellite altitude
        // Ground range = altitude * tan(look_angle/2)
        const half_look_angle_rad = (fovData.look_angle / 2) * (Math.PI / 180);

        // More accurate calculation considering Earth curvature
        const sat_distance = earth_radius + altitude;
        const ground_range_rad = Math.asin((sat_distance * Math.sin(half_look_angle_rad)) / earth_radius);
        const ground_range_km = earth_radius * ground_range_rad;

        // Convert to meters for Cesium
        return ground_range_km * 1000;
    }

    async renderFutureGroundTrack(noradId) {
        // Future ground tracks disabled - only nadir line and FOV circle are shown
        console.log('Future ground track rendering disabled');
        return;
    }

    clearNadirLine() {
        if (this.selectedSatellite) {
            const lineEntity = this.nadirEntities.get(`line_${this.selectedSatellite}`);
            const circleEntity = this.nadirEntities.get(`circle_${this.selectedSatellite}`);

            if (lineEntity) {
                this.viewer.entities.remove(lineEntity);
                this.nadirEntities.delete(`line_${this.selectedSatellite}`);
            }
            if (circleEntity) {
                this.viewer.entities.remove(circleEntity);
                this.nadirEntities.delete(`circle_${this.selectedSatellite}`);
            }
        }
    }

    clearFutureGroundTrack() {
        if (this.selectedSatellite) {
            const futureSwathEntity = this.groundTrackEntities.get(`future_swath_${this.selectedSatellite}`);
            const futureCenterEntity = this.groundTrackEntities.get(`future_center_${this.selectedSatellite}`);

            if (futureSwathEntity) {
                this.viewer.entities.remove(futureSwathEntity);
                this.groundTrackEntities.delete(`future_swath_${this.selectedSatellite}`);
            }
            if (futureCenterEntity) {
                this.viewer.entities.remove(futureCenterEntity);
                this.groundTrackEntities.delete(`future_center_${this.selectedSatellite}`);
            }
        }
    }

    clearGroundTrackCircle() {
        // This method is for compatibility - ground track circles are handled by clearNadirLine
        // since the circular swath is part of the nadir visualization
    }

    toggleGroundTracks() {
        this.showGroundTracks = !this.showGroundTracks;
        const btn = document.getElementById('groundTracksBtn');

        if (this.showGroundTracks) {
            btn.classList.add('active');
            // Show nadir line and FOV circle for earth observation satellites
            if (this.selectedSatellite && this.isEarthObservationSatellite(this.selectedSatellite)) {
                this.renderNadirLine(this.selectedSatellite);
            }
        } else {
            btn.classList.remove('active');
            this.clearNadirLine();
        }
    }

    toggleOrbits() {
        this.showOrbits = !this.showOrbits;
        const btn = document.getElementById('orbitsBtn');

        if (this.showOrbits) {
            btn.classList.add('active');
            if (this.selectedSatellite) {
                this.showOrbitPath(this.selectedSatellite);
            }
        } else {
            btn.classList.remove('active');
            this.clearSelectedOrbit();
        }
    }

    clearOrbitPaths() {
        this.orbitEntities.forEach(entity => {
            this.viewer.entities.remove(entity);
        });
        this.orbitEntities.clear();
    }

    toggleStarlink() {
        this.starlinkVisible = !this.starlinkVisible;

        this.satelliteEntities.forEach((entity, noradId) => {
            const satellite = this.satellites.get(noradId);
            if (!satellite) return;
            if (satellite.category === 'starlink' || satellite.name.toUpperCase().includes('STARLINK')) {
                if (entity.point) entity.point.show = this.starlinkVisible;
                if (entity.label) entity.label.show = false;
            }
        });

        const btn = document.getElementById('starlinkToggleBtn');
        if (btn) {
            if (this.starlinkVisible) {
                btn.classList.add('starlink-visible');
                btn.innerHTML = '<i class="fas fa-eye-slash me-1"></i> Hide Starlink';
            } else {
                btn.classList.remove('starlink-visible');
                btn.innerHTML = '<i class="fas fa-satellite me-1"></i> See Starlink';
            }
        }

        this.viewer.scene.requestRender();
    }

    // =========================================================================
    // COVERAGE SWATH VISUALIZATION (EO Satellites)
    // =========================================================================

    toggleCoverageSwath() {
        this.showCoverageSwath = !this.showCoverageSwath;
        const btn = document.getElementById('coverageSwathBtn');

        if (this.showCoverageSwath) {
            btn.classList.add('active');
            if (this.selectedSatellite) {
                this.showCoverageSwathPath(this.selectedSatellite);
            }
        } else {
            btn.classList.remove('active');
            if (this.selectedSatellite) {
                this.clearCoverageSwath(this.selectedSatellite);
            } else {
                this.clearCoverageSwath();
            }
        }
    }

    async showCoverageSwathPath(noradId) {
        try {
            console.log(`📊 Loading coverage swath for satellite ${noradId}...`);

            // Clear ALL previous swaths first to avoid showing multiple satellites
            this.clearCoverageSwath();

            // Use 1.6-hour intervals to ensure full orbit coverage (~100 mins)
            const hours_past = 1.6;
            const hours_future = 1.6;
            const interval_minutes = 2;  // Finer resolution prevents swath misalignment at poles
            const response = await fetchWithRetry(
                `/api/satellite/${noradId}/coverage-swath?hours_past=${hours_past}&hours_future=${hours_future}&interval_minutes=${interval_minutes}`
            );
            const data = await response.json();

            if (data.success && data.coverage) {
                this.renderCoverageSwath(noradId, data.coverage);
                console.log(`✅ Coverage swath loaded: ${data.coverage.sensor_type} sensor, ${data.coverage.swath_km}km swath`);
            } else {
                console.warn(`❌ Failed to load coverage swath: ${data.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Error loading coverage swath:', error);
        }
    }

    renderCoverageSwath(noradId, coverageData) {
        this.clearCoverageSwath(noradId);
        this.coverageSwathEntities.set(noradId, []);

        // --- coordinate helpers (unchanged) ---

        const isValidCoord = (c) =>
            c && c.length >= 2 && isFinite(c[0]) && isFinite(c[1]) &&
            c[1] >= -90 && c[1] <= 90;

        const normalizeLonContinuity = (coords) => {
            if (!coords.length) return coords;
            const out = [[coords[0][0], coords[0][1]]];
            let prev = coords[0][0];
            for (let i = 1; i < coords.length; i++) {
                let lon = coords[i][0];
                while (lon - prev > 180) lon -= 360;
                while (lon - prev < -180) lon += 360;
                out.push([lon, coords[i][1]]);
                prev = lon;
            }
            return out;
        };

        const removeDuplicates = (coords) => {
            if (!coords.length) return coords;
            const out = [coords[0]];
            for (let i = 1; i < coords.length; i++) {
                const p = out[out.length - 1];
                if (Math.abs(coords[i][0] - p[0]) > 1e-6 || Math.abs(coords[i][1] - p[1]) > 1e-6)
                    out.push(coords[i]);
            }
            return out;
        };

        // --- build GeometryInstances from quad strips ---
        // Uses GroundPrimitive (stencil-based) instead of entity polygons so the
        // swath renders correctly regardless of depth buffer precision — which is
        // unusable at Earth-surface scales given the near=0.1 / far=5e10 frustum.

        const buildQuadInstances = (polygons, color, alpha) => {
            const instances = [];
            polygons.forEach((polygon) => {
                if (!polygon.coordinates || !polygon.coordinates.length) return;
                let coords = polygon.coordinates[0].filter(isValidCoord);
                if (coords.length > 1) {
                    const f = coords[0], l = coords[coords.length - 1];
                    if (Math.abs(f[0] - l[0]) < 1e-4 && Math.abs(f[1] - l[1]) < 1e-4)
                        coords = coords.slice(0, -1);
                }
                coords = removeDuplicates(coords);
                if (coords.length < 4) return;
                coords = normalizeLonContinuity(coords);

                const N = Math.floor(coords.length / 2);
                if (N < 2) return;
                const leftEdge = coords.slice(0, N);
                const rightEdge = coords.slice(N).reverse();

                const segCount = Math.min(leftEdge.length, rightEdge.length) - 1;
                for (let i = 0; i < segCount; i++) {
                    const l0 = leftEdge[i], l1 = leftEdge[i + 1];
                    const r0 = rightEdge[i], r1 = rightEdge[i + 1];
                    if (!isValidCoord(l0) || !isValidCoord(l1) ||
                        !isValidCoord(r0) || !isValidCoord(r1)) continue;

                    const quad = normalizeLonContinuity([l0, l1, r1, r0]);
                    const lons = quad.map(c => c[0]);
                    if (Math.max(...lons) - Math.min(...lons) > 180) continue;

                    // No height — GroundPrimitive drapes directly onto the terrain surface
                    const positions = quad.map(c => Cesium.Cartesian3.fromDegrees(c[0], c[1]));
                    try {
                        instances.push(new Cesium.GeometryInstance({
                            geometry: new Cesium.PolygonGeometry({
                                polygonHierarchy: new Cesium.PolygonHierarchy(positions),
                                vertexFormat: Cesium.PerInstanceColorAppearance.VERTEX_FORMAT
                            }),
                            attributes: {
                                color: Cesium.ColorGeometryInstanceAttribute.fromColor(
                                    color.withAlpha(alpha)
                                )
                            }
                        }));
                    } catch (e) {
                        // skip malformed quads silently
                    }
                }
            });
            return instances;
        };

        const items = this.coverageSwathEntities.get(noradId);
        const sensor_type = coverageData.sensor_type || 'optical';
        const is_sar = sensor_type === 'SAR';

        const addGroundPrimitive = (instances) => {
            if (!instances.length) return;
            const prim = this.viewer.scene.groundPrimitives.add(
                new Cesium.GroundPrimitive({
                    geometryInstances: instances,
                    appearance: new Cesium.PerInstanceColorAppearance({
                        flat: true,
                        translucent: true
                    }),
                    classificationType: Cesium.ClassificationType.TERRAIN,
                    asynchronous: false
                })
            );
            items.push({ isPrimitive: true, primitive: prim });
        };

        // Day coverage (cyan)
        if (coverageData.day_polygons && coverageData.day_polygons.length > 0)
            addGroundPrimitive(buildQuadInstances(coverageData.day_polygons, Cesium.Color.CYAN, 0.35));

        // Night coverage (dark blue) — optical sensors only
        if (!is_sar && coverageData.night_polygons && coverageData.night_polygons.length > 0)
            addGroundPrimitive(buildQuadInstances(coverageData.night_polygons, Cesium.Color.DARKBLUE, 0.3));

        // Ground track — entity polylines with clampToGround (separate rendering path, no depth issue)
        if (coverageData.ground_track && coverageData.ground_track.length > 1) {
            const validTrack = coverageData.ground_track.filter(isValidCoord);
            const segments = [];
            let seg = [validTrack[0]];
            for (let i = 1; i < validTrack.length; i++) {
                const prevLon = seg[seg.length - 1][0];
                const currLon = validTrack[i][0];
                if (Math.abs(currLon - prevLon) > 180) {
                    if (seg.length > 1) segments.push(seg);
                    seg = [validTrack[i]];
                } else {
                    seg.push(validTrack[i]);
                }
            }
            if (seg.length > 1) segments.push(seg);

            segments.forEach((segment) => {
                const positions = segment.map(c => Cesium.Cartesian3.fromDegrees(c[0], c[1]));
                const entity = this.viewer.entities.add({
                    polyline: {
                        positions,
                        width: 2,
                        material: Cesium.Color.YELLOW.withAlpha(0.7),
                        clampToGround: true
                    }
                });
                items.push({ isPrimitive: false, entity });
            });
        }

        console.log(`✅ Rendered coverage swath: ${items.length} scene items`);
    }

    clearCoverageSwath(noradId) {
        const clearItems = (items) => {
            if (!items) return;
            items.forEach(item => {
                if (item.isPrimitive) {
                    this.viewer.scene.groundPrimitives.remove(item.primitive);
                } else {
                    this.viewer.entities.remove(item.entity);
                }
            });
        };

        if (noradId) {
            clearItems(this.coverageSwathEntities.get(noradId));
            this.coverageSwathEntities.delete(noradId);
        } else {
            this.coverageSwathEntities.forEach(items => clearItems(items));
            this.coverageSwathEntities.clear();
        }
    }

    // =========================================================================
    // ANIMATED GROUND SWATH (Current Coverage Area)
    // =========================================================================

    toggleGroundSwath() {
        this.showGroundSwath = !this.showGroundSwath;
        const btn = document.getElementById('groundSwathBtn');

        if (this.showGroundSwath) {
            btn.classList.add('active');
            if (this.selectedSatellite) {
                this.startGroundSwathAnimation(this.selectedSatellite);
            }
        } else {
            btn.classList.remove('active');
            this.stopGroundSwathAnimation();
        }
    }

    startGroundSwathAnimation(noradId) {
        // Clear any existing animation
        this.stopGroundSwathAnimation();

        // Update immediately
        this.updateGroundSwath(noradId);

        // Update every 5 seconds
        this.groundSwathUpdateInterval = setInterval(() => {
            this.updateGroundSwath(noradId);
        }, 5000);

        console.log(`🎬 Started ground swath animation for satellite ${noradId}`);
    }

    async updateGroundSwath(noradId) {
        try {
            const response = await fetchWithRetry(`/api/satellite/${noradId}/ground-swath`);
            const data = await response.json();

            if (data.success && data.ground_swath) {
                this.renderGroundSwath(data.ground_swath);
            }
        } catch (error) {
            console.error('Error updating ground swath:', error);
        }
    }

    renderGroundSwath(swathData) {
        // Remove existing ground swath
        if (this.groundSwathEntity) {
            this.viewer.entities.remove(this.groundSwathEntity);
            this.groundSwathEntity = null;
        }

        const polygon = swathData.polygon;
        if (!polygon || !polygon.coordinates || polygon.coordinates.length === 0) {
            return;
        }

        const positions = [];
        polygon.coordinates[0].forEach(coord => {
            positions.push(Cesium.Cartesian3.fromDegrees(coord[0], coord[1], 0));
        });

        // Color based on day/night
        const color = swathData.daytime ? Cesium.Color.CYAN : Cesium.Color.DARKBLUE;
        const alpha = swathData.daytime ? 0.3 : 0.2;

        this.groundSwathEntity = this.viewer.entities.add({
            name: `Current Ground Swath ${swathData.norad_id}`,
            polygon: {
                hierarchy: new Cesium.PolygonHierarchy(positions),
                material: color.withAlpha(alpha),
                outline: true,
                outlineColor: color.withAlpha(0.8),
                outlineWidth: 2,
                height: 0,
                classificationType: Cesium.ClassificationType.TERRAIN
            }
        });
    }

    stopGroundSwathAnimation() {
        if (this.groundSwathUpdateInterval) {
            clearInterval(this.groundSwathUpdateInterval);
            this.groundSwathUpdateInterval = null;
        }

        if (this.groundSwathEntity) {
            this.viewer.entities.remove(this.groundSwathEntity);
            this.groundSwathEntity = null;
        }
    }



    handleImageryAction(noradId, linkIndex) {
        const satellite = this.satellites.get(noradId);
        if (!satellite) return;

        const links = this.getImageryLinks(noradId, satellite.name);
        const link = links[linkIndex];

        if (link && link.action) {
            link.action();
        }
    }

    async loadLandsatData(noradId, landsatNum) {
        try {
            this.showLoadingIndicator('Loading Landsat imagery...');

            // Get current satellite position
            const satellite = this.satellites.get(noradId);
            if (!satellite) return;

            // Use NASA's Landsat Look API for recentimagery
            const response = await fetchWithRetry(`/api/satellite/${noradId}/imagery/landsat`);
            const data = await response.json();

            if (data.success && data.imagery_urls) {
                this.displayImageryModal('Landsat Imagery', data.imagery_urls, satellite);
            } else {
                // Fallback to NASA Worldview with satellite's current location
                const worldviewUrl = `https://worldview.earthdata.nasa.gov/?v=${satellite.longitude - 5},${satellite.latitude - 5},${satellite.longitude + 5},${satellite.latitude + 5}&l=Landsat_WELD_CorrectedReflectance_TrueColor_Global_Annual&t=2024-01-01`;
                window.open(worldviewUrl, '_blank');
            }
        } catch (error) {
            console.error('Error loading Landsat data:', error);
            this.showError('Failed to load Landsat imagery');
        } finally {
            this.hideLoadingIndicator();
        }
    }

    async loadSentinelData(noradId, sentinelType) {
        try {
            this.showLoadingIndicator('Loading Sentinel imagery...');

            const satellite = this.satellites.get(noradId);
            if (!satellite) return;

            const response = await fetchWithRetry(`/api/satellite/${noradId}/imagery/sentinel`);
            const data = await response.json();

            if (data.success && data.imagery_urls) {
                this.displayImageryModal('Sentinel Imagery', data.imagery_urls, satellite);
            } else {
                // Fallback to Copernicus Browser with satellite's current location
                const browserUrl = `https://browser.dataspace.copernicus.eu/?zoom=10&lat=${satellite.latitude}&lng=${satellite.longitude}&themeId=DEFAULT-THEME&datasetId=S${sentinelType.charAt(0)}_L2A&fromTime=2024-01-01T00%3A00%3A00.000Z&toTime=2024-12-31T23%3A59%3A59.999Z`;
                window.open(browserUrl, '_blank');
            }
        } catch (error) {
            console.error('Error loading Sentinel data:', error);
            this.showError('Failed to load Sentinel imagery');
        } finally {
            this.hideLoadingIndicator();
        }
    }

    async loadModisData(noradId, satellite) {
        try {
            this.showLoadingIndicator('Loading MODIS imagery...');

            const satelliteData = this.satellites.get(noradId);
            if (!satelliteData) return;

            const response = await fetchWithRetry(`/api/satellite/${noradId}/imagery/modis`);
            const data = await response.json();

            if (data.success && data.imagery_urls) {
                this.displayImageryModal('MODIS Imagery', data.imagery_urls, satelliteData);
            } else {
                // Fallback to NASA Worldview
                const worldviewUrl = `https://worldview.earthdata.nasa.gov/?v=${satelliteData.longitude - 10},${satelliteData.latitude - 10},${satelliteData.longitude + 10},${satelliteData.latitude + 10}&l=MODIS_${satellite.name}_CorrectedReflectance_TrueColor&t=2024-01-01`;
                window.open(worldviewUrl, '_blank');
            }
        } catch (error) {
            console.error('Error loading MODIS data:', error);
            this.showError('Failed to load MODIS imagery');
        } finally {
            this.hideLoadingIndicator();
        }
    }

    async loadNoaaData(noradId, satelliteNum) {
        try {
            this.showLoadingIndicator('Loading NOAA weather imagery...');

            const satellite = this.satellites.get(noradId);
            if (!satellite) return;

            const response = await fetchWithRetry(`/api/satellite/${noradId}/imagery/noaa`);
            const data = await response.json();

            if (data.success && data.imagery_urls) {
                this.displayImageryModal('NOAA Weather Imagery', data.imagery_urls, satellite);
            } else {
                // Fallback to NOAA STAR
                const noaaUrl = `https://www.star.nesdis.noaa.gov/GOES/fulldisk_band.php?sat=G${satelliteNum}&band=GEOCOLOR&length=12`;
                window.open(noaaUrl, '_blank');
            }
        } catch (error) {
            console.error('Error loading NOAA data:', error);
            this.showError('Failed to load NOAA imagery');
        } finally {
            this.hideLoadingIndicator();
        }
    }

    async loadResursData(noradId, resursNum) {
        try {
            this.showLoadingIndicator('Loading RESURS imagery...');

            const satellite = this.satellites.get(noradId);
            if (!satellite) return;

            const response = await fetchWithRetry(`/api/satellite/${noradId}/imagery/resurs`);
            const data = await response.json();

            if (data.success && data.imagery_urls) {
                this.displayImageryModal('RESURS Imagery', data.imagery_urls, satellite);
            } else {
                // Fallback to RESURS data portal
                const resursUrl = `https://gptl.ru/en/catalog?satellites=resurs-p${resursNum}&bbox=${satellite.longitude - 2},${satellite.latitude - 2},${satellite.longitude + 2},${satellite.latitude + 2}`;
                window.open(resursUrl, '_blank');
            }
        } catch (error) {
            console.error('Error loading RESURS data:', error);
            this.showError('Failed to load RESURS imagery');
        } finally {
            this.hideLoadingIndicator();
        }
    }

    displayImageryModal(title, imageryUrls, satellite) {
        // Create modal for displaying satellite imagery
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content bg-dark">
                    <div class="modal-header">
                        <h5 class="modal-title text-info">${title} - ${satellite.name}</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <strong>Current Position:</strong><br>
                                <small>Lat: ${satellite.latitude.toFixed(4)}°, Lon: ${satellite.longitude.toFixed(4)}°</small><br>
                                <small>Alt: ${satellite.altitude.toFixed(1)} km</small>
                            </div>
                            <div class="col-md-6 mb-3">
                                <strong>Imagery Sources:</strong><br>
                                <small>Updated: ${new Date().toLocaleString()}</small>
                            </div>
                        </div>
                        <div class="imagery-gallery">
                            ${imageryUrls.map((url, index) => `
                                <div class="mb-3">
                                    <h6>Image ${index + 1}</h6>
                                    <img src="${url}" class="img-fluid rounded" alt="Satellite imagery" style="max-height: 300px;">
                                    <br><small class="text-muted">${url}</small>
                                </div>
                            `).join('')}
                        </div>
                        ${imageryUrls.length === 0 ? '<p class="text-muted">No recent imagery available. Try external links.</p>' : ''}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();

        // Remove modal when hidden
        modal.addEventListener('hidden.bs.modal', () => {
            document.body.removeChild(modal);
        });
    }



    toggleTracking() {
        this.trackingMode = !this.trackingMode;
        const btn = document.getElementById('trackingBtn');

        if (this.trackingMode) {
            btn.classList.add('active');
            if (this.selectedSatellite) {
                this.trackSatellite(this.selectedSatellite);
            }
        } else {
            btn.classList.remove('active');
            // Stop tracking but keep satellite selected
            if (this.satelliteTrackingInterval) {
                clearInterval(this.satelliteTrackingInterval);
                this.satelliteTrackingInterval = null;
            }
        }
    }

    isEarthObservationSatellite(noradId) {
        // First check if this satellite is in our FOV database (the 17 satellites from Excel)
        const fovSatellites = [
            39634, 40697, 42063, 41335, 43437, 42969, 46984, // Sentinel series
            39084, 49260, // Landsat series
            25994, 27424, 37849, 43013, // Terra, Aqua, Suomi NPP, NOAA-20
            32060, 35946, 40115 // WorldView series
        ];

        if (fovSatellites.includes(noradId)) {
            console.log(`✅ Found EO satellite ${noradId} in FOV database`);
            return true;
        }

        // Check if this satellite is in our Earth observation database
        const satellite = this.satellites.get(noradId);
        if (!satellite) return false;

        const name = satellite.name.toUpperCase();
        const category = satellite.category?.toLowerCase() || '';

        // Check category first
        if (category === 'earth_observation') return true;

        // Check comprehensive Earth observation keywords
        const eoKeywords = [
            'LANDSAT', 'SENTINEL', 'SPOT', 'WORLDVIEW', 'QUICKBIRD', 'GEOEYE',
            'TERRA', 'AQUA', 'MODIS', 'NOAA', 'GOES', 'HIMAWARI', 'METEOSAT',
            'KOMPSAT', 'ALOS', 'RADARSAT', 'COSMO-SKYMED', 'TERRASAR',
            'ENVISAT', 'ERS-', 'CBERS', 'RESOURCESAT', 'CARTOSAT', 'RISAT',
            'OCEANSAT', 'SCATSAT', 'SARAL', 'JASON', 'TOPEX', 'POSEIDON',
            'SMAP', 'YAOGAN', 'GAOFEN', 'ZIYUAN', 'TIANHUI', 'JILIN',
            'SUPERVIEW', 'PLANETSCOPE', 'RAPIDEYE', 'SKYSAT', 'DOVE',
            'FLOCK', 'PLANET', 'BLACKSKY', 'ICEYE', 'CAPELLA'
        ];

        return eoKeywords.some(keyword => name.includes(keyword));
    }

    isISS(satellite) {
        return satellite.name.toLowerCase().includes('iss') ||
            satellite.name.toLowerCase().includes('international space station');
    }

    getImageryLinks(noradId, satelliteName) {
        const name = satelliteName.toUpperCase();
        const links = [];

        // Get current satellite position for location-specific links
        const satellite = this.satellites.get(noradId);
        const lat = satellite ? satellite.latitude.toFixed(4) : '0';
        const lon = satellite ? satellite.longitude.toFixed(4) : '0';
        const bbox = satellite ? `${(satellite.longitude - 2).toFixed(4)},${(satellite.latitude - 2).toFixed(4)},${(satellite.longitude + 2).toFixed(4)},${(satellite.latitude + 2).toFixed(4)}` : '-2,-2,2,2';

        // Landsat satellites (USGS Earth Explorer - Free)
        if (name.includes('LANDSAT')) {
            const landsatNum = name.match(/LANDSAT[- ]?(\d+)/i)?.[1] || '8';

            links.push({
                name: 'Load Landsat Data',
                url: '#',
                icon: 'fas fa-download',
                type: 'direct',
                description: 'Load latest Landsat imagery directly',
                action: () => this.loadLandsatData(noradId, landsatNum)
            });
            links.push({
                name: 'USGS Earth Explorer (Location)',
                url: `https://earthexplorer.usgs.gov/?lng=${lon}&lat=${lat}&zoom=8`,
                icon: 'fas fa-globe-americas',
                type: 'free',
                description: `Search Landsat ${landsatNum} at current position`
            });
            links.push({
                name: 'NASA Worldview (Focused)',
                url: `https://worldview.earthdata.nasa.gov/?v=${satellite ? (satellite.longitude - 5).toFixed(2) : '-5'},${satellite ? (satellite.latitude - 5).toFixed(2) : '-5'},${satellite ? (satellite.longitude + 5).toFixed(2) : '5'},${satellite ? (satellite.latitude + 5).toFixed(2) : '5'}&l=Landsat_WELD_CorrectedReflectance_TrueColor_Global_Annual&t=2024-01-01`,
                icon: 'fas fa-satellite-dish',
                type: 'free',
                description: 'View area where satellite is currently located'
            });
        }

        // Sentinel satellites (ESA Copernicus - Free)
        if (name.includes('SENTINEL')) {
            const sentinelType = name.match(/SENTINEL[- ]?(\d+[A-Z]?)/i)?.[1] || '2A';

            links.push({
                name: 'Load Sentinel Data',
                url: '#',
                icon: 'fas fa-download',
                type: 'direct',
                description: 'Load latest Sentinel imagery directly',
                action: () => this.loadSentinelData(noradId, sentinelType)
            });
            links.push({
                name: 'Copernicus Browser (Location)',
                url: `https://browser.dataspace.copernicus.eu/?zoom=10&lat=${lat}&lng=${lon}&themeId=DEFAULT-THEME&datasetId=S${sentinelType.charAt(0)}_L2A&fromTime=2024-01-01T00%3A00%3A00.000Z&toTime=2024-12-31T23%3A59%3A59.999Z`,
                icon: 'fas fa-satellite',
                type: 'free',
                description: `Browse Sentinel-${sentinelType} imagery at current position`
            });
            links.push({
                name: 'Sentinel Hub EO Browser (Focused)',
                url: `https://apps.sentinel-hub.com/eo-browser/?zoom=10&lat=${lat}&lng=${lon}&themeId=DEFAULT-THEME&datasetId=S2_L2A&fromTime=2024-01-01T00%3A00%3A00.000Z&toTime=2024-12-31T23%3A59%3A59.999Z`,
                icon: 'fas fa-eye',
                type: 'free',
                description: `Interactive viewer focused on satellite's current area`
            });
        }

        // MODIS (Terra/Aqua) - Free NASA data
        if (name.includes('TERRA') || name.includes('AQUA') || name.includes('MODIS')) {
            const satelliteName = name.includes('TERRA') ? 'Terra' : 'Aqua';

            links.push({
                name: 'Load MODIS Data',
                url: '#',
                icon: 'fas fa-download',
                type: 'direct',
                description: `Load latest ${satelliteName} MODIS imagery`,
                action: () => this.loadModisData(noradId, satelliteName)
            });
            links.push({
                name: 'NASA Worldview (Current Area)',
                url: `https://worldview.earthdata.nasa.gov/?v=${satellite ? (satellite.longitude - 10).toFixed(2) : '-10'},${satellite ? (satellite.latitude - 10).toFixed(2) : '-10'},${satellite ? (satellite.longitude + 10).toFixed(2) : '10'},${satellite ? (satellite.latitude + 10).toFixed(2) : '10'}&l=MODIS_${satelliteName}_CorrectedReflectance_TrueColor&t=2024-01-01`,
                icon: 'fas fa-rocket',
                type: 'free',
                description: `NASA ${satelliteName} MODIS imagery at current location`
            });
            links.push({
                name: 'MODIS Browse (Location)',
                url: `https://modis.gsfc.nasa.gov/cgi-bin/gallery.cgi?platform=${satelliteName}&lat=${lat}&lon=${lon}&radius=500`,
                icon: 'fas fa-database',
                type: 'free',
                description: `${satelliteName} MODIS images near current position`
            });
        }

        // NOAA satellites - Free weather imagery
        if (name.includes('NOAA') || name.includes('GOES')) {
            const satelliteNum = name.match(/(?:NOAA|GOES)[- ]?(\d+)/i)?.[1] || '16';

            links.push({
                name: 'Load Weather Data',
                url: '#',
                icon: 'fas fa-download',
                type: 'direct',
                description: 'Load latest weather imagery',
                action: () => this.loadNoaaData(noradId, satelliteNum)
            });

            if (name.includes('GOES')) {
                links.push({
                    name: 'GOES Image Viewer (Current)',
                    url: `https://www.star.nesdis.noaa.gov/GOES/fulldisk_band.php?sat=G${satelliteNum}&band=GEOCOLOR&length=12`,
                    icon: 'fas fa-satellite-dish',
                    type: 'free',
                    description: `Latest GOES-${satelliteNum} full disk imagery`
                });
                links.push({
                    name: 'GOES Sector View',
                    url: `https://cdn.star.nesdis.noaa.gov/GOES${satelliteNum}/ABI/SECTOR/`,
                    icon: 'fas fa-map',
                    type: 'free',
                    description: `GOES-${satelliteNum} sector imagery`
                });
            } else {
                links.push({
                    name: 'NOAA CLASS (Location)',
                    url: `https://www.avl.class.noaa.gov/saa/products/search?spatial_type=bbox&spatial_bbox=${bbox}&datatype_family=AVHRR&platform=NOAA-${satelliteNum}`,
                    icon: 'fas fa-cloud',
                    type: 'free',
                    description: `NOAA-${satelliteNum} data near current position`
                });
            }
        }

        // RESURS and Russian satellites
        if (name.includes('RESURS')) {
            const resursNum = name.match(/RESURS[- ]?P?(\d+)/i)?.[1] || '4';

            links.push({
                name: 'Load RESURS Data',
                url: '#',
                icon: 'fas fa-download',
                type: 'direct',
                description: 'Load available RESURS imagery',
                action: () => this.loadResursData(noradId, resursNum)
            });
            links.push({
                name: 'RESURS Data Portal (Location)',
                url: `https://gptl.ru/en/catalog?satellites=resurs-p${resursNum}&bbox=${bbox}`,
                icon: 'fas fa-satellite',
                type: 'free',
                description: `RESURS-P${resursNum} data at current position`
            });
            links.push({
                name: 'Russian Space Agency (Location)',
                url: `https://www.roscosmos.ru/en/`,
                icon: 'fas fa-rocket',
                type: 'free',
                description: `Russian satellite mission data`
            });
        }

        // WorldView satellites (DigitalGlobe/Maxar - Paid)
        if (name.includes('WORLDVIEW')) {
            const wvNum = name.match(/WORLDVIEW[- ]?(\d+)/i)?.[1] || '2';
            links.push({
                name: 'Maxar SecureWatch (Location)',
                url: `https://securewatch.digitalglobe.com/myDigitalGlobe_viewer/main.html?lat=${lat}&lng=${lon}&zoom=10`,
                icon: 'fas fa-lock',
                type: 'paid',
                description: `WorldView-${wvNum} high-res imagery at current area`
            });
            links.push({
                name: 'Google Earth (Location)',
                url: `https://earth.google.com/web/@${lat},${lon},15000a,35y,0t,0r`,
                icon: 'fab fa-google',
                type: 'free',
                description: 'View area in Google Earth'
            });
        }

        // SPOT satellites - Paid
        if (name.includes('SPOT')) {
            const spotNum = name.match(/SPOT[- ]?(\d+)/i)?.[1] || '7';
            links.push({
                name: 'Airbus Intelligence (Location)',
                url: `https://www.intelligence-airbusds.com/optical/spot/`,
                icon: 'fas fa-plane',
                type: 'paid',
                description: `SPOT-${spotNum} imagery from Airbus`
            });
            links.push({
                name: 'OneAtlas (Location)',
                url: `https://oneatlas.airbus.com/`,
                icon: 'fas fa-globe-europe',
                type: 'paid',
                description: 'Airbus satellite imagery platform'
            });
        }

        // Planet Labs satellites - Paid
        if (name.includes('DOVE') || name.includes('SKYSAT') || name.includes('PLANET')) {
            links.push({
                name: 'Planet Explorer (Location)',
                url: `https://www.planet.com/explorer/#/zoom/${satellite ? Math.round(Math.log2(111319.5 / 1000)) : 8}/${lat}/${lon}`,
                icon: 'fas fa-globe',
                type: 'paid',
                description: 'Planet Labs imagery at current position'
            });
            links.push({
                name: 'Planet Imagery API',
                url: 'https://developers.planet.com/',
                icon: 'fas fa-code',
                type: 'paid',
                description: 'Planet Labs developer platform'
            });
        }

        // RADARSAT - Mixed (some free, some paid)
        if (name.includes('RADARSAT')) {
            const rsNum = name.match(/RADARSAT[- ]?(\d+)/i)?.[1] || '2';
            links.push({
                name: 'EODMS (Location)',
                url: `https://www.eodms-sgdot.nrcan-rncan.gc.ca/index-en.html`,
                icon: 'fas fa-leaf',
                type: 'free',
                description: `Canadian EO data near lat:${lat}, lon:${lon}`
            });
            links.push({
                name: 'MDA Geospatial (Location)',
                url: `https://mdacorporation.com/geospatial/international/satellites/radarsat-${rsNum}`,
                icon: 'fas fa-radar',
                type: 'paid',
                description: `RADARSAT-${rsNum} commercial imagery`
            });
        }

        // Add generic location-specific sources for any Earth observation satellite
        if (links.length === 0 || !links.some(link => link.type === 'free')) {
            links.push({
                name: 'NASA Worldview (Location)',
                url: `https://worldview.earthdata.nasa.gov/?v=${satellite ? (satellite.longitude - 5).toFixed(2) : '-5'},${satellite ? (satellite.latitude - 5).toFixed(2) : '-5'},${satellite ? (satellite.longitude + 5).toFixed(2) : '5'},${satellite ? (satellite.latitude + 5).toFixed(2) : '5'}&l=MODIS_Aqua_CorrectedReflectance_TrueColor&t=2024-01-01`,
                icon: 'fas fa-rocket',
                type: 'free',
                description: 'NASA satellite imagery at current area'
            });
            links.push({
                name: 'Google Earth (Location)',
                url: `https://earth.google.com/web/@${lat},${lon},15000a,35y,0t,0r`,
                icon: 'fab fa-google',
                type: 'free',
                description: 'View area in Google Earth'
            });
            links.push({
                name: 'EO Browser (Location)',
                url: `https://apps.sentinel-hub.com/eo-browser/?zoom=10&lat=${lat}&lng=${lon}&themeId=DEFAULT-THEME&datasetId=S2_L2A&fromTime=2024-01-01T00%3A00%3A00.000Z&toTime=2024-12-31T23%3A59%3A59.999Z`,
                icon: 'fas fa-satellite',
                type: 'free',
                description: 'Browse Earth observation data at current position'
            });
        }

        return links.slice(0, 6); // Limit to 6 links to avoid clutter
    }

    showError(message) {
        console.error('Satellite Tracker Error:', message);
        // Show error in UI if needed
        const statusElement = document.getElementById('connectionStatus');
        if (statusElement) {
            statusElement.textContent = 'Error';
            statusElement.className = 'badge bg-danger ms-auto';
            statusElement.title = message;
        }
    }

    addUserLocationMarker() {
        // Remove existing user location marker
        if (this.userLocationMarker) {
            this.viewer.entities.remove(this.userLocationMarker);
        }

        // Add blue dot for user location like Google Maps
        this.userLocationMarker = this.viewer.entities.add({
            id: 'user_location',
            name: 'Your Location',
            position: Cesium.Cartesian3.fromDegrees(
                this.userLocation.lon,
                this.userLocation.lat,
                this.userLocation.alt
            ),
            point: {
                pixelSize: 15,
                color: Cesium.Color.DODGERBLUE,
                outlineColor: Cesium.Color.WHITE,
                outlineWidth: 3,
                heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
                disableDepthTestDistance: Number.POSITIVE_INFINITY
            },
            label: {
                text: 'You are here',
                font: '12pt Arial',
                fillColor: Cesium.Color.WHITE,
                outlineColor: Cesium.Color.BLACK,
                outlineWidth: 2,
                style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                pixelOffset: new Cesium.Cartesian2(0, -40),
                show: true,
                heightReference: Cesium.HeightReference.CLAMP_TO_GROUND
            }
        });
    }

    showLoadingIndicator(message) {
        const indicator = document.getElementById('loadingOverlay');
        if (indicator) {
            indicator.style.display = 'flex';
            const messageEl = indicator.querySelector('p');
            if (messageEl) messageEl.textContent = message;
        }
    }

    hideLoadingIndicator() {
        const indicator = document.getElementById('loadingOverlay');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }

    startAutoUpdate() {
        // Auto-refresh every 5 minutes
        this.updateInterval = setInterval(() => {
            this.loadSatellites();
        }, 300000);
    }

    setUserLocation(lat, lon, alt) {
        this.userLocation = { lat, lon, alt };
        this.addUserLocationMarker();

        // Update preferences
        this.preferences.location = this.userLocation;
        this.saveUserPreferences();

        // Fly to location
        this.viewer.camera.flyTo({
            destination: Cesium.Cartesian3.fromDegrees(lon, lat, 1000000),
            duration: 2.0
        });
    }

    resetView() {
        // If user location is available, go there; otherwise go to default view
        if (this.userLocation && (this.userLocation.lat !== 0 || this.userLocation.lon !== 0)) {
            this.viewer.camera.flyTo({
                destination: Cesium.Cartesian3.fromDegrees(
                    this.userLocation.lon,
                    this.userLocation.lat,
                    50000000 // 5000km altitude for good view
                ),
                orientation: {
                    heading: 0.0,
                    pitch: -Cesium.Math.PI_OVER_TWO,
                    roll: 0.0
                },
                duration: 2.0
            });
        } else {
            // Default view
            this.viewer.camera.flyTo({
                destination: Cesium.Cartesian3.fromDegrees(0, 30, 12000000),
                orientation: {
                    heading: 0.0,
                    pitch: -Cesium.Math.PI_OVER_TWO,
                    roll: 0.0
                },
                duration: 2.0
            });
        }
    }

    async refreshData() {
        try {
            this.updateStatus('Refreshing satellite data...', false);

            const response = await fetchWithRetry('/api/refresh', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (data.success) {
                this.updateStatus(`Data refreshed! Loaded ${data.satellite_count} satellites`, false);
                // Reload satellites to update the display
                await this.loadSatellites();
            } else {
                this.updateStatus('Failed to refresh data: ' + (data.error || 'Unknown error'), true);
            }
        } catch (error) {
            console.error('Error refreshing data:', error);
            this.updateStatus('Error refreshing data: ' + error.message, true);
        }
    }

    getCurrentLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    this.setUserLocation(
                        position.coords.latitude,
                        position.coords.longitude,
                        position.coords.altitude || 0
                    );
                },
                (error) => {
                    this.showError('Could not get your location: ' + error.message);
                }
            );
        } else {
            this.showError('Geolocation is not supported');
        }
    }

    saveCoordinates() {
        const lat = parseFloat(document.getElementById('coordLatitude').value);
        const lon = parseFloat(document.getElementById('coordLongitude').value);
        const alt = parseFloat(document.getElementById('coordAltitude').value) || 0;

        if (isNaN(lat) || isNaN(lon) || lat < -90 || lat > 90 || lon < -180 || lon > 180) {
            alert('Please enter valid coordinates');
            return;
        }

        this.setUserLocation(lat, lon, alt);

        // Close modal with proper cleanup
        this.cleanupCoordinatesModal();
    }

    cleanupCoordinatesModal() {
        // Get the modal instance
        const modalElement = document.getElementById('coordinatesModal');
        const modal = bootstrap.Modal.getInstance(modalElement);

        // Hide the modal if it exists
        if (modal) {
            modal.hide();
        }

        // Wait for modal animation to complete, then cleanup
        setTimeout(() => {
            // Remove all modal backdrops
            document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
                backdrop.remove();
            });

            // Remove modal-open class from body
            document.body.classList.remove('modal-open');

            // Restore body overflow and padding
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';

            console.log('Coordinates modal cleanup completed');
        }, 300); // Wait for Bootstrap modal animation to complete
    }

    async searchLocationByName() {
        const query = document.getElementById('locationSearchInput').value.trim();
        if (!query) {
            alert('Please enter a location name');
            return;
        }

        const resultsContainer = document.getElementById('locationSearchResults');
        resultsContainer.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin"></i> Searching...</div>';

        try {
            // Use Nominatim OSM geocoding service (free, no API key required)
            const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5&addressdetails=1`);

            if (!response.ok) {
                throw new Error('Geocoding service unavailable');
            }

            const data = await response.json();

            if (data && data.length > 0) {
                resultsContainer.innerHTML = data.map((result, index) => `
                    <div class="search-result p-2 mb-2" data-lat="${result.lat}" data-lon="${result.lon}" style="cursor: pointer; background: rgba(100, 181, 246, 0.1); border: 1px solid rgba(100, 181, 246, 0.2); border-radius: 6px; transition: all 0.3s ease;">
                        <strong class="text-info">${result.display_name}</strong><br>
                        <small class="text-muted">${parseFloat(result.lat).toFixed(4)}, ${parseFloat(result.lon).toFixed(4)}</small>
                        <small class="text-success d-block">Type: ${result.type || 'Location'}</small>
                    </div>
                `).join('');

                // Add hover effects
                resultsContainer.querySelectorAll('.search-result').forEach(item => {
                    item.addEventListener('mouseenter', () => {
                        item.style.background = 'rgba(100, 181, 246, 0.2)';
                        item.style.transform = 'translateX(4px)';
                    });
                    item.addEventListener('mouseleave', () => {
                        item.style.background = 'rgba(100, 181, 246, 0.1)';
                        item.style.transform = 'translateX(0)';
                    });
                });

                // Add click handlers
                resultsContainer.querySelectorAll('.search-result').forEach(item => {
                    item.addEventListener('click', () => {
                        const lat = parseFloat(item.dataset.lat);
                        const lon = parseFloat(item.dataset.lon);

                        // Close modal first, then update location
                        this.cleanupSearchLocationModal();

                        // Set location with a small delay to ensure modal is fully closed
                        setTimeout(() => {
                            this.setUserLocation(lat, lon, 0);
                        }, 100);
                    });
                });
            } else {
                resultsContainer.innerHTML = '<div class="text-muted p-2">No locations found. Try searching for a specific city, town, or landmark.</div>';
            }
        } catch (error) {
            console.error('Geocoding error:', error);
            resultsContainer.innerHTML = '<div class="text-danger p-2">Search failed. Please check your internet connection and try again.</div>';
        }
    }

    cleanupSearchLocationModal() {
        // Get the modal instance
        const modalElement = document.getElementById('searchLocationModal');
        const modal = bootstrap.Modal.getInstance(modalElement);

        // Hide the modal if it exists
        if (modal) {
            modal.hide();
        }

        // Wait for modal animation to complete, then cleanup
        setTimeout(() => {
            // Remove all modal backdrops
            document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
                backdrop.remove();
            });

            // Remove modal-open class from body
            document.body.classList.remove('modal-open');

            // Restore body overflow and padding
            document.body.style.overflow = '';
            document.body.style.paddingRight = '';

            // Clear search results
            const resultsContainer = document.getElementById('locationSearchResults');
            if (resultsContainer) {
                resultsContainer.innerHTML = '';
            }

            // Clear search input
            const searchInput = document.getElementById('locationSearchInput');
            if (searchInput) {
                searchInput.value = '';
            }

            console.log('Search location modal cleanup completed');
        }, 300); // Wait for Bootstrap modal animation to complete
    }

    enableGlobeSelection() {
        alert('Click anywhere on the globe to set your location');

        // Enable globe click selection
        this.globeSelectionEnabled = true;

        // Change cursor to crosshair
        document.getElementById('cesiumContainer').style.cursor = 'crosshair';

        // Add temporary click handler
        this.globeClickHandler = (event) => {
            if (!this.globeSelectionEnabled) return;

            const pickedPosition = this.viewer.camera.pickEllipsoid(event.position, this.viewer.scene.globe.ellipsoid);
            if (pickedPosition) {
                const cartographic = Cesium.Cartographic.fromCartesian(pickedPosition);
                const lat = Cesium.Math.toDegrees(cartographic.latitude);
                const lon = Cesium.Math.toDegrees(cartographic.longitude);

                this.setUserLocation(lat, lon, 0);
                this.disableGlobeSelection();

                // Ensure no modal overlays remain
                const backdrop = document.querySelector('.modal-backdrop');
                if (backdrop) {
                    backdrop.remove();
                }

                // Restore body overflow
                document.body.style.overflow = '';
                document.body.classList.remove('modal-open');
            }
        };

        this.viewer.cesiumWidget.screenSpaceEventHandler.setInputAction(
            this.globeClickHandler,
            Cesium.ScreenSpaceEventType.LEFT_CLICK
        );
    }

    disableGlobeSelection() {
        this.globeSelectionEnabled = false;
        document.getElementById('cesiumContainer').style.cursor = 'default';

        // Remove the temporary click handler and restore satellite click handler
        this.viewer.cesiumWidget.screenSpaceEventHandler.removeInputAction(Cesium.ScreenSpaceEventType.LEFT_CLICK);
        this.viewer.cesiumWidget.screenSpaceEventHandler.setInputAction(
            this.onEntityClick.bind(this),
            Cesium.ScreenSpaceEventType.LEFT_CLICK
        );
    }

    switchToSatelliteMode() {
        if (this.currentMode === 'satellites') return;

        console.log('🛰️ Switching to satellite mode');
        this.currentMode = 'satellites';

        // Update UI
        document.getElementById('satelliteModeBtn').classList.add('active');
        document.getElementById('airplaneModeBtn').classList.remove('active');
        document.getElementById('trackingMode').innerHTML = '<i class="fas fa-satellite me-1"></i>Satellite Mode';
        document.getElementById('countLabel').textContent = 'satellites';
        document.getElementById('satelliteSearch').placeholder = 'Search satellites...';

        // Clear airplane entities and data
        this.clearAirplaneEntities();
        this.selectedAirplane = null;

        // Close any open details panels
        if (typeof window.closeDetailsPanel === 'function') {
            window.closeDetailsPanel();
        }

        // Stop any airplane-related updates
        this.stopRealTimeDetailsUpdates();

        // Load and render satellites
        this.loadSatellites();
    }

    switchToAirplaneMode() {
        if (this.currentMode === 'airplanes') return;

        console.log('✈️ Switching to airplane mode');
        this.currentMode = 'airplanes';

        // Update UI
        document.getElementById('airplaneModeBtn').classList.add('active');
        document.getElementById('satelliteModeBtn').classList.remove('active');
        document.getElementById('trackingMode').innerHTML = '<i class="fas fa-plane me-1"></i>Airplane Mode';
        document.getElementById('countLabel').textContent = 'airplanes';
        document.getElementById('satelliteSearch').placeholder = 'Search airplanes...';

        // Clear satellite entities and data
        this.clearSatelliteEntities();
        this.selectedSatellite = null;

        // Close any open details panels
        if (typeof window.closeDetailsPanel === 'function') {
            window.closeDetailsPanel();
        }

        // Stop any satellite-related updates and tracking
        this.stopRealTimeDetailsUpdates();
        if (this.satelliteTrackingInterval) {
            clearInterval(this.satelliteTrackingInterval);
            this.satelliteTrackingInterval = null;
        }

        // Clear satellite visualizations
        this.clearNadirLine();
        this.clearSelectedOrbit();
        this.clearSelectedGroundTrack();

        // Initialize airplane viewer if not already done
        if (!this.airplaneViewer) {
            if (typeof AirplaneViewer === 'undefined') {
                console.error('AirplaneViewer not loaded yet, retrying...');
                setTimeout(() => this.switchToAirplaneMode(), 100);
                return;
            }
            this.airplaneViewer = new AirplaneViewer(this.viewer);
        }

        // Load and render airplanes
        this.loadAirplanes();
    }

    clearSatelliteEntities() {
        this.satelliteEntities.forEach(entity => {
            this.viewer.entities.remove(entity);
        });
        this.satelliteEntities.clear();
    }

    renderAirplanes() {
        if (!this.viewer || !this.viewer.entities) {
            console.warn('❌ Viewer not ready for airplane rendering');
            return;
        }

        console.log(`✈️ Rendering ${this.airplanes.size} airplanes`);

        // Clear existing airplane entities
        this.clearAirplaneEntities();

        // Create airplane entities with better data handling
        this.airplanes.forEach((airplane, icao24) => {
            if (!airplane.latitude || !airplane.longitude || isNaN(airplane.latitude) || isNaN(airplane.longitude)) {
                console.warn(`Invalid airplane position data for ${icao24}:`, airplane);
                return;
            }

            // Ensure altitude is valid
            const altitude = airplane.altitude_meters || airplane.geo_altitude * 1000 || 10000;
            if (altitude < 0 || altitude > 50000) {
                console.warn(`Invalid altitude for airplane ${icao24}: ${altitude}m`);
                return;
            }

            const position = Cesium.Cartesian3.fromDegrees(
                airplane.longitude,
                airplane.latitude,
                altitude
            );

            // Determine airplane color based on status
            let color = Cesium.Color.ORANGE; // Default flying color
            if (airplane.on_ground) {
                color = Cesium.Color.GRAY; // Ground color
            } else if (airplane.velocity > 200) {
                color = Cesium.Color.LIME; // High speed
            } else if (airplane.velocity < 50) {
                color = Cesium.Color.YELLOW; // Low speed/landing
            }

            // Better callsign handling
            const displayName = airplane.callsign && airplane.callsign.trim() && airplane.callsign.trim() !== ''
                ? airplane.callsign.trim()
                : `Aircraft ${icao24.toUpperCase()}`;

            const entity = this.viewer.entities.add({
                id: `airplane_${icao24}`,
                name: displayName,
                position: position,
                point: {
                    pixelSize: airplane.on_ground ? 3 : 5,
                    color: color,
                    outlineColor: Cesium.Color.WHITE,
                    outlineWidth: 1,
                    heightReference: Cesium.HeightReference.NONE,
                    show: true,
                    disableDepthTestDistance: Number.POSITIVE_INFINITY
                },
                label: {
                    text: displayName,
                    font: '10pt Arial',
                    fillColor: color,
                    outlineColor: Cesium.Color.BLACK,
                    outlineWidth: 2,
                    style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                    pixelOffset: new Cesium.Cartesian2(0, -20),
                    show: false, // Only show when selected
                    scaleByDistance: new Cesium.NearFarScalar(1.5e5, 1.0, 1.5e6, 0.5)
                },
                airplaneData: airplane
            });

            this.airplaneEntities.set(icao24, entity);
        });

        console.log(`✈️ Created ${this.airplaneEntities.size} airplane entities`);
        this.viewer.scene.requestRender();
    }

    clearAirplaneEntities() {
        this.airplaneEntities.forEach(entity => {
            this.viewer.entities.remove(entity);
        });
        this.airplaneEntities.clear();
    }

    onAirplaneClick(event) {
        const pickedObject = this.viewer.scene.pick(event.position);

        if (Cesium.defined(pickedObject) && pickedObject.id.airplaneData) {
            const airplane = pickedObject.id.airplaneData;
            this.selectAirplane(airplane.icao24, false);
        } else {
            this.deselectAirplane();
        }
    }

    async selectAirplane(icao24, enableTracking = false) {
        console.log(`✈️ Selecting airplane: ${icao24}`);

        const airplane = this.airplanes.get(icao24);
        if (!airplane) {
            console.warn(`❌ Airplane ${icao24} not found in airplanes map`);
            return;
        }

        // Clear previous airplane selection
        if (this.selectedAirplane && this.selectedAirplane !== icao24) {
            this.clearAirplaneVisualizations(this.selectedAirplane);
        }

        this.selectedAirplane = icao24;

        // Update airplane selection visuals
        this.updateAirplaneSelection();

        // Focus on airplane
        this.focusOnAirplane(icao24);

        // Load detailed information directly without API call since we have the data
        this.renderAirplaneDetails(airplane);

        // Start real-time updates for airplane details
        this.startRealTimeAirplaneUpdates(icao24);

        const displayName = airplane.callsign && airplane.callsign.trim() && airplane.callsign.trim() !== ''
            ? airplane.callsign.trim()
            : `Aircraft ${icao24.toUpperCase()}`;

        console.log(`✅ Airplane ${icao24} (${displayName}) selected successfully`);
    }

    updateAirplaneSelection() {
        this.airplaneEntities.forEach((entity, icao24) => {
            const isSelected = icao24 === this.selectedAirplane;

            // Enhanced selection appearance
            entity.point.pixelSize = isSelected ? 8 : 5;
            entity.point.outlineWidth = isSelected ? 1.5 : 1;

            // Show label for selected airplane
            if (isSelected) {
                entity.label.show = true;
                entity.point.color = Cesium.Color.CYAN;
                entity.point.outlineColor = Cesium.Color.WHITE;
            } else {
                entity.label.show = false;
                const airplane = this.airplanes.get(icao24);
                if (airplane) {
                    // Restore original color based on status
                    if (airplane.on_ground) {
                        entity.point.color = Cesium.Color.GRAY;
                    } else if (airplane.velocity > 200) {
                        entity.point.color = Cesium.Color.LIME;
                    } else if (airplane.velocity < 50) {
                        entity.point.color = Cesium.Color.YELLOW;
                    } else {
                        entity.point.color = Cesium.Color.ORANGE;
                    }
                    entity.point.outlineColor = Cesium.Color.WHITE;
                }
            }
        });
    }

    focusOnAirplane(icao24) {
        const airplane = this.airplanes.get(icao24);
        if (!airplane || !airplane.latitude || !airplane.longitude) return;

        // Focus on airplane position
        const destination = Cesium.Cartesian3.fromDegrees(
            airplane.longitude,
            airplane.latitude,
            (airplane.altitude_meters || 10000) + 50000 // 50km above airplane
        );

        this.viewer.camera.flyTo({
            destination: destination,
            orientation: {
                heading: 0.0,
                pitch: -Cesium.Math.PI_OVER_TWO,
                roll: 0.0
            },
            duration: 2.0
        });
    }

    renderAirplaneDetails(airplane) {
        const container = document.getElementById('satelliteDetails');
        if (!container) return;

        // Make details panel visible
        const detailsPanel = document.getElementById('satelliteDetailsPanel');
        if (detailsPanel) {
            detailsPanel.style.display = 'block';
        }

        const callsign = airplane.callsign || 'Unknown';
        const country = airplane.origin_country || 'Unknown';
        const squawk = airplane.squawk || 'N/A';

        // Format velocity
        const velocityMs = airplane.velocity || 0;
        const velocityKmh = velocityMs * 3.6;
        const velocityKnots = velocityMs * 1.94384;

        // Format altitude with multiple units
        const altitudeM = airplane.altitude_meters || airplane.geo_altitude * 1000 || 0;
        const altitudeFt = altitudeM * 3.28084;

        // Format heading/track
        const heading = airplane.true_track || airplane.heading || 0;

        // Format vertical rate
        const verticalRateMs = airplane.vertical_rate || 0;
        const verticalRateFpm = verticalRateMs * 196.85; // feet per minute

        // Determine flight status
        const status = airplane.on_ground ? 'On Ground' : 'In Flight';
        const statusColor = airplane.on_ground ? 'text-warning' : 'text-success';

        container.innerHTML = `
            <div class="satellite-header mb-3">
                <strong class="text-info">${callsign}</strong>
                <br><small class="text-muted">Live Aircraft Tracking</small>
            </div>

            <!-- Flight Information -->
            <div class="satellite-section mb-3">
                <h6 class="text-primary mb-2">
                    <i class="fas fa-plane me-2"></i>Flight Information
                </h6>
                <div class="row g-2">
                    <div class="col-6"><small class="text-muted">Callsign:</small></div>
                    <div class="col-6"><small class="text-info">${callsign}</small></div>
                    <div class="col-6"><small class="text-muted">ICAO24:</small></div>
                    <div class="col-6"><small class="text-white">${airplane.icao24.toUpperCase()}</small></div>
                    <div class="col-6"><small class="text-muted">Country:</small></div>
                    <div class="col-6"><small class="text-success">${country}</small></div>
                    <div class="col-6"><small class="text-muted">Transponder:</small></div>
                    <div class="col-6"><small class="text-warning">${squawk}</small></div>
                    <div class="col-6"><small class="text-muted">Status:</small></div>
                    <div class="col-6"><small class="${statusColor}">${status}</small></div>
                </div>
            </div>

            <!-- Position Information -->
            <div class="satellite-section mb-3">
                <h6 class="text-primary mb-2">
                    <i class="fas fa-map-marker-alt me-2"></i>Position
                </h6>
                <div class="row g-2">
                    <div class="col-6"><small class="text-muted">Latitude:</small></div>
                    <div class="col-6"><small class="text-white">${airplane.latitude.toFixed(6)}°</small></div>
                    <div class="col-6"><small class="text-muted">Longitude:</small></div>
                    <div class="col-6"><small class="text-white">${airplane.longitude.toFixed(6)}°</small></div>
                    <div class="col-6"><small class="text-muted">Altitude:</small></div>
                    <div class="col-6"><small class="text-success">${altitudeM.toFixed(0)}m (${altitudeFt.toFixed(0)}ft)</small></div>
                    <div class="col-6"><small class="text-muted">Heading:</small></div>
                    <div class="col-6"><small class="text-info">${heading.toFixed(0)}°</small></div>
                </div>
            </div>

            <!-- Flight Dynamics -->
            <div class="satellite-section mb-3">
                <h6 class="text-primary mb-2">
                    <i class="fas fa-tachometer-alt me-2"></i>Flight Dynamics
                </h6>
                <div class="row g-2">
                    <div class="col-6"><small class="text-muted">Ground Speed:</small></div>
                    <div class="col-6"><small class="text-warning">${velocityKmh.toFixed(0)} km/h</small></div>
                    <div class="col-6"><small class="text-muted">Speed (knots):</small></div>
                    <div class="col-6"><small class="text-warning">${velocityKnots.toFixed(0)} kts</small></div>
                    <div class="col-6"><small class="text-muted">Vertical Rate:</small></div>
                    <div class="col-6"><small class="text-info">${verticalRateFpm.toFixed(0)} fpm</small></div>
                    <div class="col-6"><small class="text-muted">Track:</small></div>
                    <div class="col-6"><small class="text-success">${heading.toFixed(1)}°</small></div>
                </div>
            </div>
        `;

        // Show the details panel
        if (typeof window.showDetailsPanel === 'function') {
            window.showDetailsPanel();
        }
    }

    startRealTimeAirplaneUpdates(icao24) {
        this.stopRealTimeAirplaneUpdates();

        this.realTimeAirplaneUpdateInterval = setInterval(async () => {
            if (this.selectedAirplane === icao24) {
                // Update with fresh airplane data from our local storage
                const airplane = this.airplanes.get(icao24);
                if (airplane) {
                    this.renderAirplaneDetails(airplane);
                }
            }
        }, 5000); // Update every 5 seconds
    }

    stopRealTimeAirplaneUpdates() {
        if (this.realTimeAirplaneUpdateInterval) {
            clearInterval(this.realTimeAirplaneUpdateInterval);
            this.realTimeAirplaneUpdateInterval = null;
        }
    }

    clearAirplaneVisualizations(icao24) {
        // Stop any airplane-specific tracking or updates
        this.stopRealTimeAirplaneUpdates();
    }

    deselectAirplane() {
        if (!this.selectedAirplane) return;

        console.log(`✈️ Deselecting airplane: ${this.selectedAirplane}`);

        // Clear visualizations
        this.clearAirplaneVisualizations(this.selectedAirplane);

        this.selectedAirplane = null;

        // Close details panel
        if (typeof window.closeDetailsPanel === 'function') {
            window.closeDetailsPanel();
        }

        // Update airplane selection visuals
        this.updateAirplaneSelection();
    }

    async loadAirplaneDetails(icao24) {
        try {
            const response = await fetchWithRetry(`/api/airplane/${icao24}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success && data.airplane) {
                this.renderAirplaneDetails(data.airplane);
            } else {
                console.warn('Failed to load airplane details:', data);
                document.getElementById('satelliteInfo').style.display = 'none';
            }
        } catch (error) {
            console.error('Error loading airplane details:', error);
            document.getElementById('satelliteInfo').style.display = 'none';
        }
    }

    startRealTimeAirplaneUpdates(icao24) {
        // Clear any existing interval
        this.stopRealTimeAirplaneUpdates();

        // Update airplane details every 15 seconds
        this.airplaneUpdateInterval = setInterval(async () => {
            if (this.selectedAirplane === icao24) {
                // Update with fresh data from airplanes map
                const airplane = this.airplanes.get(icao24);
                if (airplane) {
                    // Only update details if the panel is currently visible
                    const panel = document.getElementById('satelliteDetailsPanel');
                    if (panel && panel.classList.contains('show')) {
                        this.renderAirplaneDetails(airplane);
                    }
                }
            }
        }, 15000); // 15 seconds to match data refresh rate
    }

    stopRealTimeAirplaneUpdates() {
        if (this.airplaneUpdateInterval) {
            clearInterval(this.airplaneUpdateInterval);
            this.airplaneUpdateInterval = null;
        }
    }

    deselectAirplane() {
        if (this.selectedAirplane) {
            this.clearAirplaneVisualizations(this.selectedAirplane);
        }
        this.selectedAirplane = null;

        // Hide the sliding panel
        if (typeof window.closeDetailsPanel === 'function') {
            window.closeDetailsPanel();
        }

        // Update airplane selection visuals
        this.updateAirplaneSelection();

        // Stop any real-time updates
        this.stopRealTimeAirplaneUpdates();
    }

    onAirplaneClick(event) {
        const pickedObject = this.viewer.scene.pick(event.position);

        if (Cesium.defined(pickedObject) && pickedObject.id.airplaneData) {
            const airplane = pickedObject.id.airplaneData;
            this.selectAirplane(airplane.icao24, false);
        } else {
            this.deselectAirplane();
        }
    }

    focusOnAirplane(icao24) {
        const airplane = this.airplanes.get(icao24);
        if (!airplane || !airplane.latitude || !airplane.longitude) return;

        // Focus on airplane position
        const destination = Cesium.Cartesian3.fromDegrees(
            airplane.longitude,
            airplane.latitude,
            (airplane.altitude_meters || 10000) + 50000 // 50km above airplane
        );

        this.viewer.camera.flyTo({
            destination: destination,
            orientation: {
                heading: 0.0,
                pitch: -Cesium.Math.PI_OVER_TWO,
                roll: 0.0
            },
            duration: 2.0,
            easingFunction: Cesium.EasingFunction.CUBIC_IN_OUT
        });
    }

    startAutoUpdate() {
        // Synchronized with backend cache interval (10s) to prevent interpolation jumps
        this.updateInterval = setInterval(() => {
            console.log('Auto-updating positions...');
            if (this.currentMode === 'satellites') {
                this.loadSatellites();
            } else if (this.currentMode === 'airplanes') {
                this.loadAirplanes();
            }
        }, 10000); // 10 seconds - SYNCHRONIZED with backend cache interval

        // Optimized position interpolation for satellites only
        this.positionUpdateInterval = setInterval(() => {
            if (this.currentMode === 'satellites') {
                this.updateSatellitePositions();
            }
        }, 1000); // Update positions every 1 second for smooth interpolation between 10s data points
    }

    showLoadingIndicator(message = 'Loading...') {
        let indicator = document.getElementById('loadingIndicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'loadingIndicator';
            indicator.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: rgba(0, 0, 0, 0.9);
                color: white;
                padding: 20px 40px;
                border-radius: 10px;
                z-index: 10000;
                text-align: center;
                font-family: Arial, sans-serif;
                border: 2px solid #64b5f6;
            `;
            document.body.appendChild(indicator);
        }
        indicator.innerHTML = `
            <div style="margin-bottom: 10px;">
                <div style="border: 3px solid #f3f3f3; border-top: 3px solid #64b5f6; border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; margin: 0 auto;"></div>
            </div>
            <div>${message}</div>
        `;

        // Add CSS animation
        if (!document.getElementById('loadingStyles')) {
            const style = document.createElement('style');
            style.id = 'loadingStyles';
            style.textContent = '@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }';
            document.head.appendChild(style);
        }
    }

    hideLoadingIndicator() {
        const indicator = document.getElementById('loadingIndicator');
        if (indicator) {
            indicator.remove();
        }
    }

    showError(message) {
        document.getElementById('errorMessage').textContent = message;
        const toast = new bootstrap.Toast(document.getElementById('errorToast'));
        toast.show();
    }

    closeDetailsPanel() {
        const panel = document.getElementById('satelliteDetailsPanel');
        if (panel) {
            panel.classList.remove('show');
            console.log('📱 Details panel closed (satellite remains selected)');
        }

        // Keep satellite selected when closing panel - user can deselect manually if needed
    }

    isISS(satellite) {
        // Check if satellite is ISS based on name or NORAD ID
        const name = satellite.name ? satellite.name.toUpperCase() : '';
        return name.includes('ISS') || name.includes('ZARYA') || satellite.norad_id === 25544;
    }


}

// Function to show ISS live video
async function showISSVideo() {
    // Create ISS Video Modal
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'issVideoModal';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">ISS Live Video</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div id="issVideoContainer" class="ratio ratio-16x9">
                        <div class="d-flex align-items-center justify-content-center">
                            <div class="spinner-border text-primary" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                        </div>
                    </div>
                    <p id="issVideoInfo" class="text-muted mt-2 mb-0"></p>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Show modal first
    let modalInstance;
    if (typeof bootstrap !== 'undefined') {
        modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();

        // Clean up modal when hidden
        modal.addEventListener('hidden.bs.modal', function () {
            document.body.removeChild(modal);
        });
    } else {
        // Fallback if Bootstrap isn't loaded
        modal.style.display = 'block';
        modal.classList.add('show');

        // Add close functionality
        const closeBtn = modal.querySelector('.btn-close');
        closeBtn.addEventListener('click', function () {
            modal.style.display = 'none';
            document.body.removeChild(modal);
        });
    }

    // Fetch ISS live video URL from backend
    try {
        const response = await fetchWithRetry('/api/iss/live-video');
        const data = await response.json();

        const container = document.getElementById('issVideoContainer');
        const infoElement = document.getElementById('issVideoInfo');

        if (data.success && data.video_url) {
            // Load the video
            container.innerHTML = `
                <iframe id="issVideoFrame" width="100%" height="500" 
                    src="${data.video_url}" 
                    frameborder="0" 
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                    allowfullscreen>
                </iframe>
            `;

            if (infoElement && data.description) {
                infoElement.textContent = data.description;
            }
        } else {
            container.innerHTML = `
                <div class="alert alert-warning m-3">
                    <i class="fas fa-exclamation-triangle"></i>
                    ISS live video is temporarily unavailable
                </div>
            `;
        }
    } catch (error) {
        console.error('Error loading ISS video:', error);
        const container = document.getElementById('issVideoContainer');
        if (container) {
            container.innerHTML = `
                <div class="alert alert-danger m-3">
                    <i class="fas fa-exclamation-circle"></i>
                    Error loading ISS video: ${error.message}
                </div>
            `;
        }
    }
}

// Initialize satellite viewer when both DOM and Cesium are ready
document.addEventListener('DOMContentLoaded', function () {
    console.log('DOM loaded, checking for Cesium...');

    // Wait for Cesium to be loaded
    function initWhenReady() {
        if (typeof Cesium !== 'undefined') {
            console.log('Cesium loaded, initializing satellite viewer...');
            try {
                window.satelliteViewer = new SatelliteViewer();
            } catch (error) {
                console.error('Failed to initialize satellite viewer:', error);

                // Show error message in the cesium container
                const container = document.getElementById('cesiumContainer');
                if (container) {
                    container.innerHTML = `
                        <div style="display: flex; align-items: center; justify-content: center; height: 100%; background: linear-gradient(135deg, #1a1a2e 0%, #0c0c0c 100%); color: white; text-align: center;">
                            <div>
                                <i class="fas fa-exclamation-triangle" style="font-size: 48px; color: #ff6b6b; margin-bottom: 20px;"></i>
                                <h4>Failed to Load Satellite Viewer</h4>
                                <p style="color: #94a3b8; margin-bottom: 20px;">${error.message}</p>
                                <button class="btn btn-primary" onclick="location.reload()">
                                    <i class="fas fa-sync-alt"></i> Reload Page
                                </button>
                            </div>
                        </div>
                    `;
                }
            }
        } else {
            console.log('Cesium not yet loaded, waiting...');
            setTimeout(initWhenReady, 100);
        }
    }

    initWhenReady();
});