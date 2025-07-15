/**
 * TorWAR Review Page JavaScript Fixes
 * Author: Mohamed Toraif
 * 
 * Handles dynamic white background issues on review pages
 */

(function() {
    'use strict';
    
    // Function to fix white backgrounds in dark mode
    function fixWhiteBackgrounds() {
        const isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark';
        
        if (!isDarkMode) return;
        
        // Target elements that commonly have white backgrounds
        const problematicSelectors = [
            '.progress-container',
            '.help-panel',
            '.help-section',
            '.help-title',
            '.help-content',
            '.best-practice-item',
            '[style*="background-color: white"]',
            '[style*="background-color: #ffffff"]',
            '[style*="background-color: #f8f9fa"]',
            '[style*="background-color:white"]',
            '[style*="background-color:#ffffff"]',
            '[style*="background-color:#f8f9fa"]'
        ];
        
        problematicSelectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(element => {
                // Fix background colors
                if (element.classList.contains('progress-container')) {
                    element.style.setProperty('background-color', '#1e1e1e', 'important');
                    element.style.setProperty('color', '#ffffff', 'important');
                } else if (element.classList.contains('help-panel') || 
                          element.classList.contains('help-section') ||
                          element.classList.contains('best-practice-item')) {
                    element.style.setProperty('background-color', '#1e1e1e', 'important');
                    element.style.setProperty('color', '#ffffff', 'important');
                } else {
                    // Generic fix for any element with white background
                    element.style.setProperty('background-color', '#1e1e1e', 'important');
                    element.style.setProperty('color', '#ffffff', 'important');
                }
                
                // Fix all child elements
                const children = element.querySelectorAll('*');
                children.forEach(child => {
                    child.style.setProperty('color', '#ffffff', 'important');
                    
                    // Fix links specifically
                    if (child.tagName === 'A') {
                        child.style.setProperty('color', '#58a6ff', 'important');
                    }
                });
            });
        });
        
        // Fix any remaining white backgrounds
        const allElements = document.querySelectorAll('*');
        allElements.forEach(element => {
            const computedStyle = window.getComputedStyle(element);
            const bgColor = computedStyle.backgroundColor;
            
            // Check if background is white or near-white
            if (bgColor === 'rgb(255, 255, 255)' || 
                bgColor === 'rgb(248, 249, 250)' ||
                bgColor === 'white' ||
                bgColor === '#ffffff' ||
                bgColor === '#f8f9fa') {
                
                // Don't fix form inputs, buttons, or modals
                if (!element.matches('input, select, textarea, button, .btn, .modal-content')) {
                    element.style.setProperty('background-color', '#1e1e1e', 'important');
                    element.style.setProperty('color', '#ffffff', 'important');
                }
            }
        });
    }
    
    // Function to observe DOM changes and fix new elements
    function setupMutationObserver() {
        const observer = new MutationObserver(function(mutations) {
            let shouldFix = false;
            
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                    shouldFix = true;
                }
                if (mutation.type === 'attributes' && 
                    (mutation.attributeName === 'style' || mutation.attributeName === 'class')) {
                    shouldFix = true;
                }
            });
            
            if (shouldFix) {
                setTimeout(fixWhiteBackgrounds, 100);
            }
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['style', 'class']
        });
    }
    
    // Function to handle theme changes
    function handleThemeChange() {
        // Listen for theme changes
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes' && 
                    mutation.attributeName === 'data-theme') {
                    setTimeout(fixWhiteBackgrounds, 100);
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
        
        // Also fix on window resize (for responsive elements)
        window.addEventListener('resize', function() {
            setTimeout(fixWhiteBackgrounds, 100);
        });
        
        // Fix on scroll (for sticky elements)
        window.addEventListener('scroll', function() {
            setTimeout(fixWhiteBackgrounds, 50);
        });
        
        console.log('Review page dark mode fixes initialized');
    }
    
    // Start initialization
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
    
    // Also run after a short delay to catch any late-loading elements
    setTimeout(fixWhiteBackgrounds, 500);
    setTimeout(fixWhiteBackgrounds, 1000);
    setTimeout(fixWhiteBackgrounds, 2000);
    
})();
