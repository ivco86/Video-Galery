import os
import cv2
import subprocess
import json
from pathlib import Path
import hashlib
from typing import List, Dict, Optional, Any
import mimetypes


class VideoProcessor:
    def __init__(self, videos_folder: str = './videos'):
        self.videos_folder = videos_folder
        self.video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv', '.m4v', '.mpeg', '.mpg']

    def scan_local_videos(self) -> List[Dict[str, Any]]:
        """Scan folder for local video files"""
        videos = []

        if not os.path.exists(self.videos_folder):
            os.makedirs(self.videos_folder)
            return videos

        for root, dirs, files in os.walk(self.videos_folder):
            for file in files:
                if any(file.lower().endswith(ext) for ext in self.video_extensions):
                    full_path = os.path.join(root, file)
                    try:
                        file_stats = os.stat(full_path)
                        videos.append({
                            'path': full_path,
                            'filename': file,
                            'size': file_stats.st_size,
                            'modified_time': file_stats.st_mtime,
                            'relative_path': os.path.relpath(full_path, self.videos_folder)
                        })
                    except Exception as e:
                        print(f"Error accessing file {full_path}: {e}")

        return videos

    def generate_video_id(self, file_path: str) -> str:
        """Generate unique ID for local video based on file path and size"""
        stat = os.stat(file_path)
        unique_string = f"{file_path}_{stat.st_size}_{stat.st_mtime}"
        return hashlib.md5(unique_string.encode()).hexdigest()

    def get_video_metadata(self, video_path: str) -> Optional[Dict[str, Any]]:
        """Extract metadata from video file using OpenCV"""
        try:
            cap = cv2.VideoCapture(video_path)

            if not cap.isOpened():
                return None

            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            duration = int(frame_count / fps) if fps > 0 else 0

            metadata = {
                'duration': duration,
                'fps': fps,
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'frame_count': int(frame_count),
            }

            cap.release()
            return metadata
        except Exception as e:
            print(f"Error extracting metadata from {video_path}: {e}")
            return None

    def get_video_metadata_ffprobe(self, video_path: str) -> Optional[Dict[str, Any]]:
        """Extract detailed metadata using ffprobe (more reliable than OpenCV)"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                data = json.loads(result.stdout)

                # Find video stream
                video_stream = None
                audio_stream = None
                subtitle_streams = []

                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'video' and not video_stream:
                        video_stream = stream
                    elif stream.get('codec_type') == 'audio' and not audio_stream:
                        audio_stream = stream
                    elif stream.get('codec_type') == 'subtitle':
                        subtitle_streams.append(stream)

                format_info = data.get('format', {})

                metadata = {
                    'duration': float(format_info.get('duration', 0)),
                    'size': int(format_info.get('size', 0)),
                    'bitrate': int(format_info.get('bit_rate', 0)),
                    'format_name': format_info.get('format_name'),
                }

                if video_stream:
                    metadata.update({
                        'width': video_stream.get('width', 0),
                        'height': video_stream.get('height', 0),
                        'codec': video_stream.get('codec_name'),
                        'fps': self._parse_fps(video_stream.get('r_frame_rate', '0/1')),
                    })

                if audio_stream:
                    metadata['audio_codec'] = audio_stream.get('codec_name')
                    metadata['audio_channels'] = audio_stream.get('channels', 0)

                metadata['subtitle_tracks'] = len(subtitle_streams)
                metadata['subtitle_languages'] = [
                    s.get('tags', {}).get('language', 'unknown')
                    for s in subtitle_streams
                ]

                return metadata
            else:
                return None
        except Exception as e:
            print(f"Error running ffprobe on {video_path}: {e}")
            return None

    def _parse_fps(self, fps_string: str) -> float:
        """Parse FPS from fractional format (e.g., '30000/1001')"""
        try:
            if '/' in fps_string:
                num, denom = fps_string.split('/')
                return float(num) / float(denom)
            return float(fps_string)
        except:
            return 0.0

    def generate_thumbnail(self, video_path: str, output_path: str, timestamp: int = 5) -> Optional[str]:
        """Generate thumbnail from video at specific timestamp"""
        try:
            cap = cv2.VideoCapture(video_path)

            if not cap.isOpened():
                return None

            # Set position to timestamp (in milliseconds)
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000)

            success, frame = cap.read()

            if success:
                # Create output directory if it doesn't exist
                os.makedirs(os.path.dirname(output_path), exist_ok=True)

                # Resize to reasonable thumbnail size
                height, width = frame.shape[:2]
                max_width = 640
                if width > max_width:
                    scale = max_width / width
                    new_width = max_width
                    new_height = int(height * scale)
                    frame = cv2.resize(frame, (new_width, new_height))

                cv2.imwrite(output_path, frame)
                cap.release()
                return output_path
            else:
                cap.release()
                return None
        except Exception as e:
            print(f"Error generating thumbnail for {video_path}: {e}")
            return None

    def generate_thumbnail_ffmpeg(self, video_path: str, output_path: str, timestamp: int = 5) -> Optional[str]:
        """Generate thumbnail using ffmpeg (faster and more reliable)"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            cmd = [
                'ffmpeg',
                '-ss', str(timestamp),
                '-i', video_path,
                '-vframes', '1',
                '-vf', 'scale=640:-1',
                '-y',
                output_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and os.path.exists(output_path):
                return output_path
            else:
                return None
        except Exception as e:
            print(f"Error generating thumbnail with ffmpeg: {e}")
            return None

    def extract_subtitles(self, video_path: str, output_dir: str) -> List[Dict[str, Any]]:
        """Extract embedded subtitles from video file"""
        try:
            # First, get subtitle stream info
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                '-select_streams', 's',
                video_path
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                return []

            data = json.loads(result.stdout)
            subtitle_streams = data.get('streams', [])

            if not subtitle_streams:
                return []

            os.makedirs(output_dir, exist_ok=True)
            extracted_subtitles = []

            # Extract each subtitle stream
            for i, stream in enumerate(subtitle_streams):
                language = stream.get('tags', {}).get('language', 'unknown')
                subtitle_format = stream.get('codec_name', 'srt')

                # Determine file extension
                ext = 'srt' if subtitle_format in ['subrip', 'srt'] else subtitle_format

                output_file = os.path.join(
                    output_dir,
                    f"{Path(video_path).stem}_{language}_{i}.{ext}"
                )

                # Extract subtitle
                extract_cmd = [
                    'ffmpeg',
                    '-i', video_path,
                    '-map', f'0:s:{i}',
                    '-y',
                    output_file
                ]

                extract_result = subprocess.run(
                    extract_cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                if extract_result.returncode == 0 and os.path.exists(output_file):
                    extracted_subtitles.append({
                        'path': output_file,
                        'language': language,
                        'format': ext,
                        'stream_index': i
                    })

            return extracted_subtitles
        except Exception as e:
            print(f"Error extracting subtitles from {video_path}: {e}")
            return []

    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Get comprehensive video information"""
        filename = os.path.basename(video_path)
        video_id = self.generate_video_id(video_path)

        # Try ffprobe first (more reliable)
        metadata = self.get_video_metadata_ffprobe(video_path)

        # Fallback to OpenCV if ffprobe fails
        if not metadata:
            metadata = self.get_video_metadata(video_path)

        if not metadata:
            metadata = {}

        # Extract title from filename
        title = Path(filename).stem.replace('_', ' ').replace('-', ' ')

        return {
            'video_id': video_id,
            'title': title,
            'source': 'local',
            'file_path': video_path,
            'filename': filename,
            'duration': int(metadata.get('duration', 0)),
            'width': metadata.get('width', 0),
            'height': metadata.get('height', 0),
            'fps': metadata.get('fps', 0),
            'size': metadata.get('size', os.path.getsize(video_path)),
            'codec': metadata.get('codec', 'unknown'),
            'has_subtitles': metadata.get('subtitle_tracks', 0) > 0,
        }

    def is_video_file(self, file_path: str) -> bool:
        """Check if file is a video"""
        if not os.path.isfile(file_path):
            return False

        # Check extension
        if not any(file_path.lower().endswith(ext) for ext in self.video_extensions):
            return False

        # Check MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type and mime_type.startswith('video/'):
            return True

        return True  # Trust extension if MIME check is inconclusive
