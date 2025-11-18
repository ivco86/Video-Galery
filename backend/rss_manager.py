import feedparser
import requests
from datetime import datetime
from typing import List, Dict, Optional
import re


class RSSManager:
    """Manages RSS/Atom feed parsing and video extraction"""

    def __init__(self):
        self.user_agent = 'Mozilla/5.0 (compatible; VideoGallery/1.0)'

    def parse_feed(self, feed_url: str) -> Dict:
        """Parse an RSS/Atom feed and extract video information"""
        try:
            # Parse the feed with custom user agent
            feed = feedparser.parse(
                feed_url,
                agent=self.user_agent
            )

            if feed.bozo:  # Feed has errors
                if hasattr(feed, 'bozo_exception'):
                    raise Exception(f"Feed parsing error: {feed.bozo_exception}")

            # Extract feed metadata
            feed_info = {
                'title': feed.feed.get('title', 'Unknown Feed'),
                'description': feed.feed.get('description', ''),
                'link': feed.feed.get('link', ''),
                'updated': feed.feed.get('updated', ''),
                'entries': []
            }

            # Process entries
            for entry in feed.entries:
                video_entry = self._extract_video_from_entry(entry)
                if video_entry:
                    feed_info['entries'].append(video_entry)

            return feed_info

        except Exception as e:
            raise Exception(f"Failed to parse feed: {str(e)}")

    def _extract_video_from_entry(self, entry) -> Optional[Dict]:
        """Extract video information from a feed entry"""
        try:
            # Extract video URL from various sources
            video_url = self._find_video_url(entry)
            if not video_url:
                return None

            # Extract video ID
            video_id = self._extract_video_id(video_url)
            if not video_id:
                return None

            # Extract thumbnail
            thumbnail_url = self._find_thumbnail(entry)

            # Extract duration (if available)
            duration = self._extract_duration(entry)

            # Extract publish date
            published = entry.get('published', entry.get('updated', ''))
            if published:
                try:
                    # Parse the date
                    from email.utils import parsedate_to_datetime
                    published_dt = parsedate_to_datetime(published)
                    published = published_dt.isoformat()
                except:
                    published = datetime.now().isoformat()
            else:
                published = datetime.now().isoformat()

            return {
                'video_id': video_id,
                'title': entry.get('title', 'Untitled'),
                'description': entry.get('summary', entry.get('description', '')),
                'url': video_url,
                'thumbnail_url': thumbnail_url,
                'channel_name': entry.get('author', 'Unknown'),
                'upload_date': published,
                'duration': duration,
                'source': 'youtube' if 'youtube.com' in video_url or 'youtu.be' in video_url else 'rss'
            }

        except Exception as e:
            print(f"Error extracting video from entry: {e}")
            return None

    def _find_video_url(self, entry) -> Optional[str]:
        """Find video URL from entry"""
        # Check direct link
        if hasattr(entry, 'link'):
            return entry.link

        # Check enclosure (common in podcasts)
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enclosure in entry.enclosures:
                if 'video' in enclosure.get('type', ''):
                    return enclosure.get('href', enclosure.get('url'))

        # Check media:content (YouTube RSS)
        if hasattr(entry, 'media_content') and entry.media_content:
            return entry.media_content[0].get('url')

        # Check links array
        if hasattr(entry, 'links'):
            for link in entry.links:
                if link.get('rel') == 'alternate':
                    return link.get('href')

        return None

    def _extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from URL"""
        # YouTube video ID patterns
        youtube_patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})'
        ]

        for pattern in youtube_patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        # For non-YouTube URLs, generate ID from URL hash
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()[:11]

    def _find_thumbnail(self, entry) -> Optional[str]:
        """Find thumbnail URL from entry"""
        # Check media:thumbnail (YouTube RSS)
        if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            return entry.media_thumbnail[0].get('url')

        # Check media:content
        if hasattr(entry, 'media_content') and entry.media_content:
            for content in entry.media_content:
                if 'image' in content.get('type', ''):
                    return content.get('url')

        # Check enclosures for images
        if hasattr(entry, 'enclosures'):
            for enclosure in entry.enclosures:
                if 'image' in enclosure.get('type', ''):
                    return enclosure.get('href', enclosure.get('url'))

        # Check links for thumbnail
        if hasattr(entry, 'links'):
            for link in entry.links:
                if link.get('rel') == 'thumbnail' or link.get('rel') == 'image':
                    return link.get('href')

        # Default YouTube thumbnail for YouTube videos
        if hasattr(entry, 'link') and 'youtube.com' in entry.link:
            video_id = self._extract_video_id(entry.link)
            if video_id:
                return f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg"

        return None

    def _extract_duration(self, entry) -> Optional[int]:
        """Extract video duration in seconds"""
        # Check media:content duration
        if hasattr(entry, 'media_content') and entry.media_content:
            for content in entry.media_content:
                if 'duration' in content:
                    try:
                        return int(content['duration'])
                    except:
                        pass

        # Check itunes:duration (podcast feeds)
        if hasattr(entry, 'itunes_duration'):
            try:
                duration_str = entry.itunes_duration
                # Parse formats like "HH:MM:SS" or "MM:SS" or just seconds
                parts = duration_str.split(':')
                if len(parts) == 3:  # HH:MM:SS
                    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                elif len(parts) == 2:  # MM:SS
                    return int(parts[0]) * 60 + int(parts[1])
                else:  # Just seconds
                    return int(duration_str)
            except:
                pass

        return None

    def validate_feed_url(self, url: str) -> bool:
        """Validate if URL is a valid feed"""
        try:
            response = requests.head(url, timeout=5, headers={'User-Agent': self.user_agent})
            content_type = response.headers.get('Content-Type', '')

            # Check if content type suggests a feed
            feed_types = ['application/rss+xml', 'application/atom+xml', 'application/xml', 'text/xml']
            return any(ft in content_type for ft in feed_types) or response.status_code == 200
        except:
            return False

    def get_youtube_channel_feed_url(self, channel_id: str) -> str:
        """Convert YouTube channel ID to RSS feed URL"""
        return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

    def extract_channel_id_from_url(self, url: str) -> Optional[str]:
        """Extract YouTube channel ID from various URL formats"""
        # Pattern for channel ID in URL
        patterns = [
            r'youtube\.com\/channel\/([a-zA-Z0-9_-]+)',
            r'youtube\.com\/feeds\/videos\.xml\?channel_id=([a-zA-Z0-9_-]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None
