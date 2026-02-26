/**
 * NASA APOD Button System
 * Shows a small button below navbar to access NASA Picture of the Day
 */
class NASAAPODButton {
    constructor() {
        this.buttonCreated = false;
    }

    init() {
        // Create button after a short delay to let the app load
        setTimeout(() => {
            this.createButton();
        }, 1000);
    }

    createButton() {
        if (this.buttonCreated) return;

        // Create the buttons HTML (both APOD and Asteroids)
        const buttonHTML = `
            <div id="nasaButtonsContainer" class="nasa-buttons-container">
                <div id="nasaApodButton" class="nasa-apod-btn">
                    <a href="/nasa-picture-of-the-day" target="_blank" class="nasa-btn-link">
                        <i class="fas fa-rocket"></i>
                        <span class="nasa-btn-text">NASA APOD</span>
                    </a>
                </div>
                <div id="nasaAsteroidsButton" class="nasa-asteroids-btn">
                    <a href="/nasa-asteroids" target="_blank" class="nasa-btn-link asteroids-link">
                        <i class="fas fa-meteor"></i>
                        <span class="nasa-btn-text">Asteroids</span>
                    </a>
                </div>
                <div id="nasaDonkiButton" class="nasa-donki-btn">
                    <a href="/nasa-space-weather" target="_blank" class="nasa-btn-link donki-link">
                        <i class="fas fa-sun"></i>
                        <span class="nasa-btn-text">Space Weather</span>
                    </a>
                </div>
                <div id="nasaEonetButton" class="eonet-btn">
                    <a href="/nasa-eonet" target="_blank" class="nasa-btn-link eonet-link">
                        <i class="fas fa-globe-americas"></i>
                        <span class="nasa-btn-text">Natural Events</span>
                    </a>
                </div>
            </div>
        `;

        // Add button styles
        const styles = `
            <style>
                .nasa-buttons-container {
                    position: fixed;
                    top: 80px;
                    left: 20px;
                    z-index: 1000;
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                }

                .nasa-apod-btn {
                    background: linear-gradient(45deg, #1e88e5, #42a5f5);
                    border-radius: 25px;
                    box-shadow: 0 4px 15px rgba(30, 136, 229, 0.3);
                    transition: all 0.3s ease;
                    animation: nasaButtonPulse 3s infinite;
                }

                .nasa-asteroids-btn {
                    background: linear-gradient(45deg, #dc267f, #ff6b6b);
                    border-radius: 25px;
                    box-shadow: 0 4px 15px rgba(220, 38, 127, 0.3);
                    transition: all 0.3s ease;
                    animation: asteroidsButtonPulse 3s infinite 1.5s;
                }

                .nasa-apod-btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(30, 136, 229, 0.4);
                    animation: none;
                }

                .nasa-asteroids-btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(220, 38, 127, 0.4);
                    animation: none;
                }

                .nasa-donki-btn {
                    background: linear-gradient(45deg, #ff9800, #ffc107);
                    border-radius: 25px;
                    box-shadow: 0 4px 15px rgba(255, 152, 0, 0.3);
                    transition: all 0.3s ease;
                    animation: donkiButtonPulse 3s infinite 3s;
                }

                .nasa-donki-btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(255, 152, 0, 0.4);
                    animation: none;
                }

                .nasa-btn-link {
                    display: flex;
                    align-items: center;
                    padding: 8px 15px;
                    color: white;
                    text-decoration: none;
                    font-size: 0.9rem;
                    font-weight: 600;
                    gap: 8px;
                }

                .nasa-btn-link:hover {
                    color: white;
                    text-decoration: none;
                }

                .nasa-btn-text {
                    white-space: nowrap;
                }

                /* EONET Button Styles */
                .eonet-btn {
                    background: linear-gradient(45deg, #2ecc71, #27ae60);
                    border-radius: 25px;
                    box-shadow: 0 4px 15px rgba(46, 204, 113, 0.3);
                    transition: all 0.3s ease;
                    animation: eonetButtonPulse 3s infinite 6s; /* Adjusted delay */
                }

                .eonet-btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(46, 204, 113, 0.4);
                    animation: none;
                }

                /* Animations */
                @keyframes nasaButtonPulse {
                    0%, 100% {
                        box-shadow: 0 4px 15px rgba(30, 136, 229, 0.3);
                    }
                    50% {
                        box-shadow: 0 4px 20px rgba(30, 136, 229, 0.6);
                    }
                }

                @keyframes asteroidsButtonPulse {
                    0%, 100% {
                        box-shadow: 0 4px 15px rgba(220, 38, 127, 0.3);
                    }
                    50% {
                        box-shadow: 0 4px 20px rgba(220, 38, 127, 0.6);
                    }
                }

                @keyframes donkiButtonPulse {
                    0%, 100% { 
                        transform: scale(1); 
                        box-shadow: 0 4px 15px rgba(255, 152, 0, 0.3);
                    }
                    50% { 
                        transform: scale(1.05); 
                        box-shadow: 0 6px 25px rgba(255, 152, 0, 0.5);
                    }
                }

                @keyframes eonetButtonPulse {
                    0%, 100% { 
                        transform: scale(1); 
                        box-shadow: 0 4px 15px rgba(46, 204, 113, 0.3);
                    }
                    50% { 
                        transform: scale(1.05); 
                        box-shadow: 0 6px 25px rgba(46, 204, 113, 0.5);
                    }
                }

                @media (max-width: 768px) {
                    .nasa-buttons-container {
                        top: calc(var(--navbar-height, 60px) + 10px);
                        left: 10px;
                    }

                    .nasa-btn-link {
                        padding: 6px 12px;
                        font-size: 0.8rem;
                    }

                    .nasa-btn-text {
                        display: none;
                    }
                }

                @media (max-width: 480px) {
                    .nasa-buttons-container {
                        top: calc(var(--navbar-height, 60px) + 10px);
                        left: 12px;
                    }

                    .nasa-btn-link {
                        padding: 7px 13px;
                    }
                }
            </style>
        `;

        // Add styles to head
        document.head.insertAdjacentHTML('beforeend', styles);

        // Add button to body
        document.body.insertAdjacentHTML('beforeend', buttonHTML);

        this.buttonCreated = true;

        console.log('NASA APOD button created successfully');
    }

    // Method to manually show/hide buttons
    toggleButton() {
        const container = document.getElementById('nasaButtonsContainer');
        if (container) {
            container.style.display = container.style.display === 'none' ? 'flex' : 'none';
        }
    }

    // Method to remove buttons
    removeButton() {
        const container = document.getElementById('nasaButtonsContainer');
        if (container) {
            container.remove();
            this.buttonCreated = false;
        }
    }
}

// EONET Module
class EONETModule {
    constructor(apiKey) {
        this.apiKey = apiKey;
        this.cache = null;
        this.cacheTimestamp = null;
        this.eonetApiUrl = 'https://eonet.gsfc.nasa.gov/api/v3/events';
    }

    // Function to fetch EONET data
    async fetchEONETData() {
        const now = new Date();
        const oneDayAgo = new Date(now - 24 * 60 * 60 * 1000);

        // Check if cache is valid (less than 1 day old)
        if (this.cache && this.cacheTimestamp && this.cacheTimestamp > oneDayAgo) {
            console.log('EONET data served from cache.');
            return this.cache;
        }

        console.log('Fetching EONET data from API...');
        try {
            // Add API key as a parameter if it's required and available.
            // For EONET, the API key is often not strictly necessary for public data,
            // but it's good practice to include if the API supports it for rate limiting or access.
            // Adjust the URL construction if your API key needs to be passed differently.
            const response = await fetch(`${this.eonetApiUrl}?api_key=${this.apiKey}`);

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();

            // Update cache and timestamp
            this.cache = data;
            this.cacheTimestamp = new Date();
            console.log('EONET data fetched and cached.');
            return data;
        } catch (error) {
            console.error('Error fetching EONET data:', error);
            // If there's an error fetching, return existing cache if available, otherwise null
            return this.cache || null;
        }
    }

    // Function to open EONET in a new page
    openEONETPage() {
        window.open('/nasa-eonet', '_blank');
    }

    // Function to clear cache at the end of the day
    clearCacheAtEndOfDay() {
        const now = new Date();
        const endOfDay = new Date(now);
        endOfDay.setHours(23, 59, 59, 999); // Set to the end of the current day

        const timeUntilEndOfDay = endOfDay.getTime() - now.getTime();

        setTimeout(() => {
            this.cache = null;
            this.cacheTimestamp = null;
            console.log('EONET cache cleared at the end of the day.');
        }, timeUntilEndOfDay);
    }

    // Initialize the EONET module
    init() {
        // Set up the daily cache clearing
        this.clearCacheAtEndOfDay();

        // You can add event listeners here if needed, e.g., when the EONET button is clicked
        // For now, the button click is handled directly by the onclick attribute in the HTML.
        console.log('EONET module initialized.');
    }
}

// Initialize NASA APOD button when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Small delay to ensure other components are loaded
    setTimeout(() => {
        window.nasaApodButton = new NASAAPODButton();
        window.nasaApodButton.init();

        // Initialize EONET module if NASA_API_KEY is available
        if (window.NASA_API_KEY) {
            window.eonetModule = new EONETModule(window.NASA_API_KEY);
            window.eonetModule.init();
        } else {
            console.warn('NASA_API_KEY not found. EONET feature will not be initialized.');
        }
    }, 1000);
});

// Export for potential manual control
window.NASAAPODButton = NASAAPODButton;
window.EONETModule = EONETModule;