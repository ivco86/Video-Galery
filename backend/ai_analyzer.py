import requests
import json
from typing import List, Dict, Optional, Any


class AIAnalyzer:
    def __init__(self, lm_studio_url: str = 'http://localhost:1234'):
        self.base_url = lm_studio_url
        self.model = 'local-model'

    def _call_llm(self, prompt: str, temperature: float = 0.7, max_tokens: int = 500) -> Optional[str]:
        """Make a call to LM Studio API"""
        try:
            response = requests.post(
                f'{self.base_url}/v1/chat/completions',
                json={
                    'model': self.model,
                    'messages': [
                        {'role': 'user', 'content': prompt}
                    ],
                    'temperature': temperature,
                    'max_tokens': max_tokens
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                print(f"LM Studio API error: {response.status_code}")
                return None
        except Exception as e:
            print(f"Error calling LM Studio: {e}")
            return None

    def analyze_video_content(self, title: str, description: str = '', subtitles_text: str = '') -> Optional[Dict[str, Any]]:
        """Analyze video content and generate summary and tags"""

        # Limit subtitle text to avoid token limits
        if subtitles_text and len(subtitles_text) > 3000:
            subtitles_text = subtitles_text[:3000] + '...'

        prompt = f"""Анализирай следното видео съдържание и предостави структуриран отговор във формат JSON.

Заглавие: {title}
Описание: {description if description else 'Няма описание'}
Субтитри/Съдържание: {subtitles_text if subtitles_text else 'Няма субтитри'}

Моля, отговори САМО с валиден JSON обект в следния формат:
{{
    "summary": "кратко резюме на видеото в 2-3 изречения",
    "tags": ["таг1", "таг2", "таг3", "таг4", "таг5"],
    "category": "основна категория на видеото",
    "key_points": ["важна точка 1", "важна точка 2", "важна точка 3"],
    "language": "основен език на видеото (bg/en/etc)",
    "topics": ["тема1", "тема2"]
}}
"""

        response = self._call_llm(prompt, temperature=0.7, max_tokens=500)

        if response:
            try:
                # Try to extract JSON from response
                json_match = response.strip()

                # Remove markdown code blocks if present
                if json_match.startswith('```'):
                    json_match = json_match.split('```')[1]
                    if json_match.startswith('json'):
                        json_match = json_match[4:]

                json_match = json_match.strip()

                result = json.loads(json_match)
                return result
            except json.JSONDecodeError:
                # If JSON parsing fails, return basic structure
                return {
                    'summary': response[:200] if len(response) > 200 else response,
                    'tags': [],
                    'category': 'general',
                    'key_points': [],
                    'language': 'unknown',
                    'topics': []
                }

        return None

    def generate_tags(self, text: str, max_tags: int = 10) -> List[str]:
        """Generate relevant tags from text content"""

        if not text:
            return []

        # Limit text length
        if len(text) > 2000:
            text = text[:2000]

        prompt = f"""Въз основа на следния текст, генерирай {max_tags} релевантни тагове/ключови думи.

Текст: {text}

Върни САМО списък от тагове разделени със запетая, без номерация или допълнително форматиране.
Пример: технология, програмиране, уеб разработка, javascript
"""

        response = self._call_llm(prompt, temperature=0.5, max_tokens=100)

        if response:
            # Parse tags from response
            tags = [tag.strip() for tag in response.replace('\n', ',').split(',')]
            tags = [tag for tag in tags if tag and len(tag) > 2]
            return tags[:max_tags]

        return []

    def summarize_text(self, text: str, max_length: int = 200) -> str:
        """Generate a concise summary of text"""

        if not text:
            return ""

        # Limit input text
        if len(text) > 4000:
            text = text[:4000]

        prompt = f"""Напиши кратко резюме на следния текст в максимум {max_length} символа.

Текст: {text}

Резюме:"""

        response = self._call_llm(prompt, temperature=0.5, max_tokens=150)

        if response:
            return response.strip()[:max_length]

        return ""

    def categorize_video(self, title: str, description: str = '', tags: List[str] = None) -> str:
        """Categorize video into a main category"""

        tags_str = ', '.join(tags) if tags else 'няма тагове'

        prompt = f"""Определи най-подходящата категория за следното видео. Избери ЕДНА категория от списъка:

Категории: Образование, Развлечение, Технология, Наука, Спорт, Музика, Игри, Новини, Влогове, Готвене, Пътувания, Бизнес, Здраве, Изкуство, Друго

Заглавие: {title}
Описание: {description if description else 'няма'}
Тагове: {tags_str}

Върни САМО името на категорията, без допълнителен текст.
"""

        response = self._call_llm(prompt, temperature=0.3, max_tokens=20)

        if response:
            category = response.strip()
            return category

        return "Друго"

    def extract_topics(self, text: str, max_topics: int = 5) -> List[str]:
        """Extract main topics from text"""

        if not text or len(text) < 50:
            return []

        # Limit text length
        if len(text) > 3000:
            text = text[:3000]

        prompt = f"""Извлечи {max_topics} основни теми, които се обсъждат в следния текст.

Текст: {text}

Върни САМО темите разделени със запетая, без номерация.
"""

        response = self._call_llm(prompt, temperature=0.5, max_tokens=100)

        if response:
            topics = [topic.strip() for topic in response.replace('\n', ',').split(',')]
            topics = [topic for topic in topics if topic and len(topic) > 2]
            return topics[:max_topics]

        return []

    def semantic_search(self, query: str, video_contents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Perform semantic search across video contents"""

        if not video_contents:
            return []

        # Create a summary of each video for comparison
        summaries = []
        for video in video_contents[:20]:  # Limit to prevent token overflow
            summary = f"Title: {video.get('title', '')}\n"
            if video.get('ai_summary'):
                summary += f"Summary: {video.get('ai_summary', '')}\n"
            if video.get('description'):
                summary += f"Description: {video.get('description', '')[:200]}\n"

            summaries.append({
                'video_id': video.get('video_id'),
                'summary': summary
            })

        # Use AI to rank relevance
        prompt = f"""Търся видеа свързани с: "{query}"

Ето списък с видеа (ID и резюме):

"""
        for i, item in enumerate(summaries, 1):
            prompt += f"{i}. ID: {item['video_id']}\n{item['summary']}\n\n"

        prompt += f"""
Базирайки се на горната информация, кои видеа са най-релевантни към търсенето "{query}"?
Върни списък от ID-та на видеата подредени по релевантност (най-релевантното първо), разделени със запетая.
Пример: video1, video5, video3
"""

        response = self._call_llm(prompt, temperature=0.3, max_tokens=200)

        if response:
            # Parse video IDs from response
            video_ids = [vid.strip() for vid in response.replace('\n', ',').split(',')]
            video_ids = [vid for vid in video_ids if vid]

            # Reorder videos based on AI ranking
            ranked_videos = []
            for vid_id in video_ids:
                for video in video_contents:
                    if video.get('video_id') == vid_id:
                        ranked_videos.append(video)
                        break

            return ranked_videos

        return video_contents

    def suggest_related_videos(self, video: Dict[str, Any], all_videos: List[Dict[str, Any]], max_results: int = 5) -> List[str]:
        """Suggest related videos based on content similarity"""

        if not all_videos or len(all_videos) < 2:
            return []

        current_id = video.get('video_id')
        current_summary = f"{video.get('title', '')} {video.get('ai_summary', '')} {' '.join(video.get('ai_tags', []))}"

        # Filter out current video
        other_videos = [v for v in all_videos if v.get('video_id') != current_id][:20]

        if not other_videos:
            return []

        prompt = f"""Намирам се на видео: "{video.get('title', '')}"
Резюме: {video.get('ai_summary', '')[:200]}

Кои от следните видеа са най-сходни/свързани? Върни {max_results} ID-та подредени по сходство.

Видеа:
"""
        for v in other_videos:
            prompt += f"- ID: {v.get('video_id')}, Title: {v.get('title', '')}\n"

        prompt += f"\nВърни САМО ID-тата разделени със запетая. Пример: id1, id2, id3"

        response = self._call_llm(prompt, temperature=0.3, max_tokens=100)

        if response:
            video_ids = [vid.strip() for vid in response.replace('\n', ',').split(',')]
            return [vid for vid in video_ids if vid][:max_results]

        return []

    def is_available(self) -> bool:
        """Check if LM Studio is available"""
        try:
            response = requests.get(f'{self.base_url}/v1/models', timeout=5)
            return response.status_code == 200
        except:
            return False
