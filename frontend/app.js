// Video Gallery Application
const API_BASE = '/api';

class VideoGallery {
    constructor() {
        this.videos = [];
        this.boards = [];
        this.playlists = [];
        this.currentFilter = 'all';
        this.currentBoard = null;
        this.currentPlaylist = null;
        this.currentVideo = null;
        this.selectedBoardColor = '#3B82F6';
        this.selectedBoardIcon = '📁';
        this.selectedPlaylistColor = '#3B82F6';
        this.selectedPlaylistIcon = '▶️';

        // Playlist player state
        this.playlistPlayerActive = false;
        this.currentPlaylistVideos = [];
        this.currentPlaylistIndex = 0;
        this.playlistSettings = {
            autoPlay: true,
            shuffle: false,
            repeat: 'none' // 'none', 'all', 'one'
        };

        // Bookmark state
        this.currentBookmarks = [];
        this.selectedBookmarkColor = '#3B82F6';
        this.editingBookmark = null;

        // Player state
        this.playerLoop = false;
        this.playerIsMuted = false;
        this.playerCurrentSpeed = 1;

        // RSS Feed state
        this.rssFeeds = [];

        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.loadVideos();
        await this.loadBoards();
        await this.loadPlaylists();
        await this.loadRssFeeds();
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

        // Playlists
        document.getElementById('createPlaylistBtn').addEventListener('click', () => this.openCreatePlaylistModal());
        document.getElementById('createPlaylistSubmitBtn').addEventListener('click', () => this.createPlaylist());

        // Playlist customization
        document.querySelectorAll('.color-picker-playlist .color-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.color-picker-playlist .color-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.selectedPlaylistColor = e.target.dataset.color;
            });
        });

        document.querySelectorAll('.icon-picker-playlist .icon-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.icon-picker-playlist .icon-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.selectedPlaylistIcon = e.target.dataset.icon;
            });
        });

        // Playlist video actions
        const watchLaterBtn = document.getElementById('watchLaterBtn');
        if (watchLaterBtn) {
            watchLaterBtn.addEventListener('click', () => this.addToWatchLater());
        }

        const addToPlaylistBtn = document.getElementById('addToPlaylistBtn');
        if (addToPlaylistBtn) {
            addToPlaylistBtn.addEventListener('click', () => this.openAddToPlaylistModal());
        }

        // Playlist player controls
        const playlistPrevBtn = document.getElementById('playlistPrevBtn');
        if (playlistPrevBtn) {
            playlistPrevBtn.addEventListener('click', () => this.playlistPrevious());
        }

        const playlistNextBtn = document.getElementById('playlistNextBtn');
        if (playlistNextBtn) {
            playlistNextBtn.addEventListener('click', () => this.playlistNext());
        }

        const playlistShuffleBtn = document.getElementById('playlistShuffleBtn');
        if (playlistShuffleBtn) {
            playlistShuffleBtn.addEventListener('click', () => this.togglePlaylistShuffle());
        }

        const playlistRepeatBtn = document.getElementById('playlistRepeatBtn');
        if (playlistRepeatBtn) {
            playlistRepeatBtn.addEventListener('click', () => this.cyclePlaylistRepeat());
        }

        const playlistAutoPlayBtn = document.getElementById('playlistAutoPlayBtn');
        if (playlistAutoPlayBtn) {
            playlistAutoPlayBtn.addEventListener('click', () => this.togglePlaylistAutoPlay());
        }

        // Playlist video player events
        const playlistVideoPlayer = document.getElementById('playlistVideoPlayer');
        if (playlistVideoPlayer) {
            playlistVideoPlayer.addEventListener('ended', () => this.onPlaylistVideoEnded());
        }

        // Bookmarks
        const addBookmarkBtn = document.getElementById('addBookmarkBtn');
        if (addBookmarkBtn) {
            addBookmarkBtn.addEventListener('click', () => this.openBookmarkModal());
        }

        const saveBookmarkBtn = document.getElementById('saveBookmarkBtn');
        if (saveBookmarkBtn) {
            saveBookmarkBtn.addEventListener('click', () => this.saveBookmark());
        }

        const useCurrentTimeBtn = document.getElementById('useCurrentTimeBtn');
        if (useCurrentTimeBtn) {
            useCurrentTimeBtn.addEventListener('click', () => this.useCurrentTime());
        }

        // Bookmark color picker
        document.querySelectorAll('.color-picker-bookmark .color-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                document.querySelectorAll('.color-picker-bookmark .color-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.selectedBookmarkColor = e.target.dataset.color;
            });
        });

        // Player controls
        const playerPlayPauseBtn = document.getElementById('playerPlayPauseBtn');
        if (playerPlayPauseBtn) {
            playerPlayPauseBtn.addEventListener('click', () => this.togglePlayPause());
        }

        const playerRewind10Btn = document.getElementById('playerRewind10Btn');
        if (playerRewind10Btn) {
            playerRewind10Btn.addEventListener('click', () => this.seekVideo(-10));
        }

        const playerForward10Btn = document.getElementById('playerForward10Btn');
        if (playerForward10Btn) {
            playerForward10Btn.addEventListener('click', () => this.seekVideo(10));
        }

        const playerLoopBtn = document.getElementById('playerLoopBtn');
        if (playerLoopBtn) {
            playerLoopBtn.addEventListener('click', () => this.toggleLoop());
        }

        const playerMuteBtn = document.getElementById('playerMuteBtn');
        if (playerMuteBtn) {
            playerMuteBtn.addEventListener('click', () => this.toggleMute());
        }

        const playerVolumeSlider = document.getElementById('playerVolumeSlider');
        if (playerVolumeSlider) {
            playerVolumeSlider.addEventListener('input', (e) => this.setVolume(e.target.value));
        }

        const playerSpeedSelect = document.getElementById('playerSpeedSelect');
        if (playerSpeedSelect) {
            playerSpeedSelect.addEventListener('change', (e) => this.setPlaybackSpeed(parseFloat(e.target.value)));
        }

        const playerFullscreenBtn = document.getElementById('playerFullscreenBtn');
        if (playerFullscreenBtn) {
            playerFullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
        }

        const playerShortcutsBtn = document.getElementById('playerShortcutsBtn');
        if (playerShortcutsBtn) {
            playerShortcutsBtn.addEventListener('click', () => this.showKeyboardShortcuts());
        }

        // Progress bar interaction
        const playerProgress = document.getElementById('playerProgress');
        if (playerProgress) {
            playerProgress.addEventListener('click', (e) => this.handleProgressClick(e));
        }

        // Video player events
        const videoPlayer = document.getElementById('videoPlayer');
        if (videoPlayer) {
            videoPlayer.addEventListener('timeupdate', () => this.updateProgress());
            videoPlayer.addEventListener('loadedmetadata', () => this.onVideoLoaded());
            videoPlayer.addEventListener('ended', () => this.onVideoEnded());
        }

        // RSS Feeds
        const addRssFeedBtn = document.getElementById('addRssFeedBtn');
        if (addRssFeedBtn) {
            addRssFeedBtn.addEventListener('click', () => this.openAddRssFeedModal());
        }

        const addRssFeedSubmitBtn = document.getElementById('addRssFeedSubmitBtn');
        if (addRssFeedSubmitBtn) {
            addRssFeedSubmitBtn.addEventListener('click', () => this.addRssFeed());
        }

        const syncAllFeedsBtn = document.getElementById('syncAllFeedsBtn');
        if (syncAllFeedsBtn) {
            syncAllFeedsBtn.addEventListener('click', () => this.syncAllRssFeeds());
        }

        // Keyboard shortcuts (global)
        document.addEventListener('keydown', (e) => this.handleKeyPress(e));
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

        // Load bookmarks
        await this.loadBookmarks(video.video_id);

        // Load recommendations
        await this.loadRecommendations(video.video_id);

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

    // ========== PLAYLIST METHODS ==========

    async loadPlaylists() {
        try {
            this.playlists = await this.apiCall('/playlists');
            this.renderPlaylists();
        } catch (error) {
            console.error('Error loading playlists:', error);
        }
    }

    renderPlaylists() {
        const playlistsList = document.getElementById('playlistsList');
        playlistsList.innerHTML = '';

        this.playlists.forEach(playlist => {
            const item = document.createElement('li');
            item.className = 'playlist-item';
            item.dataset.playlistId = playlist.id;

            const color = playlist.color || '#3B82F6';
            const icon = playlist.icon || '▶️';

            item.innerHTML = `
                <span class="playlist-icon" style="background: ${color}">${icon}</span>
                <span class="playlist-name">${this.escapeHtml(playlist.name)}</span>
                <span class="playlist-count">${playlist.video_count || 0}</span>
            `;

            item.addEventListener('click', () => this.openPlaylistPlayer(playlist.id));

            playlistsList.appendChild(item);
        });
    }

    async createPlaylist() {
        const name = document.getElementById('playlistNameInput').value.trim();
        const description = document.getElementById('playlistDescriptionInput').value.trim();
        const autoPlay = document.getElementById('playlistAutoPlay').checked;
        const shuffle = document.getElementById('playlistShuffle').checked;
        const repeatMode = document.getElementById('playlistRepeatMode').value;

        if (!name) {
            this.showToast('Please enter a playlist name', 'error');
            return;
        }

        try {
            await this.apiCall('/playlists', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name,
                    description,
                    auto_play: autoPlay,
                    shuffle,
                    repeat_mode: repeatMode,
                    color: this.selectedPlaylistColor,
                    icon: this.selectedPlaylistIcon
                })
            });

            this.showToast('Playlist created successfully', 'success');
            this.closeCreatePlaylistModal();
            await this.loadPlaylists();
        } catch (error) {
            console.error('Error creating playlist:', error);
        }
    }

    openCreatePlaylistModal() {
        document.getElementById('createPlaylistModal').style.display = 'flex';
        document.getElementById('playlistNameInput').value = '';
        document.getElementById('playlistDescriptionInput').value = '';
        document.getElementById('playlistAutoPlay').checked = true;
        document.getElementById('playlistShuffle').checked = false;
        document.getElementById('playlistRepeatMode').value = 'none';

        // Reset to defaults
        this.selectedPlaylistColor = '#3B82F6';
        this.selectedPlaylistIcon = '▶️';

        document.querySelectorAll('.color-picker-playlist .color-btn')[0].classList.add('active');
        document.querySelectorAll('.icon-picker-playlist .icon-btn')[0].classList.add('active');
    }

    closeCreatePlaylistModal() {
        document.getElementById('createPlaylistModal').style.display = 'none';
    }

    async addToWatchLater() {
        if (!this.currentVideo) return;

        try {
            await this.apiCall('/playlists/watch-later/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ video_id: this.currentVideo.video_id })
            });

            this.showToast('Added to Watch Later', 'success');
        } catch (error) {
            if (error.message.includes('Failed to add')) {
                this.showToast('Video already in Watch Later', 'warning');
            } else {
                console.error('Error adding to Watch Later:', error);
            }
        }
    }

    async openAddToPlaylistModal() {
        if (!this.currentVideo) return;

        document.getElementById('addToPlaylistModal').style.display = 'flex';

        // Load playlists for selection
        const selectionList = document.getElementById('playlistsSelectionList');
        selectionList.innerHTML = '';

        this.playlists.forEach(playlist => {
            if (playlist.is_watch_later) return; // Skip Watch Later

            const item = document.createElement('div');
            item.className = 'playlist-selection-item';
            item.innerHTML = `
                <span style="background: ${playlist.color}">${playlist.icon}</span>
                <span>${this.escapeHtml(playlist.name)}</span>
                <span class="playlist-video-count">${playlist.video_count || 0} videos</span>
            `;

            item.addEventListener('click', async () => {
                await this.addVideoToPlaylist(playlist.id, this.currentVideo.video_id);
                this.closeAddToPlaylistModal();
            });

            selectionList.appendChild(item);
        });
    }

    closeAddToPlaylistModal() {
        document.getElementById('addToPlaylistModal').style.display = 'none';
    }

    async addVideoToPlaylist(playlistId, videoId) {
        try {
            await this.apiCall(`/playlists/${playlistId}/videos`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ video_id: videoId })
            });

            this.showToast('Added to playlist', 'success');
            await this.loadPlaylists(); // Refresh counts
        } catch (error) {
            console.error('Error adding video to playlist:', error);
            this.showToast('Failed to add to playlist', 'error');
        }
    }

    async openPlaylistPlayer(playlistId) {
        try {
            const playlist = await this.apiCall(`/playlists/${playlistId}`);

            if (!playlist.videos || playlist.videos.length === 0) {
                this.showToast('Playlist is empty', 'warning');
                return;
            }

            this.currentPlaylist = playlist;
            this.currentPlaylistVideos = playlist.videos;
            this.currentPlaylistIndex = 0;

            // Set playlist settings
            this.playlistSettings = {
                autoPlay: playlist.auto_play,
                shuffle: playlist.shuffle,
                repeat: playlist.repeat_mode
            };

            // Shuffle if enabled
            if (this.playlistSettings.shuffle) {
                this.shufflePlaylistVideos();
            }

            // Update UI
            document.getElementById('playlistPlayerTitle').textContent = playlist.name;
            this.updatePlaylistControls();

            // Play first video
            this.playlistPlayerActive = true;
            this.playPlaylistVideo(0);

            // Show modal
            document.getElementById('playlistPlayerModal').style.display = 'flex';
        } catch (error) {
            console.error('Error opening playlist:', error);
        }
    }

    playPlaylistVideo(index) {
        if (index < 0 || index >= this.currentPlaylistVideos.length) return;

        this.currentPlaylistIndex = index;
        const video = this.currentPlaylistVideos[index];

        const videoPlayer = document.getElementById('playlistVideoPlayer');
        const youtubePlayer = document.getElementById('playlistYoutubePlayer');
        const youtubeIframe = document.getElementById('playlistYoutubeIframe');

        // Update position indicator
        document.getElementById('playlistPosition').textContent =
            `${index + 1} / ${this.currentPlaylistVideos.length}`;

        // Load video
        if (video.source === 'youtube') {
            videoPlayer.style.display = 'none';
            youtubePlayer.style.display = 'block';
            youtubeIframe.src = `https://www.youtube.com/embed/${video.video_id}?autoplay=1`;
        } else {
            youtubePlayer.style.display = 'none';
            videoPlayer.style.display = 'block';
            videoPlayer.src = `/api/videos/${video.video_id}/stream`;
            videoPlayer.load();
            videoPlayer.play();
        }

        // Update queue
        this.renderPlaylistQueue();
    }

    renderPlaylistQueue() {
        const queueList = document.getElementById('playlistQueueList');
        queueList.innerHTML = '';

        this.currentPlaylistVideos.forEach((video, index) => {
            const item = document.createElement('div');
            item.className = 'playlist-queue-item';
            if (index === this.currentPlaylistIndex) {
                item.classList.add('active');
            }

            item.innerHTML = `
                <span class="queue-position">${index + 1}</span>
                <img src="${video.thumbnail_url}" alt="${video.title}">
                <div class="queue-item-info">
                    <div class="queue-item-title">${this.escapeHtml(video.title)}</div>
                    <div class="queue-item-duration">${this.formatDuration(video.duration)}</div>
                </div>
            `;

            item.addEventListener('click', () => this.playPlaylistVideo(index));

            queueList.appendChild(item);
        });

        // Scroll to active item
        const activeItem = queueList.querySelector('.active');
        if (activeItem) {
            activeItem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }

    playlistNext() {
        let nextIndex = this.currentPlaylistIndex + 1;

        if (nextIndex >= this.currentPlaylistVideos.length) {
            if (this.playlistSettings.repeat === 'all') {
                nextIndex = 0;
            } else {
                this.showToast('End of playlist', 'info');
                return;
            }
        }

        this.playPlaylistVideo(nextIndex);
    }

    playlistPrevious() {
        let prevIndex = this.currentPlaylistIndex - 1;

        if (prevIndex < 0) {
            if (this.playlistSettings.repeat === 'all') {
                prevIndex = this.currentPlaylistVideos.length - 1;
            } else {
                this.showToast('Start of playlist', 'info');
                return;
            }
        }

        this.playPlaylistVideo(prevIndex);
    }

    onPlaylistVideoEnded() {
        if (!this.playlistPlayerActive) return;

        if (this.playlistSettings.repeat === 'one') {
            // Replay current video
            this.playPlaylistVideo(this.currentPlaylistIndex);
        } else if (this.playlistSettings.autoPlay) {
            // Play next video
            this.playlistNext();
        }
    }

    togglePlaylistShuffle() {
        this.playlistSettings.shuffle = !this.playlistSettings.shuffle;

        const btn = document.getElementById('playlistShuffleBtn');
        btn.classList.toggle('active', this.playlistSettings.shuffle);

        if (this.playlistSettings.shuffle) {
            this.shufflePlaylistVideos();
            this.showToast('Shuffle enabled', 'info');
        } else {
            // Restore original order
            this.currentPlaylistVideos = [...this.currentPlaylist.videos];
            this.showToast('Shuffle disabled', 'info');
        }

        this.renderPlaylistQueue();
    }

    shufflePlaylistVideos() {
        const currentVideo = this.currentPlaylistVideos[this.currentPlaylistIndex];

        // Fisher-Yates shuffle
        for (let i = this.currentPlaylistVideos.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [this.currentPlaylistVideos[i], this.currentPlaylistVideos[j]] =
                [this.currentPlaylistVideos[j], this.currentPlaylistVideos[i]];
        }

        // Find new index of current video
        this.currentPlaylistIndex = this.currentPlaylistVideos.findIndex(
            v => v.video_id === currentVideo.video_id
        );
    }

    cyclePlaylistRepeat() {
        const modes = ['none', 'all', 'one'];
        const currentIndex = modes.indexOf(this.playlistSettings.repeat);
        const nextIndex = (currentIndex + 1) % modes.length;

        this.playlistSettings.repeat = modes[nextIndex];

        const btn = document.getElementById('playlistRepeatBtn');
        const icons = { 'none': '🔁', 'all': '🔁', 'one': '🔂' };

        btn.textContent = icons[this.playlistSettings.repeat];
        btn.classList.toggle('active', this.playlistSettings.repeat !== 'none');

        const labels = { 'none': 'Repeat off', 'all': 'Repeat all', 'one': 'Repeat one' };
        this.showToast(labels[this.playlistSettings.repeat], 'info');
    }

    togglePlaylistAutoPlay() {
        this.playlistSettings.autoPlay = !this.playlistSettings.autoPlay;

        const btn = document.getElementById('playlistAutoPlayBtn');
        btn.classList.toggle('active', this.playlistSettings.autoPlay);

        this.showToast(
            this.playlistSettings.autoPlay ? 'Auto-play enabled' : 'Auto-play disabled',
            'info'
        );
    }

    updatePlaylistControls() {
        document.getElementById('playlistShuffleBtn').classList.toggle('active', this.playlistSettings.shuffle);
        document.getElementById('playlistRepeatBtn').classList.toggle('active', this.playlistSettings.repeat !== 'none');
        document.getElementById('playlistAutoPlayBtn').classList.toggle('active', this.playlistSettings.autoPlay);

        const repeatBtn = document.getElementById('playlistRepeatBtn');
        const icons = { 'none': '🔁', 'all': '🔁', 'one': '🔂' };
        repeatBtn.textContent = icons[this.playlistSettings.repeat];
    }

    closePlaylistPlayerModal() {
        this.playlistPlayerActive = false;
        document.getElementById('playlistPlayerModal').style.display = 'none';

        const videoPlayer = document.getElementById('playlistVideoPlayer');
        const youtubeIframe = document.getElementById('playlistYoutubeIframe');

        videoPlayer.pause();
        youtubeIframe.src = '';
    }

    // ========== BOOKMARK METHODS ==========

    async loadBookmarks(videoId) {
        try {
            this.currentBookmarks = await this.apiCall(`/videos/${videoId}/bookmarks`);
            this.renderBookmarks();
            this.renderBookmarkTimeline();
        } catch (error) {
            console.error('Error loading bookmarks:', error);
            this.currentBookmarks = [];
        }
    }

    renderBookmarks() {
        const container = document.getElementById('bookmarksList');

        if (!this.currentBookmarks || this.currentBookmarks.length === 0) {
            container.innerHTML = '<p class="empty-message">Няма добавени bookmarks</p>';
            return;
        }

        container.innerHTML = '';

        this.currentBookmarks.forEach(bookmark => {
            const item = document.createElement('div');
            item.className = 'bookmark-item';
            item.innerHTML = `
                <div class="bookmark-marker" style="background: ${bookmark.color}"></div>
                <div class="bookmark-content">
                    <div class="bookmark-header">
                        <span class="bookmark-time">${this.formatDuration(bookmark.timestamp)}</span>
                        <span class="bookmark-title">${this.escapeHtml(bookmark.title)}</span>
                    </div>
                    ${bookmark.description ? `<p class="bookmark-description">${this.escapeHtml(bookmark.description)}</p>` : ''}
                </div>
                <div class="bookmark-actions">
                    <button class="btn-icon-small" onclick="app.jumpToBookmark(${bookmark.timestamp})" title="Премини">▶️</button>
                    <button class="btn-icon-small" onclick="app.editBookmark(${bookmark.id})" title="Редактирай">✏️</button>
                    <button class="btn-icon-small" onclick="app.deleteBookmark(${bookmark.id})" title="Изтрий">🗑️</button>
                </div>
            `;
            container.appendChild(item);
        });
    }

    renderBookmarkTimeline() {
        const timeline = document.getElementById('bookmarkTimeline');

        if (!this.currentVideo || !this.currentBookmarks || this.currentBookmarks.length === 0) {
            timeline.innerHTML = '';
            return;
        }

        const duration = this.currentVideo.duration || 1;

        timeline.innerHTML = '';

        this.currentBookmarks.forEach(bookmark => {
            const position = (bookmark.timestamp / duration) * 100;
            const marker = document.createElement('div');
            marker.className = 'timeline-marker';
            marker.style.left = `${position}%`;
            marker.style.background = bookmark.color;
            marker.title = `${bookmark.title} - ${this.formatDuration(bookmark.timestamp)}`;
            marker.onclick = () => this.jumpToBookmark(bookmark.timestamp);
            timeline.appendChild(marker);
        });
    }

    openBookmarkModal(bookmarkId = null) {
        const modal = document.getElementById('bookmarkModal');
        const title = document.getElementById('bookmarkModalTitle');
        const timeInput = document.getElementById('bookmarkTimeInput');
        const titleInput = document.getElementById('bookmarkTitleInput');
        const descInput = document.getElementById('bookmarkDescInput');

        if (bookmarkId) {
            // Edit mode
            const bookmark = this.currentBookmarks.find(b => b.id === bookmarkId);
            if (!bookmark) return;

            this.editingBookmark = bookmark;
            title.textContent = 'Редактирай Bookmark';
            timeInput.value = bookmark.timestamp;
            titleInput.value = bookmark.title;
            descInput.value = bookmark.description || '';
            this.selectedBookmarkColor = bookmark.color;

            // Set active color
            document.querySelectorAll('.color-picker-bookmark .color-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.color === bookmark.color);
            });
        } else {
            // Add mode
            this.editingBookmark = null;
            title.textContent = 'Добави Bookmark';
            timeInput.value = '';
            titleInput.value = '';
            descInput.value = '';
            this.selectedBookmarkColor = '#3B82F6';

            // Reset color picker
            document.querySelectorAll('.color-picker-bookmark .color-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.color === '#3B82F6');
            });
        }

        modal.style.display = 'flex';
    }

    useCurrentTime() {
        const videoPlayer = document.getElementById('videoPlayer');
        const timeInput = document.getElementById('bookmarkTimeInput');

        if (videoPlayer && !videoPlayer.paused) {
            timeInput.value = Math.floor(videoPlayer.currentTime);
        }
    }

    async saveBookmark() {
        const timeInput = document.getElementById('bookmarkTimeInput');
        const titleInput = document.getElementById('bookmarkTitleInput');
        const descInput = document.getElementById('bookmarkDescInput');

        const timestamp = parseInt(timeInput.value);
        const title = titleInput.value.trim();

        if (isNaN(timestamp) || timestamp < 0) {
            this.showToast('Моля въведете валидно време', 'error');
            return;
        }

        if (!title) {
            this.showToast('Моля въведете заглавие', 'error');
            return;
        }

        const bookmarkData = {
            timestamp,
            title,
            description: descInput.value.trim(),
            color: this.selectedBookmarkColor
        };

        try {
            if (this.editingBookmark) {
                // Update existing bookmark
                await this.apiCall(`/bookmarks/${this.editingBookmark.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(bookmarkData)
                });
                this.showToast('Bookmark актуализиран', 'success');
            } else {
                // Create new bookmark
                await this.apiCall(`/videos/${this.currentVideo.video_id}/bookmarks`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(bookmarkData)
                });
                this.showToast('Bookmark добавен', 'success');
            }

            await this.loadBookmarks(this.currentVideo.video_id);
            this.closeBookmarkModal();
        } catch (error) {
            console.error('Error saving bookmark:', error);
        }
    }

    async deleteBookmark(bookmarkId) {
        if (!confirm('Сигурни ли сте, че искате да изтриете този bookmark?')) {
            return;
        }

        try {
            await this.apiCall(`/bookmarks/${bookmarkId}`, { method: 'DELETE' });
            this.showToast('Bookmark изтрит', 'success');
            await this.loadBookmarks(this.currentVideo.video_id);
        } catch (error) {
            console.error('Error deleting bookmark:', error);
        }
    }

    editBookmark(bookmarkId) {
        this.openBookmarkModal(bookmarkId);
    }

    jumpToBookmark(timestamp) {
        const videoPlayer = document.getElementById('videoPlayer');
        const youtubeIframe = document.getElementById('youtubeIframe');

        if (this.currentVideo.source === 'youtube') {
            // For YouTube, we need to update the iframe URL with timestamp
            const videoId = this.currentVideo.video_id;
            youtubeIframe.src = `https://www.youtube.com/embed/${videoId}?autoplay=1&start=${timestamp}`;
        } else {
            // For local video
            videoPlayer.currentTime = timestamp;
            videoPlayer.play();
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // ========== PLAYER CONTROL METHODS ==========

    togglePlayPause() {
        const videoPlayer = document.getElementById('videoPlayer');
        if (!videoPlayer) return;

        if (videoPlayer.paused) {
            videoPlayer.play();
            document.getElementById('playerPlayPauseBtn').textContent = '⏸️';
        } else {
            videoPlayer.pause();
            document.getElementById('playerPlayPauseBtn').textContent = '▶️';
        }
    }

    seekVideo(seconds) {
        const videoPlayer = document.getElementById('videoPlayer');
        if (!videoPlayer) return;

        videoPlayer.currentTime = Math.max(0, Math.min(videoPlayer.duration, videoPlayer.currentTime + seconds));
    }

    toggleLoop() {
        const videoPlayer = document.getElementById('videoPlayer');
        if (!videoPlayer) return;

        this.playerLoop = !this.playerLoop;
        videoPlayer.loop = this.playerLoop;

        const loopBtn = document.getElementById('playerLoopBtn');
        if (loopBtn) {
            loopBtn.style.opacity = this.playerLoop ? '1' : '0.5';
            loopBtn.style.color = this.playerLoop ? 'var(--primary-color)' : '';
        }
    }

    toggleMute() {
        const videoPlayer = document.getElementById('videoPlayer');
        if (!videoPlayer) return;

        this.playerIsMuted = !this.playerIsMuted;
        videoPlayer.muted = this.playerIsMuted;

        const muteBtn = document.getElementById('playerMuteBtn');
        if (muteBtn) {
            muteBtn.textContent = this.playerIsMuted ? '🔇' : '🔊';
        }
    }

    setVolume(value) {
        const videoPlayer = document.getElementById('videoPlayer');
        if (!videoPlayer) return;

        const volume = value / 100;
        videoPlayer.volume = volume;

        if (volume === 0) {
            this.playerIsMuted = true;
            videoPlayer.muted = true;
            document.getElementById('playerMuteBtn').textContent = '🔇';
        } else {
            this.playerIsMuted = false;
            videoPlayer.muted = false;
            document.getElementById('playerMuteBtn').textContent = '🔊';
        }
    }

    setPlaybackSpeed(speed) {
        const videoPlayer = document.getElementById('videoPlayer');
        if (!videoPlayer) return;

        this.playerCurrentSpeed = speed;
        videoPlayer.playbackRate = speed;
        this.showToast(`Speed: ${speed}x`, 'info');
    }

    toggleFullscreen() {
        const container = document.getElementById('videoPlayer');
        if (!container) return;

        if (!document.fullscreenElement) {
            container.requestFullscreen().catch(err => {
                console.error('Error entering fullscreen:', err);
            });
        } else {
            document.exitFullscreen();
        }
    }

    showKeyboardShortcuts() {
        document.getElementById('shortcutsModal').style.display = 'flex';
    }

    handleProgressClick(e) {
        const videoPlayer = document.getElementById('videoPlayer');
        const progressBar = document.getElementById('playerProgress');
        if (!videoPlayer || !progressBar) return;

        const rect = progressBar.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const percentage = clickX / rect.width;
        videoPlayer.currentTime = percentage * videoPlayer.duration;
    }

    updateProgress() {
        const videoPlayer = document.getElementById('videoPlayer');
        if (!videoPlayer) return;

        const progressFilled = document.getElementById('playerProgressFilled');
        const currentTimeEl = document.getElementById('playerCurrentTime');

        if (progressFilled && videoPlayer.duration) {
            const percentage = (videoPlayer.currentTime / videoPlayer.duration) * 100;
            progressFilled.style.width = `${percentage}%`;
        }

        if (currentTimeEl) {
            currentTimeEl.textContent = this.formatDuration(Math.floor(videoPlayer.currentTime));
        }
    }

    onVideoLoaded() {
        const videoPlayer = document.getElementById('videoPlayer');
        const durationEl = document.getElementById('playerDuration');

        if (durationEl && videoPlayer) {
            durationEl.textContent = this.formatDuration(Math.floor(videoPlayer.duration));
        }

        // Show custom controls for local videos
        if (this.currentVideo && this.currentVideo.source === 'local') {
            document.getElementById('customPlayerControls').style.display = 'block';
        } else {
            document.getElementById('customPlayerControls').style.display = 'none';
        }
    }

    onVideoEnded() {
        const videoPlayer = document.getElementById('videoPlayer');
        if (!videoPlayer) return;

        // Reset play button
        document.getElementById('playerPlayPauseBtn').textContent = '▶️';

        // If not looping, reset to start
        if (!this.playerLoop) {
            videoPlayer.currentTime = 0;
        }
    }

    handleKeyPress(e) {
        // Ignore if typing in input fields
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
            return;
        }

        // Only handle shortcuts when video modal is open
        const videoModal = document.getElementById('videoModal');
        if (!videoModal || videoModal.style.display === 'none') {
            return;
        }

        const videoPlayer = document.getElementById('videoPlayer');
        if (!videoPlayer) return;

        switch (e.key.toLowerCase()) {
            case ' ':  // Space - Play/Pause
                e.preventDefault();
                this.togglePlayPause();
                break;

            case 'k':  // K - Play/Pause (YouTube style)
                e.preventDefault();
                this.togglePlayPause();
                break;

            case 'j':  // J - Rewind 10s
                e.preventDefault();
                this.seekVideo(-10);
                this.showToast('⏪ -10s', 'info');
                break;

            case 'l':  // L - Forward 10s
                e.preventDefault();
                this.seekVideo(10);
                this.showToast('⏩ +10s', 'info');
                break;

            case 'arrowleft':  // Left Arrow - Seek backward 5s
                e.preventDefault();
                this.seekVideo(-5);
                break;

            case 'arrowright':  // Right Arrow - Seek forward 5s
                e.preventDefault();
                this.seekVideo(5);
                break;

            case 'arrowup':  // Up Arrow - Volume up 10%
                e.preventDefault();
                const currentVolume = videoPlayer.volume * 100;
                const newVolumeUp = Math.min(100, currentVolume + 10);
                this.setVolume(newVolumeUp);
                document.getElementById('playerVolumeSlider').value = newVolumeUp;
                this.showToast(`Volume: ${Math.round(newVolumeUp)}%`, 'info');
                break;

            case 'arrowdown':  // Down Arrow - Volume down 10%
                e.preventDefault();
                const currentVolumeDown = videoPlayer.volume * 100;
                const newVolumeDown = Math.max(0, currentVolumeDown - 10);
                this.setVolume(newVolumeDown);
                document.getElementById('playerVolumeSlider').value = newVolumeDown;
                this.showToast(`Volume: ${Math.round(newVolumeDown)}%`, 'info');
                break;

            case 'm':  // M - Mute/Unmute
                e.preventDefault();
                this.toggleMute();
                break;

            case 'f':  // F - Fullscreen
                e.preventDefault();
                this.toggleFullscreen();
                break;

            case '<':  // < - Decrease speed
            case ',':  // , (same key as <)
                e.preventDefault();
                const speeds = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2];
                const currentIndex = speeds.indexOf(this.playerCurrentSpeed);
                if (currentIndex > 0) {
                    const newSpeed = speeds[currentIndex - 1];
                    this.setPlaybackSpeed(newSpeed);
                    document.getElementById('playerSpeedSelect').value = newSpeed;
                }
                break;

            case '>':  // > - Increase speed
            case '.':  // . (same key as >)
                e.preventDefault();
                const speedsInc = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2];
                const currentIndexInc = speedsInc.indexOf(this.playerCurrentSpeed);
                if (currentIndexInc < speedsInc.length - 1) {
                    const newSpeed = speedsInc[currentIndexInc + 1];
                    this.setPlaybackSpeed(newSpeed);
                    document.getElementById('playerSpeedSelect').value = newSpeed;
                }
                break;

            case '0':
            case '1':
            case '2':
            case '3':
            case '4':
            case '5':
            case '6':
            case '7':
            case '8':
            case '9':
                // 0-9 - Jump to percentage
                e.preventDefault();
                const percentage = parseInt(e.key) * 10;
                videoPlayer.currentTime = (percentage / 100) * videoPlayer.duration;
                this.showToast(`Jumped to ${percentage}%`, 'info');
                break;
        }
    }

    // ========== RSS FEED METHODS ==========

    async loadRssFeeds() {
        try {
            this.rssFeeds = await this.apiCall('/rss/feeds');
            this.renderRssFeeds();
        } catch (error) {
            console.error('Error loading RSS feeds:', error);
        }
    }

    renderRssFeeds() {
        const container = document.getElementById('rssFeedsList');

        if (!this.rssFeeds || this.rssFeeds.length === 0) {
            container.innerHTML = '<li class="empty-message">Няма RSS feeds</li>';
            return;
        }

        container.innerHTML = '';

        this.rssFeeds.forEach(feed => {
            const item = document.createElement('li');
            item.className = 'rss-feed-item';
            item.innerHTML = `
                <div class="rss-feed-info">
                    <span class="rss-feed-title">${this.escapeHtml(feed.title)}</span>
                    <span class="rss-feed-count">${feed.video_count || 0} videos</span>
                </div>
                <div class="rss-feed-actions">
                    <button class="btn-icon-small" onclick="app.syncRssFeed(${feed.id})" title="Sync">🔄</button>
                    <button class="btn-icon-small" onclick="app.deleteRssFeed(${feed.id})" title="Delete">🗑️</button>
                </div>
            `;
            container.appendChild(item);
        });
    }

    openAddRssFeedModal() {
        document.getElementById('rssFeedUrlInput').value = '';
        document.getElementById('rssAutoSyncInput').checked = true;
        document.getElementById('addRssFeedModal').style.display = 'flex';
    }

    async addRssFeed() {
        const url = document.getElementById('rssFeedUrlInput').value.trim();
        const autoSync = document.getElementById('rssAutoSyncInput').checked;

        if (!url) {
            this.showToast('Моля въведете RSS Feed URL', 'error');
            return;
        }

        this.showLoading(true);

        try {
            const result = await this.apiCall('/rss/feeds', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url, auto_sync: autoSync })
            });

            this.showToast(`Feed "${result.feed_info.title}" добавен успешно!`, 'success');
            await this.loadRssFeeds();
            this.closeAddRssFeedModal();

            // Ask if user wants to sync now
            if (confirm(`Искате ли да синхронизирате "${result.feed_info.title}" сега?`)) {
                await this.syncRssFeed(result.feed_id);
            }

        } catch (error) {
            console.error('Error adding RSS feed:', error);
        } finally {
            this.showLoading(false);
        }
    }

    async syncRssFeed(feedId) {
        this.showLoading(true);
        this.showToast('Синхронизирам feed...', 'info');

        try {
            const result = await this.apiCall(`/rss/feeds/${feedId}/sync`, {
                method: 'POST'
            });

            this.showToast(`Добавени ${result.added} нови видеа`, 'success');
            await this.loadVideos();
            await this.loadRssFeeds();

        } catch (error) {
            console.error('Error syncing RSS feed:', error);
        } finally {
            this.showLoading(false);
        }
    }

    async deleteRssFeed(feedId) {
        if (!confirm('Сигурни ли сте, че искате да изтриете този RSS feed?')) {
            return;
        }

        try {
            await this.apiCall(`/rss/feeds/${feedId}`, {
                method: 'DELETE'
            });

            this.showToast('Feed изтрит', 'success');
            await this.loadRssFeeds();

        } catch (error) {
            console.error('Error deleting RSS feed:', error);
        }
    }

    async syncAllRssFeeds() {
        this.showLoading(true);
        this.showToast('Синхронизирам всички feeds...', 'info');

        try {
            const result = await this.apiCall('/rss/feeds/sync-all', {
                method: 'POST'
            });

            const successful = result.results.filter(r => r.success).length;
            const totalAdded = result.results.reduce((sum, r) => sum + (r.added || 0), 0);

            this.showToast(`Синхронизирани ${successful}/${result.total_feeds} feeds. Добавени ${totalAdded} видеа.`, 'success');
            await this.loadVideos();
            await this.loadRssFeeds();

        } catch (error) {
            console.error('Error syncing all RSS feeds:', error);
        } finally {
            this.showLoading(false);
        }
    }

    closeAddRssFeedModal() {
        document.getElementById('addRssFeedModal').style.display = 'none';
    }

    // ========== RECOMMENDATIONS METHODS ==========

    async loadRecommendations(videoId) {
        try {
            const result = await this.apiCall(`/videos/${videoId}/recommendations?limit=6`);
            this.renderRecommendations(result.recommendations || []);
        } catch (error) {
            console.error('Error loading recommendations:', error);
            this.renderRecommendations([]);
        }
    }

    renderRecommendations(recommendations) {
        const container = document.getElementById('recommendationsList');

        if (!recommendations || recommendations.length === 0) {
            container.innerHTML = '<p class="empty-message">Няма намерени свързани видеа</p>';
            return;
        }

        container.innerHTML = '';

        recommendations.forEach(video => {
            const card = document.createElement('div');
            card.className = 'recommendation-card';
            card.onclick = () => {
                closeVideoModal();
                setTimeout(() => this.playVideo(video), 100);
            };

            const thumbnail = video.thumbnail_url || '/api/thumbnails/default.jpg';
            const duration = this.formatDuration(video.duration);
            const score = video.similarity_score || 0;

            // Determine reason for recommendation
            let reason = '';
            if (score >= 30) {
                reason = '📺 Същ канал';
            } else if (score >= 20) {
                reason = '🏷️ Споделени тагове';
            } else if (score >= 10) {
                reason = '🔗 Сходно съдържание';
            }

            card.innerHTML = `
                <div class="recommendation-thumbnail">
                    <img src="${thumbnail}" alt="${this.escapeHtml(video.title)}">
                    <span class="video-duration-badge">${duration}</span>
                    ${score > 0 ? `<span class="similarity-badge">${score}</span>` : ''}
                </div>
                <div class="recommendation-info">
                    <h4 class="recommendation-title">${this.escapeHtml(video.title)}</h4>
                    <p class="recommendation-channel">${this.escapeHtml(video.channel_name || 'Unknown')}</p>
                    ${reason ? `<span class="recommendation-reason">${reason}</span>` : ''}
                </div>
            `;

            container.appendChild(card);
        });
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

function closeCreatePlaylistModal() {
    document.getElementById('createPlaylistModal').style.display = 'none';
}

function closeAddToPlaylistModal() {
    document.getElementById('addToPlaylistModal').style.display = 'none';
}

function closePlaylistPlayerModal() {
    if (window.app) {
        window.app.closePlaylistPlayerModal();
    }
}

function closeBookmarkModal() {
    document.getElementById('bookmarkModal').style.display = 'none';
}

function closeShortcutsModal() {
    document.getElementById('shortcutsModal').style.display = 'none';
}

function closeAddRssFeedModal() {
    document.getElementById('addRssFeedModal').style.display = 'none';
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.app = new VideoGallery();
});
