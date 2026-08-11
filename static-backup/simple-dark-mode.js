/**
 * TorWAR Simple Dark Mode Manager
 * Author: Mohamed Toraif
 * Simplified dark mode implementation
 */

(function() {
    'use strict';
    
    const STORAGE_KEY = 'torwar-dark-mode';
    const THEME_ATTRIBUTE = 'data-theme';
    
    // Initialize theme immediately to prevent flash
    function initializeTheme() {
        const savedTheme = localStorage.getItem(STORAGE_KEY);
        const systemPrefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        const theme = savedTheme || (systemPrefersDark ? 'dark' : 'light');
        
        document.documentElement.setAttribute(THEME_ATTRIBUTE, theme);
        document.documentElement.classList.add('theme-loading');
        
        return theme;
    }
    
    // Update toggle button icon
    function updateToggleIcon(theme) {
        const icon = document.getElementById('darkModeIcon');
        if (icon) {
            icon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    }
    
    // Toggle theme
    function toggleTheme() {
        const currentTheme = document.documentElement.getAttribute(THEME_ATTRIBUTE);
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute(THEME_ATTRIBUTE, newTheme);
        localStorage.setItem(STORAGE_KEY, newTheme);
        updateToggleIcon(newTheme);
        
        console.log(`Theme switched to: ${newTheme}`);
    }
    
    // Setup event listeners
    function setupEventListeners() {
        const toggleButton = document.getElementById('darkModeToggle');
        if (toggleButton) {
            toggleButton.addEventListener('click', toggleTheme);
        }
        
        // Listen for system theme changes
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addEventListener('change', function(e) {
                // Only update if user hasn't manually set a preference
                if (!localStorage.getItem(STORAGE_KEY)) {
                    const newTheme = e.matches ? 'dark' : 'light';
                    document.documentElement.setAttribute(THEME_ATTRIBUTE, newTheme);
                    updateToggleIcon(newTheme);
                }
            });
        }
    }
    
    // Initialize on page load
    function initialize() {
        const currentTheme = initializeTheme();
        
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                updateToggleIcon(currentTheme);
                setupEventListeners();
                
                // Remove loading class to enable transitions
                setTimeout(() => {
                    document.documentElement.classList.remove('theme-loading');
                }, 100);
            });
        } else {
            updateToggleIcon(currentTheme);
            setupEventListeners();
            
            // Remove loading class to enable transitions
            setTimeout(() => {
                document.documentElement.classList.remove('theme-loading');
            }, 100);
        }
    }
    
    // Start initialization
    initialize();
    
    // Export for debugging
    window.TorWARDarkMode = {
        toggle: toggleTheme,
        getCurrentTheme: () => document.documentElement.getAttribute(THEME_ATTRIBUTE),
        setTheme: (theme) => {
            document.documentElement.setAttribute(THEME_ATTRIBUTE, theme);
            localStorage.setItem(STORAGE_KEY, theme);
            updateToggleIcon(theme);
        }
    };
})();
