class CommentsManager {
    constructor() {
        // Wait for DOM to be fully loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initialize());
        } else {
            this.initialize();
        }

        // Listen for add comment event
        window.addEventListener('addComment', async (event) => {
            const { postId, content } = event.detail;
            await this.addComment(postId, content);
        });

        // Bind additional event listeners
        this.bindPostEvents();
    }

    initialize() {
        console.log('Initializing CommentsManager');
        this.template = document.getElementById('commentTemplate');

        if (!this.template) {
            console.error('Comment template not found!');
            return;
        }

        console.log('Template found:', this.template);

        this.currentPostId = null;
        this.currentPage = 1;
        this.hasMore = true;
        this.loading = false;

        // Bind event listeners
        this.bindEvents();
    }

    bindEvents() {
        console.log('Binding events');
        // Listen for comment section open requests
        window.addEventListener('openComments', async (event) => {
            console.log('openComments event received', event.detail);
            this.currentPostId = event.detail;
            await this.loadComments(true);
        });
    }

    bindPostEvents() {
        // Handle comment button clicks
        document.addEventListener('click', (e) => {
            if (e.target.closest('.post-comment-btn')) {
                const postCard = e.target.closest('.post-card');
                const postId = postCard.dataset.postId;
                const commentsSection = postCard.querySelector('.comments-section');

                // Toggle the comments section visibility
                commentsSection.classList.toggle('d-none');

                // Dispatch the 'openComments' event
                window.dispatchEvent(new CustomEvent('openComments', { detail: postId }));
            }
        });

        // Handle comment submission
        document.addEventListener('click', async (e) => {
            if (e.target.closest('.add-comment-btn')) {
                const postCard = e.target.closest('.post-card');
                const input = postCard.querySelector('.comment-input');
                const postId = postCard.dataset.postId;
                
                if (input.value.trim()) {
                    await this.addComment(postId, input.value);
                    input.value = ''; // Clear input after posting
                }
            }
        });

        // Show/hide delete button based on post ownership
        document.addEventListener('DOMNodeInserted', (e) => {
            if (e.target.classList?.contains('post-card')) {
                const post = e.target;
                if (post.dataset.isOwner === 'true') {
                    post.querySelector('.post-owner-actions')?.classList.remove('d-none');
                }
            }
        });

        // Handle post deletion
        document.addEventListener('click', async (e) => {
            if (e.target.closest('.post-delete')) {
                const postCard = e.target.closest('.post-card');
                const postId = postCard.dataset.postId;
                
                if (confirm('Are you sure you want to delete this post?')) {
                    try {
                        await API.deletePost(postId);
                        postCard.remove();
                        showNotification('Post deleted successfully', 'success');
                    } catch (error) {
                        showNotification('Error deleting post', 'error');
                    }
                }
            }
        });
    }

    async loadComments(reset = false) {
        console.log('Loading comments for post:', this.currentPostId);
        if (!this.currentPostId) {
            console.error('No post ID set');
            return;
        }

        if (reset) {
            this.currentPage = 1;
            this.hasMore = true;
            // Clear existing comments
            const container = document.querySelector(`[data-post-id="${this.currentPostId}"] .comments-container`);
            if (container) {
                console.log('Clearing comments container');
                container.innerHTML = '';
            } else {
                console.error('Comments container not found');
                return;
            }
        }

        if (!this.hasMore || this.loading) return;

        try {
            this.loading = true;
            console.log('Fetching post data...');
            const post = await API.getPost(this.currentPostId);
            console.log('Post data received:', post);

            if (!post || !post.post || !post.post.comments) {
                throw new Error('Invalid post data received');
            }

            this.renderComments(post.post.comments);
        } catch (error) {
            console.error('Error loading comments:', error);
            showNotification('Error loading comments', 'error');
        } finally {
            this.loading = false;
        }
    }

    async addComment(postId, content) {
        try {
            const response = await API.addComment(postId, content);
            const commentElement = this.createCommentElement(response.comment);
            
            // Add to container
            const container = document.querySelector(`[data-post-id="${postId}"] .comments-container`);
            container.insertBefore(commentElement, container.firstChild);
            
            // Update comment count
            const countElement = document.querySelector(`[data-post-id="${postId}"] .post-comments-count`);
            countElement.textContent = parseInt(countElement.textContent) + 1;
            
            return response.comment;
        } catch (error) {
            showNotification('Error adding comment', 'error');
            throw error;
        }
    }

    renderComments(comments) {
        console.log('Rendering comments:', comments);
        if (!Array.isArray(comments)) {
            console.error('Comments is not an array:', comments);
            return;
        }

        const container = document.querySelector(`[data-post-id="${this.currentPostId}"] .comments-container`);
        if (!container) {
            console.error('Comments container not found');
            return;
        }

        comments.forEach(comment => {
            const commentElement = this.createCommentElement(comment);
            if (commentElement) {
                container.appendChild(commentElement);
            }
        });
    }

    createCommentElement(comment) {
        const template = this.template.content.cloneNode(true);
        const commentElement = template.querySelector('.comment');

        // Set comment ID
        commentElement.dataset.commentId = comment.id;

        // Set user info
        const avatar = commentElement.querySelector('.comment-avatar');
        avatar.src = comment.user.avatar_url || '/static/images/default-avatar.png';
        avatar.alt = `${comment.user.username}'s avatar`;

        commentElement.querySelector('.comment-username').textContent = comment.user.username;
        commentElement.querySelector('.comment-content').textContent = comment.content;
        commentElement.querySelector('.comment-date').textContent = this.formatDate(comment.created_at);
        commentElement.querySelector('.comment-likes-count').textContent = comment.likes_count;

        // Setup interactions
        this.setupCommentInteractions(commentElement, comment);

        return commentElement;
    }

    setupCommentInteractions(commentElement, comment) {
        const likeBtn = commentElement.querySelector('.comment-like-btn');
        const deleteBtn = commentElement.querySelector('.comment-delete');
        const reportBtn = commentElement.querySelector('.comment-report');
        const replyBtn = commentElement.querySelector('.comment-reply-btn');

        // Like button
        likeBtn.addEventListener('click', async () => {
            try {
                const response = await API.likeComment(comment.id);
                const likesCount = commentElement.querySelector('.comment-likes-count');
                likesCount.textContent = response.likes_count;

                const icon = likeBtn.querySelector('i');
                icon.classList.toggle('far');
                icon.classList.toggle('fas');
                icon.classList.toggle('text-danger');
            } catch (error) {
                showNotification('Error liking comment', 'error');
            }
        });

        // Delete button (only for comment owner)
        if (comment.is_owner) {
            deleteBtn.addEventListener('click', async () => {
                if (confirm('Are you sure you want to delete this comment?')) {
                    try {
                        await API.deleteComment(comment.id);
                        commentElement.remove();
                        showNotification('Comment deleted successfully', 'success');

                        // Update comment count in post
                        const post = document.querySelector(`[data-post-id="${this.currentPostId}"]`);
                        const countElement = post.querySelector('.post-comments-count');
                        countElement.textContent = parseInt(countElement.textContent) - 1;
                    } catch (error) {
                        showNotification('Error deleting comment', 'error');
                    }
                }
            });
        } else {
            deleteBtn.parentElement.remove();
        }

        // Report button
        reportBtn.addEventListener('click', () => {
            window.dispatchEvent(new CustomEvent('openReportModal', {
                detail: {
                    type: 'comment',
                    id: comment.id
                }
            }));
        });

        // Reply button
        replyBtn.addEventListener('click', () => {
            const textarea = document.querySelector(`[data-post-id="${this.currentPostId}"] .comment-input`);
            if (textarea) {
                textarea.value = `@${comment.user.username} `;
                textarea.focus();
            }
        });
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;

        // Less than 1 minute
        if (diff < 60000) {
            return 'Just now';
        }

        // Less than 1 hour
        if (diff < 3600000) {
            const minutes = Math.floor(diff / 60000);
            return `${minutes}m ago`;
        }

        // Less than 1 day
        if (diff < 86400000) {
            const hours = Math.floor(diff / 3600000);
            return `${hours}h ago`;
        }

        // Less than 1 week
        if (diff < 604800000) {
            const days = Math.floor(diff / 86400000);
            return `${days}d ago`;
        }

        // Default to full date
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

}

document.addEventListener('DOMContentLoaded', () => {
    window.commentsManager = new CommentsManager();
});

