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
