"""
Critic Agent - Quality Assurance and Content Review

Evaluates content quality, identifies issues, and provides recommendations.
Acts as QA checkpoint for agent-generated outputs.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SeverityLevel(str, Enum):
    """Issue severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IssueCategory(str, Enum):
    """Categories of issues that can be found."""
    ACCURACY = "accuracy"  # Factual correctness
    COMPLETENESS = "completeness"  # Missing information
    CLARITY = "clarity"  # Understandability
    RELEVANCE = "relevance"  # Topic alignment
    CONSISTENCY = "consistency"  # Internal contradiction
    QUALITY = "quality"  # General quality
    FORMATTING = "formatting"  # Structure/presentation
    GRAMMAR = "grammar"  # Language correctness


@dataclass
class Issue:
    """Represents a detected issue with suggested fix."""
    category: IssueCategory
    severity: SeverityLevel
    description: str
    location: Optional[str] = None  # Where in content (e.g., "paragraph 3")
    suggestion: Optional[str] = None  # How to fix
    affected_text: Optional[str] = None  # The problematic text
    confidence: float = 0.8  # Confidence in issue detection (0-1)
    
    def to_dict(self):
        return asdict(self)


@dataclass
class ReviewResult:
    """Result of content review."""
    content_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    overall_quality_score: float = 0.0  # 0-1, higher is better
    issues: List[Issue] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    is_approved: bool = False
    review_summary: str = ""
    reviewer_notes: str = ""
    
    def to_dict(self):
        return {
            "content_id": self.content_id,
            "timestamp": self.timestamp.isoformat(),
            "overall_quality_score": self.overall_quality_score,
            "issues": [issue.to_dict() for issue in self.issues],
            "recommendations": self.recommendations,
            "is_approved": self.is_approved,
            "review_summary": self.review_summary,
            "reviewer_notes": self.reviewer_notes,
        }


@dataclass
class CriticConfig:
    """Configuration for critic behavior."""
    check_accuracy: bool = True
    check_completeness: bool = True
    check_clarity: bool = True
    check_relevance: bool = True
    check_consistency: bool = True
    check_formatting: bool = True
    check_grammar: bool = False  # Expensive operation
    require_sources: bool = True
    min_quality_score: float = 0.7  # Minimum score for approval
    max_errors_allowed: int = 3
    max_warnings_allowed: int = 5


class CriticAgent:
    """Reviews and critiques content for quality assurance."""
    
    def __init__(self, config: Optional[CriticConfig] = None):
        self.config = config or CriticConfig()
        self.reviews: Dict[str, ReviewResult] = {}
    
    def review(
        self,
        content: str,
        content_type: str = "text",
        context: Optional[Dict] = None,
        source_references: Optional[List[str]] = None,
    ) -> ReviewResult:
        """
        Review content for quality and issues.
        
        Args:
            content: The text content to review
            content_type: Type of content (text, code, summary, etc.)
            context: Optional context about the content
            source_references: Optional list of sources used
        
        Returns:
            ReviewResult with issues and recommendations
        """
        content_id = self._generate_content_id()
        result = ReviewResult(content_id=content_id)
        
        # Run checks based on configuration
        if self.config.check_accuracy:
            result.issues.extend(self._check_accuracy(content, source_references or []))
        
        if self.config.check_completeness:
            result.issues.extend(self._check_completeness(content, context or {}))
        
        if self.config.check_clarity:
            result.issues.extend(self._check_clarity(content))
        
        if self.config.check_relevance:
            result.issues.extend(self._check_relevance(content, context or {}))
        
        if self.config.check_consistency:
            result.issues.extend(self._check_consistency(content))
        
        if self.config.check_formatting:
            result.issues.extend(self._check_formatting(content, content_type))
        
        if self.config.check_grammar:
            result.issues.extend(self._check_grammar(content))
        
        # Calculate quality score
        result.overall_quality_score = self._calculate_quality_score(result)
        
        # Determine approval
        error_count = sum(1 for i in result.issues if i.severity == SeverityLevel.ERROR)
        warning_count = sum(1 for i in result.issues if i.severity == SeverityLevel.WARNING)
        
        result.is_approved = (
            result.overall_quality_score >= self.config.min_quality_score
            and error_count <= self.config.max_errors_allowed
            and warning_count <= self.config.max_warnings_allowed
        )
        
        # Generate summary
        result.review_summary = self._generate_summary(result)
        
        self.reviews[content_id] = result
        return result
    
    def _check_accuracy(
        self,
        content: str,
        source_references: List[str],
    ) -> List[Issue]:
        """Check factual accuracy of content."""
        issues = []
        
        # Check if sources are provided for claims
        if self.config.require_sources and not source_references:
            issues.append(Issue(
                category=IssueCategory.ACCURACY,
                severity=SeverityLevel.WARNING,
                description="No source references provided for content claims",
                suggestion="Add references to source documents that support the claims",
                confidence=0.9,
            ))
        
        # Check for unsupported statements
        if len(content) > 100 and len(source_references) < 2:
            issues.append(Issue(
                category=IssueCategory.ACCURACY,
                severity=SeverityLevel.WARNING,
                description="Content is substantial but has few source references",
                suggestion="Add more source citations to support statements",
                confidence=0.7,
            ))
        
        return issues
    
    def _check_completeness(
        self,
        content: str,
        context: Dict,
    ) -> List[Issue]:
        """Check if content is complete and covers key points."""
        issues = []
        
        if len(content) < 100:
            issues.append(Issue(
                category=IssueCategory.COMPLETENESS,
                severity=SeverityLevel.WARNING,
                description="Content appears to be very brief",
                suggestion="Expand with more detail and explanations",
                confidence=0.6,
            ))
        
        # Check for common missing sections
        content_lower = content.lower()
        missing_sections = []
        
        if "summary" not in context.get("content_type", "").lower():
            if "context" not in content_lower and "background" not in content_lower:
                missing_sections.append("background context")
        
        if "conclusion" not in content_lower and len(content) > 500:
            missing_sections.append("conclusion")
        
        if missing_sections:
            issues.append(Issue(
                category=IssueCategory.COMPLETENESS,
                severity=SeverityLevel.INFO,
                description=f"Missing sections: {', '.join(missing_sections)}",
                suggestion="Consider adding the missing sections for completeness",
                confidence=0.7,
            ))
        
        return issues
    
    def _check_clarity(self, content: str) -> List[Issue]:
        """Check clarity and readability of content."""
        issues = []
        
        # Check sentence length
        sentences = content.split('.')
        long_sentences = [s for s in sentences if len(s.split()) > 25]
        
        if len(long_sentences) > len(sentences) * 0.3:  # More than 30% long sentences
            issues.append(Issue(
                category=IssueCategory.CLARITY,
                severity=SeverityLevel.WARNING,
                description="Many sentences are overly long and complex",
                affected_text=long_sentences[0][:100] if long_sentences else None,
                suggestion="Break long sentences into shorter, simpler ones",
                confidence=0.7,
            ))
        
        # Check for jargon without explanation
        technical_terms = self._find_technical_terms(content)
        if technical_terms:
            issues.append(Issue(
                category=IssueCategory.CLARITY,
                severity=SeverityLevel.INFO,
                description=f"Technical terms used: {', '.join(technical_terms[:3])}",
                suggestion="Ensure technical terms are explained or accessible to audience",
                confidence=0.6,
            ))
        
        return issues
    
    def _check_relevance(self, content: str, context: Dict) -> List[Issue]:
        """Check if content is relevant to stated goal."""
        issues = []
        
        goal = context.get("goal", "")
        if not goal:
            return issues
        
        # Simple keyword matching
        goal_words = set(goal.lower().split())
        content_words = set(content.lower().split())
        
        overlap = goal_words & content_words
        if len(overlap) < len(goal_words) * 0.3:  # Less than 30% overlap
            issues.append(Issue(
                category=IssueCategory.RELEVANCE,
                severity=SeverityLevel.WARNING,
                description="Content may not fully address the stated goal",
                suggestion="Ensure content directly addresses: " + goal,
                confidence=0.6,
            ))
        
        return issues
    
    def _check_consistency(self, content: str) -> List[Issue]:
        """Check for internal consistency and contradictions."""
        issues = []
        
        # Simple contradiction detection
        if "however" in content.lower() or "but" in content.lower():
            # This is a simplification - real implementation would be more sophisticated
            issues.append(Issue(
                category=IssueCategory.CONSISTENCY,
                severity=SeverityLevel.INFO,
                description="Content contains contrasting statements",
                suggestion="Ensure contrasting points are clearly explained and justified",
                confidence=0.5,
            ))
        
        return issues
    
    def _check_formatting(self, content: str, content_type: str) -> List[Issue]:
        """Check formatting and structure."""
        issues = []
        
        lines = content.split('\n')
        
        # Check for consistent structure
        if len(lines) > 5:
            # Check for paragraphs
            single_line_length = [len(l) for l in lines]
            very_long_lines = sum(1 for l in single_line_length if l > 150)
            
            if very_long_lines > len(lines) * 0.5:
                issues.append(Issue(
                    category=IssueCategory.FORMATTING,
                    severity=SeverityLevel.INFO,
                    description="Lines are very long and difficult to read",
                    suggestion="Add line breaks and formatting to improve readability",
                    confidence=0.6,
                ))
        
        # Check for proper spacing
        if "  " in content:  # Double spaces
            issues.append(Issue(
                category=IssueCategory.FORMATTING,
                severity=SeverityLevel.WARNING,
                description="Multiple consecutive spaces found",
                suggestion="Remove extra spaces for cleaner formatting",
                confidence=0.9,
            ))
        
        return issues
    
    def _check_grammar(self, content: str) -> List[Issue]:
        """Check grammar and language correctness."""
        issues = []
        
        # Note: This is a simplified check. Real implementation would use NLP library
        common_mistakes = {
            "it's": ("its", "Use 'its' for possessive"),
            "there": ("their/they're", "Check usage of there/their/they're"),
            "alot": ("a lot", "Use 'a lot' (two words)"),
        }
        
        for mistake, (correction, tip) in common_mistakes.items():
            if mistake in content.lower():
                issues.append(Issue(
                    category=IssueCategory.GRAMMAR,
                    severity=SeverityLevel.WARNING,
                    description=f"Potential grammar issue: {mistake}",
                    suggestion=f"{tip}. Consider: {correction}",
                    confidence=0.6,
                ))
        
        return issues
    
    def _calculate_quality_score(self, result: ReviewResult) -> float:
        """Calculate overall quality score (0-1)."""
        if not result.issues:
            return 1.0
        
        # Score calculation
        score = 1.0
        
        # Deduct points for issues
        critical_count = sum(1 for i in result.issues if i.severity == SeverityLevel.CRITICAL)
        error_count = sum(1 for i in result.issues if i.severity == SeverityLevel.ERROR)
        warning_count = sum(1 for i in result.issues if i.severity == SeverityLevel.WARNING)
        info_count = sum(1 for i in result.issues if i.severity == SeverityLevel.INFO)
        
        score -= critical_count * 0.25
        score -= error_count * 0.15
        score -= warning_count * 0.05
        score -= info_count * 0.01
        
        # Apply confidence weighting
        for issue in result.issues:
            score -= (1 - issue.confidence) * 0.02
        
        return max(0.0, min(1.0, score))
    
    def _generate_summary(self, result: ReviewResult) -> str:
        """Generate human-readable review summary."""
        if result.is_approved:
            return f"✓ Approved. Quality score: {result.overall_quality_score:.1%}. "
        else:
            return f"✗ Needs revision. Quality score: {result.overall_quality_score:.1%}. "
        
        issue_summary = []
        for severity in [SeverityLevel.CRITICAL, SeverityLevel.ERROR, SeverityLevel.WARNING]:
            count = sum(1 for i in result.issues if i.severity == severity)
            if count > 0:
                issue_summary.append(f"{count} {severity.value}(s)")
        
        if issue_summary:
            return result.review_summary + "Issues: " + ", ".join(issue_summary)
        
        return result.review_summary + "No major issues found."
    
    def _find_technical_terms(self, content: str) -> List[str]:
        """Identify technical terms in content."""
        # Simplified: look for capitalized words and common technical patterns
        words = content.split()
        technical = []
        
        for word in words:
            if word[0].isupper() and len(word) > 5:
                technical.append(word)
        
        return list(set(technical[:5]))  # Return top 5 unique terms
    
    def _generate_content_id(self) -> str:
        """Generate unique content ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
        return f"review_{timestamp}"
    
    def get_review(self, content_id: str) -> Optional[ReviewResult]:
        """Retrieve review by content ID."""
        return self.reviews.get(content_id)
    
    def get_all_reviews(self) -> List[ReviewResult]:
        """Get all reviews."""
        return list(self.reviews.values())
    
    def get_approved_reviews(self) -> List[ReviewResult]:
        """Get only approved reviews."""
        return [r for r in self.reviews.values() if r.is_approved]
    
    def get_failed_reviews(self) -> List[ReviewResult]:
        """Get reviews that failed approval."""
        return [r for r in self.reviews.values() if not r.is_approved]
    
    def suggest_improvements(self, content_id: str) -> List[str]:
        """Get improvement suggestions for specific review."""
        review = self.reviews.get(content_id)
        if not review:
            return []
        
        suggestions = review.recommendations.copy()
        
        # Add suggestions from issues
        for issue in review.issues:
            if issue.suggestion:
                suggestions.append(f"[{issue.category.value}] {issue.suggestion}")
        
        return suggestions
