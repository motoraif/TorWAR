/**
 * TorWAR Dark Mode Manager
 * Author: Mohamed Toraif
 * 
 * Handles dark mode toggle, persistence, and system preference detection
 */

class DarkModeManager {
    constructor() {
        this.storageKey = 'torwar-dark-mode';
        this.toggleButton = null;
        this.toggleIcon = null;
        this.init();
    }

    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.setup());
        } else {
            this.setup();
        }
    }

    setup() {
        this.toggleButton = document.getElementById('darkModeToggle');
        this.toggleIcon = document.getElementById('darkModeIcon');
        
        if (!this.toggleButton || !this.toggleIcon) {
            console.warn('Dark mode toggle elements not found');
            return;
        }

        // Set initial theme (theme was already applied in IIFE above)
        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        this.updateToggleIcon(currentTheme);
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Listen for system theme changes
        this.setupSystemThemeListener();
        
        // Remove loading class to enable transitions
        setTimeout(() => {
            document.documentElement.classList.remove('theme-loading');
        }, 100);
        
        console.log('Dark mode manager initialized');
    }

    setInitialTheme() {
        const savedTheme = this.getSavedTheme();
        const systemTheme = this.getSystemTheme();
        
        let theme;
        if (savedTheme) {
            theme = savedTheme;
        } else {
            theme = systemTheme;
        }
        
        this.applyTheme(theme);
        this.updateToggleIcon(theme);
    }

    getSavedTheme() {
        try {
            return localStorage.getItem(this.storageKey);
        } catch (e) {
            console.warn('Could not access localStorage for theme preference');
            return null;
        }
    }

    getSystemTheme() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    getCurrentTheme() {
        return document.documentElement.getAttribute('data-theme') || 'light';
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        
        // Update meta theme-color for mobile browsers
        this.updateMetaThemeColor(theme);
        
        // Dispatch custom event for other components
        window.dispatchEvent(new CustomEvent('themeChanged', { 
            detail: { theme } 
        }));
    }

    updateMetaThemeColor(theme) {
        let metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (!metaThemeColor) {
            metaThemeColor = document.createElement('meta');
            metaThemeColor.name = 'theme-color';
            document.head.appendChild(metaThemeColor);
        }
        
        metaThemeColor.content = theme === 'dark' ? '#1a1a1a' : '#ffffff';
    }

    saveTheme(theme) {
        try {
            localStorage.setItem(this.storageKey, theme);
        } catch (e) {
            console.warn('Could not save theme preference to localStorage');
        }
    }

    toggleTheme() {
        const currentTheme = this.getCurrentTheme();
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        this.applyTheme(newTheme);
        this.saveTheme(newTheme);
        this.updateToggleIcon(newTheme);
        
        // Add a subtle animation to indicate the change
        this.animateToggle();
        
        // Announce to screen readers
        this.announceThemeChange(newTheme);
    }

    updateToggleIcon(theme) {
        if (!this.toggleIcon) return;
        
        if (theme === 'dark') {
            this.toggleIcon.className = 'fas fa-sun';
            this.toggleButton.title = 'Switch to Light Mode';
            this.toggleButton.setAttribute('aria-label', 'Switch to Light Mode');
        } else {
            this.toggleIcon.className = 'fas fa-moon';
            this.toggleButton.title = 'Switch to Dark Mode';
            this.toggleButton.setAttribute('aria-label', 'Switch to Dark Mode');
        }
        
        // Ensure button styling is maintained
        this.toggleButton.style.border = 'none';
        this.toggleButton.style.background = 'none';
        this.toggleButton.style.textDecoration = 'none';
    }

    animateToggle() {
        if (!this.toggleButton) return;
        
        this.toggleButton.style.transform = 'scale(0.9)';
        setTimeout(() => {
            this.toggleButton.style.transform = 'scale(1)';
        }, 150);
    }

    announceThemeChange(theme) {
        // Create a temporary element for screen reader announcement
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = `Switched to ${theme} mode`;
        
        document.body.appendChild(announcement);
        
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }

    setupEventListeners() {
        if (this.toggleButton) {
            this.toggleButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggleTheme();
            });
            
            // Keyboard support
            this.toggleButton.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.toggleTheme();
                }
            });
        }
        
        // Listen for theme change events from other parts of the app
        window.addEventListener('themeChanged', (e) => {
            console.log('Theme changed to:', e.detail.theme);
        });
    }

    setupSystemThemeListener() {
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            
            mediaQuery.addEventListener('change', (e) => {
                // Only auto-switch if user hasn't manually set a preference
                const savedTheme = this.getSavedTheme();
                if (!savedTheme) {
                    const newTheme = e.matches ? 'dark' : 'light';
                    this.applyTheme(newTheme);
                    this.updateToggleIcon(newTheme);
                }
            });
        }
    }

    // Public methods for external use
    setTheme(theme) {
        if (theme !== 'light' && theme !== 'dark') {
            console.warn('Invalid theme:', theme);
            return;
        }
        
        this.applyTheme(theme);
        this.saveTheme(theme);
        this.updateToggleIcon(theme);
    }

    getTheme() {
        return this.getCurrentTheme();
    }

    // Reset to system preference
    resetToSystem() {
        try {
            localStorage.removeItem(this.storageKey);
        } catch (e) {
            console.warn('Could not remove theme preference from localStorage');
        }
        
        const systemTheme = this.getSystemTheme();
        this.applyTheme(systemTheme);
        this.updateToggleIcon(systemTheme);
    }
}

// Initialize dark mode manager
window.darkModeManager = new DarkModeManager();

// Utility functions for other scripts
window.DarkModeUtils = {
    /**
     * Check if dark mode is currently active
     */
    isDarkMode: function() {
        return document.documentElement.getAttribute('data-theme') === 'dark';
    },

    /**
     * Get current theme
     */
    getCurrentTheme: function() {
        return document.documentElement.getAttribute('data-theme') || 'light';
    },

    /**
     * Listen for theme changes
     */
    onThemeChange: function(callback) {
        window.addEventListener('themeChanged', (e) => {
            callback(e.detail.theme);
        });
    },

    /**
     * Get theme-appropriate color
     */
    getThemeColor: function(lightColor, darkColor) {
        return this.isDarkMode() ? darkColor : lightColor;
    }
};

// Add keyboard shortcut for theme toggle (Ctrl+Shift+D)
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.shiftKey && e.key === 'D') {
        e.preventDefault();
        if (window.darkModeManager) {
            window.darkModeManager.toggleTheme();
        }
    }
});

// Remove the duplicate IIFE since we now have inline initialization
// The theme is already set by the inline script in base.html
