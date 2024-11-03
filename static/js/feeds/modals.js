API_ENDPOINTS.REPORT_POST = (postId) => `/api/posts/${postId}/report/`;
API_ENDPOINTS.REPORT_COMMENT = (commentId) => `/api/comments/${commentId}/report/`;

/**
 * engagement.js - Handles post engagement modal functionality
 */
class EngagementModal {
    constructor() {
        this.modal = document.getElementById('engagementModal');
        this.title = document.getElementById('engagementModalLabel');
        this.list = this.modal.querySelector('.engagement-list');
        this.loadingState = this.modal.querySelector('.engagement-loading');
        this.errorState = this.modal.querySelector('.engagement-error');
        this.loadMoreBtn = this.modal.querySelector('.load-more-engagement');

        this.currentPostId = null;
        this.currentType = null;
        this.currentPage = 1;
        this.hasNextPage = false;

        this.init();
    }

    init() {
        this.modal.querySelector('.reload-engagement').addEventListener('click', () => {
            this.loadEngagement(this.currentPostId, this.currentType);
        });
        this.loadMoreBtn.querySelector('button').addEventListener('click', () => {
            this.loadEngagement(this.currentPostId, this.currentType, this.currentPage + 1);
        });
    }

    async loadEngagement(postId, type, page = 1) {
        this.currentPostId = postId;
        this.currentType = type;
        this.currentPage = page;
        const titles = {
            likes: 'Likes',
            comments: 'Comments',
            views: 'Views'
        };
        this.title.textContent = `Post ${titles[type]}`;
        if (page === 1) {
            this.list.innerHTML = this.loadingState.outerHTML;
            this.loadMoreBtn.classList.add('d-none');
            this.errorState.classList.add('d-none');
        }

        try {
            const data = await API.getEngagement(postId, type, page);
            const items = data.data.map(item => {
                switch (type) {
                    case 'likes':
                        return this.createLikeItem(item);
                    case 'comments':
                        return this.createCommentItem(item);
                    case 'views':
                        return this.createViewItem(item);
                }
            }).join('');
            if (page === 1) {
                this.list.innerHTML = items;
            } else {
                this.list.insertAdjacentHTML('beforeend', items);
            }
            this.hasNextPage = data.has_next;
            this.loadMoreBtn.classList.toggle('d-none', !this.hasNextPage);

        } catch (error) {
            if (page === 1) {
                this.errorState.classList.remove('d-none');
                this.list.innerHTML = '';
            }
            showNotification('Failed to load engagement data', 'error');
        }
    }

    createLikeItem(user) {
        return `
            <div class="d-flex align-items-center p-2 hover-shadow rounded-3">
                <img src="${user.avatar_url}" class="rounded-circle me-2" 
                    alt="${user.username}'s avatar" width="40" height="40" 
                    style="object-fit: cover;">
                <div class="flex-grow-1">
                    <h6 class="mb-0">${user.username}</h6>
                    <small class="text-muted">${user.course}</small>
                </div>
            </div>
        `;
    }

    createCommentItem(comment) {
        return `
            <div class="p-2 hover-shadow rounded-3">
                <div class="d-flex align-items-center mb-2">
                    <img src="${comment.user.avatar_url}" class="rounded-circle me-2" 
                        alt="${comment.user.username}'s avatar" width="40" height="40"
                        style="object-fit: cover;">
                    <div>
                        <h6 class="mb-0">${comment.user.username}</h6>
                        <small class="text-muted">${comment.created_at}</small>
                    </div>
                </div>
                <p class="mb-0 ms-5 ps-2">${comment.content}</p>
            </div>
        `;
    }

    createViewItem(view) {
        return `
            <div class="d-flex align-items-center p-2 hover-shadow rounded-3">
                <img src="${view.user.avatar_url}" class="rounded-circle me-2" 
                    alt="${view.user.username}'s avatar" width="40" height="40"
                    style="object-fit: cover;">
                <div class="flex-grow-1">
                    <h6 class="mb-0">${view.user.username}</h6>
                    <small class="text-muted">${view.viewed_at}</small>
                </div>
            </div>
        `;
    }
}

/**
 * report.js - Handles content reporting modal functionality
 */
class ReportModal {
    constructor() {
        this.modal = document.getElementById('reportModal');
        this.form = document.getElementById('reportForm');
        this.contentIdInput = document.getElementById('reportContentId');
        this.contentTypeInput = document.getElementById('reportContentType');
        this.typeSelect = document.getElementById('reportType');
        this.descriptionTextarea = document.getElementById('reportDescription');
        this.submitButton = document.getElementById('submitReport');

        this.init();
    }

    init() {
        this.form.addEventListener('submit', (e) => e.preventDefault());
        this.submitButton.addEventListener('click', () => this.handleSubmit());
        this.modal.addEventListener('hidden.mdb.modal', () => {
            this.form.reset();
            this.form.classList.remove('was-validated');
        });
    }

    async handleSubmit() {
        if (!this.form.checkValidity()) {
            this.form.classList.add('was-validated');
            return;
        }

        const reportData = {
            report_type: this.typeSelect.value,
            description: this.descriptionTextarea.value
        };

        try {
            const endpoint = this.contentTypeInput.value === 'post'
                ? API_ENDPOINTS.REPORT_POST(this.contentIdInput.value)
                : API_ENDPOINTS.REPORT_COMMENT(this.contentIdInput.value);

            const response = await apiCall(endpoint, {
                method: 'POST',
                body: reportData
            });

            showNotification('Report submitted successfully', 'success'); mdb.Modal.getInstance(this.modal).hide();

        } catch (error) {
            showNotification('Failed to submit report', 'error');
        }
    }
    setupReport(contentId, contentType) {
        this.contentIdInput.value = contentId;
        this.contentTypeInput.value = contentType;
    }
}

/**
 * sharing.js - Handles post sharing modal functionality
 */
class ShareModal {
    constructor() {
        this.modal = document.getElementById('shareModal');
        this.linkInput = document.getElementById('shareLink');
        this.copyButton = document.getElementById('copyShareLink');

        this.currentPostId = null;
        this.init();
    }

    init() {
        this.copyButton.addEventListener('click', () => this.copyLink());
        const socialButtons = {
            'facebook-f': this.shareFacebook.bind(this),
            'twitter': this.shareTwitter.bind(this),
            'whatsapp': this.shareWhatsApp.bind(this),
            'telegram': this.shareTelegram.bind(this)
        };

        Object.entries(socialButtons).forEach(([platform, handler]) => {
            const button = this.modal.querySelector(`.fab.fa-${platform}`).closest('button');
            button.addEventListener('click', handler);
        });
    }

    async copyLink() {
        try {
            await navigator.clipboard.writeText(this.linkInput.value);
            this.copyButton.innerHTML = '<i class="fas fa-check me-2"></i>Copied!';
            setTimeout(() => {
                this.copyButton.innerHTML = '<i class="far fa-copy me-2"></i>Copy Link';
            }, 2000);
        } catch (err) {
            showNotification('Failed to copy link', 'error');
        }
    }

    setupShare(postId) {
        this.currentPostId = postId;
        this.linkInput.value = `${window.location.origin}/posts/${postId}/`;
    }

    shareFacebook() {
        const url = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(this.linkInput.value)}`;
        window.open(url, '_blank', 'width=600,height=400');
    }

    shareTwitter() {
        const url = `https://twitter.com/intent/tweet?url=${encodeURIComponent(this.linkInput.value)}`;
        window.open(url, '_blank', 'width=600,height=400');
    }

    shareWhatsApp() {
        const url = `https://api.whatsapp.com/send?text=${encodeURIComponent(this.linkInput.value)}`;
        window.open(url, '_blank');
    }

    shareTelegram() {
        const url = `https://t.me/share/url?url=${encodeURIComponent(this.linkInput.value)}`;
        window.open(url, '_blank');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.engagementModal = new EngagementModal();
    window.reportModal = new ReportModal();
    window.shareModal = new ShareModal();
});
