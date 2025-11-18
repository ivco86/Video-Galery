import pysrt
import webvtt
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
import re


class SubtitleManager:

    @staticmethod
    def parse_srt(file_path: str) -> List[Dict[str, Any]]:
        """Parse SRT subtitle file"""
        try:
            subs = pysrt.open(file_path, encoding='utf-8')
            return [{
                'index': sub.index,
                'start': sub.start.ordinal / 1000,  # Convert to seconds
                'end': sub.end.ordinal / 1000,
                'text': sub.text.replace('\n', ' ')
            } for sub in subs]
        except Exception as e:
            print(f"Error parsing SRT file {file_path}: {e}")
            return []

    @staticmethod
    def parse_vtt(file_path: str) -> List[Dict[str, Any]]:
        """Parse WebVTT subtitle file"""
        try:
            vtt = webvtt.read(file_path)
            return [{
                'start': SubtitleManager._time_to_seconds(caption.start),
                'end': SubtitleManager._time_to_seconds(caption.end),
                'text': caption.text.replace('\n', ' ')
            } for caption in vtt]
        except Exception as e:
            print(f"Error parsing VTT file {file_path}: {e}")
            return []

    @staticmethod
    def parse_subtitle_file(file_path: str) -> List[Dict[str, Any]]:
        """Auto-detect format and parse subtitle file"""
        ext = Path(file_path).suffix.lower()

        if ext == '.srt':
            return SubtitleManager.parse_srt(file_path)
        elif ext in ['.vtt', '.webvtt']:
            return SubtitleManager.parse_vtt(file_path)
        else:
            # Try to auto-detect
            try:
                return SubtitleManager.parse_srt(file_path)
            except:
                try:
                    return SubtitleManager.parse_vtt(file_path)
                except:
                    return []

    @staticmethod
    def _time_to_seconds(time_str: str) -> float:
        """Convert timestamp string to seconds"""
        try:
            # Handle formats like "00:01:23.456" or "01:23.456"
            parts = time_str.split(':')

            if len(parts) == 3:
                h, m, s = parts
                return int(h) * 3600 + int(m) * 60 + float(s)
            elif len(parts) == 2:
                m, s = parts
                return int(m) * 60 + float(s)
            else:
                return float(time_str)
        except:
            return 0.0

    @staticmethod
    def _seconds_to_time(seconds: float) -> str:
        """Convert seconds to timestamp string (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        milliseconds = int((secs % 1) * 1000)
        secs = int(secs)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

    @staticmethod
    def get_full_text(subtitles: List[Dict[str, Any]]) -> str:
        """Extract full text from subtitle entries"""
        return ' '.join([sub['text'] for sub in subtitles if 'text' in sub])

    @staticmethod
    def search_in_subtitles(subtitles: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Search for query in subtitles and return matching entries with context"""
        results = []
        query_lower = query.lower()

        for i, sub in enumerate(subtitles):
            if query_lower in sub['text'].lower():
                # Get context (previous and next subtitle)
                context_before = subtitles[i-1]['text'] if i > 0 else ''
                context_after = subtitles[i+1]['text'] if i < len(subtitles) - 1 else ''

                results.append({
                    'timestamp': sub['start'],
                    'end': sub['end'],
                    'text': sub['text'],
                    'context_before': context_before,
                    'context_after': context_after,
                    'index': i
                })

        return results

    @staticmethod
    def filter_by_time_range(subtitles: List[Dict[str, Any]], start_time: float, end_time: float) -> List[Dict[str, Any]]:
        """Get subtitles within a specific time range"""
        return [
            sub for sub in subtitles
            if start_time <= sub['start'] <= end_time or start_time <= sub['end'] <= end_time
        ]

    @staticmethod
    def save_as_srt(subtitles: List[Dict[str, Any]], output_path: str) -> bool:
        """Save subtitles in SRT format"""
        try:
            srt_subs = pysrt.SubRipFile()

            for i, sub in enumerate(subtitles, start=1):
                item = pysrt.SubRipItem()
                item.index = i
                item.start.seconds = sub['start']
                item.end.seconds = sub['end']
                item.text = sub['text']
                srt_subs.append(item)

            srt_subs.save(output_path, encoding='utf-8')
            return True
        except Exception as e:
            print(f"Error saving SRT file: {e}")
            return False

    @staticmethod
    def save_as_vtt(subtitles: List[Dict[str, Any]], output_path: str) -> bool:
        """Save subtitles in WebVTT format"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("WEBVTT\n\n")

                for sub in subtitles:
                    start = SubtitleManager._format_vtt_time(sub['start'])
                    end = SubtitleManager._format_vtt_time(sub['end'])
                    f.write(f"{start} --> {end}\n")
                    f.write(f"{sub['text']}\n\n")

            return True
        except Exception as e:
            print(f"Error saving VTT file: {e}")
            return False

    @staticmethod
    def _format_vtt_time(seconds: float) -> str:
        """Format seconds as VTT timestamp (HH:MM:SS.mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60

        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

    @staticmethod
    def convert_youtube_transcript(transcript_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert YouTube transcript format to standard subtitle format"""
        subtitles = []

        for item in transcript_data:
            subtitles.append({
                'start': item.get('start', 0),
                'end': item.get('start', 0) + item.get('duration', 0),
                'text': item.get('text', '')
            })

        return subtitles

    @staticmethod
    def merge_subtitles(subtitles: List[Dict[str, Any]], max_gap: float = 2.0) -> List[Dict[str, Any]]:
        """Merge consecutive subtitle entries with small gaps"""
        if not subtitles:
            return []

        merged = []
        current = subtitles[0].copy()

        for i in range(1, len(subtitles)):
            next_sub = subtitles[i]
            gap = next_sub['start'] - current['end']

            if gap <= max_gap:
                # Merge
                current['end'] = next_sub['end']
                current['text'] += ' ' + next_sub['text']
            else:
                # Save current and start new
                merged.append(current)
                current = next_sub.copy()

        merged.append(current)
        return merged

    @staticmethod
    def clean_subtitle_text(text: str) -> str:
        """Clean subtitle text from formatting tags and extra whitespace"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Remove formatting tags like {italic}, [music], etc.
        text = re.sub(r'[\{\[].*?[\}\]]', '', text)

        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)

        # Remove speaker labels like "Speaker 1:", "NARRATOR:", etc.
        text = re.sub(r'^[A-Z\s]+:', '', text)

        return text.strip()

    @staticmethod
    def generate_subtitle_summary(subtitles: List[Dict[str, Any]], max_length: int = 500) -> str:
        """Generate a summary of subtitle content"""
        full_text = SubtitleManager.get_full_text(subtitles)

        # Clean text
        clean_text = SubtitleManager.clean_subtitle_text(full_text)

        # Truncate if too long
        if len(clean_text) > max_length:
            clean_text = clean_text[:max_length] + '...'

        return clean_text

    @staticmethod
    def extract_keywords(subtitles: List[Dict[str, Any]], min_word_length: int = 4) -> List[str]:
        """Extract potential keywords from subtitles"""
        full_text = SubtitleManager.get_full_text(subtitles)

        # Clean and split into words
        words = re.findall(r'\b\w+\b', full_text.lower())

        # Filter by length
        words = [w for w in words if len(w) >= min_word_length]

        # Count frequency
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1

        # Sort by frequency and return top keywords
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)

        # Return top 20 keywords
        return [word for word, freq in sorted_words[:20]]

    @staticmethod
    def find_similar_subtitles(subtitles: List[Dict[str, Any]], text: str, threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Find subtitles similar to given text using simple similarity"""
        results = []
        text_lower = text.lower()
        text_words = set(re.findall(r'\b\w+\b', text_lower))

        for sub in subtitles:
            sub_words = set(re.findall(r'\b\w+\b', sub['text'].lower()))

            # Calculate Jaccard similarity
            if text_words and sub_words:
                intersection = len(text_words & sub_words)
                union = len(text_words | sub_words)
                similarity = intersection / union if union > 0 else 0

                if similarity >= threshold:
                    results.append({
                        **sub,
                        'similarity': similarity
                    })

        # Sort by similarity
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results
