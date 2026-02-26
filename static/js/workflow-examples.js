
// Examples of how to use the new SatelliteWorkflow class

// Example 1: Using the workflow from a click event (original pattern)
function handleSatelliteClick(noradId) {
    // Simple single-click selection
    satelliteViewer.satelliteWorkflow.executeSatelliteSelectionWorkflow(noradId, false, 'click');
}

function handleSatelliteDoubleClick(noradId) {
    // Double-click with tracking enabled
    satelliteViewer.satelliteWorkflow.executeSatelliteSelectionWorkflow(noradId, true, 'doubleclick');
}

// Example 2: Custom event listener that uses the same workflow
document.getElementById('myCustomButton').addEventListener('click', async () => {
    const noradId = 25544; // ISS example
    const result = await satelliteViewer.satelliteWorkflow.executeSatelliteSelectionWorkflow(noradId, true);
    
    if (result.success) {
        console.log('Satellite selected successfully:', result.satellite.name);
    } else {
        console.error('Selection failed:', result.error);
    }
});

// Example 3: Search-based selection using workflow
document.getElementById('searchButton').addEventListener('click', async () => {
    const query = document.getElementById('searchInput').value;
    const result = await satelliteViewer.satelliteWorkflow.executeSearchAndSelectWorkflow(query);
    
    if (result.success) {
        console.log('Search and select completed');
    } else {
        console.error('Search failed:', result.error);
    }
});

// Example 4: Quick info on hover (lighter workflow)
function handleSatelliteHover(noradId) {
    satelliteViewer.satelliteWorkflow.executeQuickInfoWorkflow(noradId);
}

// Example 5: Category-based selection
document.getElementById('earthObservationBtn').addEventListener('click', () => {
    satelliteViewer.satelliteWorkflow.executeCategorySelectWorkflow('earth_observation');
});

// Example 6: Batch operations on multiple satellites
document.getElementById('highlightAllISS').addEventListener('click', () => {
    const issNoradIds = [25544, 48274]; // ISS and related modules
    satelliteViewer.satelliteWorkflow.executeBatchSatelliteWorkflow(issNoradIds, 'highlight');
});

// Example 7: Custom workflow for a specific use case
document.getElementById('weatherSatelliteBtn').addEventListener('click', async () => {
    const customSteps = {
        filter_weather_satellites: async () => {
            // Filter to show only weather satellites
            satelliteViewer.satelliteFilter.setCategoryFilter('weather');
            
            // Find all weather satellites
            const weatherSats = [];
            satelliteViewer.satellites.forEach((satellite, noradId) => {
                if (satellite.name.toUpperCase().includes('NOAA') || 
                    satellite.name.toUpperCase().includes('GOES') ||
                    satellite.name.toUpperCase().includes('METEOSAT')) {
                    weatherSats.push(satellite);
                }
            });
            
            return weatherSats;
        },

        select_best_weather_satellite: async () => {
            const weatherSats = satelliteWorkflow.workflowData.filter_weather_satellites_result;
            if (weatherSats.length === 0) {
                throw new Error('No weather satellites found');
            }
            
            // Select the first GOES satellite if available, otherwise first weather sat
            const goesSat = weatherSats.find(sat => sat.name.toUpperCase().includes('GOES'));
            const selectedSat = goesSat || weatherSats[0];
            
            return await satelliteViewer.satelliteWorkflow.executeSatelliteSelectionWorkflow(
                selectedSat.norad_id, false, 'weather_workflow'
            );
        },

        show_weather_info: async () => {
            // Show additional weather-specific information
            const toast = document.createElement('div');
            toast.className = 'toast show position-fixed';
            toast.style.cssText = 'top: 150px; right: 20px; z-index: 9999;';
            toast.innerHTML = `
                <div class="toast-header bg-info text-white">
                    <i class="fas fa-cloud-sun me-2"></i>
                    <strong class="me-auto">Weather Satellite Mode</strong>
                </div>
                <div class="toast-body bg-dark text-light">
                    Weather satellite selected. Check imagery links for latest weather data.
                </div>
            `;
            document.body.appendChild(toast);
            
            setTimeout(() => {
                if (document.body.contains(toast)) {
                    document.body.removeChild(toast);
                }
            }, 4000);
        }
    };

    const result = await satelliteViewer.satelliteWorkflow.executeCustomWorkflow(
        'weather_satellite_selection', 
        customSteps
    );
    
    if (result.success) {
        console.log('Weather satellite workflow completed successfully');
    } else {
        console.error('Weather satellite workflow failed:', result.error);
    }
});

// Example 8: API-triggered workflow (for external integrations)
async function apiSelectSatellite(noradId, options = {}) {
    const {
        enableTracking = false,
        showToast = true,
        focusCamera = true
    } = options;

    const result = await satelliteViewer.satelliteWorkflow.executeSatelliteSelectionWorkflow(
        noradId, 
        enableTracking, 
        'api'
    );

    if (result.success && showToast) {
        const toast = document.createElement('div');
        toast.className = 'toast show position-fixed';
        toast.style.cssText = 'bottom: 20px; right: 20px; z-index: 9999;';
        toast.innerHTML = `
            <div class="toast-body bg-success text-white">
                <i class="fas fa-check-circle me-2"></i>
                Satellite ${result.satellite.name} selected via API
            </div>
        `;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            if (document.body.contains(toast)) {
                document.body.removeChild(toast);
            }
        }, 3000);
    }

    return result;
}

// Example 9: Keyboard shortcut integration
document.addEventListener('keydown', async (e) => {
    // Press 'S' to select random satellite using workflow
    if (e.key === 's' && !e.ctrlKey && !e.metaKey) {
        const satelliteIds = Array.from(satelliteViewer.satellites.keys());
        if (satelliteIds.length > 0) {
            const randomId = satelliteIds[Math.floor(Math.random() * satelliteIds.length)];
            await satelliteViewer.satelliteWorkflow.executeSatelliteSelectionWorkflow(randomId);
        }
    }
    
    // Press 'I' for quick info of current satellite
    if (e.key === 'i' && satelliteViewer.selectedSatellite) {
        await satelliteViewer.satelliteWorkflow.executeQuickInfoWorkflow(satelliteViewer.selectedSatellite);
    }
});

// Example 10: Integration with existing search module
class EnhancedSatelliteSearch extends SatelliteSearch {
    async selectSatelliteFromSearch(noradId) {
        console.log(`🔍 Enhanced search: selecting satellite ${noradId} using workflow`);
        
        // Use the workflow instead of direct selection
        const result = await this.satelliteViewer.satelliteWorkflow.executeSatelliteSelectionWorkflow(
            noradId, 
            true, 
            'search'
        );
        
        if (result.success) {
            // Clear search state after successful selection
            this.currentQuery = '';
            this.searchInput.value = '';
            this.searchResults = [];
            this.clearSearchFilter();
        } else {
            this.showSelectionError(result.error);
        }
        
        this.isSelectingFromSearch = false;
        return result;
    }
}
