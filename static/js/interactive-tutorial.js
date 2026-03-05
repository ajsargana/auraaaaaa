
class InteractiveTutorial {
    constructor() {
        this.currentStep = 0;
        this.steps = [
            {
                title: "Welcome to AURA-AI! 🛰️",
                message: "Let's take a quick tour of 4 key features. Click 'Next' to continue.",
                target: null,
                position: "center"
            },
            {
                title: "AI Assistant 🤖",
                message: "Your intelligent space companion! Click this bubble to ask questions, control the interface, search satellites, and get expert guidance about space and satellites.",
                target: "#ai-agent-bubble",
                position: "left"
            },
            {
                title: "Pass Prediction",
                message: "Find satellites that will pass over your location! Set your location and time filters to see upcoming satellite passes in your area.",
                target: "button[data-bs-target='#passFilterModal']",
                position: "bottom"
            },
            {
                title: "Motion Control ⏱️",
                message: "Control time and see satellite movement! Speed up time to predict future positions or go back to see past satellite locations.",
                target: "#motionControlBtn",
                position: "left"
            },
            {
                title: "Satellite Information Panel 📊",
                message: "Click any satellite on the globe to see detailed information here! View altitude, speed, orbit details, and upcoming passes over your location.",
                target: "#satelliteDetailsPanel",
                position: "left"
            },
            {
                title: "Ready to Explore! 🚀",
                message: "You're all set! Click any satellite on the globe to start tracking. Happy exploring!",
                target: null,
                position: "center"
            }
        ];
        
        this.overlay = null;
        this.tooltip = null;
        this.hasSeenTutorial = localStorage.getItem('skyscape_tutorial_seen') === 'true';
    }

    start() {
        if (this.hasSeenTutorial) {
            console.log('Tutorial already seen, skipping...');
            return;
        }

        // Wait for page to be fully loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.showStep(0));
        } else {
            // Small delay to ensure all elements are rendered
            setTimeout(() => this.showStep(0), 1000);
        }
    }

    showStep(stepIndex) {
        if (stepIndex >= this.steps.length) {
            this.finish();
            return;
        }

        this.currentStep = stepIndex;
        const step = this.steps[stepIndex];

        // Remove existing tooltip and overlay
        this.removeTooltip();
        this.removeOverlay();

        // Create overlay (without blur)
        this.createOverlay();

        // Create tooltip
        this.createTooltip(step);

        // Highlight target element
        if (step.target) {
            this.highlightElement(step.target);
        }
    }

    createOverlay() {
        this.overlay = document.createElement('div');
        this.overlay.id = 'tutorial-overlay';
        this.overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 9998;
            pointer-events: none;
        `;
        document.body.appendChild(this.overlay);
    }

    createTooltip(step) {
        this.tooltip = document.createElement('div');
        this.tooltip.id = 'tutorial-tooltip';
        this.tooltip.style.cssText = `
            position: fixed;
            background: linear-gradient(135deg, rgba(26, 26, 46, 0.98) 0%, rgba(12, 12, 12, 0.98) 100%);
            border: 2px solid rgba(100, 181, 246, 0.5);
            border-radius: 15px;
            padding: 25px;
            max-width: 380px;
            z-index: 10000;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5), 0 0 20px rgba(100, 181, 246, 0.3);
            animation: tooltipFadeIn 0.3s ease-out;
            pointer-events: auto;
        `;

        this.tooltip.innerHTML = `
            <style>
                @keyframes tooltipFadeIn {
                    from {
                        opacity: 0;
                        transform: scale(0.9) translateY(-10px);
                    }
                    to {
                        opacity: 1;
                        transform: scale(1) translateY(0);
                    }
                }
                @keyframes highlightPulse {
                    0%, 100% {
                        box-shadow: 0 0 0 0 rgba(100, 181, 246, 0.7);
                    }
                    50% {
                        box-shadow: 0 0 0 15px rgba(100, 181, 246, 0);
                    }
                }
                .tutorial-highlight {
                    position: relative;
                    z-index: 9999 !important;
                    box-shadow: 0 0 0 4px rgba(100, 181, 246, 0.8), 0 0 20px rgba(100, 181, 246, 0.5) !important;
                    border-radius: 8px !important;
                    animation: highlightPulse 2s infinite;
                    pointer-events: auto !important;
                }
            </style>
            <div style="margin-bottom: 20px;">
                <h5 style="color: #64b5f6; margin: 0 0 10px 0; font-weight: 600; font-size: 1.2rem;">
                    ${step.title}
                </h5>
                <p style="color: #e2e8f0; margin: 0; line-height: 1.6; font-size: 1rem;">
                    ${step.message}
                </p>
            </div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 20px;">
                <small style="color: #94a3b8; font-size: 0.85rem;">
                    Step ${this.currentStep + 1} of ${this.steps.length}
                </small>
                <div style="display: flex; gap: 10px;">
                    ${this.currentStep > 0 ? `
                        <button id="tutorial-prev" style="
                            background: rgba(255, 255, 255, 0.1);
                            border: 1px solid rgba(255, 255, 255, 0.3);
                            color: white;
                            padding: 8px 20px;
                            border-radius: 8px;
                            cursor: pointer;
                            font-size: 0.9rem;
                            transition: all 0.3s ease;
                        ">
                            Previous
                        </button>
                    ` : ''}
                    <button id="tutorial-skip" style="
                        background: rgba(244, 67, 54, 0.2);
                        border: 1px solid rgba(244, 67, 54, 0.5);
                        color: #ff6b6b;
                        padding: 8px 20px;
                        border-radius: 8px;
                        cursor: pointer;
                        font-size: 0.9rem;
                        transition: all 0.3s ease;
                    ">
                        Skip
                    </button>
                    <button id="tutorial-next" style="
                        background: linear-gradient(135deg, #64b5f6, #42a5f5);
                        border: none;
                        color: white;
                        padding: 8px 20px;
                        border-radius: 8px;
                        cursor: pointer;
                        font-size: 0.9rem;
                        font-weight: 600;
                        transition: all 0.3s ease;
                        box-shadow: 0 4px 15px rgba(100, 181, 246, 0.3);
                    ">
                        ${this.currentStep === this.steps.length - 1 ? 'Finish' : 'Next'}
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(this.tooltip);

        // Position tooltip
        this.positionTooltip(step);

        // Add event listeners
        const nextBtn = document.getElementById('tutorial-next');
        const skipBtn = document.getElementById('tutorial-skip');
        const prevBtn = document.getElementById('tutorial-prev');

        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.showStep(this.currentStep + 1));
            nextBtn.addEventListener('mouseenter', (e) => {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 6px 20px rgba(100, 181, 246, 0.4)';
            });
            nextBtn.addEventListener('mouseleave', (e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 4px 15px rgba(100, 181, 246, 0.3)';
            });
        }

        if (skipBtn) {
            skipBtn.addEventListener('click', () => this.finish());
            skipBtn.addEventListener('mouseenter', (e) => {
                e.target.style.background = 'rgba(244, 67, 54, 0.3)';
            });
            skipBtn.addEventListener('mouseleave', (e) => {
                e.target.style.background = 'rgba(244, 67, 54, 0.2)';
            });
        }

        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.showStep(this.currentStep - 1));
            prevBtn.addEventListener('mouseenter', (e) => {
                e.target.style.background = 'rgba(255, 255, 255, 0.2)';
            });
            prevBtn.addEventListener('mouseleave', (e) => {
                e.target.style.background = 'rgba(255, 255, 255, 0.1)';
            });
        }
    }

    positionTooltip(step) {
        if (!step.target) {
            // Center position
            this.tooltip.style.top = '50%';
            this.tooltip.style.left = '50%';
            this.tooltip.style.transform = 'translate(-50%, -50%)';
            return;
        }

        const target = document.querySelector(step.target);
        if (!target) {
            // Fallback to center if target not found
            this.tooltip.style.top = '50%';
            this.tooltip.style.left = '50%';
            this.tooltip.style.transform = 'translate(-50%, -50%)';
            return;
        }

        const targetRect = target.getBoundingClientRect();
        const tooltipRect = this.tooltip.getBoundingClientRect();

        let top, left;
        const spacing = 15; // Space between target and tooltip

        switch (step.position) {
            case 'bottom':
                top = targetRect.bottom + spacing;
                left = targetRect.left + (targetRect.width / 2) - (tooltipRect.width / 2);
                break;
            case 'top':
                top = targetRect.top - tooltipRect.height - spacing;
                left = targetRect.left + (targetRect.width / 2) - (tooltipRect.width / 2);
                break;
            case 'left':
                top = targetRect.top + (targetRect.height / 2) - (tooltipRect.height / 2);
                left = targetRect.left - tooltipRect.width - spacing;
                break;
            case 'right':
                top = targetRect.top + (targetRect.height / 2) - (tooltipRect.height / 2);
                left = targetRect.right + spacing;
                break;
            default:
                top = targetRect.bottom + spacing;
                left = targetRect.left + (targetRect.width / 2) - (tooltipRect.width / 2);
        }

        // Keep tooltip in viewport with margin
        const margin = 15;
        top = Math.max(margin, Math.min(top, window.innerHeight - tooltipRect.height - margin));
        left = Math.max(margin, Math.min(left, window.innerWidth - tooltipRect.width - margin));

        this.tooltip.style.top = `${top}px`;
        this.tooltip.style.left = `${left}px`;
        this.tooltip.style.transform = 'none';
    }

    highlightElement(selector) {
        const element = document.querySelector(selector);
        if (element) {
            element.classList.add('tutorial-highlight');
        }
    }

    removeHighlight() {
        const highlighted = document.querySelectorAll('.tutorial-highlight');
        highlighted.forEach(el => el.classList.remove('tutorial-highlight'));
    }

    removeTooltip() {
        if (this.tooltip) {
            this.tooltip.remove();
            this.tooltip = null;
        }
        this.removeHighlight();
    }

    removeOverlay() {
        if (this.overlay) {
            this.overlay.remove();
            this.overlay = null;
        }
    }

    finish() {
        this.removeTooltip();
        this.removeOverlay();
        localStorage.setItem('skyscape_tutorial_seen', 'true');
        console.log('Tutorial completed!');
    }

    reset() {
        localStorage.removeItem('skyscape_tutorial_seen');
        this.hasSeenTutorial = false;
        console.log('Tutorial reset - will show on next page load');
    }
}

// Initialize tutorial when page loads
let tutorial;
document.addEventListener('DOMContentLoaded', () => {
    tutorial = new InteractiveTutorial();
    // Auto-start tutorial for first-time users
    tutorial.start();
});

// Make tutorial globally accessible for manual restart
window.restartTutorial = () => {
    if (tutorial) {
        tutorial.hasSeenTutorial = false;
        tutorial.start();
    }
};
