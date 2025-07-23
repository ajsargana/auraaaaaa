
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
        this.fpsCounter = 0;
        this.lastFrameTime = 0;
        this.frameCount = 0;
        this.preferences = {};

        // Performance optimizations
        this.updateRate = 1000; // 1000ms (1 second) for better synchronization
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
    }

    async loadUserPreferences() {
        try {
            const response = await fetch('/api/user/preferences');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            if (data.success) {
                this.preferences = data.preferences;
                this.userLocation = this.preferences.location || { lat: 0, lon: 0, alt: 0 };
            }
        } catch (error) {
            console.error('Error loading user preferences:', error);
            this.preferences = {
                location: { lat: 0, lon: 0, alt: 0 },
                update_interval: 1,
                show_satellite_paths: true,
                favorite_satellites: []
            };
        }
    }

    setupEventListeners() {
        // Control buttons
        document.getElementById('homeBtn').addEventListener('click', () => {
            this.viewer.camera.setView({
                destination: Cesium.Cartesian3.fromDegrees(0, 0, 15000000)
            });
        });

        document.getElementById('trackingBtn').addEventListener('click', () => {
            this.trackingMode = !this.trackingMode;
            document.getElementById('trackingBtn').classList.toggle('btn-outline-success', this.trackingMode);
        });

        document.getElementById('orbitsBtn').addEventListener('click', () => {
            this.toggleOrbits();
        });

        document.getElementById('groundTracksBtn').addEventListener('click', () => {
            this.toggleGroundTracks();
        });

        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.refreshSatelliteData();
        });

        document.getElementById('locationBtn').addEventListener('click', () => {
            const modal = new bootstrap.Modal(document.getElementById('locationModal'));
            modal.show();
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
            <div class="d-flex align-items-center">
                <div class="category-color" style="background-color: ${color}"></div>
                <span class="category-name">${name}</span>
            </div>
            <span class="badge bg-secondary">${count}</span>
        `;

        item.addEventListener('click', () => {
            this.filterByCategory(key);
            document.querySelectorAll('.category-item').forEach(i => i.classList.remove('active'));
            item.classList.add('active');
        });

        return item;
    }

    filterByCategory(categoryKey) {
        this.activeCategoryFilter = categoryKey === 'all' ? null : categoryKey;
        this.updateSatelliteVisibility();
    }

    updateSatelliteVisibility() {
        this.satelliteEntities.forEach((entity, noradId) => {
            const satellite = this.satellites.get(noradId);
            if (satellite) {
                const shouldShow = !this.activeCategoryFilter || satellite.category === this.activeCategoryFilter;
                entity.show = shouldShow;
            }
        });
    }

    async loadSatellites() {
        try {
            const response = await fetch('/api/satellites');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success && data.satellites) {
                this.updateSatellites(data.satellites);
                this.updateStatusBar(data.satellites.length, data.timestamp);
            } else {
                this.showError('Failed to load satellites');
            }
        } catch (error) {
            console.error('Error loading satellites:', error);
            this.showError('Error loading satellite data');
        }
    }

    updateSatellites(satellitesData) {
        const existingEntities = new Set(this.satelliteEntities.keys());

        satellitesData.forEach(sat => {
            this.satellites.set(sat.norad_id, sat);
            existingEntities.delete(sat.norad_id);

            if (!this.satelliteEntities.has(sat.norad_id)) {
                this.createSatelliteEntity(sat);
            } else {
                this.updateSatelliteEntity(sat);
            }
        });

        // Remove satellites that no longer exist
        existingEntities.forEach(noradId => {
            this.removeSatelliteEntity(noradId);
        });

        this.updateSatelliteVisibility();
    }

    createSatelliteEntity(satellite) {
        const entity = this.viewer.entities.add({
            id: `satellite_${satellite.norad_id}`,
            name: satellite.name,
            position: Cesium.Cartesian3.fromDegrees(
                satellite.longitude,
                satellite.latitude,
                satellite.altitude * 1000
            ),
            point: {
                pixelSize: 8,
                color: Cesium.Color.fromCssColorString(satellite.color),
                outlineColor: Cesium.Color.WHITE,
                outlineWidth: 2,
                heightReference: Cesium.HeightReference.NONE
            },
            label: {
                text: satellite.name,
                font: '12pt sans-serif',
                fillColor: Cesium.Color.WHITE,
                outlineColor: Cesium.Color.BLACK,
                outlineWidth: 2,
                style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
                pixelOffset: new Cesium.Cartesian2(0, -20),
                show: false
            },
            satellite_data: satellite
        });

        this.satelliteEntities.set(satellite.norad_id, entity);
    }

    updateSatelliteEntity(satellite) {
        const entity = this.satelliteEntities.get(satellite.norad_id);
        if (entity) {
            entity.position = Cesium.Cartesian3.fromDegrees(
                satellite.longitude,
                satellite.latitude,
                satellite.altitude * 1000
            );
            entity.satellite_data = satellite;
        }
    }

    removeSatelliteEntity(noradId) {
        const entity = this.satelliteEntities.get(noradId);
        if (entity) {
            this.viewer.entities.remove(entity);
            this.satelliteEntities.delete(noradId);
        }
        this.satellites.delete(noradId);
    }

    onSatelliteClick(event) {
        const picked = this.viewer.scene.pick(event.position);
        if (picked && picked.id && picked.id.id.startsWith('satellite_')) {
            const noradId = parseInt(picked.id.id.replace('satellite_', ''));
            this.selectSatellite(noradId);
        } else {
            this.deselectSatellite();
        }
    }

    async selectSatellite(noradId) {
        // Clear previous selection
        this.deselectSatellite();
        
        this.selectedSatellite = noradId;
        const entity = this.satelliteEntities.get(noradId);
        
        if (entity) {
            // Highlight selected satellite
            entity.point.pixelSize = 12;
            entity.label.show = true;
            
            // Load and display satellite details
            await this.loadSatelliteDetails(noradId);
            
            // Load and display pass predictions
            await this.loadPassPredictions(noradId);
            
            // Create nadir line and ground track circle
            this.createNadirLine(noradId);
            this.createGroundTrackCircle(noradId);
            
            // Track the satellite if tracking mode is enabled
            if (this.trackingMode) {
                this.viewer.trackedEntity = entity;
            }
        }
    }

    deselectSatellite() {
        if (this.selectedSatellite) {
            const entity = this.satelliteEntities.get(this.selectedSatellite);
            if (entity) {
                entity.point.pixelSize = 8;
                entity.label.show = false;
            }
            
            // Remove nadir line and ground track circle
            this.removeNadirLine(this.selectedSatellite);
            this.removeGroundTrackCircle(this.selectedSatellite);
            
            this.selectedSatellite = null;
            this.viewer.trackedEntity = undefined;
            
            // Hide satellite info panels
            document.getElementById('satelliteInfo').style.display = 'none';
            document.getElementById('passInfo').style.display = 'none';
        }
    }

    createNadirLine(noradId) {
        const satellite = this.satellites.get(noradId);
        if (!satellite) return;

        const entity = this.viewer.entities.add({
            id: `nadir_${noradId}`,
            polyline: {
                positions: [
                    Cesium.Cartesian3.fromDegrees(satellite.longitude, satellite.latitude, satellite.altitude * 1000),
                    Cesium.Cartesian3.fromDegrees(satellite.longitude, satellite.latitude, 0)
                ],
                width: 2,
                material: Cesium.Color.YELLOW.withAlpha(0.8),
                clampToGround: false
            }
        });

        this.nadirEntities.set(noradId, entity);
    }

    createGroundTrackCircle(noradId) {
        const satellite = this.satellites.get(noradId);
        if (!satellite) return;

        // Create circular ground track with 300km radius
        const entity = this.viewer.entities.add({
            id: `ground_circle_${noradId}`,
            position: Cesium.Cartesian3.fromDegrees(satellite.longitude, satellite.latitude, 0),
            ellipse: {
                semiMajorAxis: 300000, // 300km in meters
                semiMinorAxis: 300000,
                material: Cesium.Color.CYAN.withAlpha(0.3),
                outline: true,
                outlineColor: Cesium.Color.CYAN,
                extrudedHeight: 0,
                clampToGround: true
            }
        });

        this.groundCircleEntities.set(noradId, entity);
    }

    removeNadirLine(noradId) {
        const entity = this.nadirEntities.get(noradId);
        if (entity) {
            this.viewer.entities.remove(entity);
            this.nadirEntities.delete(noradId);
        }
    }

    removeGroundTrackCircle(noradId) {
        const entity = this.groundCircleEntities.get(noradId);
        if (entity) {
            this.viewer.entities.remove(entity);
            this.groundCircleEntities.delete(noradId);
        }
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
                
                // Start real-time updates for selected satellite
                this.startRealTimeUpdates(noradId);
            } else {
                console.warn('Failed to load satellite details:', data);
                document.getElementById('satelliteInfo').style.display = 'none';
            }
        } catch (error) {
            console.error('Error loading satellite details:', error);
            document.getElementById('satelliteInfo').style.display = 'none';
        }
    }

    startRealTimeUpdates(noradId) {
        // Clear existing interval
        if (this.realTimeUpdateInterval) {
            clearInterval(this.realTimeUpdateInterval);
        }
        
        // Update satellite details every second
        this.realTimeUpdateInterval = setInterval(async () => {
            if (this.selectedSatellite === noradId) {
                await this.updateRealTimeDetails(noradId);
            } else {
                clearInterval(this.realTimeUpdateInterval);
            }
        }, 1000);
    }

    async updateRealTimeDetails(noradId) {
        const satellite = this.satellites.get(noradId);
        if (!satellite) return;

        // Update the details display with current satellite data
        const latElement = document.getElementById('realtime-lat');
        const lonElement = document.getElementById('realtime-lon');
        const velElement = document.getElementById('realtime-vel');
        
        if (latElement) latElement.textContent = satellite.latitude.toFixed(4) + '°';
        if (lonElement) lonElement.textContent = satellite.longitude.toFixed(4) + '°';
        if (velElement) velElement.textContent = (satellite.velocity / 1000).toFixed(2) + ' km/s';
        
        // Update nadir line position
        this.updateNadirLine(noradId);
        this.updateGroundTrackCircle(noradId);
    }

    updateNadirLine(noradId) {
        const satellite = this.satellites.get(noradId);
        const entity = this.nadirEntities.get(noradId);
        
        if (satellite && entity) {
            entity.polyline.positions = [
                Cesium.Cartesian3.fromDegrees(satellite.longitude, satellite.latitude, satellite.altitude * 1000),
                Cesium.Cartesian3.fromDegrees(satellite.longitude, satellite.latitude, 0)
            ];
        }
    }

    updateGroundTrackCircle(noradId) {
        const satellite = this.satellites.get(noradId);
        const entity = this.groundCircleEntities.get(noradId);
        
        if (satellite && entity) {
            entity.position = Cesium.Cartesian3.fromDegrees(satellite.longitude, satellite.latitude, 0);
        }
    }

    renderSatelliteDetails(satellite) {
        const container = document.getElementById('satelliteDetails');

        container.innerHTML = `
            <div class="satellite-header mb-3">
                <strong class="text-info">${satellite.name}</strong>
            </div>
            
            <div class="satellite-section mb-3">
                <h6 class="text-warning mb-2">Real-time Position</h6>
                <div class="satellite-detail-item">
                    <span>Latitude:</span>
                    <span id="realtime-lat">${satellite.position.latitude.toFixed(4)}°</span>
                </div>
                <div class="satellite-detail-item">
                    <span>Longitude:</span>
                    <span id="realtime-lon">${satellite.position.longitude.toFixed(4)}°</span>
                </div>
                <div class="satellite-detail-item">
                    <span>Velocity:</span>
                    <span id="realtime-vel">${satellite.orbit.velocity.toFixed(2)} km/s</span>
                </div>
            </div>

            <div class="satellite-section mb-3">
                <h6 class="text-warning mb-2">Orbital Information</h6>
                <div class="satellite-detail-item">
                    <span>Altitude:</span>
                    <span>${satellite.orbit.altitude.toFixed(0)} km</span>
                </div>
                <div class="satellite-detail-item">
                    <span>Inclination:</span>
                    <span>${satellite.orbit.inclination.toFixed(2)}°</span>
                </div>
                <div class="satellite-detail-item">
                    <span>Period:</span>
                    <span>${satellite.orbit.period.toFixed(1)} min</span>
                </div>
                <div class="satellite-detail-item">
                    <span>Orbit Type:</span>
                    <span class="text-cyan">${satellite.orbit.orbit_type}</span>
                </div>
            </div>

            <div class="satellite-section">
                <h6 class="text-warning mb-2">Technical Details</h6>
                <div class="satellite-detail-item">
                    <span>NORAD ID:</span>
                    <span>${satellite.technical.norad_id}</span>
                </div>
                <div class="satellite-detail-item">
                    <span>Launch Date:</span>
                    <span>${satellite.technical.launch_date}</span>
                </div>
                <div class="satellite-detail-item">
                    <span>Type:</span>
                    <span>${satellite.technical.type}</span>
                </div>
                <div class="satellite-detail-item">
                    <span>Agency:</span>
                    <span>${satellite.technical.agency}</span>
                </div>
                <div class="satellite-detail-item">
                    <span>Status:</span>
                    <span class="text-success">${satellite.technical.status}</span>
                </div>
            </div>
        `;

        document.getElementById('satelliteInfo').style.display = 'block';
    }

    async loadPassPredictions(noradId) {
        try {
            const response = await fetch(`/api/satellite/${noradId}/passes?lat=${this.userLocation.lat}&lon=${this.userLocation.lon}&alt=${this.userLocation.alt}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success && data.passes) {
                this.renderPassPredictions(data.passes);
            } else {
                console.warn('Failed to load pass predictions:', data);
                document.getElementById('passInfo').style.display = 'none';
            }
        } catch (error) {
            console.error('Error loading pass predictions:', error);
            document.getElementById('passInfo').style.display = 'none';
        }
    }

    renderPassPredictions(passes) {
        if (!passes || passes.length === 0) {
            document.getElementById('passInfo').style.display = 'none';
            return;
        }

        const navTabs = document.getElementById('passNavTabs');
        const tabContent = document.getElementById('passTabContent');
        
        navTabs.innerHTML = '';
        tabContent.innerHTML = '';

        passes.slice(0, 6).forEach((pass, index) => {
            const tabId = `pass-tab-${index}`;
            const contentId = `pass-content-${index}`;
            
            // Create tab
            const tab = document.createElement('li');
            tab.className = 'nav-item';
            tab.innerHTML = `
                <button class="nav-link ${index === 0 ? 'active' : ''}" 
                        id="${tabId}" 
                        data-bs-toggle="tab" 
                        data-bs-target="#${contentId}" 
                        type="button" 
                        role="tab">
                    Pass ${index + 1}
                </button>
            `;
            navTabs.appendChild(tab);
            
            // Create content
            const content = document.createElement('div');
            content.className = `tab-pane fade ${index === 0 ? 'show active' : ''}`;
            content.id = contentId;
            content.setAttribute('role', 'tabpanel');
            
            const riseTime = new Date(pass.rise_time).toLocaleString();
            const setTime = new Date(pass.set_time).toLocaleString();
            const culminationTime = new Date(pass.culmination_time).toLocaleString();
            
            content.innerHTML = `
                <div class="mt-3">
                    <div class="satellite-detail-item">
                        <span>Rise Time:</span>
                        <span>${riseTime}</span>
                    </div>
                    <div class="satellite-detail-item">
                        <span>Culmination:</span>
                        <span>${culminationTime}</span>
                    </div>
                    <div class="satellite-detail-item">
                        <span>Set Time:</span>
                        <span>${setTime}</span>
                    </div>
                    <div class="satellite-detail-item">
                        <span>Max Elevation:</span>
                        <span>${pass.max_elevation ? pass.max_elevation.toFixed(1) + '°' : 'N/A'}</span>
                    </div>
                    <div class="satellite-detail-item">
                        <span>Duration:</span>
                        <span>${pass.duration_minutes ? pass.duration_minutes.toFixed(1) + ' min' : 'N/A'}</span>
                    </div>
                </div>
            `;
            
            tabContent.appendChild(content);
        });

        document.getElementById('passInfo').style.display = 'block';
    }

    toggleOrbits() {
        this.showOrbits = !this.showOrbits;
        document.getElementById('orbitsBtn').classList.toggle('btn-outline-success', this.showOrbits);
        
        if (this.showOrbits) {
            this.loadOrbitsForVisibleSatellites();
        } else {
            this.clearAllOrbits();
        }
    }

    async loadOrbitsForVisibleSatellites() {
        const visibleSatellites = Array.from(this.satellites.keys()).slice(0, 10); // Limit for performance
        
        for (const noradId of visibleSatellites) {
            await this.loadSatelliteOrbit(noradId);
        }
    }

    async loadSatelliteOrbit(noradId) {
        try {
            const response = await fetch(`/api/satellite/${noradId}/orbit?duration=3`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success && data.orbit_points) {
                this.createOrbitEntity(noradId, data.orbit_points);
            }
        } catch (error) {
            console.error('Error loading satellite orbit:', error);
        }
    }

    createOrbitEntity(noradId, orbitPoints) {
        if (orbitPoints.length < 2) return;

        const positions = orbitPoints.map(point => 
            Cesium.Cartesian3.fromDegrees(point.longitude, point.latitude, point.altitude * 1000)
        );

        const satellite = this.satellites.get(noradId);
        const color = satellite ? satellite.color : '#FFFFFF';

        const entity = this.viewer.entities.add({
            id: `orbit_${noradId}`,
            polyline: {
                positions: positions,
                width: 2,
                material: Cesium.Color.fromCssColorString(color).withAlpha(0.7),
                clampToGround: false
            }
        });

        this.orbitEntities.set(noradId, entity);
    }

    clearAllOrbits() {
        this.orbitEntities.forEach((entity) => {
            this.viewer.entities.remove(entity);
        });
        this.orbitEntities.clear();
    }

    toggleGroundTracks() {
        this.showGroundTracks = !this.showGroundTracks;
        document.getElementById('groundTracksBtn').classList.toggle('btn-outline-success', this.showGroundTracks);
        
        if (this.showGroundTracks) {
            this.loadGroundTracksForVisibleSatellites();
        } else {
            this.clearAllGroundTracks();
        }
    }

    async loadGroundTracksForVisibleSatellites() {
        const visibleSatellites = Array.from(this.satellites.keys()).slice(0, 10); // Limit for performance
        
        for (const noradId of visibleSatellites) {
            await this.loadSatelliteGroundTrack(noradId);
        }
    }

    async loadSatelliteGroundTrack(noradId) {
        try {
            const response = await fetch(`/api/satellite/${noradId}/ground-track?duration=3&swath_width=300`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success && data.ground_track) {
                this.createGroundTrackEntity(noradId, data.ground_track);
            }
        } catch (error) {
            console.error('Error loading satellite ground track:', error);
        }
    }

    createGroundTrackEntity(noradId, groundTrackPoints) {
        if (groundTrackPoints.length < 2) return;

        const positions = groundTrackPoints.map(point => 
            Cesium.Cartesian3.fromDegrees(point.longitude, point.latitude, 0)
        );

        const satellite = this.satellites.get(noradId);
        const color = satellite ? satellite.color : '#FFFFFF';

        const entity = this.viewer.entities.add({
            id: `ground_track_${noradId}`,
            polyline: {
                positions: positions,
                width: 3,
                material: Cesium.Color.fromCssColorString(color).withAlpha(0.8),
                clampToGround: true
            }
        });

        this.groundTrackEntities.set(noradId, entity);
    }

    clearAllGroundTracks() {
        this.groundTrackEntities.forEach((entity) => {
            this.viewer.entities.remove(entity);
        });
        this.groundTrackEntities.clear();
    }

    async searchSatellites(query) {
        if (!query || query.trim().length < 2) {
            document.getElementById('searchResults').innerHTML = '';
            return;
        }

        try {
            const response = await fetch(`/api/satellites/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();

            if (data.success) {
                this.renderSearchResults(data.satellites);
            }
        } catch (error) {
            console.error('Error searching satellites:', error);
        }
    }

    renderSearchResults(satellites) {
        const container = document.getElementById('searchResults');
        container.innerHTML = '';

        satellites.slice(0, 20).forEach(sat => {
            const item = document.createElement('div');
            item.className = 'search-result';
            item.innerHTML = `
                <div class="fw-bold">${sat.name}</div>
                <small class="text-muted">${sat.category}</small>
            `;

            item.addEventListener('click', () => {
                this.selectSatellite(sat.norad_id);
                container.innerHTML = '';
                document.getElementById('satelliteSearch').value = '';
            });

            container.appendChild(item);
        });
    }

    startAutoUpdate() {
        this.updateInterval = setInterval(() => {
            this.loadSatellites();
        }, this.updateRate);
    }

    async refreshSatelliteData() {
        try {
            const response = await fetch('/api/refresh');
            const data = await response.json();

            if (data.success) {
                await this.loadCategories();
                await this.loadSatellites();
                this.showSuccess('Satellite data refreshed successfully');
            } else {
                this.showError('Failed to refresh satellite data');
            }
        } catch (error) {
            console.error('Error refreshing satellite data:', error);
            this.showError('Error refreshing satellite data');
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
                    this.showError('Geolocation failed: ' + error.message);
                }
            );
        } else {
            this.showError('Geolocation is not supported by this browser');
        }
    }

    saveLocation() {
        const lat = parseFloat(document.getElementById('latitude').value);
        const lon = parseFloat(document.getElementById('longitude').value);
        const alt = parseFloat(document.getElementById('altitude').value) || 0;

        if (isNaN(lat) || isNaN(lon) || lat < -90 || lat > 90 || lon < -180 || lon > 180) {
            this.showError('Invalid coordinates. Please check your input.');
            return;
        }

        this.userLocation = { lat, lon, alt };
        this.preferences.location = this.userLocation;
        this.saveUserPreferences();

        const modal = bootstrap.Modal.getInstance(document.getElementById('locationModal'));
        modal.hide();

        this.showSuccess('Location saved successfully');
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
            console.error('Error saving preferences:', error);
        }
    }

    updateStatusBar(satelliteCount, timestamp) {
        document.getElementById('satCount').textContent = satelliteCount;
        document.getElementById('lastUpdate').textContent = `Last updated: ${new Date(timestamp).toLocaleTimeString()}`;
    }

    showSuccess(message) {
        // You could implement a success toast here
        console.log('Success:', message);
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
