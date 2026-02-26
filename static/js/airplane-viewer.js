
/**
 * Airplane Viewer Module - Dedicated airplane tracking and visualization
 * Separated from satellite functionality for better organization
 */

class AirplaneViewer {
    constructor(viewer) {
        this.viewer = viewer;
        this.airplanes = new Map();
        this.airplaneEntities = new Map();
        this.selectedAirplane = null;
        this.airplaneTrackingInterval = null;
        this.realTimeAirplaneUpdateInterval = null;
        this.autoRefreshInterval = null;
        this.lastUpdate = null;
        this.isLoading = false;

        console.log('✈️ Airplane Viewer initialized');
    }

    async loadAirplanes() {
        if (!this.viewer) {
            console.warn('❌ Viewer not ready for airplane loading');
            return;
        }

        // Prevent duplicate loading requests
        if (this.isLoading) {
            console.log('✈️ Already loading airplanes, skipping duplicate request');
            return;
        }

        console.log('✈️ Loading airplanes from API...');
        this.isLoading = true;
        this.showLoadingIndicator();

        try {
            const response = await fetch('/api/airplanes', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();
            console.log('✈️ API Response:', {
                success: data.success,
                airplaneCount: data.airplane_count,
                cached: data.cached,
                hasData: data.airplanes && data.airplanes.length > 0
            });

            if (data.success && data.airplanes && data.airplanes.length > 0) {
                // Update airplane data efficiently
                const newAirplanes = new Map();
                let validCount = 0;

                for (const airplane of data.airplanes) {
                    // Quick validation
                    if (airplane.icao24 &&
                        typeof airplane.latitude === 'number' &&
                        typeof airplane.longitude === 'number' &&
                        !isNaN(airplane.latitude) &&
                        !isNaN(airplane.longitude)) {
                        newAirplanes.set(airplane.icao24, airplane);
                        validCount++;
                    }
                }

                this.airplanes = newAirplanes;
                this.lastUpdate = new Date();
                console.log(`✅ Loaded ${validCount} valid airplanes`);

                // Batch render for better performance
                this.renderAirplanes();
                this.updateStatus(validCount, data.timestamp);
                this.updateConnectionStatus('Connected', 'success');

                const countElement = document.getElementById('count');
                if (countElement) {
                    countElement.textContent = validCount;
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
            this.isLoading = false;
            this.hideLoadingIndicator();
        }
    }

    renderAirplanes() {
        if (!this.viewer || !this.viewer.entities) {
            console.warn('❌ Viewer not ready for airplane rendering');
            return;
        }

        console.log(`✈️ Rendering ${this.airplanes.size} airplanes`);

        // Clear existing airplane entities efficiently
        this.clearAirplaneEntities();

        // Suspend entity collection notifications for batch operations
        this.viewer.entities.suspendEvents();

        let entityCount = 0;
        const batchSize = 1000; // Process in batches for better performance

        try {
            // Convert to array for batch processing
            const airplanesArray = Array.from(this.airplanes.entries());

            for (let i = 0; i < airplanesArray.length; i += batchSize) {
                const batch = airplanesArray.slice(i, i + batchSize);

                batch.forEach(([icao24, airplane]) => {
                    // Quick validation
                    if (!airplane.latitude || !airplane.longitude ||
                        isNaN(airplane.latitude) || isNaN(airplane.longitude)) {
                        return;
                    }

                    // Ensure altitude is valid
                    const altitude = airplane.altitude_meters || 10000;
                    if (altitude < -500 || altitude > 60000) { // More reasonable bounds
                        return;
                    }

                    // Determine airplane color based on status
                    let color = Cesium.Color.ORANGE; // Default flying color
                    if (airplane.on_ground) {
                        color = Cesium.Color.GRAY;
                    } else if (airplane.velocity > 200) {
                        color = Cesium.Color.LIME;
                    } else if (airplane.velocity < 50) {
                        color = Cesium.Color.YELLOW;
                    }

                    // Optimized callsign handling
                    const displayName = (airplane.callsign && airplane.callsign.trim()) ||
                        `Aircraft ${icao24.toUpperCase()}`;

                    const entity = this.viewer.entities.add({
                        id: `airplane_${icao24}`,
                        name: displayName,
                        position: Cesium.Cartesian3.fromDegrees(
                            airplane.longitude,
                            airplane.latitude,
                            altitude
                        ),
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
                            font: '9pt Arial',
                            fillColor: color,
                            outlineColor: Cesium.Color.BLACK,
                            outlineWidth: 1,
                            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                            pixelOffset: new Cesium.Cartesian2(0, -15),
                            show: false, // Only show when selected
                            scaleByDistance: new Cesium.NearFarScalar(1.0e5, 1.0, 1.0e6, 0.3)
                        },
                        airplaneData: airplane
                    });

                    this.airplaneEntities.set(icao24, entity);
                    entityCount++;
                });

                // Continue processing batches synchronously
                // (async batching removed - 1ms delay was negligible)
            }
        } finally {
            // Resume entity collection notifications
            this.viewer.entities.resumeEvents();
        }

        console.log(`✈️ Created ${entityCount} airplane entities`);
        this.viewer.scene.requestRender();
    }

    clearAirplaneEntities() {
        if (this.airplaneEntities.size === 0) return;

        // Suspend events for batch removal
        this.viewer.entities.suspendEvents();

        try {
            this.airplaneEntities.forEach(entity => {
                this.viewer.entities.remove(entity);
            });
            this.airplaneEntities.clear();
        } finally {
            this.viewer.entities.resumeEvents();
        }

        console.log('✈️ Cleared airplane entities');
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

        // Load detailed information
        this.renderAirplaneDetails(airplane);

        // Start real-time updates for airplane details
        this.startRealTimeAirplaneUpdates(icao24);

        const displayName = airplane.callsign && airplane.callsign.trim() && airplane.callsign.trim() !== ''
            ? airplane.callsign.trim()
            : `Aircraft ${icao24.toUpperCase()}`;

        console.log(`✅ Selected airplane: ${displayName}`);
    }

    deselectAirplane() {
        if (!this.selectedAirplane) return;

        console.log(`✈️ Deselecting airplane: ${this.selectedAirplane}`);
        this.selectedAirplane = null;

        // Close details panel
        if (typeof window.closeDetailsPanel === 'function') {
            window.closeDetailsPanel();
        }

        // Update airplane selection visuals
        this.updateAirplaneSelection();

        // Stop any real-time updates
        this.stopRealTimeAirplaneUpdates();
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
        const detailsPanel = document.getElementById('detailsPanel');
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
    }

    startRealTimeAirplaneUpdates(icao24) {
        this.stopRealTimeAirplaneUpdates();

        this.realTimeAirplaneUpdateInterval = setInterval(async () => {
            try {
                // Only update if airplane is still selected
                if (this.selectedAirplane !== icao24) {
                    this.stopRealTimeAirplaneUpdates();
                    return;
                }

                const response = await fetch(`/api/airplane/${icao24}`, {
                    method: 'GET',
                    headers: { 'Content-Type': 'application/json' }
                });

                if (!response.ok) {
                    console.warn(`API error for airplane ${icao24}: ${response.status}`);
                    return;
                }

                const data = await response.json();

                if (data.success && data.airplane) {
                    // Update airplane data efficiently
                    const airplaneData = data.airplane;

                    const updatedAirplane = {
                        icao24: airplaneData.aircraft.icao24,
                        callsign: airplaneData.aircraft.callsign,
                        origin_country: airplaneData.aircraft.origin_country,
                        latitude: airplaneData.position.latitude,
                        longitude: airplaneData.position.longitude,
                        altitude_meters: airplaneData.position.altitude_meters,
                        on_ground: airplaneData.position.on_ground,
                        velocity: airplaneData.flight.velocity_ms,
                        true_track: airplaneData.flight.true_track,
                        heading: airplaneData.flight.true_track,
                        vertical_rate: airplaneData.flight.vertical_rate_ms,
                        squawk: airplaneData.aircraft.squawk
                    };

                    this.airplanes.set(icao24, updatedAirplane);

                    // Only update details if panel is visible
                    const detailsPanel = document.getElementById('detailsPanel');
                    if (detailsPanel && detailsPanel.style.display !== 'none') {
                        this.renderAirplaneDetails(updatedAirplane);
                    }

                    // Update entity position efficiently
                    const entity = this.airplaneEntities.get(icao24);
                    if (entity && entity.position) {
                        entity.position = Cesium.Cartesian3.fromDegrees(
                            updatedAirplane.longitude,
                            updatedAirplane.latitude,
                            updatedAirplane.altitude_meters
                        );
                    }
                }
            } catch (error) {
                console.warn('Error updating airplane details:', error);
            }
        }, 10000); // Reduced to 10 seconds for better balance
    }

    stopRealTimeAirplaneUpdates() {
        if (this.realTimeAirplaneUpdateInterval) {
            clearInterval(this.realTimeAirplaneUpdateInterval);
            this.realTimeAirplaneUpdateInterval = null;
        }
    }

    clearAirplaneVisualizations(icao24) {
        // Stop any airplane-specific tracking or updates
        if (this.airplaneTrackingInterval) {
            clearInterval(this.airplaneTrackingInterval);
            this.airplaneTrackingInterval = null;
        }
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

    searchAirplanes(query) {
        const matchingAirplanes = Array.from(this.airplanes.values())
            .filter(airplane =>
                airplane.callsign.toLowerCase().includes(query.toLowerCase()) ||
                airplane.icao24.toLowerCase().includes(query.toLowerCase()) ||
                airplane.origin_country.toLowerCase().includes(query.toLowerCase())
            )
            .slice(0, 10); // Limit to 10 results

        return matchingAirplanes;
    }

    updateStatus(count, timestamp) {
        this.lastUpdate = timestamp;

        const timestampElement = document.getElementById('lastUpdate');
        if (timestampElement && timestamp) {
            const date = new Date(timestamp);
            timestampElement.textContent = date.toLocaleTimeString();
        }
    }

    updateConnectionStatus(text, type) {
        const statusElement = document.getElementById('connectionStatus');
        if (statusElement) {
            statusElement.textContent = text;
            statusElement.className = `badge bg-${type}`;
        }
    }

    showLoadingIndicator() {
        const loadingElement = document.getElementById('loadingIndicator');
        if (loadingElement) {
            loadingElement.style.display = 'block';
        }
    }

    hideLoadingIndicator() {
        const loadingElement = document.getElementById('loadingIndicator');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }

    showError(message) {
        console.error('Airplane Viewer Error:', message);
        // Could show a toast notification or other UI feedback here
    }

    // Auto-refresh airplanes periodically with better caching
    startAutoRefresh(intervalMs = 45000) { // Optimized to 45 seconds
        this.stopAutoRefresh(); // Ensure no duplicate intervals

        this.autoRefreshInterval = setInterval(() => {
            // Only refresh if no airplane is selected to avoid interruptions
            if (!this.selectedAirplane) {
                const now = Date.now();
                const timeSinceUpdate = this.lastUpdate ? (now - this.lastUpdate.getTime()) : Infinity;

                // Only refresh if data is older than 40 seconds
                if (timeSinceUpdate > 40000) {
                    console.log('✈️ Auto-refreshing airplane data after', Math.round(timeSinceUpdate / 1000), 'seconds');
                    this.loadAirplanes();
                } else {
                    console.log('✈️ Skipping auto-refresh, data is recent');
                }
            } else {
                console.log('✈️ Skipping auto-refresh, airplane selected');
            }
        }, intervalMs);
    }

    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        }
    }

    destroy() {
        this.stopRealTimeAirplaneUpdates();
        this.stopAutoRefresh();
        this.clearAirplaneEntities();
        this.airplanes.clear();
        console.log('✈️ Airplane Viewer destroyed');
    }
}

// Export for use in other modules
window.AirplaneViewer = AirplaneViewer;
