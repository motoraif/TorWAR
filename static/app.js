/**
 * TorWAR Simplified JavaScript
 * Author: Mohamed Toraif
 * 
 * Essential functionality without complex animations
 */

class TorWARUI {
    constructor() {
        this.init();
    }

    init() {
        this.setupBasicInteractivity();
        this.setupFormEnhancements();
        this.setupStatusMonitoring();
    }

    /**
     * Setup basic interactive elements
     */
    setupBasicInteractivity() {
        // Simple button loading states
        document.querySelectorAll('form button[type="submit"]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const form = btn.closest('form');
                if (form && form.checkValidity()) {
                    this.setButtonLoading(btn, true);
                }
            });
        });

        // Simple card hover effects
        document.querySelectorAll('.card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-2px)';
                card.style.boxShadow = '0 4px 8px rgba(0,0,0,0.15)';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0)';
                card.style.boxShadow = '';
            });
        });
    }

    /**
     * Set button loading state
     */
    setButtonLoading(button, loading) {
        if (loading) {
            button.dataset.originalText = button.innerHTML;
            button.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
            button.disabled = true;
            button.classList.add('loading');
        } else {
            button.innerHTML = button.dataset.originalText || button.innerHTML;
            button.disabled = false;
            button.classList.remove('loading');
        }
    }

    /**
     * Setup form enhancements
     */
    setupFormEnhancements() {
        // Auto-save form data to localStorage (non-sensitive only)
        document.querySelectorAll('form input:not([type="password"]), form textarea, form select').forEach(input => {
            if (input.name && input.name !== 'password') {
                const key = `torwar_form_${input.name}`;
                
                // Load saved data
                const savedValue = localStorage.getItem(key);
                if (savedValue && input.value === '') {
                    input.value = savedValue;
                }
                
                // Save data on change
                input.addEventListener('change', () => {
                    localStorage.setItem(key, input.value);
                });
            }
        });

        // Form validation feedback
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', (e) => {
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn && form.checkValidity()) {
                    this.setButtonLoading(submitBtn, true);
                    
                    // Auto-remove loading after 10 seconds as fallback
                    setTimeout(() => {
                        this.setButtonLoading(submitBtn, false);
                    }, 10000);
                }
            });
        });
    }

    /**
     * Setup AWS connection status monitoring
     */
    setupStatusMonitoring() {
        // Check connection status every 60 seconds (less frequent)
        if (document.querySelector('.alert-success')) {
            this.statusCheckInterval = setInterval(() => {
                this.checkAWSStatus();
            }, 60000);
        }
    }

    /**
     * Check AWS connection status
     */
    async checkAWSStatus() {
        try {
            const response = await fetch('/aws-status', {
                method: 'GET',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            if (!response.ok) {
                console.warn('Status check returned:', response.status);
            }
        } catch (error) {
            console.warn('Status check failed:', error.message);
        }
    }

    /**
     * Show simple notification
     */
    showNotification(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(alertDiv, container.firstChild);
            
            // Auto-dismiss after 5 seconds
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        }
    }

    /**
     * Cleanup method
     */
    destroy() {
        if (this.statusCheckInterval) {
            clearInterval(this.statusCheckInterval);
        }
    }
}

// Initialize TorWAR UI when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.torwarUI = new TorWARUI();
    
    // Simple tooltip initialization for Bootstrap
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
    }
    
    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // ESC key to close modals
        if (e.key === 'Escape') {
            const activeModal = document.querySelector('.modal.show');
            if (activeModal && typeof bootstrap !== 'undefined') {
                const modal = bootstrap.Modal.getInstance(activeModal);
                if (modal) modal.hide();
            }
        }
    });
});

// Simple utility functions
window.TorWARUtils = {
    /**
     * Format file size
     */
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    /**
     * Format date
     */
    formatDate: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    },

    /**
     * Copy text to clipboard
     */
    copyToClipboard: function(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(() => {
                if (window.torwarUI) {
                    window.torwarUI.showNotification('Copied to clipboard!', 'success');
                }
            });
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            
            if (window.torwarUI) {
                window.torwarUI.showNotification('Copied to clipboard!', 'success');
            }
        }
    }
};
