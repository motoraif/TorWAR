// TorWAR Optimized Main JavaScript
// Consolidated from multiple JS files for better performance

class TorWAR {
  constructor() {
    this.domBatcher = new DOMBatcher();
    this.init();
  }

  init() {
    this.setupThemeToggle();
    this.setupNotifications();
    this.setupPerformanceOptimizations();
    this.setupLazyLoading();
    this.setupDebouncing();
  }

  // Debounce function to prevent excessive calls
  debounce(func, wait) {
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
  throttle(func, limit) {
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

  setupThemeToggle() {
    const theme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', theme);
    
    const toggleBtn = document.getElementById('theme-toggle');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Update toggle button icon
        const icon = toggleBtn.querySelector('i');
        if (icon) {
          icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
      });
    }
  }

  setupNotifications() {
    window.showNotification = (message, type = 'info', duration = 5000) => {
      const notification = document.createElement('div');
      notification.className = `notification ${type}`;
      notification.innerHTML = `
        <div class="d-flex justify-content-between align-items-start">
          <div class="notification-content">${message}</div>
          <button type="button" class="btn-close ms-2" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
      `;
      
      document.body.appendChild(notification);
      
      // Trigger show animation
      setTimeout(() => notification.classList.add('show'), 10);
      
      // Auto remove
      setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
      }, duration);
    };
  }

  setupPerformanceOptimizations() {
    // Batch DOM operations to prevent forced reflows
    this.setupDOMBatching();
    
    // Optimize scroll events
    const optimizedScroll = this.throttle(() => {
      // Handle scroll events efficiently
      this.handleScroll();
    }, 16); // ~60fps
    
    window.addEventListener('scroll', optimizedScroll, { passive: true });
    
    // Optimize resize events
    const optimizedResize = this.debounce(() => {
      this.handleResize();
    }, 250);
    
    window.addEventListener('resize', optimizedResize);
  }

  setupLazyLoading() {
    // Lazy load images
    const images = document.querySelectorAll('img[data-src]');
    
    if ('IntersectionObserver' in window) {
      const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target;
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
            img.classList.add('loaded');
            imageObserver.unobserve(img);
          }
        });
      }, {
        rootMargin: '50px 0px',
        threshold: 0.01
      });
      
      images.forEach(img => imageObserver.observe(img));
    } else {
      // Fallback for older browsers
      images.forEach(img => {
        img.src = img.dataset.src;
        img.removeAttribute('data-src');
      });
    }
  }

  setupDebouncing() {
    // Debounce search inputs
    const searchInputs = document.querySelectorAll('input[type="search"], input[data-search]');
    searchInputs.forEach(input => {
      const debouncedSearch = this.debounce((value) => {
        const event = new CustomEvent('debouncedSearch', { detail: value });
        input.dispatchEvent(event);
      }, 300);
      
      input.addEventListener('input', (e) => {
        debouncedSearch(e.target.value);
      });
    });
  }

  setupDOMBatching() {
    // Batch DOM reads and writes to prevent layout thrashing
    this.domBatcher.scheduleWork();
  }

  handleScroll() {
    // Efficient scroll handling
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    
    // Update scroll-dependent elements
    this.domBatcher.write(() => {
      document.documentElement.style.setProperty('--scroll-y', scrollTop + 'px');
    });
  }

  handleResize() {
    // Efficient resize handling
    const width = window.innerWidth;
    const height = window.innerHeight;
    
    this.domBatcher.write(() => {
      document.documentElement.style.setProperty('--viewport-width', width + 'px');
      document.documentElement.style.setProperty('--viewport-height', height + 'px');
    });
  }
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
    if (!this.scheduled) {
      this.scheduled = true;
      requestAnimationFrame(() => this.flush());
    }
  }
  
  flush() {
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
  }
  
  scheduleWork() {
    // Schedule regular batching work
    setInterval(() => {
      if (this.readQueue.length || this.writeQueue.length) {
        this.schedule();
      }
    }, 16); // ~60fps
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.torwar = new TorWAR();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = TorWAR;
}
