
class SatelliteFilter {
    constructor(satelliteViewer) {
        this.satelliteViewer = satelliteViewer;
        this.activeFilters = {
            category: null,
            country: null,
            agency: null,
            launchYearFrom: null,
            launchYearTo: null,
            orbit: null,
            sensor: null,
            status: null,
            altitudeMin: null,
            altitudeMax: null,
            mission: null,
            resolution: null,
            search: null
        };
        this.filteredSatellites = new Set();

        this.setupEventListeners();
    }

    setupEventListeners() {
        // Filter functionality
        const applyBtn = document.getElementById('applyFiltersBtn');
        if (applyBtn) {
            applyBtn.addEventListener('click', () => {
                this.applyFilters();
            });
        }

        const clearBtn = document.getElementById('clearFiltersBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                this.clearAllFilters();
            });
        }
    }

    applyFilters() {
        // Get filter values from the modal
        this.activeFilters.country = document.getElementById('countryFilter').value || null;
        this.activeFilters.agency = document.getElementById('agencyFilter').value || null;
        this.activeFilters.launchYearFrom = document.getElementById('launchYearFrom').value ? parseInt(document.getElementById('launchYearFrom').value) : null;
        this.activeFilters.launchYearTo = document.getElementById('launchYearTo').value ? parseInt(document.getElementById('launchYearTo').value) : null;
        this.activeFilters.orbit = document.getElementById('orbitFilter').value || null;
        this.activeFilters.sensor = document.getElementById('sensorFilter').value || null;
        this.activeFilters.status = document.getElementById('statusFilter').value || null;
        this.activeFilters.altitudeMin = document.getElementById('altitudeMin').value ? parseInt(document.getElementById('altitudeMin').value) : null;
        this.activeFilters.altitudeMax = document.getElementById('altitudeMax').value ? parseInt(document.getElementById('altitudeMax').value) : null;
        this.activeFilters.mission = document.getElementById('missionFilter').value || null;
        this.activeFilters.resolution = document.getElementById('resolutionFilter').value || null;

        // Apply the filters
        this.applyCurrentFilters();

        // Update active filters display
        this.updateActiveFiltersDisplay();

        // Close the modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('filterModal'));
        if (modal) {
            modal.hide();
        }

        console.log('Filters applied:', this.activeFilters);
    }

    clearAllFilters() {
        // Reset all filters
        this.activeFilters = {
            category: null,
            country: null,
            agency: null,
            launchYearFrom: null,
            launchYearTo: null,
            orbit: null,
            sensor: null,
            status: null,
            altitudeMin: null,
            altitudeMax: null,
            mission: null,
            resolution: null,
            search: null
        };

        // Clear form values
        document.getElementById('countryFilter').value = '';
        document.getElementById('agencyFilter').value = '';
        document.getElementById('launchYearFrom').value = '';
        document.getElementById('launchYearTo').value = '';
        document.getElementById('orbitFilter').value = '';
        document.getElementById('sensorFilter').value = '';
        document.getElementById('statusFilter').value = '';
        document.getElementById('altitudeMin').value = '';
        document.getElementById('altitudeMax').value = '';
        document.getElementById('missionFilter').value = '';
        document.getElementById('resolutionFilter').value = '';

        // Clear search input and filter
        const searchInput = document.getElementById('satelliteSearch');
        if (searchInput) {
            searchInput.value = '';
        }

        // Clear search filter using the search module
        if (this.satelliteViewer.satelliteSearch) {
            this.satelliteViewer.satelliteSearch.clearSearch();
        }

        // Apply the cleared filters
        this.applyCurrentFilters();

        // Update active filters display
        this.updateActiveFiltersDisplay();

        console.log('All filters cleared');
    }

    applyCurrentFilters() {
        console.log(`🎯 Applying filters to ${this.satelliteViewer.satellites.size} satellites`);

        let visibleCount = 0;
        let hiddenCount = 0;

        this.satelliteViewer.satelliteEntities.forEach((entity, noradId) => {
            const satellite = this.satelliteViewer.satellites.get(noradId);
            const shouldShow = this.shouldShowSatellite(satellite);
            const isSelected = noradId === this.satelliteViewer.selectedSatellite;

            if (entity.point) {
                entity.point.show = shouldShow;
            }
            if (entity.label) {
                // Keep selected satellite label visible, hide others
                entity.label.show = shouldShow && isSelected;
            }

            if (shouldShow) {
                visibleCount++;
            } else {
                hiddenCount++;
            }
        });

        console.log(`✅ Visible: ${visibleCount}, Hidden: ${hiddenCount}`);

        // Update visible satellite count in status bar
        const visibleCountElement = document.getElementById('visibleSats');
        const visibleCountBadge = document.getElementById('visibleCount');

        if (visibleCountElement && visibleCountBadge) {
            visibleCountElement.textContent = visibleCount;

            // Show/hide the visible count badge based on whether filters are active
            const hasActiveFilters = Object.values(this.activeFilters).some(filter => filter !== null);
            if (hasActiveFilters) {
                visibleCountBadge.style.display = 'inline-block';
            } else {
                visibleCountBadge.style.display = 'none';
            }
        }

        // Maintain selection appearance after filtering
        if (this.satelliteViewer.selectedSatellite) {
            this.satelliteViewer.updateSatelliteSelection();
        }
    }

    shouldShowSatellite(satellite) {
        if (!satellite) return false;

        // Hide Starlink when toggle is off
        const isStarlink = satellite.category === 'starlink' || satellite.name.toUpperCase().includes('STARLINK');
        if (isStarlink && !this.satelliteViewer.starlinkVisible) return false;

        // Priority satellites (Sentinel, Landsat, WorldView) are ALWAYS visible
        const prioritySatellites = [
            'LANDSAT', 'SENTINEL', 'WORLDVIEW'
        ];

        const isPrioritySatellite = prioritySatellites.some(prefix =>
            satellite.name.toUpperCase().includes(prefix)
        );

        if (isPrioritySatellite) {
            console.log(`⭐ Priority satellite always visible: ${satellite.name}`);
            return true;
        }

        // Category filter - check both satellite.category and derived category
        if (this.activeFilters.category && this.activeFilters.category !== 'all') {
            const satCategory = satellite.category || 'other';

            // Direct category matching - satellite.category should match the filter exactly
            console.log(`🔍 Checking satellite ${satellite.name}: category=${satCategory}, filter=${this.activeFilters.category}`);

            if (satCategory !== this.activeFilters.category) {
                return false;
            }
        }

        // Search filter disabled
        // if (this.activeFilters.search) {
        //     const searchTerm = this.activeFilters.search.toLowerCase();
        //     if (!satellite.name.toLowerCase().includes(searchTerm)) {
        //         return false;
        //     }
        // }

        // Country filter
        if (this.activeFilters.country) {
            const country = this.getSatelliteCountry(satellite);
            if (country !== this.activeFilters.country) {
                return false;
            }
        }

        // Agency filter
        if (this.activeFilters.agency) {
            const agency = this.getSatelliteAgency(satellite);
            if (agency !== this.activeFilters.agency) {
                return false;
            }
        }

        // Launch year filter
        if (this.activeFilters.launchYearFrom || this.activeFilters.launchYearTo) {
            const launchYear = this.getSatelliteLaunchYear(satellite);
            if (this.activeFilters.launchYearFrom && launchYear < this.activeFilters.launchYearFrom) {
                return false;
            }
            if (this.activeFilters.launchYearTo && launchYear > this.activeFilters.launchYearTo) {
                return false;
            }
        }

        // Orbit type filter
        if (this.activeFilters.orbit) {
            const orbitType = this.getSatelliteOrbitType(satellite);
            if (orbitType !== this.activeFilters.orbit) {
                return false;
            }
        }

        // Altitude filter
        if (this.activeFilters.altitudeMin && satellite.altitude < this.activeFilters.altitudeMin) {
            return false;
        }
        if (this.activeFilters.altitudeMax && satellite.altitude > this.activeFilters.altitudeMax) {
            return false;
        }

        // Status filter
        if (this.activeFilters.status) {
            const status = this.getSatelliteStatus(satellite);
            if (status !== this.activeFilters.status) {
                return false;
            }
        }

        // Mission type filter
        if (this.activeFilters.mission) {
            const mission = this.getSatelliteMissionType(satellite);
            if (mission !== this.activeFilters.mission) {
                return false;
            }
        }

        return true;
    }

    updateActiveFiltersDisplay() {
        const activeFiltersContainer = document.getElementById('activeFilters');
        const activeFiltersList = document.getElementById('activeFiltersList');

        if (!activeFiltersContainer || !activeFiltersList) return;

        const activeFilterKeys = Object.keys(this.activeFilters).filter(key => this.activeFilters[key] !== null);

        if (activeFilterKeys.length === 0) {
            activeFiltersContainer.style.display = 'none';
            return;
        }

        activeFiltersContainer.style.display = 'block';
        activeFiltersList.innerHTML = '';

        activeFilterKeys.forEach(filterKey => {
            const filterValue = this.activeFilters[filterKey];
            const badge = document.createElement('span');
            badge.className = 'badge bg-primary me-2 mb-2';
            badge.innerHTML = `${filterKey}: ${filterValue} <i class="fas fa-times ms-1" style="cursor: pointer;" onclick="satelliteViewer.satelliteFilter.removeFilter('${filterKey}')"></i>`;
            activeFiltersList.appendChild(badge);
        });
    }

    removeFilter(filterKey) {
        this.activeFilters[filterKey] = null;
        this.applyCurrentFilters();
        this.updateActiveFiltersDisplay();
    }

    searchSatellites(searchTerm) {
        // Search functionality is now handled by the SatelliteSearch module
        const resultsContainer = document.getElementById('searchResults');
        if (!resultsContainer) return;

        // Clear any existing results
        resultsContainer.innerHTML = '';

        // If search term is provided, let the search module handle it
        if (searchTerm && this.satelliteViewer.satelliteSearch) {
            this.satelliteViewer.satelliteSearch.applySearchFilter(searchTerm);
        } else {
            // Clear search filter
            this.activeFilters.search = null;
            if (this.satelliteViewer.satelliteSearch) {
                this.satelliteViewer.satelliteSearch.clearSearchFilter();
            }
        }
    }

    // Helper methods for satellite properties
    getSatelliteCountry(satellite) {
        const name = satellite.name.toUpperCase();
        if (name.includes('USA') || name.includes('GPS') || name.includes('LANDSAT') || name.includes('NOAA')) return 'usa';
        if (name.includes('COSMOS') || name.includes('GLONASS')) return 'russia';
        if (name.includes('YAOGAN') || name.includes('FENGYUN') || name.includes('BEIDOU')) return 'china';
        if (name.includes('SENTINEL') || name.includes('GALILEO') || name.includes('METEOSAT')) return 'europe';
        if (name.includes('HIMAWARI') || name.includes('ALOS')) return 'japan';
        if (name.includes('RESOURCESAT') || name.includes('CARTOSAT')) return 'india';
        if (name.includes('RADARSAT')) return 'canada';
        return 'other';
    }

    getSatelliteAgency(satellite) {
        const name = satellite.name.toUpperCase();
        if (name.includes('STARLINK')) return 'spacex';
        if (name.includes('GLONASS') || name.includes('COSMOS')) return 'roscosmos';
        if (name.includes('SENTINEL') || name.includes('GALILEO')) return 'esa';
        if (name.includes('YAOGAN') || name.includes('FENGYUN')) return 'cnsa';
        if (name.includes('RESOURCESAT') || name.includes('CARTOSAT')) return 'isro';
        if (name.includes('HIMAWARI') || name.includes('ALOS')) return 'jaxa';
        if (name.includes('NOAA') || name.includes('GOES')) return 'noaa';
        if (name.includes('USA') || name.includes('NROL')) return 'military';
        return 'other';
    }

    getSatelliteLaunchYear(satellite) {
        // Extract from NORAD ID or use a default based on satellite type
        const noradId = satellite.norad_id;
        if (noradId < 10000) return 1970;
        if (noradId < 20000) return 1980;
        if (noradId < 30000) return 1990;
        if (noradId < 40000) return 2000;
        if (noradId < 50000) return 2010;
        return 2020;
    }

    getSatelliteOrbitType(satellite) {
        const altitude = satellite.altitude;
        if (altitude < 2000) return 'leo';
        if (altitude >= 35686 && altitude <= 35886) return 'geo';
        if (altitude < 35786) return 'meo';
        return 'heo';
    }

    getSatelliteStatus(satellite) {
        const name = satellite.name.toUpperCase();
        if (name.includes('DEAD') || name.includes('INACTIVE')) return 'inactive';
        if (name.includes('DEB') || name.includes('DEBRIS')) return 'debris';
        return 'active';
    }

    getSatelliteMissionType(satellite) {
        const name = satellite.name.toUpperCase();
        const category = satellite.category?.toLowerCase() || '';

        if (category.includes('earth_observation') || name.includes('LANDSAT') || name.includes('SENTINEL')) return 'earth_observation';
        if (category.includes('communication') || name.includes('INTELSAT') || name.includes('EUTELSAT')) return 'communication';
        if (category.includes('gps') || name.includes('GPS') || name.includes('GLONASS') || name.includes('GALILEO')) return 'navigation';
        if (category.includes('weather') || name.includes('NOAA') || name.includes('GOES') || name.includes('METEOSAT')) return 'weather';
        if (category.includes('scientific') || name.includes('HUBBLE') || name.includes('KEPLER')) return 'scientific';
        if (category.includes('military') || name.includes('USA') || name.includes('NROL')) return 'military';
        return 'other';
    }

    // Method to show all satellites with current filters (for motion control exit)
    showAllSatellitesWithFilters() {
        this.applyCurrentFilters();
    }

    // Method to filter satellites by pass results (for pass filter integration)
    filterSatellitesByPassResults(passResults) {
        // Create a set of satellite IDs that have passes
        const satellitesWithPasses = new Set(passResults.map(result => result.satellite_id));

        // Hide all satellites except those with passes
        this.satelliteViewer.satelliteEntities.forEach((entity, noradId) => {
            const shouldShow = satellitesWithPasses.has(noradId);

            if (entity.point) {
                entity.point.show = shouldShow;
            }
            if (entity.label) {
                entity.label.show = shouldShow && noradId === this.satelliteViewer.selectedSatellite;
            }
        });

        // Update status
        const visibleCount = satellitesWithPasses.size;
        const visibleCountElement = document.getElementById('visibleSats');
        const visibleCountBadge = document.getElementById('visibleCount');

        if (visibleCountElement && visibleCountBadge) {
            visibleCountElement.textContent = visibleCount;
            visibleCountBadge.style.display = 'inline-block';
        }

        console.log(`🎯 Filtered to show ${visibleCount} satellites with passes`);
    }

    // Method to set category filter (for external use)
    setCategoryFilter(category) {
        this.activeFilters.category = category;
        this.applyCurrentFilters();
        this.updateActiveFiltersDisplay();
    }

    // Method to check if any filters are active
    hasActiveFilters() {
        return Object.values(this.activeFilters).some(filter => filter !== null);
    }
}

// Add CSS styles for search results
if (!document.getElementById('searchModuleCSS')) {
    const style = document.createElement('style');
    style.id = 'searchModuleCSS';
    style.textContent = `
        .search-results-container {
            scrollbar-width: thin;
            scrollbar-color: rgba(100, 181, 246, 0.3) transparent;
            min-width: 280px;
            max-width: 320px;
            position: relative;
            z-index: 10000;
        }

        .search-results-container::-webkit-scrollbar {
            width: 6px;
        }

        .search-results-container::-webkit-scrollbar-track {
            background: transparent;
        }

        .search-results-container::-webkit-scrollbar-thumb {
            background: rgba(100, 181, 246, 0.3);
            border-radius: 3px;
        }

        .search-results-header {
            padding: 8px 12px;
            border-bottom: 1px solid rgba(100, 181, 246, 0.2);
            font-size: 0.75rem;
            color: #64b5f6;
        }

        .search-results-list {
            max-height: 320px;
            overflow-y: auto;
            overflow-x: hidden;
        }

        .search-result-item {
            padding: 8px 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            cursor: pointer;
            transition: all 0.2s ease;
            position: relative;
        }

        .search-result-item:hover {
            border-left: 3px solid #64b5f6;
            padding-left: 9px;
        }

        .search-result-item.highlighted {
            border-left: 3px solid #64b5f6;
            padding-left: 9px;
        }

        .result-main {
            display: flex;
            flex-direction: column;
            gap: 3px;
        }

        .result-name {
            display: flex;
            align-items: flex-start;
            gap: 8px;
            width: 100%;
        }

        .sat-icon {
            color: #64b5f6;
            font-size: 0.9rem;
            margin-top: 1px;
            flex-shrink: 0;
        }

        .sat-details {
            flex: 1;
            min-width: 0;
        }

        .sat-name {
            font-size: 0.85rem;
            font-weight: 600;
            color: #e2e8f0;
            margin-bottom: 3px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            line-height: 1.2;
        }

        .result-details {
            display: flex;
            gap: 8px;
            font-size: 0.7rem;
            align-items: center;
            flex-wrap: nowrap;
        }

        .detail-item {
            white-space: nowrap;
            font-weight: 500;
        }

        .detail-item.norad-id {
            color: #9ca3af;
        }

        .detail-item.altitude {
            color: #22c55e;
            display: flex;
            align-items: center;
            gap: 2px;
        }

        .detail-item.status-active {
            color: #4caf50;
        }

        .detail-item.status-inactive {
            color: #ff9800;
        }

        .altitude-icon {
            font-size: 0.6rem;
            color: #22c55e;
        }

        .search-loading, .search-no-results, .search-error {
            padding: 16px;
            text-align: center;
            font-size: 0.8rem;
        }

        mark.bg-warning {
            background: transparent !important;
            color: #ffc107 !important;
            font-weight: 600;
        }

        /* Full screen responsive adjustments */
        @media (min-width: 1200px) {
            .search-results-container {
                max-width: 350px;
            }
            
            .search-results-list {
                max-height: 400px;
            }
        }

        /* Mobile responsiveness */
        @media (max-width: 768px) {
            .search-results-container {
                max-height: 280px;
                min-width: 260px;
                max-width: 300px;
            }
            
            .search-result-item {
                padding: 6px 10px;
            }
            
            .sat-name {
                font-size: 0.8rem;
            }

            .result-details {
                font-size: 0.65rem;
                gap: 6px;
            }
        }
    `;
    document.head.appendChild(style);
}
