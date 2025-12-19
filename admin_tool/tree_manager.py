"""
Tree Manager - Handles tree view display and interactions
Version: 2.3 - Added enable/disable visual indicators
"""

from shared.constants import *
from shared.models import Subject


class TreeManager:
    """Manages the tree view for lessons and questions"""
    
    def __init__(self, tree_widget, main_window):
        self.tree = tree_widget
        self.main_window = main_window
        
        # Enable multi-select
        self.tree.config(selectmode='extended')
        
        # Configure tags for styling disabled items
        self.tree.tag_configure('disabled', foreground='#999999')  # Gray color
        
        # Bind events
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.tree.bind('<Double-1>', self.on_tree_double_click)
    
    def clear_tree(self):
        """Clear all items from tree"""
        self.tree.delete(*self.tree.get_children())
    
    def refresh_tree(self, subject: Subject, focus_item=None, preserve_expansion=True):
        """
        Refresh tree view with subject data
        Args:
            subject: Subject object to display
            focus_item: dict with focus information {'type': 'lesson'/'question', 'lesson_id'/'q_id': ...}
            preserve_expansion: bool - whether to preserve expanded/collapsed state (default: True)
        """
        # Save expanded state BEFORE clearing (use lesson IDs for reliability)
        expanded_lesson_ids = []
        expanded_others = False
        
        if preserve_expansion:
            for item in self.tree.get_children():
                if self.tree.item(item, 'open'):
                    tags = self.tree.item(item, 'tags')
                    if len(tags) >= 1:
                        if tags[0] == 'lesson' and len(tags) >= 2:
                            expanded_lesson_ids.append(tags[1])
                        elif tags[0] == 'others':
                            expanded_others = True
        
        # Clear tree
        self.clear_tree()
        
        # Add lessons
        for lesson in subject.lessons:
            lesson_id = lesson.id
            lesson_name = lesson.name
            lesson_enabled = getattr(lesson, 'enabled', True)
            
            # Get questions in this lesson
            questions = subject.get_questions_by_lesson(lesson_id)
            
            # Count ENABLED questions only
            enabled_count = sum(1 for q in questions if getattr(q, 'enabled', True))
            
            # Visual indicator for disabled lesson
            status_icon = "" if lesson_enabled else "🚫 "
            
            # Create lesson node
            lesson_text = f"{status_icon}{ICON_LESSON} {lesson_name} ({enabled_count})"
            
            # Build tags list
            lesson_tags = ['lesson', lesson_id]
            if not lesson_enabled:
                lesson_tags.append('disabled')
            
            lesson_node = self.tree.insert('', 'end', text=lesson_text,
                                          tags=tuple(lesson_tags), open=False)
            
            # Restore expanded state based on lesson_id
            if preserve_expansion and lesson_id in expanded_lesson_ids:
                self.tree.item(lesson_node, open=True)
            
            # Add questions under lesson
            for question in questions:
                self._add_question_to_tree(lesson_node, question)
        
        # Add "Others" category
        others_questions = subject.get_questions_by_lesson(None)
        
        # Count ENABLED questions in Others
        enabled_count = sum(1 for q in others_questions if getattr(q, 'enabled', True))
        
        others_text = f"{OTHERS_DISPLAY} ({enabled_count})"
        others_node = self.tree.insert('', 'end', text=others_text,
                                       tags=('others',), open=False)
        
        # Restore expanded state for Others
        if preserve_expansion and expanded_others:
            self.tree.item(others_node, open=True)
        
        # Add questions under Others
        for question in others_questions:
            self._add_question_to_tree(others_node, question)
        
        # Handle focus
        if focus_item:
            self.focus_on_item(focus_item, subject)
    
    def _add_question_to_tree(self, parent_node, question):
        """
        Helper method to add a question to the tree
        Args:
            parent_node: Parent tree node (lesson or others)
            question: Question object to add
        """
        qtype_short = QUESTION_TYPE_ICONS.get(question.type, '?')
        question_enabled = getattr(question, 'enabled', True)
        
        # Get question text
        if hasattr(question, 'question'):
            qtext = question.question[:50]
        elif hasattr(question, 'passage'):
            qtext = question.passage[:50]
        else:
            qtext = f"Question {question.id}"
        
        # Visual indicators
        status_icon = "" if question_enabled else "🚫 "
        has_img = f"{ICON_IMAGE} " if question.questionImage else ""
        
        question_text = f"  {status_icon}{has_img}[{qtype_short}] {qtext}..."
        
        # Build tags list
        question_tags = ['question', str(question.id)]
        if not question_enabled:
            question_tags.append('disabled')
        
        self.tree.insert(parent_node, 'end', text=question_text,
                       tags=tuple(question_tags))
    
    def focus_on_item(self, item_info: dict, subject: Subject):
        """
        Focus on a specific item in the tree
        Args:
            item_info: dict with 'type' and id info
            subject: Subject object for lookups
        """
        item_type = item_info.get('type')
        
        if item_type == 'lesson':
            lesson_id = item_info.get('lesson_id')
            self._focus_lesson(lesson_id)
        
        elif item_type == 'question':
            q_id = item_info.get('q_id')
            self._focus_question(q_id)
        
        elif item_type == 'next_question':
            parent = item_info.get('parent')
            index = item_info.get('index', 0)
            self._focus_next_question(parent, index)
    
    def _focus_lesson(self, lesson_id: str):
        """Focus on a lesson node"""
        for item in self.tree.get_children():
            tags = self.tree.item(item, 'tags')
            if len(tags) >= 2 and tags[0] == 'lesson' and tags[1] == lesson_id:
                self.tree.selection_set(item)
                self.tree.see(item)
                self.tree.focus(item)
                return
    
    def _focus_question(self, question_id: int):
        """Focus on a question node"""
        for parent in self.tree.get_children():
            # Expand parent to make question visible
            # self.tree.item(parent, open=True)
            
            for child in self.tree.get_children(parent):
                tags = self.tree.item(child, 'tags')
                if len(tags) >= 2 and tags[0] == 'question' and int(tags[1]) == question_id:
                    self.tree.selection_set(child)
                    self.tree.see(child)
                    self.tree.focus(child)
                    return
    
    def _focus_next_question(self, parent_item, index: int):
        """Focus on next question after deletion"""
        if parent_item and self.tree.exists(parent_item):
            children = self.tree.get_children(parent_item)
            if children:
                target_index = min(index, len(children) - 1)
                self.tree.selection_set(children[target_index])
                self.tree.see(children[target_index])
                self.tree.focus(children[target_index])
    
    def get_selected_item(self):
        """
        Get information about the currently selected item
        Returns: dict with 'type' and 'id', or None
        """
        selection = self.tree.selection()
        if not selection:
            return None
        
        item = selection[0]
        tags = self.tree.item(item, 'tags')
        
        if len(tags) < 1:
            return None
        
        item_type = tags[0]
        
        if item_type == 'lesson':
            return {'type': 'lesson', 'id': tags[1] if len(tags) > 1 else None}
        elif item_type == 'question':
            return {'type': 'question', 'id': int(tags[1]) if len(tags) > 1 else None}
        elif item_type == 'others':
            return {'type': 'others', 'id': None}
        
        return None
    
    def get_selected_items(self):
        """
        Get information about all selected items (for multi-select)
        Returns: list of dicts with 'type' and 'id'
        """
        selection = self.tree.selection()
        items = []
        
        for item in selection:
            tags = self.tree.item(item, 'tags')
            if len(tags) < 1:
                continue
            
            item_type = tags[0]
            
            if item_type == 'lesson' and len(tags) >= 2:
                items.append({'type': 'lesson', 'id': tags[1]})
            elif item_type == 'question' and len(tags) >= 2:
                items.append({'type': 'question', 'id': int(tags[1])})
            elif item_type == 'others':
                items.append({'type': 'others', 'id': None})
        
        return items
    
    def on_tree_select(self, event=None):
        """Handle tree selection event - supports multi-select"""
        selection = self.tree.selection()
        
        if not selection:
            self.update_buttons(None, 0)
            return
        
        # Check if multiple items selected
        if len(selection) > 1:
            # Multi-select mode
            self.handle_multi_select(selection)
        else:
            # Single select mode
            selected = self.get_selected_item()
            if not selected:
                self.update_buttons(None, 0)
                return
            
            item_type = selected['type']
            self.update_buttons(item_type, 1)
            
            # Update details panel
            if item_type == 'question':
                question_id = selected['id']
                question = self.main_window.current_subject.get_question_by_id(question_id)
                if question:
                    self.main_window.details_panel.show_question(question, 
                                                                 self.main_window.current_subject)
            
            elif item_type == 'lesson':
                lesson_id = selected['id']
                lesson = self.main_window.current_subject.get_lesson_by_id(lesson_id)
                if lesson:
                    self.main_window.details_panel.show_lesson(lesson, 
                                                               self.main_window.current_subject)
            
            elif item_type == 'others':
                self.main_window.details_panel.show_others(self.main_window.current_subject)
    
    def handle_multi_select(self, selection):
        """Handle multiple selection"""
        # Check if all selected items are questions
        all_questions = True
        question_count = 0
        
        # Check if all selected items are lessons
        all_lessons = True
        lesson_count = 0
        
        for item in selection:
            tags = self.tree.item(item, 'tags')
            if len(tags) >= 1:
                if tags[0] == 'question':
                    question_count += 1
                    all_lessons = False
                elif tags[0] == 'lesson':
                    lesson_count += 1
                    all_questions = False
                else:
                    all_questions = False
                    all_lessons = False
        
        if all_questions and question_count > 0:
            # All selected are questions - enable bulk operations
            self.update_buttons('multi_question', question_count)
            
            # Show multi-select info in details panel
            self.main_window.details_panel.clear()
            info_text = f"Selected: {question_count} question(s)\n\n"
            info_text += "Available actions:\n"
            info_text += "• Bulk Move to lesson\n"
            info_text += "• Bulk Enable/Disable\n"
            info_text += "• Delete selected\n"
            
            import tkinter as tk
            text_widget = tk.Text(self.main_window.details_panel.content_frame, 
                                 font=('Consolas', 10), wrap=tk.WORD, 
                                 height=10, width=40)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            text_widget.insert('1.0', info_text)
            text_widget.config(state=tk.DISABLED)
        
        elif all_lessons and lesson_count > 0:
            # All selected are lessons - enable bulk operations
            self.update_buttons('multi_lesson', lesson_count)
            
            # Show multi-select info in details panel
            self.main_window.details_panel.clear()
            info_text = f"Selected: {lesson_count} lesson(s)\n\n"
            info_text += "Available actions:\n"
            info_text += "• Bulk Enable/Disable\n"
            
            import tkinter as tk
            text_widget = tk.Text(self.main_window.details_panel.content_frame, 
                                 font=('Consolas', 10), wrap=tk.WORD, 
                                 height=10, width=40)
            text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            text_widget.insert('1.0', info_text)
            text_widget.config(state=tk.DISABLED)
        
        else:
            # Mixed selection
            self.update_buttons('mixed', len(selection))
    
    def on_tree_double_click(self, event):
        """Handle double-click on tree item"""
        selected = self.get_selected_item()
        if selected and selected['type'] == 'question':
            self.main_window.edit_question()
    
    def update_buttons(self, item_type, count=1):
        """Enable/disable buttons based on selection"""
        if item_type == 'multi_question' and count > 1:
            # Multiple questions selected
            self.main_window.btn_add_question.config(state='disabled')
            self.main_window.btn_add_lesson.config(state='normal')
            self.main_window.btn_edit.config(state='disabled')
            self.main_window.btn_delete.config(state='normal')
            self.main_window.btn_move.config(state='disabled')
            self.main_window.btn_bulk_move.config(state='normal')
            self.main_window.btn_toggle.config(state='normal')  # NEW
            self.main_window.btn_move_up.config(state='disabled')
            self.main_window.btn_move_down.config(state='disabled')
        
        elif item_type == 'multi_lesson' and count > 1:
            # Multiple lessons selected
            self.main_window.btn_add_question.config(state='disabled')
            self.main_window.btn_add_lesson.config(state='normal')
            self.main_window.btn_edit.config(state='disabled')
            self.main_window.btn_delete.config(state='disabled')
            self.main_window.btn_move.config(state='disabled')
            self.main_window.btn_bulk_move.config(state='disabled')
            self.main_window.btn_toggle.config(state='normal')  # NEW
            self.main_window.btn_move_up.config(state='disabled')
            self.main_window.btn_move_down.config(state='disabled')
        
        elif item_type == 'lesson':
            self.main_window.btn_add_question.config(state='normal')
            self.main_window.btn_add_lesson.config(state='normal')
            self.main_window.btn_edit.config(state='normal')
            self.main_window.btn_delete.config(state='normal')
            self.main_window.btn_move.config(state='disabled')
            self.main_window.btn_bulk_move.config(state='disabled')
            self.main_window.btn_toggle.config(state='normal')  # NEW
            self.main_window.btn_move_up.config(state='normal')
            self.main_window.btn_move_down.config(state='normal')
        
        elif item_type == 'question':
            self.main_window.btn_add_question.config(state='normal')
            self.main_window.btn_add_lesson.config(state='normal')
            self.main_window.btn_edit.config(state='normal')
            self.main_window.btn_delete.config(state='normal')
            self.main_window.btn_move.config(state='normal')
            self.main_window.btn_bulk_move.config(state='disabled')
            self.main_window.btn_toggle.config(state='normal')  # NEW
            self.main_window.btn_move_up.config(state='disabled')
            self.main_window.btn_move_down.config(state='disabled')
        
        elif item_type == 'others':
            self.main_window.btn_add_question.config(state='normal')
            self.main_window.btn_add_lesson.config(state='normal')
            self.main_window.btn_edit.config(state='disabled')
            self.main_window.btn_delete.config(state='disabled')
            self.main_window.btn_move.config(state='disabled')
            self.main_window.btn_bulk_move.config(state='disabled')
            self.main_window.btn_toggle.config(state='disabled')  # NEW
            self.main_window.btn_move_up.config(state='disabled')
            self.main_window.btn_move_down.config(state='disabled')
        
        else:
            # No selection or mixed selection
            self.main_window.btn_add_question.config(state='normal' if self.main_window.current_subject else 'disabled')
            self.main_window.btn_add_lesson.config(state='normal' if self.main_window.current_subject else 'disabled')
            self.main_window.btn_edit.config(state='disabled')
            self.main_window.btn_delete.config(state='disabled')
            self.main_window.btn_move.config(state='disabled')
            self.main_window.btn_bulk_move.config(state='disabled')
            self.main_window.btn_toggle.config(state='disabled')  # NEW
            self.main_window.btn_move_up.config(state='disabled')
            self.main_window.btn_move_down.config(state='disabled')