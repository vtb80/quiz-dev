"""
Reordering Question Form
Handles creation and editing of reordering questions
Version: 1.0
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Dict, Any, Tuple

from shared.models import Subject, Question, ReorderingQuestion
from shared.validators import QuestionValidator
from admin_tool.dialogs.question_forms.base_form import BaseQuestionForm


class ReorderingForm(BaseQuestionForm):
    """Form for Reordering questions"""
    
    def __init__(self, parent_frame: ttk.Frame, subject: Subject, 
                 lesson_id: Optional[str], mode: str, question: Optional[ReorderingQuestion] = None):
        super().__init__(parent_frame, subject, lesson_id, mode, question)
        
        # Render and load
        self.render()
        if mode == "edit" and question:
            self.load_data()
    
    def render(self):
        """Render Reordering form"""
        # Question text
        ttk.Label(self.parent_frame, text="Question:", font=('', 10, 'bold')).pack(anchor=tk.W, pady=(5, 0))
        self.question_text = tk.Text(self.parent_frame, height=3, font=('', 10))
        self.question_text.pack(fill=tk.X, pady=5)
        
        # Items
        ttk.Label(self.parent_frame, text="Items (one per line, in correct order):", 
                 font=('', 10, 'bold')).pack(anchor=tk.W, pady=(10, 0))
        ttk.Label(self.parent_frame, text="Enter items in the order they should appear", 
                 foreground='gray', font=('', 9)).pack(anchor=tk.W)
        ttk.Label(self.parent_frame, text="Students will see them shuffled", 
                 foreground='gray', font=('', 9)).pack(anchor=tk.W)
        
        self.items_text = tk.Text(self.parent_frame, height=10, font=('', 10))
        self.items_text.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def load_data(self):
        """Load data from question object (edit mode)"""
        if not self.question:
            return
        
        # Load question text
        self.question_text.insert('1.0', self.question.question)
        
        # Load items in correct order
        items = sorted(self.question.items, key=lambda x: x.get('order', 0))
        items_text = '\n'.join([item.get('text', '') for item in items])
        self.items_text.insert('1.0', items_text)
    
    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect data from form"""
        try:
            data = {}
            
            # Question text
            data['question'] = self.question_text.get('1.0', tk.END).strip()
            
            # Parse items
            lines = [l.strip() for l in self.items_text.get('1.0', tk.END).split('\n') 
                    if l.strip()]
            
            items = []
            for i, line in enumerate(lines):
                if not line:
                    continue
                items.append({"text": line, "order": i + 1})
            
            data['items'] = items
            
            return data
            
        except Exception as e:
            print(f"Error collecting data: {str(e)}")
            return None
    
    def validate(self) -> Tuple[bool, str]:
        """Validate form data"""
        question_text = self.question_text.get('1.0', tk.END).strip()
        
        if not question_text:
            return False, "Question text is required"
        
        # Validate items
        lines = [l.strip() for l in self.items_text.get('1.0', tk.END).split('\n') 
                if l.strip()]
        
        if len(lines) < 2:
            return False, "At least 2 items are required"
        
        for i, line in enumerate(lines):
            if not line:
                return False, f"Item {i+1} is empty"
        
        # Check for duplicates
        if len(lines) != len(set(lines)):
            return False, "Duplicate items found. Each item must be unique"
        
        return True, ""
