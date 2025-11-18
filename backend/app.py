from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import os
from pathlib import Path
from database import VideoDatabase
from youtube_manager import YouTubeManager
from video_processor import VideoProcessor
from subtitle_manager import SubtitleManager
from ai_analyzer import AIAnalyzer
from rss_manager import RSSManager
from datetime import datetime
import json

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# Configuration
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY', '')
LM_STUDIO_URL = os.environ.get('LM_STUDIO_URL', 'http://localhost:1234')
VIDEOS_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'videos')
THUMBNAILS_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'thumbnails')

# Initialize components
db = VideoDatabase('videos.db')
youtube = YouTubeManager(api_key=YOUTUBE_API_KEY if YOUTUBE_API_KEY else None)
video_processor = VideoProcessor(videos_folder=VIDEOS_FOLDER)
ai_analyzer = AIAnalyzer(lm_studio_url=LM_STUDIO_URL)
rss_manager = RSSManager()

# Ensure directories exist
os.makedirs(VIDEOS_FOLDER, exist_ok=True)
os.makedirs(THUMBNAILS_FOLDER, exist_ok=True)


@app.route('/')
def index():
    """Serve frontend"""
    return send_from_directory('../frontend', 'index.html')


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get system status"""
    return jsonify({
        'database': 'connected',
        'youtube_api': 'configured' if YOUTUBE_API_KEY else 'not configured',
        'lm_studio': 'available' if ai_analyzer.is_available() else 'not available',
        'videos_count': len(db.get_videos()),
        'boards_count': len(db.get_boards())
    })


# ========== VIDEO ENDPOINTS ==========

@app.route('/api/videos', methods=['GET'])
def get_videos():
    """Get all videos with optional filtering"""
    source = request.args.get('source', 'all')
    board_id = request.args.get('board_id', type=int)
    favorite_only = request.args.get('favorite', 'false') == 'true'

    if board_id:
        videos = db.get_videos(board_id=board_id)
    elif source != 'all':
        videos = db.get_videos(source=source)
    else:
        videos = db.get_videos()

    if favorite_only:
        videos = [v for v in videos if v.get('is_favorite')]

    return jsonify(videos)


@app.route('/api/videos/<video_id>', methods=['GET'])
def get_video(video_id):
    """Get specific video details"""
    video = db.get_video(video_id)

    if video:
        return jsonify(video)
    else:
        return jsonify({'error': 'Video not found'}), 404


@app.route('/api/videos/<video_id>', methods=['PUT'])
def update_video(video_id):
    """Update video information"""
    updates = request.json

    success = db.update_video(video_id, updates)

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Video not found'}), 404


@app.route('/api/videos/<video_id>', methods=['DELETE'])
def delete_video(video_id):
    """Delete a video"""
    success = db.delete_video(video_id)

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Video not found'}), 404


@app.route('/api/videos/<video_id>/watch', methods=['POST'])
def mark_watched(video_id):
    """Mark video as watched"""
    db.update_watch_stats(video_id)
    return jsonify({'success': True})


@app.route('/api/videos/<video_id>/favorite', methods=['POST'])
def toggle_favorite(video_id):
    """Toggle video favorite status"""
    video = db.get_video(video_id)

    if video:
        new_status = not video.get('is_favorite', False)
        db.update_video(video_id, {'is_favorite': new_status})
        return jsonify({'success': True, 'is_favorite': new_status})
    else:
        return jsonify({'error': 'Video not found'}), 404


# ========== YOUTUBE ENDPOINTS ==========

@app.route('/api/youtube/sync', methods=['POST'])
def sync_youtube():
    """Sync videos from YouTube (liked videos)"""
    if not YOUTUBE_API_KEY:
        return jsonify({'error': 'YouTube API key not configured'}), 400

    try:
        saved_videos = youtube.get_saved_videos(max_results=50)
        added_count = 0

        for item in saved_videos.get('items', []):
            video_data = youtube.format_video_data(item, source='youtube')

            # Check if already exists
            if db.get_video(video_data['video_id']):
                continue

            # Download subtitles
            subtitles = youtube.download_subtitles(video_data['video_id'])

            # AI analysis if subtitles available
            if subtitles and ai_analyzer.is_available():
                subtitle_lang = 'bg' if 'bg' in subtitles else 'en'
                if subtitle_lang in subtitles:
                    sub_data = subtitles[subtitle_lang]['data']
                    full_text = ' '.join([s['text'] for s in sub_data])

                    ai_result = ai_analyzer.analyze_video_content(
                        video_data['title'],
                        video_data.get('description', ''),
                        full_text[:3000]
                    )

                    if ai_result:
                        video_data['ai_summary'] = ai_result.get('summary')
                        video_data['ai_tags'] = ai_result.get('tags', [])

            # Add to database
            video_id = db.add_video(video_data)

            if video_id:
                added_count += 1

                # Save subtitles to database
                for lang, sub_info in subtitles.items():
                    converted_subs = SubtitleManager.convert_youtube_transcript(sub_info['data'])
                    full_text = SubtitleManager.get_full_text(converted_subs)

                    db.add_subtitle({
                        'video_id': video_data['video_id'],
                        'language': lang,
                        'content': full_text,
                        'source': 'youtube'
                    })

        return jsonify({'success': True, 'added': added_count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/youtube/import', methods=['POST'])
def import_youtube_video():
    """Import a specific YouTube video by URL"""
    data = request.json
    video_url = data.get('url')

    if not video_url:
        return jsonify({'error': 'URL required'}), 400

    try:
        # Extract video ID
        video_id = youtube.extract_video_id(video_url)

        if not video_id:
            return jsonify({'error': 'Invalid YouTube URL'}), 400

        # Check if already exists
        if db.get_video(video_id):
            return jsonify({'error': 'Video already exists'}), 409

        # Get video info
        if YOUTUBE_API_KEY:
            video_info = youtube.get_video_details(video_id)
            if video_info:
                video_data = youtube.format_video_data(video_info, source='youtube')
            else:
                return jsonify({'error': 'Video not found'}), 404
        else:
            # Use yt-dlp as fallback
            video_info = youtube.get_video_info_without_api(video_url)
            if video_info:
                video_data = video_info
                video_data['source'] = 'youtube'
            else:
                return jsonify({'error': 'Could not fetch video info'}), 500

        # Download subtitles
        subtitles = youtube.download_subtitles(video_id)

        # AI analysis
        if subtitles and ai_analyzer.is_available():
            subtitle_lang = 'bg' if 'bg' in subtitles else 'en'
            if subtitle_lang in subtitles:
                sub_data = subtitles[subtitle_lang]['data']
                full_text = ' '.join([s['text'] for s in sub_data])

                ai_result = ai_analyzer.analyze_video_content(
                    video_data['title'],
                    video_data.get('description', ''),
                    full_text[:3000]
                )

                if ai_result:
                    video_data['ai_summary'] = ai_result.get('summary')
                    video_data['ai_tags'] = ai_result.get('tags', [])

        # Add to database
        added_id = db.add_video(video_data)

        if added_id:
            # Save subtitles
            for lang, sub_info in subtitles.items():
                converted_subs = SubtitleManager.convert_youtube_transcript(sub_info['data'])
                full_text = SubtitleManager.get_full_text(converted_subs)

                db.add_subtitle({
                    'video_id': video_id,
                    'language': lang,
                    'content': full_text,
                    'source': 'youtube'
                })

            return jsonify({'success': True, 'video_id': video_id})
        else:
            return jsonify({'error': 'Failed to add video'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========== LOCAL VIDEO ENDPOINTS ==========

@app.route('/api/videos/scan-local', methods=['POST'])
def scan_local():
    """Scan for local video files"""
    try:
        videos = video_processor.scan_local_videos()
        added_count = 0

        for video in videos:
            video_info = video_processor.get_video_info(video['path'])

            # Check if already exists
            if db.get_video(video_info['video_id']):
                continue

            # Generate thumbnail
            thumb_filename = f"{video_info['video_id']}.jpg"
            thumb_path = os.path.join(THUMBNAILS_FOLDER, thumb_filename)
            thumbnail = video_processor.generate_thumbnail_ffmpeg(video['path'], thumb_path, timestamp=5)

            if thumbnail:
                video_info['thumbnail_url'] = f'/api/thumbnails/{thumb_filename}'

            # Extract subtitles if available
            subtitle_dir = os.path.join(THUMBNAILS_FOLDER, 'subtitles')
            os.makedirs(subtitle_dir, exist_ok=True)

            extracted_subs = video_processor.extract_subtitles(video['path'], subtitle_dir)

            # Add to database
            video_id = db.add_video(video_info)

            if video_id:
                added_count += 1

                # Process and save subtitles
                for sub_file in extracted_subs:
                    subtitles = SubtitleManager.parse_subtitle_file(sub_file['path'])
                    full_text = SubtitleManager.get_full_text(subtitles)

                    db.add_subtitle({
                        'video_id': video_info['video_id'],
                        'language': sub_file['language'],
                        'subtitle_path': sub_file['path'],
                        'content': full_text,
                        'source': 'embedded'
                    })

                    # AI analysis if available
                    if ai_analyzer.is_available() and full_text:
                        ai_result = ai_analyzer.analyze_video_content(
                            video_info['title'],
                            '',
                            full_text[:3000]
                        )

                        if ai_result:
                            db.update_video(video_info['video_id'], {
                                'ai_summary': ai_result.get('summary'),
                                'ai_tags': ai_result.get('tags', [])
                            })

        return jsonify({'success': True, 'added': added_count, 'total_found': len(videos)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/videos/<video_id>/stream')
def stream_video(video_id):
    """Stream local video file"""
    video = db.get_video(video_id)

    if not video or video.get('source') != 'local':
        return jsonify({'error': 'Video not found'}), 404

    file_path = video.get('file_path')

    if not file_path or not os.path.exists(file_path):
        return jsonify({'error': 'Video file not found'}), 404

    return send_file(file_path, mimetype='video/mp4')


@app.route('/api/thumbnails/<filename>')
def get_thumbnail(filename):
    """Serve thumbnail images"""
    return send_from_directory(THUMBNAILS_FOLDER, filename)


# ========== SUBTITLE ENDPOINTS ==========

@app.route('/api/videos/<video_id>/subtitles', methods=['GET'])
def get_subtitles(video_id):
    """Get subtitles for a video"""
    lang = request.args.get('lang')

    subtitles = db.get_subtitles(video_id, language=lang)

    if subtitles:
        # Parse subtitle content if needed
        for sub in subtitles:
            if sub.get('subtitle_path'):
                parsed = SubtitleManager.parse_subtitle_file(sub['subtitle_path'])
                sub['entries'] = parsed

        return jsonify(subtitles)
    else:
        return jsonify([])


# ========== SEARCH ENDPOINTS ==========

@app.route('/api/search', methods=['GET'])
def search():
    """Search videos by title, description, and subtitles"""
    query = request.args.get('q', '')
    search_subtitles = request.args.get('subtitles', 'true') == 'true'

    if not query:
        return jsonify({'results': []})

    results = db.search_videos(query, search_subtitles=search_subtitles)

    # Add subtitle matches with timestamps
    for video in results:
        if search_subtitles:
            subtitles = db.get_subtitles(video['video_id'])

            for sub in subtitles:
                if sub.get('subtitle_path'):
                    parsed_subs = SubtitleManager.parse_subtitle_file(sub['subtitle_path'])
                    matches = SubtitleManager.search_in_subtitles(parsed_subs, query)

                    if matches:
                        video['subtitle_matches'] = matches[:5]  # Top 5 matches
                        break

    return jsonify({'results': results, 'count': len(results)})


# ========== BOARD ENDPOINTS ==========

@app.route('/api/boards', methods=['GET'])
def get_boards():
    """Get all boards"""
    boards = db.get_boards()
    return jsonify(boards)


@app.route('/api/boards', methods=['POST'])
def create_board():
    """Create a new board"""
    board_data = request.json

    if not board_data.get('name'):
        return jsonify({'error': 'Board name required'}), 400

    board_id = db.create_board(board_data)

    return jsonify({'success': True, 'board_id': board_id})


@app.route('/api/boards/<int:board_id>/videos', methods=['POST'])
def add_video_to_board(board_id):
    """Add video to board"""
    data = request.json
    video_id = data.get('video_id')

    if not video_id:
        return jsonify({'error': 'video_id required'}), 400

    success = db.add_video_to_board(video_id, board_id)

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to add video to board'}), 400


@app.route('/api/boards/<int:board_id>/videos/<video_id>', methods=['DELETE'])
def remove_video_from_board(board_id, video_id):
    """Remove video from board"""
    success = db.remove_video_from_board(video_id, board_id)

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Video not in board'}), 404


# ========== AI ENDPOINTS ==========

@app.route('/api/ai/analyze/<video_id>', methods=['POST'])
def analyze_video(video_id):
    """Run AI analysis on a video"""
    if not ai_analyzer.is_available():
        return jsonify({'error': 'AI analyzer not available'}), 503

    video = db.get_video(video_id)

    if not video:
        return jsonify({'error': 'Video not found'}), 404

    # Get subtitles
    subtitles = db.get_subtitles(video_id)
    subtitle_text = ''

    if subtitles:
        subtitle_text = subtitles[0].get('content', '')

    ai_result = ai_analyzer.analyze_video_content(
        video['title'],
        video.get('description', ''),
        subtitle_text[:3000]
    )

    if ai_result:
        # Update video with AI results
        db.update_video(video_id, {
            'ai_summary': ai_result.get('summary'),
            'ai_tags': ai_result.get('tags', [])
        })

        return jsonify({'success': True, 'result': ai_result})
    else:
        return jsonify({'error': 'AI analysis failed'}), 500


@app.route('/api/ai/status', methods=['GET'])
def ai_status():
    """Check AI analyzer status"""
    return jsonify({
        'available': ai_analyzer.is_available(),
        'url': LM_STUDIO_URL
    })


# ========== PLAYLIST ENDPOINTS ==========

@app.route('/api/playlists', methods=['GET'])
def get_playlists():
    """Get all playlists"""
    playlists = db.get_playlists()
    return jsonify(playlists)


@app.route('/api/playlists', methods=['POST'])
def create_playlist():
    """Create a new playlist"""
    playlist_data = request.json

    if not playlist_data.get('name'):
        return jsonify({'error': 'Playlist name required'}), 400

    playlist_id = db.create_playlist(playlist_data)
    return jsonify({'success': True, 'playlist_id': playlist_id})


@app.route('/api/playlists/<int:playlist_id>', methods=['GET'])
def get_playlist(playlist_id):
    """Get a specific playlist with its videos"""
    playlist = db.get_playlist(playlist_id)

    if not playlist:
        return jsonify({'error': 'Playlist not found'}), 404

    videos = db.get_playlist_videos(playlist_id)
    playlist['videos'] = videos

    return jsonify(playlist)


@app.route('/api/playlists/<int:playlist_id>', methods=['PUT'])
def update_playlist(playlist_id):
    """Update playlist settings"""
    updates = request.json

    success = db.update_playlist(playlist_id, updates)

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Playlist not found'}), 404


@app.route('/api/playlists/<int:playlist_id>', methods=['DELETE'])
def delete_playlist(playlist_id):
    """Delete a playlist"""
    success = db.delete_playlist(playlist_id)

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Playlist not found'}), 404


@app.route('/api/playlists/<int:playlist_id>/videos', methods=['POST'])
def add_video_to_playlist(playlist_id):
    """Add a video to a playlist"""
    data = request.json
    video_id = data.get('video_id')
    position = data.get('position')

    if not video_id:
        return jsonify({'error': 'video_id required'}), 400

    success = db.add_video_to_playlist(playlist_id, video_id, position)

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to add video to playlist'}), 400


@app.route('/api/playlists/<int:playlist_id>/videos/<video_id>', methods=['DELETE'])
def remove_video_from_playlist(playlist_id, video_id):
    """Remove a video from a playlist"""
    success = db.remove_video_from_playlist(playlist_id, video_id)

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Video not in playlist'}), 404


@app.route('/api/playlists/<int:playlist_id>/reorder', methods=['POST'])
def reorder_playlist(playlist_id):
    """Reorder videos in a playlist"""
    video_orders = request.json.get('videos', [])

    success = db.reorder_playlist_videos(playlist_id, video_orders)

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Failed to reorder playlist'}), 500


@app.route('/api/playlists/watch-later', methods=['GET'])
def get_watch_later():
    """Get or create Watch Later playlist"""
    playlist_id = db.get_or_create_watch_later()
    playlist = db.get_playlist(playlist_id)
    videos = db.get_playlist_videos(playlist_id)
    playlist['videos'] = videos

    return jsonify(playlist)


@app.route('/api/playlists/watch-later/add', methods=['POST'])
def add_to_watch_later():
    """Add video to Watch Later"""
    data = request.json
    video_id = data.get('video_id')

    if not video_id:
        return jsonify({'error': 'video_id required'}), 400

    playlist_id = db.get_or_create_watch_later()
    success = db.add_video_to_playlist(playlist_id, video_id)

    if success:
        return jsonify({'success': True, 'playlist_id': playlist_id})
    else:
        return jsonify({'error': 'Failed to add to Watch Later'}), 400


# ========== WATCH HISTORY ENDPOINTS ==========

@app.route('/api/history/recently-watched', methods=['GET'])
def get_recently_watched():
    """Get recently watched videos"""
    limit = request.args.get('limit', 20, type=int)
    videos = db.get_recently_watched(limit=limit)

    return jsonify(videos)


@app.route('/api/history/progress/<video_id>', methods=['GET'])
def get_video_progress(video_id):
    """Get watch progress for a video"""
    progress = db.get_watch_progress(video_id)

    return jsonify({'video_id': video_id, 'progress': progress})


@app.route('/api/history/progress/<video_id>', methods=['POST'])
def save_video_progress(video_id):
    """Save watch progress for a video"""
    data = request.json
    progress = data.get('progress', 0)
    completed = data.get('completed', False)

    history_id = db.add_watch_history(video_id, progress, completed)

    return jsonify({'success': True, 'history_id': history_id})


# ========== RECOMMENDATIONS ENDPOINTS ==========

@app.route('/api/videos/<video_id>/recommendations', methods=['GET'])
def get_video_recommendations(video_id):
    """Get recommended videos based on similarity"""
    limit = request.args.get('limit', 10, type=int)

    recommendations = db.get_similar_videos(video_id, limit=limit)

    return jsonify({
        'video_id': video_id,
        'recommendations': recommendations,
        'count': len(recommendations)
    })


# ========== BOOKMARK ENDPOINTS ==========

@app.route('/api/videos/<video_id>/bookmarks', methods=['GET'])
def get_video_bookmarks(video_id):
    """Get all bookmarks for a video"""
    bookmarks = db.get_bookmarks(video_id)
    return jsonify(bookmarks)


@app.route('/api/videos/<video_id>/bookmarks', methods=['POST'])
def add_video_bookmark(video_id):
    """Add a bookmark to a video"""
    data = request.json

    # Validate required fields
    if not data.get('timestamp') and data.get('timestamp') != 0:
        return jsonify({'error': 'timestamp required'}), 400

    if not data.get('title'):
        return jsonify({'error': 'title required'}), 400

    bookmark_data = {
        'video_id': video_id,
        'timestamp': data.get('timestamp'),
        'title': data.get('title'),
        'description': data.get('description', ''),
        'color': data.get('color', '#3B82F6')
    }

    bookmark_id = db.add_bookmark(bookmark_data)

    return jsonify({'success': True, 'bookmark_id': bookmark_id})


@app.route('/api/bookmarks/<int:bookmark_id>', methods=['GET'])
def get_bookmark(bookmark_id):
    """Get a specific bookmark"""
    bookmark = db.get_bookmark(bookmark_id)

    if bookmark:
        return jsonify(bookmark)
    else:
        return jsonify({'error': 'Bookmark not found'}), 404


@app.route('/api/bookmarks/<int:bookmark_id>', methods=['PUT'])
def update_bookmark(bookmark_id):
    """Update a bookmark"""
    updates = request.json

    success = db.update_bookmark(bookmark_id, updates)

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Bookmark not found'}), 404


@app.route('/api/bookmarks/<int:bookmark_id>', methods=['DELETE'])
def delete_bookmark(bookmark_id):
    """Delete a bookmark"""
    success = db.delete_bookmark(bookmark_id)

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Bookmark not found'}), 404


# ========== RSS FEED ENDPOINTS ==========

@app.route('/api/rss/feeds', methods=['GET'])
def get_rss_feeds():
    """Get all RSS feeds"""
    feeds = db.get_rss_feeds()
    return jsonify(feeds)


@app.route('/api/rss/feeds', methods=['POST'])
def add_rss_feed():
    """Add a new RSS feed"""
    data = request.json
    feed_url = data.get('url')

    if not feed_url:
        return jsonify({'error': 'Feed URL required'}), 400

    try:
        # Parse the feed to get metadata
        feed_info = rss_manager.parse_feed(feed_url)

        # Add to database
        feed_data = {
            'url': feed_url,
            'title': feed_info.get('title', 'Unknown Feed'),
            'description': feed_info.get('description', ''),
            'auto_sync': data.get('auto_sync', True),
            'sync_interval': data.get('sync_interval', 3600)
        }

        feed_id = db.add_rss_feed(feed_data)

        if feed_id == -1:
            return jsonify({'error': 'Feed already exists'}), 409

        return jsonify({'success': True, 'feed_id': feed_id, 'feed_info': feed_info})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/rss/feeds/<int:feed_id>', methods=['GET'])
def get_rss_feed(feed_id):
    """Get a specific RSS feed"""
    feed = db.get_rss_feed(feed_id)

    if feed:
        return jsonify(feed)
    else:
        return jsonify({'error': 'Feed not found'}), 404


@app.route('/api/rss/feeds/<int:feed_id>', methods=['PUT'])
def update_rss_feed(feed_id):
    """Update RSS feed settings"""
    updates = request.json

    success = db.update_rss_feed(feed_id, updates)

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Feed not found'}), 404


@app.route('/api/rss/feeds/<int:feed_id>', methods=['DELETE'])
def delete_rss_feed(feed_id):
    """Delete an RSS feed"""
    success = db.delete_rss_feed(feed_id)

    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Feed not found'}), 404


@app.route('/api/rss/feeds/<int:feed_id>/sync', methods=['POST'])
def sync_rss_feed(feed_id):
    """Sync videos from a specific RSS feed"""
    feed = db.get_rss_feed(feed_id)

    if not feed:
        return jsonify({'error': 'Feed not found'}), 404

    try:
        # Parse the feed
        feed_info = rss_manager.parse_feed(feed['url'])

        added_count = 0
        skipped_count = 0

        # Process each entry
        for entry in feed_info.get('entries', []):
            # Check if video already exists
            if db.get_video(entry['video_id']):
                skipped_count += 1
                continue

            # Add video to database
            video_id = db.add_video(entry)

            if video_id:
                added_count += 1

                # Download subtitles for YouTube videos
                if entry.get('source') == 'youtube':
                    try:
                        subtitles = youtube.download_subtitles(entry['video_id'])

                        for lang, sub_info in subtitles.items():
                            converted_subs = SubtitleManager.convert_youtube_transcript(sub_info['data'])
                            full_text = SubtitleManager.get_full_text(converted_subs)

                            db.add_subtitle({
                                'video_id': entry['video_id'],
                                'language': lang,
                                'content': full_text,
                                'source': 'youtube'
                            })
                    except:
                        pass  # Continue even if subtitles fail

        # Update feed sync time and video count
        db.update_feed_sync_time(feed_id, added_count)

        return jsonify({
            'success': True,
            'added': added_count,
            'skipped': skipped_count,
            'total': len(feed_info.get('entries', []))
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/rss/feeds/sync-all', methods=['POST'])
def sync_all_rss_feeds():
    """Sync all RSS feeds that have auto_sync enabled"""
    feeds = db.get_rss_feeds()
    results = []

    for feed in feeds:
        if not feed.get('auto_sync'):
            continue

        try:
            feed_info = rss_manager.parse_feed(feed['url'])
            added_count = 0

            for entry in feed_info.get('entries', []):
                if db.get_video(entry['video_id']):
                    continue

                video_id = db.add_video(entry)
                if video_id:
                    added_count += 1

            db.update_feed_sync_time(feed['id'], added_count)

            results.append({
                'feed_id': feed['id'],
                'feed_title': feed['title'],
                'added': added_count,
                'success': True
            })

        except Exception as e:
            results.append({
                'feed_id': feed['id'],
                'feed_title': feed['title'],
                'error': str(e),
                'success': False
            })

    return jsonify({
        'success': True,
        'results': results,
        'total_feeds': len(feeds)
    })


# ========== VIDEO NOTES ENDPOINTS ==========

@app.route('/api/videos/<video_id>/notes', methods=['GET'])
def get_video_notes(video_id):
    """Get all notes for a video"""
    category = request.args.get('category')
    notes = db.get_notes(video_id, category)
    return jsonify({'notes': notes})


@app.route('/api/videos/<video_id>/notes', methods=['POST'])
def add_video_note(video_id):
    """Add a note to a video"""
    data = request.json

    note_data = {
        'video_id': video_id,
        'content': data.get('content'),
        'category': data.get('category', 'general'),
        'timestamp': data.get('timestamp'),
        'color': data.get('color', '#10B981')
    }

    if not note_data['content']:
        return jsonify({'error': 'Note content is required'}), 400

    note_id = db.add_note(note_data)
    note = db.get_note(note_id)

    return jsonify({
        'success': True,
        'note': note
    }), 201


@app.route('/api/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    """Get a single note"""
    note = db.get_note(note_id)

    if not note:
        return jsonify({'error': 'Note not found'}), 404

    return jsonify({'note': note})


@app.route('/api/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    """Update a note"""
    note = db.get_note(note_id)

    if not note:
        return jsonify({'error': 'Note not found'}), 404

    data = request.json
    updates = {}

    if 'content' in data:
        updates['content'] = data['content']
    if 'category' in data:
        updates['category'] = data['category']
    if 'timestamp' in data:
        updates['timestamp'] = data['timestamp']
    if 'color' in data:
        updates['color'] = data['color']

    if updates:
        db.update_note(note_id, updates)

    updated_note = db.get_note(note_id)
    return jsonify({
        'success': True,
        'note': updated_note
    })


@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete a note"""
    note = db.get_note(note_id)

    if not note:
        return jsonify({'error': 'Note not found'}), 404

    db.delete_note(note_id)
    return jsonify({'success': True})


@app.route('/api/notes/search', methods=['GET'])
def search_notes():
    """Search notes by content"""
    query = request.args.get('q', '')
    video_id = request.args.get('video_id')

    if not query:
        return jsonify({'error': 'Search query is required'}), 400

    notes = db.search_notes(query, video_id)
    return jsonify({'notes': notes})


@app.route('/api/notes/recent', methods=['GET'])
def get_recent_notes():
    """Get recent notes across all videos"""
    limit = request.args.get('limit', 100, type=int)
    notes = db.get_all_notes_for_all_videos(limit)
    return jsonify({'notes': notes})


# ========== ERROR HANDLERS ==========

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print("=" * 50)
    print("Video Gallery Server")
    print("=" * 50)
    print(f"YouTube API: {'Configured' if YOUTUBE_API_KEY else 'Not configured'}")
    print(f"LM Studio: {LM_STUDIO_URL}")
    print(f"Videos folder: {VIDEOS_FOLDER}")
    print("=" * 50)

    app.run(debug=True, host='0.0.0.0', port=5000)
