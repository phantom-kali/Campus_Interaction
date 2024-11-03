// Global constants and state
let currentPage = 1;
let csrfToken;

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', initializeApp);

function initializeApp() {
    csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    initializeEventHandlers();
}

function initializeEventHandlers() {
    // Initialize forms
    initializeForms();
    
    // Initialize delete button
    initializeDeleteButton();
    
    // Initialize reply forms
    document.addEventListener('click', handleReplyButtonClick);
    
    // Initialize all comment forms
    document.querySelectorAll('.comment-form').forEach(form => {
        form.addEventListener('submit', handleFormSubmit);
    });
}

function initializeForms() {
    const mainCommentForm = document.querySelector('form[action*="add_comment"]');
    if (mainCommentForm) {
        mainCommentForm.addEventListener('submit', (e) => {
            e.preventDefault();
            handleFormSubmit(e);
        });
    }

    document.querySelectorAll('.reply-form form').forEach(form => {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            handleFormSubmit(e);
        });
    });
}

function initializeDeleteButton() {
    const deleteButton = document.querySelector('.delete-event-btn');
    if (deleteButton) {
        deleteButton.addEventListener('click', async () => {
            const eventId = deleteButton.dataset.eventId;
            if (confirm("Are you sure you want to delete this event? This action cannot be undone.")) {
                await deleteEvent(eventId);
            }
        });
    }
}

// Form handling functions
async function handleFormSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const submitButton = form.querySelector('button[type="submit"]');
    const formData = new FormData(form);
    const eventId = window.location.pathname.split('/')[2];

    try {
        await showLoadingState(submitButton);
        const response = await submitFormData(form, formData, eventId);
        await handleSubmissionResponse(response, formData, form);
    } catch (error) {
        showNotification(error.message, 'error');
    } finally {
        resetSubmitButton(submitButton);
    }
}
// Updated comment handling functions
async function handleSubmissionResponse(data, formData, form) {
    if (data.status === 'success') {
        form.reset();
        const parentId = formData.get('parent_comment_id');
        
        if (parentId) {
            handleReplySubmission(parentId, data.comment_html);
            updateRepliesCount(parentId, 1);
        } else {
            handleMainCommentSubmission(data.comment_html);
        }
        
        showNotification('Comment posted successfully!', 'success');
    }
}

function handleReplySubmission(parentId, commentHtml) {
    const repliesContainer = document.getElementById(`replies-${parentId}`);
    const repliesSection = document.querySelector(`#comment-${parentId} .replies-section`);
    
    if (!repliesSection) {
        // Create new replies section if it doesn't exist
        const newRepliesSection = `
            <div class="replies-section mt-3">
                <button 
                    onclick="toggleReplies(${parentId})" 
                    class="btn btn-sm btn-link text-decoration-none ps-0"
                >
                    <i class="fas fa-chevron-down me-1"></i>
                    Show 1 reply
                </button>
                <div id="replies-${parentId}" class="replies-container mt-2 ms-4" style="display: block;">
                    ${commentHtml}
                </div>
            </div>
        `;
        document.querySelector(`#comment-${parentId} .flex-grow-1`).insertAdjacentHTML('beforeend', newRepliesSection);
    } else {
        if (!repliesContainer) {
            // Create replies container if it doesn't exist
            const container = document.createElement('div');
            container.id = `replies-${parentId}`;
            container.className = 'replies-container mt-2 ms-4';
            repliesSection.appendChild(container);
        }
        repliesContainer.style.display = 'block';
        repliesContainer.insertAdjacentHTML('afterbegin', commentHtml);
    }
    toggleReplyForm(parentId);
}

function updateRepliesCount(commentId, change) {
    const toggleButton = document.querySelector(`#comment-${commentId} .replies-section button`);
    if (toggleButton) {
        const currentCount = parseInt(toggleButton.textContent.match(/\d+/)[0]) + change;
        toggleButton.innerHTML = `
            <i class="fas fa-chevron-down me-1"></i>
            Show ${currentCount} repl${currentCount === 1 ? 'y' : 'ies'}
        `;
    }
}

// Add delete functionality
async function deleteComment(commentId, isReply = false) {
    if (!confirm("Are you sure you want to delete this comment? This action cannot be undone.")) {
        return;
    }

    try {
        const response = await fetch(`/events/comment/${commentId}/delete/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json',
            }
        });

        if (!response.ok) throw new Error('Failed to delete comment');

        const elementId = isReply ? `reply-${commentId}` : `comment-${commentId}`;
        const element = document.getElementById(elementId);
        
        if (element) {
            if (isReply) {
                // Update reply count
                const parentId = element.closest('.replies-container').id.split('-')[1];
                updateRepliesCount(parentId, -1);
            }
            element.remove();
            showNotification('Comment deleted successfully', 'success');
        }
    } catch (error) {
        showNotification('Error deleting comment', 'error');
    }
}

async function submitFormData(form, formData, eventId) {
    const response = await fetch(form.action || `/events/${eventId}/comment/`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrfToken
        },
        body: formData
    });

    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.message || 'Error posting comment');
    }
    return data;
}

// UI State Management
function showLoadingState(button) {
    button.disabled = true;
    button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Posting...';
}

function resetSubmitButton(button) {
    button.disabled = false;
    button.innerHTML = '<i class="fas fa-paper-plane"></i> Post';
}

// Comment and Reply Functions
async function handleSubmissionResponse(data, formData, form) {
    if (data.status === 'success') {
        form.reset();
        const parentId = formData.get('parent_comment_id');
        
        if (parentId) {
            handleReplySubmission(parentId, data.comment_html);
        } else {
            handleMainCommentSubmission(data.comment_html);
        }
        
        showNotification('Comment posted successfully!', 'success');
    }
}

function handleReplySubmission(parentId, commentHtml) {
    const repliesContainer = document.getElementById(`replies-${parentId}`);
    if (repliesContainer) {
        repliesContainer.style.display = 'block';
        repliesContainer.insertAdjacentHTML('afterbegin', commentHtml);
        toggleReplyForm(parentId);
    }
}

function handleMainCommentSubmission(commentHtml) {
    const commentsContainer = document.getElementById('main-comments');
    commentsContainer.insertAdjacentHTML('afterbegin', commentHtml);
}

// Toggle Functions
function toggleElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = element.style.display === 'none' ? 'block' : 'none';
    }
}

function toggleComments() {
    const commentsSection = document.getElementById('main-comments');
    const toggleButton = document.getElementById('toggleCommentsBtn');
    const isHidden = commentsSection.style.display === 'none';
    
    commentsSection.style.display = isHidden ? 'block' : 'none';
    toggleButton.textContent = isHidden ? 'Hide Comments' : 'Show Comments';
}

function toggleReplies(commentId) {
    const repliesContainer = document.getElementById(`replies-${commentId}`);
    const toggleButton = repliesContainer.previousElementSibling;
    const isHidden = repliesContainer.style.display === 'none';
    
    repliesContainer.style.display = isHidden ? 'block' : 'none';
    toggleButton.innerHTML = `
        <i class="fas fa-chevron-${isHidden ? 'up' : 'down'} me-1"></i>
        ${isHidden ? 'Hide' : 'Show'} replies
    `;
}

function toggleReplyForm(commentId) {
    const replyForm = document.getElementById(`reply-form-${commentId}`);
    if (replyForm) {
        const isHidden = replyForm.style.display === 'none';
        replyForm.style.display = isHidden ? 'block' : 'none';
        if (isHidden) {
            replyForm.querySelector('textarea').focus();
        }
    }
}

// API Functions
async function toggleLike(commentId) {
    try {
        const response = await fetch(`/events/comment/${commentId}/like/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json',
            }
        });

        if (!response.ok) throw new Error('Failed to toggle like');
        
        const data = await response.json();
        updateLikeButton(commentId, data.likes_count);
    } catch (error) {
        showNotification('Error updating like', 'error');
    }
}

async function deleteEvent(eventId) {
    try {
        const response = await fetch(`/events/${eventId}/delete/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json',
            }
        });

        if (response.ok) {
            window.location.href = '/events/';
        } else {
            const data = await response.json();
            showNotification(data.message || "Failed to delete event.", 'error');
        }
    } catch (error) {
        showNotification("Error deleting event.", 'error');
    }
}

async function loadMoreComments(eventId) {
    try {
        currentPage += 1;
        const response = await fetch(`/events/${eventId}/load-more-comments?page=${currentPage}`);
        const data = await response.json();
        
        if (data.comments_html) {
            document.getElementById('comments-container').insertAdjacentHTML('beforeend', data.comments_html);
        } else {
            document.getElementById('load-more-button').style.display = 'none';
        }
    } catch (error) {
        console.error("Error loading comments:", error);
        showNotification('Error loading more comments', 'error');
    }
}

// Helper Functions
function updateLikeButton(commentId, likesCount) {
    const likeButton = document.querySelector(`button[data-comment-id="${commentId}"], button[data-reply-id="${commentId}"]`);
    const likesCountElement = likeButton.querySelector('.likes-count');
    
    likeButton.classList.toggle('btn-danger');
    likeButton.classList.toggle('btn-outline-danger');
    likesCountElement.textContent = likesCount;
}

function handleReplyButtonClick(e) {
    if (e.target.matches('.reply-button')) {
        const commentId = e.target.dataset.commentId;
        toggleReplyForm(commentId);
    }
}

function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
    notification.style.zIndex = '1050';
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('fade-out');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Make functions available globally
window.toggleReplyForm = toggleReplyForm;
window.toggleReplies = toggleReplies;
window.toggleLike = toggleLike;
window.toggleComments = toggleComments;
window.loadMoreComments = loadMoreComments;