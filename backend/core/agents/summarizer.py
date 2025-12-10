"""
Summarizer Agent - Content Extraction and Synthesis

Extracts key information and generates summaries using multiple strategies.
Supports briefings, summaries, and key point extraction.
"""

from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
from datetime import datetime
from collections import Counter

logger = logging.getLogger(__name__)


class SummaryStyle(str, Enum):
    """Style of summary to generate."""
    BULLET_POINTS = "bullet_points"  # List of key points
    NARRATIVE = "narrative"  # Paragraph form
    TECHNICAL = "technical"  # Detailed technical summary
    EXECUTIVE = "executive"  # High-level business summary
    TIMELINE = "timeline"  # Chronological summary


class SummaryLength(str, Enum):
    """Desired length of summary."""
    SHORT = "short"  # 50-100 words
    MEDIUM = "medium"  # 150-250 words
    LONG = "long"  # 300-500 words
    FULL = "full"  # Complete preservation


@dataclass
class KeyPoint:
    """Extracted key point from content."""
    text: str
    importance_score: float  # 0-1, higher is more important
    source_section: Optional[str] = None  # Where it came from
    supporting_details: List[str] = field(default_factory=list)
    category: Optional[str] = None  # Type of key point
    
    def to_dict(self):
        return asdict(self)


@dataclass
class SummaryResult:
    """Result of summarization."""
    content_id: str
    original_length: int
    summary_text: str
    style: SummaryStyle
    summary_length: int = 0
    compression_ratio: float = 0.0
    key_points: List[KeyPoint] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self):
        return {
            "content_id": self.content_id,
            "original_length": self.original_length,
            "summary_length": self.summary_length,
            "compression_ratio": self.compression_ratio,
            "summary_text": self.summary_text,
            "style": self.style.value,
            "key_points": [kp.to_dict() for kp in self.key_points],
            "topics": self.topics,
            "entities": self.entities,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class SummaryConfig:
    """Configuration for summarization."""
    style: SummaryStyle = SummaryStyle.BULLET_POINTS
    length: SummaryLength = SummaryLength.MEDIUM
    extract_key_points: bool = True
    extract_topics: bool = True
    extract_entities: bool = True
    preserve_tone: bool = True
    include_context: bool = True
    target_key_points: int = 5  # Number of key points to extract
    min_point_length: int = 20  # Minimum character length for a point
    target_summary_words: int = 150


class SummarizerAgent:
    """Generates summaries and extracts key information from content."""
    
    def __init__(self, config: Optional[SummaryConfig] = None):
        self.config = config or SummaryConfig()
        self.summaries: Dict[str, SummaryResult] = {}
    
    def summarize(
        self,
        content: str,
        style: Optional[SummaryStyle] = None,
        length: Optional[SummaryLength] = None,
        context: Optional[Dict] = None,
    ) -> SummaryResult:
        """
        Summarize content using specified style and length.
        
        Args:
            content: Text to summarize
            style: Summary style (defaults to config)
            length: Summary length (defaults to config)
            context: Optional context about content
        
        Returns:
            SummaryResult with summary and extracted information
        """
        style = style or self.config.style
        length = length or self.config.length
        
        content_id = self._generate_content_id()
        result = SummaryResult(
            content_id=content_id,
            original_length=len(content),
            summary_text="",
            style=style,
        )
        
        # Extract key information
        if self.config.extract_key_points:
            result.key_points = self._extract_key_points(content)
        
        if self.config.extract_topics:
            result.topics = self._extract_topics(content)
        
        if self.config.extract_entities:
            result.entities = self._extract_entities(content)
        
        # Generate summary based on style
        if style == SummaryStyle.BULLET_POINTS:
            result.summary_text = self._summarize_bullet_points(content, result.key_points)
        elif style == SummaryStyle.NARRATIVE:
            result.summary_text = self._summarize_narrative(content, result.key_points)
        elif style == SummaryStyle.TECHNICAL:
            result.summary_text = self._summarize_technical(content)
        elif style == SummaryStyle.EXECUTIVE:
            result.summary_text = self._summarize_executive(content, result.key_points)
        elif style == SummaryStyle.TIMELINE:
            result.summary_text = self._summarize_timeline(content)
        
        # Apply length constraints
        result.summary_text = self._apply_length_constraint(result.summary_text, length)
        
        # Calculate metrics
        result.summary_length = len(result.summary_text)
        result.compression_ratio = (
            (result.original_length - result.summary_length) / result.original_length
            if result.original_length > 0
            else 0.0
        )
        
        result.metadata = context or {}
        
        self.summaries[content_id] = result
        return result
    
    def _extract_key_points(self, content: str) -> List[KeyPoint]:
        """Extract key points from content."""
        sentences = self._split_sentences(content)
        
        # Score sentences
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = self._score_sentence(sentence, sentences)
            if len(sentence.strip()) > self.config.min_point_length:
                scored_sentences.append((sentence, score, i))
        
        # Sort by importance and take top N
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        top_points = scored_sentences[:self.config.target_key_points]
        
        # Sort back to original order
        top_points.sort(key=lambda x: x[2])
        
        # Create KeyPoint objects
        key_points = []
        for sentence, score, _ in top_points:
            point = KeyPoint(
                text=sentence.strip(),
                importance_score=min(1.0, score),
                supporting_details=self._find_supporting_details(sentence, content),
            )
            key_points.append(point)
        
        return key_points
    
    def _score_sentence(self, sentence: str, all_sentences: List[str]) -> float:
        """Score sentence importance."""
        score = 0.0
        
        # Length score (not too short, not too long)
        words = sentence.split()
        if 5 < len(words) < 30:
            score += 0.3
        
        # Position score (beginning and end are important)
        position_index = all_sentences.index(sentence) if sentence in all_sentences else 0
        if position_index < 3:
            score += 0.2
        
        # Keyword score (contains common important words)
        important_words = {
            'important', 'key', 'significant', 'critical', 'essential',
            'major', 'notable', 'main', 'primary', 'vital',
            'conclude', 'summary', 'result', 'finding'
        }
        sentence_lower = sentence.lower()
        keyword_count = sum(1 for word in important_words if word in sentence_lower)
        score += keyword_count * 0.15
        
        # Unique word score
        unique_words = set(word.lower() for word in sentence.split())
        if len(unique_words) > len(sentence.split()) * 0.6:
            score += 0.2
        
        return min(1.0, score)
    
    def _extract_topics(self, content: str) -> List[str]:
        """Extract main topics from content."""
        words = content.lower().split()
        
        # Filter words (remove stopwords and short words)
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'be', 'been',
            'have', 'has', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'it', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
        }
        
        filtered_words = [
            w.strip('.,!?;:') for w in words
            if len(w) > 4 and w.lower() not in stopwords and w.isalpha()
        ]
        
        # Find most common words (topics)
        word_freq = Counter(filtered_words)
        top_topics = [word for word, _ in word_freq.most_common(5)]
        
        return top_topics
    
    def _extract_entities(self, content: str) -> List[str]:
        """Extract named entities from content."""
        words = content.split()
        entities = []
        
        # Simple heuristic: capitalized multi-word phrases
        current_entity = []
        for word in words:
            if word and word[0].isupper() and word[0].isalpha():
                current_entity.append(word.rstrip('.,!?;:'))
            else:
                if current_entity and len(current_entity) > 1:
                    entity = ' '.join(current_entity)
                    if len(entity) > 4:
                        entities.append(entity)
                current_entity = []
        
        # Remove duplicates while preserving order
        seen = set()
        unique_entities = []
        for entity in entities:
            if entity not in seen:
                unique_entities.append(entity)
                seen.add(entity)
        
        return unique_entities[:10]  # Top 10 entities
    
    def _summarize_bullet_points(
        self,
        content: str,
        key_points: List[KeyPoint],
    ) -> str:
        """Generate bullet point summary."""
        if not key_points:
            return "• No key points identified"
        
        summary = ""
        for i, point in enumerate(key_points, 1):
            summary += f"• {point.text}\n"
        
        return summary.rstrip()
    
    def _summarize_narrative(
        self,
        content: str,
        key_points: List[KeyPoint],
    ) -> str:
        """Generate narrative summary."""
        if not key_points:
            return "Unable to generate narrative summary."
        
        # Convert key points to narrative form
        sentences = []
        for point in key_points:
            # Remove period and add context
            text = point.text.rstrip('.')
            sentences.append(text)
        
        # Join into paragraph
        summary = ". ".join(sentences) + "."
        
        return summary
    
    def _summarize_technical(self, content: str) -> str:
        """Generate technical summary."""
        sections = content.split('\n\n')
        
        summary_parts = []
        for section in sections[:3]:  # Take first 3 sections
            if section.strip():
                # Take first 2 sentences of each section
                sentences = self._split_sentences(section)
                if sentences:
                    summary_parts.append(sentences[0])
        
        return "\n\n".join(summary_parts) if summary_parts else content[:300]
    
    def _summarize_executive(
        self,
        content: str,
        key_points: List[KeyPoint],
    ) -> str:
        """Generate executive summary (high-level overview)."""
        summary = "Executive Summary:\n\n"
        
        if key_points:
            summary += "Key findings:\n"
            for point in key_points[:3]:  # Top 3 points
                summary += f"- {point.text}\n"
        
        return summary
    
    def _summarize_timeline(self, content: str) -> str:
        """Generate timeline summary."""
        # Look for temporal markers
        temporal_markers = [
            'first', 'initially', 'then', 'next', 'subsequently', 'finally',
            'before', 'after', 'earlier', 'later', 'meanwhile', 'today'
        ]
        
        sentences = self._split_sentences(content)
        timeline = []
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(marker in sentence_lower for marker in temporal_markers):
                timeline.append(sentence)
        
        if not timeline:
            # Fallback: use chronological order of paragraphs
            timeline = sentences[:5]
        
        return "\n".join(timeline) if timeline else content[:400]
    
    def _apply_length_constraint(self, text: str, length: SummaryLength) -> str:
        """Apply length constraint to summary."""
        if length == SummaryLength.FULL:
            return text
        
        # Define target word counts
        target_words = {
            SummaryLength.SHORT: 75,
            SummaryLength.MEDIUM: 150,
            SummaryLength.LONG: 400,
        }
        
        target = target_words.get(length, 150)
        words = text.split()
        
        if len(words) <= target:
            return text
        
        # Truncate to target length
        truncated = " ".join(words[:target])
        
        # Ensure we end at a sentence boundary
        last_period = truncated.rfind('.')
        if last_period > target * 0.8:  # If period is close to end
            truncated = truncated[:last_period + 1]
        
        return truncated
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting on periods, question marks, exclamation marks
        import re
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _find_supporting_details(self, key_point: str, content: str) -> List[str]:
        """Find supporting details for a key point."""
        details = []
        
        # Simple approach: find sentences near the key point in original content
        sentences = self._split_sentences(content)
        
        for i, sentence in enumerate(sentences):
            if key_point in sentence or sentence in key_point:
                # Add adjacent sentences as supporting details
                if i > 0 and sentences[i-1].strip():
                    details.append(sentences[i-1])
                if i < len(sentences) - 1 and sentences[i+1].strip():
                    details.append(sentences[i+1])
        
        return details[:2]  # Return max 2 details
    
    def _generate_content_id(self) -> str:
        """Generate unique content ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        return f"summary_{timestamp}"
    
    def get_summary(self, content_id: str) -> Optional[SummaryResult]:
        """Retrieve summary by content ID."""
        return self.summaries.get(content_id)
    
    def get_all_summaries(self) -> List[SummaryResult]:
        """Get all generated summaries."""
        return list(self.summaries.values())
    
    def batch_summarize(
        self,
        contents: List[str],
        style: Optional[SummaryStyle] = None,
        length: Optional[SummaryLength] = None,
    ) -> List[SummaryResult]:
        """Summarize multiple contents efficiently."""
        results = []
        for content in contents:
            result = self.summarize(content, style, length)
            results.append(result)
        
        return results
    
    def extract_briefing(self, content: str) -> SummaryResult:
        """Extract information for a briefing."""
        return self.summarize(
            content,
            style=SummaryStyle.BULLET_POINTS,
            length=SummaryLength.MEDIUM,
        )
    
    def extract_brief_report(self, content: str) -> SummaryResult:
        """Extract information for a brief report."""
        return self.summarize(
            content,
            style=SummaryStyle.EXECUTIVE,
            length=SummaryLength.LONG,
        )
    
    def compare_summaries(self, content_id1: str, content_id2: str) -> Dict:
        """Compare two summaries."""
        summary1 = self.summaries.get(content_id1)
        summary2 = self.summaries.get(content_id2)
        
        if not summary1 or not summary2:
            return {}
        
        return {
            "summary1_compression": summary1.compression_ratio,
            "summary2_compression": summary2.compression_ratio,
            "summary1_key_points": len(summary1.key_points),
            "summary2_key_points": len(summary2.key_points),
            "shared_topics": set(summary1.topics) & set(summary2.topics),
            "shared_entities": set(summary1.entities) & set(summary2.entities),
        }
