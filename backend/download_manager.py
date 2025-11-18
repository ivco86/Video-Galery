"""Download Manager for Video Gallery - handles video downloads with yt-dlp"""
import os
import threading
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import yt_dlp


class DownloadManager:
    def __init__(self, download_folder='downloads', db=None):
        self.download_folder = download_folder
        self.db = db
        self.active_downloads = {}
        self.download_threads = {}

        # Create download folder if it doesn't exist
        os.makedirs(download_folder, exist_ok=True)

    def add_to_queue(self, video_id: str, url: str, title: str, quality: str = 'best') -> int:
        """Add a video to the download queue"""
        download_data = {
            'video_id': video_id,
            'url': url,
            'title': title,
            'quality': quality
        }

        download_id = self.db.add_download(download_data)
        return download_id

    def start_download(self, download_id: int) -> bool:
        """Start downloading a video"""
        download = self.db.get_download(download_id)

        if not download:
            return False

        # Update status to downloading
        self.db.update_download(download_id, {
            'status': 'downloading',
            'started_date': datetime.now().isoformat()
        })

        # Start download in a separate thread
        thread = threading.Thread(
            target=self._download_worker,
            args=(download_id, download['url'], download['title'], download['quality'])
        )
        thread.daemon = True
        thread.start()

        self.download_threads[download_id] = thread

        return True

    def _download_worker(self, download_id: int, url: str, title: str, quality: str):
        """Worker function to download a video"""
        try:
            # Set up yt-dlp options
            output_template = os.path.join(self.download_folder, f'{download_id}_%(title)s.%(ext)s')

            ydl_opts = {
                'format': self._get_format_string(quality),
                'outtmpl': output_template,
                'progress_hooks': [lambda d: self._progress_hook(download_id, d)],
                'quiet': True,
                'no_warnings': True,
            }

            # Download the video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                file_size = info.get('filesize') or info.get('filesize_approx', 0)

                # Update database with completion
                self.db.update_download(download_id, {
                    'status': 'completed',
                    'progress': 100,
                    'file_path': filename,
                    'file_size': file_size,
                    'completed_date': datetime.now().isoformat()
                })

        except Exception as e:
            # Update database with error
            self.db.update_download(download_id, {
                'status': 'failed',
                'error_message': str(e)
            })

        finally:
            # Clean up
            if download_id in self.active_downloads:
                del self.active_downloads[download_id]
            if download_id in self.download_threads:
                del self.download_threads[download_id]

    def _progress_hook(self, download_id: int, d: Dict[str, Any]):
        """Hook to track download progress"""
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)

            if total > 0:
                progress = int((downloaded / total) * 100)

                # Store active download info
                self.active_downloads[download_id] = {
                    'progress': progress,
                    'downloaded_bytes': downloaded,
                    'total_bytes': total,
                    'speed': d.get('speed', 0),
                    'eta': d.get('eta', 0)
                }

                # Update database every 5%
                if progress % 5 == 0:
                    self.db.update_download(download_id, {'progress': progress})

    def _get_format_string(self, quality: str) -> str:
        """Get yt-dlp format string based on quality"""
        quality_map = {
            'best': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            '1080p': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]',
            '720p': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]',
            '480p': 'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]',
            '360p': 'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]',
            'audio': 'bestaudio[ext=m4a]/bestaudio'
        }

        return quality_map.get(quality, quality_map['best'])

    def cancel_download(self, download_id: int) -> bool:
        """Cancel an active download"""
        if download_id in self.active_downloads:
            # Update status
            self.db.update_download(download_id, {
                'status': 'cancelled'
            })

            # Clean up
            if download_id in self.active_downloads:
                del self.active_downloads[download_id]

            return True

        return False

    def delete_download(self, download_id: int, delete_file: bool = False) -> bool:
        """Delete a download record and optionally the file"""
        download = self.db.get_download(download_id)

        if not download:
            return False

        # Delete file if requested and exists
        if delete_file and download.get('file_path'):
            try:
                if os.path.exists(download['file_path']):
                    os.remove(download['file_path'])
            except Exception as e:
                print(f"Error deleting file: {e}")

        # Delete from database
        return self.db.delete_download(download_id)

    def get_active_download_info(self, download_id: int) -> Optional[Dict]:
        """Get real-time info for an active download"""
        return self.active_downloads.get(download_id)

    def get_all_downloads(self) -> Dict[str, Any]:
        """Get all downloads grouped by status"""
        all_downloads = self.db.get_downloads()

        # Add real-time info for active downloads
        for download in all_downloads:
            if download['id'] in self.active_downloads:
                download['real_time_info'] = self.active_downloads[download['id']]

        return {
            'pending': [d for d in all_downloads if d['status'] == 'pending'],
            'downloading': [d for d in all_downloads if d['status'] == 'downloading'],
            'completed': [d for d in all_downloads if d['status'] == 'completed'],
            'failed': [d for d in all_downloads if d['status'] == 'failed'],
            'cancelled': [d for d in all_downloads if d['status'] == 'cancelled']
        }

    def process_queue(self, max_concurrent: int = 2):
        """Process pending downloads with concurrency limit"""
        active_count = len([d for d in self.db.get_downloads() if d['status'] == 'downloading'])

        if active_count < max_concurrent:
            pending = self.db.get_pending_downloads()

            for download in pending[:max_concurrent - active_count]:
                self.start_download(download['id'])
