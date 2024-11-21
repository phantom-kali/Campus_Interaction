document.addEventListener('DOMContentLoaded', function() {
    // Delegate event listener for delete buttons
    document.querySelectorAll('.delete-event-btn').forEach(button => {
        button.addEventListener('click', async function(e) {
            e.preventDefault();
            
            if (!confirm('Are you sure you want to delete this event?')) {
                return;
            }

            const eventId = this.getAttribute('data-event-id');
            
            try {
                const response = await fetch(`/events/${eventId}/delete/`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': getCsrfToken(),
                        'Content-Type': 'application/json',
                    },
                    credentials: 'same-origin'  // Important for CSRF
                });

                const data = await response.json();

                if (response.ok) {
                    console.log("Redirecting to event list...");
                    window.location.href = '/events/';
                } else {
                    showNotification(data.message || 'Failed to delete event', 'error');
                }
                
            } catch (error) {
                console.error('Error:', error);
                showNotification('Error deleting event', 'error');
            }
        });
    });

    // Helper function to get CSRF token
    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    // Helper function to show notifications
    function showNotification(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.role = 'alert';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        document.querySelector('#notifications-container').appendChild(alertDiv);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alertDiv.remove();
        }, 2000);
    }
});