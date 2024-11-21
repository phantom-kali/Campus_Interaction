// comment-system.js

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the comment system
    initializeCommentSystem();
});

function initializeCommentSystem() {
    // Main comment form submission
    const commentForm = document.getElementById('commentForm');
    if (commentForm) {
        commentForm.addEventListener('submit', handleCommentSubmission);
    }

    // Initialize all reply forms
    document.addEventListener('click', function(e) {
        // Reply button click handler
        if (e.target.matches('.reply-button') || e.target.closest('.reply-button')) {
            e.preventDefault();
            const button = e.target.closest('.reply-button');
            const commentId = button.dataset.commentId;
            toggleReplyForm(commentId);
        }

        // Cancel reply button handler
        if (e.target.matches('.cancel-reply') || e.target.closest('.cancel-reply')) {
            e.preventDefault();
            const button = e.target.closest('.cancel-reply');
            const commentId = button.dataset.commentId;
            hideReplyForm(commentId);
        }

        // Other click handlers remain the same...
        if (e.target.matches('.toggle-replies') || e.target.closest('.toggle-replies')) {
            handleToggleReplies(e);
        }

        if (e.target.matches('.like-button') || e.target.closest('.like-button')) {
            handleLikeToggle(e);
        }

        if (e.target.matches('.delete-comment') || e.target.closest('.delete-comment')) {
            handleCommentDeletion(e);
        }

        if (e.target.matches('.delete-reply') || e.target.closest('.delete-reply')) {
            handleReplyDeletion(e);
        }
    });

    // Initialize all reply forms for submission
    document.addEventListener('submit', function(e) {
        if (e.target.classList.contains('reply-form')) {
            e.preventDefault();
            handleReplySubmission(e);
        }
    });
}
async function handleCommentSubmission(e) {
    e.preventDefault();
    const form = e.target;
    const url = form.getAttribute('action');
    const formData = new FormData(form);

    try {
        const response = await fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        const data = await response.json();

        if (response.ok) {
            // Insert the new comment at the top of the comments section
            const commentsSection = document.getElementById('main-comments');
            commentsSection.insertAdjacentHTML('afterbegin', data.comment_html);
            
            // Clear the form
            form.reset();
            
            // Show success message
            showNotification('Comment posted successfully!', 'success');
        } else {
            throw new Error(data.message || 'Error posting comment');
        }
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

function handleReplyButtonClick(e) {
    const button = e.target.closest('.reply-button');
    const commentId = button.dataset.commentId;
    const replyForm = document.getElementById(`reply-form-${commentId}`);
    
    // Hide all other reply forms first
    document.querySelectorAll('.reply-form').forEach(form => {
        if (form.id !== `reply-form-${commentId}`) {
            form.style.display = 'none';
        }
    });

    // Toggle the clicked reply form
    replyForm.style.display = replyForm.style.display === 'none' ? 'block' : 'none';
}

function handleCancelReply(e) {
    const button = e.target.closest('.cancel-reply');
    const commentId = button.dataset.commentId;
    const replyForm = document.getElementById(`reply-form-${commentId}`);
    replyForm.style.display = 'none';
}

async function handleReplySubmission(e) {
    e.preventDefault();
    const form = e.target;
    const url = form.getAttribute('action');
    const formData = new FormData(form);

    try {
        const response = await fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        const data = await response.json();

        if (response.ok) {
            // Get the parent comment's replies container
            const commentId = formData.get('parent_comment_id');
            const repliesContainer = document.getElementById(`replies-${commentId}`);
            
            // Insert the new reply
            repliesContainer.insertAdjacentHTML('beforeend', data.comment_html);
            
            // Clear and hide the reply form
            form.reset();
            form.closest('.reply-form').style.display = 'none';
            
            // Update replies count and show the replies section
            updateRepliesCount(commentId);
            showNotification('Reply posted successfully!', 'success');
        } else {
            throw new Error(data.message || 'Error posting reply');
        }
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

function toggleReplyForm(commentId) {
    // Hide all other reply forms first
    document.querySelectorAll('.reply-form').forEach(form => {
        if (form.id !== `reply-form-${commentId}`) {
            form.style.display = 'none';
        }
    });

    // Toggle the clicked reply form
    const replyForm = document.getElementById(`reply-form-${commentId}`);
    if (replyForm) {
        const isHidden = replyForm.style.display === 'none' || replyForm.style.display === '';
        replyForm.style.display = isHidden ? 'block' : 'none';
        
        // Focus on textarea if showing form
        if (isHidden) {
            const textarea = replyForm.querySelector('textarea');
            if (textarea) {
                textarea.focus();
            }
        }
    }
}
function hideReplyForm(commentId) {
    const replyForm = document.getElementById(`reply-form-${commentId}`);
    if (replyForm) {
        replyForm.style.display = 'none';
        replyForm.reset();
    }
}

async function handleReplySubmission(e) {
    e.preventDefault();
    const form = e.target;
    const url = form.getAttribute('action');
    const formData = new FormData(form);

    try {
        const response = await fetch(url, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        const data = await response.json();

        if (response.ok) {
            // Get the parent comment's replies container
            const commentId = formData.get('parent_comment_id');
            let repliesContainer = document.getElementById(`replies-${commentId}`);
            
            // If there's no replies container yet, create one
            if (!repliesContainer) {
                const commentCard = document.getElementById(`comment-${commentId}`);
                const repliesSection = document.createElement('div');
                repliesSection.className = 'replies-section mt-3';
                repliesSection.innerHTML = `
                    <button class="btn btn-sm btn-link text-decoration-none ps-0 toggle-replies"
                            data-comment-id="${commentId}">
                        <i class="fas fa-chevron-down me-1"></i>
                        Show 1 reply
                    </button>
                    <div id="replies-${commentId}" class="replies-container mt-2 ms-4">
                    </div>
                `;
                commentCard.querySelector('.flex-grow-1').appendChild(repliesSection);
                repliesContainer = document.getElementById(`replies-${commentId}`);
            }

            // Insert the new reply
            repliesContainer.insertAdjacentHTML('beforeend', data.comment_html);
            
            // Clear and hide the reply form
            form.reset();
            hideReplyForm(commentId);
            
            // Update replies count
            updateRepliesCount(commentId);
            showNotification('Reply posted successfully!', 'success');

            // Show replies if they were hidden
            repliesContainer.style.display = 'block';
            const toggleButton = document.querySelector(`[data-comment-id="${commentId}"].toggle-replies`);
            if (toggleButton) {
                toggleButton.innerHTML = '<i class="fas fa-chevron-up me-1"></i>Hide replies';
            }
        } else {
            throw new Error(data.message || 'Error posting reply');
        }
    } catch (error) {
        showNotification(error.message, 'error');
    }
}
function handleToggleReplies(e) {
    const button = e.target.closest('.toggle-replies');
    const commentId = button.dataset.commentId;
    const repliesContainer = document.getElementById(`replies-${commentId}`);
    
    if (repliesContainer.style.display === 'none') {
        repliesContainer.style.display = 'block';
        button.innerHTML = '<i class="fas fa-chevron-up me-1"></i>Hide replies';
    } else {
        repliesContainer.style.display = 'none';
        button.innerHTML = '<i class="fas fa-chevron-down me-1"></i>Show replies';
    }
}

async function handleLikeToggle(e) {
    const button = e.target.closest('.like-button');
    const url = button.dataset.url;
    const isLiked = button.dataset.liked === 'true';

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        const data = await response.json();

        if (response.ok) {
            // Update like button appearance and count
            button.dataset.liked = (!isLiked).toString();
            button.classList.toggle('btn-danger', !isLiked);
            button.classList.toggle('btn-outline-danger', isLiked);
            
            const likesCount = button.querySelector('.likes-count');
            likesCount.textContent = data.likes_count;
        } else {
            throw new Error(data.message || 'Error toggling like');
        }
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function handleCommentDeletion(e) {
    if (!confirm('Are you sure you want to delete this comment?')) return;

    const button = e.target.closest('.delete-comment');
    const url = button.dataset.url;
    const commentId = button.dataset.commentId;

    try {
        const response = await fetch(url, {
            method: 'DELETE',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (response.ok) {
            // Remove the comment from the DOM
            const commentElement = document.getElementById(`comment-${commentId}`);
            commentElement.remove();
            showNotification('Comment deleted successfully!', 'success');
        } else {
            throw new Error('Error deleting comment');
        }
    } catch (error) {
        showNotification(error.message, 'error');
    }
}

async function handleReplyDeletion(e) {
    if (!confirm('Are you sure you want to delete this reply?')) return;

    const button = e.target.closest('.delete-reply');
    const url = button.dataset.url;
    const replyId = button.dataset.replyId;

    try {
        const response = await fetch(url, {
            method: 'DELETE',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        if (response.ok) {
            // Remove the reply from the DOM
            const replyElement = document.getElementById(`reply-${replyId}`);
            const commentId = replyElement.closest('.comment-card').id.split('-')[1];
            replyElement.remove();
            
            // Update replies count
            updateRepliesCount(commentId);
            showNotification('Reply deleted successfully!', 'success');
        } else {
            throw new Error('Error deleting reply');
        }
    } catch (error) {
        showNotification(error.message, 'error');
    }
}


// ... (rest of the functions remain the same)

function updateRepliesCount(commentId) {
    const repliesContainer = document.getElementById(`replies-${commentId}`);
    if (repliesContainer) {
        const repliesCount = repliesContainer.children.length;
        const toggleButton = document.querySelector(`[data-comment-id="${commentId}"].toggle-replies`);
        
        if (toggleButton) {
            const text = repliesCount === 1 ? 'reply' : 'replies';
            toggleButton.innerHTML = `<i class="fas fa-chevron-down me-1"></i>Show ${repliesCount} ${text}`;
        }
    }
}

function showNotification(message, type = 'success') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} position-fixed top-0 end-0 m-3`;
    notification.style.zIndex = '1050';
    notification.textContent = message;

    // Add to document
    document.body.appendChild(notification);

    // Remove after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}