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
        // Initial load
        this.loadSatellites();

        // Check offline status
        this.checkOfflineStatus();

        // Start update interval
        this.startUpdateInterval();
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
            animation: true,
            timeline: true,
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
                this.updateRate = (this.preferences.update_interval || 5) * 200;

                // Update UI safely
                const latElement = document.getElementById('latitude');
                const lonElement = document.getElementById('longitude');
                const altElement = document.getElementById('altitude');
                const updateRateElement = document.getElementById('updateRate');

                if (latElement) latElement.value = this.userLocation.lat;
                if (lonElement) lonElement.value = this.userLocation.lon;
                if (altElement) altElement.value = this.userLocation.alt;
                if (updateRateElement) updateRateElement.textContent = `${this.preferences.update_interval || 5}s`;
            } else {
                // Set defaults
                this.userLocation = { lat: 0, lon: 0, alt: 0 };
                this.updateRate = 1000; // 5 seconds
            }
        } catch (error) {
            console.warn('Could not load user preferences, using defaults:', error);
            this.userLocation = { lat: 0, lon: 0, alt: 0 };
            this.updateRate = 1000;
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
            const response = await fetch(`/api/satellite/${noradId}/orbit`);
            const data = await response.json();

            if (data.success) {
                this.renderSatelliteOrbit(noradId, data.orbit);
            }
        } catch (error) {
            console.error('Error loading satellite orbit:', error);
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
            container.innerHTML = '<p class="text-muted">No upcoming passes found</p>';
        } else {
            container.innerHTML = passes.slice(0, 3).map(pass => `
                <div class="pass-item">
                    <div class="pass-time">${new Date(pass.rise_time).toLocaleString()}</div>
                    <div class="pass-details">
                        <small>Max elevation: ${pass.max_elevation?.toFixed(1)}° • Duration: ${pass.duration_minutes?.toFixed(1)} min</small>
                    </div>
                </div>
            `).join('');
        }

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

        this.viewer.camera.flyTo({
            destination: Cesium.Cartesian3.fromDegrees(
                satellite.longitude,
                satellite.latitude,
                satellite.altitude * 1000 + 2000000 // 2000km above satellite
            ),
            orientation: {
                heading: 0.0,
                pitch: -Cesium.Math.PI_OVER_FOUR,
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

    resetView() {
        this.viewer.camera.flyTo({
            destination: Cesium.Cartesian3.fromDegrees(0, 30, 12000000),
            orientation: {
                heading: 0.0,
                pitch: -Cesium.Math.PI_OVER_FOUR,
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

    startUpdateInterval() {
        // Clear existing interval
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }

        // Start new interval with current update rate
        this.updateInterval = setInterval(() => {
            this.loadSatellites();
        }, this.updateRate * 1000);

        console.log(`Update interval set to ${this.updateRate} seconds`);
    }

    async checkOfflineStatus() {
        try {
            const response = await fetch('/api/offline/status');
            const data = await response.json();

            if (data.success) {
                this.updateOfflineIndicator(data.offline_status);
            }
        } catch (error) {
            console.error('Error checking offline status:', error);
            this.updateOfflineIndicator({ offline_mode: true, cache_available: false });
        }
    }

    updateOfflineIndicator(status) {
        // Create or update offline status indicator
        let indicator = document.getElementById('offline-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'offline-indicator';
            indicator.style.cssText = `
                position: fixed;
                top: 10px;
                right: 10px;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 12px;
                z-index: 1000;
                font-weight: bold;
            `;
            document.body.appendChild(indicator);
        }

        if (status.offline_mode) {
            indicator.innerHTML = `🔒 OFFLINE MODE<br>
                <small>${status.cache_available ? 
                    `${status.cache_stats?.total_satellites || 0} satellites cached` : 
                    'No cache available'}</small>`;
            indicator.style.backgroundColor = status.can_predict_offline ? '#ff9800' : '#f44336';
            indicator.style.color = 'white';
        } else if (status.cache_available) {
            indicator.innerHTML = `🌐 ONLINE<br>
                <small>Offline backup ready (${status.cache_stats?.total_satellites || 0} sats)</small>`;
            indicator.style.backgroundColor = '#4caf50';
            indicator.style.color = 'white';
        } else {
            indicator.innerHTML = '🌐 ONLINE';
            indicator.style.backgroundColor = '#2196f3';
            indicator.style.color = 'white';
        }
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