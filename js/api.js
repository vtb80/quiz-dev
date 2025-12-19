/**
 * API Module - Data Loading
 * Handles fetching JSON files and filtering disabled items
 * Version: 2.0 - Added enable/disable filtering
 */

import { CONFIG } from './config.js';

/**
 * Discover available subjects by trying to fetch JSON files
 * @returns {Promise<string[]>} Array of available subject names
 */
export async function loadAvailableSubjects() {
  const availableSubjects = [];
  
  for (const subject of CONFIG.POSSIBLE_SUBJECTS) {
    try {
      const response = await fetch(`questions/questions-${subject}.json`);
      if (response.ok) {
        availableSubjects.push(subject);
      }
    } catch (error) {
      // Subject file doesn't exist, skip
      console.debug(`Subject '${subject}' not found`);
    }
  }
  
  return availableSubjects;
}

/**
 * Load subject data from JSON file and filter disabled items
 * @param {string} subjectName - Subject name (e.g., 'sample', 'science')
 * @returns {Promise<Object>} Subject data with lessons and questions (enabled only)
 */
export async function loadSubjectData(subjectName) {
  try {
    const response = await fetch(`questions/questions-${subjectName}.json`);
    
    if (!response.ok) {
      throw new Error(`Failed to load subject: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    // Validate structure
    if (!data.questions || !Array.isArray(data.questions)) {
      throw new Error('Invalid data format: missing questions array');
    }
    
    // Ensure lessons array exists
    if (!data.lessons) {
      data.lessons = [];
    }
    
    // ===== FILTER DISABLED ITEMS =====
    console.log(`[FILTER] Original data: ${data.lessons.length} lessons, ${data.questions.length} questions`);
    
    // Filter out disabled lessons
    data.lessons = data.lessons.filter(lesson => lesson.enabled !== false);
    console.log(`[FILTER] After lesson filter: ${data.lessons.length} lessons`);
    
    // Filter out disabled questions
    data.questions = data.questions.filter(q => q.enabled !== false);
    console.log(`[FILTER] After question filter: ${data.questions.length} questions`);
    
    // Create set of enabled lesson IDs for quick lookup
    const enabledLessonIds = new Set(data.lessons.map(l => l.id));
    
    // Filter questions: remove questions from disabled lessons
    // Keep questions with lessonId = null (Others category)
    const originalQuestionCount = data.questions.length;
    data.questions = data.questions.filter(q => 
      q.lessonId === null || enabledLessonIds.has(q.lessonId)
    );
    
    const filteredByLesson = originalQuestionCount - data.questions.length;
    if (filteredByLesson > 0) {
      console.log(`[FILTER] Filtered ${filteredByLesson} question(s) from disabled lessons`);
    }
    
    console.log(`[FILTER] Final data: ${data.lessons.length} lessons, ${data.questions.length} questions`);
    // ===== END FILTER =====
    
    return data;
    
  } catch (error) {
    console.error('Error loading subject data:', error);
    throw error;
  }
}