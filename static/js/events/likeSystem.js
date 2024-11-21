
// Like System
const LikeSystem = {
    init() {
        // Event delegation for all like buttons
        document.addEventListener('click', (e) => {
            const likeButton = e.target.closest('.like-button');
            if (likeButton) {
                e.preventDefault();
                this.handleLikeClick(likeButton);
            }
        });
    },

    async handleLikeClick(button) {
        const commentId = button.dataset.commentId;
        const replyId = button.dataset.replyId;
        const isReply = !!replyId;  // Check if this is a reply (if `replyId` exists)
        const id = isReply ? replyId : commentId;
        const url = isReply 
            ? `/events/reply/${id}/like/` 
            : `/events/comment/${id}/like/`;

        try {
            // Prevent double-clicks
            button.disabled = true;

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCSRFToken(),
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) throw new Error('Failed to toggle like');

            const data = await response.json();

            // Ensure UI reflects server's response
            this.updateLikeButton(button, data.likes_count, data.is_liked);

        } catch (error) {
            console.error('Like error:', error);
            this.showError('Error updating like');
        } finally {
            button.disabled = false;
        }
    },

    updateLikeButton(button, likesCount, isLiked) {
        // Update the displayed like count
        const likesCountElement = button.querySelector('.likes-count');
        likesCountElement.textContent = likesCount; // Use server's exact response

        // Toggle button class based on liked state
        if (isLiked) {
            button.classList.remove('btn-outline-danger');
            button.classList.add('btn-danger');
            button.dataset.liked = 'true';
        } else {
            button.classList.remove('btn-danger');
            button.classList.add('btn-outline-danger');
            button.dataset.liked = 'false';
        }
    },

    getCSRFToken() {
        return document.querySelector('meta[name="csrf-token"]')?.content || 
               document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    },

    showError(message) {
        // Display your notification or alert
        alert(message);
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => LikeSystem.init());

// Helper Functions
// function updateLikeButton(commentId, likesCount) {
//     const likeButton = document.querySelector(`button[data-comment-id="${commentId}"], button[data-reply-id="${commentId}"]`);
//     const likesCountElement = likeButton.querySelector('.likes-count');
    
//     likeButton.classList.toggle('btn-danger');
//     likeButton.classList.toggle('btn-outline-danger');
//     likesCountElement.textContent = likesCount;
// }