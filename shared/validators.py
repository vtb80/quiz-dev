"""
Validation Functions
Version: 2.2 - Added multiple_choice_multiple validation
"""

from typing import Tuple, List, Dict, Any
from shared.constants import (
    MIN_OPTIONS_MC,
    MIN_PAIRS_MATCHING,
    MIN_ITEMS_REORDERING,
    MIN_ANSWERS_FILL,
    MIN_SUBQUESTIONS_READING,
    MIN_CORRECT_ANSWERS_MCM
)


class QuestionValidator:
    """Validates question data"""
    
    @staticmethod
    def validate_multiple_choice(question_text: str, options: List[str], 
                                 correct_index: int) -> Tuple[bool, str]:
        """
        Validate multiple choice question
        Returns: (is_valid, error_message)
        """
        if not question_text or not question_text.strip():
            return False, "Question text is required"
        
        if len(options) < MIN_OPTIONS_MC:
            return False, f"Need at least {MIN_OPTIONS_MC} options"
        
        # Check for empty options
        for i, opt in enumerate(options):
            if not opt or not opt.strip():
                return False, f"Option {i} is empty"
        
        if correct_index < 0 or correct_index >= len(options):
            return False, f"Correct index must be between 0 and {len(options)-1}"
        
        return True, ""
    
    @staticmethod
    def validate_multiple_choice_multiple(question_text: str, options: List[str], 
                                         correct_indices: List[int]) -> Tuple[bool, str]:
        """
        Validate multiple choice question with multiple correct answers
        Returns: (is_valid, error_message)
        """
        if not question_text or not question_text.strip():
            return False, "Question text is required"
        
        if len(options) < MIN_OPTIONS_MC:
            return False, f"Need at least {MIN_OPTIONS_MC} options"
        
        # Check for empty options
        for i, opt in enumerate(options):
            if not opt or not opt.strip():
                return False, f"Option {i} is empty"
        
        # Validate correct indices
        if not correct_indices or len(correct_indices) < MIN_CORRECT_ANSWERS_MCM:
            return False, f"Need at least {MIN_CORRECT_ANSWERS_MCM} correct answer"
        
        if len(correct_indices) > len(options):
            return False, "Too many correct answers"
        
        # Check for duplicates
        if len(correct_indices) != len(set(correct_indices)):
            return False, "Duplicate correct answer indices found"
        
        # Check indices are in valid range
        for idx in correct_indices:
            if idx < 0 or idx >= len(options):
                return False, f"Correct index {idx} is out of range (0-{len(options)-1})"
        
        return True, ""
    
    @staticmethod
    def validate_true_false(question_text: str, correct: int) -> Tuple[bool, str]:
        """
        Validate true/false question
        Returns: (is_valid, error_message)
        """
        if not question_text or not question_text.strip():
            return False, "Question text is required"
        
        if correct not in [0, 1]:
            return False, "Correct answer must be 0 (True) or 1 (False)"
        
        return True, ""
    
    @staticmethod
    def validate_fill_in_blank(question_text: str, answers) -> Tuple[bool, str]:
        """
        Validate fill in the blank question
        Supports both old (list) and new (dict) formats
        Returns: (is_valid, error_message)
        """
        if not question_text or not question_text.strip():
            return False, "Question text is required"
        
        # Check format type
        is_multi_blank = isinstance(answers, dict)
        
        if is_multi_blank:
            # New multi-blank format validation
            return QuestionValidator._validate_multi_blank(question_text, answers)
        else:
            # Old single-blank format validation
            return QuestionValidator._validate_single_blank(answers)

    @staticmethod
    def _validate_single_blank(answers: List[str]) -> Tuple[bool, str]:
        """
        Validate single-blank format (old format)
        Args:
            answers: List of acceptable answers
        Returns: (is_valid, error_message)
        """
        if not isinstance(answers, list):
            return False, "Answers must be a list for single-blank questions"
        
        if len(answers) < MIN_ANSWERS_FILL:
            return False, f"Need at least {MIN_ANSWERS_FILL} acceptable answer"
        
        # Check for empty answers
        for i, ans in enumerate(answers):
            if not ans or not ans.strip():
                return False, f"Answer {i+1} is empty"
        
        return True, ""

        @staticmethod
        def _validate_multi_blank(question_text: str, answers: Dict[str, List[str]]) -> Tuple[bool, str]:
            """
            Validate multi-blank format (new format)
            Args:
                question_text: Question text with _Q1_, _Q2_ placeholders
                answers: Dict mapping blank IDs to lists of acceptable answers
            Returns: (is_valid, error_message)
            """
            import re
            from shared.constants import (
                MAX_BLANKS_FILL, 
                BLANK_PLACEHOLDER_PATTERN,
                BLANK_PLACEHOLDER_PREFIX,
                BLANK_PLACEHOLDER_SUFFIX
            )
            
            if not isinstance(answers, dict):
                return False, "Answers must be a dictionary for multi-blank questions"
            
            if len(answers) == 0:
                return False, "At least one blank is required"
            
            if len(answers) > MAX_BLANKS_FILL:
                return False, f"Maximum {MAX_BLANKS_FILL} blanks allowed, found {len(answers)}"
            
            # Extract blank IDs from question text
            placeholders_in_text = re.findall(BLANK_PLACEHOLDER_PATTERN, question_text)
            placeholder_ids = [f'Q{num}' for num in placeholders_in_text]
            
            if len(placeholder_ids) == 0:
                return False, f"No blanks found in question text. Use format: {BLANK_PLACEHOLDER_PREFIX}1{BLANK_PLACEHOLDER_SUFFIX}, {BLANK_PLACEHOLDER_PREFIX}2{BLANK_PLACEHOLDER_SUFFIX}, etc."
            
            # Get blank IDs from answers dict
            answer_blank_ids = list(answers.keys())
            
            # Check if all placeholders in text have corresponding answers
            for pid in placeholder_ids:
                if pid not in answer_blank_ids:
                    return False, f"Blank '{BLANK_PLACEHOLDER_PREFIX}{pid.replace('Q', '')}{BLANK_PLACEHOLDER_SUFFIX}' found in question text but no answers provided"
            
            # Check if all answers have corresponding placeholders in text
            for aid in answer_blank_ids:
                if aid not in placeholder_ids:
                    return False, f"Answers provided for '{BLANK_PLACEHOLDER_PREFIX}{aid.replace('Q', '')}{BLANK_PLACEHOLDER_SUFFIX}' but blank not found in question text"
            
            # Validate consecutive numbering (Q1, Q2, Q3... no gaps)
            blank_numbers = sorted([int(bid.replace('Q', '')) for bid in answer_blank_ids])
            expected_numbers = list(range(1, len(blank_numbers) + 1))
            
            if blank_numbers != expected_numbers:
                return False, f"Blank numbering must be consecutive starting from 1. Expected: Q{', Q'.join(map(str, expected_numbers))}, Found: Q{', Q'.join(map(str, blank_numbers))}"
            
            # Validate each blank's answers
            for blank_id, acceptable_answers in answers.items():
                if not isinstance(acceptable_answers, list):
                    return False, f"Answers for {BLANK_PLACEHOLDER_PREFIX}{blank_id.replace('Q', '')}{BLANK_PLACEHOLDER_SUFFIX} must be a list"
                
                if len(acceptable_answers) < MIN_ANSWERS_FILL:
                    return False, f"{BLANK_PLACEHOLDER_PREFIX}{blank_id.replace('Q', '')}{BLANK_PLACEHOLDER_SUFFIX} needs at least {MIN_ANSWERS_FILL} acceptable answer"
                
                # Check for empty answers
                for i, ans in enumerate(acceptable_answers):
                    if not ans or not ans.strip():
                        return False, f"{BLANK_PLACEHOLDER_PREFIX}{blank_id.replace('Q', '')}{BLANK_PLACEHOLDER_SUFFIX} answer {i+1} is empty"
            
            return True, ""
    
    @staticmethod
    def _validate_multi_blank(question_text: str, answers: Dict[str, List[str]]) -> Tuple[bool, str]:
        """
        Validate multi-blank format (new format)
        Args:
            question_text: Question text with _Q1_, _Q2_ placeholders
            answers: Dict mapping blank IDs to lists of acceptable answers
        Returns: (is_valid, error_message)
        """
        import re
        from shared.constants import (
            MAX_BLANKS_FILL, 
            BLANK_PLACEHOLDER_PATTERN,
            BLANK_PLACEHOLDER_PREFIX,
            BLANK_PLACEHOLDER_SUFFIX
        )
        
        if not isinstance(answers, dict):
            return False, "Answers must be a dictionary for multi-blank questions"
        
        if len(answers) == 0:
            return False, "At least one blank is required"
        
        if len(answers) > MAX_BLANKS_FILL:
            return False, f"Maximum {MAX_BLANKS_FILL} blanks allowed, found {len(answers)}"
        
        # Extract blank IDs from question text
        placeholders_in_text = re.findall(BLANK_PLACEHOLDER_PATTERN, question_text)
        placeholder_ids = [f'Q{num}' for num in placeholders_in_text]
        
        if len(placeholder_ids) == 0:
            return False, f"No blanks found in question text. Use format: {BLANK_PLACEHOLDER_PREFIX}1{BLANK_PLACEHOLDER_SUFFIX}, {BLANK_PLACEHOLDER_PREFIX}2{BLANK_PLACEHOLDER_SUFFIX}, etc."
        
        # Get blank IDs from answers dict
        answer_blank_ids = list(answers.keys())
        
        # Check if all placeholders in text have corresponding answers
        for pid in placeholder_ids:
            if pid not in answer_blank_ids:
                return False, f"Blank '{BLANK_PLACEHOLDER_PREFIX}{pid.replace('Q', '')}{BLANK_PLACEHOLDER_SUFFIX}' found in question text but no answers provided"
        
        # Check if all answers have corresponding placeholders in text
        for aid in answer_blank_ids:
            if aid not in placeholder_ids:
                return False, f"Answers provided for '{BLANK_PLACEHOLDER_PREFIX}{aid.replace('Q', '')}{BLANK_PLACEHOLDER_SUFFIX}' but blank not found in question text"
        
        # Validate consecutive numbering (Q1, Q2, Q3... no gaps)
        blank_numbers = sorted([int(bid.replace('Q', '')) for bid in answer_blank_ids])
        expected_numbers = list(range(1, len(blank_numbers) + 1))
        
        if blank_numbers != expected_numbers:
            return False, f"Blank numbering must be consecutive starting from 1. Expected: Q{', Q'.join(map(str, expected_numbers))}, Found: Q{', Q'.join(map(str, blank_numbers))}"
        
        # Validate each blank's answers
        for blank_id, acceptable_answers in answers.items():
            if not isinstance(acceptable_answers, list):
                return False, f"Answers for {BLANK_PLACEHOLDER_PREFIX}{blank_id.replace('Q', '')}{BLANK_PLACEHOLDER_SUFFIX} must be a list"
            
            if len(acceptable_answers) < MIN_ANSWERS_FILL:
                return False, f"{BLANK_PLACEHOLDER_PREFIX}{blank_id.replace('Q', '')}{BLANK_PLACEHOLDER_SUFFIX} needs at least {MIN_ANSWERS_FILL} acceptable answer"
            
            # Check for empty answers
            for i, ans in enumerate(acceptable_answers):
                if not ans or not ans.strip():
                    return False, f"{BLANK_PLACEHOLDER_PREFIX}{blank_id.replace('Q', '')}{BLANK_PLACEHOLDER_SUFFIX} answer {i+1} is empty"
        
        return True, ""
    
    @staticmethod
    def validate_matching(question_text: str, pairs: List[Dict[str, str]]) -> Tuple[bool, str]:
        """
        Validate matching question
        Returns: (is_valid, error_message)
        """
        if not question_text or not question_text.strip():
            return False, "Question text is required"
        
        if len(pairs) < MIN_PAIRS_MATCHING:
            return False, f"Need at least {MIN_PAIRS_MATCHING} pairs"
        
        # Check each pair
        for i, pair in enumerate(pairs):
            if not pair.get('country') or not pair.get('country').strip():
                return False, f"Pair {i+1} left side is empty"
            if not pair.get('capital') or not pair.get('capital').strip():
                return False, f"Pair {i+1} right side is empty"
            if not pair.get('id'):
                return False, f"Pair {i+1} missing ID"
        
        return True, ""
    
    @staticmethod
    def validate_reordering(question_text: str, items: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Validate reordering question
        Returns: (is_valid, error_message)
        """
        if not question_text or not question_text.strip():
            return False, "Question text is required"
        
        if len(items) < MIN_ITEMS_REORDERING:
            return False, f"Need at least {MIN_ITEMS_REORDERING} items"
        
        # Check each item
        for i, item in enumerate(items):
            if not item.get('text') or not item.get('text').strip():
                return False, f"Item {i+1} text is empty"
            if 'order' not in item:
                return False, f"Item {i+1} missing order"
        
        return True, ""
    
    @staticmethod
    def validate_reading_comprehension(passage_text: str, 
                                       sub_questions: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Validate reading comprehension question
        Returns: (is_valid, error_message)
        """
        if not passage_text or not passage_text.strip():
            return False, "Passage text is required"
        
        if len(sub_questions) < MIN_SUBQUESTIONS_READING:
            return False, f"Need at least {MIN_SUBQUESTIONS_READING} sub-question"
        
        # Check each sub-question
        for i, sq in enumerate(sub_questions):
            if not sq.get('question') or not sq.get('question').strip():
                return False, f"Sub-question {i+1} text is empty"
            
            options = sq.get('options', [])
            if len(options) < MIN_OPTIONS_MC:
                return False, f"Sub-question {i+1} needs at least {MIN_OPTIONS_MC} options"
            
            for j, opt in enumerate(options):
                if not opt or not opt.strip():
                    return False, f"Sub-question {i+1}, option {j} is empty"
            
            correct = sq.get('correct')
            if correct is None or correct < 0 or correct >= len(options):
                return False, f"Sub-question {i+1} has invalid correct answer"
        
        return True, ""
    
    @staticmethod
    def validate_question_by_type(question_type: str, **kwargs) -> Tuple[bool, str]:
        """
        Validate question based on type
        Returns: (is_valid, error_message)
        """
        validators = {
            'multiple_choice': QuestionValidator.validate_multiple_choice,
            'multiple_choice_multiple': QuestionValidator.validate_multiple_choice_multiple,
            'true_false': QuestionValidator.validate_true_false,
            'fill_in_blank': QuestionValidator.validate_fill_in_blank,
            'matching': QuestionValidator.validate_matching,
            'reordering': QuestionValidator.validate_reordering,
            'reading_comprehension': QuestionValidator.validate_reading_comprehension
        }
        
        validator = validators.get(question_type)
        if not validator:
            return False, f"Unknown question type: {question_type}"
        
        try:
            return validator(**kwargs)
        except Exception as e:
            return False, f"Validation error: {str(e)}"


class LessonValidator:
    """Validates lesson data"""
    
    @staticmethod
    def validate_lesson_name(name: str, existing_names: List[str] = None) -> Tuple[bool, str]:
        """
        Validate lesson name
        Returns: (is_valid, error_message)
        """
        if not name or not name.strip():
            return False, "Lesson name cannot be empty"
        
        if len(name) > 100:
            return False, "Lesson name too long (max 100 characters)"
        
        if existing_names and name in existing_names:
            return False, "Lesson name already exists"
        
        return True, ""
    
    @staticmethod
    def validate_lesson_id(lesson_id: str) -> Tuple[bool, str]:
        """
        Validate lesson ID format
        Returns: (is_valid, error_message)
        """
        if not lesson_id or not lesson_id.strip():
            return False, "Lesson ID cannot be empty"
        
        if len(lesson_id) > 10:
            return False, "Lesson ID too long (max 10 characters)"
        
        return True, ""


class SubjectValidator:
    """Validates subject data"""
    
    @staticmethod
    def validate_subject_name(name: str) -> Tuple[bool, str]:
        """
        Validate subject name
        Returns: (is_valid, error_message)
        """
        if not name or not name.strip():
            return False, "Subject name cannot be empty"
        
        # Check for invalid characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in invalid_chars:
            if char in name:
                return False, f"Subject name cannot contain '{char}'"
        
        if len(name) > 50:
            return False, "Subject name too long (max 50 characters)"
        
        return True, ""
