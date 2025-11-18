from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import yt_dlp
import os
from typing import List, Dict, Optional, Any
import re


class YouTubeManager:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.youtube = None
        if api_key:
            self.youtube = build('youtube', 'v3', developerKey=api_key)

    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'^([0-9A-Za-z_-]{11})$'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_saved_videos(self, max_results: int = 50) -> Dict[str, Any]:
        """Get saved/liked videos from YouTube"""
        if not self.youtube:
            raise Exception("YouTube API key not configured")

        request = self.youtube.videos().list(
            part='snippet,contentDetails,statistics',
            myRating='like',
            maxResults=max_results
        )
        return request.execute()

    def get_subscription_videos(self, channel_id: str, max_results: int = 20) -> Dict[str, Any]:
        """Get latest videos from a subscribed channel"""
        if not self.youtube:
            raise Exception("YouTube API key not configured")

        request = self.youtube.search().list(
            part='snippet',
            channelId=channel_id,
            order='date',
            maxResults=max_results,
            type='video'
        )
        return request.execute()

    def get_video_details(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a video"""
        if not self.youtube:
            raise Exception("YouTube API key not configured")

        request = self.youtube.videos().list(
            part='snippet,contentDetails,statistics',
            id=video_id
        )
        response = request.execute()

        if response.get('items'):
            return response['items'][0]
        return None

    def get_channel_info(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Get channel information"""
        if not self.youtube:
            raise Exception("YouTube API key not configured")

        request = self.youtube.channels().list(
            part='snippet,statistics',
            id=channel_id
        )
        response = request.execute()

        if response.get('items'):
            return response['items'][0]
        return None

    def search_videos(self, query: str, max_results: int = 25) -> Dict[str, Any]:
        """Search for videos on YouTube"""
        if not self.youtube:
            raise Exception("YouTube API key not configured")

        request = self.youtube.search().list(
            part='snippet',
            q=query,
            maxResults=max_results,
            type='video'
        )
        return request.execute()

    def download_subtitles(self, video_id: str, languages: List[str] = ['bg', 'en']) -> Dict[str, List[Dict]]:
        """Download subtitles/transcripts for a video"""
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            subtitles = {}

            for lang in languages:
                try:
                    # Try to get manual subtitles first
                    transcript = transcript_list.find_transcript([lang])
                    subtitles[lang] = {
                        'data': transcript.fetch(),
                        'is_generated': transcript.is_generated,
                        'language': transcript.language,
                        'language_code': transcript.language_code
                    }
                except:
                    continue

            # If no subtitles found, try auto-generated English
            if not subtitles:
                try:
                    transcript = transcript_list.find_generated_transcript(['en'])
                    subtitles['en'] = {
                        'data': transcript.fetch(),
                        'is_generated': True,
                        'language': transcript.language,
                        'language_code': transcript.language_code
                    }
                except:
                    pass

            return subtitles
        except Exception as e:
            print(f"Error downloading subtitles for {video_id}: {e}")
            return {}

    def download_video(self, video_url: str, output_path: str = './videos') -> Optional[Dict[str, Any]]:
        """Download video file (optional feature)"""
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': f'{output_path}/%(id)s.%(ext)s',
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['bg', 'en'],
            'subtitlesformat': 'vtt',
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                return info
        except Exception as e:
            print(f"Error downloading video: {e}")
            return None

    def get_video_info_without_api(self, video_url: str) -> Optional[Dict[str, Any]]:
        """Get video information without using YouTube API (using yt-dlp)"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                return {
                    'video_id': info.get('id'),
                    'title': info.get('title'),
                    'description': info.get('description'),
                    'duration': info.get('duration'),
                    'thumbnail': info.get('thumbnail'),
                    'uploader': info.get('uploader'),
                    'upload_date': info.get('upload_date'),
                    'view_count': info.get('view_count'),
                    'channel_id': info.get('channel_id'),
                    'channel_url': info.get('channel_url'),
                    'tags': info.get('tags', []),
                }
        except Exception as e:
            print(f"Error extracting video info: {e}")
            return None

    def parse_duration(self, duration_str: str) -> int:
        """Parse YouTube API duration format (PT1H2M3S) to seconds"""
        import re

        pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
        match = pattern.match(duration_str)

        if not match:
            return 0

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)

        return hours * 3600 + minutes * 60 + seconds

    def format_video_data(self, video_item: Dict[str, Any], source: str = 'youtube') -> Dict[str, Any]:
        """Format YouTube API response to standard video data format"""
        snippet = video_item.get('snippet', {})
        content_details = video_item.get('contentDetails', {})
        statistics = video_item.get('statistics', {})

        # Get best quality thumbnail
        thumbnails = snippet.get('thumbnails', {})
        thumbnail_url = (
            thumbnails.get('maxres', {}).get('url') or
            thumbnails.get('high', {}).get('url') or
            thumbnails.get('medium', {}).get('url') or
            thumbnails.get('default', {}).get('url')
        )

        return {
            'video_id': video_item.get('id'),
            'title': snippet.get('title'),
            'source': source,
            'url': f"https://www.youtube.com/watch?v={video_item.get('id')}",
            'thumbnail_url': thumbnail_url,
            'duration': self.parse_duration(content_details.get('duration', 'PT0S')),
            'channel_name': snippet.get('channelTitle'),
            'description': snippet.get('description'),
            'upload_date': snippet.get('publishedAt'),
            'views': int(statistics.get('viewCount', 0)),
            'tags': snippet.get('tags', [])
        }

    def get_playlist_videos(self, playlist_id: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """Get all videos from a playlist"""
        if not self.youtube:
            raise Exception("YouTube API key not configured")

        videos = []
        next_page_token = None

        while True:
            request = self.youtube.playlistItems().list(
                part='snippet',
                playlistId=playlist_id,
                maxResults=min(max_results - len(videos), 50),
                pageToken=next_page_token
            )
            response = request.execute()

            for item in response.get('items', []):
                video_id = item['snippet']['resourceId']['videoId']
                videos.append({'id': video_id})

            next_page_token = response.get('nextPageToken')

            if not next_page_token or len(videos) >= max_results:
                break

        # Get detailed info for all videos
        if videos:
            video_ids = [v['id'] for v in videos[:50]]  # API limit
            request = self.youtube.videos().list(
                part='snippet,contentDetails,statistics',
                id=','.join(video_ids)
            )
            response = request.execute()
            return response.get('items', [])

        return []

    def get_user_subscriptions(self, max_results: int = 50) -> List[Dict[str, Any]]:
        """Get user's channel subscriptions"""
        if not self.youtube:
            raise Exception("YouTube API key not configured")

        subscriptions = []
        next_page_token = None

        while True:
            request = self.youtube.subscriptions().list(
                part='snippet',
                mine=True,
                maxResults=min(max_results - len(subscriptions), 50),
                pageToken=next_page_token
            )
            response = request.execute()

            subscriptions.extend(response.get('items', []))
            next_page_token = response.get('nextPageToken')

            if not next_page_token or len(subscriptions) >= max_results:
                break

        return subscriptions
