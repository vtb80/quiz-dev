"""
True/False Question Form
Handles creation and editing of true/false questions
Version: 1.0
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any, Tuple

from shared.models import Subject, Question, TrueFalseQuestion
from shared.validators import QuestionValidator
from admin_tool.dialogs.question_forms.base_form import BaseQuestionForm


class TrueFalseForm(BaseQuestionForm):
    """Form for True/False questions"""
    
    def __init__(self, parent_frame: ttk.Frame, subject: Subject, 
                 lesson_id: Optional[str], mode: str, question: Optional[TrueFalseQuestion] = None):
        super().__init__(parent_frame, subject, lesson_id, mode, question)
        
        # Render and load
        self.render()
        if mode == "edit" and question:
            self.load_data()
    
    def render(self):
        """Render True/False form"""
        # Question text
        ttk.Label(self.parent_frame, text="Question:", font=('', 10, 'bold')).pack(anchor=tk.W, pady=(5, 0))
        self.question_text = tk.Text(self.parent_frame, height=5, font=('', 10))
        self.question_text.pack(fill=tk.X, pady=5)
        
        # Answer selection
        ttk.Label(self.parent_frame, text="Answer:", font=('', 10, 'bold')).pack(anchor=tk.W, pady=(15, 5))
        
        self.correct_var = tk.StringVar(value="0")
        ttk.Radiobutton(self.parent_frame, text="True", variable=self.correct_var, 
                       value="0").pack(anchor=tk.W, pady=2)
        ttk.Radiobutton(self.parent_frame, text="False", variable=self.correct_var, 
                       value="1").pack(anchor=tk.W, pady=2)
    
    def load_data(self):
        """Load data from question object (edit mode)"""
        if not self.question:
            return
        
        # Load question text
        self.question_text.insert('1.0', self.question.question)
        
        # Load correct answer
        self.correct_var.set(str(self.question.correct))
    
    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect data from form"""
        try:
            data = {}
            
            # Question text
            data['question'] = self.question_text.get('1.0', tk.END).strip()
            
            # Correct answer
            data['correct'] = int(self.correct_var.get())
            
            return data
            
        except Exception as e:
            print(f"Error collecting data: {str(e)}")
            return None
    
    def validate(self) -> Tuple[bool, str]:
        """Validate form data"""
        question_text = self.question_text.get('1.0', tk.END).strip()
        
        if not question_text:
            return False, "Question text is required"
        
        # Validate correct answer
        try:
            correct = int(self.correct_var.get())
            if correct not in [0, 1]:
                return False, "Correct answer must be 0 (True) or 1 (False)"
        except ValueError:
            return False, "Invalid correct answer"
        
        return True, ""
