import sqlite3
from datetime import datetime
import json
from typing import List, Dict, Optional, Any


class VideoDatabase:
    def __init__(self, db_path='videos.db'):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        """Returns a database connection"""
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Initialize database with all required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Videos table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT UNIQUE,
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                file_path TEXT,
                url TEXT,
                thumbnail_url TEXT,
                duration INTEGER,
                channel_name TEXT,
                description TEXT,
                upload_date TEXT,
                views INTEGER,
                added_date TEXT,
                last_watched TEXT,
                watch_count INTEGER DEFAULT 0,
                is_favorite BOOLEAN DEFAULT 0,
                tags TEXT,
                ai_summary TEXT,
                ai_tags TEXT
            )
        ''')

        # Subtitles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subtitles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT,
                language TEXT,
                subtitle_path TEXT,
                content TEXT,
                source TEXT,
                FOREIGN KEY (video_id) REFERENCES videos(video_id)
            )
        ''')

        # Boards/Collections table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS boards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_date TEXT,
                thumbnail_video_id TEXT,
                color TEXT,
                icon TEXT
            )
        ''')

        # Video-Board mapping
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_boards (
                video_id TEXT,
                board_id INTEGER,
                added_date TEXT,
                PRIMARY KEY (video_id, board_id),
                FOREIGN KEY (video_id) REFERENCES videos(video_id),
                FOREIGN KEY (board_id) REFERENCES boards(id)
            )
        ''')

        # YouTube subscriptions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT UNIQUE,
                channel_name TEXT,
                channel_url TEXT,
                thumbnail_url TEXT,
                last_sync TEXT,
                auto_import BOOLEAN DEFAULT 0
            )
        ''')

        # Playlists table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_date TEXT,
                updated_date TEXT,
                thumbnail_video_id TEXT,
                is_watch_later BOOLEAN DEFAULT 0,
                auto_play BOOLEAN DEFAULT 1,
                shuffle BOOLEAN DEFAULT 0,
                repeat_mode TEXT DEFAULT 'none',
                color TEXT,
                icon TEXT
            )
        ''')

        # Playlist-Video mapping with order
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlist_videos (
                playlist_id INTEGER,
                video_id TEXT,
                position INTEGER,
                added_date TEXT,
                PRIMARY KEY (playlist_id, video_id),
                FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
                FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
            )
        ''')

        # Watch history for resume playback
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watch_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT,
                watch_date TEXT,
                progress INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT 0,
                FOREIGN KEY (video_id) REFERENCES videos(video_id)
            )
        ''')

        # Bookmarks/Timestamps for videos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT,
                timestamp INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                created_date TEXT,
                color TEXT DEFAULT '#3B82F6',
                FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
            )
        ''')

        # RSS Feeds table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rss_feeds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT,
                description TEXT,
                added_date TEXT,
                last_sync TEXT,
                auto_sync BOOLEAN DEFAULT 1,
                sync_interval INTEGER DEFAULT 3600,
                video_count INTEGER DEFAULT 0
            )
        ''')

        # Video Notes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                content TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                timestamp INTEGER,
                created_date TEXT,
                updated_date TEXT,
                color TEXT DEFAULT '#10B981',
                FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
            )
        ''')

        # Watch Sessions table for detailed analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watch_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                duration_watched INTEGER DEFAULT 0,
                video_progress_start INTEGER DEFAULT 0,
                video_progress_end INTEGER DEFAULT 0,
                completed BOOLEAN DEFAULT 0,
                FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
            )
        ''')

        # Downloads table for tracking video downloads
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS downloads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id TEXT NOT NULL,
                url TEXT NOT NULL,
                title TEXT,
                status TEXT DEFAULT 'pending',
                progress INTEGER DEFAULT 0,
                file_path TEXT,
                file_size INTEGER,
                quality TEXT DEFAULT 'best',
                added_date TEXT,
                started_date TEXT,
                completed_date TEXT,
                error_message TEXT,
                FOREIGN KEY (video_id) REFERENCES videos(video_id) ON DELETE CASCADE
            )
        ''')

        conn.commit()
        conn.close()

    # Video operations
    def add_video(self, video_data: Dict[str, Any]) -> Optional[str]:
        """Add a new video to the database"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            video_data['added_date'] = datetime.now().isoformat()

            # Convert lists to JSON strings
            if 'tags' in video_data and isinstance(video_data['tags'], list):
                video_data['tags'] = json.dumps(video_data['tags'])
            if 'ai_tags' in video_data and isinstance(video_data['ai_tags'], list):
                video_data['ai_tags'] = json.dumps(video_data['ai_tags'])

            cursor.execute('''
                INSERT INTO videos (
                    video_id, title, source, file_path, url, thumbnail_url,
                    duration, channel_name, description, upload_date, views,
                    added_date, tags, ai_summary, ai_tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                video_data.get('video_id'),
                video_data.get('title'),
                video_data.get('source'),
                video_data.get('file_path'),
                video_data.get('url'),
                video_data.get('thumbnail_url'),
                video_data.get('duration'),
                video_data.get('channel_name'),
                video_data.get('description'),
                video_data.get('upload_date'),
                video_data.get('views'),
                video_data.get('added_date'),
                video_data.get('tags'),
                video_data.get('ai_summary'),
                video_data.get('ai_tags')
            ))

            conn.commit()
            return video_data.get('video_id')
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()

    def get_videos(self, source: Optional[str] = None, board_id: Optional[int] = None) -> List[Dict]:
        """Get videos with optional filtering"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if board_id:
            cursor.execute('''
                SELECT v.* FROM videos v
                JOIN video_boards vb ON v.video_id = vb.video_id
                WHERE vb.board_id = ?
                ORDER BY v.added_date DESC
            ''', (board_id,))
        elif source:
            cursor.execute('''
                SELECT * FROM videos
                WHERE source = ?
                ORDER BY added_date DESC
            ''', (source,))
        else:
            cursor.execute('SELECT * FROM videos ORDER BY added_date DESC')

        videos = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # Parse JSON fields
        for video in videos:
            if video.get('tags'):
                try:
                    video['tags'] = json.loads(video['tags'])
                except:
                    video['tags'] = []
            if video.get('ai_tags'):
                try:
                    video['ai_tags'] = json.loads(video['ai_tags'])
                except:
                    video['ai_tags'] = []

        return videos

    def get_video(self, video_id: str) -> Optional[Dict]:
        """Get a single video by ID"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM videos WHERE video_id = ?', (video_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            video = dict(row)
            if video.get('tags'):
                try:
                    video['tags'] = json.loads(video['tags'])
                except:
                    video['tags'] = []
            if video.get('ai_tags'):
                try:
                    video['ai_tags'] = json.loads(video['ai_tags'])
                except:
                    video['ai_tags'] = []
            return video
        return None

    def update_video(self, video_id: str, updates: Dict[str, Any]) -> bool:
        """Update video information"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Convert lists to JSON
        if 'tags' in updates and isinstance(updates['tags'], list):
            updates['tags'] = json.dumps(updates['tags'])
        if 'ai_tags' in updates and isinstance(updates['ai_tags'], list):
            updates['ai_tags'] = json.dumps(updates['ai_tags'])

        set_clause = ', '.join([f'{key} = ?' for key in updates.keys()])
        values = list(updates.values()) + [video_id]

        cursor.execute(f'UPDATE videos SET {set_clause} WHERE video_id = ?', values)
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        return affected > 0

    def delete_video(self, video_id: str) -> bool:
        """Delete a video"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM videos WHERE video_id = ?', (video_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        return affected > 0

    def update_watch_stats(self, video_id: str):
        """Update video watch statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE videos
            SET watch_count = watch_count + 1,
                last_watched = ?
            WHERE video_id = ?
        ''', (datetime.now().isoformat(), video_id))

        conn.commit()
        conn.close()

    # Subtitle operations
    def add_subtitle(self, subtitle_data: Dict[str, Any]) -> Optional[int]:
        """Add subtitle for a video"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO subtitles (video_id, language, subtitle_path, content, source)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            subtitle_data.get('video_id'),
            subtitle_data.get('language'),
            subtitle_data.get('subtitle_path'),
            subtitle_data.get('content'),
            subtitle_data.get('source')
        ))

        conn.commit()
        subtitle_id = cursor.lastrowid
        conn.close()

        return subtitle_id

    def get_subtitles(self, video_id: str, language: Optional[str] = None) -> List[Dict]:
        """Get subtitles for a video"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if language:
            cursor.execute('''
                SELECT * FROM subtitles
                WHERE video_id = ? AND language = ?
            ''', (video_id, language))
        else:
            cursor.execute('''
                SELECT * FROM subtitles
                WHERE video_id = ?
            ''', (video_id,))

        subtitles = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return subtitles

    # Board operations
    def create_board(self, board_data: Dict[str, Any]) -> int:
        """Create a new board"""
        conn = self.get_connection()
        cursor = conn.cursor()

        board_data['created_date'] = datetime.now().isoformat()

        cursor.execute('''
            INSERT INTO boards (name, description, created_date, color, icon)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            board_data.get('name'),
            board_data.get('description'),
            board_data.get('created_date'),
            board_data.get('color', '#3B82F6'),
            board_data.get('icon', '📁')
        ))

        conn.commit()
        board_id = cursor.lastrowid
        conn.close()

        return board_id

    def get_boards(self) -> List[Dict]:
        """Get all boards"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM boards ORDER BY created_date DESC')
        boards = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return boards

    def add_video_to_board(self, video_id: str, board_id: int) -> bool:
        """Add a video to a board"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO video_boards (video_id, board_id, added_date)
                VALUES (?, ?, ?)
            ''', (video_id, board_id, datetime.now().isoformat()))

            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def remove_video_from_board(self, video_id: str, board_id: int) -> bool:
        """Remove a video from a board"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM video_boards
            WHERE video_id = ? AND board_id = ?
        ''', (video_id, board_id))

        conn.commit()
        affected = cursor.rowcount
        conn.close()

        return affected > 0

    # Search operations
    def search_videos(self, query: str, search_subtitles: bool = True) -> List[Dict]:
        """Search videos by title, description, and optionally subtitles"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        search_term = f'%{query}%'

        if search_subtitles:
            cursor.execute('''
                SELECT DISTINCT v.*, s.content as subtitle_match
                FROM videos v
                LEFT JOIN subtitles s ON v.video_id = s.video_id
                WHERE v.title LIKE ?
                   OR v.description LIKE ?
                   OR v.tags LIKE ?
                   OR s.content LIKE ?
                ORDER BY v.added_date DESC
            ''', (search_term, search_term, search_term, search_term))
        else:
            cursor.execute('''
                SELECT * FROM videos
                WHERE title LIKE ?
                   OR description LIKE ?
                   OR tags LIKE ?
                ORDER BY added_date DESC
            ''', (search_term, search_term, search_term))

        videos = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return videos

    # Subscription operations
    def add_subscription(self, subscription_data: Dict[str, Any]) -> int:
        """Add a YouTube channel subscription"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO subscriptions (
                    channel_id, channel_name, channel_url,
                    thumbnail_url, last_sync, auto_import
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                subscription_data.get('channel_id'),
                subscription_data.get('channel_name'),
                subscription_data.get('channel_url'),
                subscription_data.get('thumbnail_url'),
                datetime.now().isoformat(),
                subscription_data.get('auto_import', False)
            ))

            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return -1
        finally:
            conn.close()

    def get_subscriptions(self) -> List[Dict]:
        """Get all subscriptions"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM subscriptions ORDER BY channel_name')
        subscriptions = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return subscriptions

    # Playlist operations
    def create_playlist(self, playlist_data: Dict[str, Any]) -> int:
        """Create a new playlist"""
        conn = self.get_connection()
        cursor = conn.cursor()

        now = datetime.now().isoformat()
        playlist_data['created_date'] = now
        playlist_data['updated_date'] = now

        cursor.execute('''
            INSERT INTO playlists (
                name, description, created_date, updated_date,
                is_watch_later, auto_play, shuffle, repeat_mode, color, icon
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            playlist_data.get('name'),
            playlist_data.get('description'),
            playlist_data.get('created_date'),
            playlist_data.get('updated_date'),
            playlist_data.get('is_watch_later', False),
            playlist_data.get('auto_play', True),
            playlist_data.get('shuffle', False),
            playlist_data.get('repeat_mode', 'none'),
            playlist_data.get('color', '#3B82F6'),
            playlist_data.get('icon', '▶️')
        ))

        conn.commit()
        playlist_id = cursor.lastrowid
        conn.close()

        return playlist_id

    def get_playlists(self) -> List[Dict]:
        """Get all playlists with video count"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT p.*, COUNT(pv.video_id) as video_count
            FROM playlists p
            LEFT JOIN playlist_videos pv ON p.id = pv.playlist_id
            GROUP BY p.id
            ORDER BY p.created_date DESC
        ''')

        playlists = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return playlists

    def get_playlist(self, playlist_id: int) -> Optional[Dict]:
        """Get a single playlist"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM playlists WHERE id = ?', (playlist_id,))
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def update_playlist(self, playlist_id: int, updates: Dict[str, Any]) -> bool:
        """Update playlist information"""
        conn = self.get_connection()
        cursor = conn.cursor()

        updates['updated_date'] = datetime.now().isoformat()

        set_clause = ', '.join([f'{key} = ?' for key in updates.keys()])
        values = list(updates.values()) + [playlist_id]

        cursor.execute(f'UPDATE playlists SET {set_clause} WHERE id = ?', values)
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        return affected > 0

    def delete_playlist(self, playlist_id: int) -> bool:
        """Delete a playlist"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM playlists WHERE id = ?', (playlist_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        return affected > 0

    def add_video_to_playlist(self, playlist_id: int, video_id: str, position: Optional[int] = None) -> bool:
        """Add a video to a playlist"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Get current max position if not specified
        if position is None:
            cursor.execute('''
                SELECT MAX(position) as max_pos FROM playlist_videos
                WHERE playlist_id = ?
            ''', (playlist_id,))
            result = cursor.fetchone()
            position = (result[0] or 0) + 1

        try:
            cursor.execute('''
                INSERT INTO playlist_videos (playlist_id, video_id, position, added_date)
                VALUES (?, ?, ?, ?)
            ''', (playlist_id, video_id, position, datetime.now().isoformat()))

            # Update playlist updated_date
            cursor.execute('''
                UPDATE playlists SET updated_date = ? WHERE id = ?
            ''', (datetime.now().isoformat(), playlist_id))

            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def remove_video_from_playlist(self, playlist_id: int, video_id: str) -> bool:
        """Remove a video from a playlist"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM playlist_videos
            WHERE playlist_id = ? AND video_id = ?
        ''', (playlist_id, video_id))

        # Update playlist updated_date
        cursor.execute('''
            UPDATE playlists SET updated_date = ? WHERE id = ?
        ''', (datetime.now().isoformat(), playlist_id))

        conn.commit()
        affected = cursor.rowcount
        conn.close()

        return affected > 0

    def get_playlist_videos(self, playlist_id: int) -> List[Dict]:
        """Get all videos in a playlist in order"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT v.*, pv.position, pv.added_date as added_to_playlist
            FROM videos v
            JOIN playlist_videos pv ON v.video_id = pv.video_id
            WHERE pv.playlist_id = ?
            ORDER BY pv.position ASC
        ''', (playlist_id,))

        videos = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # Parse JSON fields
        for video in videos:
            if video.get('tags'):
                try:
                    video['tags'] = json.loads(video['tags'])
                except:
                    video['tags'] = []
            if video.get('ai_tags'):
                try:
                    video['ai_tags'] = json.loads(video['ai_tags'])
                except:
                    video['ai_tags'] = []

        return videos

    def reorder_playlist_videos(self, playlist_id: int, video_orders: List[Dict[str, Any]]) -> bool:
        """Reorder videos in a playlist"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            for item in video_orders:
                cursor.execute('''
                    UPDATE playlist_videos
                    SET position = ?
                    WHERE playlist_id = ? AND video_id = ?
                ''', (item['position'], playlist_id, item['video_id']))

            # Update playlist updated_date
            cursor.execute('''
                UPDATE playlists SET updated_date = ? WHERE id = ?
            ''', (datetime.now().isoformat(), playlist_id))

            conn.commit()
            return True
        except:
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_or_create_watch_later(self) -> int:
        """Get or create the Watch Later playlist"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check if Watch Later exists
        cursor.execute('SELECT id FROM playlists WHERE is_watch_later = 1')
        result = cursor.fetchone()

        if result:
            playlist_id = result['id']
        else:
            # Create Watch Later playlist
            now = datetime.now().isoformat()
            cursor.execute('''
                INSERT INTO playlists (
                    name, description, created_date, updated_date,
                    is_watch_later, auto_play, color, icon
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                'Watch Later',
                'Videos to watch later',
                now,
                now,
                True,
                True,
                '#F59E0B',
                '🕐'
            ))
            conn.commit()
            playlist_id = cursor.lastrowid

        conn.close()
        return playlist_id

    # Watch history operations
    def add_watch_history(self, video_id: str, progress: int = 0, completed: bool = False) -> int:
        """Add or update watch history"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO watch_history (video_id, watch_date, progress, completed)
            VALUES (?, ?, ?, ?)
        ''', (video_id, datetime.now().isoformat(), progress, completed))

        conn.commit()
        history_id = cursor.lastrowid
        conn.close()

        return history_id

    def get_watch_progress(self, video_id: str) -> Optional[int]:
        """Get last watch progress for a video"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT progress FROM watch_history
            WHERE video_id = ?
            ORDER BY watch_date DESC
            LIMIT 1
        ''', (video_id,))

        result = cursor.fetchone()
        conn.close()

        return result[0] if result else None

    def get_recently_watched(self, limit: int = 20) -> List[Dict]:
        """Get recently watched videos"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT v.*, wh.watch_date, wh.progress, wh.completed
            FROM videos v
            JOIN watch_history wh ON v.video_id = wh.video_id
            ORDER BY wh.watch_date DESC
            LIMIT ?
        ''', (limit,))

        videos = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return videos

    # Bookmark operations
    def add_bookmark(self, bookmark_data: Dict[str, Any]) -> int:
        """Add a bookmark/timestamp to a video"""
        conn = self.get_connection()
        cursor = conn.cursor()

        bookmark_data['created_date'] = datetime.now().isoformat()

        cursor.execute('''
            INSERT INTO bookmarks (
                video_id, timestamp, title, description, created_date, color
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            bookmark_data.get('video_id'),
            bookmark_data.get('timestamp'),
            bookmark_data.get('title'),
            bookmark_data.get('description'),
            bookmark_data.get('created_date'),
            bookmark_data.get('color', '#3B82F6')
        ))

        conn.commit()
        bookmark_id = cursor.lastrowid
        conn.close()

        return bookmark_id

    def get_bookmarks(self, video_id: str) -> List[Dict]:
        """Get all bookmarks for a video ordered by timestamp"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM bookmarks
            WHERE video_id = ?
            ORDER BY timestamp ASC
        ''', (video_id,))

        bookmarks = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return bookmarks

    def get_bookmark(self, bookmark_id: int) -> Optional[Dict]:
        """Get a single bookmark by ID"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM bookmarks WHERE id = ?', (bookmark_id,))
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def update_bookmark(self, bookmark_id: int, updates: Dict[str, Any]) -> bool:
        """Update bookmark information"""
        conn = self.get_connection()
        cursor = conn.cursor()

        set_clause = ', '.join([f'{key} = ?' for key in updates.keys()])
        values = list(updates.values()) + [bookmark_id]

        cursor.execute(f'UPDATE bookmarks SET {set_clause} WHERE id = ?', values)
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        return affected > 0

    def delete_bookmark(self, bookmark_id: int) -> bool:
        """Delete a bookmark"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM bookmarks WHERE id = ?', (bookmark_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        return affected > 0

    # Recommendation operations
    def get_similar_videos(self, video_id: str, limit: int = 10) -> List[Dict]:
        """Get similar videos based on tags, channel, and content analysis"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get the source video
        cursor.execute('SELECT * FROM videos WHERE video_id = ?', (video_id,))
        source_video = cursor.fetchone()

        if not source_video:
            conn.close()
            return []

        source_video = dict(source_video)

        # Parse source video tags
        source_tags = []
        source_ai_tags = []

        if source_video.get('tags'):
            try:
                source_tags = json.loads(source_video['tags']) if isinstance(source_video['tags'], str) else source_video['tags']
            except:
                source_tags = []

        if source_video.get('ai_tags'):
            try:
                source_ai_tags = json.loads(source_video['ai_tags']) if isinstance(source_video['ai_tags'], str) else source_video['ai_tags']
            except:
                source_ai_tags = []

        # Get all other videos
        cursor.execute('SELECT * FROM videos WHERE video_id != ? ORDER BY added_date DESC', (video_id,))
        all_videos = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # Calculate similarity scores
        scored_videos = []

        for video in all_videos:
            score = 0

            # Parse video tags
            video_tags = []
            video_ai_tags = []

            if video.get('tags'):
                try:
                    video_tags = json.loads(video['tags']) if isinstance(video['tags'], str) else video['tags']
                except:
                    video_tags = []

            if video.get('ai_tags'):
                try:
                    video_ai_tags = json.loads(video['ai_tags']) if isinstance(video['ai_tags'], str) else video['ai_tags']
                except:
                    video_ai_tags = []

            # Same channel = +30 points
            if source_video.get('channel_name') and video.get('channel_name'):
                if source_video['channel_name'].lower() == video['channel_name'].lower():
                    score += 30

            # Shared regular tags = +10 points each
            if source_tags and video_tags:
                common_tags = set([t.lower() for t in source_tags]) & set([t.lower() for t in video_tags])
                score += len(common_tags) * 10

            # Shared AI tags = +15 points each (weighted more heavily)
            if source_ai_tags and video_ai_tags:
                common_ai_tags = set([t.lower() for t in source_ai_tags]) & set([t.lower() for t in video_ai_tags])
                score += len(common_ai_tags) * 15

            # Title similarity (simple word overlap) = +5 points per common word
            if source_video.get('title') and video.get('title'):
                source_words = set(source_video['title'].lower().split())
                video_words = set(video['title'].lower().split())
                common_words = source_words & video_words
                # Exclude common words like 'the', 'a', 'and', etc.
                stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'be', 'been', 'being'}
                common_words = common_words - stop_words
                score += len(common_words) * 5

            # Same source = +10 points
            if source_video.get('source') == video.get('source'):
                score += 10

            # Boost for favorites
            if video.get('is_favorite'):
                score += 5

            # Boost for recently watched
            if video.get('watch_count', 0) > 0:
                score += min(video['watch_count'] * 2, 10)

            # Only include videos with score > 0
            if score > 0:
                video['similarity_score'] = score
                scored_videos.append(video)

        # Sort by score descending
        scored_videos.sort(key=lambda x: x['similarity_score'], reverse=True)

        # Return top N videos
        return scored_videos[:limit]

    # RSS Feed operations
    def add_rss_feed(self, feed_data: Dict[str, Any]) -> int:
        """Add a new RSS feed"""
        conn = self.get_connection()
        cursor = conn.cursor()

        feed_data['added_date'] = datetime.now().isoformat()

        try:
            cursor.execute('''
                INSERT INTO rss_feeds (
                    url, title, description, added_date, auto_sync, sync_interval
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                feed_data.get('url'),
                feed_data.get('title'),
                feed_data.get('description'),
                feed_data.get('added_date'),
                feed_data.get('auto_sync', True),
                feed_data.get('sync_interval', 3600)
            ))

            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return -1  # Feed already exists
        finally:
            conn.close()

    def get_rss_feeds(self) -> List[Dict]:
        """Get all RSS feeds"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM rss_feeds ORDER BY added_date DESC')
        feeds = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return feeds

    def get_rss_feed(self, feed_id: int) -> Optional[Dict]:
        """Get a single RSS feed"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM rss_feeds WHERE id = ?', (feed_id,))
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def update_rss_feed(self, feed_id: int, updates: Dict[str, Any]) -> bool:
        """Update RSS feed information"""
        conn = self.get_connection()
        cursor = conn.cursor()

        set_clause = ', '.join([f'{key} = ?' for key in updates.keys()])
        values = list(updates.values()) + [feed_id]

        cursor.execute(f'UPDATE rss_feeds SET {set_clause} WHERE id = ?', values)
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        return affected > 0

    def delete_rss_feed(self, feed_id: int) -> bool:
        """Delete an RSS feed"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM rss_feeds WHERE id = ?', (feed_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        return affected > 0

    def update_feed_sync_time(self, feed_id: int, video_count: int = 0):
        """Update feed's last sync time and video count"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE rss_feeds
            SET last_sync = ?, video_count = ?
            WHERE id = ?
        ''', (datetime.now().isoformat(), video_count, feed_id))

        conn.commit()
        conn.close()

    # Video Notes operations
    def add_note(self, note_data: Dict[str, Any]) -> int:
        """Add a note to a video"""
        conn = self.get_connection()
        cursor = conn.cursor()

        now = datetime.now().isoformat()
        note_data['created_date'] = now
        note_data['updated_date'] = now

        cursor.execute('''
            INSERT INTO video_notes (
                video_id, content, category, timestamp, created_date, updated_date, color
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            note_data.get('video_id'),
            note_data.get('content'),
            note_data.get('category', 'general'),
            note_data.get('timestamp'),
            note_data.get('created_date'),
            note_data.get('updated_date'),
            note_data.get('color', '#10B981')
        ))

        conn.commit()
        note_id = cursor.lastrowid
        conn.close()

        return note_id

    def get_notes(self, video_id: str, category: Optional[str] = None) -> List[Dict]:
        """Get all notes for a video, optionally filtered by category"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if category:
            cursor.execute('''
                SELECT * FROM video_notes
                WHERE video_id = ? AND category = ?
                ORDER BY timestamp ASC, created_date ASC
            ''', (video_id, category))
        else:
            cursor.execute('''
                SELECT * FROM video_notes
                WHERE video_id = ?
                ORDER BY timestamp ASC, created_date ASC
            ''', (video_id,))

        notes = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return notes

    def get_note(self, note_id: int) -> Optional[Dict]:
        """Get a single note by ID"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM video_notes WHERE id = ?', (note_id,))
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def update_note(self, note_id: int, updates: Dict[str, Any]) -> bool:
        """Update note information"""
        conn = self.get_connection()
        cursor = conn.cursor()

        updates['updated_date'] = datetime.now().isoformat()

        set_clause = ', '.join([f'{key} = ?' for key in updates.keys()])
        values = list(updates.values()) + [note_id]

        cursor.execute(f'UPDATE video_notes SET {set_clause} WHERE id = ?', values)
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        return affected > 0

    def delete_note(self, note_id: int) -> bool:
        """Delete a note"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM video_notes WHERE id = ?', (note_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        return affected > 0

    def search_notes(self, query: str, video_id: Optional[str] = None) -> List[Dict]:
        """Search notes by content"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        search_term = f'%{query}%'

        if video_id:
            cursor.execute('''
                SELECT * FROM video_notes
                WHERE video_id = ? AND content LIKE ?
                ORDER BY created_date DESC
            ''', (video_id, search_term))
        else:
            cursor.execute('''
                SELECT vn.*, v.title as video_title
                FROM video_notes vn
                JOIN videos v ON vn.video_id = v.video_id
                WHERE vn.content LIKE ?
                ORDER BY vn.created_date DESC
            ''', (search_term,))

        notes = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return notes

    def get_all_notes_for_all_videos(self, limit: int = 100) -> List[Dict]:
        """Get recent notes across all videos"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT vn.*, v.title as video_title, v.thumbnail_url
            FROM video_notes vn
            JOIN videos v ON vn.video_id = v.video_id
            ORDER BY vn.created_date DESC
            LIMIT ?
        ''', (limit,))

        notes = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return notes

    # Analytics operations
    def record_watch_session(self, session_data: Dict[str, Any]) -> int:
        """Record a watch session for analytics"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO watch_sessions (
                video_id, start_time, end_time, duration_watched,
                video_progress_start, video_progress_end, completed
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_data.get('video_id'),
            session_data.get('start_time', datetime.now().isoformat()),
            session_data.get('end_time', datetime.now().isoformat()),
            session_data.get('duration_watched', 0),
            session_data.get('video_progress_start', 0),
            session_data.get('video_progress_end', 0),
            session_data.get('completed', False)
        ))

        conn.commit()
        session_id = cursor.lastrowid
        conn.close()

        return session_id

    def get_watch_statistics(self, days: int = 30) -> Dict:
        """Get overall watch statistics for the last N days"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        from_date = (datetime.now() - __import__('datetime').timedelta(days=days)).isoformat()

        # Total watch time
        cursor.execute('''
            SELECT SUM(duration_watched) as total_seconds
            FROM watch_sessions
            WHERE start_time >= ?
        ''', (from_date,))
        total_time = cursor.fetchone()['total_seconds'] or 0

        # Total videos watched
        cursor.execute('''
            SELECT COUNT(DISTINCT video_id) as video_count
            FROM watch_sessions
            WHERE start_time >= ?
        ''', (from_date,))
        total_videos = cursor.fetchone()['video_count'] or 0

        # Total sessions
        cursor.execute('''
            SELECT COUNT(*) as session_count
            FROM watch_sessions
            WHERE start_time >= ?
        ''', (from_date,))
        total_sessions = cursor.fetchone()['session_count'] or 0

        # Completed videos
        cursor.execute('''
            SELECT COUNT(*) as completed_count
            FROM watch_sessions
            WHERE start_time >= ? AND completed = 1
        ''', (from_date,))
        completed_count = cursor.fetchone()['completed_count'] or 0

        # Average watch time per session
        avg_session_time = total_time / total_sessions if total_sessions > 0 else 0

        conn.close()

        return {
            'total_watch_time_seconds': total_time,
            'total_videos_watched': total_videos,
            'total_sessions': total_sessions,
            'completed_videos': completed_count,
            'average_session_time_seconds': int(avg_session_time),
            'days': days
        }

    def get_top_watched_videos(self, limit: int = 10, days: int = 30) -> List[Dict]:
        """Get most watched videos in the last N days"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        from_date = (datetime.now() - __import__('datetime').timedelta(days=days)).isoformat()

        cursor.execute('''
            SELECT
                v.*,
                COUNT(ws.id) as session_count,
                SUM(ws.duration_watched) as total_watch_time,
                AVG(ws.duration_watched) as avg_watch_time
            FROM videos v
            JOIN watch_sessions ws ON v.video_id = ws.video_id
            WHERE ws.start_time >= ?
            GROUP BY v.video_id
            ORDER BY total_watch_time DESC
            LIMIT ?
        ''', (from_date, limit))

        videos = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # Parse JSON fields
        for video in videos:
            if video.get('tags'):
                try:
                    video['tags'] = json.loads(video['tags'])
                except:
                    video['tags'] = []
            if video.get('ai_tags'):
                try:
                    video['ai_tags'] = json.loads(video['ai_tags'])
                except:
                    video['ai_tags'] = []

        return videos

    def get_watch_activity_by_day(self, days: int = 30) -> List[Dict]:
        """Get daily watch activity for the last N days"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        from_date = (datetime.now() - __import__('datetime').timedelta(days=days)).isoformat()

        cursor.execute('''
            SELECT
                DATE(start_time) as date,
                COUNT(*) as session_count,
                COUNT(DISTINCT video_id) as unique_videos,
                SUM(duration_watched) as total_watch_time,
                SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed_count
            FROM watch_sessions
            WHERE start_time >= ?
            GROUP BY DATE(start_time)
            ORDER BY date DESC
        ''', (from_date,))

        activity = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return activity

    def get_watch_stats_by_source(self, days: int = 30) -> List[Dict]:
        """Get watch statistics grouped by video source"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        from_date = (datetime.now() - __import__('datetime').timedelta(days=days)).isoformat()

        cursor.execute('''
            SELECT
                v.source,
                COUNT(ws.id) as session_count,
                COUNT(DISTINCT ws.video_id) as unique_videos,
                SUM(ws.duration_watched) as total_watch_time
            FROM watch_sessions ws
            JOIN videos v ON ws.video_id = v.video_id
            WHERE ws.start_time >= ?
            GROUP BY v.source
            ORDER BY total_watch_time DESC
        ''', (from_date,))

        stats = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return stats

    def get_watch_stats_by_channel(self, limit: int = 10, days: int = 30) -> List[Dict]:
        """Get watch statistics grouped by channel"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        from_date = (datetime.now() - __import__('datetime').timedelta(days=days)).isoformat()

        cursor.execute('''
            SELECT
                v.channel_name,
                COUNT(ws.id) as session_count,
                COUNT(DISTINCT ws.video_id) as unique_videos,
                SUM(ws.duration_watched) as total_watch_time
            FROM watch_sessions ws
            JOIN videos v ON ws.video_id = v.video_id
            WHERE ws.start_time >= ? AND v.channel_name IS NOT NULL
            GROUP BY v.channel_name
            ORDER BY total_watch_time DESC
            LIMIT ?
        ''', (from_date, limit))

        stats = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return stats

    # Download operations
    def add_download(self, download_data: Dict[str, Any]) -> int:
        """Add a new download to the queue"""
        conn = self.get_connection()
        cursor = conn.cursor()

        download_data['added_date'] = datetime.now().isoformat()
        download_data['status'] = 'pending'

        cursor.execute('''
            INSERT INTO downloads (
                video_id, url, title, quality, status, added_date
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            download_data.get('video_id'),
            download_data.get('url'),
            download_data.get('title'),
            download_data.get('quality', 'best'),
            download_data.get('status'),
            download_data.get('added_date')
        ))

        conn.commit()
        download_id = cursor.lastrowid
        conn.close()

        return download_id

    def get_downloads(self, status: Optional[str] = None) -> List[Dict]:
        """Get all downloads, optionally filtered by status"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if status:
            cursor.execute('''
                SELECT * FROM downloads
                WHERE status = ?
                ORDER BY added_date DESC
            ''', (status,))
        else:
            cursor.execute('''
                SELECT * FROM downloads
                ORDER BY added_date DESC
            ''')

        downloads = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return downloads

    def get_download(self, download_id: int) -> Optional[Dict]:
        """Get a single download by ID"""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM downloads WHERE id = ?', (download_id,))
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def update_download(self, download_id: int, updates: Dict[str, Any]) -> bool:
        """Update download information"""
        conn = self.get_connection()
        cursor = conn.cursor()

        set_clause = ', '.join([f'{key} = ?' for key in updates.keys()])
        values = list(updates.values()) + [download_id]

        cursor.execute(f'UPDATE downloads SET {set_clause} WHERE id = ?', values)
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        return affected > 0

    def delete_download(self, download_id: int) -> bool:
        """Delete a download"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM downloads WHERE id = ?', (download_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()

        return affected > 0

    def get_pending_downloads(self) -> List[Dict]:
        """Get all pending downloads"""
        return self.get_downloads(status='pending')

    def get_active_downloads(self) -> List[Dict]:
        """Get all active (downloading) downloads"""
        return self.get_downloads(status='downloading')

    def get_completed_downloads(self) -> List[Dict]:
        """Get all completed downloads"""
        return self.get_downloads(status='completed')
