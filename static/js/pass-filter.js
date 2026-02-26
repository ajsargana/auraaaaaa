class PassFilter {
    constructor(satelliteViewer) {
        this.satelliteViewer = satelliteViewer;
        this.loadingMessageInterval = null;
        this.showingPastPasses = false;
        this.pastPassesData = [];
        // Cache the marker coordinates to prevent drift
        this.cachedMarkerCoordinates = null;

        // Web Worker for pass calculations
        this.worker = null;
        this.isWorkerSupported = typeof Worker !== 'undefined';
        this.initializeWorker();

        // Multi-threading configuration
        this.batchSize = 25; // Reduced batch size for faster updates

        console.log('🔧 PassFilter initialized with web worker support:', this.isWorkerSupported);
    }

    initializeWorker() {
        if (!this.isWorkerSupported) {
            console.warn('⚠️ Web Workers not supported, falling back to main thread');
            return;
        }

        try {
            this.worker = new Worker('/static/js/pass-calculation-worker.js');

            this.worker.onmessage = (event) => {
                this.handleWorkerMessage(event.data);
            };

            this.worker.onerror = (error) => {
                console.error('❌ Worker error:', error);
                this.worker = null;
                this.isWorkerSupported = false;
            };

            console.log('✅ Web worker initialized successfully');
        } catch (error) {
            console.error('❌ Failed to initialize web worker:', error);
            this.worker = null;
            this.isWorkerSupported = false;
        }
    }

    handleWorkerMessage(data) {
        const { type } = data;

        switch (type) {
            case 'INITIALIZED':
                console.log('✅ Worker initialized with', data.satelliteCount, 'satellites');
                break;

            case 'PROGRESS':
                this.updateStatus(data.message, data.progress);

                // Handle intermediate results for real-time updates
                if (data.intermediate_results && data.intermediate_results.length > 0) {
                    this.addIntermediateResults(data.intermediate_results);
                }
                break;

            case 'CALCULATION_COMPLETE':
                this.handleCalculationComplete(data);
                break;

            case 'FILTER_COMPLETE':
                this.handleFilterComplete(data);
                break;

            case 'BATCH_COMPLETE':
                this.handleBatchComplete(data);
                break;

            case 'ERROR':
                console.error('❌ Worker error:', data.error);
                this.updateStatus(data.error, 0, 'danger');
                break;
        }
    }

    // Method to extract and cache marker coordinates
    extractAndCacheMarkerCoordinates() {
        // Check multiple possible location marker properties
        let locationMarker = null;
        if (this.satelliteViewer.locationMarker) {
            locationMarker = this.satelliteViewer.locationMarker;
        } else if (this.satelliteViewer.userLocationMarker) {
            locationMarker = this.satelliteViewer.userLocationMarker;
        }

        // Extract coordinates from location marker ONLY
        if (locationMarker && locationMarker.position) {
            const position = locationMarker.position;
            if (position) {
                try {
                    // Handle both ConstantProperty and direct Cartesian3
                    let cartographic;
                    if (position.getValue && typeof position.getValue === 'function') {
                        // It's a Property (like ConstantProperty)
                        const cartesian = position.getValue(Cesium.JulianDate.now());
                        if (cartesian) {
                            cartographic = Cesium.Cartographic.fromCartesian(cartesian);
                        }
                    } else if (position.x !== undefined && position.y !== undefined && position.z !== undefined) {
                        // It's a direct Cartesian3
                        cartographic = Cesium.Cartographic.fromCartesian(position);
                    }

                    if (cartographic) {
                        const lat = Cesium.Math.toDegrees(cartographic.latitude);
                        const lon = Cesium.Math.toDegrees(cartographic.longitude);
                        const alt = cartographic.height || 0;

                        // Validate coordinates are reasonable
                        if (Math.abs(lat) <= 90 && Math.abs(lon) <= 180) {
                            this.cachedMarkerCoordinates = {
                                lat: lat,
                                lon: lon,
                                alt: alt,
                                timestamp: Date.now()
                            };
                            console.log(`🎯 Cached marker coordinates: (${lat.toFixed(6)}, ${lon.toFixed(6)})`);
                            return this.cachedMarkerCoordinates;
                        } else {
                            console.warn('⚠️ Invalid coordinates from marker:', lat, lon);
                        }
                    }
                } catch (error) {
                    console.error('❌ Error extracting marker coordinates:', error);
                }
            }
        }

        return null;
    }

    // Method to get reliable marker coordinates
    getMarkerCoordinates() {
        // First try to extract fresh coordinates
        const freshCoords = this.extractAndCacheMarkerCoordinates();
        if (freshCoords) {
            return freshCoords;
        }

        // If fresh extraction failed, use cached coordinates if they're recent (within 5 minutes)
        if (this.cachedMarkerCoordinates) {
            const age = Date.now() - this.cachedMarkerCoordinates.timestamp;
            if (age < 5 * 60 * 1000) { // 5 minutes
                console.log(`🔄 Using cached marker coordinates (${age/1000}s old)`);
                return this.cachedMarkerCoordinates;
            } else {
                console.log('⏰ Cached coordinates too old, clearing cache');
                this.cachedMarkerCoordinates = null;
            }
        }

        return null;
    }

    async applyTimeBasedPassFilter() {
        const timeFilter = document.getElementById('timeFilterSelect').value;
        if (!timeFilter) return;

        console.log(`🚀 Applying ${timeFilter}hr pass filter with${this.isWorkerSupported ? '' : 'out'} web worker`);

        // Validate user location
        const userLat = this.satelliteViewer.userLocation.lat;
        const userLon = this.satelliteViewer.userLocation.lon;

        if (!userLat && !userLon) {
            this.updateStatus('Please set your location first', 0, 'warning');
            return;
        }

        this.isRunning = true;
        this.processedCount = 0;
        this.totalPasses = 0;
        this.currentResults = [];
        this.satellites = this.satelliteViewer.satellites ? Array.from(this.satelliteViewer.satellites.values()) : [];

        // Disable apply button during calculation
        document.getElementById('applyPassFilterBtn').disabled = true;

        // Clear previous results
        document.getElementById('passesContainer').innerHTML = '<div class="text-center py-4"><div class="loading-spinner"></div><p>Initializing calculations...</p></div>';

        try {
            if (this.isWorkerSupported && this.worker) {
                await this.processWithWebWorker(timeFilter);
            } else {
                await this.processWithMainThread(timeFilter);
            }
        } catch (error) {
            console.error('❌ Error in pass filter:', error);
            this.updateStatus('Error occurred during calculation', 0, 'danger');
        } finally {
            this.isRunning = false;
            document.getElementById('applyPassFilterBtn').disabled = false;
        }
    }

    async processWithWebWorker(timeFilter) {
        // Initialize worker with satellite data and location
        this.worker.postMessage({
            type: 'INIT',
            data: {
                satellites: this.satellites,
                userLocation: this.satelliteViewer.userLocation
            }
        });

        // Start calculation in worker
        this.worker.postMessage({
            type: 'CALCULATE_PASSES',
            data: {
                timeFilter: timeFilter,
                batchSize: this.batchSize
            }
        });
    }

    async processWithMainThread(timeFilter) {
        console.log('🔧 Processing with main thread (no web worker)');
        await this.processAllSatellites();
    }

    addIntermediateResults(results) {
        // Add results incrementally for real-time updates
        for (const result of results) {
            if (result && result.passes && result.passes.length > 0) {
                this.currentResults.push(result);
                this.totalPasses += result.passes.length;
            }
        }

        // Update display with latest results
        this.displayResults(this.currentResults);
        this.updateTotalPassesCount();
    }

    handleCalculationComplete(data) {
        console.log('✅ Worker calculation complete:', data.totalPasses, 'passes found');

        this.currentResults = data.results || [];
        this.totalPasses = data.totalPasses || 0;
        this.processedCount = data.processedSatellites || 0;

        this.displayResults(this.currentResults);
        this.updateStatus('Calculation complete!', 100);
        this.updateTotalPassesCount();
    }

    handleFilterComplete(data) {
        console.log('✅ Worker filter complete:', data.filteredCount, 'satellites');
        // Handle filtered satellite results
    }

    handleBatchComplete(data) {
        console.log('✅ Worker batch operation complete:', data.operation);
        // Handle batch operation results
    }

    // Placeholder for the actual processing of all satellites
    async processAllSatellites() {
        // This function should be implemented to handle calculations directly in the main thread
        // when web workers are not available or not used.
        // For now, it can just update the status.
        this.updateStatus('Processing calculations...', 50);
        // Simulate some work
        await new Promise(resolve => setTimeout(resolve, 1000));
        this.updateStatus('Calculations finished.', 100);

        // Fetch data using the API directly
        const timeFilter = document.getElementById('timeFilterSelect').value;
        const markerCoords = this.getMarkerCoordinates();

        if (!markerCoords) {
            alert('Please set your location marker on the map first to calculate satellite passes.');
            return;
        }

        const { lat: targetLat, lon: targetLon, alt: targetAlt } = markerCoords;

        try {
            this.showCreativePassLoadingMessages(timeFilter);
            const response = await fetch(`/api/satellites/passes-filter?lat=${targetLat}&lon=${targetLon}&alt=${targetAlt}&time_filter=${timeFilter}`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            this.hideCreativePassLoadingMessages();

            if (data.success && data.satellites_with_passes) {
                this.displayPassFilterResults(data.satellites_with_passes, timeFilter);
                this.filterSatellitesByPassResults(data.satellites_with_passes);
                console.log(`✅ Found ${data.satellites_with_passes.length} satellites with passes in ${timeFilter}hr window for MARKER LOCATION`);
            } else {
                console.error('❌ Failed to get pass filter results:', data);
                this.showPassFilterError('Failed to calculate satellite passes. This could be due to high orbital activity or network issues. Please try again.');
            }
        } catch (error) {
            console.error('💥 Error applying pass filter:', error);
            this.hideCreativePassLoadingMessages();
            this.showPassFilterError(`Network error: ${error.message}. Please check your connection and try again.`);
        }
    }

    updateStatus(message, progress, type = 'info') {
        const progressBar = document.getElementById('calculationProgressBar');
        const statusMessage = document.getElementById('statusMessage');

        if (progressBar) {
            progressBar.style.width = `${progress}%`;
            progressBar.setAttribute('aria-valuenow', progress);
            progressBar.classList.remove('bg-info', 'bg-warning', 'bg-danger', 'bg-success');
            switch (type) {
                case 'warning':
                    progressBar.classList.add('bg-warning');
                    break;
                case 'danger':
                    progressBar.classList.add('bg-danger');
                    break;
                case 'success':
                    progressBar.classList.add('bg-success');
                    break;
                default:
                    progressBar.classList.add('bg-info');
            }
        }

        if (statusMessage) {
            statusMessage.textContent = message;
        }
    }

    updateTotalPassesCount() {
        const totalPassesElement = document.getElementById('totalPassesCount');
        if (totalPassesElement) {
            totalPassesElement.textContent = this.totalPasses;
        }
    }

    displayResults(results) {
        const container = document.getElementById('passesContainer');
        if (!container) return;

        // Clear previous results
        container.innerHTML = '';

        if (results.length === 0) {
            container.innerHTML = '<p class="text-center py-4">No passes found for the selected criteria.</p>';
            return;
        }

        results.forEach(result => {
            if (!result.passes || result.passes.length === 0) return;

            const satelliteElement = document.createElement('div');
            satelliteElement.className = 'satellite-passes mb-4 p-3 rounded';
            satelliteElement.style.cssText = `background-color: rgba(255, 255, 255, 0.03); border-left: 5px solid ${this.getPassColor(result.satellite_info.type)};`;

            let passesHtml = `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h5 class="text-primary mb-0">
                        <i class="fas fa-satellite me-2"></i>${result.satellite_info.name} <span class="badge bg-secondary">${result.satellite_info.norad_id}</span>
                    </h5>
                    <span class="badge bg-info">${result.satellite_info.type}</span>
                </div>
                <p class="text-muted mb-3" style="font-size: 0.9em;">
                    <i class="fas fa-map-marker-alt me-1"></i>Location: ${result.satellite_info.last_location || 'N/A'}
                </p>
                <div class="passes-list">
            `;

            result.passes.forEach(pass => {
                const riseTime = new Date(pass.rise_time);
                const setTime = new Date(pass.set_time);
                const maxTime = new Date(pass.culmination_time);
                const isHighElevation = pass.max_elevation > 30;

                passesHtml += `
                    <div class="pass-item mb-3 p-2 rounded" style="background-color: rgba(255, 255, 255, 0.05); border-left: 3px solid ${isHighElevation ? '#28a745' : '#ffc107'};">
                        <div class="d-flex justify-content-between align-items-center mb-1">
                            <small class="text-warning"><strong>Pass:</strong> ${riseTime.toLocaleString()}</small>
                            <span class="badge ${isHighElevation ? 'bg-success' : 'bg-warning'}">${pass.max_elevation}°</span>
                        </div>
                        <div class="row g-1">
                            <div class="col-6">
                                <small class="text-muted">Duration:</small>
                                <div class="detail-value text-info">${pass.duration_minutes.toFixed(1)} min</div>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Range:</small>
                                <div class="detail-value text-primary">${pass.range_km} km</div>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Rise Az:</small>
                                <div class="detail-value text-secondary">${pass.rise_azimuth?.toFixed(0)}°</div>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Set Az:</small>
                                <div class="detail-value text-secondary">${pass.set_azimuth?.toFixed(0)}°</div>
                            </div>
                        </div>
                    </div>
                `;
            });

            passesHtml += `</div>`;
            satelliteElement.innerHTML = passesHtml;
            container.appendChild(satelliteElement);
        });
    }

    getPassColor(satelliteType) {
        switch (satelliteType) {
            case 'GEO': return '#ff6b6b';
            case 'LEO': return '#64b5f6';
            case 'MEO': return '#ffd700';
            case 'IGSO': return '#9c27b0';
            case 'EO': return '#2e7d32';
            default: return '#757575';
        }
    }

    showCreativePassLoadingMessages(timeFilter) {
        // Remove any existing loading panel
        this.hideCreativePassLoadingMessages();

        // Create loading panel
        const loadingPanel = document.createElement('div');
        loadingPanel.id = 'passLoadingPanel';
        loadingPanel.className = 'pass-loading-panel';
        loadingPanel.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 400px;
            max-width: 90vw;
            background: linear-gradient(135deg, rgba(26, 26, 46, 0.98) 0%, rgba(12, 12, 12, 0.98) 100%);
            border: 2px solid rgba(100, 181, 246, 0.5);
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            z-index: 9999;
            backdrop-filter: blur(20px);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8);
            animation: fadeInScale 0.5s ease-out;
        `;

        const creativeMessages = [
                "🧠 Smart filtering viable satellites...",
                "🚀 Eliminating GEO satellites (too high!)...",
                "🌍 Checking orbital inclinations...",
                "🔭 Filtering by hemisphere visibility...",
                "✨ Using multiprocessing for speed...",
                "🛸 Batching calculations intelligently...",
                "🌌 Caching results for faster future queries...",
                "🎯 Progressive time window calculation...",
                "📡 Vectorizing orbital computations...",
                "⚡ Using cached 24hr data as base...",
                "🌟 Parallel processing satellite batches...",
                "🔄 Optimizing calculation priorities...",
                "🎪 Smart location-aware filtering...",
                "🧮 Running efficient pass algorithms...",
                "🌙 Checking elevation thresholds...",
                "☄️ Filtering debris and inactive sats...",
                "🛰️ Processing only promising candidates...",
                "🌐 Location hash validation...",
                "🔍 Smart cache hit optimization...",
                "⭐ Final pass validation and sorting..."
            ];

        let messageIndex = 0;
        let dotCount = 0;

        loadingPanel.innerHTML = `
            <div style="margin-bottom: 20px;">
                <div style="width: 60px; height: 60px; margin: 0 auto 15px; border: 4px solid rgba(100, 181, 246, 0.3); border-top: 4px solid #64b5f6; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                <h5 style="color: #64b5f6; margin-bottom: 10px;">🔍 Pass Calculation in Progress</h5>
                <p style="color: #e2e8f0; margin-bottom: 5px;">Searching for satellites with passes in ${timeFilter}hr window</p>
                <small style="color: #94a3b8;">This may take 30-60 seconds for comprehensive analysis</small>
            </div>
            <div id="creativeMessage" style="color: #ffd700; font-weight: bold; margin: 15px 0; min-height: 25px; font-size: 16px;"></div>
            <div style="margin-top: 20px;">
                <button onclick="window.satelliteViewer.passFilter.hideCreativePassLoadingMessages()" style="background: rgba(244, 67, 54, 0.8); color: white; border: none; padding: 8px 16px; border-radius: 20px; cursor: pointer; font-size: 14px;">
                    Cancel
                </button>
            </div>
        `;

        // Add CSS animations
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeInScale {
                from { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
                to { opacity: 1; transform: translate(-50%, -50%) scale(1); }
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        `;
        if (!document.getElementById('passLoadingStyles')) {
            style.id = 'passLoadingStyles';
            document.head.appendChild(style);
        }

        document.body.appendChild(loadingPanel);

        // Animate creative messages
        const messageElement = document.getElementById('creativeMessage');
        this.loadingMessageInterval = setInterval(() => {
            dotCount = (dotCount + 1) % 4;
            const dots = '.'.repeat(dotCount);
            messageElement.textContent = creativeMessages[messageIndex] + dots;

            // Change message every 3 seconds
            if (dotCount === 0) {
                messageIndex = (messageIndex + 1) % creativeMessages.length;
            }
        }, 750);
    }

    hideCreativePassLoadingMessages() {
        const loadingPanel = document.getElementById('passLoadingPanel');
        if (loadingPanel) {
            loadingPanel.remove();
        }

        if (this.loadingMessageInterval) {
            clearInterval(this.loadingMessageInterval);
            this.loadingMessageInterval = null;
        }
    }

    showPassFilterError(errorMessage) {
        // Remove any existing panels
        this.hideCreativePassLoadingMessages();
        this.clearPassFilter();

        // Create error panel
        const errorPanel = document.createElement('div');
        errorPanel.id = 'passErrorPanel';
        errorPanel.className = 'pass-error-panel';
        errorPanel.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 400px;
            max-width: 90vw;
            background: linear-gradient(135deg, rgba(244, 67, 54, 0.1) 0%, rgba(26, 26, 46, 0.98) 100%);
            border: 2px solid rgba(244, 67, 54, 0.5);
            border-radius: 15px;
            padding: 30px;
            text-align: center;
            z-index: 9999;
            backdrop-filter: blur(20px);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.8);
        `;

        errorPanel.innerHTML = `
            <div style="margin-bottom: 20px;">
                <i class="fas fa-exclamation-triangle" style="font-size: 48px; color: #ff6b6b; margin-bottom: 15px;"></i>
                <h5 style="color: #ff6b6b; margin-bottom: 15px;">Pass Calculation Failed</h5>
                <p style="color: #e2e8f0; margin-bottom: 0; line-height: 1.5;">${errorMessage}</p>
            </div>
            <div style="margin-top: 20px;">
                <button onclick="this.parentElement.parentElement.remove()" style="background: rgba(100, 181, 246, 0.8); color: white; border: none; padding: 10px 20px; border-radius: 20px; cursor: pointer; margin-right: 10px;">
                    Close
                </button>
                <button onclick="this.parentElement.parentElement.remove(); window.satelliteViewer.passFilter.applyTimeBasedPassFilter()" style="background: rgba(76, 175, 80, 0.8); color: white; border: none; padding: 10px 20px; border-radius: 20px; cursor: pointer;">
                    Try Again
                </button>
            </div>
        `;

        document.body.appendChild(errorPanel);

        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (errorPanel && errorPanel.parentNode) {
                errorPanel.remove();
            }
        }, 10000);
    }

    displayPassFilterResults(satellitesWithPasses, timeFilter) {
        // Remove any loading or error panels
        this.hideCreativePassLoadingMessages();
        const errorPanel = document.getElementById('passErrorPanel');
        if (errorPanel) errorPanel.remove();

        // Use cached marker coordinates for display
        const coords = this.cachedMarkerCoordinates;
        const targetLat = coords ? coords.lat : 'N/A';
        const targetLon = coords ? coords.lon : 'N/A';

        // Create or update pass filter results panel
        let resultsPanel = document.getElementById('passFilterResults');
        if (!resultsPanel) {
            resultsPanel = document.createElement('div');
            resultsPanel.id = 'passFilterResults';
            resultsPanel.className = 'pass-filter-results';
            resultsPanel.style.cssText = `
                position: fixed;
                top: 100px;
                right: 20px;
                width: 380px;
                max-width: 90vw;
                max-height: calc(100vh - 140px);
                background: linear-gradient(135deg, rgba(26, 26, 46, 0.98) 0%, rgba(12, 12, 12, 0.98) 100%);
                border: 1px solid rgba(100, 181, 246, 0.3);
                border-radius: 15px;
                backdrop-filter: blur(15px);
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.7);
                z-index: 1030;
                overflow-y: auto;
                animation: slideInRight 0.5s ease-out;
            `;

            document.body.appendChild(resultsPanel);
        }

        const sortedResults = satellitesWithPasses.sort((a, b) => b.max_elevation - a.max_elevation);

        resultsPanel.innerHTML = `
            <div style="padding: 20px; border-bottom: 1px solid rgba(100, 181, 246, 0.2); background: linear-gradient(135deg, rgba(100, 181, 246, 0.1) 0%, rgba(66, 165, 245, 0.1) 100%); border-radius: 15px 15px 0 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <h6 class="text-primary" style="margin: 0;">
                        <i class="fas fa-satellite me-2"></i>Pass Results (${timeFilter}hr)
                    </h6>
                    <button type="button" onclick="window.satelliteViewer.passFilter.clearPassFilter()" style="background: rgba(244, 67, 54, 0.8); color: white; border: none; width: 25px; height: 25px; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center;">
                        <i class="fas fa-times" style="font-size: 12px;"></i>
                    </button>
                </div>
                <div style="font-size: 12px; color: #94a3b8;">
                    Found ${sortedResults.length} satellites with passes<br>
                    Marker Location: ${typeof targetLat === 'number' ? targetLat.toFixed(4) : targetLat}, ${typeof targetLon === 'number' ? targetLon.toFixed(4) : targetLon}
                </div>
            </div>
            <div style="padding: 15px; max-height: 400px; overflow-y: auto;">
                ${sortedResults.length === 0 ? `
                    <div style="text-align: center; padding: 30px; color: #94a3b8;">
                        <i class="fas fa-satellite" style="font-size: 48px; margin-bottom: 15px; opacity: 0.5;"></i>
                        <p>No satellites found with passes in the ${timeFilter}hr window.</p>
                        <small>Try a different time window or check your location marker placement.</small>
                    </div>
                ` : sortedResults.slice(0, 25).map((result, index) => `
                    <div class="pass-result-item" data-norad-id="${result.satellite_id}" style="padding: 12px; margin-bottom: 8px; background: rgba(255, 255, 255, 0.02); border-radius: 8px; cursor: pointer; transition: all 0.3s ease; border-left: 3px solid rgba(100, 181, 246, 0.3);" onmouseover="this.style.background='rgba(100, 181, 246, 0.1)'; this.style.borderLeftColor='#64b5f6'" onmouseout="this.style.background='rgba(255, 255, 255, 0.02)'; this.style.borderLeftColor='rgba(100, 181, 246, 0.3)'">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                            <strong class="text-info" style="font-size: 14px;">${result.satellite_name}</strong>
                            <span class="badge ${result.max_elevation > 30 ? 'bg-success' : 'bg-warning'}" style="font-size: 11px;">${result.max_elevation}°</span>
                        </div>
                        <div style="font-size: 11px; color: #94a3b8; line-height: 1.4;">
                            Pass: ${new Date(result.pass_time).toLocaleString()}<br>
                            Range: ${result.range_km}km | Az: ${result.azimuth}°
                            ${result.is_earth_observation ? ' | <span style="color: #4caf50;">EO Satellite</span>' : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;

        // Add CSS animation for slide-in effect
        const slideStyle = document.createElement('style');
        slideStyle.textContent = `
            @keyframes slideInRight {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        if (!document.getElementById('slideInStyles')) {
            slideStyle.id = 'slideInStyles';
            document.head.appendChild(slideStyle);
        }

        // Add click handlers to pass result items - use workflow system
        resultsPanel.querySelectorAll('.pass-result-item').forEach(item => {
            item.addEventListener('click', async () => {
                const noradId = parseInt(item.dataset.noradId);

                // Use the centralized workflow system for consistent behavior
                await this.satelliteViewer.satelliteWorkflow.executeSatelliteSelectionWorkflow(
                    noradId,
                    true,
                    'pass-filter'
                );

                // Highlight selected item
                resultsPanel.querySelectorAll('.pass-result-item').forEach(i => {
                    i.style.borderLeftColor = 'rgba(100, 181, 246, 0.3)';
                    i.style.background = 'rgba(255, 255, 255, 0.02)';
                });
                item.style.borderLeftColor = '#64b5f6';
                item.style.background = 'rgba(100, 181, 246, 0.2)';
            });
        });

        // Auto-hide after 30 seconds if no interaction
        setTimeout(() => {
            if (resultsPanel && resultsPanel.parentNode) {
                resultsPanel.style.opacity = '0.7';
            }
        }, 30000);
    }

    filterSatellitesByPassResults(passResults) {
        // Use the satellite filter module to handle this
        if (this.satelliteViewer.satelliteFilter) {
            this.satelliteViewer.satelliteFilter.filterSatellitesByPassResults(passResults);
        }
    }

    clearPassFilter() {
        // Hide pass filter results panel
        const resultsPanel = document.getElementById('passFilterResults');
        if (resultsPanel) {
            resultsPanel.remove();
        }

        // Hide loading messages
        this.hideCreativePassLoadingMessages();

        // Hide error panel
        const errorPanel = document.getElementById('passErrorPanel');
        if (errorPanel) {
            errorPanel.remove();
        }

        // Reset time filter select
        const timeFilterSelect = document.getElementById('timeFilterSelect');
        if (timeFilterSelect) {
            timeFilterSelect.value = '24';
        }

        // Clear cached coordinates when clearing filter
        this.cachedMarkerCoordinates = null;

        // Show all satellites again based on current filters
        if (this.satelliteViewer.satelliteFilter) {
            this.satelliteViewer.satelliteFilter.applyCurrentFilters();
        }

        console.log('🧹 Pass filter cleared and coordinates cache cleared');
    }

    async togglePastPasses() {
        if (!this.satelliteViewer.selectedSatellite) {
            console.warn('No satellite selected for past passes');
            return;
        }

        // Get ONLY marker coordinates - NO GPS FALLBACK
        const markerCoords = this.getMarkerCoordinates();

        if (!markerCoords) {
            alert('Please set your location marker on the map first to calculate past passes');
            return;
        }

        const { lat: targetLat, lon: targetLon, alt: targetAlt } = markerCoords;

        const button = document.getElementById('pastPassesBtn');
        if (!button) return;

        if (this.showingPastPasses) {
            // Hide past passes
            this.showingPastPasses = false;
            button.innerHTML = '<i class="fas fa-history"></i> Past Passes';
            button.classList.remove('btn-info');
            button.classList.add('btn-warning');

            // Hide past passes info and show regular passes
            const pastPassesInfo = document.getElementById('pastPassesInfo');
            if (pastPassesInfo) {
                pastPassesInfo.style.display = 'none';
            }

            const passInfo = document.getElementById('passInfo');
            if (passInfo) {
                passInfo.style.display = 'block';
            }
        } else {
            // Show past passes
            this.showingPastPasses = true;
            button.innerHTML = '<i class="fas fa-eye"></i> Current Passes';
            button.classList.remove('btn-warning');
            button.classList.add('btn-info');

            // Load and show past passes with marker location ONLY
            await this.loadAndDisplayPastPasses(targetLat, targetLon, targetAlt);
        }
    }

    async loadAndDisplayPastPasses(targetLat, targetLon, targetAlt) {
        if (!this.satelliteViewer.selectedSatellite) return;

        try {
            console.log(`Loading past passes for satellite ${this.satelliteViewer.selectedSatellite} at MARKER LOCATION ONLY (${targetLat}, ${targetLon})`);

            const response = await fetch(`/api/satellite/${this.satelliteViewer.selectedSatellite}/past-passes?lat=${targetLat}&lon=${targetLon}&alt=${targetAlt}&days_back=7`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success && data.past_passes) {
                this.displayPastPassesInfo(data.past_passes, data.satellite_info, data.is_earth_observation, data.fov_info);
            } else {
                console.warn('Failed to load past passes:', data);
                this.showNoPastPassesMessage();
            }
        } catch (error) {
            console.error('Error loading past passes:', error);
            this.showNoPastPassesMessage();
        }
    }

    displayPastPassesInfo(pastPasses, satelliteInfo, isEarthObservation = false, fovInfo = null) {
        // Hide current passes and show past passes
        const passInfo = document.getElementById('passInfo');
        if (passInfo) {
            passInfo.style.display = 'none';
        }

        // Create or get past passes container
        let pastPassesInfo = document.getElementById('pastPassesInfo');
        if (!pastPassesInfo) {
            pastPassesInfo = document.createElement('div');
            pastPassesInfo.id = 'pastPassesInfo';
            pastPassesInfo.className = 'pass-info';

            // Insert after passInfo
            if (passInfo && passInfo.parentNode) {
                passInfo.parentNode.insertBefore(pastPassesInfo, passInfo.nextSibling);
            } else {
                // Fallback: append to satellite details
                const container = document.getElementById('satelliteDetails');
                if (container) {
                    container.appendChild(pastPassesInfo);
                }
            }
        }

        pastPassesInfo.style.display = 'block';

        const headerText = isEarthObservation ? 'Past Coverage Events' : 'Historical Passes';
        const headerIcon = isEarthObservation ? 'fas fa-satellite' : 'fas fa-history';

        pastPassesInfo.innerHTML = `
            <h6 class="text-warning mb-3">
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
                        <strong>Historical Coverage Analysis:</strong><br>
                        <small>Satellite: ${satelliteInfo?.name || 'Unknown'}</small><br>
                        <small>Swath Width: ${fovInfo.default_swath || 'N/A'} km</small><br>
                        <small>Sensors: ${fovInfo.sensors ? fovInfo.sensors.join(', ') : 'N/A'}</small><br>
                        <small>Analysis Period: Past 7 days</small>
                    </div>
                </div>
            `;
            pastPassesInfo.appendChild(fovInfoDiv);
        }

        if (!pastPasses || pastPasses.length === 0) {
            const noPassesMsg = isEarthObservation ?
                'No coverage events found in the past 7 days for your marker location.' :
                'No visible passes found in the past 7 days for your marker location.';
            pastPassesInfo.innerHTML += `<p class="text-muted">${noPassesMsg}</p>`;
            return;
        }

        // Create tabs for each past pass
        const navTabs = document.createElement('ul');
        navTabs.className = 'nav nav-tabs';
        navTabs.id = 'pastPassNavTabs';
        navTabs.setAttribute('role', 'tablist');

        const tabContent = document.createElement('div');
        tabContent.className = 'tab-content';
        tabContent.id = 'pastPassTabContent';

        pastPasses.forEach((pass, index) => {
            const passDate = new Date(pass.rise_time);
            const tabId = `pastpass-${this.satelliteViewer.selectedSatellite}-${index}`;
            const paneId = `pastpane-${this.satelliteViewer.selectedSatellite}-${index}`;

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

            const tabText = isEarthObservation ? `Event ${index + 1}` : `Pass ${index + 1}`;
            tabLink.innerHTML = `${tabText}<br><small>${passDate.toLocaleDateString()}</small>`;

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

            if (pass.swath_width && pass.swath_width > 0) {
                additionalInfo += `
                    <div class="row mb-2">
                        <div class="col-6">
                            <small class="text-muted">Swath Width:</small><br>
                            <small class="text-success">${pass.swath_width} km</small>
                        </div>
                        <div class="col-6">
                            <small class="text-muted">Coverage Type:</small><br>
                            <small class="text-warning">${pass.coverage_type || 'Historical'}</small>
                        </div>
                    </div>
                `;
            }

            const startLabel = isEarthObservation ? 'Coverage Start:' : 'Pass Start:';
            const endLabel = isEarthObservation ? 'Coverage End:' : 'Pass End:';

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
                    <div class="row">
                        <div class="col-6">
                            <small class="text-muted">Start Az:</small><br>
                            <small class="text-primary">${pass.rise_azimuth?.toFixed(1)}°</small>
                        </div>
                        <div class="col-6">
                            <small class="text-muted">End Az:</small><br>
                            <small class="text-primary">${pass.set_azimuth?.toFixed(1)}°</small>
                        </div>
                    </div>
                    <div class="row mt-2">
                        <div class="col-12">
                            <small class="text-muted">Event Type:</small><br>
                            <small class="badge bg-secondary">${pass.coverage_type || 'Historical Pass'}</small>
                        </div>
                    </div>
                </div>
            `;

            tabContent.appendChild(tabPane);
        });

        pastPassesInfo.appendChild(navTabs);
        pastPassesInfo.appendChild(tabContent);
    }

    showNoPastPassesMessage() {
        let pastPassesInfo = document.getElementById('pastPassesInfo');
        if (!pastPassesInfo) {
            pastPassesInfo = document.createElement('div');
            pastPassesInfo.id = 'pastPassesInfo';
            pastPassesInfo.className = 'pass-info';

            const passInfo = document.getElementById('passInfo');
            if (passInfo && passInfo.parentNode) {
                passInfo.parentNode.insertBefore(pastPassesInfo, passInfo.nextSibling);
            }
        }

        pastPassesInfo.style.display = 'block';
        pastPassesInfo.innerHTML = `
            <h6 class="text-warning mb-3">
                <i class="fas fa-history me-2"></i>Past Passes
            </h6>
            <div class="alert alert-warning">
                <p class="mb-0">Unable to load past passes data. This could be due to:</p>
                <ul class="mb-0 mt-2">
                    <li>Network connectivity issues</li>
                    <li>Satellite altitude too high (>20,000 km)</li>
                    <li>No location marker set for calculations</li>
                </ul>
            </div>
        `;

        // Hide current passes
        const passInfo = document.getElementById('passInfo');
        if (passInfo) {
            passInfo.style.display = 'none';
        }
    }

    // Helper methods for past passes
    getDirectionFromAzimuth(azimuth) {
        if (azimuth === undefined) return 'N/A';
        const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
        const index = Math.round(azimuth / 22.5) % 16;
        return directions[index];
    }

    getTimeSincePass(passTime) {
        const now = new Date();
        const diffMs = now - passTime;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        const diffHours = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));

        if (diffDays > 0) {
            return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
        } else if (diffHours > 0) {
            return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
        } else {
            const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
            return `${diffMinutes} minute${diffMinutes > 1 ? 's' : ''} ago`;
        }
    }

    async loadPastPasses(noradId) {
        // Get ONLY marker coordinates - NO GPS FALLBACK
        const markerCoords = this.getMarkerCoordinates();

        if (!markerCoords) {
            this.renderPastPassesError('No location marker set. Please set a location marker first.');
            return;
        }

        const { lat, lon, alt } = markerCoords;

        try {
            console.log(`Loading past passes for satellite ${noradId} at MARKER LOCATION ONLY (${lat}, ${lon})`);

            const response = await fetch(`/api/satellite/${noradId}/past-passes?lat=${lat}&lon=${lon}&alt=${alt}&days_back=7`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success && data.past_passes) {
                this.pastPassesData = data.past_passes;
                this.renderPastPasses(data);
                console.log(`Loaded ${data.past_passes.length} past passes for MARKER LOCATION`);
            } else {
                console.warn('Failed to load past passes:', data);
                this.renderPastPassesError(data.error || 'No past passes found');
            }
        } catch (error) {
            console.error('Error loading past passes:', error);
            this.renderPastPassesError(error.message);
        }
    }

    renderPastPasses(data) {
        const passInfo = document.getElementById('passInfo');
        if (!passInfo) return;

        const satellite_info = data.satellite_info || { name: 'Unknown', norad_id: 'Unknown' };
        const pastPasses = data.past_passes || [];
        const daysSearched = data.days_searched || 7;

        let passContent = `
            <h6 class="text-warning mb-3">
                <i class="fas fa-history me-2"></i>Past Passes - ${satellite_info.name}
            </h6>
            <div class="text-info mb-3">
                <small>Showing historical passes from the last ${daysSearched} days at marker location</small>
            </div>
        `;

        if (pastPasses.length === 0) {
            passContent += `
                <div class="alert alert-info" role="alert">
                    <i class="fas fa-info-circle me-2"></i>
                    No past passes found for this satellite in the last ${daysSearched} days from your marker location.
                    <br><small class="text-muted">This could be due to orbital parameters or satellite visibility constraints.</small>
                </div>
            `;
        } else {
            pastPasses.forEach((pass, index) => {
                const riseTime = new Date(pass.rise_time);
                const setTime = new Date(pass.set_time);
                const maxTime = new Date(pass.culmination_time);

                const isHighQuality = pass.max_elevation > 30;
                const elevationClass = isHighQuality ? 'text-success' : 'text-warning';

                passContent += `
                    <div class="pass-item mb-3" style="background-color: rgba(255, 193, 7, 0.1); border-left: 4px solid #ffc107;">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <div class="pass-time text-warning">
                                <i class="fas fa-clock me-1"></i>
                                ${riseTime.toLocaleDateString()} ${riseTime.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                            </div>
                            <span class="badge bg-info">
                                ${pass.coverage_type}
                            </span>
                        </div>

                        <div class="row g-2 pass-details">
                            <div class="col-6">
                                <small class="text-muted">Max Elevation:</small>
                                <div class="detail-value ${elevationClass}">${pass.max_elevation}°</div>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Duration:</small>
                                <div class="detail-value text-info">${pass.duration_minutes.toFixed(1)} min</div>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Rise Direction:</small>
                                <div class="detail-value text-primary">${this.getDirectionFromAzimuth(pass.rise_azimuth)} (${pass.rise_azimuth}°)</div>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Set Direction:</small>
                                <div class="detail-value text-primary">${this.getDirectionFromAzimuth(pass.set_azimuth)} (${pass.set_azimuth}°)</div>
                            </div>
                            <div class="col-12">
                                <small class="text-muted">Peak Time:</small>
                                <div class="detail-value text-success">${maxTime.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</div>
                            </div>
                            ${pass.swath_width > 0 ? `
                                <div class="col-12">
                                    <small class="text-muted">Swath Width:</small>
                                    <div class="detail-value text-cyan">${pass.swath_width} km</div>
                                </div>
                            ` : ''}
                        </div>

                        <div class="mt-2">
                            <small class="text-muted d-block">
                                <i class="fas fa-satellite me-1"></i>
                                Time since pass: ${this.getTimeSincePass(riseTime)}
                            </small>
                        </div>
                    </div>
                `;
            });
        }

        passInfo.innerHTML = passContent;
    }

    renderPastPassesError(errorMessage) {
        const passInfo = document.getElementById('passInfo');
        if (!passInfo) return;

        passInfo.innerHTML = `
            <h6 class="text-warning mb-3">
                <i class="fas fa-history me-2"></i>Past Passes
            </h6>
            <div class="alert alert-warning" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Error loading past passes: ${errorMessage}
            </div>
        `;
    }

    // Method to manually refresh coordinates cache (call this when marker is moved)
    refreshMarkerCoordinates() {
        this.cachedMarkerCoordinates = null;
        const coords = this.getMarkerCoordinates();
        if (coords) {
            console.log(`🔄 Marker coordinates refreshed: (${coords.lat.toFixed(6)}, ${coords.lon.toFixed(6)})`);
        }
        return coords;
    }

    // Method to check if marker coordinates are valid and recent
    areMarkerCoordinatesValid() {
        if (!this.cachedMarkerCoordinates) return false;

        const age = Date.now() - this.cachedMarkerCoordinates.timestamp;
        const isRecent = age < 5 * 60 * 1000; // 5 minutes
        const hasValidCoords = Math.abs(this.cachedMarkerCoordinates.lat) <= 90 &&
                               Math.abs(this.cachedMarkerCoordinates.lon) <= 180;

        return isRecent && hasValidCoords;
    }
}