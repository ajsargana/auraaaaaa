class SatelliteViewer {
    constructor() {
        this.viewer = null;
        this.satellites = new Map();
        this.satelliteEntities = new Map();
        this.orbitEntities = new Map();
        this.selectedSatellite = null;
        this.userLocation = { lat: 0, lon: 0, alt: 0 };
        this.categories = {};
        this.activeCategoryFilter = null;
        this.showOrbits = false;
        this.showGroundTracks = false;
        this.trackingMode = true;
        this.updateInterval = null;
        this.groundTrackEntities = new Map();
        this.nadirEntities = new Map();
        this.groundCircleEntities = new Map();
        this.realTimeUpdateInterval = null;
        this.satelliteTrackingInterval = null;
        this.preferences = {};
        this.clickTimeout = null;
        this.userLocationMarker = null;
        this.cloudCoverEnabled = false;
        this.cloudProvider = null;

        // Performance optimizations for smooth movement  
        this.updateRate = 30000; // 30 seconds for better performance
        this.maxVisibleSatellites = 300; // Optimized limit for smooth rendering
        this.lodDistance = 10000000; // Level of detail distance 

        this.init();
    }

    async init() {
        try {
            console.log('Initializing SatelliteViewer...');
            await this.initializeCesium();
            this.setupEventListeners();
            await this.loadUserPreferences();
            await this.loadCategories();
            await this.loadSatellites();
            this.startAutoUpdate();
            this.setupGeolocation();
            console.log('SatelliteViewer initialization complete');
        } catch (error) {
            console.error('Error initializing SatelliteViewer:', error);
            this.showError('Failed to initialize satellite viewer: ' + error.message);
        }
    }

    async initializeCesium() {
        // Check if Cesium is loaded
        if (typeof Cesium === 'undefined') {
            throw new Error('Cesium library not loaded. Please check your internet connection.');
        }

        console.log('Initializing Cesium...');
        
        // Use default Cesium Ion token
        Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJlYWE1ZjJiOS1mOGYyLTQ1M2MtOGM2MS1kYzA2YjIxOGI4ZjciLCJpZCI6MjAzNzIsImlhdCI6MTY5NDU0Mzk5OX0.SW1LQITUzCb5gFmLNAa8aeJ7bXhDI1_3pj6_8yUAKPk';

        try {
            this.viewer = new Cesium.Viewer('cesiumContainer', {
            // Performance optimizations
            terrainProvider: new Cesium.EllipsoidTerrainProvider(),
            imageryProvider: new Cesium.OpenStreetMapImageryProvider({
                url: 'https://a.tile.openstreetmap.org/'
            }),
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
            maximumRenderTimeChange: 1000/10, // Target 10fps for smooth movement
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

            // Set initial camera position for better Earth view
            this.viewer.camera.setView({
                destination: Cesium.Cartesian3.fromDegrees(0, 0, 15000000),
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
                this.onSatelliteClick.bind(this),
                Cesium.ScreenSpaceEventType.LEFT_CLICK
            );

            // Remove loading overlay if it exists
            const loadingOverlay = document.querySelector('.loading-overlay');
            if (loadingOverlay) {
                loadingOverlay.style.display = 'none';
            }

            console.log('Cesium initialization complete');

        } catch (error) {
            console.error('Error creating Cesium viewer:', error);
            throw new Error('Failed to initialize Cesium viewer: ' + error.message);
        }
    }

    async loadUserPreferences() {
        try {
            const response = await fetch('/api/user/preferences');
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
                const updateRateElement = document.getElementById('updateRate');

                if (latElement) latElement.value = this.userLocation.lat;
                if (lonElement) lonElement.value = this.userLocation.lon;
                if (altElement) altElement.value = this.userLocation.alt;
                if (updateRateElement) updateRateElement.textContent = `${this.preferences.update_interval || 10}s`;
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
            await fetch('/api/user/preferences', {
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
        // Enhanced event listeners with performance considerations
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.refreshData();
        });

        document.getElementById('locationBtn').addEventListener('click', () => {
            const modal = new bootstrap.Modal(document.getElementById('locationModal'));
            modal.show();
        });

        document.getElementById('homeBtn').addEventListener('click', () => {
            this.resetView();
        });

        document.getElementById('trackingBtn').addEventListener('click', () => {
            this.toggleTracking();
        });

        document.getElementById('orbitsBtn').addEventListener('click', () => {
            this.toggleOrbits();
        });

        document.getElementById('groundTracksBtn').addEventListener('click', () => {
            this.toggleGroundTracks();
        });

        document.getElementById('cloudCoverBtn').addEventListener('click', () => {
            this.toggleCloudCover();
        });

        document.getElementById('saveLocationBtn').addEventListener('click', () => {
            this.saveLocation();
        });

        document.getElementById('autoLocationBtn').addEventListener('click', () => {
            this.getCurrentLocation();
        });

        // Optimized search with debouncing
        let searchTimeout;
        document.getElementById('satelliteSearch').addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.searchSatellites(e.target.value);
            }, 300);
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

    async loadCategories() {
        try {
            const response = await fetch('/api/categories');
            const data = await response.json();

            if (data.success) {
                this.categories = data.categories;
                this.renderCategories();
            } else {
                this.showError('Failed to load satellite categories');
            }
        } catch (error) {
            console.error('Error loading categories:', error);
            this.showError('Error loading satellite categories');
        }
    }

    renderCategories() {
        const container = document.getElementById('categoriesList');
        container.innerHTML = '';

        // Add "All" category with enhanced styling
        const totalCount = Object.values(this.categories).reduce((sum, cat) => sum + cat.count, 0);
        const allItem = this.createCategoryItem('all', 'All Satellites', '#64b5f6', totalCount);
        container.appendChild(allItem);

        // Add individual categories
        Object.entries(this.categories).forEach(([key, category]) => {
            if (category.count > 0) {
                const item = this.createCategoryItem(key, category.name, category.color, category.count);
                container.appendChild(item);
            }
        });
    }

    createCategoryItem(key, name, color, count) {
        const item = document.createElement('div');
        item.className = 'category-item';
        item.dataset.category = key;

        item.innerHTML = `
            <div style="display: flex; align-items: center;">
                <div class="category-color" style="background-color: ${color};"></div>
                <span class="category-name text-white">${name}</span>
            </div>
            <span class="category-count badge bg-secondary">${count}</span>
        `;

        item.addEventListener('click', () => {
            this.filterByCategory(key === 'all' ? null : key);

            // Update active state with animation
            document.querySelectorAll('.category-item').forEach(el => el.classList.remove('active'));
            item.classList.add('active');
        });

        return item;
    }

    async loadSatellites() {
        try {
            const response = await fetch('/api/satellites');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success && data.satellites && data.satellites.length > 0) {
                // Efficient satellite data update with position interpolation
                const isFirstLoad = this.satellites.size === 0;

                // Update satellite data with smooth transitions
                const newSatellites = new Map();
                data.satellites.forEach(sat => {
                    const existingSat = this.satellites.get(sat.norad_id);
                    if (existingSat) {
                        // Smooth interpolation for position updates
                        sat.lastUpdateTime = Date.now();
                        sat.previousPosition = {
                            latitude: existingSat.latitude,
                            longitude: existingSat.longitude,
                            altitude: existingSat.altitude
                        };
                    }
                    newSatellites.set(sat.norad_id, sat);
                });

                this.satellites = newSatellites;

                // Always update positions for smooth motion
                this.updateSatellitePositions();

                // Always re-render entities for debugging
                console.log(`Loading ${data.satellites.length} satellites, first load: ${isFirstLoad}`);
                this.renderSatellites();

                this.updateStatus(data.satellites.length, data.timestamp);
                document.getElementById('connectionStatus').textContent = 'Connected';
                document.getElementById('connectionStatus').className = 'badge bg-success ms-auto';

                const satCountElement = document.getElementById('satCount');
                if (satCountElement) {
                    satCountElement.textContent = data.satellites.length;
                }
            } else {
                console.error('Failed to load satellites:', data);
                this.showError(data.error || 'Failed to load satellite data');
                document.getElementById('connectionStatus').textContent = 'No Data';
                document.getElementById('connectionStatus').className = 'badge bg-warning ms-auto';
            }
        } catch (error) {
            console.error('Error loading satellites:', error);
            this.showError(`Network error: ${error.message}`);
            document.getElementById('connectionStatus').textContent = 'Disconnected';
            document.getElementById('connectionStatus').className = 'badge bg-danger ms-auto';
        }
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
        // Enhanced performance rendering
        const camera = this.viewer.camera;
        const scene = this.viewer.scene;

        // Clear existing entities efficiently
        this.satelliteEntities.forEach(entity => {
            this.viewer.entities.remove(entity);
        });
        this.satelliteEntities.clear();

        // Render satellites with LOD and performance optimizations
        let renderedCount = 0;
        console.log(`Starting to render satellites. Total in map: ${this.satellites.size}`);

        this.satellites.forEach((satellite, noradId) => {
            if (this.activeCategoryFilter && satellite.category !== this.activeCategoryFilter) {
                return;
            }

            if (renderedCount >= this.maxVisibleSatellites) {
                return;
            }

            // Validate satellite position data
            if (typeof satellite.latitude !== 'number' || typeof satellite.longitude !== 'number' || 
                typeof satellite.altitude !== 'number' || isNaN(satellite.latitude) || 
                isNaN(satellite.longitude) || isNaN(satellite.altitude)) {
                console.warn(`Skipping satellite ${satellite.name} due to invalid position:`, satellite);
                return;
            }

            // Reduced logging for better performance
            if (renderedCount < 2) {  // Only log first 2 for debugging
                console.log(`Rendering satellite ${renderedCount + 1}: ${satellite.name} at ${satellite.latitude.toFixed(2)}, ${satellite.longitude.toFixed(2)}, ${satellite.altitude.toFixed(2)}km`);
            }

            // Dynamic position that updates with satellite movement
            const position = new Cesium.CallbackProperty(() => {
                const currentSat = this.satellites.get(noradId);
                if (currentSat) {
                    return Cesium.Cartesian3.fromDegrees(
                        currentSat.longitude,
                        currentSat.latitude,
                        currentSat.altitude * 1000
                    );
                }
                return Cesium.Cartesian3.fromDegrees(
                    satellite.longitude,
                    satellite.latitude,
                    satellite.altitude * 1000
                );
            }, false);

            const entity = this.viewer.entities.add({
                id: `satellite_${noradId}`,
                name: satellite.name,
                position: position,
                point: {
                    pixelSize: 3,
                    color: Cesium.Color.fromCssColorString(satellite.color || '#64b5f6'),
                    outlineColor: Cesium.Color.WHITE,
                    outlineWidth: 0.3,
                    heightReference: Cesium.HeightReference.NONE,
                    show: true,
                    // Enable depth testing so satellites behind Earth are hidden
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
                    leadTime: 3600, // 15 minutes
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
            renderedCount++;
        });

        console.log(`Rendered ${renderedCount} satellites out of ${this.satellites.size} total satellites`);

        // Debug: Check if any satellites were actually added to Cesium
        const totalEntities = this.viewer.entities.values.length;
        console.log(`Total entities in Cesium viewer: ${totalEntities}`);

        // Enable proper depth testing and lighting for realistic rendering
        this.viewer.scene.globe.enableLighting = true;
        this.viewer.scene.globe.depthTestAgainstTerrain = true;
    }

    onSatelliteClick(event) {
        const pickedObject = this.viewer.scene.pick(event.position);

        if (Cesium.defined(pickedObject) && pickedObject.id.satelliteData) {
            const satellite = pickedObject.id.satelliteData;
            
            // Clear any existing click timeout
            if (this.clickTimeout) {
                clearTimeout(this.clickTimeout);
                this.clickTimeout = null;
                
                // This is a double click - enable continuous tracking
                this.selectSatellite(satellite.norad_id, true);
                return;
            }
            
            // This might be a single click - wait to see if double click follows
            this.clickTimeout = setTimeout(() => {
                this.clickTimeout = null;
                // Single click - focus but don't track continuously
                this.selectSatellite(satellite.norad_id, false);
            }, 300);
            
        } else {
            this.deselectSatellite();
        }
    }

    async selectSatellite(noradId, enableTracking = false) {
        // Clear previous selection visualizations
        if (this.selectedSatellite && this.selectedSatellite !== noradId) {
            this.clearSatelliteVisualizations(this.selectedSatellite);
        }

        this.selectedSatellite = noradId;

        // Enhanced visual selection
        this.updateSatelliteSelection();

        // Focus on satellite
        this.focusOnSatellite(noradId);

        // Only start continuous tracking if it's a double click or tracking is enabled
        if (enableTracking) {
            this.trackSatellite(noradId);
        }

        // Load detailed information
        await this.loadSatelliteDetails(noradId);

        // Start real-time details updates
        this.startRealTimeDetailsUpdates(noradId);

        // Load orbital path if enabled
        if (this.showOrbits) {
            await this.showOrbitPath(noradId);
        }

        // Only show ground tracks, nadir line, and field of view for Earth observation satellites
        if (this.showGroundTracks && this.isEarthObservationSatellite(noradId)) {
            await this.loadSatelliteGroundTrack(noradId);
            await this.renderFutureGroundTrack(noradId);
            this.renderNadirLine(noradId);
        }

        // Only show pass predictions for LEO satellites (not HEO/GEO)
        const satellite = this.satellites.get(noradId);
        if (satellite && satellite.altitude < 10000 && (this.userLocation.lat !== 0 || this.userLocation.lon !== 0)) {
            await this.loadPassPredictions(noradId);
        }
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
                await this.loadSatelliteDetails(noradId);
            }
        }, 10000);
    }

    stopRealTimeDetailsUpdates() {
        if (this.realTimeUpdateInterval) {
            clearInterval(this.realTimeUpdateInterval);
            this.realTimeUpdateInterval = null;
        }
    }

    deselectSatellite() {
        if (this.selectedSatellite) {
            this.clearSatelliteVisualizations(this.selectedSatellite);
        }
        this.selectedSatellite = null;

        document.getElementById('satelliteInfo').style.display = 'none';
        document.getElementById('passInfo').style.display = 'none';

        this.updateSatelliteSelection();
    }

    updateSatelliteSelection() {
        this.satelliteEntities.forEach((entity, noradId) => {
            const isSelected = noradId === this.selectedSatellite;

            // Enhanced selection appearance with smaller sizes
            entity.point.pixelSize = isSelected ? 6 : 3;
            entity.point.outlineWidth = isSelected ? 0.8 : 0.3;
            entity.label.show = isSelected;

            if (isSelected) {
                entity.point.color = Cesium.Color.YELLOW;
                entity.point.outlineColor = Cesium.Color.WHITE;
            } else {
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
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success && data.satellite) {
                this.renderSatelliteDetails(data.satellite);
            } else {
                console.warn('Failed to load satellite details:', data);
                document.getElementById('satelliteInfo').style.display = 'none';
            }
        } catch (error) {
            console.error('Error loading satellite details:', error);
            document.getElementById('satelliteInfo').style.display = 'none';
        }
    }

    renderSatelliteDetails(satellite) {
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
            <div class="d-flex justify-content-start mt-3">
                        ${this.isISS(satellite) ? `
                            <button class="btn btn-primary btn-sm" onclick="showISSVideo()">
                                <i class="fas fa-video"></i> Live Video
                            </button>
                        ` : ''}
                    </div>
        `;

        document.getElementById('satelliteInfo').style.display = 'block';
    }

    async loadSatelliteOrbit(noradId) {
        try {
            this.clearSelectedOrbit();

            const response = await fetch(`/api/satellite/${noradId}/orbit?duration=3`);
            const data = await response.json();

            if (data.success && data.orbit_points.length > 0) {
                this.renderSatelliteOrbit(noradId, data.orbit_points);
            }
        } catch (error) {
            console.error('Error loading satellite orbit:', error);
        }
    }

    async loadSatelliteGroundTrack(noradId) {
        try {
            const response = await fetch(`/api/satellite/${noradId}/ground-track?duration=3&swath_width=300`);
            const data = await response.json();

            if (data.success && data.ground_track.length > 0) {
                this.renderSatelliteGroundTrack(noradId, data.ground_track);
            }
        } catch (error) {
            console.error('Error loading satellite ground track:', error);
        }
    }

    renderSatelliteGroundTrack(noradId, groundTrackPoints) {
        // Remove existing ground track for this satellite
        this.clearSelectedGroundTrack();

        if (groundTrackPoints.length < 2) return;

        const satellite = this.satellites.get(noradId);
        const color = satellite ? satellite.color : '#64b5f6';

        // Create center line positions
        const centerPositions = groundTrackPoints.map(point =>
            Cesium.Cartesian3.fromDegrees(point.longitude, point.latitude, 0)
        );

        // Create swath boundary positions
        const leftBoundaryPositions = groundTrackPoints.map(point =>
            Cesium.Cartesian3.fromDegrees(point.swath_left_lon, point.swath_left_lat, 0)
        );

        const rightBoundaryPositions = groundTrackPoints.map(point =>
            Cesium.Cartesian3.fromDegrees(point.swath_right_lon, point.swath_right_lat, 0)
        );

        // Create swath polygon for coverage area
        const swathPositions = [];
        leftBoundaryPositions.forEach(pos => swathPositions.push(pos));
        rightBoundaryPositions.reverse().forEach(pos => swathPositions.push(pos));

        // Add enhanced swath coverage area with real-time satellite reference
        const swathEntity = this.viewer.entities.add({
            id: `ground_swath_${noradId}`,
            polygon: {
                hierarchy: swathPositions,
                material: new Cesium.ColorMaterialProperty(
                    new Cesium.CallbackProperty(() => {
                        const currentSat = this.satellites.get(noradId);
                        if (currentSat && this.selectedSatellite === noradId) {
                            return Cesium.Color.fromCssColorString(color).withAlpha(0.4);
                        }
                        return Cesium.Color.fromCssColorString(color).withAlpha(0.2);
                    }, false)
                ),
                outline: true,
                outlineColor: new Cesium.CallbackProperty(() => {
                    const currentSat = this.satellites.get(noradId);
                    if (currentSat && this.selectedSatellite === noradId) {
                        return Cesium.Color.fromCssColorString(color).withAlpha(0.8);
                    }
                    return Cesium.Color.fromCssColorString(color).withAlpha(0.5);
                }, false),
                height: 0,
                extrudedHeight: 0
            }
        });

        // Add enhanced center line with dynamic properties
        const centerLineEntity = this.viewer.entities.add({
            id: `ground_track_center_${noradId}`,
            polyline: {
                positions: centerPositions,
                width: new Cesium.CallbackProperty(() => {
                    const currentSat = this.satellites.get(noradId);
                    if (currentSat && this.selectedSatellite === noradId) {
                        return 4; // Thicker line for selected satellite
                    }
                    return 2;
                }, false),
                material: new Cesium.PolylineGlowMaterialProperty({
                    glowPower: new Cesium.CallbackProperty(() => {
                        const currentSat = this.satellites.get(noradId);
                        if (currentSat && this.selectedSatellite === noradId) {
                            return 0.6; // More glow for selected satellite
                        }
                        return 0.3;
                    }, false),
                    color: new Cesium.CallbackProperty(() => {
                        const currentSat = this.satellites.get(noradId);
                        if (currentSat && this.selectedSatellite === noradId) {
                            return Cesium.Color.fromCssColorString(color).withAlpha(1.0);
                        }
                        return Cesium.Color.fromCssColorString(color).withAlpha(0.7);
                    }, false)
                }),
                clampToGround: true
            }
        });

        // Add satellite reference markers along the ground track
        const currentSatellitePosition = this.viewer.entities.add({
            id: `ground_track_current_${noradId}`,
            position: new Cesium.CallbackProperty(() => {
                const currentSat = this.satellites.get(noradId);
                if (currentSat) {
                    return Cesium.Cartesian3.fromDegrees(
                        currentSat.longitude,
                        currentSat.latitude,
                        0
                    );
                }
                return undefined;
            }, false),
            point: {
                pixelSize: 8,
                color: Cesium.Color.fromCssColorString(color),
                outlineColor: Cesium.Color.WHITE,
                outlineWidth: 2,
                heightReference: Cesium.HeightReference.CLAMP_TO_GROUND,
                show: new Cesium.CallbackProperty(() => {
                    return this.selectedSatellite === noradId;
                }, false)
            },
            label: {
                text: 'Current Position',
                font: '10pt Arial',
                fillColor: Cesium.Color.WHITE,
                outlineColor: Cesium.Color.BLACK,
                outlineWidth: 2,
                style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                pixelOffset: new Cesium.Cartesian2(0, -30),
                show: new Cesium.CallbackProperty(() => {
                    return this.selectedSatellite === noradId;
                }, false),
                heightReference: Cesium.HeightReference.CLAMP_TO_GROUND
            }
        });

        this.groundTrackEntities.set(`swath_${noradId}`, swathEntity);
        this.groundTrackEntities.set(`center_${noradId}`, centerLineEntity);
        this.groundTrackEntities.set(`current_${noradId}`, currentSatellitePosition);
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

    renderSatelliteOrbit(noradId, orbitPoints) {
        this.clearSelectedOrbit();

        if (orbitPoints.length < 2) return;

        const positions = orbitPoints.map(point => 
            Cesium.Cartesian3.fromDegrees(point.longitude, point.latitude, point.altitude * 1000)
        );

        const satellite = this.satellites.get(noradId);
        const color = satellite ? satellite.color : '#64b5f6';

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
        try {
            const response = await fetch(`/api/satellite/${noradId}/passes?lat=${this.userLocation.lat}&lon=${this.userLocation.lon}&alt=${this.userLocation.alt}`);
            const data = await response.json();

            if (data.success) {
                this.renderPassPredictions(data.passes);
            }
        } catch (error) {
            console.error('Error loading pass predictions:', error);
        }
    }

    renderPassPredictions(passes) {
        const tabsContainer = document.getElementById('passNavTabs');
        const contentContainer = document.getElementById('passTabContent');

        if (passes.length === 0) {
            tabsContainer.innerHTML = '';
            contentContainer.innerHTML = '<p class="text-muted p-3">No upcoming passes found</p>';
            document.getElementById('passInfo').style.display = 'block';
            return;
        }

        // Create tabs for each pass
        const tabsHtml = passes.slice(0, 6).map((pass, index) => `
            <li class="nav-item" role="presentation">
                <button class="nav-link ${index === 0 ? 'active' : ''}" id="pass-tab-${index}" 
                        data-bs-toggle="tab" data-bs-target="#pass-${index}" type="button" 
                        role="tab" aria-controls="pass-${index}" aria-selected="${index === 0}">
                    Pass ${index + 1}
                </button>
            </li>
        `).join('');

        // Create tab content for each pass
        const contentHtml = passes.slice(0, 6).map((pass, index) => `
            <div class="tab-pane fade ${index === 0 ? 'show active' : ''}" id="pass-${index}" 
                 role="tabpanel" aria-labelledby="pass-tab-${index}">
                <div class="p-3">
                    <div class="mb-2">
                        <strong class="text-info">Rise Time:</strong><br>
                        <small>${new Date(pass.rise_time).toLocaleString()}</small>
                    </div>
                    <div class="mb-2">
                        <strong class="text-success">Max Elevation:</strong><br>
                        <small>${pass.max_elevation?.toFixed(1)}° at ${new Date(pass.culmination_time || pass.rise_time).toLocaleTimeString()}</small>
                    </div>
                    <div class="mb-2">
                        <strong class="text-warning">Duration:</strong><br>
                        <small>${pass.duration_minutes?.toFixed(1)} minutes</small>
                    </div>
                    ${pass.set_time ? `
                    <div class="mb-2">
                        <strong class="text-danger">Set Time:</strong><br>
                        <small>${new Date(pass.set_time).toLocaleString()}</small>
                    </div>
                    ` : ''}
                    <div class="row g-2 mt-2">
                        <div class="col-6">
                            <small class="text-muted">Rise Az:</small><br>
                            <small class="text-primary">${pass.rise_azimuth?.toFixed(1)}°</small>
                        </div>
                        <div class="col-6">
                            <small class="text-muted">Set Az:</small><br>
                            <small class="text-primary">${pass.set_azimuth?.toFixed(1)}°</small>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        tabsContainer.innerHTML = tabsHtml;
        contentContainer.innerHTML = contentHtml;
        document.getElementById('passInfo').style.display = 'block';
    }

    async searchSatellites(query) {
        const container = document.getElementById('searchResults');

        if (!query || query.length < 2) {
            container.innerHTML = '';
            this.showAllSatellites();
            return;
        }

        try {
            const response = await fetch(`/api/satellites/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();

            if (data.success && data.satellites.length > 0) {
                // Show only searched satellites
                this.showOnlySearchedSatellites(data.satellites);

                container.innerHTML = data.satellites.slice(0, 10).map(sat => `
                    <div class="search-result" data-norad-id="${sat.norad_id}">
                        <div class="d-flex align-items-center">
                            <div class="category-color me-2"></div>
                            <span class="text-white">${sat.name}</span>
                            <small class="text-muted ms-auto">${sat.category}</small>
                        </div>
                    </div>
                `).join('');

                // Add click handlers
                container.querySelectorAll('.search-result').forEach(item => {
                    item.addEventListener('click', () => {
                        const noradId = parseInt(item.dataset.noradId);
                        this.selectSatellite(noradId);
                        this.focusOnSatellite(noradId);
                        container.innerHTML = '';
                    });
                });
            } else {
                container.innerHTML = '<div class="text-muted p-2">No satellites found</div>';
            }
        } catch (error) {
            console.error('Error searching satellites:', error);
        }
    }

    showOnlySearchedSatellites(searchedSatellites) {
        // Hide all satellite entities first
        this.satelliteEntities.forEach(entity => {
            entity.show = false;
        });

        // Show only searched satellites
        searchedSatellites.forEach(searchedSat => {
            const entity = this.satelliteEntities.get(searchedSat.norad_id);
            if (entity) {
                entity.show = true;
            }
        });
    }

    showAllSatellites() {
        // Show all satellite entities
        this.satelliteEntities.forEach(entity => {
            entity.show = true;
        });
    }

    focusOnSatellite(noradId) {
        const satellite = this.satellites.get(noradId);
        if (!satellite) return;

        // Smooth flyTo animation to satellite's actual position in space
        const satelliteAltitude = parseFloat(satellite.altitude) * 1000; // Convert km to meters
        const viewingDistance = Math.max(satelliteAltitude + 2000000, 2000000); // At least 2000km viewing distance
        
        const destination = Cesium.Cartesian3.fromDegrees(
            parseFloat(satellite.longitude),
            parseFloat(satellite.latitude),
            viewingDistance
        );

        this.viewer.camera.flyTo({
            destination: destination,
            orientation: {
                heading: 0.0,
                pitch: -Cesium.Math.PI_OVER_TWO, // Look down at an angle to see satellite
                roll: 0.0
            },
            duration: 2.0,
            easingFunction: Cesium.EasingFunction.CUBIC_IN_OUT
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

    filterByCategory(category) {
        this.activeCategoryFilter = category;
        this.renderSatellites();
    }



    async showOrbitPath(noradId) {
        try {
            const response = await fetch(`/api/satellite/${noradId}/orbit?duration=3`);
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

        // Create dynamic circular swath footprint that updates with satellite position
        const circularSwath = this.viewer.entities.add({
            id: `nadir_circle_${noradId}`,
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
                        // Calculate swath radius based on altitude (300km default swath width)
                        const swathWidth = 300000; // 300km in meters
                        const altitude = currentSat.altitude * 1000; // Convert to meters
                        return Math.min(swathWidth / 2, altitude * Math.tan(Math.PI / 6)); // Max 30° viewing angle
                    }
                    return 150000; // Default 150km radius
                }, false),
                semiMinorAxis: new Cesium.CallbackProperty(() => {
                    const currentSat = this.satellites.get(noradId);
                    if (currentSat) {
                        const swathWidth = 300000; // 300km in meters
                        const altitude = currentSat.altitude * 1000;
                        return Math.min(swathWidth / 2, altitude * Math.tan(Math.PI / 6));
                    }
                    return 150000;
                }, false),
                material: new Cesium.ColorMaterialProperty(
                    Cesium.Color.fromCssColorString(color).withAlpha(0.2)
                ),
                outline: true,
                outlineColor: Cesium.Color.fromCssColorString(color).withAlpha(0.6),
                height: 0,
                rotation: new Cesium.CallbackProperty(() => {
                    // Add slight rotation based on satellite movement for realism
                    const currentSat = this.satellites.get(noradId);
                    if (currentSat && currentSat.velocity) {
                        return (Date.now() / 10000) % (2 * Math.PI); // Slow rotation
                    }
                    return 0;
                }, false)
            }
        });

        this.nadirEntities.set(`line_${noradId}`, nadirLine);
        this.nadirEntities.set(`circle_${noradId}`, circularSwath);
    }

    async renderFutureGroundTrack(noradId) {
        try {
            const response = await fetch(`/api/satellite/${noradId}/ground-track?duration=6&swath_width=300`);
            const data = await response.json();

            if (data.success && data.ground_track.length > 0) {
                const satellite = this.satellites.get(noradId);
                const color = satellite ? satellite.color : '#64b5f6';

                // Split ground track into past (dimmer) and future (brighter)
                const currentTime = Date.now();
                const futurePoints = data.ground_track.filter(point => point.time_offset_minutes > 0);

                if (futurePoints.length < 2) return;

                // Create future center line positions
                const futureCenterPositions = futurePoints.map(point =>
                    Cesium.Cartesian3.fromDegrees(point.longitude, point.latitude, 0)
                );

                // Create future swath boundary positions
                const futureLeftBoundary = futurePoints.map(point =>
                    Cesium.Cartesian3.fromDegrees(point.swath_left_lon, point.swath_left_lat, 0)
                );

                const futureRightBoundary = futurePoints.map(point =>
                    Cesium.Cartesian3.fromDegrees(point.swath_right_lon, point.swath_right_lat, 0)
                );

                // Create future swath polygon
                const futureSwathPositions = [];
                futureLeftBoundary.forEach(pos => futureSwathPositions.push(pos));
                futureRightBoundary.reverse().forEach(pos => futureSwathPositions.push(pos));

                // Add future swath coverage area
                const futureSwathEntity = this.viewer.entities.add({
                    id: `future_ground_swath_${noradId}`,
                    polygon: {
                        hierarchy: futureSwathPositions,
                        material: Cesium.Color.fromCssColorString(color).withAlpha(0.15),
                        outline: true,
                        outlineColor: Cesium.Color.fromCssColorString(color).withAlpha(0.4),
                        height: 0,
                        extrudedHeight: 0
                    }
                });

                // Add future center line
                const futureCenterLineEntity = this.viewer.entities.add({
                    id: `future_ground_track_center_${noradId}`,
                    polyline: {
                        positions: futureCenterPositions,
                        width: 2,
                        material: new Cesium.PolylineDashMaterialProperty({
                            color: Cesium.Color.fromCssColorString(color).withAlpha(0.8),
                            dashLength: 16
                        }),
                        clampToGround: true
                    }
                });

                this.groundTrackEntities.set(`future_swath_${noradId}`, futureSwathEntity);
                this.groundTrackEntities.set(`future_center_${noradId}`, futureCenterLineEntity);
            }
        } catch (error) {
            console.error('Error loading future ground track:', error);
        }
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
            // Ground tracks will be shown only for earth observation satellites
            if (this.selectedSatellite && this.isEarthObservationSatellite(this.selectedSatellite)) {
                this.loadSatelliteGroundTrack(this.selectedSatellite);
                this.renderFutureGroundTrack(this.selectedSatellite);
                this.renderNadirLine(this.selectedSatellite);
            }
        } else {
            btn.classList.remove('active');
            this.clearSelectedGroundTrack();
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

    toggleCloudCover() {
        this.cloudCoverEnabled = !this.cloudCoverEnabled;
        const btn = document.getElementById('cloudCoverBtn');

        if (this.cloudCoverEnabled) {
            btn.classList.add('active');
            this.enableCloudCover();
        } else {
            btn.classList.remove('active');
            this.disableCloudCover();
        }
    }

    async enableCloudCover() {
        try {
            console.log('Enabling real-time cloud cover...');

            // Remove any existing cloud layers first
            this.disableCloudCover();

            // Use OpenWeatherMap cloud layer - reliable and works well
            this.cloudLayer = this.viewer.imageryLayers.addImageryProvider(
                new Cesium.UrlTemplateImageryProvider({
                    url: 'https://tile.openweathermap.org/map/clouds_new/{z}/{x}/{y}.png?appid=b6907d289e10d714a6e88b30761fae22',
                    credit: 'OpenWeatherMap Clouds',
                    maximumLevel: 18,
                    minimumLevel: 0,
                    hasAlphaChannel: true,
                    tilingScheme: new Cesium.WebMercatorTilingScheme(),
                    tileWidth: 256,
                    tileHeight: 256
                })
            );

            // Set optimal properties for cloud visibility
            this.cloudLayer.alpha = 0.6;
            this.cloudLayer.brightness = 1.2;
            this.cloudLayer.contrast = 1.1;
            this.cloudLayer.hue = 0.0;
            this.cloudLayer.saturation = 1.0;
            this.cloudLayer.gamma = 1.0;

            console.log('OpenWeatherMap cloud cover enabled successfully');

            // Add precipitation layer for enhanced weather visualization
            try {
                this.precipitationLayer = this.viewer.imageryLayers.addImageryProvider(
                    new Cesium.UrlTemplateImageryProvider({
                        url: 'https://tile.openweathermap.org/map/precipitation_new/{z}/{x}/{y}.png?appid=b6907d289e10d714a6e88b30761fae22',
                        credit: 'OpenWeatherMap Precipitation',
                        maximumLevel: 16,
                        minimumLevel: 0,
                        hasAlphaChannel: true,
                        tilingScheme: new Cesium.WebMercatorTilingScheme()
                    })
                );
                
                this.precipitationLayer.alpha = 0.4;
                this.precipitationLayer.brightness = 1.0;
                console.log('Precipitation layer added');
            } catch (precipError) {
                console.warn('Could not load precipitation data:', precipError);
            }

            // Enhanced atmospheric effects for realism
            this.viewer.scene.skyAtmosphere.show = true;
            this.viewer.scene.fog.enabled = true;
            this.viewer.scene.fog.density = 0.0002;
            this.viewer.scene.fog.screenSpaceErrorFactor = 2.0;

            // Update clouds every 10 minutes for fresh data
            this.cloudUpdateInterval = setInterval(() => {
                this.updateCloudData();
            }, 600000); // 10 minutes

            // Force scene update
            this.viewer.scene.requestRender();
            
            console.log('Real-time cloud cover system activated');

        } catch (error) {
            console.warn('Primary cloud service failed, trying NASA GIBS:', error);
            this.enableNASACloudCover();
        }
    }

    enableNASACloudCover() {
        try {
            console.log('Enabling NASA GIBS cloud visualization...');

            // Get yesterday's date (NASA GIBS usually has 1-day delay)
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);
            const dateString = yesterday.getFullYear() + '-' + 
                String(yesterday.getMonth() + 1).padStart(2, '0') + '-' + 
                String(yesterday.getDate()).padStart(2, '0');

            // Use NASA GIBS MODIS Aqua True Color imagery
            this.cloudLayer = this.viewer.imageryLayers.addImageryProvider(
                new Cesium.UrlTemplateImageryProvider({
                    url: `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Aqua_CorrectedReflectance_TrueColor/default/${dateString}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg`,
                    credit: 'NASA GIBS MODIS Aqua',
                    maximumLevel: 9,
                    minimumLevel: 0,
                    tilingScheme: new Cesium.WebMercatorTilingScheme(),
                    tileWidth: 256,
                    tileHeight: 256,
                    hasAlphaChannel: false
                })
            );

            // Optimal settings for NASA imagery
            this.cloudLayer.alpha = 0.8;
            this.cloudLayer.brightness = 1.1;
            this.cloudLayer.contrast = 1.3;
            this.cloudLayer.gamma = 0.9;
            this.cloudLayer.saturation = 1.2;

            // Enhanced atmospheric effects
            this.viewer.scene.skyAtmosphere.show = true;
            this.viewer.scene.fog.enabled = true;
            this.viewer.scene.fog.density = 0.0001;
            this.viewer.scene.fog.screenSpaceErrorFactor = 1.8;

            console.log('NASA GIBS cloud cover enabled successfully');

        } catch (error) {
            console.error('Failed to enable NASA cloud effects:', error);
            this.enableBasicAtmosphericEffects();
        }
    }

    enableBasicAtmosphericEffects() {
        console.log('Enabling basic atmospheric effects...');
        
        // Last resort: enhance atmospheric rendering
        this.viewer.scene.skyAtmosphere.show = true;
        this.viewer.scene.skyAtmosphere.brightnessShift = 0.1;
        this.viewer.scene.fog.enabled = true;
        this.viewer.scene.fog.density = 0.0003;
        this.viewer.scene.fog.minimumBrightness = 0.03;
        
        // Add subtle haze effect
        this.viewer.scene.globe.atmosphereHueShift = 0.1;
        this.viewer.scene.globe.atmosphereSaturationShift = 0.1;
        this.viewer.scene.globe.atmosphereBrightnessShift = 0.05;
        
        console.log('Basic atmospheric enhancement enabled');
    }

    updateCloudData() {
        console.log('Updating real-time cloud data...');
        
        if (!this.cloudCoverEnabled) {
            console.log('Cloud cover disabled, skipping update');
            return;
        }

        try {
            // Store current settings
            const currentAlpha = this.cloudLayer?.alpha || 0.6;
            const currentBrightness = this.cloudLayer?.brightness || 1.2;
            const currentContrast = this.cloudLayer?.contrast || 1.1;

            // Remove old cloud layers
            if (this.cloudLayer) {
                this.viewer.imageryLayers.remove(this.cloudLayer);
                this.cloudLayer = null;
            }
            if (this.precipitationLayer) {
                this.viewer.imageryLayers.remove(this.precipitationLayer);
                this.precipitationLayer = null;
            }

            // Add fresh cloud layer with timestamp to avoid caching
            const timestamp = Date.now();
            this.cloudLayer = this.viewer.imageryLayers.addImageryProvider(
                new Cesium.UrlTemplateImageryProvider({
                    url: `https://tile.openweathermap.org/map/clouds_new/{z}/{x}/{y}.png?appid=b6907d289e10d714a6e88b30761fae22&t=${timestamp}`,
                    credit: 'OpenWeatherMap Clouds (Updated)',
                    maximumLevel: 18,
                    minimumLevel: 0,
                    hasAlphaChannel: true,
                    tilingScheme: new Cesium.WebMercatorTilingScheme()
                })
            );

            // Restore settings
            this.cloudLayer.alpha = currentAlpha;
            this.cloudLayer.brightness = currentBrightness;
            this.cloudLayer.contrast = currentContrast;

            // Add updated precipitation layer
            this.precipitationLayer = this.viewer.imageryLayers.addImageryProvider(
                new Cesium.UrlTemplateImageryProvider({
                    url: `https://tile.openweathermap.org/map/precipitation_new/{z}/{x}/{y}.png?appid=b6907d289e10d714a6e88b30761fae22&t=${timestamp}`,
                    credit: 'OpenWeatherMap Precipitation (Updated)',
                    maximumLevel: 16,
                    minimumLevel: 0,
                    hasAlphaChannel: true,
                    tilingScheme: new Cesium.WebMercatorTilingScheme()
                })
            );

            this.precipitationLayer.alpha = 0.4;
            this.precipitationLayer.brightness = 1.0;

            // Force scene refresh
            this.viewer.scene.requestRender();
            
            console.log('Cloud data updated successfully with fresh imagery');

        } catch (error) {
            console.warn('Failed to update cloud data:', error);
            // Try to re-enable cloud cover if update fails
            setTimeout(() => {
                if (this.cloudCoverEnabled) {
                    this.enableCloudCover();
                }
            }, 5000);
        }
    }

    disableCloudCover() {
        console.log('Disabling cloud cover...');

        // Remove all cloud-related layers
        if (this.cloudLayer) {
            this.viewer.imageryLayers.remove(this.cloudLayer);
            this.cloudLayer = null;
        }

        if (this.precipitationLayer) {
            this.viewer.imageryLayers.remove(this.precipitationLayer);
            this.precipitationLayer = null;
        }

        if (this.goesLayer) {
            this.viewer.imageryLayers.remove(this.goesLayer);  
            this.goesLayer = null;
        }

        if (this.cloudProvider) {
            this.cloudProvider = null;
        }

        // Clear update interval
        if (this.cloudUpdateInterval) {
            clearInterval(this.cloudUpdateInterval);
            this.cloudUpdateInterval = null;
        }

        // Reset atmospheric effects to normal
        this.viewer.scene.fog.enabled = false;
        this.viewer.scene.fog.density = 0.0;
        this.viewer.scene.fog.minimumBrightness = 0.0;
        this.viewer.scene.skyAtmosphere.show = true; // Keep atmosphere visible
        this.viewer.scene.skyAtmosphere.brightnessShift = 0.0;
        
        // Reset globe atmospheric effects
        this.viewer.scene.globe.atmosphereHueShift = 0.0;
        this.viewer.scene.globe.atmosphereSaturationShift = 0.0;
        this.viewer.scene.globe.atmosphereBrightnessShift = 0.0;

        // Force scene refresh
        this.viewer.scene.requestRender();

        console.log('Cloud cover completely disabled and atmospheric effects reset');
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

    resetView() {
        // If user location is available, go there; otherwise go to default view
        if (this.userLocation && (this.userLocation.lat !== 0 || this.userLocation.lon !== 0)) {
            this.viewer.camera.flyTo({
                destination: Cesium.Cartesian3.fromDegrees(
                    this.userLocation.lon,
                    this.userLocation.lat,
                    5000000 // 5000km altitude for good view
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

            const response = await fetch('/api/refresh', {
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
                    document.getElementById('latitude').value = position.coords.latitude;
                    document.getElementById('longitude').value = position.coords.longitude;
                    document.getElementById('altitude').value = position.coords.altitude || 0;
                },
                (error) => {
                    this.showError('Could not get your location');
                }
            );
        } else {
            this.showError('Geolocation is not supported');
        }
    }

    saveLocation() {
        const lat = parseFloat(document.getElementById('latitude').value);
        const lon = parseFloat(document.getElementById('longitude').value);
        const alt = parseFloat(document.getElementById('altitude').value) || 0;

        this.userLocation = { lat, lon, alt };
        this.preferences.location = this.userLocation;
        this.saveUserPreferences();

        const modal = bootstrap.Modal.getInstance(document.getElementById('locationModal'));
        modal.hide();

        // Reload pass predictions for selected satellite
        if (this.selectedSatellite) {
            this.loadPassPredictions(this.selectedSatellite);
        }
    }

    startAutoUpdate() {
        // Optimized update frequency for better performance
        this.updateInterval = setInterval(() => {
            console.log('Auto-updating satellite positions...');
            this.loadSatellites();
        }, 30000); // 30 seconds for better performance

        // Optimized position interpolation for balanced performance
        this.positionUpdateInterval = setInterval(() => {
            this.updateSatellitePositions();
        }, 5000); // Update positions every 5 seconds for balanced performance
    }

    updateStatus(count, timestamp) {
        document.getElementById('satelliteCount').textContent = `${count} satellites`;

        const lastUpdateTime = new Date(timestamp);
        document.getElementById('lastUpdate').textContent = 
            `Updated: ${lastUpdateTime.toLocaleTimeString()}`;
    }

    showLoadingOverlay() {
        // Loading overlay removed for smoother experience
    }

    hideLoadingOverlay() {
        // Loading overlay removed for smoother experience
    }

    showError(message) {
        document.getElementById('errorMessage').textContent = message;
        const toast = new bootstrap.Toast(document.getElementById('errorToast'));
        toast.show();
    }

    clearGroundTrack() {
        // Remove ground track entity
        if (this.groundTrackEntity) {
            this.viewer.entities.remove(this.groundTrackEntity);
            this.groundTrackEntity = null;
        }

        // Remove nadir line entity
        if (this.nadirLineEntity) {
            this.viewer.entities.remove(this.nadirLineEntity);
            this.nadirLineEntity = null;
        }

        // Remove any ground track related entities
        const entitiesToRemove = [];
        this.viewer.entities.values.forEach(entity => {
            if (entity.id && (entity.id.includes('groundtrack') || entity.id.includes('nadir') || entity.id.includes('swath'))) {
                entitiesToRemove.push(entity);
            }
        });

        entitiesToRemove.forEach(entity => {
            this.viewer.entities.remove(entity);
        });

        // Clear any polyline collections
        if (this.viewer.scene.primitives) {
            const primitivesToRemove = [];
            for (let i = 0; i < this.viewer.scene.primitives.length; i++) {
                const primitive = this.viewer.scene.primitives.get(i);
                if (primitive.constructor.name === 'PolylineCollection') {
                    primitivesToRemove.push(primitive);
                }
            }
            primitivesToRemove.forEach(primitive => {
                this.viewer.scene.primitives.remove(primitive);
            });
        }
    }

    createISSVideoModal() {
        // Create ISS Video Modal
        const modalHTML = `
            <div class="modal fade" id="issVideoModal" tabindex="-1" aria-labelledby="issVideoModalLabel" aria-hidden="true">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="issVideoModalLabel">ISS Live Video</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <iframe id="issVideoFrame" width="100%" height="500" src="" frameborder="0" allowfullscreen></iframe>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHTML);
    }

    isISS(satellite) {
        // Check if satellite is ISS based on name or NORAD ID
        const name = satellite.name ? satellite.name.toUpperCase() : '';
        return name.includes('ISS') || name.includes('ZARYA') || satellite.norad_id === 25544;
    }

    isEarthObservationSatellite(noradId) {
        // Check if satellite is earth observation based on category
        const satellite = this.satellites.get(noradId);
        if (!satellite) return false;
        
        const category = satellite.category ? satellite.category.toLowerCase() : '';
        const name = satellite.name ? satellite.name.toUpperCase() : '';
        
        // Check category first
        if (category === 'earth_observation' || category === 'scientific') return true;
        
        // Check name patterns for earth observation satellites
        const earthObsKeywords = [
            'LANDSAT', 'SENTINEL', 'SPOT', 'WORLDVIEW', 'QUICKBIRD', 
            'TERRA', 'AQUA', 'MODIS', 'IKONOS', 'GEOEYE', 'PLEIADES',
            'RESOURCESAT', 'CARTOSAT', 'KOMPSAT', 'ALOS', 'RADARSAT',
            'COSMO-SKYMED', 'TERRASAR', 'ENVISAT', 'ERS', 'CBERS',
            'NOAA', 'GOES', 'METEOSAT', 'HIMAWARI', 'METEOR'
        ];
        
        return earthObsKeywords.some(keyword => name.includes(keyword));
    }
}

// Function to show ISS live video
function showISSVideo() {
    // Create modal for ISS video
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = 'issVideoModal';
    modal.innerHTML = `
        <div class="modal-dialog modal-lg">
            <div class="modal-content bg-dark text-light">
                <div class="modal-header">
                    <h5 class="modal-title">ISS Live Video Stream</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="ratio ratio-16x9">
                        <iframe src="https://www.youtube.com/embed/fO9e9jnhYK8?rel=0&modestbranding=1" 
                                frameborder="0" 
                                allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                                allowfullscreen>
                        </iframe>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Check if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const modalInstance = new bootstrap.Modal(modal);
        modalInstance.show();

        // Clean up modal when hidden
        modal.addEventListener('hidden.bs.modal', function() {
            document.body.removeChild(modal);
        });
    } else {
        // Fallback if Bootstrap isn't loaded
        modal.style.display = 'block';
        modal.classList.add('show');

        // Add close functionality
        const closeBtn = modal.querySelector('.btn-close');
        closeBtn.addEventListener('click', function() {
            modal.style.display = 'none';
            document.body.removeChild(modal);
        });
    }
}

// Initialize satellite viewer when both DOM and Cesium are ready
document.addEventListener('DOMContentLoaded', function() {
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