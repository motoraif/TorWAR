// Notification bubble system
function showNotification(message, type = 'success', duration = 4000) {
    // Remove existing notifications
    const existing = document.querySelectorAll('.notification-bubble');
    existing.forEach(n => n.remove());
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification-bubble notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => notification.classList.add('show'), 100);
    
    // Auto remove
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

// Handle sync button clicks
document.addEventListener('DOMContentLoaded', function() {
    const syncButtons = document.querySelectorAll('.sync-data-btn, a[href*="sync-trusted-advisor"], a[href*="sync-data"]');
    syncButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            showNotification('Syncing Trusted Advisor data...', 'info', 2000);
            
            const url = this.href;
            fetch(url)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showNotification(data.message || 'Sync completed successfully!', 'success');
                        setTimeout(() => window.location.reload(), 1500);
                    } else {
                        showNotification(data.message || 'Sync failed', 'error');
                    }
                })
                .catch(error => {
                    showNotification('Network error during sync', 'error');
                });
        });
    });
});
