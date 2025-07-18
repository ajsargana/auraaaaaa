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
        this.trackingMode = false;
        this.updateInterval = null;
        this.launchDateFilter = { start: null, end: null };
        
        this.init();
    }
    
    init() {
        this.initializeCesium();
        this.setupEventListeners();
        this.loadCategories();
        this.loadSatellites();
        this.startAutoUpdate();
        this.setupGeolocation();
    }
    
    initializeCesium() {
        // Set Cesium Ion access token (using default for demo)
        Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJlYWE1ZjJiOS1mOGYyLTQ1M2MtOGM2MS1kYzA2YjIxOGI4ZjciLCJpZCI6MjAzNzIsImlhdCI6MTY5NDU0Mzk5OX0.SW1LQITUzCb5gFmLNAa8aeJ7bXhDI1_3pj6_8yUAKPk';
        
        this.viewer = new Cesium.Viewer('cesiumContainer', {
            // Use basic earth imagery that doesn't require Ion
            imageryProvider: new Cesium.OpenStreetMapImageryProvider({
                url: 'https://a.tile.openstreetmap.org/'
            }),
            baseLayerPicker: true,
            geocoder: false,
            homeButton: false,
            sceneModePicker: false,
            navigationHelpButton: false,
            animation: false,
            timeline: false,
            fullscreenButton: false,
            creditContainer: document.createElement('div') // Hide credits
        });
        
        // Set initial camera position - properly centered on Earth
        this.viewer.camera.setView({
            destination: Cesium.Cartesian3.fromDegrees(0, 0, 15000000),
            orientation: {
                heading: 0.0,
                pitch: -Cesium.Math.PI_OVER_FOUR,
                roll: 0.0
            }
        });
        
        // Enable lighting and atmosphere
        this.viewer.scene.globe.enableLighting = true;
        this.viewer.scene.globe.atmosphereHslShift = new Cesium.Cartesian3(0.0, 0.0, 0.0);
        this.viewer.scene.skyAtmosphere.show = true;
        
        // Enable real-time clock for satellite movement
        this.viewer.clock.shouldAnimate = true;
        this.viewer.clock.multiplier = 1;
        
        // Set up click handler for satellite selection
        this.viewer.cesiumWidget.screenSpaceEventHandler.setInputAction(
            this.onSatelliteClick.bind(this),
            Cesium.ScreenSpaceEventType.LEFT_CLICK
        );
        
        // Loading overlay removed for smoother experience
    }
    
    setupEventListeners() {
        // Refresh button
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.refreshData();
        });
        
        // Location button
        document.getElementById('locationBtn').addEventListener('click', () => {
            const modal = new bootstrap.Modal(document.getElementById('locationModal'));
            modal.show();
        });
        
        // Home button (reset view)
        document.getElementById('homeBtn').addEventListener('click', () => {
            this.resetView();
        });
        
        // Tracking button
        document.getElementById('trackingBtn').addEventListener('click', () => {
            this.toggleTracking();
        });
        
        // Orbits button
        document.getElementById('orbitsBtn').addEventListener('click', () => {
            this.toggleOrbits();
        });
        
        // Location modal save button
        document.getElementById('saveLocationBtn').addEventListener('click', () => {
            this.saveLocation();
        });
        
        // Auto location button
        document.getElementById('autoLocationBtn').addEventListener('click', () => {
            this.getCurrentLocation();
        });
        
        // Search functionality
        document.getElementById('satelliteSearch').addEventListener('input', (e) => {
            this.searchSatellites(e.target.value);
        });
        
        // AI Chat functionality
        document.getElementById('sendChatBtn').addEventListener('click', () => {
            this.sendChatMessage();
        });
        
        document.getElementById('chatInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendChatMessage();
            }
        });

        // Launch date filter functionality
        document.getElementById('startDate').addEventListener('change', () => {
            this.updateDateFilter();
        });
        
        document.getElementById('endDate').addEventListener('change', () => {
            this.updateDateFilter();
        });

        document.getElementById('clearDateFilter').addEventListener('click', () => {
            this.clearDateFilter();
        });
    }
    
    setupGeolocation() {
        // Try to get user's location
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    this.userLocation = {
                        lat: position.coords.latitude,
                        lon: position.coords.longitude,
                        alt: position.coords.altitude || 0
                    };
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
        
        // Add "All" category
        const allItem = this.createCategoryItem('all', 'All Satellites', '#ffffff', 
            Object.values(this.categories).reduce((sum, cat) => sum + cat.count, 0));
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
                <span class="category-name">${name}</span>
            </div>
            <span class="category-count">${count}</span>
        `;
        
        item.addEventListener('click', () => {
            this.filterByCategory(key === 'all' ? null : key);
            
            // Update active state
            document.querySelectorAll('.category-item').forEach(el => el.classList.remove('active'));
            item.classList.add('active');
        });
        
        return item;
    }
    
    async loadSatellites() {
        try {
            const response = await fetch('/api/satellites');
            const data = await response.json();
            
            if (data.success) {
                // Update satellite data without re-rendering entities
                const isFirstLoad = this.satellites.size === 0;
                
                this.satellites.clear();
                data.satellites.forEach(sat => {
                    this.satellites.set(sat.norad_id, sat);
                });
                
                // Only re-render satellites on first load or when entities are missing
                if (isFirstLoad || this.satelliteEntities.size === 0) {
                    this.renderSatellites();
                }
                
                this.updateStatus(data.satellites.length, data.timestamp);
                document.getElementById('connectionStatus').textContent = 'Connected';
                document.getElementById('connectionStatus').className = 'badge bg-success ms-auto';
            } else {
                this.showError(data.error || 'Failed to load satellites');
                document.getElementById('connectionStatus').textContent = 'Error';
                document.getElementById('connectionStatus').className = 'badge bg-danger ms-auto';
            }
        } catch (error) {
            console.error('Error loading satellites:', error);
            this.showError('Error connecting to satellite data service');
            const statusEl = document.getElementById('connectionStatus');
            if (statusEl) {
                statusEl.textContent = 'Disconnected';
                statusEl.className = 'badge bg-danger ms-auto';
            }
        } finally {
            this.hideLoadingOverlay();
        }
    }
    
    renderSatellites() {
        // Clear existing satellite entities
        this.satelliteEntities.forEach(entity => {
            this.viewer.entities.remove(entity);
        });
        this.satelliteEntities.clear();
        
        // Add satellites to the globe
        this.satellites.forEach((satellite, noradId) => {
            if (this.activeCategoryFilter && satellite.category !== this.activeCategoryFilter) {
                return; // Skip if category filter is active
            }
            
            if (!this.passesDateFilter(satellite)) {
                return; // Skip if doesn't pass date filter
            }
            
            // Create a dynamic position property that updates in real-time
            const positionProperty = new Cesium.CallbackProperty(() => {
                // Get current satellite data (will be updated by auto-refresh)
                const currentSat = this.satellites.get(noradId);
                if (currentSat) {
                    return Cesium.Cartesian3.fromDegrees(
                        currentSat.longitude,
                        currentSat.latitude,
                        currentSat.altitude * 1000 // Convert km to meters
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
                    pixelSize: 5,
                    color: Cesium.Color.fromCssColorString(satellite.color),
                    outlineColor: Cesium.Color.WHITE,
                    outlineWidth: 0.2,
                    heightReference: Cesium.HeightReference.NONE,
                    scaleByDistance: new Cesium.NearFarScalar(1.5e6, 1.5, 1.5e7, 0.8)
                },
                label: {
                    text: satellite.name,
                    font: '11pt Arial',
                    fillColor: Cesium.color.BLUE,
                    outlineColor: Cesium.Color.BLACK,
                    outlineWidth: 2,
                    style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                    pixelOffset: new Cesium.Cartesian2(15, -15),
                    show: false,
                    scaleByDistance: new Cesium.NearFarScalar(1.5e6, 1.0, 1.5e7, 0.5)
                },
                path: {
                    show: false,
                    leadTime: 600, // 10 minutes ahead
                    trailTime: 600, // 10 minutes behind
                    width: 2,
                    resolution: 120,
                    material: new Cesium.PolylineGlowMaterialProperty({
                        glowPower: 0.2,
                        color: Cesium.Color.fromCssColorString(satellite.color).withAlpha(0.7)
                    })
                },
                satelliteData: satellite
            });
            
            this.satelliteEntities.set(noradId, entity);
        });
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
        
        // Update visual selection
        this.updateSatelliteSelection();
        
        // Load detailed satellite information
        await this.loadSatelliteDetails(noradId);
        
        // Load orbital path if orbits are enabled
        if (this.showOrbits) {
            await this.loadSatelliteOrbit(noradId);
        }
        
        // Load pass predictions if user location is set
        if (this.userLocation.lat !== 0 || this.userLocation.lon !== 0) {
            await this.loadPassPredictions(noradId);
        }
        
        // Focus camera on satellite if tracking is enabled
        if (this.trackingMode) {
            this.focusOnSatellite(noradId);
        }
    }
    
    deselectSatellite() {
        this.selectedSatellite = null;
        
        // Hide satellite info panel
        document.getElementById('satelliteInfo').style.display = 'none';
        document.getElementById('passInfo').style.display = 'none';
        
        // Update visual selection
        this.updateSatelliteSelection();
        
        // Clear orbit if shown
        this.clearSelectedOrbit();
    }
    
    updateSatelliteSelection() {
        this.satelliteEntities.forEach((entity, noradId) => {
            const isSelected = noradId === this.selectedSatellite;
            
            // Update point appearance
            entity.point.pixelSize = isSelected ? 12 : 8;
            entity.point.outlineWidth = isSelected ? 3 : 2;
            
            // Show/hide label
            entity.label.show = isSelected;
        });
    }
    
    async loadSatelliteDetails(noradId) {
        try {
            const response = await fetch(`/api/satellite/${noradId}`);
            const data = await response.json();
            
            if (data.success) {
                this.renderSatelliteDetails(data.satellite);
            } else {
                this.showError('Failed to load satellite details');
            }
        } catch (error) {
            console.error('Error loading satellite details:', error);
            this.showError('Error loading satellite details');
        }
    }
    
    renderSatelliteDetails(satellite) {
        const container = document.getElementById('satelliteDetails');
        const categoryInfo = this.categories[satellite.category] || { name: 'Unknown', color: '#ffffff' };
        
        container.innerHTML = `
            <div class="satellite-detail-item">
                <span class="detail-label">Name:</span>
                <span class="detail-value">${satellite.name}</span>
            </div>
            <div class="satellite-detail-item">
                <span class="detail-label">NORAD ID:</span>
                <span class="detail-value">${satellite.norad_id}</span>
            </div>
            <div class="satellite-detail-item">
                <span class="detail-label">Category:</span>
                <span class="detail-value">
                    <span class="category-color d-inline-block me-2" style="background-color: ${categoryInfo.color}; width: 10px; height: 10px; border-radius: 50%;"></span>
                    ${categoryInfo.name}
                </span>
            </div>
            <div class="satellite-detail-item">
                <span class="detail-label">Latitude:</span>
                <span class="detail-value">${satellite.current_position.latitude.toFixed(4)}°</span>
            </div>
            <div class="satellite-detail-item">
                <span class="detail-label">Longitude:</span>
                <span class="detail-value">${satellite.current_position.longitude.toFixed(4)}°</span>
            </div>
            <div class="satellite-detail-item">
                <span class="detail-label">Altitude:</span>
                <span class="detail-value">${satellite.current_position.altitude.toFixed(2)} km</span>
            </div>
            <div class="satellite-detail-item">
                <span class="detail-label">Velocity:</span>
                <span class="detail-value">${(satellite.velocity || 0).toFixed(0)} m/s (${((satellite.velocity || 0) * 3.6).toFixed(1)} km/h)</span>
            </div>
            <div class="satellite-detail-item">
                <span class="detail-label">Inclination:</span>
                <span class="detail-value">${satellite.orbital_elements.inclination.toFixed(2)}°</span>
            </div>
            <div class="satellite-detail-item">
                <span class="detail-label">Eccentricity:</span>
                <span class="detail-value">${satellite.orbital_elements.eccentricity.toFixed(6)}</span>
            </div>
            <div class="satellite-detail-item">
                <span class="detail-label">Orbital Period:</span>
                <span class="detail-value">${satellite.orbital_elements.orbital_period.toFixed(2)} min</span>
            </div>
            <div class="satellite-detail-item">
                <span class="detail-label">Mean Motion:</span>
                <span class="detail-value">${satellite.orbital_elements.mean_motion.toFixed(8)} rev/day</span>
            </div>
            <div class="satellite-detail-item">
                <span class="detail-label">TLE Epoch:</span>
                <span class="detail-value">${satellite.tle_data.epoch}</span>
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
        // Clear existing orbit
        this.clearSelectedOrbit();
        
        if (orbitPoints.length < 2) return;
        
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
                material: Cesium.Color.YELLOW,
                clampToGround: false
            }
        });
        
        this.orbitEntities.set(noradId, orbitEntity);
    }
    
    clearSelectedOrbit() {
        if (this.selectedSatellite && this.orbitEntities.has(this.selectedSatellite)) {
            const orbitEntity = this.orbitEntities.get(this.selectedSatellite);
            this.viewer.entities.remove(orbitEntity);
            this.orbitEntities.delete(this.selectedSatellite);
        }
    }
    
    async loadPassPredictions(noradId) {
        try {
            const params = new URLSearchParams({
                lat: this.userLocation.lat,
                lon: this.userLocation.lon,
                alt: this.userLocation.alt
            });
            
            const response = await fetch(`/api/satellite/${noradId}/passes?${params}`);
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
            container.innerHTML = '<p class="text-muted">No visible passes in the next 7 days</p>';
        } else {
            container.innerHTML = passes.map(pass => {
                const riseTime = new Date(pass.rise_time);
                const setTime = new Date(pass.set_time);
                
                return `
                    <div class="pass-item">
                        <div class="pass-time">
                            ${riseTime.toLocaleDateString()} ${riseTime.toLocaleTimeString()}
                        </div>
                        <div class="pass-details">
                            Max Elevation: ${pass.max_elevation ? pass.max_elevation.toFixed(1) : 'N/A'}° | 
                            Duration: ${pass.duration_minutes ? pass.duration_minutes.toFixed(1) : 'N/A'} min
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        document.getElementById('passInfo').style.display = 'block';
    }
    
    searchSatellites(query) {
        const container = document.getElementById('searchResults');
        
        if (!query.trim()) {
            container.innerHTML = '';
            return;
        }
        
        const matchingSatellites = Array.from(this.satellites.values())
            .filter(sat => sat.name.toLowerCase().includes(query.toLowerCase()))
            .slice(0, 10); // Limit to 10 results
        
        if (matchingSatellites.length === 0) {
            container.innerHTML = '<p class="text-muted">No satellites found</p>';
            return;
        }
        
        container.innerHTML = matchingSatellites.map(sat => {
            const categoryInfo = this.categories[sat.category] || { color: '#ffffff' };
            
            return `
                <div class="search-result" data-norad-id="${sat.norad_id}">
                    <div style="display: flex; align-items: center;">
                        <div class="category-color me-2" style="background-color: ${categoryInfo.color};"></div>
                        <span>${sat.name}</span>
                    </div>
                </div>
            `;
        }).join('');
        
        // Add click handlers to search results
        container.querySelectorAll('.search-result').forEach(result => {
            result.addEventListener('click', () => {
                const noradId = parseInt(result.dataset.noradId);
                this.selectSatellite(noradId);
                this.focusOnSatellite(noradId);
                
                // Clear search
                document.getElementById('satelliteSearch').value = '';
                container.innerHTML = '';
            });
        });
    }
    
    focusOnSatellite(noradId) {
        const satellite = this.satellites.get(noradId);
        if (!satellite) return;
        
        this.viewer.camera.flyTo({
            destination: Cesium.Cartesian3.fromDegrees(
                satellite.longitude,
                satellite.latitude,
                satellite.altitude * 1000 + 1000000 // 1000km above satellite
            ),
            duration: 2.0
        });
    }
    
    filterByCategory(category) {
        this.activeCategoryFilter = category;
        this.renderSatellites();
    }
    
    toggleOrbits() {
        this.showOrbits = !this.showOrbits;
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
            destination: Cesium.Cartesian3.fromDegrees(0, 0, 15000000),
            duration: 2.0
        });
    }
    
    refreshData() {
        this.loadSatellites();
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
                    this.showError('Unable to get current location: ' + error.message);
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
            this.showError('Please enter valid coordinates');
            return;
        }
        
        this.userLocation = { lat, lon, alt };
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('locationModal'));
        modal.hide();
        
        // Reload pass predictions for selected satellite
        if (this.selectedSatellite) {
            this.loadPassPredictions(this.selectedSatellite);
        }
    }
    
    startAutoUpdate() {
        // Update satellite positions every 2 seconds for smoother movement
        this.updateInterval = setInterval(() => {
            this.loadSatellites();
        }, 2000);
    }
    
    updateStatus(count, timestamp) {
        const satelliteCountEl = document.getElementById('satelliteCount');
        const lastUpdateEl = document.getElementById('lastUpdate');
        
        if (satelliteCountEl) {
            satelliteCountEl.textContent = `${count} satellites`;
        }
        
        if (lastUpdateEl) {
            const lastUpdateTime = new Date(timestamp);
            lastUpdateEl.textContent = `Last updated: ${lastUpdateTime.toLocaleTimeString()}`;
        }
        
        // Ensure status bar is visible
        const statusBar = document.querySelector('.status-bar');
        if (statusBar) {
            statusBar.style.display = 'flex';
        }
    }
    
    showLoadingOverlay() {
        document.getElementById('loadingOverlay').style.display = 'flex';
    }
    
    hideLoadingOverlay() {
        document.getElementById('loadingOverlay').style.display = 'none';
    }
    
    showError(message) {
        document.getElementById('errorMessage').textContent = message;
        const toast = new bootstrap.Toast(document.getElementById('errorToast'));
        toast.show();
    }
    
    async sendChatMessage() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();
        
        if (!message) return;
        
        // Add user message to chat
        this.addChatMessage(message, 'user');
        input.value = '';
        
        try {
            const response = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.addChatMessage(data.response, 'ai');
            } else {
                this.addChatMessage('Sorry, I encountered an error. Please try again.', 'ai');
            }
        } catch (error) {
            console.error('Chat error:', error);
            this.addChatMessage('Sorry, I\'m having trouble connecting. Please try again.', 'ai');
        }
    }
    
    addChatMessage(message, sender) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}-message`;
        
        const senderName = sender === 'user' ? 'You' : 'AI Assistant';
        messageDiv.innerHTML = `
            <small class="text-muted">${senderName}</small>
            <p>${this.escapeHtml(message)}</p>
        `;
        
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    updateDateFilter() {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        
        this.launchDateFilter = {
            start: startDate ? new Date(startDate) : null,
            end: endDate ? new Date(endDate) : null
        };
        
        this.renderSatellites();
    }

    clearDateFilter() {
        document.getElementById('startDate').value = '';
        document.getElementById('endDate').value = '';
        this.launchDateFilter = { start: null, end: null };
        this.renderSatellites();
    }

    passesDateFilter(satellite) {
        if (!this.launchDateFilter.start && !this.launchDateFilter.end) {
            return true;
        }
        
        if (!satellite.launch_date) {
            return true; // Include satellites without launch date
        }
        
        const launchDate = new Date(satellite.launch_date);
        
        if (this.launchDateFilter.start && launchDate < this.launchDateFilter.start) {
            return false;
        }
        
        if (this.launchDateFilter.end && launchDate > this.launchDateFilter.end) {
            return false;
        }
        
        return true;
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.satelliteViewer = new SatelliteViewer();
});
