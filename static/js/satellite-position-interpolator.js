/**
 * Satellite Position Interpolator
 * Uses cached satellite positions to create smooth, interpolated movement
 */

class SatellitePositionInterpolator {
    constructor(viewer) {
        this.viewer = viewer;
        this.cachedPositions = new Map(); // norad_id -> cached position data
        this.interpolationCallbacks = new Map(); // norad_id -> Cesium.SampledPositionProperty
        this.updateInterval = null;
        this.isRunning = false;
    }

    /**
     * Start the interpolation system
     */
    start() {
        if (this.isRunning) return;
        
        console.log('🎬 Starting position interpolation system...');
        this.isRunning = true;
        
        // Fetch cached positions every 5 seconds for better sync
        this.updateCachedPositions();
        this.updateInterval = setInterval(() => {
            this.updateCachedPositions();
        }, 5000);
    }

    /**
     * Stop the interpolation system
     */
    stop() {
        if (!this.isRunning) return;
        
        console.log('⏹️ Stopping position interpolation system...');
        this.isRunning = false;
        
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }

    /**
     * Fetch cached positions from backend for priority satellites
     */
    async updateCachedPositions() {
        try {
            console.log('📥 Fetching cached position data...');
            
            // Get cache status to see which satellites are cached
            const statusResponse = await fetch('/api/position-cache/status');
            if (!statusResponse.ok) {
                console.warn('Cache status not available, falling back to real-time positions');
                return;
            }

            const statusData = await statusResponse.json();
            if (!statusData.success) {
                console.warn('Cache not ready:', statusData);
                return;
            }

            console.log('📊 Cache status:', statusData);

            // For now, we'll enhance the regular API with interpolation hints
            // In the future, we can fetch full cached trajectories for priority satellites
            
        } catch (error) {
            console.error('Error fetching cached positions:', error);
        }
    }

    /**
     * Create a Cesium SampledPositionProperty for smooth interpolation
     */
    createInterpolatedPosition(noradId, cachedData) {
        const sampledPosition = new Cesium.SampledPositionProperty();
        sampledPosition.setInterpolationOptions({
            interpolationDegree: 5,
            interpolationAlgorithm: Cesium.LagrangePolynomialApproximation
        });

        // Add all cached positions as samples
        cachedData.timestamps.forEach((timestamp, index) => {
            const julianDate = Cesium.JulianDate.fromIso8601(timestamp);
            const position = Cesium.Cartesian3.fromDegrees(
                cachedData.longitudes[index],
                cachedData.latitudes[index],
                cachedData.altitudes[index] * 1000 // Convert km to meters
            );
            sampledPosition.addSample(julianDate, position);
        });

        this.interpolationCallbacks.set(noradId, sampledPosition);
        return sampledPosition;
    }

    /**
     * Get interpolated position callback for a satellite
     */
    getPositionCallback(noradId) {
        return this.interpolationCallbacks.get(noradId);
    }

    /**
     * Check if satellite has cached positions available
     */
    hasCachedPositions(noradId) {
        return this.cachedPositions.has(noradId);
    }

    /**
     * Request on-demand caching for a specific satellite
     */
    async requestCaching(noradId, durationHours = 24) {
        try {
            console.log(`📦 Requesting on-demand cache for satellite ${noradId}...`);
            
            const response = await fetch(`/api/position-cache/on-demand/${noradId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    duration_hours: durationHours
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log(`✅ On-demand cache created for satellite ${noradId}:`, data);
            return data.success;
            
        } catch (error) {
            console.error(`Error requesting cache for satellite ${noradId}:`, error);
            return false;
        }
    }

    /**
     * Linear interpolation between two positions
     */
    static interpolatePosition(pos1, pos2, fraction) {
        return {
            latitude: pos1.latitude + (pos2.latitude - pos1.latitude) * fraction,
            longitude: pos1.longitude + (pos2.longitude - pos1.longitude) * fraction,
            altitude: pos1.altitude + (pos2.altitude - pos1.altitude) * fraction
        };
    }

    /**
     * Get smoothly interpolated position at current time
     */
    getInterpolatedPosition(satellite, currentTime) {
        if (!satellite.previousPosition || !satellite.lastUpdateTime) {
            return {
                latitude: satellite.latitude,
                longitude: satellite.longitude,
                altitude: satellite.altitude
            };
        }

        // Calculate time elapsed since last update
        const timeSinceUpdate = currentTime - satellite.lastUpdateTime;
        const updateInterval = 30000; // 30 seconds between updates
        
        // Calculate interpolation fraction (0 to 1)
        const fraction = Math.min(timeSinceUpdate / updateInterval, 1);

        // Smooth easing function (ease-in-out)
        const easedFraction = fraction < 0.5 
            ? 2 * fraction * fraction 
            : 1 - Math.pow(-2 * fraction + 2, 2) / 2;

        return SatellitePositionInterpolator.interpolatePosition(
            satellite.previousPosition,
            {
                latitude: satellite.latitude,
                longitude: satellite.longitude,
                altitude: satellite.altitude
            },
            easedFraction
        );
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SatellitePositionInterpolator;
}
