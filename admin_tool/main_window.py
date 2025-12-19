"""
Main Window - Admin Tool
Handles the main application window and subject/lesson/question management
Version: 2.2 - Added enable/disable toggle functionality
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os

from shared.data_manager import DataManager
from shared.models import Subject, Lesson, Question
from shared.validators import SubjectValidator, LessonValidator
from shared.constants import *
from admin_tool.tree_manager import TreeManager
from admin_tool.widgets.details_panel import DetailsPanel
from admin_tool.dialogs.question_dialog import QuestionDialog


class MainWindow:
    """Main application window"""
    
    def __init__(self, root):
        self.root = root
        self.data_manager = DataManager()
        self.current_subject = None
        self.dialog_open = False
        
        self.setup_ui()
        self.load_subjects()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Top frame - Subject selection
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(top_frame, text="Subject:", font=('', 11, 'bold')).pack(side=tk.LEFT, padx=5)
        
        self.subject_var = tk.StringVar()
        self.subject_combo = ttk.Combobox(top_frame, textvariable=self.subject_var,
                                          state="readonly", width=30, font=('', 10))
        self.subject_combo.pack(side=tk.LEFT, padx=5)
        self.subject_combo.bind('<<ComboboxSelected>>', self.on_subject_change)
        
        ttk.Button(top_frame, text="+ New Subject", command=self.create_subject).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Delete Subject", command=self.delete_subject).pack(side=tk.LEFT, padx=5)
        
        # Main content - 2 columns
        content_frame = ttk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left: Tree View
        left_frame = ttk.LabelFrame(content_frame, text="📚 Lessons & Questions")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Tree widget
        tree_container = ttk.Frame(left_frame)
        tree_container.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.tree = ttk.Treeview(tree_container, selectmode='browse', height=TREE_HEIGHT)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tree_scroll = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        # Create TreeManager
        self.tree_manager = TreeManager(self.tree, self)
        
        # Buttons for Tree - Row 1
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        self.btn_add_lesson = ttk.Button(btn_frame, text="+ Add Lesson", 
                                         command=self.add_lesson, width=12)
        self.btn_add_lesson.pack(side=tk.LEFT, padx=2)
        
        self.btn_add_question = ttk.Button(btn_frame, text="+ Add Question", 
                                           command=self.add_question, width=14, state=tk.DISABLED)
        self.btn_add_question.pack(side=tk.LEFT, padx=2)
        
        self.btn_edit = ttk.Button(btn_frame, text="Edit", command=self.edit_item, 
                                   width=10, state=tk.DISABLED)
        self.btn_edit.pack(side=tk.LEFT, padx=2)
        
        self.btn_delete = ttk.Button(btn_frame, text="Delete", command=self.delete_item, 
                                     width=10, state=tk.DISABLED)
        self.btn_delete.pack(side=tk.LEFT, padx=2)
        
        self.btn_move = ttk.Button(btn_frame, text="Move to...", command=self.move_question, 
                                   width=12, state=tk.DISABLED)
        self.btn_move.pack(side=tk.LEFT, padx=2)

        # Buttons for Tree - Row 2
        btn_frame2 = ttk.Frame(left_frame)
        btn_frame2.pack(fill=tk.X, pady=5)
        
        # NEW: Toggle Enable/Disable button
        self.btn_toggle = ttk.Button(btn_frame2, text="⚡ Toggle Enable/Disable", 
                                     command=self.toggle_enabled, 
                                     width=20, state=tk.DISABLED)
        self.btn_toggle.pack(side=tk.LEFT, padx=2)
        
        # Bulk move button
        self.btn_bulk_move = ttk.Button(btn_frame2, text="📦 Bulk Move", 
                                command=self.bulk_move_questions, 
                                width=12, state=tk.DISABLED)
        self.btn_bulk_move.pack(side=tk.LEFT, padx=2)

        # Lesson reorder buttons
        reorder_frame = ttk.Frame(left_frame)
        reorder_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(reorder_frame, text="Reorder Lesson:", font=('', 9)).pack(side=tk.LEFT, padx=5)
        self.btn_move_up = ttk.Button(reorder_frame, text="↑ Up", 
                                      command=self.move_lesson_up, width=8, state=tk.DISABLED)
        self.btn_move_up.pack(side=tk.LEFT, padx=2)
        
        self.btn_move_down = ttk.Button(reorder_frame, text="↓ Down", 
                                        command=self.move_lesson_down, width=8, state=tk.DISABLED)
        self.btn_move_down.pack(side=tk.LEFT, padx=2)
        
        # Right: Details Panel
        right_frame = ttk.LabelFrame(content_frame, text="📋 Details", width=DETAILS_WIDTH)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(5, 0))
        right_frame.pack_propagate(False)
        
        # Create DetailsPanel
        self.details_panel = DetailsPanel(right_frame, self)
    
    def load_subjects(self):
        """Load all available subjects"""
        subjects = self.data_manager.discover_subjects()
        self.subject_combo['values'] = sorted(subjects.keys())
    
    def create_subject(self):
        """Create a new subject"""
        if self.dialog_open:
            return
        
        self.dialog_open = True
        subject_name = simpledialog.askstring("New Subject", "Enter subject name:")
        self.dialog_open = False
        
        if not subject_name:
            return
        
        # Validate name
        subject_name = subject_name.lower().strip()
        is_valid, error = SubjectValidator.validate_subject_name(subject_name)
        if not is_valid:
            messagebox.showerror("Invalid Name", error)
            return
        
        # Create subject
        subject = self.data_manager.create_subject(subject_name)
        if subject:
            self.load_subjects()
            self.subject_combo.set(subject_name)
            self.on_subject_change()
            messagebox.showinfo("Success", f"Subject '{subject_name}' created")
        else:
            messagebox.showerror("Error", "Subject already exists or could not be created")
    
    def delete_subject(self):
        """Delete the current subject"""
        if not self.current_subject:
            messagebox.showwarning("Warning", MSG_SELECT_SUBJECT)
            return
        
        subject_name = self.current_subject.name
        
        if messagebox.askyesno("Confirm", 
                              f"Delete subject '{subject_name}'?\n"
                              "All lessons, questions, and images will be deleted.\n\n"
                              "This cannot be undone!"):
            
            if self.data_manager.delete_subject(self.current_subject, delete_images=True):
                self.load_subjects()
                self.subject_combo.set('')
                self.current_subject = None
                self.tree_manager.clear_tree()
                self.details_panel.clear()
                messagebox.showinfo("Success", "Subject deleted")
            else:
                messagebox.showerror("Error", "Failed to delete subject")
    
    def on_subject_change(self, event=None):
        """Handle subject selection change"""
        subject_name = self.subject_var.get()
        if not subject_name:
            self.tree_manager.clear_tree()
            self.details_panel.clear()
            return
        
        # Load subject
        subjects = self.data_manager.discover_subjects()
        filename = subjects.get(subject_name)
        
        if filename:
            self.current_subject = self.data_manager.load_subject(subject_name, filename)
            if self.current_subject:
                self.tree_manager.refresh_tree(self.current_subject)
                self.details_panel.clear()
            else:
                messagebox.showerror("Error", f"Failed to load subject '{subject_name}'")
    
    def add_lesson(self):
        """Add a new lesson"""
        if not self.current_subject:
            messagebox.showwarning("Warning", MSG_SELECT_SUBJECT)
            return
        
        if self.dialog_open:
            return
        
        self.dialog_open = True
        lesson_name = simpledialog.askstring("New Lesson", "Enter lesson name:")
        self.dialog_open = False
        
        if not lesson_name:
            return
        
        # Validate name
        existing_names = [l.name for l in self.current_subject.lessons]
        is_valid, error = LessonValidator.validate_lesson_name(lesson_name, existing_names)
        if not is_valid:
            messagebox.showerror("Invalid Name", error)
            return
        
        # Create lesson
        lesson_id = self.current_subject.get_next_lesson_id()
        lesson = Lesson(id=lesson_id, name=lesson_name, enabled=True)  # NEW: default enabled
        
        self.current_subject.add_lesson(lesson)
        
        if self.data_manager.save_subject(self.current_subject):
            self.tree_manager.refresh_tree(self.current_subject, 
                                          focus_item={'type': 'lesson', 'lesson_id': lesson_id})
            messagebox.showinfo("Success", f"Lesson '{lesson_name}' created")
        else:
            messagebox.showerror("Error", "Failed to save lesson")
    
    def edit_lesson(self):
        """Edit the selected lesson"""
        selected = self.tree_manager.get_selected_item()
        if not selected or selected['type'] != 'lesson':
            messagebox.showwarning("Warning", MSG_SELECT_LESSON)
            return
        
        lesson_id = selected['id']
        lesson = self.current_subject.get_lesson_by_id(lesson_id)
        
        if not lesson:
            return
        
        if self.dialog_open:
            return
        
        self.dialog_open = True
        new_name = simpledialog.askstring("Edit Lesson", "Enter new name:", 
                                         initialvalue=lesson.name)
        self.dialog_open = False
        
        if not new_name or new_name == lesson.name:
            return
        
        # Validate name
        existing_names = [l.name for l in self.current_subject.lessons if l.id != lesson_id]
        is_valid, error = LessonValidator.validate_lesson_name(new_name, existing_names)
        if not is_valid:
            messagebox.showerror("Invalid Name", error)
            return
        
        # Update lesson
        lesson.name = new_name
        
        if self.data_manager.save_subject(self.current_subject):
            self.tree_manager.refresh_tree(self.current_subject,
                                          focus_item={'type': 'lesson', 'lesson_id': lesson_id})
            messagebox.showinfo("Success", "Lesson updated")
        else:
            messagebox.showerror("Error", "Failed to save lesson")
    
    def delete_lesson(self):
        """Delete the selected lesson"""
        selected = self.tree_manager.get_selected_item()
        if not selected or selected['type'] != 'lesson':
            messagebox.showwarning("Warning", MSG_SELECT_LESSON)
            return
        
        lesson_id = selected['id']
        lesson = self.current_subject.get_lesson_by_id(lesson_id)
        
        if not lesson:
            return
        
        # Count questions
        question_count = len(self.current_subject.get_questions_by_lesson(lesson_id))
        
        msg = f"Delete lesson '{lesson.name}'?"
        if question_count > 0:
            msg += f"\n\n{question_count} question(s) will be moved to 'Others'."
        
        if not messagebox.askyesno("Confirm", msg):
            return
        
        # Delete lesson
        self.current_subject.remove_lesson(lesson_id)
        
        if self.data_manager.save_subject(self.current_subject):
            self.tree_manager.refresh_tree(self.current_subject)
            messagebox.showinfo("Success", "Lesson deleted")
        else:
            messagebox.showerror("Error", "Failed to delete lesson")
    
    def move_lesson_up(self):
        """Move selected lesson up in order"""
        selected = self.tree_manager.get_selected_item()
        if not selected or selected['type'] != 'lesson':
            return
        
        lesson_id = selected['id']
        lessons = self.current_subject.lessons
        
        # Find lesson index
        lesson_idx = next((i for i, l in enumerate(lessons) if l.id == lesson_id), None)
        
        if lesson_idx is None or lesson_idx == 0:
            return
        
        # Swap with previous
        lessons[lesson_idx], lessons[lesson_idx - 1] = lessons[lesson_idx - 1], lessons[lesson_idx]
        
        if self.data_manager.save_subject(self.current_subject):
            self.tree_manager.refresh_tree(self.current_subject,
                                          focus_item={'type': 'lesson', 'lesson_id': lesson_id})
    
    def move_lesson_down(self):
        """Move selected lesson down in order"""
        selected = self.tree_manager.get_selected_item()
        if not selected or selected['type'] != 'lesson':
            return
        
        lesson_id = selected['id']
        lessons = self.current_subject.lessons
        
        # Find lesson index
        lesson_idx = next((i for i, l in enumerate(lessons) if l.id == lesson_id), None)
        
        if lesson_idx is None or lesson_idx >= len(lessons) - 1:
            return
        
        # Swap with next
        lessons[lesson_idx], lessons[lesson_idx + 1] = lessons[lesson_idx + 1], lessons[lesson_idx]
        
        if self.data_manager.save_subject(self.current_subject):
            self.tree_manager.refresh_tree(self.current_subject,
                                          focus_item={'type': 'lesson', 'lesson_id': lesson_id})
    
    def add_question(self):
        """Add a new question - can be called without lesson selection"""
        if not self.current_subject:
            messagebox.showwarning("Warning", MSG_SELECT_SUBJECT)
            return
        
        # Get current selection if any
        selected = self.tree_manager.get_selected_item()
        
        # Determine initial lesson
        if selected and selected['type'] == 'lesson':
            initial_lesson_id = selected['id']
        elif selected and selected['type'] == 'others':
            initial_lesson_id = None
        else:
            # No selection or question selected - default to None (Others)
            initial_lesson_id = None
        
        # Open dialog with lesson selector (user can change it)
        QuestionDialog(self.root, self.current_subject, initial_lesson_id, "add", 
                      callback=self.on_question_saved, parent_app=self)
    
    def edit_item(self):
        """Edit selected item (lesson or question)"""
        selected = self.tree_manager.get_selected_item()
        if not selected:
            return
        
        if selected['type'] == 'lesson':
            self.edit_lesson()
        elif selected['type'] == 'question':
            self.edit_question()
    
    def edit_question(self):
        """Edit the selected question"""
        selected = self.tree_manager.get_selected_item()
        if not selected or selected['type'] != 'question':
            messagebox.showwarning("Warning", MSG_SELECT_QUESTION)
            return
        
        question_id = selected['id']
        question = self.current_subject.get_question_by_id(question_id)
        
        if not question:
            return
        
        QuestionDialog(self.root, self.current_subject, question.lessonId, "edit",
                      question=question, callback=self.on_question_saved, parent_app=self)
    
    def delete_item(self):
        """Delete selected item(s) - supports bulk delete"""
        selection = self.tree.selection()
        
        if not selection:
            return
        
        # Check if multiple items
        if len(selection) > 1:
            self.bulk_delete_questions()
        else:
            # Single item - use existing logic
            selected = self.tree_manager.get_selected_item()
            if not selected:
                return
            
            if selected['type'] == 'lesson':
                self.delete_lesson()
            elif selected['type'] == 'question':
                self.delete_question()
    
    def bulk_delete_questions(self):
        """Delete multiple selected questions"""
        selection = self.tree.selection()
        
        # Get all question IDs
        question_ids = []
        for item in selection:
            tags = self.tree.item(item, 'tags')
            if len(tags) >= 2 and tags[0] == 'question':
                try:
                    question_ids.append(int(tags[1]))
                except ValueError:
                    continue
        
        if not question_ids:
            messagebox.showwarning("Warning", "No questions selected")
            return
        
        # Confirm deletion
        msg = f"Delete {len(question_ids)} question(s)?\n\n"
        msg += "Associated images will also be deleted.\n\n"
        msg += "This cannot be undone!"
        
        if not messagebox.askyesno("Confirm Bulk Delete", msg):
            return
        
        # Delete all questions
        deleted_count = 0
        total_images_deleted = 0
        
        for question_id in question_ids:
            # Delete question
            self.current_subject.remove_question(question_id)
            deleted_count += 1
            
            # Delete images
            try:
                from utils.image_helper import delete_question_images
                img_count = delete_question_images(self.current_subject.name, question_id)
                total_images_deleted += img_count
            except Exception as e:
                print(f"Warning: Could not delete images for question {question_id}: {str(e)}")
        
        # Save subject
        if self.data_manager.save_subject(self.current_subject):
            if total_images_deleted > 0:
                print(f"Deleted {total_images_deleted} image(s)")
            
            # Clear details panel and refresh tree
            self.details_panel.clear()
            self.tree_manager.refresh_tree(self.current_subject)
            
            messagebox.showinfo("Success", 
                              f"Deleted {deleted_count} question(s) successfully")
        else:
            messagebox.showerror("Error", "Failed to delete questions")
        
    def delete_question(self):
        """Delete the selected question"""
        selected = self.tree_manager.get_selected_item()
        if not selected or selected['type'] != 'question':
            messagebox.showwarning("Warning", MSG_SELECT_QUESTION)
            return
        
        if not messagebox.askyesno("Confirm", "Delete this question?\n\nAssociated images will also be deleted."):
            return
        
        question_id = selected['id']
        
        # Store info for focus management
        tree_item = self.tree.selection()[0]
        parent_item = self.tree.parent(tree_item)
        siblings = list(self.tree.get_children(parent_item))
        item_index = siblings.index(tree_item) if tree_item in siblings else 0
        
        # Delete question from data
        self.current_subject.remove_question(question_id)
        
        if self.data_manager.save_subject(self.current_subject):
            # Clean up associated images
            try:
                from utils.image_helper import delete_question_images
                deleted_count = delete_question_images(self.current_subject.name, question_id)
                if deleted_count > 0:
                    print(f"Deleted {deleted_count} image(s) for question {question_id}")
            except ImportError:
                print("Warning: image_helper not available, images not deleted")
            except Exception as e:
                print(f"Warning: Could not delete images: {str(e)}")
            
            # Clear details panel
            self.details_panel.clear()
            
            # Refresh tree with focus management
            self.tree_manager.refresh_tree(self.current_subject,
                                          focus_item={'type': 'next_question', 
                                                     'parent': parent_item,
                                                     'index': item_index})
            
            messagebox.showinfo("Success", "Question deleted successfully")
        else:
            messagebox.showerror("Error", "Failed to delete question")
    
    def move_question(self):
        """Move question to another lesson"""
        selected = self.tree_manager.get_selected_item()
        if not selected or selected['type'] != 'question':
            messagebox.showwarning("Warning", MSG_SELECT_QUESTION)
            return
        
        question_id = selected['id']
        question = self.current_subject.get_question_by_id(question_id)
        
        if not question:
            return
        
        if self.dialog_open:
            return
        
        # Create lesson selection dialog
        lesson_names = [l.name for l in self.current_subject.lessons] + [OTHERS_CATEGORY]
        lesson_ids = [l.id for l in self.current_subject.lessons] + [None]
        
        self.dialog_open = True
        dialog = tk.Toplevel(self.root)
        dialog.title("Move Question")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Move to lesson:", font=('', 10)).pack(pady=15)
        
        var = tk.StringVar()
        combo = ttk.Combobox(dialog, textvariable=var, values=lesson_names, 
                            state="readonly", width=35, font=('', 10))
        combo.pack(pady=10)
        
        def do_move():
            if not var.get():
                messagebox.showwarning("Warning", "Select a lesson")
                return
            
            lesson_idx = lesson_names.index(var.get())
            new_lesson_id = lesson_ids[lesson_idx]
            
            question.lessonId = new_lesson_id
            
            if self.data_manager.save_subject(self.current_subject):
                dialog.destroy()
                self.dialog_open = False
                self.tree_manager.refresh_tree(self.current_subject,
                                              focus_item={'type': 'question', 'q_id': question_id})
                messagebox.showinfo("Success", "Question moved")
            else:
                messagebox.showerror("Error", "Failed to move question")
        
        def cancel():
            dialog.destroy()
            self.dialog_open = False
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="Move", command=do_move, width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=cancel, width=12).pack(side=tk.LEFT, padx=5)
        
        dialog.protocol("WM_DELETE_WINDOW", cancel)
    
    def bulk_move_questions(self):
        """Move multiple selected questions to another lesson"""
        selection = self.tree.selection()
        
        # Get all question IDs from selection
        question_ids = []
        for item in selection:
            tags = self.tree.item(item, 'tags')
            if len(tags) >= 2 and tags[0] == 'question':
                try:
                    question_ids.append(int(tags[1]))
                except ValueError:
                    continue
        
        if not question_ids:
            messagebox.showwarning("Warning", "No questions selected")
            return
        
        # Show lesson selection dialog
        lesson_names = [l.name for l in self.current_subject.lessons] + [OTHERS_CATEGORY]
        lesson_ids = [l.id for l in self.current_subject.lessons] + [None]
        
        if self.dialog_open:
            return
        
        self.dialog_open = True
        dialog = tk.Toplevel(self.root)
        dialog.title("Bulk Move Questions")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text=f"Move {len(question_ids)} question(s) to:", 
                 font=('', 11, 'bold')).pack(pady=15)
        
        # Show list of selected questions
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
        
        list_label = ttk.Label(list_frame, text="Selected questions:", 
                               font=('', 9), foreground='gray')
        list_label.pack(anchor=tk.W)
        
        questions_text = tk.Text(list_frame, height=4, font=('', 9), 
                                state=tk.DISABLED, wrap=tk.WORD)
        questions_text.pack(fill=tk.BOTH, expand=True)
        
        # Populate question list
        questions_text.config(state=tk.NORMAL)
        for qid in question_ids:
            q = self.current_subject.get_question_by_id(qid)
            if q:
                qtext = q.question[:40] if hasattr(q, 'question') else f"Question {qid}"
                questions_text.insert(tk.END, f"• {qtext}...\n")
        questions_text.config(state=tk.DISABLED)
        
        var = tk.StringVar()
        combo = ttk.Combobox(dialog, textvariable=var, values=lesson_names,
                            state="readonly", width=35, font=('', 10))
        combo.pack(pady=10)
        
        def do_bulk_move():
            if not var.get():
                messagebox.showwarning("Warning", "Select a lesson")
                return
            
            lesson_idx = lesson_names.index(var.get())
            new_lesson_id = lesson_ids[lesson_idx]
            
            # Move all questions
            for qid in question_ids:
                question = self.current_subject.get_question_by_id(qid)
                if question:
                    question.lessonId = new_lesson_id
            
            if self.data_manager.save_subject(self.current_subject):
                dialog.destroy()
                self.dialog_open = False
                self.tree_manager.refresh_tree(self.current_subject)
                self.details_panel.clear()
                messagebox.showinfo("Success", 
                                  f"Moved {len(question_ids)} question(s) successfully")
            else:
                messagebox.showerror("Error", "Failed to move questions")
        
        def cancel():
            dialog.destroy()
            self.dialog_open = False
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="Move All", command=do_bulk_move, 
                  width=12).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=cancel, 
                  width=12).pack(side=tk.LEFT, padx=5)
        
        dialog.protocol("WM_DELETE_WINDOW", cancel)
    
    # ========================================================================
    # NEW: TOGGLE ENABLE/DISABLE FUNCTIONALITY
    # ========================================================================
    
    def toggle_enabled(self):
        """Toggle enabled status of selected items"""
        selection = self.tree.selection()
        
        if not selection:
            return
        
        # Check if multiple items selected
        if len(selection) > 1:
            # Bulk toggle
            self.bulk_toggle_enabled()
        else:
            # Single item toggle
            selected = self.tree_manager.get_selected_item()
            if not selected:
                return
            
            if selected['type'] == 'lesson':
                self.toggle_lesson_enabled(selected['id'])
            elif selected['type'] == 'question':
                self.toggle_question_enabled(selected['id'])
    
    def toggle_lesson_enabled(self, lesson_id: str):
        """Toggle enabled status of a lesson"""
        lesson = self.current_subject.get_lesson_by_id(lesson_id)
        if not lesson:
            return
        
        # Toggle status
        current_status = getattr(lesson, 'enabled', True)
        lesson.enabled = not current_status
        
        # Get questions in this lesson
        questions = self.current_subject.get_questions_by_lesson(lesson_id)
        
        if not lesson.enabled:
            # DISABLING lesson - ask about cascading disable
            if questions:
                if messagebox.askyesno("Cascade Disable", 
                                      f"Also disable all {len(questions)} question(s) in this lesson?"):
                    for q in questions:
                        q.enabled = False
        else:
            # ENABLING lesson - ask about cascading enable
            disabled_questions = [q for q in questions if not getattr(q, 'enabled', True)]
            if disabled_questions:
                if messagebox.askyesno("Cascade Enable", 
                                      f"Also enable {len(disabled_questions)} disabled question(s) in this lesson?"):
                    for q in disabled_questions:
                        q.enabled = True
        
        # Save and refresh
        if self.data_manager.save_subject(self.current_subject):
            status_text = "disabled" if not lesson.enabled else "enabled"
            self.tree_manager.refresh_tree(self.current_subject,
                                          focus_item={'type': 'lesson', 'lesson_id': lesson_id})
            messagebox.showinfo("Success", f"Lesson '{lesson.name}' {status_text}")
        else:
            messagebox.showerror("Error", "Failed to save changes")
    
    def toggle_question_enabled(self, question_id: int):
        """Toggle enabled status of a question"""
        question = self.current_subject.get_question_by_id(question_id)
        if not question:
            return
        
        # Toggle status
        current_status = getattr(question, 'enabled', True)
        question.enabled = not current_status
        
        # Save and refresh
        if self.data_manager.save_subject(self.current_subject):
            status_text = "disabled" if not question.enabled else "enabled"
            self.tree_manager.refresh_tree(self.current_subject,
                                          focus_item={'type': 'question', 'q_id': question_id})
            
            # Update details panel if still showing this question
            selected = self.tree_manager.get_selected_item()
            if selected and selected['type'] == 'question' and selected['id'] == question_id:
                self.details_panel.show_question(question, self.current_subject)
        else:
            messagebox.showerror("Error", "Failed to save changes")

    def bulk_toggle_enabled(self):
        """Bulk toggle enabled status"""
        selection = self.tree.selection()
        
        # Collect items
        lessons_to_toggle = []
        questions_to_toggle = []
        
        for item in selection:
            tags = self.tree.item(item, 'tags')
            if len(tags) >= 2:
                if tags[0] == 'lesson':
                    lessons_to_toggle.append(tags[1])
                elif tags[0] == 'question':
                    questions_to_toggle.append(int(tags[1]))
        
        # Confirm action
        if not lessons_to_toggle and not questions_to_toggle:
            return
        
        msg = f"Toggle enabled/disabled status for:\n"
        if lessons_to_toggle:
            msg += f"• {len(lessons_to_toggle)} lesson(s)\n"
        if questions_to_toggle:
            msg += f"• {len(questions_to_toggle)} question(s)\n"
        
        if not messagebox.askyesno("Confirm Bulk Toggle", msg):
            return
        
        # Toggle lessons
        cascade_questions = False
        if lessons_to_toggle:
            # Ask about cascading
            if messagebox.askyesno("Cascade to Questions", 
                                  "Also toggle questions inside selected lessons?"):
                cascade_questions = True
        
        for lesson_id in lessons_to_toggle:
            lesson = self.current_subject.get_lesson_by_id(lesson_id)
            if lesson:
                current_status = getattr(lesson, 'enabled', True)
                lesson.enabled = not current_status
                
                # Cascade to questions if requested
                if cascade_questions:
                    for q in self.current_subject.get_questions_by_lesson(lesson_id):
                        q.enabled = lesson.enabled
        
        # Toggle questions
        for q_id in questions_to_toggle:
            question = self.current_subject.get_question_by_id(q_id)
            if question:
                current_status = getattr(question, 'enabled', True)
                question.enabled = not current_status
        
        # Save and refresh
        if self.data_manager.save_subject(self.current_subject):
            self.tree_manager.refresh_tree(self.current_subject)
            self.details_panel.clear()
            messagebox.showinfo("Success", "Bulk toggle completed successfully")
        else:
            messagebox.showerror("Error", "Failed to save changes")

    # ========================================================================
    # END: TOGGLE ENABLE/DISABLE FUNCTIONALITY
    # ========================================================================

    def on_question_saved(self, mode, question_id):
        """Callback after question is saved"""
        if mode == "add":
            # Focus on newly added question
            self.tree_manager.refresh_tree(self.current_subject,
                                          focus_item={'type': 'question', 'q_id': question_id})
        elif mode == "edit":
            # Keep focus on edited question
            self.tree_manager.refresh_tree(self.current_subject,
                                          focus_item={'type': 'question', 'q_id': question_id})    