
/**
 * Weather Module - Dedicated weather functionality for satellite viewer
 * Can be enabled/disabled independently while preserving all other features
 */

class WeatherModule {
    constructor(viewer) {
        this.viewer = viewer;
        this.weatherEnabled = false;
        this.cloudLayer = null;
        this.precipitationLayer = null;
        this.weatherLayer = null;
        this.cloudEffect = null;
        this.weatherLegend = null;
        
        console.log('🌤️ Weather Module initialized');
    }

    /**
     * Enable weather functionality
     */
    async enable() {
        if (this.weatherEnabled) {
            console.log('🌤️ Weather already enabled');
            return;
        }

        console.log('🌤️ Enabling weather functionality...');
        this.weatherEnabled = true;

        try {
            // Update UI button
            this.updateWeatherButton(true);
            
            // Show loading indicator
            this.showLoadingIndicator('Loading weather data...');

            // Try multiple weather data sources in order of preference
            let weatherLoaded = await this.loadOpenWeatherMapData();
            
            if (!weatherLoaded) {
                weatherLoaded = await this.loadNASAWeatherData();
            }
            
            if (!weatherLoaded) {
                this.enableAtmosphericWeatherSimulation();
            }

            // Add weather legend
            this.addWeatherLegend();
            
            // Enhanced atmospheric effects for realism
            this.enhanceAtmosphericEffects();
            
            this.hideLoadingIndicator();
            console.log('✅ Weather functionality enabled');
            
        } catch (error) {
            console.error('❌ Error enabling weather:', error);
            this.disable(); // Clean rollback on error
        }
    }

    /**
     * Disable weather functionality
     */
    disable() {
        if (!this.weatherEnabled) {
            console.log('🌤️ Weather already disabled');
            return;
        }

        console.log('🌤️ Disabling weather functionality...');
        this.weatherEnabled = false;

        // Update UI button
        this.updateWeatherButton(false);

        // Remove all weather layers
        this.removeWeatherLayers();

        // Remove weather effects
        this.removeWeatherEffects();

        // Remove weather legend
        this.removeWeatherLegend();

        // Reset atmospheric effects to default
        this.resetAtmosphericEffects();

        // Force render update
        if (this.viewer && this.viewer.scene) {
            this.viewer.scene.requestRender();
        }

        console.log('✅ Weather functionality disabled');
    }

    /**
     * Toggle weather functionality
     */
    toggle() {
        if (this.weatherEnabled) {
            this.disable();
        } else {
            this.enable();
        }
    }

    /**
     * Load OpenWeatherMap cloud and precipitation data
     */
    async loadOpenWeatherMapData() {
        try {
            console.log('🌤️ Loading OpenWeatherMap data...');
            
            // Get API key from backend
            const response = await fetch('/api/weather-key');
            const data = await response.json();

            if (!data.api_key) {
                console.warn('⚠️ OpenWeatherMap API key not available');
                return false;
            }

            const apiKey = data.api_key;

            // Test API key with a single tile request first
            const testUrl = `https://tile.openweathermap.org/map/clouds_new/1/0/0.png?appid=${apiKey}`;
            const testResponse = await fetch(testUrl);
            
            if (!testResponse.ok) {
                console.warn('⚠️ OpenWeatherMap API test failed, status:', testResponse.status);
                return false;
            }

            // Add clouds layer with better error handling
            const cloudProvider = new Cesium.UrlTemplateImageryProvider({
                url: `https://tile.openweathermap.org/map/clouds_new/{z}/{x}/{y}.png?appid=${apiKey}`,
                credit: 'OpenWeatherMap Clouds',
                maximumLevel: 8,
                minimumLevel: 0,  // Must start at 0 to cover full globe without stripe gaps
                hasAlphaChannel: true,
                tilingScheme: new Cesium.WebMercatorTilingScheme(),
                enablePickFeatures: false,
                tileDiscardPolicy: new Cesium.DiscardMissingTileImagePolicy({
                    missingImageUrl: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA+eo0AAAAAABJRU5ErkJggg==',
                    pixelsToCheck: [new Cesium.Cartesian2(0, 0)]
                })
            });

            this.cloudLayer = this.viewer.imageryLayers.addImageryProvider(cloudProvider);
            this.cloudLayer.alpha = 0.7;
            this.cloudLayer.brightness = 1.5;   // Brighter so white cloud areas are clearly visible
            this.cloudLayer.contrast = 1.2;
            this.cloudLayer.saturation = 0.0;   // Desaturate: removes the multi-color OWM palette, giving natural white/gray clouds
            this.cloudLayer.gamma = 1.6;        // Gamma boost makes cloud whites stand out over clear areas

            // Add precipitation layer with similar improvements
            const precipProvider = new Cesium.UrlTemplateImageryProvider({
                url: `https://tile.openweathermap.org/map/precipitation_new/{z}/{x}/{y}.png?appid=${apiKey}`,
                credit: 'OpenWeatherMap Precipitation',
                maximumLevel: 6,
                minimumLevel: 0,  // Must start at 0 to cover full globe without stripe gaps
                hasAlphaChannel: true,
                tilingScheme: new Cesium.WebMercatorTilingScheme(),
                enablePickFeatures: false,
                tileDiscardPolicy: new Cesium.DiscardMissingTileImagePolicy({
                    missingImageUrl: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAGA+eo0AAAAAABJRU5ErkJggg==',
                    pixelsToCheck: [new Cesium.Cartesian2(0, 0)]
                })
            });

            this.precipitationLayer = this.viewer.imageryLayers.addImageryProvider(precipProvider);
            this.precipitationLayer.alpha = 0.5;
            this.precipitationLayer.brightness = 1.2;

            console.log('✅ OpenWeatherMap data loaded with improved tile handling');
            return true;

        } catch (error) {
            console.warn('⚠️ Failed to load OpenWeatherMap data:', error);
            return false;
        }
    }

    /**
     * Load NASA GIBS weather data as fallback
     */
    async loadNASAWeatherData() {
        try {
            console.log('🌤️ Loading NASA GIBS weather data...');
            
            // Use yesterday's date as NASA data might not be available for today
            const yesterday = new Date();
            yesterday.setDate(yesterday.getDate() - 1);
            const dateStr = yesterday.getFullYear() + '-' +
                String(yesterday.getMonth() + 1).padStart(2, '0') + '-' +
                String(yesterday.getDate()).padStart(2, '0');

            // Try MODIS Terra first (more reliable for weather visualization)
            const nasaProvider = new Cesium.UrlTemplateImageryProvider({
                url: `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/${dateStr}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg`,
                credit: 'NASA GIBS MODIS Terra',
                maximumLevel: 7,  // Reduced for better performance
                minimumLevel: 0,
                tilingScheme: new Cesium.WebMercatorTilingScheme(),
                enablePickFeatures: false
            });

            this.weatherLayer = this.viewer.imageryLayers.addImageryProvider(nasaProvider);
            this.weatherLayer.alpha = 0.6;  // Reduced opacity
            this.weatherLayer.brightness = 1.0;  // Normal brightness
            this.weatherLayer.contrast = 1.1;

            // Try to add a cloud layer from NASA as well
            try {
                const cloudProvider = new Cesium.UrlTemplateImageryProvider({
                    url: `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_Cloud_Fraction_Day/default/${dateStr}/GoogleMapsCompatible_Level6/{z}/{y}/{x}.png`,
                    credit: 'NASA GIBS Cloud Fraction',
                    maximumLevel: 6,
                    minimumLevel: 0,
                    hasAlphaChannel: true,
                    tilingScheme: new Cesium.WebMercatorTilingScheme(),
                    enablePickFeatures: false
                });

                this.cloudLayer = this.viewer.imageryLayers.addImageryProvider(cloudProvider);
                this.cloudLayer.alpha = 0.4;
                this.cloudLayer.brightness = 1.2;
            } catch (cloudError) {
                console.warn('⚠️ NASA cloud layer failed, continuing with base imagery');
            }

            console.log('✅ NASA GIBS weather data loaded');
            return true;

        } catch (error) {
            console.warn('⚠️ Failed to load NASA weather data:', error);
            return false;
        }
    }

    /**
     * Enable atmospheric weather simulation as fallback
     */
    enableAtmosphericWeatherSimulation() {
        console.log('🌤️ Enabling atmospheric weather simulation...');

        try {
            // Enhanced atmospheric effects for weather simulation
            this.viewer.scene.skyAtmosphere.show = true;
            this.viewer.scene.skyAtmosphere.brightnessShift = 0.1;  // Reduced for subtlety
            this.viewer.scene.skyAtmosphere.saturationShift = 0.1;
            this.viewer.scene.skyAtmosphere.hueShift = 0.05;

            // Enhanced fog for weather effects
            this.viewer.scene.fog.enabled = true;
            this.viewer.scene.fog.density = 0.0003;  // Reduced density
            this.viewer.scene.fog.minimumBrightness = 0.1;  // Slightly brighter
            this.viewer.scene.fog.screenSpaceErrorFactor = 2.0;

            // Globe atmospheric effects for weather - more subtle
            this.viewer.scene.globe.atmosphereHueShift = 0.05;
            this.viewer.scene.globe.atmosphereSaturationShift = 0.1;
            this.viewer.scene.globe.atmosphereBrightnessShift = 0.05;

            // Add realistic cloud simulation using particle system approach
            if (this.viewer.scene.postProcessStages) {
                const weatherShader = `
                    uniform sampler2D colorTexture;
                    uniform float u_time;
                    varying vec2 v_textureCoordinates;
                    
                    float noise(vec2 p) {
                        return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
                    }
                    
                    float fbm(vec2 p) {
                        float value = 0.0;
                        float amplitude = 0.5;
                        for(int i = 0; i < 3; i++) {
                            value += amplitude * noise(p);
                            p *= 2.0;
                            amplitude *= 0.5;
                        }
                        return value;
                    }
                    
                    void main() {
                        vec4 color = texture2D(colorTexture, v_textureCoordinates);
                        
                        // Create cloud-like patterns
                        vec2 cloudCoord = v_textureCoordinates * 8.0 + u_time * 0.01;
                        float cloudPattern = fbm(cloudCoord);
                        
                        // Apply cloud effect selectively
                        float cloudMask = smoothstep(0.4, 0.7, cloudPattern);
                        vec3 cloudColor = vec3(0.9, 0.9, 1.0);
                        
                        // Blend clouds with scene
                        color.rgb = mix(color.rgb, cloudColor, cloudMask * 0.15);
                        
                        gl_FragColor = color;
                    }
                `;
                
                this.cloudEffect = new Cesium.PostProcessStage({
                    fragmentShader: weatherShader,
                    uniforms: {
                        u_time: function() {
                            return performance.now() / 1000.0;
                        }
                    }
                });
                this.viewer.scene.postProcessStages.add(this.cloudEffect);
            }

            console.log('✅ Atmospheric weather simulation enabled with realistic cloud effects');

        } catch (error) {
            console.warn('⚠️ Atmospheric weather simulation failed:', error);
        }
    }

    /**
     * Enhance atmospheric effects for realistic weather
     */
    enhanceAtmosphericEffects() {
        if (!this.viewer || !this.viewer.scene) return;

        try {
            this.viewer.scene.skyAtmosphere.show = true;
            this.viewer.scene.fog.enabled = true;
            this.viewer.scene.fog.density = 0.0003;
            this.viewer.scene.fog.screenSpaceErrorFactor = 2.2;
            this.viewer.scene.fog.minimumBrightness = 0.05;
        } catch (error) {
            console.warn('⚠️ Error enhancing atmospheric effects:', error);
        }
    }

    /**
     * Remove all weather layers
     */
    removeWeatherLayers() {
        try {
            if (this.cloudLayer) {
                this.viewer.imageryLayers.remove(this.cloudLayer);
                this.cloudLayer = null;
            }
            if (this.precipitationLayer) {
                this.viewer.imageryLayers.remove(this.precipitationLayer);
                this.precipitationLayer = null;
            }
            if (this.weatherLayer) {
                this.viewer.imageryLayers.remove(this.weatherLayer);
                this.weatherLayer = null;
            }
        } catch (error) {
            console.warn('⚠️ Error removing weather layers:', error);
        }
    }

    /**
     * Remove weather effects
     */
    removeWeatherEffects() {
        try {
            if (this.cloudEffect && this.viewer.scene.postProcessStages) {
                this.viewer.scene.postProcessStages.remove(this.cloudEffect);
                this.cloudEffect = null;
            }
        } catch (error) {
            console.warn('⚠️ Error removing weather effects:', error);
        }
    }

    /**
     * Reset atmospheric effects to default
     */
    resetAtmosphericEffects() {
        if (!this.viewer || !this.viewer.scene) return;

        try {
            // Keep atmosphere but reset weather-specific modifications
            this.viewer.scene.skyAtmosphere.show = true;
            this.viewer.scene.skyAtmosphere.brightnessShift = 0.0;
            this.viewer.scene.skyAtmosphere.saturationShift = 0.0;
            this.viewer.scene.skyAtmosphere.hueShift = 0.0;

            // Disable weather fog
            this.viewer.scene.fog.enabled = false;
            this.viewer.scene.fog.density = 0.0;
            this.viewer.scene.fog.minimumBrightness = 0.0;
            this.viewer.scene.fog.screenSpaceErrorFactor = 1.0;

            // Reset globe atmospheric effects
            this.viewer.scene.globe.atmosphereHueShift = 0.0;
            this.viewer.scene.globe.atmosphereSaturationShift = 0.0;
            this.viewer.scene.globe.atmosphereBrightnessShift = 0.0;
        } catch (error) {
            console.warn('⚠️ Error resetting atmospheric effects:', error);
        }
    }

    /**
     * Add weather legend
     */
    addWeatherLegend() {
        this.removeWeatherLegend(); // Remove existing if any

        try {
            const legend = document.createElement('div');
            legend.id = 'weatherLegend';
            legend.className = 'weather-legend';
            legend.innerHTML = `
                <div class="legend-header">
                    <h6><i class="fas fa-cloud-sun"></i> Weather Data</h6>
                    <button type="button" class="btn-close btn-close-white btn-sm" onclick="satelliteViewer.weatherModule.removeWeatherLegend()"></button>
                </div>
                <div class="legend-content">
                    <div class="legend-item">
                        <div class="legend-color" style="background: rgba(255,255,255,0.8)"></div>
                        <span>Dense Clouds</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: rgba(255,255,255,0.5)"></div>
                        <span>Light Clouds</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: rgba(100,149,237,0.7)"></div>
                        <span>Precipitation</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: rgba(70,130,180,0.6)"></div>
                        <span>Weather Systems</span>
                    </div>
                    <div class="legend-footer">
                        <small><i class="fas fa-satellite"></i> Real-time Weather</small>
                        <small>OpenWeatherMap • NASA GIBS</small>
                    </div>
                </div>
            `;

            // Add required CSS if not present
            this.addWeatherCSS();
            
            document.body.appendChild(legend);
            this.weatherLegend = legend;

        } catch (error) {
            console.warn('⚠️ Error adding weather legend:', error);
        }
    }

    /**
     * Remove weather legend
     */
    removeWeatherLegend() {
        if (this.weatherLegend) {
            try {
                this.weatherLegend.remove();
                this.weatherLegend = null;
            } catch (error) {
                console.warn('⚠️ Error removing weather legend:', error);
            }
        }

        // Also remove by ID as fallback
        const legend = document.getElementById('weatherLegend');
        if (legend) {
            legend.remove();
        }
    }

    /**
     * Add required CSS for weather legend
     */
    addWeatherCSS() {
        if (!document.getElementById('weatherModuleCSS')) {
            const style = document.createElement('style');
            style.id = 'weatherModuleCSS';
            style.textContent = `
                .weather-legend {
                    position: fixed;
                    top: 120px;
                    left: 20px;
                    background: linear-gradient(135deg, rgba(26, 26, 46, 0.95) 0%, rgba(12, 12, 12, 0.95) 100%);
                    border: 1px solid rgba(100, 181, 246, 0.3);
                    border-radius: 10px;
                    padding: 15px;
                    max-width: 280px;
                    color: white;
                    font-size: 12px;
                    backdrop-filter: blur(10px);
                    z-index: 1000;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                }

                .weather-legend .legend-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 10px;
                    padding-bottom: 8px;
                    border-bottom: 1px solid rgba(100, 181, 246, 0.2);
                }

                .weather-legend .legend-header h6 {
                    margin: 0;
                    color: #64b5f6;
                    font-weight: 600;
                }

                .weather-legend .legend-content {
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                }

                .weather-legend .legend-item {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }

                .weather-legend .legend-color {
                    width: 16px;
                    height: 16px;
                    border-radius: 3px;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }

                .weather-legend .legend-footer {
                    margin-top: 10px;
                    padding-top: 8px;
                    border-top: 1px solid rgba(100, 181, 246, 0.2);
                    display: flex;
                    flex-direction: column;
                    gap: 4px;
                }

                .weather-legend .legend-footer small {
                    color: #94a3b8;
                    font-size: 10px;
                }
            `;
            document.head.appendChild(style);
        }
    }

    /**
     * Update weather button state
     */
    updateWeatherButton(enabled) {
        const btn = document.getElementById('weatherToggleBtn');
        if (btn) {
            if (enabled) {
                btn.innerHTML = '<i class="fas fa-cloud-sun"></i> Disable Weather';
                btn.classList.add('btn-warning');
                btn.classList.remove('btn-outline-warning');
            } else {
                btn.innerHTML = '<i class="fas fa-cloud-sun"></i> Enable Weather';
                btn.classList.add('btn-outline-warning');
                btn.classList.remove('btn-warning');
            }
        }
    }

    /**
     * Show loading indicator
     */
    showLoadingIndicator(message) {
        const indicator = document.getElementById('loadingOverlay');
        if (indicator) {
            indicator.style.display = 'flex';
            const messageEl = indicator.querySelector('p');
            if (messageEl) messageEl.textContent = message;
        }
    }

    /**
     * Hide loading indicator
     */
    hideLoadingIndicator() {
        const indicator = document.getElementById('loadingOverlay');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }

    /**
     * Check if weather is enabled
     */
    isEnabled() {
        return this.weatherEnabled;
    }

    /**
     * Cleanup when destroying the module
     */
    destroy() {
        this.disable();
        console.log('🌤️ Weather Module destroyed');
    }
}

// Export for use in other modules
window.WeatherModule = WeatherModule;
