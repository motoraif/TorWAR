/**
 * TorWAR Review Page JavaScript Fixes - Optimized
 * Author: Mohamed Toraif
 * 
 * Handles dynamic white background issues on review pages with performance optimization
 */

(function() {
    'use strict';
    
    let isFixing = false;
    
    // Function to fix white backgrounds in dark mode
    function fixWhiteBackgrounds() {
        if (isFixing) return;
        isFixing = true;
        
        requestAnimationFrame(() => {
            const isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark';
            
            if (!isDarkMode) {
                isFixing = false;
                return;
            }
            
            // Batch DOM operations
            const problematicSelectors = [
                '.progress-container',
                '.help-panel',
                '.help-section',
                '.help-title',
                '.help-content',
                '.best-practice-item'
            ];
            
            const elementsToFix = [];
            
            problematicSelectors.forEach(selector => {
                const elements = document.querySelectorAll(selector);
                elements.forEach(element => elementsToFix.push(element));
            });
            
            // Apply fixes in batches
            elementsToFix.forEach(element => {
                element.style.cssText += 'background-color: #1e1e1e !important; color: #ffffff !important;';
                
                // Fix child links
                const links = element.querySelectorAll('a');
                links.forEach(link => {
                    link.style.color = '#58a6ff';
                });
            });
            
            isFixing = false;
        });
    }
    
    // Throttled mutation observer
    let observerTimeout;
    function setupMutationObserver() {
        const observer = new MutationObserver(function(mutations) {
            if (observerTimeout) return;
            
            observerTimeout = setTimeout(() => {
                fixWhiteBackgrounds();
                observerTimeout = null;
            }, 100);
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['style', 'class']
        });
    }
    
    // Throttled theme change handler
    function handleThemeChange() {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes' && 
                    mutation.attributeName === 'data-theme') {
                    setTimeout(fixWhiteBackgrounds, 50);
                }
            });
        });
        
        observer.observe(document.documentElement, {
            attributes: true,
            attributeFilter: ['data-theme']
        });
    }
    
    // Initialize when DOM is ready
    function initialize() {
        fixWhiteBackgrounds();
        setupMutationObserver();
        handleThemeChange();
    }
    
    // Start initialization
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
    
})();
