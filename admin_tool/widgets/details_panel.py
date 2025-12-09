"""
Details Panel Widget - Displays question/lesson details
Version: 2.2 - Added MCM support
"""

import tkinter as tk
from tkinter import ttk
import os

from shared.models import Subject, Lesson, Question
from shared.constants import QUESTION_TYPE_NAMES

# Try to import PIL for image preview
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class DetailsPanel:
    """Widget for displaying details of selected items"""
    
    def __init__(self, parent_frame, main_window):
        self.parent_frame = parent_frame
        self.main_window = main_window
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the details panel UI"""
        # Create scrollable container
        self.container = ttk.Frame(self.parent_frame)
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        self.scrollbar = ttk.Scrollbar(self.container, orient=tk.VERTICAL)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Canvas for scrolling
        self.canvas = tk.Canvas(self.container, yscrollcommand=self.scrollbar.set, bg='#f8f9fa')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.scrollbar.config(command=self.canvas.yview)
        
        # Frame inside canvas
        self.content_frame = ttk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.content_frame, anchor='nw')
        
        # Update scrollregion when content changes
        self.content_frame.bind('<Configure>', 
                               lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
    
    def clear(self):
        """Clear the details panel"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def show_question(self, question: Question, subject: Subject):
        """Display question details"""
        self.clear()
        
        # Create text widget
        text_widget = tk.Text(self.content_frame, font=('Consolas', 9), 
                             wrap=tk.WORD, height=15, width=50)
        text_widget.pack(fill=tk.X, padx=5, pady=5)
        
        # Format question details
        details = self._format_question_text(question, subject)
        text_widget.insert('1.0', details)
        text_widget.config(state=tk.DISABLED)
        
        # Show question image if exists
        if question.questionImage and PIL_AVAILABLE:
            self._show_image_preview(question.questionImage, 
                                    scale=question.questionImageScale)
    
    def show_lesson(self, lesson: Lesson, subject: Subject):
        """Display lesson summary"""
        self.clear()
        
        text_widget = tk.Text(self.content_frame, font=('Consolas', 9), 
                             wrap=tk.WORD, height=20, width=50)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Get lesson statistics
        questions = subject.get_questions_by_lesson(lesson.id)
        
        details = f"LESSON DETAILS\n{'='*50}\n\n"
        details += f"Name: {lesson.name}\n"
        details += f"ID: {lesson.id}\n"
        details += f"Questions: {len(questions)}\n\n"
        
        if questions:
            details += "Question Types:\n"
            types = {}
            for q in questions:
                qtype = QUESTION_TYPE_NAMES.get(q.type, q.type)
                types[qtype] = types.get(qtype, 0) + 1
            
            for qtype, count in sorted(types.items()):
                details += f"  • {qtype}: {count}\n"
            
            # Count with images
            with_images = sum(1 for q in questions if q.questionImage)
            if with_images > 0:
                details += f"\nQuestions with images: {with_images}\n"
        
        text_widget.insert('1.0', details)
        text_widget.config(state=tk.DISABLED)
    
    def show_others(self, subject: Subject):
        """Display Others category summary"""
        self.clear()
        
        text_widget = tk.Text(self.content_frame, font=('Consolas', 9), 
                             wrap=tk.WORD, height=20, width=50)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        questions = subject.get_questions_by_lesson(None)
        
        details = f"OTHERS (UNASSIGNED)\n{'='*50}\n\n"
        details += f"Questions: {len(questions)}\n\n"
        
        if questions:
            details += "Question Types:\n"
            types = {}
            for q in questions:
                qtype = QUESTION_TYPE_NAMES.get(q.type, q.type)
                types[qtype] = types.get(qtype, 0) + 1
            
            for qtype, count in sorted(types.items()):
                details += f"  • {qtype}: {count}\n"
            
            # Count with images
            with_images = sum(1 for q in questions if q.questionImage)
            if with_images > 0:
                details += f"\nQuestions with images: {with_images}\n"
        
        text_widget.insert('1.0', details)
        text_widget.config(state=tk.DISABLED)
    
    def _format_question_text(self, q: Question, subject: Subject) -> str:
        """Format question for text display"""
        qtype_name = QUESTION_TYPE_NAMES.get(q.type, q.type)
        text = f"QUESTION DETAILS\n{'='*50}\n\n"
        text += f"Type: {qtype_name}\n"
        text += f"ID: {q.id}\n"
        
        # Show lesson
        if q.lessonId:
            lesson = subject.get_lesson_by_id(q.lessonId)
            text += f"Lesson: {lesson.name if lesson else 'Unknown'}\n"
        else:
            text += "Lesson: Others\n"
        
        # Image info
        if q.questionImage:
            text += f"📷 Image: {os.path.basename(q.questionImage)} ({q.questionImageScale}%)\n"
        
        text += "\n" + "-" * 50 + "\n\n"
        
        # Type-specific details
        if q.type == "multiple_choice":
            text += f"Question:\n{q.question}\n\nOptions:\n"
            for i, opt in enumerate(q.options):
                mark = "✓" if i == q.correct else " "
                img_indicator = " 🖼️" if hasattr(q, 'optionImages') and q.optionImages and q.optionImages.get(str(i)) else ""
                text += f"  [{mark}] {i}. {opt}{img_indicator}\n"
        
        elif q.type == "multiple_choice_multiple":
            text += f"Question:\n{q.question}\n\nOptions:\n"
            for i, opt in enumerate(q.options):
                mark = "✓" if i in q.correct else " "
                img_indicator = " 🖼️" if hasattr(q, 'optionImages') and q.optionImages and q.optionImages.get(str(i)) else ""
                text += f"  [{mark}] {i}. {opt}{img_indicator}\n"
            
            # Show all correct answers
            correct_indices = ", ".join(str(i) for i in sorted(q.correct))
            text += f"\nCorrect answers: {correct_indices}\n"
        
        elif q.type == "true_false":
            text += f"Question:\n{q.question}\n\n"
            text += f"Answer: {'True' if q.correct == 0 else 'False'}\n"
        
        elif q.type == "fill_in_blank":
            text += f"Question:\n{q.question}\n\n"
            text += "Accepted Answers:\n"
            for ans in q.correct:
                text += f"  • {ans}\n"
        
        elif q.type == "matching":
            text += f"Question:\n{q.question}\n\n"
            text += "Pairs:\n"
            for p in q.pairs:
                text += f"  {p.get('country', '')} → {p.get('capital', '')}\n"
        
        elif q.type == "reordering":
            text += f"Question:\n{q.question}\n\n"
            text += "Correct Order:\n"
            sorted_items = sorted(q.items, key=lambda x: x.get('order', 0))
            for i, item in enumerate(sorted_items, 1):
                text += f"  {i}. {item.get('text', '')}\n"
        
        elif q.type == "reading_comprehension":
            text += f"Passage:\n{q.passage}\n\n"
            text += "Sub-Questions:\n"
            for i, sq in enumerate(q.questions, 1):
                text += f"\n  {i}. {sq.get('question', '')}\n"
                for j, opt in enumerate(sq.get('options', [])):
                    mark = "✓" if j == sq.get('correct') else " "
                    text += f"     [{mark}] {opt}\n"
        
        return text
    
    def _show_image_preview(self, image_path: str, scale: int = 50):
        """Show image preview if PIL available"""
        if not PIL_AVAILABLE or not image_path or not os.path.exists(image_path):
            return
        
        try:
            img = Image.open(image_path)
            
            # Calculate size based on scale
            width, height = img.size
            new_width = int(width * scale / 100)
            new_height = int(height * scale / 100)
            
            # Limit max size for preview
            max_width = 400
            if new_width > max_width:
                ratio = max_width / new_width
                new_width = max_width
                new_height = int(new_height * ratio)
            
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            
            label = tk.Label(self.content_frame, image=photo)
            label.image = photo  # Keep reference
            label.pack(pady=5)
            
            # Show info
            info_label = ttk.Label(self.content_frame, 
                                  text=f"{os.path.basename(image_path)} ({scale}%)",
                                  font=('', 8), foreground='gray')
            info_label.pack()
        
        except Exception as e:
            ttk.Label(self.content_frame, text=f"Error loading image: {str(e)}",
                     foreground='red').pack(pady=5)
