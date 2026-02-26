
class SatelliteSearch {
    constructor(satelliteViewer) {
        this.satelliteViewer = satelliteViewer;
        this.searchResults = [];
        this.isSearching = false;
        this.searchTimeout = null;
        this.currentQuery = '';
        this.maxResults = 50;
        this.isSelectingFromSearch = false; // Track selection state

        this.setupSearchInterface();
        this.setupEventListeners();
    }

    setupSearchInterface() {
        // Get the existing search input
        this.searchInput = document.getElementById('satelliteSearch');
        if (!this.searchInput) {
            console.warn('⚠️ SatelliteSearch: #satelliteSearch input not found in DOM');
            return;
        }

        // Create results container if it doesn't exist
        if (!document.getElementById('searchResultsContainer')) {
            const resultsContainer = document.createElement('div');
            resultsContainer.id = 'searchResultsContainer';
            resultsContainer.className = 'search-results-container';
            resultsContainer.style.cssText = `
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                background: linear-gradient(135deg, rgba(26, 26, 46, 0.98) 0%, rgba(12, 12, 12, 0.98) 100%);
                border: 1px solid rgba(100, 181, 246, 0.3);
                border-top: none;
                border-radius: 0 0 10px 10px;
                max-height: 400px;
                overflow-y: auto;
                backdrop-filter: blur(15px);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
                z-index: 9999;
                display: none;
            `;

            // Insert after the search input
            this.searchInput.parentNode.style.position = 'relative';
            this.searchInput.parentNode.appendChild(resultsContainer);
        }

        this.resultsContainer = document.getElementById('searchResultsContainer');
    }

    setupEventListeners() {
        if (!this.searchInput) return;

        // Input event for responsive search
        this.searchInput.addEventListener('input', (e) => {
            this.handleSearchInput(e.target.value);
        });

        // Focus and blur events
        this.searchInput.addEventListener('focus', () => {
            if (this.searchResults.length > 0) {
                this.showResults();
            }
        });

        this.searchInput.addEventListener('blur', () => {
            // Delay hiding to allow for click events
            setTimeout(() => {
                this.hideResults();
            }, 200);
        });

        // Keyboard navigation
        this.searchInput.addEventListener('keydown', (e) => {
            this.handleKeyNavigation(e);
        });

        // Add global keyboard shortcut for search
        document.addEventListener('keydown', (e) => {
            // Ctrl+F or Cmd+F to focus search (prevent default browser search)
            if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
                e.preventDefault();
                this.searchInput.focus();
                this.searchInput.select();
            }
            // Escape to clear search
            else if (e.key === 'Escape' && document.activeElement === this.searchInput) {
                this.clearSearch();
                this.searchInput.blur();
            }
        });

        // Close results when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.searchInput.contains(e.target) && !this.resultsContainer.contains(e.target)) {
                this.hideResults();
            }
        });
    }

    handleSearchInput(query) {
        this.currentQuery = query.trim();

        // Clear previous timeout
        if (this.searchTimeout) {
            clearTimeout(this.searchTimeout);
        }

        // Clear results and apply filter if query is empty
        if (this.currentQuery.length === 0) {
            this.hideResults();
            this.clearSearchFilter();
            return;
        }

        // For very short queries, just apply filter without showing dropdown
        if (this.currentQuery.length < 2) {
            this.applySearchFilter(this.currentQuery);
            this.hideResults();
            return;
        }

        // For longer queries, show dropdown and apply filter
        this.searchTimeout = setTimeout(() => {
            this.performSearch(this.currentQuery);
            this.applySearchFilter(this.currentQuery);
        }, 300);
    }

    async performSearch(query) {
        if (this.isSearching) return;

        this.isSearching = true;
        this.showLoadingState();

        try {
            // Search through loaded satellites
            const results = this.searchInLoadedSatellites(query);

            // If we have few results, try API search for more
            if (results.length < 10) {
                const apiResults = await this.searchViaAPI(query);

                // Merge results, avoiding duplicates
                const existingIds = new Set(results.map(r => r.norad_id));
                apiResults.forEach(result => {
                    if (!existingIds.has(result.norad_id)) {
                        results.push(result);
                    }
                });
            }

            this.searchResults = results.slice(0, this.maxResults);
            this.displayResults();

        } catch (error) {
            console.error('Search error:', error);
            this.showErrorState();
        } finally {
            this.isSearching = false;
        }
    }

    searchInLoadedSatellites(query) {
        const results = [];
        const queryLower = query.toLowerCase();

        this.satelliteViewer.satellites.forEach((satellite, noradId) => {
            const name = satellite.name.toLowerCase();
            let score = 0;

            // Scoring system for relevance
            if (name === queryLower) {
                score = 100; // Exact match
            } else if (name.startsWith(queryLower)) {
                score = 80; // Starts with query
            } else if (name.includes(queryLower)) {
                score = 60; // Contains query
            } else {
                // Check individual words with more flexible matching
                const queryWords = queryLower.split(/\s+/);
                const nameWords = name.split(/[\s-]+/); // Split on space or dash

                let wordMatches = 0;
                queryWords.forEach(queryWord => {
                    nameWords.forEach(nameWord => {
                        if (nameWord.includes(queryWord) || queryWord.includes(nameWord)) {
                            wordMatches++;
                        }
                    });
                });

                if (wordMatches > 0) {
                    score = Math.min(50, wordMatches * 15);
                }
            }

            // Boost priority satellites (Sentinel, Landsat, WorldView) - check both name and category
            const isPriority = name.includes('landsat') ||
                name.includes('sentinel') ||
                name.includes('worldview') ||
                name.includes('swarm');

            if (isPriority) {
                score += 20;
                console.log(`⭐ Priority satellite found: ${satellite.name} (score: ${score})`);
            }

            if (score > 0) {
                results.push({
                    ...satellite,
                    score: score,
                    source: 'loaded'
                });
            }
        });

        // Sort by score
        results.sort((a, b) => b.score - a.score);

        console.log(`🔍 Search "${query}" found ${results.length} satellites (${results.filter(r => r.score > 70).length} high-priority)`);

        return results;
    }

    async searchViaAPI(query) {
        try {
            const response = await fetch(`/api/satellites/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();

            if (data.success && data.satellites) {
                return data.satellites.map(sat => ({
                    ...sat,
                    score: 30, // Lower score for API results
                    source: 'api'
                }));
            }
        } catch (error) {
            console.warn('API search failed:', error);
        }

        return [];
    }

    displayResults() {
        if (!this.resultsContainer) return;

        if (this.searchResults.length === 0) {
            this.showNoResults();
            return;
        }

        const resultsHTML = this.searchResults.map((satellite, index) => {
            const status = this.satelliteViewer.satelliteFilter.getSatelliteStatus(satellite);
            const isLoaded = satellite.source === 'loaded';
            const altitude = satellite.altitude ? Math.round(satellite.altitude) : 'N/A';

            return `
                <div class="search-result-item" data-norad-id="${satellite.norad_id}" data-index="${index}">
                    <div class="result-main">
                        <div class="result-name">
                            <div class="sat-icon">
                                <i class="fas fa-satellite"></i>
                            </div>
                            <div class="sat-details">
                                <div class="sat-name">${this.highlightMatch(satellite.name, this.currentQuery)}</div>
                                <div class="result-details">
                                    <span class="detail-item norad-id">ID: ${satellite.norad_id}</span>
                                    <span class="detail-item altitude">
                                        <i class="fas fa-arrow-up altitude-icon"></i> ${altitude}
                                    </span>
                                    <span class="detail-item status-${status}">${status}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        this.resultsContainer.innerHTML = `
            <div class="search-results-header">
                <i class="fas fa-search"></i> ${this.searchResults.length} results for "${this.currentQuery}"
            </div>
            <div class="search-results-list">
                ${resultsHTML}
            </div>
        `;

        this.attachResultClickHandlers();
        this.showResults();
    }

    attachResultClickHandlers() {
        const resultItems = this.resultsContainer.querySelectorAll('.search-result-item');

        resultItems.forEach((item, index) => {
            item.addEventListener('click', () => {
                const noradId = parseInt(item.dataset.noradId);
                this.selectSatelliteFromSearch(noradId);
            });

            // Hover effects
            item.addEventListener('mouseenter', () => {
                item.style.background = 'rgba(100, 181, 246, 0.1)';
                item.style.borderColor = 'rgba(100, 181, 246, 0.5)';
            });

            item.addEventListener('mouseleave', () => {
                item.style.background = '';
                item.style.borderColor = '';
            });
        });
    }

    async selectSatelliteFromSearch(noradId) {
        console.log(`🔍 Selecting satellite ${noradId} from search results using workflow`);

        // Set selection state to prevent auto-update interference
        this.isSelectingFromSearch = true;

        // Hide search results first
        this.hideResults();

        try {
            // Check if satellite is loaded
            const satellite = this.satelliteViewer.satellites.get(noradId);

            if (satellite) {
                console.log(`🔍 Found loaded satellite ${satellite.name}, using workflow`);

                // Use the centralized workflow system for consistent behavior
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
                    console.log(`✅ Workflow completed for satellite: ${satellite.name}`);
                } else {
                    this.showSelectionError(result.error);
                }

            } else {
                // Satellite not loaded - load it first then use workflow
                this.showLoadingSelection(noradId);

                const response = await fetch(`/api/satellite/${noradId}`);
                const data = await response.json();

                if (data.success && data.satellite) {
                    // Add satellite to loaded satellites temporarily
                    const tempSatellite = {
                        norad_id: noradId,
                        name: data.satellite.name,
                        latitude: data.satellite.position.latitude,
                        longitude: data.satellite.position.longitude,
                        altitude: data.satellite.orbit.altitude,
                        color: '#FF6B6B',
                        category: 'search_result'
                    };

                    this.satelliteViewer.satellites.set(noradId, tempSatellite);
                    this.createSearchResultEntity(tempSatellite);

                    // Now use workflow for consistent selection process
                    const result = await this.satelliteViewer.satelliteWorkflow.executeSatelliteSelectionWorkflow(
                        noradId,
                        true,
                        'search-api'
                    );

                    if (result.success) {
                        this.searchInput.value = '';
                        this.currentQuery = '';
                        this.clearSearchFilter();
                    } else {
                        this.showSelectionError(result.error);
                    }

                } else {
                    this.showSelectionError('Satellite data not available');
                }
            }

        } catch (error) {
            console.error('Error in search selection:', error);
            this.showSelectionError('Failed to load satellite');
        } finally {
            this.isSelectingFromSearch = false;
        }
    }

    createSearchResultEntity(satellite) {
        const noradId = satellite.norad_id;

        // Create dynamic position
        const position = new Cesium.CallbackProperty(() => {
            const currentSat = this.satelliteViewer.satellites.get(noradId);
            if (currentSat) {
                return Cesium.Cartesian3.fromDegrees(
                    currentSat.longitude,
                    currentSat.latitude,
                    currentSat.altitude * 1000
                );
            }
            return Cesium.Cartesian3.fromDegrees(
                satellite.longitude,
                satellite.latitude,
                satellite.altitude * 1000
            );
        }, false);

        const entity = this.satelliteViewer.viewer.entities.add({
            id: `satellite_${noradId}`,
            name: satellite.name,
            position: position,
            point: {
                pixelSize: 4,
                color: Cesium.Color.fromCssColorString(satellite.color),
                outlineColor: Cesium.Color.WHITE,
                outlineWidth: 0.5,
                heightReference: Cesium.HeightReference.NONE,
                show: true,
                disableDepthTestDistance: 0
            },
            label: {
                text: satellite.name,
                font: '12pt Arial',
                fillColor: Cesium.Color.YELLOW,
                outlineColor: Cesium.Color.BLACK,
                outlineWidth: 2,
                style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                pixelOffset: new Cesium.Cartesian2(0, -25),
                show: false,
                scaleByDistance: new Cesium.NearFarScalar(1.5e6, 1.0, 1.5e7, 0.5)
            },
            satelliteData: satellite
        });

        this.satelliteViewer.satelliteEntities.set(noradId, entity);
    }

    highlightMatch(text, query) {
        if (!query) return text;

        const regex = new RegExp(`(${query})`, 'gi');
        return text.replace(regex, '<mark class="bg-warning text-dark">$1</mark>');
    }

    showLoadingState() {
        if (!this.resultsContainer) return;

        this.resultsContainer.innerHTML = `
            <div class="search-loading">
                <div class="d-flex align-items-center justify-content-center p-3">
                    <div class="spinner-border spinner-border-sm text-primary me-2" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <small class="text-muted">Searching satellites...</small>
                </div>
            </div>
        `;
        this.showResults();
    }

    showLoadingSelection(noradId) {
        const toast = document.createElement('div');
        toast.className = 'toast show position-fixed';
        toast.style.cssText = 'top: 100px; right: 20px; z-index: 9999;';
        toast.innerHTML = `
            <div class="toast-header bg-dark text-light">
                <i class="fas fa-satellite text-primary me-2"></i>
                <strong class="me-auto">Loading Satellite</strong>
            </div>
            <div class="toast-body bg-dark text-light">
                Loading satellite ${noradId}...
            </div>
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            if (document.body.contains(toast)) {
                document.body.removeChild(toast);
            }
        }, 3000);
    }

    showSelectionError(message) {
        const toast = document.createElement('div');
        toast.className = 'toast show position-fixed';
        toast.style.cssText = 'top: 100px; right: 20px; z-index: 9999;';
        toast.innerHTML = `
            <div class="toast-header bg-danger text-light">
                <i class="fas fa-exclamation-triangle text-warning me-2"></i>
                <strong class="me-auto">Search Error</strong>
            </div>
            <div class="toast-body bg-dark text-light">
                ${message}
            </div>
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            if (document.body.contains(toast)) {
                document.body.removeChild(toast);
            }
        }, 5000);
    }

    showNoResults() {
        if (!this.resultsContainer) return;

        this.resultsContainer.innerHTML = `
            <div class="search-no-results">
                <div class="text-center p-3">
                    <i class="fas fa-search text-muted mb-2" style="font-size: 24px;"></i>
                    <p class="text-muted mb-1">No satellites found for "${this.currentQuery}"</p>
                    <small class="text-muted">Try a different search term or satellite name</small>
                </div>
            </div>
        `;
        this.showResults();
    }

    showErrorState() {
        if (!this.resultsContainer) return;

        this.resultsContainer.innerHTML = `
            <div class="search-error">
                <div class="text-center p-3">
                    <i class="fas fa-exclamation-triangle text-warning mb-2"></i>
                    <p class="text-warning mb-0">Search failed</p>
                    <small class="text-muted">Please try again</small>
                </div>
            </div>
        `;
        this.showResults();
    }

    showResults() {
        if (this.resultsContainer) {
            this.resultsContainer.style.display = 'block';
        }
    }

    hideResults() {
        if (this.resultsContainer) {
            this.resultsContainer.style.display = 'none';
        }
    }

    clearSearch() {
        console.log(`🔍 Performing complete search clear`);
        this.searchInput.value = '';
        this.currentQuery = '';
        this.searchResults = [];
        this.hideResults();
        this.clearSearchFilter();

        // Force a re-render to ensure clean state
        if (this.satelliteViewer) {
            this.satelliteViewer.viewer.scene.requestRender();
        }
    }

    // Apply search as a filter to visible satellites
    applySearchFilter(query) {
        if (!query || query.length === 0) {
            this.clearSearchFilter();
            return;
        }

        const queryLower = query.toLowerCase();
        let visibleCount = 0;
        const matchedSatellites = [];

        this.satelliteViewer.satelliteEntities.forEach((entity, noradId) => {
            const satellite = this.satelliteViewer.satellites.get(noradId);
            if (!satellite) return;

            const name = satellite.name.toLowerCase();
            let shouldShow = false;

            // More flexible matching - split on spaces and dashes
            const nameParts = name.split(/[\s-]+/);
            const queryParts = queryLower.split(/[\s-]+/);

            // Check if satellite name matches search query
            if (name.includes(queryLower) ||
                name.startsWith(queryLower) ||
                this.matchesWords(name, queryLower) ||
                nameParts.some(part => queryParts.some(qp => part.startsWith(qp)))) {
                shouldShow = true;
                visibleCount++;
                matchedSatellites.push(satellite.name);
            }

            // Apply visibility
            if (entity.point) {
                entity.point.show = shouldShow;
            }
            if (entity.label) {
                entity.label.show = shouldShow && (noradId === this.satelliteViewer.selectedSatellite);
            }
        });

        // Update status to show filtered count
        this.updateFilteredStatus(visibleCount, query);

        console.log(`🔍 Search filter applied: ${visibleCount} satellites match "${query}"`);
        if (visibleCount > 0 && visibleCount <= 10) {
            console.log(`🎯 Matched satellites: ${matchedSatellites.join(', ')}`);
        }
    }

    // Clear search filter and show all satellites
    clearSearchFilter() {
        console.log(`🔍 Clearing search filter, current query was: "${this.currentQuery}"`);

        // Clear the current query and search state
        this.currentQuery = '';
        this.searchResults = [];

        // Reset satellite filter to show satellites according to current filters
        if (this.satelliteViewer.satelliteFilter) {
            console.log(`🔍 Applying regular filters after clearing search`);
            this.satelliteViewer.satelliteFilter.applyCurrentFilters();
        } else {
            // Fallback: show all satellites
            console.log(`🔍 Fallback: showing all satellites`);
            this.satelliteViewer.satelliteEntities.forEach((entity, noradId) => {
                if (entity.point) {
                    entity.point.show = true;
                }
                if (entity.label) {
                    entity.label.show = (noradId === this.satelliteViewer.selectedSatellite);
                }
            });
        }

        // Reset status display
        this.clearFilteredStatus();
    }

    // Helper function for word matching
    matchesWords(name, query) {
        const queryWords = query.split(/\s+/);
        const nameWords = name.split(/\s+/);

        return queryWords.some(queryWord =>
            nameWords.some(nameWord =>
                nameWord.includes(queryWord) || queryWord.includes(nameWord)
            )
        );
    }

    // Update status to show search filter is active
    updateFilteredStatus(count, query) {
        const visibleCountElement = document.getElementById('visibleSats');
        const visibleCountBadge = document.getElementById('visibleCount');

        if (visibleCountElement && visibleCountBadge) {
            visibleCountElement.textContent = count;
            visibleCountBadge.style.display = 'inline-block';
            visibleCountBadge.title = `Filtered by search: "${query}"`;
        }
    }

    // Clear filtered status display
    clearFilteredStatus() {
        const visibleCountElement = document.getElementById('visibleSats');
        const visibleCountBadge = document.getElementById('visibleCount');

        if (visibleCountElement && visibleCountBadge) {
            const totalSats = this.satelliteViewer.satellites.size;
            visibleCountElement.textContent = totalSats;

            // Only hide badge if no other filters are active
            const hasActiveFilters = this.satelliteViewer.satelliteFilter &&
                this.satelliteViewer.satelliteFilter.hasActiveFilters();
            if (!hasActiveFilters) {
                visibleCountBadge.style.display = 'none';
            }
            visibleCountBadge.title = '';
        }
    }

    handleKeyNavigation(e) {
        const resultItems = this.resultsContainer.querySelectorAll('.search-result-item');

        if (resultItems.length === 0) return;

        let currentIndex = -1;
        resultItems.forEach((item, index) => {
            if (item.classList.contains('highlighted')) {
                currentIndex = index;
                item.classList.remove('highlighted');
            }
        });

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                currentIndex = Math.min(currentIndex + 1, resultItems.length - 1);
                break;
            case 'ArrowUp':
                e.preventDefault();
                currentIndex = Math.max(currentIndex - 1, -1);
                break;
            case 'Enter':
                e.preventDefault();
                if (currentIndex >= 0) {
                    const selectedItem = resultItems[currentIndex];
                    const noradId = parseInt(selectedItem.dataset.noradId);
                    this.selectSatelliteFromSearch(noradId);
                }
                return;
            case 'Escape':
                this.hideResults();
                this.searchInput.blur();
                return;
        }

        if (currentIndex >= 0) {
            resultItems[currentIndex].classList.add('highlighted');
            resultItems[currentIndex].scrollIntoView({
                behavior: 'smooth',
                block: 'nearest'
            });
        }
    }
}
