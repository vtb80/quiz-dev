"""
Matching Question Form
Handles creation and editing of matching questions
Version: 1.0
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any, Tuple

from shared.models import Subject, Question, MatchingQuestion
from shared.validators import QuestionValidator
from admin_tool.dialogs.question_forms.base_form import BaseQuestionForm


class MatchingForm(BaseQuestionForm):
    """Form for Matching questions"""
    
    def __init__(self, parent_frame: ttk.Frame, subject: Subject, 
                 lesson_id: Optional[str], mode: str, question: Optional[MatchingQuestion] = None):
        super().__init__(parent_frame, subject, lesson_id, mode, question)
        
        # Render and load
        self.render()
        if mode == "edit" and question:
            self.load_data()
    
    def render(self):
        """Render Matching form"""
        # Question text
        ttk.Label(self.parent_frame, text="Question:", font=('', 10, 'bold')).pack(anchor=tk.W, pady=(5, 0))
        self.question_text = tk.Text(self.parent_frame, height=3, font=('', 10))
        self.question_text.pack(fill=tk.X, pady=5)
        
        # Pairs
        ttk.Label(self.parent_frame, text="Pairs (format: Left | Right):", 
                 font=('', 10, 'bold')).pack(anchor=tk.W, pady=(10, 0))
        ttk.Label(self.parent_frame, text="Example: Italy | Rome", 
                 foreground='gray', font=('', 9)).pack(anchor=tk.W)
        ttk.Label(self.parent_frame, text="Enter one pair per line", 
                 foreground='gray', font=('', 9)).pack(anchor=tk.W)
        
        self.pairs_text = tk.Text(self.parent_frame, height=10, font=('', 10))
        self.pairs_text.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def load_data(self):
        """Load data from question object (edit mode)"""
        if not self.question:
            return
        
        # Load question text
        self.question_text.insert('1.0', self.question.question)
        
        # Load pairs
        pairs_text = '\n'.join([f"{p.get('country')} | {p.get('capital')}" 
                               for p in self.question.pairs])
        self.pairs_text.insert('1.0', pairs_text)
    
    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect data from form"""
        try:
            data = {}
            
            # Question text
            data['question'] = self.question_text.get('1.0', tk.END).strip()
            
            # Parse pairs
            lines = [l.strip() for l in self.pairs_text.get('1.0', tk.END).split('\n') 
                    if l.strip()]
            
            pairs = []
            correct = {}
            
            for i, line in enumerate(lines):
                if ' | ' not in line:
                    # Return error info
                    data['error'] = f"Line {i+1}: Use format 'Left | Right'"
                    return data
                
                parts = line.split(' | ')
                if len(parts) != 2:
                    data['error'] = f"Line {i+1}: Invalid format"
                    return data
                
                left, right = parts[0].strip(), parts[1].strip()
                
                if not left or not right:
                    data['error'] = f"Line {i+1}: Both sides must have text"
                    return data
                
                pid = chr(97 + i)  # a, b, c, ...
                pairs.append({"country": left, "capital": right, "id": pid})
                correct[pid] = right
            
            data['pairs'] = pairs
            data['correct'] = correct
            
            return data
            
        except Exception as e:
            print(f"Error collecting data: {str(e)}")
            return None
    
    def validate(self) -> Tuple[bool, str]:
        """Validate form data"""
        question_text = self.question_text.get('1.0', tk.END).strip()
        
        if not question_text:
            return False, "Question text is required"
        
        # Collect and validate pairs
        data = self.collect_data()
        
        if not data:
            return False, "Failed to collect form data"
        
        if 'error' in data:
            return False, data['error']
        
        pairs = data.get('pairs', [])
        
        if len(pairs) < 2:
            return False, "At least 2 pairs are required"
        
        if len(pairs) > 26:
            return False, "Maximum 26 pairs allowed"
        
        return True, ""
