const PostsState = {
    currentPage: 1,
    currentFilter: 'all',
    loading: false,
    hasMore: true,
    searchQuery: '',
    posts: new Map(),

    reset() {
        this.currentPage = 1;
        this.hasMore = true;
        this.posts.clear();
    }
};

const initFloatingButton = () => {
    const createBtn = document.querySelector('.floating-create-btn');
    let lastScrollTop = 0;
    let ticking = false;

    window.addEventListener('scroll', () => {
        if (!ticking) {
            window.requestAnimationFrame(() => {
                const st = window.scrollY || document.documentElement.scrollTop;
                
                if (st < lastScrollTop || st < 100) {
                    createBtn?.classList.remove('hidden');
                } else if (st > lastScrollTop) {
                    createBtn?.classList.add('hidden');
                }
                
                lastScrollTop = st <= 0 ? 0 : st;
                ticking = false;
            });
            ticking = true;
        }
    });
};

const postTemplate = document.getElementById('postTemplate');
const postsContainer = document.getElementById('postsContainer');
const loadMoreBtn = document.getElementById('loadMoreBtn');
const loadingSpinner = document.getElementById('loadingSpinner');
const postsError = document.getElementById('postsError');


function initFilterHandlers() {
    const filterButtons = document.querySelectorAll('[data-filter]');

    filterButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();

            filterButtons.forEach(btn => btn.classList.remove('active'));

            button.classList.add('active');

            const filter = button.dataset.filter;

            if (filter !== PostsState.currentFilter) {
                PostsState.currentFilter = filter;
                postsContainer.innerHTML = '';
                PostsState.reset();
                loadPosts(filter, true);
            }
        });
    });
}


function initInfiniteScroll() {
    if (window.postsObserver) {
        window.postsObserver.disconnect();
    }

    const options = {
        root: null,
        rootMargin: '100px',
        threshold: 0.1
    };

    window.postsObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !PostsState.loading && PostsState.hasMore) {
                loadPosts(PostsState.currentFilter);
            }
        });
    }, options);

    if (loadMoreBtn) {
        window.postsObserver.observe(loadMoreBtn);
    }
}


async function loadPosts(filter = 'all', reset = false) {
    if (PostsState.loading) return;

    if (reset) {
        PostsState.reset();
        postsContainer.innerHTML = '';
    }

    if (!PostsState.hasMore) return;

    try {
        PostsState.loading = true;
        showLoading();

        const endpoint = PostsState.searchQuery
            ? `${API_ENDPOINTS.SEARCH_POSTS}?q=${encodeURIComponent(PostsState.searchQuery)}&page=${PostsState.currentPage}`
            : `${API_ENDPOINTS.FEED_LIST}?page=${PostsState.currentPage}&filter=${filter}`;

        const data = await apiCall(endpoint);

        if (!data.posts || data.posts.length === 0) {
            PostsState.hasMore = false;
            if (PostsState.posts.size === 0) {
                const emptyMessage = PostsState.searchQuery
                    ? `No posts found for "${PostsState.searchQuery}"`
                    : 'No posts to show';

                postsContainer.innerHTML = `
                    <div class="text-center py-5">
                        <i class="fas fa-${PostsState.searchQuery ? 'search' : 'inbox'} text-muted mb-3" style="font-size: 3rem;"></i>
                        <h5 class="text-muted">${emptyMessage}</h5>
                    </div>
                `;
            }
            return;
        }

        const newPosts = data.posts.filter(post => !PostsState.posts.has(post.id));
        newPosts.forEach(post => PostsState.posts.set(post.id, post));

        renderPosts(newPosts);

        PostsState.currentPage = data.current_page + 1;
        PostsState.hasMore = data.has_next;
        hideError();

    } catch (error) {
        handleLoadError(error);
    } finally {
        PostsState.loading = false;
        hideLoading();
        updateLoadMoreButton();
    }
}

function showEmptyState() {
    const emptyState = document.createElement('div');
    emptyState.className = 'text-center py-5';
    emptyState.innerHTML = `
        <i class="fas fa-inbox text-muted mb-3" style="font-size: 3rem;"></i>
        <h5 class="text-muted">No posts to show</h5>
    `;
    postsContainer.appendChild(emptyState);
}


function handleLoadError(error) {
    console.error('Load error:', error);

    const errorMessage = error.status === 429
        ? 'Too many requests. Please wait a moment.'
        : 'Error loading posts. Please try again.';

    showError(errorMessage);

    if (error.status === 401) {
        window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname);
    }
}

function renderPosts(posts) {
    const fragment = document.createDocumentFragment();

    posts.forEach(post => {
        if (!document.querySelector(`[data-post-id="${post.id}"]`)) {
            const postElement = createPostElement(post);
            fragment.appendChild(postElement);
        }
    });

    postsContainer.appendChild(fragment);
}

function createPostElement(post) {
    const element = postTemplate.content.cloneNode(true);
    const postCard = element.querySelector('.post-card');

    const oldPost = document.querySelector(`[data-post-id="${post.id}"]`);
    if (oldPost) {
        oldPost.remove();
    }

    postCard.dataset.postId = post.id;

    const avatar = postCard.querySelector('.post-avatar');
    avatar.src = post.user.avatar_url || '/static/images/default-avatar.png';
    avatar.alt = `${post.user.username}'s avatar`;

    postCard.querySelector('.post-username').textContent = post.user.username;
    postCard.querySelector('.post-date').textContent = formatDate(post.created_at);

    const courseElement = postCard.querySelector('.user-course');
    const campusElement = postCard.querySelector('.user-campus');

    if (post.user.course) {
        courseElement.textContent = post.user.course;
        courseElement.classList.remove('d-none');
    }

    if (post.user.campus) {
        campusElement.textContent = post.user.campus;
        campusElement.classList.remove('d-none');
    }

    const contentElement = postCard.querySelector('.post-content');
    contentElement.innerHTML = formatContent(post.content);

    if (post.image_url) {
        const img = document.createElement('img');
        img.src = post.image_url;
        img.className = 'img-fluid rounded mb-3';
        img.alt = 'Post image';
        contentElement.appendChild(img);
    } else if (post.video_url) {
        const video = document.createElement('video');
        video.src = post.video_url;
        video.className = 'w-100 rounded mb-3';
        video.controls = true;
        contentElement.appendChild(video);
    }

    postCard.querySelector('.post-likes-count').textContent = post.likes_count;
    postCard.querySelector('.post-comments-count').textContent = post.comments_count;
    postCard.querySelector('.post-views-count').textContent = post.views_count;

    const dropdownBtn = postCard.querySelector('.post-dropdown-btn');
    if (dropdownBtn) {
        dropdownBtn.setAttribute('data-mdb-toggle', 'dropdown');
        dropdownBtn.setAttribute('aria-expanded', 'false');

        new mdb.Dropdown(dropdownBtn);
    }

    const ownerActions = postCard.querySelector('.post-owner-actions');
    const nonOwnerActions = postCard.querySelector('.post-non-owner-actions');

    if (post.is_owner) {
        ownerActions?.classList.remove('d-none');
        nonOwnerActions?.classList.add('d-none');
    } else {
        ownerActions?.classList.add('d-none');
        nonOwnerActions?.classList.remove('d-none');
    }

    setupPostInteractions(postCard, post);

    return postCard;
}


function setupPostInteractions(postCard, post) {
    const likeBtn = postCard.querySelector('.post-like-btn');
    const commentBtn = postCard.querySelector('.post-comment-btn');
    const shareBtn = postCard.querySelector('.post-share-btn');
    const ownerActions = postCard.querySelector('.post-owner-actions');
    const nonOwnerActions = postCard.querySelector('.post-non-owner-actions');
    const deleteBtn = postCard.querySelector('.post-delete');
    const reportBtn = postCard.querySelector('.post-report');
    const engagementBtns = postCard.querySelectorAll('.view-engagement');

    if (post.is_owner) {
        ownerActions?.classList.remove('d-none');
        nonOwnerActions?.classList.add('d-none');
    } else {
        ownerActions?.classList.add('d-none');
        nonOwnerActions?.classList.remove('d-none');
    }

    if (likeBtn) {
        likeBtn.addEventListener('click', async () => {
            const likesCount = postCard.querySelector('.post-likes-count');
            const icon = likeBtn.querySelector('i');

            await handlePostInteraction(
                post.id,
                () => API.likePost(post.id),
                (response) => {
                    likesCount.textContent = response.likes_count;
                    icon.classList.toggle('far');
                    icon.classList.toggle('fas');
                    icon.classList.toggle('text-danger');
                }
            );
        });
    }

    if (deleteBtn && post.is_owner) {
        deleteBtn.addEventListener('click', async () => {
            if (confirm('Are you sure you want to delete this post?')) {
                await handlePostInteraction(
                    post.id,
                    () => API.deletePost(post.id),
                    () => {
                        postCard.remove();
                        showNotification('Post deleted successfully', 'success');
                    }
                );
            }
        });
    }

    if (reportBtn && !post.is_owner) {
        reportBtn.addEventListener('click', async () => {
            if (window.reportModal) {
                window.reportModal.setupReport(post.id, 'post');
                const reportModalElement = document.getElementById('reportModal');
                const modal = new mdb.Modal(reportModalElement);
                modal.show();
            }
        });
    }

    if (commentBtn) {
        commentBtn.addEventListener('click', () => {
            window.dispatchEvent(new CustomEvent('openComments', {
                detail: post.id
            }));
        });
    }

    if (shareBtn) {
        shareBtn.addEventListener('click', () => {
            window.dispatchEvent(new CustomEvent('sharePost', {
                detail: post
            }));
        });
    }

    engagementBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const type = btn.dataset.type;
            window.dispatchEvent(new CustomEvent('viewEngagement', {
                detail: { postId: post.id, type }
            }));
        });
    });
}

async function handlePostInteraction(postId, action, updateUI) {
    try {
        const response = await action();
        updateUI(response);
    } catch (error) {
        if (error.status === 401) {
            showNotification('Please log in to perform this action', 'error');
        } else if (error.status === 403) {
            showNotification('You do not have permission to perform this action', 'error');
        } else if (error.status === 404) {
            showNotification('This post is no longer available', 'error');
            const postElement = document.querySelector(`[data-post-id="${postId}"]`);
            postElement?.remove();
        } else {
            showNotification('Error performing action', 'error');
        }
        throw error;
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatContent(content) {
    content = content.replace(
        /(https?:\/\/[^\s]+)/g,
        '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
    );

    content = content.replace(
        /#(\w+)/g,
        '<a href="/search?q=%23$1">#$1</a>'
    );

    content = content.replace(
        /@(\w+)/g,
        '<a href="/profile/$1">@$1</a>'
    );

    return content;
}

function showLoading() {
    loadingSpinner.classList.remove('d-none');
    loadMoreBtn.classList.add('d-none');
}

function hideLoading() {
    loadingSpinner.classList.add('d-none');
    updateLoadMoreButton();
}

function showError() {
    postsError.classList.remove('d-none');
}

function hideError() {
    postsError.classList.add('d-none');
}

function updateLoadMoreButton() {
    if (PostsState.hasMore) {
        loadMoreBtn.classList.remove('d-none');
    } else {
        loadMoreBtn.classList.add('d-none');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    loadPosts();
    initInfiniteScroll();
    initFilterHandlers();
    initFloatingButton();

    window.removeEventListener('changeFilter', null);

    window.addEventListener('changeFilter', (event) => {
        const newFilter = event.detail;
        if (newFilter !== PostsState.currentFilter) {
            PostsState.currentFilter = newFilter;
            loadPosts(newFilter, true);
        }
    });

    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            if (!e.target.value.trim()) {
                PostsState.searchQuery = '';
                loadPosts(PostsState.currentFilter, true);
            }
        });
    }
});

