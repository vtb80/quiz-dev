/**
 * Answer Handler
 * Collects and validates user answers
 * Version: 2.1 - Added Dropdown support
 */

import { state } from './state.js';

/**
 * Collect answer from the current question's UI
 */
export function collectAnswer(question) {
  switch(question.type) {
    case 'multiple_choice':
    case 'true_false':
      return collectRadioAnswer();
    
    case 'multiple_choice_multiple':
      return collectCheckboxAnswer();
    
    case 'fill_in_blank':
      return collectFillBlankAnswer();
    
    case 'dropdown':
      return collectDropdownAnswer();
    
    case 'matching':
      return collectMatchingAnswer();
    
    case 'reordering':
      return collectReorderingAnswer();
    
    case 'reading_comprehension':
      return collectReadingComprehensionAnswer(question);
    
    default:
      return null;
  }
}

/**
 * Collect radio button answer (MC/TF)
 */
function collectRadioAnswer() {
  const selected = document.querySelector('input[name="answer"]:checked');
  return selected ? parseInt(selected.value) : null;
}

/**
 * Collect checkbox answer (MCM - Multiple Choice Multiple)
 */
function collectCheckboxAnswer() {
  const checkboxes = document.querySelectorAll('input[name="answer"]:checked');
  const answers = Array.from(checkboxes).map(cb => parseInt(cb.value));
  return answers.length > 0 ? answers : null;
}

/**
 * Collect fill in the blank answer
 * Supports both single-blank (old) and multi-blank (new) formats
 */
function collectFillBlankAnswer() {
  // Check if multi-blank inputs exist
  const multiInputs = document.querySelectorAll('.fill-blank-multi-input');
  
  if (multiInputs.length > 0) {
    // Multi-blank format - collect all inputs as object
    const answers = {};
    multiInputs.forEach(input => {
      const blankId = input.getAttribute('data-blank-id');
      answers[blankId] = input.value.trim();
    });
    return answers;
  } else {
    // Single-blank format - collect single input as string
    const input = document.getElementById('fillBlank');
    return input ? input.value.trim() : null;
  }
}

/**
 * Collect dropdown answer
 * Returns object mapping dropdown IDs to selected indices
 */
function collectDropdownAnswer() {
  const answer = {};
  const dropdowns = document.querySelectorAll('.dropdown-select');
  
  dropdowns.forEach(select => {
    const ddId = select.getAttribute('data-dd-id');
    const value = select.value;
    
    // Store as integer if selected, null if not
    answer[ddId] = value !== '' ? parseInt(value) : null;
  });
  
  return answer;
}

/**
 * Collect matching answer
 */
function collectMatchingAnswer() {
  const answer = {};
  document.querySelectorAll('.pair-select').forEach(select => {
    answer[select.dataset.id] = select.value;
  });
  return answer;
}

/**
 * Collect reordering answer
 */
function collectReorderingAnswer() {
  const items = document.querySelectorAll('.reordering-item');
  return Array.from(items).map(item => parseInt(item.dataset.order));
}

/**
 * Collect reading comprehension answer
 */
function collectReadingComprehensionAnswer(question) {
  const answer = {};
  question.questions.forEach((subQ, idx) => {
    const selected = document.querySelector(`input[name="reading_q${idx}"]:checked`);
    answer[idx] = selected ? parseInt(selected.value) : null;
  });
  return answer;
}

/**
 * Validate that an answer is provided
 */
export function validateAnswer(question, answer) {
  if (answer === null || answer === '') {
    return { valid: false, message: 'Please provide an answer' };
  }
  
  // Special validation for MCM (array)
  if (question.type === 'multiple_choice_multiple') {
    if (!Array.isArray(answer) || answer.length === 0) {
      return { valid: false, message: 'Please select at least one answer' };
    }
  }
  
  // Special validation for dropdown
  if (question.type === 'dropdown') {
    const allSelected = Object.values(answer).every(v => v !== null && v !== '');
    if (!allSelected) {
      return { valid: false, message: 'Please select an answer for all dropdowns' };
    }
  }
  
  // Special validation for reading comprehension
  if (question.type === 'reading_comprehension') {
    const hasAllAnswers = Object.values(answer).every(v => v !== null);
    if (!hasAllAnswers) {
      return { valid: false, message: 'Please answer all questions in the passage' };
    }
  }
  
  // Special validation for matching
  if (question.type === 'matching') {
    const hasAllSelections = Object.values(answer).every(v => v !== '');
    if (!hasAllSelections) {
      return { valid: false, message: 'Please match all pairs' };
    }
  }
  
  return { valid: true };
}

/**
 * Check if answer is correct
 */
export function checkAnswer(question, answer) {
  switch(question.type) {
    case 'multiple_choice':
    case 'true_false':
      return answer === question.correct;
    
    case 'multiple_choice_multiple':
      return checkMultipleChoiceMultiple(question, answer);
    
    case 'fill_in_blank':
      return checkFillInBlank(question, answer);
    
    case 'dropdown':
      return checkDropdown(question, answer);
    
    case 'matching':
      return checkMatching(question, answer);
    
    case 'reordering':
      return checkReordering(question, answer);
    
    case 'reading_comprehension':
      return checkReadingComprehension(question, answer);
    
    default:
      return false;
  }
}

/**
 * Check multiple choice multiple answer (EXACT MATCH required)
 */
function checkMultipleChoiceMultiple(question, answer) {
  if (!answer || !Array.isArray(answer)) {
    return false;
  }
  
  if (!question.correct || !Array.isArray(question.correct)) {
    return false;
  }
  
  // Sort both arrays and compare
  const userSorted = [...answer].sort((a, b) => a - b);
  const correctSorted = [...question.correct].sort((a, b) => a - b);
  
  // Must have same length
  if (userSorted.length !== correctSorted.length) {
    return false;
  }
  
  // Compare element by element
  return userSorted.every((val, idx) => val === correctSorted[idx]);
}

/**
 * Check fill in the blank answer
 * Supports both single-blank (old) and multi-blank (new) formats
 */
function checkFillInBlank(question, answer) {
  // Detect format
  const isMultiBlank = typeof question.correct === 'object' && !Array.isArray(question.correct);
  
  if (isMultiBlank) {
    // Multi-blank format
    return checkMultiBlankAnswer(question, answer);
  } else {
    // Single-blank format (old)
    return checkSingleBlankAnswer(question, answer);
  }
}

/**
 * Check single-blank answer (old format)
 */
function checkSingleBlankAnswer(question, answer) {
  if (!question.correct || !Array.isArray(question.correct)) {
    return false;
  }
  return question.correct.some(c => 
    c.toLowerCase() === (answer || '').toLowerCase()
  );
}

/**
 * Check multi-blank answer (new format)
 */
function checkMultiBlankAnswer(question, answer) {
  if (!answer || typeof answer !== 'object') {
    return false;
  }
  
  // Check all blanks
  for (const blankId in question.correct) {
    const acceptableAnswers = question.correct[blankId];
    const userAnswer = answer[blankId] || '';
    
    // Check if user's answer matches any acceptable answer (case-insensitive)
    const isCorrect = acceptableAnswers.some(acceptable => 
      acceptable.toLowerCase() === userAnswer.toLowerCase()
    );
    
    if (!isCorrect) {
      return false;  // If any blank is wrong, entire answer is wrong
    }
  }
  
  return true;  // All blanks are correct
}

/**
 * Check dropdown answer
 * All dropdowns must have correct selection
 */
function checkDropdown(question, answer) {
  if (!answer || typeof answer !== 'object') {
    return false;
  }
  
  // Check each dropdown
  for (const ddId in question.dropdowns) {
    const correct = question.dropdowns[ddId].correct;
    
    // User's answer must match correct index
    if (answer[ddId] !== correct) {
      return false;
    }
  }
  
  return true;  // All dropdowns correct
}

/**
 * Check matching answer
 */
function checkMatching(question, answer) {
  if (!answer || Object.keys(answer).length === 0) {
    return false;
  }
  return Object.keys(question.correct).every(key => 
    answer[key] === question.correct[key]
  );
}

/**
 * Check reordering answer
 */
function checkReordering(question, answer) {
  if (!answer) return false;
  const correctOrder = question.items.map(item => item.order);
  return JSON.stringify(answer) === JSON.stringify(correctOrder);
}

/**
 * Check reading comprehension answer
 */
function checkReadingComprehension(question, answer) {
  if (!answer || typeof answer !== 'object') {
    return false;
  }
  return question.questions.every((subQ, idx) => 
    answer[idx] === subQ.correct
  );
}

/**
 * Format user answer for display
 */
export function formatUserAnswer(question, answer) {
  if (answer === null || answer === '') {
    return 'No answer provided';
  }
  
  switch(question.type) {
    case 'multiple_choice':
      return question.options[answer] || answer;
    
    case 'multiple_choice_multiple':
      if (!Array.isArray(answer) || answer.length === 0) {
        return 'No answer provided';
      }
      // Sort and format as "A, B, D"
      const sortedAnswers = [...answer].sort((a, b) => a - b);
      return sortedAnswers.map(idx => question.options[idx]).join(', ');
    
    case 'true_false':
      return answer === 0 ? 'True' : 'False';
    
    case 'fill_in_blank':
      if (typeof answer === 'object' && answer !== null) {
        // Multi-blank format
        const parts = [];
        const blankIds = Object.keys(answer).sort((a, b) => {
          const numA = parseInt(a.replace('Q', ''));
          const numB = parseInt(b.replace('Q', ''));
          return numA - numB;
        });
        
        blankIds.forEach(blankId => {
          const displayId = blankId.replace('Q', '');
          parts.push(`Q${displayId}: ${answer[blankId] || '(empty)'}`);
        });
        
        return parts.join(', ');
      } else {
        // Single-blank format
        return answer || '(empty)';
      }
    
    case 'dropdown':
      if (!answer || typeof answer !== 'object') {
        return 'No answer provided';
      }
      
      const parts = [];
      const ddIds = Object.keys(question.dropdowns).sort((a, b) => {
        return parseInt(a.replace('DD', '')) - parseInt(b.replace('DD', ''));
      });
      
      ddIds.forEach(ddId => {
        const displayId = ddId.replace('DD', '');
        const answerIdx = answer[ddId];
        
        if (answerIdx !== null && answerIdx !== undefined) {
          const options = question.dropdowns[ddId].options;
          const answerText = options[answerIdx] || '(invalid)';
          parts.push(`DD${displayId}: ${answerText}`);
        } else {
          parts.push(`DD${displayId}: (not selected)`);
        }
      });
      
      return parts.join(', ');
    
    case 'matching':
      return Object.values(answer).join(', ');
    
    case 'reordering':
      const orderMap = {};
      question.items.forEach(item => {
        orderMap[item.order] = item.text;
      });
      return answer.map(order => orderMap[order]).join(' → ');
    
    case 'reading_comprehension':
      const results = [];
      question.questions.forEach((subQ, idx) => {
        if (answer[idx] !== undefined) {
          results.push(`Q${idx + 1}: ${subQ.options[answer[idx]]}`);
        }
      });
      return results.join(', ');
    
    default:
      return String(answer);
  }
}

/**
 * Format correct answer for display
 */
export function formatCorrectAnswer(question) {
  switch(question.type) {
    case 'multiple_choice':
      return question.options[question.correct];
    
    case 'multiple_choice_multiple':
      if (!Array.isArray(question.correct) || question.correct.length === 0) {
        return 'N/A';
      }
      // Sort and format as "A, B, D"
      const sortedCorrect = [...question.correct].sort((a, b) => a - b);
      return sortedCorrect.map(idx => question.options[idx]).join(', ');
    
    case 'true_false':
      return question.correct === 0 ? 'True' : 'False';
    
    case 'fill_in_blank':
      if (typeof question.correct === 'object' && !Array.isArray(question.correct)) {
        // Multi-blank format
        const parts = [];
        const blankIds = Object.keys(question.correct).sort((a, b) => {
          const numA = parseInt(a.replace('Q', ''));
          const numB = parseInt(b.replace('Q', ''));
          return numA - numB;
        });
        
        blankIds.forEach(blankId => {
          const displayId = blankId.replace('Q', '');
          const answers = question.correct[blankId].join(' / ');
          parts.push(`Q${displayId}: ${answers}`);
        });
        
        return parts.join(', ');
      } else {
        // Single-blank format
        return Array.isArray(question.correct) ? question.correct.join(', ') : 'N/A';
      }
    
    case 'dropdown':
      if (!question.dropdowns) {
        return 'N/A';
      }
      
      const parts = [];
      const ddIds = Object.keys(question.dropdowns).sort((a, b) => {
        return parseInt(a.replace('DD', '')) - parseInt(b.replace('DD', ''));
      });
      
      ddIds.forEach(ddId => {
        const displayId = ddId.replace('DD', '');
        const ddData = question.dropdowns[ddId];
        const correctIdx = ddData.correct;
        const correctText = ddData.options[correctIdx];
        parts.push(`DD${displayId}: ${correctText}`);
      });
      
      return parts.join(', ');
    
    case 'matching':
      return Object.values(question.correct).join(', ');
    
    case 'reordering':
      const sortedItems = [...question.items].sort((a, b) => a.order - b.order);
      return sortedItems.map(item => item.text).join(' → ');
    
    case 'reading_comprehension':
      const results = [];
      question.questions.forEach((subQ, idx) => {
        results.push(`Q${idx + 1}: ${subQ.options[subQ.correct]}`);
      });
      return results.join(', ');
    
    default:
      return 'N/A';
  }
}
