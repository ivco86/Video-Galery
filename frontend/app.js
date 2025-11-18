// Video Gallery Application
const API_BASE = '/api';

class VideoGallery {
    constructor() {
        this.videos = [];
        this.boards = [];
        this.currentFilter = 'all';
        this.currentBoard = null;
        this.currentVideo = null;
        this.selectedBoardColor = '#3B82F6';
        this.selectedBoardIcon = '📁';

        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.loadVideos();
        await this.loadBoards();
        this.updateStats();
    }

    // Event Listeners
    setupEventListeners() {
        // Search
        document.getElementById('searchBtn').addEventListener('click', () => this.handleSearch());
        document.getElementById('searchInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleSearch();
        });

        // YouTube sync and import
        document.getElementById('syncYoutubeBtn').addEventListener('click', () => this.syncYouTube());
        document.getElementById('scanLocalBtn').addEventListener('click', () => this.scanLocal());
        document.getElementById('importYoutubeBtn').addEventListener('click', () => this.openImportModal());
        document.getElementById('importSubmitBtn').addEventListener('click', () => this.importYouTubeVideo());

        // Filters
        document.querySelectorAll('.filter-item').forEach(item => {
            item.addEventListener('click', (e) => this.handleFilterChange(e.target.closest('.filter-item')));
        });

        // View toggle
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.toggleView(e.target.closest('.view-btn')));
        });

        // Sort
        document.getElementById('sortSelect').addEventListener('change', (e) => this.sortVideos(e.target.value));

        // Boards
        document.getElementById('createBoardBtn').addEventListener('click', () => this.openCreateBoardModal());
        document.getElementById('createBoardSubmitBtn').addEventListener('click', () => this.createBoard());

        // Board customization
        document.querySelectorAll('.color-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.color-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.selectedBoardColor = e.target.dataset.color;
            });
        });

        document.querySelectorAll('.icon-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.icon-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.selectedBoardIcon = e.target.dataset.icon;
            });
        });

        // Video player controls
        const analyzeBtn = document.getElementById('analyzeBtn');
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => this.analyzeCurrentVideo());
        }

        const favoriteBtn = document.getElementById('favoriteBtn');
        if (favoriteBtn) {
            favoriteBtn.addEventListener('click', () => this.toggleFavorite());
        }

        // Subtitle search
        const subtitleSearch = document.getElementById('subtitleSearch');
        if (subtitleSearch) {
            subtitleSearch.addEventListener('input', (e) => this.searchSubtitles(e.target.value));
        }
    }

    // API Calls
    async apiCall(endpoint, options = {}) {
        try {
            const response = await fetch(`${API_BASE}${endpoint}`, options);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Request failed');
            }

            return data;
        } catch (error) {
            this.showToast(error.message, 'error');
            throw error;
        }
    }

    // Load Videos
    async loadVideos(filter = 'all', boardId = null) {
        this.showLoading(true);

        try {
            let endpoint = '/videos';

            if (boardId) {
                endpoint += `?board_id=${boardId}`;
            } else if (filter === 'favorites') {
                endpoint += '?favorite=true';
            } else if (filter !== 'all') {
                endpoint += `?source=${filter}`;
            }

            this.videos = await this.apiCall(endpoint);
            this.renderVideos();
            this.updateStats();
        } catch (error) {
            console.error('Error loading videos:', error);
        } finally {
            this.showLoading(false);
        }
    }

    // Load Boards
    async loadBoards() {
        try {
            this.boards = await this.apiCall('/boards');
            this.renderBoards();
            this.updateStats();
        } catch (error) {
            console.error('Error loading boards:', error);
        }
    }

    // Render Videos
    renderVideos() {
        const grid = document.getElementById('videoGrid');
        const emptyState = document.getElementById('emptyState');

        if (this.videos.length === 0) {
            grid.style.display = 'none';
            emptyState.style.display = 'flex';
            return;
        }

        grid.style.display = 'grid';
        emptyState.style.display = 'none';
        grid.innerHTML = '';

        this.videos.forEach(video => {
            const card = this.createVideoCard(video);
            grid.appendChild(card);
        });
    }

    // Create Video Card
    createVideoCard(video) {
        const card = document.createElement('div');
        card.className = 'video-card';
        card.dataset.videoId = video.video_id;

        const thumbnail = video.thumbnail_url || '/api/thumbnails/default.jpg';
        const duration = this.formatDuration(video.duration);
        const source = video.source === 'youtube' ? '▶️ YouTube' : '💾 Local';
        const favoriteClass = video.is_favorite ? 'favorite' : '';

        card.innerHTML = `
            <div class="video-thumbnail">
                <img src="${thumbnail}" alt="${video.title}" loading="lazy">
                <span class="video-duration">${duration}</span>
                ${video.is_favorite ? '<span class="favorite-badge">⭐</span>' : ''}
            </div>
            <div class="video-info">
                <h3 class="video-title">${this.escapeHtml(video.title)}</h3>
                <p class="video-channel">${video.channel_name || 'Unknown'}</p>
                <div class="video-meta">
                    <span class="video-source">${source}</span>
                    ${video.views ? `<span class="video-views">${this.formatViews(video.views)} views</span>` : ''}
                </div>
                ${video.ai_summary ? `<p class="video-summary">${this.escapeHtml(video.ai_summary.substring(0, 100))}...</p>` : ''}
            </div>
        `;

        card.addEventListener('click', () => this.playVideo(video));

        return card;
    }

    // Render Boards
    renderBoards() {
        const boardsList = document.getElementById('boardsList');
        boardsList.innerHTML = '';

        this.boards.forEach(board => {
            const item = document.createElement('li');
            item.className = 'board-item';
            item.dataset.boardId = board.id;

            const color = board.color || '#3B82F6';
            const icon = board.icon || '📁';

            item.innerHTML = `
                <span class="board-icon" style="background: ${color}">${icon}</span>
                <span class="board-name">${this.escapeHtml(board.name)}</span>
            `;

            item.addEventListener('click', () => this.filterByBoard(board.id));

            boardsList.appendChild(item);
        });
    }

    // Play Video
    async playVideo(video) {
        this.currentVideo = video;

        const modal = document.getElementById('videoModal');
        const videoPlayer = document.getElementById('videoPlayer');
        const youtubePlayer = document.getElementById('youtubePlayer');
        const youtubeIframe = document.getElementById('youtubeIframe');

        // Update video info
        document.getElementById('videoTitle').textContent = video.title;
        document.getElementById('videoChannel').textContent = video.channel_name || '';
        document.getElementById('videoViews').textContent = video.views ? `${this.formatViews(video.views)} views` : '';
        document.getElementById('videoDuration').textContent = this.formatDuration(video.duration);
        document.getElementById('videoDescription').textContent = video.description || 'No description';

        // AI Summary
        if (video.ai_summary) {
            document.getElementById('aiSummarySection').style.display = 'block';
            document.getElementById('aiSummary').textContent = video.ai_summary;

            const tagsContainer = document.getElementById('aiTags');
            tagsContainer.innerHTML = '';

            if (video.ai_tags && Array.isArray(video.ai_tags)) {
                video.ai_tags.forEach(tag => {
                    const tagEl = document.createElement('span');
                    tagEl.className = 'tag';
                    tagEl.textContent = tag;
                    tagsContainer.appendChild(tagEl);
                });
            }
        } else {
            document.getElementById('aiSummarySection').style.display = 'none';
        }

        // Update favorite button
        const favoriteBtn = document.getElementById('favoriteBtn');
        favoriteBtn.classList.toggle('active', video.is_favorite);

        // Load video
        if (video.source === 'youtube') {
            videoPlayer.style.display = 'none';
            youtubePlayer.style.display = 'block';

            const videoId = video.video_id;
            youtubeIframe.src = `https://www.youtube.com/embed/${videoId}?autoplay=1`;
        } else {
            youtubePlayer.style.display = 'none';
            videoPlayer.style.display = 'block';

            videoPlayer.src = `/api/videos/${video.video_id}/stream`;
            videoPlayer.load();
        }

        // Load subtitles
        await this.loadSubtitles(video.video_id);

        // Mark as watched
        this.apiCall(`/videos/${video.video_id}/watch`, { method: 'POST' });

        // Show modal
        modal.style.display = 'flex';
    }

    // Load Subtitles
    async loadSubtitles(videoId) {
        try {
            const subtitles = await this.apiCall(`/videos/${videoId}/subtitles`);
            const select = document.getElementById('subtitleLangSelect');

            select.innerHTML = '<option value="">Select language</option>';

            subtitles.forEach(sub => {
                const option = document.createElement('option');
                option.value = sub.language;
                option.textContent = sub.language.toUpperCase();
                select.appendChild(option);
            });

            if (subtitles.length > 0) {
                this.currentSubtitles = subtitles;
            }
        } catch (error) {
            console.error('Error loading subtitles:', error);
        }
    }

    // Search
    async handleSearch() {
        const query = document.getElementById('searchInput').value.trim();

        if (!query) {
            await this.loadVideos();
            return;
        }

        this.showLoading(true);

        try {
            const result = await this.apiCall(`/search?q=${encodeURIComponent(query)}&subtitles=true`);
            this.videos = result.results || [];
            this.renderVideos();
        } catch (error) {
            console.error('Search error:', error);
        } finally {
            this.showLoading(false);
        }
    }

    // Sync YouTube
    async syncYouTube() {
        this.showLoading(true);
        this.showToast('Syncing YouTube videos...', 'info');

        try {
            const result = await this.apiCall('/youtube/sync', { method: 'POST' });
            this.showToast(`Added ${result.added} videos`, 'success');
            await this.loadVideos();
        } catch (error) {
            console.error('YouTube sync error:', error);
        } finally {
            this.showLoading(false);
        }
    }

    // Scan Local
    async scanLocal() {
        this.showLoading(true);
        this.showToast('Scanning local videos...', 'info');

        try {
            const result = await this.apiCall('/videos/scan-local', { method: 'POST' });
            this.showToast(`Found ${result.total_found} videos, added ${result.added} new videos`, 'success');
            await this.loadVideos();
        } catch (error) {
            console.error('Local scan error:', error);
        } finally {
            this.showLoading(false);
        }
    }

    // Import YouTube Video
    async importYouTubeVideo() {
        const url = document.getElementById('youtubeUrlInput').value.trim();

        if (!url) {
            this.showToast('Please enter a URL', 'error');
            return;
        }

        const statusDiv = document.getElementById('importStatus');
        statusDiv.textContent = 'Importing...';

        try {
            await this.apiCall('/youtube/import', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            this.showToast('Video imported successfully', 'success');
            this.closeImportModal();
            await this.loadVideos();
        } catch (error) {
            statusDiv.textContent = `Error: ${error.message}`;
        }
    }

    // Create Board
    async createBoard() {
        const name = document.getElementById('boardNameInput').value.trim();
        const description = document.getElementById('boardDescriptionInput').value.trim();

        if (!name) {
            this.showToast('Please enter a board name', 'error');
            return;
        }

        try {
            await this.apiCall('/boards', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name,
                    description,
                    color: this.selectedBoardColor,
                    icon: this.selectedBoardIcon
                })
            });

            this.showToast('Board created successfully', 'success');
            this.closeCreateBoardModal();
            await this.loadBoards();
        } catch (error) {
            console.error('Error creating board:', error);
        }
    }

    // Analyze Current Video
    async analyzeCurrentVideo() {
        if (!this.currentVideo) return;

        this.showToast('Analyzing video...', 'info');

        try {
            const result = await this.apiCall(`/ai/analyze/${this.currentVideo.video_id}`, {
                method: 'POST'
            });

            this.showToast('Analysis complete', 'success');

            // Update display
            if (result.result) {
                document.getElementById('aiSummarySection').style.display = 'block';
                document.getElementById('aiSummary').textContent = result.result.summary;

                const tagsContainer = document.getElementById('aiTags');
                tagsContainer.innerHTML = '';

                (result.result.tags || []).forEach(tag => {
                    const tagEl = document.createElement('span');
                    tagEl.className = 'tag';
                    tagEl.textContent = tag;
                    tagsContainer.appendChild(tagEl);
                });
            }
        } catch (error) {
            console.error('Analysis error:', error);
        }
    }

    // Toggle Favorite
    async toggleFavorite() {
        if (!this.currentVideo) return;

        try {
            const result = await this.apiCall(`/videos/${this.currentVideo.video_id}/favorite`, {
                method: 'POST'
            });

            this.currentVideo.is_favorite = result.is_favorite;

            const favoriteBtn = document.getElementById('favoriteBtn');
            favoriteBtn.classList.toggle('active', result.is_favorite);

            this.showToast(result.is_favorite ? 'Added to favorites' : 'Removed from favorites', 'success');
        } catch (error) {
            console.error('Favorite toggle error:', error);
        }
    }

    // Filter Change
    handleFilterChange(filterItem) {
        document.querySelectorAll('.filter-item').forEach(item => item.classList.remove('active'));
        filterItem.classList.add('active');

        this.currentFilter = filterItem.dataset.filter;
        this.currentBoard = null;

        this.loadVideos(this.currentFilter);
    }

    // Filter by Board
    filterByBoard(boardId) {
        this.currentBoard = boardId;
        this.loadVideos('all', boardId);

        // Update UI
        document.querySelectorAll('.filter-item').forEach(item => item.classList.remove('active'));
        document.querySelectorAll('.board-item').forEach(item => {
            item.classList.toggle('active', item.dataset.boardId == boardId);
        });
    }

    // Toggle View
    toggleView(btn) {
        document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const view = btn.dataset.view;
        const grid = document.getElementById('videoGrid');

        if (view === 'list') {
            grid.classList.add('list-view');
        } else {
            grid.classList.remove('list-view');
        }
    }

    // Sort Videos
    sortVideos(sortBy) {
        switch (sortBy) {
            case 'title':
                this.videos.sort((a, b) => a.title.localeCompare(b.title));
                break;
            case 'duration':
                this.videos.sort((a, b) => b.duration - a.duration);
                break;
            case 'watched':
                this.videos.sort((a, b) => (b.watch_count || 0) - (a.watch_count || 0));
                break;
            case 'recent':
            default:
                this.videos.sort((a, b) => new Date(b.added_date) - new Date(a.added_date));
        }

        this.renderVideos();
    }

    // Update Stats
    updateStats() {
        document.getElementById('totalVideos').textContent = this.videos.length;
        document.getElementById('totalBoards').textContent = this.boards.length;
    }

    // Utilities
    formatDuration(seconds) {
        if (!seconds) return '0:00';

        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;

        if (hours > 0) {
            return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
        }

        return `${minutes}:${String(secs).padStart(2, '0')}`;
    }

    formatViews(views) {
        if (views >= 1000000) {
            return `${(views / 1000000).toFixed(1)}M`;
        } else if (views >= 1000) {
            return `${(views / 1000).toFixed(1)}K`;
        }
        return views.toString();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showLoading(show) {
        const indicator = document.getElementById('loadingIndicator');
        indicator.style.display = show ? 'flex' : 'none';
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;

        container.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('show');
        }, 100);

        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // Modal Controls
    openImportModal() {
        document.getElementById('importModal').style.display = 'flex';
        document.getElementById('youtubeUrlInput').value = '';
        document.getElementById('importStatus').textContent = '';
    }

    closeImportModal() {
        document.getElementById('importModal').style.display = 'none';
    }

    openCreateBoardModal() {
        document.getElementById('createBoardModal').style.display = 'flex';
        document.getElementById('boardNameInput').value = '';
        document.getElementById('boardDescriptionInput').value = '';

        // Reset to defaults
        this.selectedBoardColor = '#3B82F6';
        this.selectedBoardIcon = '📁';

        document.querySelectorAll('.color-btn')[0].classList.add('active');
        document.querySelectorAll('.icon-btn')[0].classList.add('active');
    }

    closeCreateBoardModal() {
        document.getElementById('createBoardModal').style.display = 'none';
    }
}

// Modal close functions (global)
function closeVideoModal() {
    const modal = document.getElementById('videoModal');
    modal.style.display = 'none';

    const videoPlayer = document.getElementById('videoPlayer');
    const youtubeIframe = document.getElementById('youtubeIframe');

    videoPlayer.pause();
    youtubeIframe.src = '';
}

function closeImportModal() {
    document.getElementById('importModal').style.display = 'none';
}

function closeCreateBoardModal() {
    document.getElementById('createBoardModal').style.display = 'none';
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new VideoGallery();
});
