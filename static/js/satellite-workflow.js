
class SatelliteWorkflow {
    constructor(satelliteViewer) {
        this.viewer = satelliteViewer;
        this.workflowSteps = new Map();
        this.currentWorkflow = null;
        this.workflowData = {};
    }

    // Define the complete satellite selection workflow
    async executeSatelliteSelectionWorkflow(noradId, enableTracking = false, source = 'click') {
        console.log(`🔄 Starting satellite selection workflow for ${noradId}`);
        
        this.currentWorkflow = 'satellite_selection';
        this.workflowData = { noradId, enableTracking, source, startTime: Date.now() };

        try {
            // Step 1: Validate satellite exists
            await this.executeStep('validate_satellite', async () => {
                const satellite = this.viewer.satellites.get(noradId);
                if (!satellite) {
                    throw new Error(`Satellite ${noradId} not found`);
                }
                return satellite;
            });

            // Step 2: Clear previous selections
            await this.executeStep('clear_previous_selection', async () => {
                if (this.viewer.currentMode === 'airplanes') {
                    this.viewer.deselectAirplane();
                    this.viewer.stopRealTimeAirplaneUpdates();
                }

                if (this.viewer.selectedSatellite && this.viewer.selectedSatellite !== noradId) {
                    this.viewer.clearSatelliteVisualizations(this.viewer.selectedSatellite);
                }
            });

            // Step 3: Set selection state
            await this.executeStep('set_selection', async () => {
                this.viewer.selectedSatellite = noradId;

                // Ensure entity exists and is visible
                let entity = this.viewer.satelliteEntities.get(noradId);
                if (!entity) {
                    console.warn(`Entity for satellite ${noradId} not found, checking viewer...`);

                    // Check if entity exists in viewer but not in map
                    const viewerEntity = this.viewer.viewer.entities.getById(`satellite_${noradId}`);
                    if (viewerEntity) {
                        // Re-associate existing entity with map
                        this.viewer.satelliteEntities.set(noradId, viewerEntity);
                        entity = viewerEntity;
                        console.log(`✅ Re-associated existing entity for satellite ${noradId}`);
                    } else {
                        // Entity truly missing, create all (with duplicate protection)
                        console.warn(`🔨 Entity missing, recreating entities...`);
                        this.viewer.createAllSatelliteEntities();
                        entity = this.viewer.satelliteEntities.get(noradId);
                    }
                }

                if (entity && entity.point) {
                    entity.point.show = true;
                }
            });

            // Step 4: Update visual selection
            await this.executeStep('update_visuals', async () => {
                this.viewer.updateSatelliteSelection();
            });

            // Step 5: Focus camera on satellite
            await this.executeStep('focus_camera', async () => {
                this.viewer.focusOnSatellite(noradId);
            });

            // Step 6: Load detailed information
            await this.executeStep('load_details', async () => {
                await this.viewer.loadSatelliteDetails(noradId);
            });

            // Step 7: Start real-time updates
            await this.executeStep('start_updates', async () => {
                this.viewer.startRealTimeDetailsUpdates(noradId);
            });

            // Step 8: Handle orbital visualizations
            await this.executeStep('orbital_visualizations', async () => {
                if (this.viewer.showOrbits) {
                    await this.viewer.showOrbitPath(noradId);
                }

                if (this.viewer.showGroundTracks && this.viewer.isEarthObservationSatellite(noradId)) {
                    this.viewer.renderNadirLine(noradId);
                }

                // Coverage swath visualization for EO satellites
                if (this.viewer.showCoverageSwath) {
                    await this.viewer.showCoverageSwathPath(noradId);
                }

                // Animated ground swath for EO satellites
                if (this.viewer.showGroundSwath) {
                    this.viewer.startGroundSwathAnimation(noradId);
                }
            });

            // Step 9: Load pass predictions for LEO satellites
            await this.executeStep('load_passes', async () => {
                const satellite = this.viewer.satellites.get(noradId);
                if (satellite && satellite.altitude < 10000 && 
                    (this.viewer.userLocation.lat !== 0 || this.viewer.userLocation.lon !== 0)) {
                    await this.viewer.loadPassPredictions(noradId);
                }
            });

            // Step 10: Handle tracking if enabled
            await this.executeStep('enable_tracking', async () => {
                if (enableTracking) {
                    this.viewer.trackSatellite(noradId);
                }
            });

            // Step 11: Show details panel
            await this.executeStep('show_panel', async () => {
                return new Promise((resolve) => {
                    const showPanel = () => {
                        // Try our dedicated method first
                        if (this.forceShowDetailsPanel()) {
                            resolve({ panelShown: true, method: 'workflow_force' });
                            return;
                        }
                        
                        // Fallback to global function
                        if (typeof window.showDetailsPanel === 'function') {
                            window.showDetailsPanel();
                            resolve({ panelShown: true, method: 'global_function' });
                            return;
                        }
                        
                        console.warn('📱 Could not show details panel - no available methods');
                        resolve({ panelShown: false, error: 'No panel show methods available' });
                    };

                    // Try immediately first
                    if (document.readyState === 'complete') {
                        showPanel();
                    } else {
                        // If DOM not ready, wait for it
                        setTimeout(showPanel, 100);
                    }
                });
            });

            console.log(`✅ Satellite selection workflow completed for ${noradId} in ${Date.now() - this.workflowData.startTime}ms`);
            return { success: true, satellite: this.viewer.satellites.get(noradId) };

        } catch (error) {
            console.error(`❌ Satellite selection workflow failed for ${noradId}:`, error);
            this.handleWorkflowError(error);
            return { success: false, error: error.message };
        } finally {
            this.currentWorkflow = null;
            this.workflowData = {};
        }
    }

    // Generic workflow executor for reusable patterns
    async executeCustomWorkflow(workflowName, steps, data = {}) {
        console.log(`🔄 Starting custom workflow: ${workflowName}`);
        
        this.currentWorkflow = workflowName;
        this.workflowData = { ...data, startTime: Date.now() };

        try {
            for (const [stepName, stepFunction] of Object.entries(steps)) {
                await this.executeStep(stepName, stepFunction);
            }

            console.log(`✅ Custom workflow '${workflowName}' completed in ${Date.now() - this.workflowData.startTime}ms`);
            return { success: true, data: this.workflowData };

        } catch (error) {
            console.error(`❌ Custom workflow '${workflowName}' failed:`, error);
            this.handleWorkflowError(error);
            return { success: false, error: error.message };
        } finally {
            this.currentWorkflow = null;
            this.workflowData = {};
        }
    }

    // Execute individual workflow step with error handling and logging
    async executeStep(stepName, stepFunction) {
        const stepStart = Date.now();
        
        try {
            console.log(`  📋 Executing step: ${stepName}`);
            const result = await stepFunction();
            
            const duration = Date.now() - stepStart;
            console.log(`  ✅ Step '${stepName}' completed in ${duration}ms`);
            
            // Store step result for potential use in later steps
            this.workflowData[`${stepName}_result`] = result;
            this.workflowData[`${stepName}_duration`] = duration;
            
            return result;
        } catch (error) {
            const duration = Date.now() - stepStart;
            console.error(`  ❌ Step '${stepName}' failed after ${duration}ms:`, error);
            throw new Error(`Workflow step '${stepName}' failed: ${error.message}`);
        }
    }

    handleWorkflowError(error) {
        // Reset any partial state changes on workflow failure
        if (this.currentWorkflow === 'satellite_selection') {
            // Clean up any partial satellite selection state
            this.viewer.stopRealTimeDetailsUpdates();
            
            if (this.workflowData.noradId && this.viewer.selectedSatellite === this.workflowData.noradId) {
                this.viewer.selectedSatellite = null;
                this.viewer.updateSatelliteSelection();
            }
        }

        // Show error to user
        this.viewer.showError(`Workflow failed: ${error.message}`);
    }

    // Pre-built workflow patterns for common operations

    // Pattern 1: Search and select satellite
    async executeSearchAndSelectWorkflow(query) {
        const steps = {
            search_satellite: async () => {
                if (!this.viewer.satelliteSearch) {
                    throw new Error('Search module not initialized');
                }
                
                const results = await this.viewer.satelliteSearch.performSearch(query);
                if (results.length === 0) {
                    throw new Error(`No satellites found for query: ${query}`);
                }
                return results[0]; // Return best match
            },

            select_from_search: async () => {
                const satellite = this.workflowData.search_satellite_result;
                return await this.executeSatelliteSelectionWorkflow(satellite.norad_id, true, 'search');
            }
        };

        return await this.executeCustomWorkflow('search_and_select', steps, { query });
    }

    // Pattern 2: Category filter and select first satellite
    async executeCategorySelectWorkflow(category) {
        const steps = {
            apply_category_filter: async () => {
                if (!this.viewer.satelliteFilter) {
                    throw new Error('Filter module not initialized');
                }
                
                this.viewer.satelliteFilter.setCategoryFilter(category);
                
                // Find first visible satellite in this category
                let firstSatellite = null;
                this.viewer.satellites.forEach((satellite, noradId) => {
                    if (!firstSatellite && this.viewer.satelliteFilter.shouldShowSatellite(satellite)) {
                        firstSatellite = satellite;
                    }
                });
                
                if (!firstSatellite) {
                    throw new Error(`No satellites found in category: ${category}`);
                }
                
                return firstSatellite;
            },

            select_category_satellite: async () => {
                const satellite = this.workflowData.apply_category_filter_result;
                return await this.executeSatelliteSelectionWorkflow(satellite.norad_id, false, 'category');
            }
        };

        return await this.executeCustomWorkflow('category_select', steps, { category });
    }

    // Pattern 3: Quick satellite info workflow (without full selection)
    async executeQuickInfoWorkflow(noradId) {
        const steps = {
            validate_satellite: async () => {
                const satellite = this.viewer.satellites.get(noradId);
                if (!satellite) {
                    throw new Error(`Satellite ${noradId} not found`);
                }
                return satellite;
            },

            load_quick_details: async () => {
                const url = `/api/satellite/${noradId}?lat=${this.viewer.userLocation.lat}&lon=${this.viewer.userLocation.lon}&alt=${this.viewer.userLocation.alt}`;
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return await response.json();
            },

            show_quick_info: async () => {
                const data = this.workflowData.load_quick_details_result;
                if (data.success && data.satellite) {
                    // Show quick info in a toast or modal instead of full panel
                    this.showQuickInfoToast(data.satellite);
                }
            }
        };

        return await this.executeCustomWorkflow('quick_info', steps, { noradId });
    }

    // Pattern 4: Batch satellite operation workflow
    async executeBatchSatelliteWorkflow(noradIds, operation) {
        const steps = {
            validate_batch: async () => {
                const validSatellites = [];
                for (const noradId of noradIds) {
                    const satellite = this.viewer.satellites.get(noradId);
                    if (satellite) {
                        validSatellites.push(satellite);
                    }
                }
                if (validSatellites.length === 0) {
                    throw new Error('No valid satellites found in batch');
                }
                return validSatellites;
            },

            execute_batch_operation: async () => {
                const satellites = this.workflowData.validate_batch_result;
                const results = [];
                
                for (const satellite of satellites) {
                    try {
                        let result;
                        switch (operation) {
                            case 'highlight':
                                result = this.highlightSatellite(satellite.norad_id);
                                break;
                            case 'load_passes':
                                result = await this.viewer.loadPassPredictions(satellite.norad_id);
                                break;
                            case 'show_orbit':
                                result = await this.viewer.showOrbitPath(satellite.norad_id);
                                break;
                            default:
                                result = { success: false, error: `Unknown operation: ${operation}` };
                        }
                        results.push({ noradId: satellite.norad_id, result });
                    } catch (error) {
                        results.push({ noradId: satellite.norad_id, error: error.message });
                    }
                }
                
                return results;
            }
        };

        return await this.executeCustomWorkflow('batch_operation', steps, { noradIds, operation });
    }

    // Utility method to highlight a satellite without full selection
    highlightSatellite(noradId) {
        const entity = this.viewer.satelliteEntities.get(noradId);
        if (entity && entity.point) {
            const originalColor = entity.point.color;
            entity.point.color = Cesium.Color.YELLOW;
            entity.point.pixelSize = 6;
            
            // Reset after 3 seconds
            setTimeout(() => {
                const satellite = this.viewer.satellites.get(noradId);
                if (satellite && entity.point) {
                    entity.point.color = Cesium.Color.fromCssColorString(satellite.color);
                    entity.point.pixelSize = 3;
                }
            }, 3000);
            
            return { success: true, message: 'Satellite highlighted' };
        }
        return { success: false, error: 'Entity not found' };
    }

    // Show quick info in a toast notification
    showQuickInfoToast(satelliteData) {
        const toast = document.createElement('div');
        toast.className = 'toast show position-fixed';
        toast.style.cssText = 'top: 100px; right: 20px; z-index: 9999; max-width: 300px;';
        
        toast.innerHTML = `
            <div class="toast-header bg-dark text-light">
                <i class="fas fa-satellite text-primary me-2"></i>
                <strong class="me-auto">${satelliteData.name}</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body bg-dark text-light">
                <small>
                    <strong>Alt:</strong> ${satelliteData.orbit.altitude.toFixed(1)} km<br>
                    <strong>Pos:</strong> ${satelliteData.position.latitude.toFixed(2)}°, ${satelliteData.position.longitude.toFixed(2)}°<br>
                    <strong>Period:</strong> ${satelliteData.orbit.period.toFixed(1)} min<br>
                    <strong>Country:</strong> ${satelliteData.position.country}
                </small>
            </div>
        `;
        
        document.body.appendChild(toast);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (document.body.contains(toast)) {
                document.body.removeChild(toast);
            }
        }, 5000);

        // Handle close button
        const closeBtn = toast.querySelector('.btn-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                if (document.body.contains(toast)) {
                    document.body.removeChild(toast);
                }
            });
        }
    }

    // Dedicated method to ensure panel visibility with fade animation
    forceShowDetailsPanel() {
        const panel = document.getElementById('satelliteDetailsPanel');
        if (panel) {
            panel.style.display = 'block';
            panel.classList.remove('fade-out');
            // Force reflow to ensure display change takes effect
            panel.offsetHeight;
            panel.classList.add('show');
            console.log('🔧 Workflow forced panel to show with animation');
            return true;
        }
        return false;
    }

    // Dedicated method to hide panel with fade animation
    forceHideDetailsPanel() {
        const panel = document.getElementById('satelliteDetailsPanel');
        if (panel) {
            panel.classList.add('fade-out');
            panel.classList.remove('show');
            
            // Hide panel after animation completes
            setTimeout(() => {
                if (panel.classList.contains('fade-out')) {
                    panel.style.display = 'none';
                    panel.classList.remove('fade-out');
                }
            }, 300);
            
            console.log('🔧 Workflow forced panel to hide with animation');
            return true;
        }
        return false;
    }

    // Get workflow status
    getWorkflowStatus() {
        return {
            currentWorkflow: this.currentWorkflow,
            isRunning: this.currentWorkflow !== null,
            data: { ...this.workflowData }
        };
    }

    // Cancel current workflow
    cancelCurrentWorkflow() {
        if (this.currentWorkflow) {
            console.log(`🚫 Cancelling workflow: ${this.currentWorkflow}`);
            this.currentWorkflow = null;
            this.workflowData = {};
        }
    }

    // Create workflow patterns for different event types
    createEventPattern(eventType, customSteps = {}) {
        const patterns = {
            'click': () => this.executeSatelliteSelectionWorkflow,
            'doubleclick': (noradId) => this.executeSatelliteSelectionWorkflow(noradId, true, 'doubleclick'),
            'hover': (noradId) => this.executeQuickInfoWorkflow(noradId),
            'search': (query) => this.executeSearchAndSelectWorkflow(query),
            'category': (category) => this.executeCategorySelectWorkflow(category),
            'batch': (noradIds, operation) => this.executeBatchSatelliteWorkflow(noradIds, operation)
        };

        return patterns[eventType] || null;
    }
}
