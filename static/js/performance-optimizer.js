/**
 * TorWAR Performance Optimizer
 * Author: Mohamed Toraif
 * 
 * Optimizes heavy operations and prevents performance violations
 */

(function() {
    'use strict';
    
    // Debounce function to prevent excessive calls
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Throttle function for scroll/resize events
    function throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
    
    // Batch DOM operations to prevent forced reflows
    class DOMBatcher {
        constructor() {
            this.readQueue = [];
            this.writeQueue = [];
            this.scheduled = false;
        }
        
        read(fn) {
            this.readQueue.push(fn);
            this.schedule();
        }
        
        write(fn) {
            this.writeQueue.push(fn);
            this.schedule();
        }
        
        schedule() {
            if (this.scheduled) return;
            this.scheduled = true;
            
            requestAnimationFrame(() => {
                // Execute all reads first
                while (this.readQueue.length) {
                    const fn = this.readQueue.shift();
                    fn();
                }
                
                // Then execute all writes
                while (this.writeQueue.length) {
                    const fn = this.writeQueue.shift();
                    fn();
                }
                
                this.scheduled = false;
            });
        }
    }
    
    // Global DOM batcher instance
    window.domBatcher = new DOMBatcher();
    
    // Optimize heavy operations by breaking them into chunks
    function processInChunks(items, processor, chunkSize = 50) {
        let index = 0;
        
        function processChunk() {
            const end = Math.min(index + chunkSize, items.length);
            
            for (let i = index; i < end; i++) {
                processor(items[i], i);
            }
            
            index = end;
            
            if (index < items.length) {
                // Use requestIdleCallback if available, otherwise setTimeout
                if (window.requestIdleCallback) {
                    requestIdleCallback(processChunk);
                } else {
                    setTimeout(processChunk, 0);
                }
            }
        }
        
        processChunk();
    }
    
    // Optimize scroll events
    const optimizedScrollHandler = throttle(function() {
        // Handle scroll events here
    }, 16); // ~60fps
    
    // Optimize resize events
    const optimizedResizeHandler = debounce(function() {
        // Handle resize events here
    }, 250);
    
    // Replace heavy setTimeout operations
    function optimizeTimeouts() {
        const originalSetTimeout = window.setTimeout;
        
        window.setTimeout = function(callback, delay, ...args) {
            // If delay is very long (>1000ms), break it into smaller chunks
            if (delay > 1000) {
                let remaining = delay;
                const chunkSize = 100;
                
                function executeChunk() {
                    if (remaining <= chunkSize) {
                        return originalSetTimeout(callback, remaining, ...args);
                    } else {
                        remaining -= chunkSize;
                        return originalSetTimeout(executeChunk, chunkSize);
                    }
                }
                
                return executeChunk();
            }
            
            return originalSetTimeout(callback, delay, ...args);
        };
    }
    
    // Initialize performance optimizations
    function init() {
        // Optimize timeouts
        optimizeTimeouts();
        
        // Add optimized event listeners
        window.addEventListener('scroll', optimizedScrollHandler, { passive: true });
        window.addEventListener('resize', optimizedResizeHandler);
        
        // Expose utilities globally
        window.TorWARPerf = {
            debounce,
            throttle,
            processInChunks,
            domBatcher: window.domBatcher
        };
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
})();
