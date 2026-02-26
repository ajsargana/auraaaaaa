
class MotionControl {
    constructor(satelliteViewer) {
        this.viewer = satelliteViewer;
        this.motionControlEnabled = false;
        this.motionControlEntities = new Map();
        this.motionControlInterval = null;
        this.motionSpeed = 1; // Speed multiplier: -10 to +10
        this.currentOrbitTimeIndex = 0;
        this.orbitTimeData = []; // Array of timestamps for each orbit position
        this.currentOrbitPoints = null;
        this.currentPositionIndex = 0;
        this.originalSatellitePosition = null; // Store original position callback
    }

    toggleMotionControl() {
        if (!this.viewer.selectedSatellite) {
            alert('Please select a satellite first to enable motion control');
            return;
        }

        this.motionControlEnabled = !this.motionControlEnabled;
        const btn = document.getElementById('motionControlBtn');
        const speedPanel = document.getElementById('speedControlPanel');
        const timeDisplay = document.getElementById('orbitTimeDisplay');

        if (this.motionControlEnabled) {
            btn.classList.add('active');
            btn.innerHTML = '<i class="fas fa-route"></i> Exit Motion';
            speedPanel.style.display = 'block';
            timeDisplay.style.display = 'block';
            this.enableMotionControl();
        } else {
            btn.classList.remove('active');
            btn.innerHTML = '<i class="fas fa-route"></i> Motion Control';
            speedPanel.style.display = 'none';
            timeDisplay.style.display = 'none';
            this.disableMotionControl();
        }
    }

    setMotionSpeed(speed) {
        const oldSpeed = this.motionSpeed;
        this.motionSpeed = Math.max(-50, Math.min(50, speed));
        document.getElementById('speedControlSlider').value = this.motionSpeed;

        // Enhanced speed display with clear indicators
        const speedValue = document.getElementById('speedValue');
        if (this.motionSpeed === 0) {
            speedValue.textContent = 'PAUSED';
            speedValue.className = 'text-primary fw-bold'; // Blue for pause
        } else if (this.motionSpeed === 1) {
            speedValue.textContent = '1x REAL-TIME';
            speedValue.className = 'text-success fw-bold'; // Green for real-time
        } else if (this.motionSpeed === -1) {
            speedValue.textContent = '1x REVERSE';
            speedValue.className = 'text-warning fw-bold'; // Orange for reverse
        } else {
            speedValue.textContent = this.motionSpeed + 'x';

            // Color coding based on speed and direction
            if (this.motionSpeed < 0) {
                speedValue.className = 'text-warning fw-bold'; // Past (orange)
            } else if (this.motionSpeed > 25) {
                speedValue.className = 'text-danger fw-bold'; // Very fast (red)
            } else {
                speedValue.className = 'text-success fw-bold'; // Future (green)
            }
        }
        
        // Log speed changes with more detail
        if (oldSpeed !== this.motionSpeed) {
            if (this.motionSpeed === 0) {
                console.log('🎬 Motion PAUSED - satellite frozen in time');
            } else if (Math.abs(this.motionSpeed) === 1) {
                console.log(`🎬 Motion set to ${this.motionSpeed > 0 ? 'REAL-TIME FORWARD' : 'REAL-TIME REVERSE'}`);
            } else {
                const direction = this.motionSpeed > 0 ? 'FUTURE' : 'PAST';
                const frameRate = this.calculateFrameRate(this.motionSpeed);
                console.log(`🎬 Motion speed: ${this.motionSpeed}x ${direction} (${frameRate} fps)`);
            }
            
            // Restart animation with new speed if motion control is enabled
            if (this.motionControlEnabled) {
                this.startMotionAnimation();
            }
        }
    }
    
    calculateFrameRate(speed) {
        if (speed === 0) return 0;
        const absSpeed = Math.abs(speed);
        let animationSpeed;

        if (absSpeed === 1) {
            animationSpeed = 1000;
        } else if (absSpeed <= 10) {
            animationSpeed = Math.max(1000 / absSpeed, 50);
        } else if (absSpeed <= 25) {
            animationSpeed = Math.max(100 - (absSpeed - 10) * 2, 30);
        } else {
            animationSpeed = Math.max(30 - (absSpeed - 25), 10);
        }

        return (1000 / animationSpeed).toFixed(1);
    }

    adjustSpeed(delta) {
        this.setMotionSpeed(this.motionSpeed + delta);
    }

    async enableMotionControl() {
        if (!this.viewer.selectedSatellite) {
            console.warn('No satellite selected for motion control');
            return;
        }

        console.log('🎬 Enabling motion control for satellite:', this.viewer.selectedSatellite);

        // CRITICAL FIX: Store original position callback before overriding
        const satelliteEntity = this.viewer.satelliteEntities.get(this.viewer.selectedSatellite);
        if (satelliteEntity) {
            this.originalSatellitePosition = satelliteEntity.position;
            console.log('✅ Stored original satellite position callback');
        }

        // Hide all other satellites
        this.hideAllSatellitesExceptSelected();

        // Show loading indicator
        this.viewer.showLoadingIndicator('Calculating orbital motion paths...');

        try {
            // Get extended orbital path data using cache (3.5 days past, 3.5 days future = full 7-day cache)
            await this.loadExtendedOrbitPath(this.viewer.selectedSatellite);

            // Start motion animation
            this.startMotionAnimation();

        } catch (error) {
            console.error('Error enabling motion control:', error);
            this.viewer.showError('Failed to load motion data: ' + error.message);
        } finally {
            this.viewer.hideLoadingIndicator();
        }
    }

    disableMotionControl() {
        console.log('🎬 Disabling motion control');

        // CRITICAL FIX: Restore original satellite position BEFORE stopping animation
        if (this.viewer.selectedSatellite && this.originalSatellitePosition) {
            const satelliteEntity = this.viewer.satelliteEntities.get(this.viewer.selectedSatellite);
            if (satelliteEntity) {
                satelliteEntity.position = this.originalSatellitePosition;
                console.log('✅ Restored original satellite position callback');
            }
            this.originalSatellitePosition = null;
        }

        // Stop motion animation
        this.stopMotionAnimation();

        // Clear motion control entities
        this.clearMotionControlEntities();

        // Show all satellites again with current filters
        this.showAllSatellitesWithFilters();

        // Reset motion control state
        this.motionControlEnabled = false;
        this.motionSpeed = 1;
        this.currentOrbitTimeIndex = 0;
        this.orbitTimeData = [];
        this.currentOrbitPoints = null;

        // Reset speed control UI
        document.getElementById('speedControlSlider').value = 1;
        document.getElementById('speedValue').textContent = '1x';
        document.getElementById('speedValue').className = 'text-success';
    }

    hideAllSatellitesExceptSelected() {
        this.viewer.satelliteEntities.forEach((entity, noradId) => {
            if (noradId !== this.viewer.selectedSatellite) {
                if (entity.point) entity.point.show = false;
                if (entity.label) entity.label.show = false;
            }
        });
    }

    showAllSatellitesWithFilters() {
        // Re-apply current filters to show satellites using satellite filter module
        if (this.viewer.satelliteFilter) {
            this.viewer.satelliteFilter.showAllSatellitesWithFilters();
        }
    }

    async loadExtendedOrbitPath(noradId) {
        try {
            // OPTIMIZED: Use 2 days past/future with 60s intervals for fast loading + smooth motion
            // Total: ~5,760 points (4 days × 24 hours × 60 points/hour)
            const response = await fetchWithRetry(`/api/satellite/${noradId}/extended-orbit?days_past=2&days_future=2&interval_seconds=60`);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.success && data.orbit_points) {
                console.log(`📊 Loaded ${data.orbit_points.length} orbit points with ${data.interval_seconds || 10}s intervals`);
                this.renderExtendedOrbitPath(noradId, data.orbit_points, data.current_position_index);
            } else {
                throw new Error('Failed to load extended orbit data');
            }
        } catch (error) {
            console.error('Error loading extended orbit path:', error);
            throw error;
        }
    }

    renderExtendedOrbitPath(noradId, orbitPoints, currentIndex) {
        // Clear existing motion entities
        this.clearMotionControlEntities();

        if (orbitPoints.length < 2) {
            console.warn('Insufficient orbit points for motion control');
            return;
        }

        const satellite = this.viewer.satellites.get(noradId);
        const color = satellite ? satellite.color : '#64b5f6';

        // Split orbit into past, current, and future segments
        const pastPoints = orbitPoints.slice(0, currentIndex);
        const futurePoints = orbitPoints.slice(currentIndex);

        // Create past orbit trail (faded)
        if (pastPoints.length > 1) {
            const pastPositions = pastPoints.map(point =>
                Cesium.Cartesian3.fromDegrees(point.longitude, point.latitude, point.altitude * 1000)
            );

            const pastOrbitEntity = this.viewer.viewer.entities.add({
                id: `motion_past_${noradId}`,
                polyline: {
                    positions: pastPositions,
                    width: 2,
                    material: new Cesium.PolylineGlowMaterialProperty({
                        glowPower: 0.2,
                        color: Cesium.Color.fromCssColorString(color).withAlpha(0.4)
                    }),
                    clampToGround: false
                }
            });

            this.motionControlEntities.set(`past_${noradId}`, pastOrbitEntity);
        }

        // Create future orbit trail (bright)
        if (futurePoints.length > 1) {
            const futurePositions = futurePoints.map(point =>
                Cesium.Cartesian3.fromDegrees(point.longitude, point.latitude, point.altitude * 1000)
            );

            const futureOrbitEntity = this.viewer.viewer.entities.add({
                id: `motion_future_${noradId}`,
                polyline: {
                    positions: futurePositions,
                    width: 4,
                    material: new Cesium.PolylineGlowMaterialProperty({
                        glowPower: 0.5,
                        color: Cesium.Color.fromCssColorString(color).withAlpha(0.8)
                    }),
                    clampToGround: false
                }
            });

            this.motionControlEntities.set(`future_${noradId}`, futureOrbitEntity);
        }

        // Create motion points along the path
        this.createMotionPoints(noradId, orbitPoints, currentIndex, color);

        // Store orbit data for animation with timestamps
        this.currentOrbitPoints = orbitPoints;
        this.currentPositionIndex = currentIndex;
        this.currentOrbitTimeIndex = currentIndex; // Start at current position
        
        // Generate timestamps for each orbit position
        this.generateOrbitTimestamps(orbitPoints, currentIndex);
        
        // Initialize time display
        this.updateTimeDisplay();
    }

    createMotionPoints(noradId, orbitPoints, currentIndex, color) {
        // OPTIMIZED: Add markers every 6 hours, adjust for actual interval
        // Assume 60s intervals: 6 hours = 360 points
        const intervalSeconds = 60; // Match the fetch interval
        const hoursPerMarker = 6;
        const markerInterval = Math.floor((hoursPerMarker * 3600) / intervalSeconds);

        console.log(`📍 Creating markers every ${markerInterval} points (${hoursPerMarker} hours)`);

        for (let i = 0; i < orbitPoints.length; i += markerInterval) {
            const point = orbitPoints[i];
            const isPast = i < currentIndex;
            const isCurrent = Math.abs(i - currentIndex) < 5;

            let markerColor, markerSize, labelText;

            if (isCurrent) {
                markerColor = Cesium.Color.YELLOW;
                markerSize = 8;
                labelText = 'NOW';
            } else if (isPast) {
                markerColor = Cesium.Color.fromCssColorString(color).withAlpha(0.6);
                markerSize = 4;
                const pointsPerHour = 3600 / intervalSeconds; // 60 points/hour at 60s intervals
                labelText = `${Math.round((currentIndex - i) / pointsPerHour)} hrs ago`;
            } else {
                markerColor = Cesium.Color.fromCssColorString(color);
                markerSize = 4;
                const pointsPerHour = 3600 / intervalSeconds;
                labelText = `+${Math.round((i - currentIndex) / pointsPerHour)} hrs`;
            }

            const markerEntity = this.viewer.viewer.entities.add({
                id: `motion_marker_${noradId}_${i}`,
                position: Cesium.Cartesian3.fromDegrees(
                    point.longitude, 
                    point.latitude, 
                    point.altitude * 1000
                ),
                point: {
                    pixelSize: markerSize,
                    color: markerColor,
                    outlineColor: Cesium.Color.WHITE,
                    outlineWidth: 1,
                    heightReference: Cesium.HeightReference.NONE,
                    disableDepthTestDistance: 0
                },
                label: {
                    text: labelText,
                    font: '10pt Arial',
                    fillColor: Cesium.Color.WHITE,
                    outlineColor: Cesium.Color.BLACK,
                    outlineWidth: 1,
                    style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                    pixelOffset: new Cesium.Cartesian2(0, -20),
                    scale: 0.8,
                    show: isCurrent || i === 0 || i === orbitPoints.length - 1
                }
            });

            this.motionControlEntities.set(`marker_${noradId}_${i}`, markerEntity);
        }
    }

    generateOrbitTimestamps(orbitPoints, currentIndex) {
        // Generate timestamps for each orbit position
        // OPTIMIZED: Using 60-second intervals for fast loading
        const secondsPerPoint = 60;

        // Use the server's current time for accurate synchronization
        const serverTime = this.getServerTime();

        this.orbitTimeData = orbitPoints.map((point, index) => {
            // Calculate time offset from current position
            const timeOffsetSeconds = (index - currentIndex) * secondsPerPoint;
            return serverTime + (timeOffsetSeconds * 1000);
        });

        console.log(`🕐 Generated ${this.orbitTimeData.length} timestamps with ${secondsPerPoint}s intervals`);
        console.log(`🕐 Current index: ${currentIndex}`);
        console.log(`🕐 Current server time: ${new Date(serverTime).toISOString()}`);
        console.log(`🕐 Satellite current time: ${new Date(this.orbitTimeData[currentIndex]).toISOString()}`);
    }

    getServerTime() {
        // Get the last known satellite data timestamp for better synchronization
        if (this.viewer.satellites.size > 0) {
            const firstSat = this.viewer.satellites.values().next().value;
            if (firstSat.lastUpdateTime) {
                return firstSat.lastUpdateTime;
            }
        }
        // Fallback to client time
        return Date.now();
    }

    updateTimeDisplay() {
        if (!this.orbitTimeData || this.currentOrbitTimeIndex >= this.orbitTimeData.length) {
            return;
        }
        
        const timestamp = this.orbitTimeData[this.currentOrbitTimeIndex];
        const date = new Date(timestamp);
        
        // Format date and time
        const dateStr = date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
        const timeStr = date.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        // Update display
        const dateElement = document.getElementById('orbitDate');
        const timeElement = document.getElementById('orbitTime');
        
        if (dateElement && timeElement) {
            dateElement.textContent = dateStr;
            timeElement.textContent = timeStr;
        }
        
        // Show if we're in past, present, or future
        const now = Date.now();
        const timeDiff = timestamp - now;
        const statusElement = document.getElementById('timeStatus');
        
        if (statusElement) {
            if (Math.abs(timeDiff) < 30000) { // Within 30 seconds
                statusElement.textContent = 'LIVE';
                statusElement.className = 'badge bg-success';
            } else if (timeDiff < 0) {
                const minutesAgo = Math.abs(timeDiff) / (1000 * 60);
                if (minutesAgo < 60) {
                    statusElement.textContent = `${Math.round(minutesAgo)}m ago`;
                } else {
                    const hoursAgo = minutesAgo / 60;
                    statusElement.textContent = `${Math.round(hoursAgo)}h ago`;
                }
                statusElement.className = 'badge bg-warning';
            } else {
                const minutesFromNow = timeDiff / (1000 * 60);
                if (minutesFromNow < 60) {
                    statusElement.textContent = `+${Math.round(minutesFromNow)}m`;
                } else {
                    const hoursFromNow = minutesFromNow / 60;
                    statusElement.textContent = `+${Math.round(hoursFromNow)}h`;
                }
                statusElement.className = 'badge bg-info';
            }
        }

        // Update pass predictions when time changes significantly
        if (this.viewer.selectedSatellite && this.motionControlEnabled) {
            // Reload pass predictions every 30 motion control steps to keep them synchronized
            if (this.currentOrbitTimeIndex % 30 === 0) {
                this.viewer.loadPassPredictions(this.viewer.selectedSatellite);
            }
        }
    }

    startMotionAnimation() {
        // Clear any existing animation
        this.stopMotionAnimation();

        if (!this.currentOrbitPoints || !this.viewer.selectedSatellite || !this.orbitTimeData) {
            return;
        }

        console.log('🎬 Starting motion animation with speed:', this.motionSpeed + 'x');

        // TRUE PAUSE at 0x - completely stop animation
        if (this.motionSpeed === 0) {
            console.log('🎬 Motion PAUSED at 0x speed');
            return; // No interval created, complete stop
        }

        // EXPONENTIAL speed calculation for speeds 1-50x
        let animationSpeed;
        const absSpeed = Math.abs(this.motionSpeed);

        if (absSpeed === 1) {
            // 1x speed: Real-time motion (60 seconds per orbit point)
            animationSpeed = 1000; // 1 second per frame = 60x speedup
        } else if (absSpeed <= 10) {
            // Speeds 2-10: Progressive acceleration
            animationSpeed = Math.max(1000 / absSpeed, 50);
        } else if (absSpeed <= 25) {
            // Speeds 11-25: Fast range
            animationSpeed = Math.max(100 - (absSpeed - 10) * 2, 30);
        } else {
            // Speeds 26-50: Ultra-fast range
            animationSpeed = Math.max(30 - (absSpeed - 25), 10);
        }

        console.log(`🎬 Speed ${this.motionSpeed}x -> Animation interval: ${animationSpeed}ms (${(1000/animationSpeed).toFixed(1)} frames/sec)`);

        this.motionControlInterval = setInterval(() => {
            // FRAME-BY-FRAME ANIMATION CONTROL
            // Each interval step represents one animation frame
            
            // Update orbit time index based on speed direction
            if (this.motionSpeed > 0) {
                // Forward motion (future)
                this.currentOrbitTimeIndex++;
                if (this.currentOrbitTimeIndex >= this.currentOrbitPoints.length) {
                    this.currentOrbitTimeIndex = 0; // Loop to beginning
                    console.log('🔄 Animation looped to start (future)');
                }
            } else if (this.motionSpeed < 0) {
                // Backward motion (past)
                this.currentOrbitTimeIndex--;
                if (this.currentOrbitTimeIndex < 0) {
                    this.currentOrbitTimeIndex = this.currentOrbitPoints.length - 1; // Loop to end
                    console.log('🔄 Animation looped to end (past)');
                }
            }

            const point = this.currentOrbitPoints[this.currentOrbitTimeIndex];
            
            // Update satellite position for animation FRAME
            const satelliteEntity = this.viewer.satelliteEntities.get(this.viewer.selectedSatellite);
            if (satelliteEntity && point) {
                // Create precise animated position for this frame
                const animatedPosition = Cesium.Cartesian3.fromDegrees(
                    point.longitude,
                    point.latitude,
                    point.altitude * 1000
                );

                // Update the satellite's displayed position (single frame)
                satelliteEntity.position = new Cesium.ConstantProperty(animatedPosition);

                // Update camera to follow if tracking is enabled (smooth following)
                if (this.viewer.trackingMode) {
                    const cameraPosition = Cesium.Cartesian3.fromDegrees(
                        point.longitude,
                        point.latitude,
                        (point.altitude + 2000) * 1000
                    );

                    // Use flyTo for smoother camera movement at slower speeds, setView for faster speeds
                    if (Math.abs(this.motionSpeed) <= 3) {
                        this.viewer.viewer.camera.flyTo({
                            destination: cameraPosition,
                            orientation: {
                                heading: 0.0,
                                pitch: -Cesium.Math.PI_OVER_TWO,
                                roll: 0.0
                            },
                            duration: animationSpeed / 2000, // Smooth duration based on speed
                            easingFunction: Cesium.EasingFunction.LINEAR_NONE
                        });
                    } else {
                        // Instant camera update for high speeds
                        this.viewer.viewer.camera.setView({
                            destination: cameraPosition,
                            orientation: {
                                heading: 0.0,
                                pitch: -Cesium.Math.PI_OVER_TWO,
                                roll: 0.0
                            }
                        });
                    }
                }
                
                // Update time display for current frame
                this.updateTimeDisplay();
                
                // Force scene render for immediate visual feedback
                this.viewer.viewer.scene.requestRender();
                
                // Log frame updates for very slow speeds (debugging)
                if (Math.abs(this.motionSpeed) <= 2 && this.currentOrbitTimeIndex % 30 === 0) {
                    console.log(`🎬 Frame ${this.currentOrbitTimeIndex}/${this.currentOrbitPoints.length} at ${this.motionSpeed}x speed`);
                }
            }
        }, animationSpeed);
    }

    stopMotionAnimation() {
        // COMPLETE STOP - clear any running animation
        if (this.motionControlInterval) {
            clearInterval(this.motionControlInterval);
            this.motionControlInterval = null;
            console.log('🎬 Motion animation STOPPED');
        }

        // If speed is 0, keep satellite frozen at current animated position
        if (this.motionSpeed === 0) {
            console.log('🎬 Satellite FROZEN at current position (PAUSE mode)');
            return; // Keep current animated position
        }

        // Position restoration is handled by disableMotionControl() using original callback
        console.log('🎬 Motion stopped, position will be restored when motion control exits');
    }

    clearMotionControlEntities() {
        this.motionControlEntities.forEach(entity => {
            this.viewer.viewer.entities.remove(entity);
        });
        this.motionControlEntities.clear();
    }
}
