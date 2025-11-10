"""
Data Models for Quiz Application
Version: 2.1
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from shared.constants import DEFAULT_IMAGE_SCALE, DEFAULT_LESSON_ID_PREFIX


@dataclass
class Lesson:
    """Represents a lesson within a subject"""
    id: str
    name: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON storage"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Lesson':
        """Create from dictionary"""
        return cls(
            id=data.get('id', ''),
            name=data.get('name', '')
        )
    
    def __str__(self):
        return f"{self.name} ({self.id})"


@dataclass
class Question:
    """Base question class"""
    id: int
    type: str
    lessonId: Optional[str] = None
    questionImage: Optional[str] = None
    questionImageScale: int = DEFAULT_IMAGE_SCALE
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON storage"""
        data = asdict(self)
        # Remove None values
        return {k: v for k, v in data.items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Question':
        """Create from dictionary - override in subclasses"""
        qtype = data.get('type', 'multiple_choice')
        
        # Route to appropriate subclass
        if qtype == 'multiple_choice':
            return MultipleChoiceQuestion.from_dict(data)
        elif qtype == 'true_false':
            return TrueFalseQuestion.from_dict(data)
        elif qtype == 'fill_in_blank':
            return FillInBlankQuestion.from_dict(data)
        elif qtype == 'matching':
            return MatchingQuestion.from_dict(data)
        elif qtype == 'reordering':
            return ReorderingQuestion.from_dict(data)
        elif qtype == 'reading_comprehension':
            return ReadingComprehensionQuestion.from_dict(data)
        else:
            # Generic question - create with explicit type
            return Question(
                id=data.get('id', 0),
                type=qtype,
                lessonId=data.get('lessonId'),
                questionImage=data.get('questionImage'),
                questionImageScale=data.get('questionImageScale', DEFAULT_IMAGE_SCALE)
            )


@dataclass
class MultipleChoiceQuestion(Question):
    """Multiple choice question"""
    question: str = ""
    options: List[str] = field(default_factory=list)
    correct: int = 0
    optionImages: Optional[Dict[str, str]] = None
    optionImageScale: int = DEFAULT_IMAGE_SCALE
    
    def __post_init__(self):
        # Ensure type is set
        object.__setattr__(self, 'type', 'multiple_choice')
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MultipleChoiceQuestion':
        return cls(
            id=data.get('id', 0),
            type='multiple_choice',
            lessonId=data.get('lessonId'),
            questionImage=data.get('questionImage'),
            questionImageScale=data.get('questionImageScale', DEFAULT_IMAGE_SCALE),
            question=data.get('question', ''),
            options=data.get('options', []),
            correct=data.get('correct', 0),
            optionImages=data.get('optionImages'),
            optionImageScale=data.get('optionImageScale', DEFAULT_IMAGE_SCALE)
        )


@dataclass
class TrueFalseQuestion(Question):
    """True/False question"""
    question: str = ""
    correct: int = 0  # 0=True, 1=False
    
    def __post_init__(self):
        self.type = 'true_false'
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TrueFalseQuestion':
        return cls(
            id=data.get('id', 0),
            type='true_false',
            lessonId=data.get('lessonId'),
            questionImage=data.get('questionImage'),
            questionImageScale=data.get('questionImageScale', DEFAULT_IMAGE_SCALE),
            question=data.get('question', ''),
            correct=data.get('correct', 0)
        )


@dataclass
class FillInBlankQuestion(Question):
    """Fill in the blank question"""
    question: str = ""
    correct: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        self.type = 'fill_in_blank'
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FillInBlankQuestion':
        return cls(
            id=data.get('id', 0),
            type='fill_in_blank',
            lessonId=data.get('lessonId'),
            questionImage=data.get('questionImage'),
            questionImageScale=data.get('questionImageScale', DEFAULT_IMAGE_SCALE),
            question=data.get('question', ''),
            correct=data.get('correct', [])
        )


@dataclass
class MatchingPair:
    """A single matching pair"""
    country: str
    capital: str
    id: str
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class MatchingQuestion(Question):
    """Matching question"""
    question: str = ""
    pairs: List[Dict[str, str]] = field(default_factory=list)
    correct: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        self.type = 'matching'
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MatchingQuestion':
        return cls(
            id=data.get('id', 0),
            type='matching',
            lessonId=data.get('lessonId'),
            questionImage=data.get('questionImage'),
            questionImageScale=data.get('questionImageScale', DEFAULT_IMAGE_SCALE),
            question=data.get('question', ''),
            pairs=data.get('pairs', []),
            correct=data.get('correct', {})
        )


@dataclass
class ReorderingItem:
    """A single item to reorder"""
    text: str
    order: int
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ReorderingQuestion(Question):
    """Reordering question"""
    question: str = ""
    items: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        self.type = 'reordering'
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ReorderingQuestion':
        return cls(
            id=data.get('id', 0),
            type='reordering',
            lessonId=data.get('lessonId'),
            questionImage=data.get('questionImage'),
            questionImageScale=data.get('questionImageScale', DEFAULT_IMAGE_SCALE),
            question=data.get('question', ''),
            items=data.get('items', [])
        )


@dataclass
class SubQuestion:
    """Sub-question for reading comprehension"""
    id: str
    question: str
    options: List[str]
    correct: int
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ReadingComprehensionQuestion(Question):
    """Reading comprehension question"""
    passage: str = ""
    passageId: str = ""
    questions: List[Dict[str, Any]] = field(default_factory=list)
    
    def __post_init__(self):
        self.type = 'reading_comprehension'
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ReadingComprehensionQuestion':
        return cls(
            id=data.get('id', 0),
            type='reading_comprehension',
            lessonId=data.get('lessonId'),
            questionImage=data.get('questionImage'),
            questionImageScale=data.get('questionImageScale', DEFAULT_IMAGE_SCALE),
            passage=data.get('passage', ''),
            passageId=data.get('passageId', ''),
            questions=data.get('questions', [])
        )


@dataclass
class Subject:
    """Represents a subject with its lessons and questions"""
    name: str
    filename: str
    lessons: List[Lesson] = field(default_factory=list)
    questions: List[Question] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to JSON structure"""
        return {
            'lessons': [lesson.to_dict() for lesson in self.lessons],
            'questions': [q.to_dict() for q in self.questions]
        }
    
    @classmethod
    def from_dict(cls, name: str, filename: str, data: dict) -> 'Subject':
        """Create from JSON data"""
        lessons = [Lesson.from_dict(l) for l in data.get('lessons', [])]
        questions = [Question.from_dict(q) for q in data.get('questions', [])]
        
        return cls(
            name=name,
            filename=filename,
            lessons=lessons,
            questions=questions
        )
    
    def get_lesson_by_id(self, lesson_id: str) -> Optional[Lesson]:
        """Find lesson by ID"""
        return next((l for l in self.lessons if l.id == lesson_id), None)
    
    def get_question_by_id(self, question_id: int) -> Optional[Question]:
        """Find question by ID"""
        return next((q for q in self.questions if q.id == question_id), None)
    
    def get_questions_by_lesson(self, lesson_id: Optional[str]) -> List[Question]:
        """Get all questions for a lesson"""
        return [q for q in self.questions if q.lessonId == lesson_id]
    
    def get_next_question_id(self) -> int:
        """Get next available question ID"""
        if not self.questions:
            return 1
        return max(q.id for q in self.questions) + 1
    
    def get_next_lesson_id(self) -> str:
        """Get next available lesson ID"""
        if not self.lessons:
            return f"{DEFAULT_LESSON_ID_PREFIX}001"
        
        # Extract numbers from existing IDs
        numbers = []
        for lesson in self.lessons:
            try:
                num = int(lesson.id.replace(DEFAULT_LESSON_ID_PREFIX, ''))
                numbers.append(num)
            except:
                pass
        
        next_num = max(numbers) + 1 if numbers else 1
        return f"{DEFAULT_LESSON_ID_PREFIX}{str(next_num).zfill(3)}"
    
    def add_lesson(self, lesson: Lesson):
        """Add a lesson"""
        self.lessons.append(lesson)
    
    def remove_lesson(self, lesson_id: str):
        """Remove a lesson and unassign its questions"""
        self.lessons = [l for l in self.lessons if l.id != lesson_id]
        # Move questions to Others
        for q in self.questions:
            if q.lessonId == lesson_id:
                q.lessonId = None
    
    def add_question(self, question: Question):
        """Add a question"""
        self.questions.append(question)
    
    def remove_question(self, question_id: int):
        """Remove a question"""
        self.questions = [q for q in self.questions if q.id != question_id]
    
    def update_question(self, question_id: int, updated_question: Question):
        """Update a question"""
        for i, q in enumerate(self.questions):
            if q.id == question_id:
                self.questions[i] = updated_question
                break