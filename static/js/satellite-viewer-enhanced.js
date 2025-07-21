
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
        this.fpsCounter = 0;
        this.lastFrameTime = 0;
        this.frameCount = 0;
        this.preferences = {};

        // Performance optimizations
        this.updateRate = 200; // 200ms for 10fps feel
        this.maxVisibleSatellites = 10000;
        this.lodDistance = 10000000; // Level of detail distance

        this.init();
    }

    async init() {
        this.initializeCesium();
        this.setupEventListeners();
        await this.loadUserPreferences();
        await this.loadCategories();
        await this.loadSatellites();
        this.startAutoUpdate();
        this.setupGeolocation();
    }

    initializeCesium() {
        // Use default Cesium Ion token
        Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJlYWE1ZjJiOS1mOGYyLTQ1M2MtOGM2MS1kYzA2YjIxOGI4ZjciLCJpZCI6MjAzNzIsImlhdCI6MTY5NDU0Mzk5OX0.SW1LQITUzCb5gFmLNAa8aeJ7bXhDI1_3pj6_8yUAKPk';

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
            maximumRenderTimeChange: 1000/10, // Target 10fps
        });

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

        // Loading overlay removed for smoother experience
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
                this.updateRate = (this.preferences.update_interval || 1) * 200;

                // Update UI safely
                const latElement = document.getElementById('latitude');
                const lonElement = document.getElementById('longitude');
                const altElement = document.getElementById('altitude');
                const updateRateElement = document.getElementById('updateRate');

                if (latElement) latElement.value = this.userLocation.lat;
                if (lonElement) lonElement.value = this.userLocation.lon;
                if (altElement) altElement.value = this.userLocation.alt;
                if (updateRateElement) updateRateElement.textContent = `${this.preferences.update_interval || 1}s`;
            } else {
                // Set defaults
                this.userLocation = { lat: 0, lon: 0, alt: 0 };
                this.updateRate = 200; // 1 seconds
            }
        } catch (error) {
            console.warn('Could not load user preferences, using defaults:', error);
            this.userLocation = { lat: 0, lon: 0, alt: 0 };
            this.updateRate = 200;
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

                    // Update preferences
                    this.preferences.location = this.userLocation;
                    this.saveUserPreferences();

                    document.getElementById('latitude').value = this.userLocation.lat;
                    document.getElementById('longitude').value = this.userLocation.lon;
                    document.getElementById('altitude').value = this.userLocation.alt;
                },
                (error) => {
                    console.warn('Geolocation failed:', error);
                }
            );
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
                // Efficient satellite data update
                const isFirstLoad = this.satellites.size === 0;

                // Update satellite data
                const newSatellites = new Map();
                data.satellites.forEach(sat => {
                    newSatellites.set(sat.norad_id, sat);
                });

                this.satellites = newSatellites;

                // Only re-render if necessary
                if (isFirstLoad || this.satelliteEntities.size === 0) {
                    this.renderSatellites();
                }

                this.updateStatus(data.satellites.length, data.timestamp);
                document.getElementById('connectionStatus').textContent = 'Connected';
                document.getElementById('connectionStatus').className = 'badge bg-success ms-auto';

                const satCountElement = document.getElementById('satCount');
                if (satCountElement) {
                    satCountElement.textContent = data.satellites.length;
                }
            } else {
                console.warn('No satellite data received:', data);
                document.getElementById('connectionStatus').textContent = 'No Data';
                document.getElementById('connectionStatus').className = 'badge bg-warning ms-auto';
            }
        } catch (error) {
            console.error('Error loading satellites:', error);
            document.getElementById('connectionStatus').textContent = 'Disconnected';
            document.getElementById('connectionStatus').className = 'badge bg-danger ms-auto';
        }
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
        this.satellites.forEach((satellite, noradId) => {
            if (this.activeCategoryFilter && satellite.category !== this.activeCategoryFilter) {
                return;
            }

            if (renderedCount >= this.maxVisibleSatellites) {
                return;
            }

            // Dynamic position property with enhanced performance
            const positionProperty = new Cesium.CallbackProperty(() => {
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
                position: positionProperty,
                point: {
                    pixelSize: 10,
                    color: Cesium.Color.fromCssColorString(satellite.color),
                    outlineColor: Cesium.Color.WHITE,
                    outlineWidth: 0.5,
                    heightReference: Cesium.HeightReference.NONE,
                    scaleByDistance: new Cesium.NearFarScalar(1.5e6, 2.0, 1.5e7, 0.5),
                    translucencyByDistance: new Cesium.NearFarScalar(1.5e6, 1.0, 1.5e7, 0.8)
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

        console.log(`Rendered ${renderedCount} satellites for optimal performance`);
    }

    onSatelliteClick(event) {
        const pickedObject = this.viewer.scene.pick(event.position);

        if (Cesium.defined(pickedObject) && pickedObject.id.satelliteData) {
            const satellite = pickedObject.id.satelliteData;
            this.selectSatellite(satellite.norad_id);
        } else {
            this.deselectSatellite();
        }
    }

    async selectSatellite(noradId) {
        this.selectedSatellite = noradId;

        // Enhanced visual selection
        this.updateSatelliteSelection();

        // Load detailed information
        await this.loadSatelliteDetails(noradId);

        // Load orbital path if enabled
        if (this.showOrbits || this.preferences.show_satellite_paths) {
            await this.loadSatelliteOrbit(noradId);
        }

        // Load pass predictions
        if (this.userLocation.lat !== 0 || this.userLocation.lon !== 0) {
            await this.loadPassPredictions(noradId);
        }

        // Enhanced tracking
        if (this.trackingMode) {
            this.focusOnSatellite(noradId);
        }
    }

    deselectSatellite() {
        this.selectedSatellite = null;

        document.getElementById('satelliteInfo').style.display = 'none';
        document.getElementById('passInfo').style.display = 'none';

        this.updateSatelliteSelection();
        this.clearSelectedOrbit();
    }

    updateSatelliteSelection() {
        this.satelliteEntities.forEach((entity, noradId) => {
            const isSelected = noradId === this.selectedSatellite;

            // Enhanced selection appearance
            entity.point.pixelSize = isSelected ? 16 : 12;
            entity.point.outlineWidth = isSelected ? 3 : 2;
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
            const response = await fetch(`/api/satellite/${noradId}`);
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

        container.innerHTML = `
            <div class="satellite-header mb-3">
                <strong class="text-info">${satellite.name}</strong>
            </div>

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

            // Load ground track only if ground tracks are enabled OR if it's an Earth observation satellite
            const satellite = this.satellites.get(noradId);
            if (this.showGroundTracks || (satellite && satellite.category === 'Earth_Observation')) {
                await this.loadSatelliteGroundTrack(noradId);
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
        this.clearGroundTrack(noradId);

        if (groundTrackPoints.length < 2) return;

        const satellite = this.satellites.get(noradId);
        const color = satellite ? satellite.color : '#64b5f6';

        // Create ground track line (clamped to ground)
        const positions = groundTrackPoints.map(point =>
            Cesium.Cartesian3.fromDegrees(point.longitude, point.latitude)
        );

        const groundTrackEntity = this.viewer.entities.add({
            id: `ground_track_${noradId}`,
            polyline: {
                positions: positions,
                width: 3,
                material: new Cesium.PolylineGlowMaterialProperty({
                    glowPower: 0.2,
                    color: Cesium.Color.fromCssColorString(color).withAlpha(0.6)
                }),
                clampToGround: true
            }
        });

        this.orbitEntities.set(`ground_track_${noradId}`, groundTrackEntity);

        // Create swath coverage visualization (polygons showing coverage width)
        if (groundTrackPoints.length > 1 && groundTrackPoints[0].swath_width_km) {
            this.renderSwathCoverage(noradId, groundTrackPoints, color);
        }

        // Add nadir line for selected satellite
        if (noradId === this.selectedSatellite) {
            this.renderNadirLine(noradId, satellite, color);
        }
    }

    renderSwathCoverage(noradId, groundTrackPoints, color) {
        // Create polygons to show swath width coverage
        for (let i = 0; i < groundTrackPoints.length - 1; i += 5) { // Skip some points for performance
            const point = groundTrackPoints[i];
            const nextPoint = groundTrackPoints[i + 1] || point;
            
            // Calculate swath boundary points
            const swathHalfWidth = point.swath_width_km / 2;
            const earthRadius = 6371; // km
            const latOffset = (swathHalfWidth / earthRadius) * (180 / Math.PI);
            
            // Create a simple rectangular swath coverage
            const swathPositions = [
                Cesium.Cartesian3.fromDegrees(point.longitude, point.latitude - latOffset),
                Cesium.Cartesian3.fromDegrees(point.longitude, point.latitude + latOffset),
                Cesium.Cartesian3.fromDegrees(nextPoint.longitude, nextPoint.latitude + latOffset),
                Cesium.Cartesian3.fromDegrees(nextPoint.longitude, nextPoint.latitude - latOffset)
            ];

            const swathEntity = this.viewer.entities.add({
                id: `swath_${noradId}_${i}`,
                polygon: {
                    hierarchy: swathPositions,
                    material: Cesium.Color.fromCssColorString(color).withAlpha(0.15),
                    outline: false,
                    extrudedHeight: 0
                }
            });

            this.orbitEntities.set(`swath_${noradId}_${i}`, swathEntity);
        }
    }

    renderNadirLine(noradId, satellite, color) {
        // Create nadir point on ground
        const nadirPosition = Cesium.Cartesian3.fromDegrees(
            satellite.longitude, 
            satellite.latitude, 
            0
        );

        // Create satellite position
        const satellitePosition = Cesium.Cartesian3.fromDegrees(
            satellite.longitude, 
            satellite.latitude, 
            satellite.altitude * 1000
        );

        // Create nadir line (vertical line from satellite to ground)
        const nadirLineEntity = this.viewer.entities.add({
            id: `nadir_line_${noradId}`,
            polyline: {
                positions: [satellitePosition, nadirPosition],
                width: 2,
                material: Cesium.Color.fromCssColorString(color).withAlpha(0.7),
                clampToGround: false
            }
        });

        this.orbitEntities.set(`nadir_line_${noradId}`, nadirLineEntity);

        // Create circular ground footprint with blur effect
        const footprintRadius = (satellite.altitude * 1000) * Math.tan(0.1); // Approximate sensor footprint
        const footprintEntity = this.viewer.entities.add({
            id: `nadir_footprint_${noradId}`,
            position: nadirPosition,
            ellipse: {
                semiMajorAxis: footprintRadius,
                semiMinorAxis: footprintRadius,
                material: new Cesium.RadialGradientMaterialProperty({
                    color: Cesium.Color.fromCssColorString(color).withAlpha(0.3),
                    radius: 1.0
                }),
                outline: true,
                outlineColor: Cesium.Color.fromCssColorString(color).withAlpha(0.6)
            }
        });

        this.orbitEntities.set(`nadir_footprint_${noradId}`, footprintEntity);
    }

    clearGroundTrack(noradId) {
        // Clear ground track line
        const groundTrackEntity = this.orbitEntities.get(`ground_track_${noradId}`);
        if (groundTrackEntity) {
            this.viewer.entities.remove(groundTrackEntity);
            this.orbitEntities.delete(`ground_track_${noradId}`);
        }

        // Clear swath coverage polygons
        const swathKeys = Array.from(this.orbitEntities.keys()).filter(key => 
            key.startsWith(`swath_${noradId}_`)
        );
        swathKeys.forEach(key => {
            const entity = this.orbitEntities.get(key);
            if (entity) {
                this.viewer.entities.remove(entity);
                this.orbitEntities.delete(key);
            }
        });

        // Clear nadir line and footprint
        const nadirLineEntity = this.orbitEntities.get(`nadir_line_${noradId}`);
        if (nadirLineEntity) {
            this.viewer.entities.remove(nadirLineEntity);
            this.orbitEntities.delete(`nadir_line_${noradId}`);
        }

        const nadirFootprintEntity = this.orbitEntities.get(`nadir_footprint_${noradId}`);
        if (nadirFootprintEntity) {
            this.viewer.entities.remove(nadirFootprintEntity);
            this.orbitEntities.delete(`nadir_footprint_${noradId}`);
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
        if (this.selectedSatellite && this.orbitEntities.has(this.selectedSatellite)) {
            this.viewer.entities.remove(this.orbitEntities.get(this.selectedSatellite));
            this.orbitEntities.delete(this.selectedSatellite);
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
        const container = document.getElementById('passPredictions');

        if (passes.length === 0) {
            container.innerHTML = '<p class="text-muted">No upcoming passes found for your location</p>';
            document.getElementById('passInfo').style.display = 'block';
        } else {
            container.innerHTML = passes.slice(0, 6).map((pass, index) => `
                <div class="pass-item">
                    <div class="pass-time">Pass ${index + 1}: ${new Date(pass.rise_time).toLocaleDateString()} ${new Date(pass.rise_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
                    <div class="pass-details">
                        <small>
                            <strong>Rise:</strong> ${new Date(pass.rise_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} 
                            (${pass.rise_azimuth ? pass.rise_azimuth.toFixed(0) + '°' : 'N/A'})<br>
                            <strong>Peak:</strong> ${pass.max_elevation ? pass.max_elevation.toFixed(1) + '°' : 'N/A'} elevation<br>
                            <strong>Set:</strong> ${pass.set_time ? new Date(pass.set_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : 'N/A'}
                            (${pass.set_azimuth ? pass.set_azimuth.toFixed(0) + '°' : 'N/A'})<br>
                            <strong>Duration:</strong> ${pass.duration_minutes ? pass.duration_minutes.toFixed(1) + ' min' : 'N/A'}
                        </small>
                    </div>
                </div>
            `).join('');
            document.getElementById('passInfo').style.display = 'block';
        }
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

        this.viewer.camera.flyTo({
            destination: Cesium.Cartesian3.fromDegrees(
                satellite.longitude,
                satellite.latitude,
                satellite.altitude * 1000 + 2000000 // 2000km above satellite
            ),
            orientation: {
                heading: 0.0,
                pitch: -Cesium.Math.PI_OVER_TWO,
                roll: 0.0
            },
            duration: 3.0
        });
    }

    filterByCategory(category) {
        this.activeCategoryFilter = category;
        this.renderSatellites();
    }

    async toggleOrbits() {
        this.showOrbits = !this.showOrbits;

        if (this.showOrbits && this.selectedSatellite) {
            await this.showOrbitPath(this.selectedSatellite);
        } else {
            this.clearOrbitPaths();
        }
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

        const positions = [];
        orbitPoints.forEach(point => {
            positions.push(Cesium.Cartesian3.fromDegrees(
                point.longitude,
                point.latitude,
                point.altitude * 1000
            ));
        });

        const orbitEntity = this.viewer.entities.add({
            id: `orbit_${noradId}`,
            polyline: {
                positions: positions,
                width: 2,
                material: Cesium.Color.YELLOW.withAlpha(0.8),
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

    clearOrbitPaths() {
        this.orbitEntities.forEach(entity => {
            this.viewer.entities.remove(entity);
        });
        this.orbitEntities.clear();
        const btn = document.getElementById('orbitsBtn');

        if (this.showOrbits) {
            btn.classList.add('active');
            if (this.selectedSatellite) {
                this.loadSatelliteOrbit(this.selectedSatellite);
            }
        } else {
            btn.classList.remove('active');
            this.clearSelectedOrbit();
        }
    }

    toggleTracking() {
        this.trackingMode = !this.trackingMode;
        const btn = document.getElementById('trackingBtn');

        if (this.trackingMode) {
            btn.classList.add('active');
            if (this.selectedSatellite) {
                this.focusOnSatellite(this.selectedSatellite);
            }
        } else {
            btn.classList.remove('active');
        }
    }

    toggleGroundTracks() {
        this.showGroundTracks = !this.showGroundTracks;
        const btn = document.getElementById('groundTracksBtn');

        if (this.showGroundTracks) {
            btn.classList.add('active');
            this.showAllGroundTracks();
        } else {
            btn.classList.remove('active');
            this.clearAllGroundTracks();
        }
    }

    async showAllGroundTracks() {
        // Show ground tracks for Earth observation satellites
        for (const [noradId, satellite] of this.satellites) {
            if (satellite.category === 'Earth_Observation') {
                await this.loadSatelliteGroundTrack(noradId);
            }
        }
    }

    clearAllGroundTracks() {
        // Clear all ground track entities
        const groundTrackKeys = Array.from(this.orbitEntities.keys()).filter(key => 
            key.startsWith('ground_track_') || key.startsWith('nadir_')
        );
        
        groundTrackKeys.forEach(key => {
            const entity = this.orbitEntities.get(key);
            if (entity) {
                this.viewer.entities.remove(entity);
                this.orbitEntities.delete(key);
            }
        });
    }

    resetView() {
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

    refreshData() {
        this.loadSatellites();
        this.loadCategories();
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
        // High-frequency updates for smooth 10fps feel
        this.updateInterval = setInterval(() => {
            this.loadSatellites();
        }, this.updateRate);
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
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.satelliteViewer = new SatelliteViewer();
});
