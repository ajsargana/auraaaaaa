
// Web Worker for satellite pass calculations
// This runs in a separate thread to avoid blocking the main UI

class PassCalculationWorker {
    constructor() {
        this.satellites = [];
        this.userLocation = { lat: 0, lon: 0, alt: 0 };
        self.onmessage = this.handleMessage.bind(this);
    }

    handleMessage(event) {
        const { type, data } = event.data;
        
        switch (type) {
            case 'INIT':
                this.initialize(data);
                break;
            case 'CALCULATE_PASSES':
                this.calculatePasses(data);
                break;
            case 'FILTER_SATELLITES':
                this.filterSatellites(data);
                break;
            case 'BATCH_PROCESS':
                this.batchProcess(data);
                break;
            default:
                this.postMessage({ type: 'ERROR', error: `Unknown message type: ${type}` });
        }
    }

    initialize(data) {
        this.satellites = data.satellites || [];
        this.userLocation = data.userLocation || { lat: 0, lon: 0, alt: 0 };
        
        this.postMessage({
            type: 'INITIALIZED',
            satelliteCount: this.satellites.length,
            location: this.userLocation
        });
    }

    async calculatePasses(data) {
        const { timeFilter, batchSize = 50 } = data;
        
        try {
            this.postMessage({ 
                type: 'PROGRESS', 
                message: `Starting pass calculations for ${this.satellites.length} satellites...`,
                progress: 0
            });

            const results = [];
            let processedCount = 0;
            
            // Process satellites in batches to avoid overwhelming the API
            for (let i = 0; i < this.satellites.length; i += batchSize) {
                const batch = this.satellites.slice(i, i + batchSize);
                
                // Process batch with parallel requests for speed
                const batchPromises = batch.map(satellite => 
                    this.fetchSatellitePassData(satellite, timeFilter)
                );
                
                try {
                    const batchResults = await Promise.allSettled(batchPromises);
                    
                    // Process results
                    for (const result of batchResults) {
                        if (result.status === 'fulfilled' && result.value) {
                            results.push(result.value);
                        }
                    }
                    
                    processedCount += batch.length;
                    const progress = Math.round((processedCount / this.satellites.length) * 100);
                    
                    this.postMessage({
                        type: 'PROGRESS',
                        message: `Processed ${processedCount}/${this.satellites.length} satellites...`,
                        progress: progress,
                        intermediate_results: results.slice(-batch.length) // Send latest batch results
                    });
                    
                    // Small delay to prevent overwhelming the server
                    await this.sleep(100);
                    
                } catch (batchError) {
                    console.error('Batch processing error:', batchError);
                    processedCount += batch.length; // Continue with next batch
                }
            }
            
            // Sort results by next pass time
            results.sort((a, b) => {
                if (!a.next_pass || !b.next_pass) return 0;
                return new Date(a.next_pass.rise_time) - new Date(b.next_pass.rise_time);
            });
            
            this.postMessage({
                type: 'CALCULATION_COMPLETE',
                results: results,
                totalPasses: results.reduce((sum, sat) => sum + (sat.passes ? sat.passes.length : 0), 0),
                processedSatellites: processedCount
            });
            
        } catch (error) {
            this.postMessage({
                type: 'ERROR',
                error: `Calculation failed: ${error.message}`
            });
        }
    }

    async fetchSatellitePassData(satellite, timeFilter) {
        try {
            const url = `/api/satellite/${satellite.norad_id}/passes?lat=${this.userLocation.lat}&lon=${this.userLocation.lon}&alt=${this.userLocation.alt}&time_offset=0`;
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.passes && data.passes.length > 0) {
                // Filter passes by time if needed
                let filteredPasses = data.passes;
                if (timeFilter && timeFilter !== 'all') {
                    const timeFilterHours = parseInt(timeFilter);
                    const cutoffTime = new Date(Date.now() + timeFilterHours * 60 * 60 * 1000);
                    
                    filteredPasses = data.passes.filter(pass => {
                        const passTime = new Date(pass.rise_time);
                        return passTime <= cutoffTime;
                    });
                }
                
                if (filteredPasses.length > 0) {
                    return {
                        satellite_id: satellite.norad_id,
                        satellite_name: satellite.name,
                        satellite_category: satellite.category,
                        satellite_color: satellite.color,
                        passes: filteredPasses,
                        next_pass: filteredPasses[0],
                        is_earth_observation: data.is_earth_observation || false,
                        fov_info: data.fov_info || null
                    };
                }
            }
            
            return null;
            
        } catch (error) {
            // Return null for failed requests - don't stop the whole process
            return null;
        }
    }

    filterSatellites(data) {
        const { filters } = data;
        let filteredSatellites = [...this.satellites];
        
        // Apply category filter
        if (filters.category && filters.category !== 'all') {
            filteredSatellites = filteredSatellites.filter(sat => 
                sat.category === filters.category
            );
        }
        
        // Apply altitude filter
        if (filters.minAltitude !== undefined) {
            filteredSatellites = filteredSatellites.filter(sat => 
                sat.altitude >= filters.minAltitude
            );
        }
        
        if (filters.maxAltitude !== undefined) {
            filteredSatellites = filteredSatellites.filter(sat => 
                sat.altitude <= filters.maxAltitude
            );
        }
        
        // Apply name search
        if (filters.searchQuery) {
            const query = filters.searchQuery.toLowerCase();
            filteredSatellites = filteredSatellites.filter(sat => 
                sat.name.toLowerCase().includes(query)
            );
        }
        
        this.postMessage({
            type: 'FILTER_COMPLETE',
            filteredSatellites: filteredSatellites,
            originalCount: this.satellites.length,
            filteredCount: filteredSatellites.length
        });
    }

    async batchProcess(data) {
        const { operation, params } = data;
        
        switch (operation) {
            case 'ORBITAL_ANALYSIS':
                await this.performOrbitalAnalysis(params);
                break;
            case 'COLLISION_DETECTION':
                await this.performCollisionDetection(params);
                break;
            case 'VISIBILITY_ANALYSIS':
                await this.performVisibilityAnalysis(params);
                break;
            default:
                this.postMessage({ 
                    type: 'ERROR', 
                    error: `Unknown batch operation: ${operation}` 
                });
        }
    }

    async performOrbitalAnalysis(params) {
        // Analyze orbital characteristics of satellites
        const results = [];
        
        for (let i = 0; i < this.satellites.length; i++) {
            const satellite = this.satellites[i];
            
            // Classify orbit type based on altitude
            let orbitType = 'Unknown';
            if (satellite.altitude < 2000) {
                orbitType = 'LEO (Low Earth Orbit)';
            } else if (satellite.altitude < 20000) {
                orbitType = 'MEO (Medium Earth Orbit)';
            } else if (satellite.altitude >= 35686 && satellite.altitude <= 35886) {
                orbitType = 'GEO (Geostationary Orbit)';
            } else {
                orbitType = 'HEO (High Earth Orbit)';
            }
            
            results.push({
                norad_id: satellite.norad_id,
                name: satellite.name,
                altitude: satellite.altitude,
                orbit_type: orbitType,
                category: satellite.category
            });
            
            // Report progress every 100 satellites
            if (i % 100 === 0) {
                this.postMessage({
                    type: 'BATCH_PROGRESS',
                    operation: 'ORBITAL_ANALYSIS',
                    progress: Math.round((i / this.satellites.length) * 100),
                    processed: i
                });
            }
        }
        
        this.postMessage({
            type: 'BATCH_COMPLETE',
            operation: 'ORBITAL_ANALYSIS',
            results: results
        });
    }

    async performVisibilityAnalysis(params) {
        // Analyze which satellites are currently visible from user location
        const results = [];
        const { elevationThreshold = 10 } = params;
        
        for (let i = 0; i < this.satellites.length; i++) {
            const satellite = this.satellites[i];
            
            // Simple visibility calculation based on distance and angle
            const distance = this.calculateDistance(
                this.userLocation.lat, 
                this.userLocation.lon,
                satellite.latitude,
                satellite.longitude
            );
            
            // Rough elevation calculation
            const earthRadius = 6371; // km
            const elevationAngle = Math.atan2(
                satellite.altitude,
                distance
            ) * (180 / Math.PI);
            
            if (elevationAngle >= elevationThreshold) {
                results.push({
                    norad_id: satellite.norad_id,
                    name: satellite.name,
                    elevation_angle: Math.round(elevationAngle * 10) / 10,
                    distance: Math.round(distance),
                    altitude: satellite.altitude,
                    category: satellite.category
                });
            }
            
            // Report progress
            if (i % 50 === 0) {
                this.postMessage({
                    type: 'BATCH_PROGRESS',
                    operation: 'VISIBILITY_ANALYSIS',
                    progress: Math.round((i / this.satellites.length) * 100),
                    processed: i
                });
            }
        }
        
        // Sort by elevation angle (highest first)
        results.sort((a, b) => b.elevation_angle - a.elevation_angle);
        
        this.postMessage({
            type: 'BATCH_COMPLETE',
            operation: 'VISIBILITY_ANALYSIS',
            results: results
        });
    }

    calculateDistance(lat1, lon1, lat2, lon2) {
        const R = 6371; // Earth's radius in kilometers
        const dLat = this.toRadians(lat2 - lat1);
        const dLon = this.toRadians(lon2 - lon1);
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(this.toRadians(lat1)) * Math.cos(this.toRadians(lat2)) * 
                  Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
    }

    toRadians(degrees) {
        return degrees * (Math.PI / 180);
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    postMessage(message) {
        self.postMessage(message);
    }
}

// Initialize the worker
new PassCalculationWorker();
