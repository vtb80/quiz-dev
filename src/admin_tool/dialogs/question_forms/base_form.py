"""
Base Form for Question Types
Abstract base class for question form implementations
Version: 1.0
"""

from abc import ABC, abstractmethod
import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any, Tuple

from shared.models import Subject, Question


class BaseQuestionForm(ABC):
    """Abstract base class for question type forms"""
    
    def __init__(self, parent_frame: ttk.Frame, subject: Subject, 
                 lesson_id: Optional[str], mode: str, question: Optional[Question] = None):
        """
        Initialize base form
        
        Args:
            parent_frame: Parent frame to render form in
            subject: Subject object
            lesson_id: Initial lesson ID assignment
            mode: 'add' or 'edit'
            question: Question object (for edit mode)
        """
        self.parent_frame = parent_frame
        self.subject = subject
        self.lesson_id = lesson_id
        self.mode = mode
        self.question = question
        
        # Common attributes
        self.temp_image_paths = {}
        self.image_controls = {}
        
    @abstractmethod
    def render(self):
        """
        Render the form UI
        Must be implemented by subclass
        """
        pass
    
    @abstractmethod
    def load_data(self):
        """
        Load data from question object (edit mode)
        Must be implemented by subclass
        """
        pass
    
    @abstractmethod
    def collect_data(self) -> Optional[Dict[str, Any]]:
        """
        Collect data from form UI
        
        Returns:
            Dict with form data, or None if collection fails
        """
        pass
    
    @abstractmethod
    def validate(self) -> Tuple[bool, str]:
        """
        Validate form data
        
        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        pass
    
    def get_lesson_id(self) -> Optional[str]:
        """
        Get the lesson ID for this question
        
        Returns:
            Lesson ID or None
        """
        return self.lesson_id
    
    def cleanup(self):
        """
        Cleanup resources (optional override)
        Called when form is destroyed
        """
        pass
    
    def clear(self):
        """Clear all widgets from parent frame"""
        for widget in self.parent_frame.winfo_children():
            widget.destroy()
        self.image_controls.clear()
        self.temp_image_paths.clear()
