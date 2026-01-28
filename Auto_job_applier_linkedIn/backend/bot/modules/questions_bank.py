'''
Author:     Leonardo Fragoso (adapted)
System:     Questions Bank Manager
Purpose:    Manage and deduplicate job application questions for reuse
'''

import json
import hashlib
import os
import re
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

def print_lg(message):
    """Simple logging function for questions bank"""
    print(f"[Questions Bank] {message}")

class QuestionsBank:
    def __init__(self, db_path: str = "data/questions_bank.json"):
        self.db_path = db_path
        self.questions: Dict[str, Dict[str, Any]] = {}
        self._ensure_db_exists()
        self._load_questions()
    
    def _ensure_db_exists(self):
        """Ensure database directory and file exist"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if not os.path.exists(self.db_path):
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
    
    def _load_questions(self):
        """Load questions from JSON file"""
        try:
            with open(self.db_path, 'r', encoding='utf-8') as f:
                self.questions = json.load(f)
            print_lg(f"✅ Loaded {len(self.questions)} questions from bank")
        except Exception as e:
            print_lg(f"⚠️ Error loading questions bank: {e}")
            self.questions = {}
    
    def _save_questions(self):
        """Save questions to JSON file"""
        try:
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump(self.questions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print_lg(f"❌ Error saving questions bank: {e}")
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for better matching (remove extra spaces, lowercase)"""
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single
        text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
        return text
    
    def _generate_question_hash(self, label: str, question_type: str) -> str:
        """Generate unique hash for question based on normalized label"""
        normalized = self._normalize_text(label)
        hash_input = f"{normalized}_{question_type}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]
    
    def add_question(self, label: str, answer: str, question_type: str, 
                    options: Optional[List[str]] = None, prev_answer: Optional[str] = None,
                    job_id: Optional[str] = None, job_title: Optional[str] = None) -> bool:
        """
        Add or update a question in the bank
        
        Args:
            label: Question text/label
            answer: Answer provided
            question_type: Type of question (select, radio, text, textarea, checkbox)
            options: List of available options (for select/radio)
            prev_answer: Previous answer (if any)
            job_id: LinkedIn job ID
            job_title: Job title where question appeared
        
        Returns:
            bool: True if new question, False if updated existing
        """
        question_hash = self._generate_question_hash(label, question_type)
        
        is_new = question_hash not in self.questions
        
        if is_new:
            self.questions[question_hash] = {
                "label": label,
                "normalized_label": self._normalize_text(label),
                "type": question_type,
                "answer": answer,
                "options": options or [],
                "first_seen": datetime.now().isoformat(),
                "last_seen": datetime.now().isoformat(),
                "times_seen": 1,
                "jobs": [{"job_id": job_id, "job_title": job_title, "date": datetime.now().isoformat()}] if job_id else [],
                "verified": False,  # User needs to verify
                "notes": ""
            }
            print_lg(f"📝 NEW question added to bank: '{label[:60]}...'")
        else:
            # Update existing question
            self.questions[question_hash]["last_seen"] = datetime.now().isoformat()
            self.questions[question_hash]["times_seen"] += 1
            
            # Update answer if different and not empty
            if answer and answer != self.questions[question_hash]["answer"]:
                print_lg(f"🔄 Updated answer for '{label[:40]}...' from '{self.questions[question_hash]['answer']}' to '{answer}'")
                self.questions[question_hash]["answer"] = answer
            
            # Add job to list if provided
            if job_id and not any(j.get("job_id") == job_id for j in self.questions[question_hash].get("jobs", [])):
                self.questions[question_hash].setdefault("jobs", []).append({
                    "job_id": job_id,
                    "job_title": job_title,
                    "date": datetime.now().isoformat()
                })
        
        self._save_questions()
        return is_new
    
    def get_answer(self, label: str, question_type: str) -> Optional[str]:
        """
        Get stored answer for a question
        
        Args:
            label: Question text/label
            question_type: Type of question
        
        Returns:
            str: Stored answer or None if not found
        """
        question_hash = self._generate_question_hash(label, question_type)
        
        if question_hash in self.questions:
            question = self.questions[question_hash]
            # Only return if verified or seen multiple times
            if question.get("verified") or question.get("times_seen", 0) > 1:
                print_lg(f"💡 Using stored answer for '{label[:50]}...': '{question['answer']}'")
                return question["answer"]
        
        return None
    
    def search_similar(self, label: str, threshold: float = 0.8) -> List[Dict[str, Any]]:
        """
        Search for similar questions using fuzzy matching
        
        Args:
            label: Question text to search
            threshold: Similarity threshold (0-1)
        
        Returns:
            List of similar questions with similarity scores
        """
        from difflib import SequenceMatcher
        
        normalized_input = self._normalize_text(label)
        results = []
        
        for q_hash, question in self.questions.items():
            similarity = SequenceMatcher(None, normalized_input, question["normalized_label"]).ratio()
            if similarity >= threshold:
                results.append({
                    "hash": q_hash,
                    "question": question,
                    "similarity": similarity
                })
        
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results
    
    def get_unverified_count(self) -> int:
        """Get count of unverified questions"""
        return sum(1 for q in self.questions.values() if not q.get("verified", False))
    
    def mark_verified(self, question_hash: str, verified: bool = True):
        """Mark a question as verified by user"""
        if question_hash in self.questions:
            self.questions[question_hash]["verified"] = verified
            self._save_questions()
    
    def update_answer(self, question_hash: str, new_answer: str):
        """Update answer for a specific question"""
        if question_hash in self.questions:
            self.questions[question_hash]["answer"] = new_answer
            self.questions[question_hash]["verified"] = True
            self._save_questions()
            print_lg(f"✅ Updated answer for question {question_hash}")
    
    def export_for_review(self) -> List[Dict[str, Any]]:
        """Export all questions for review interface"""
        questions_list = []
        for q_hash, question in self.questions.items():
            questions_list.append({
                "hash": q_hash,
                **question
            })
        
        # Sort by last_seen (most recent first)
        questions_list.sort(key=lambda x: x.get("last_seen", ""), reverse=True)
        return questions_list
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the questions bank"""
        total = len(self.questions)
        verified = sum(1 for q in self.questions.values() if q.get("verified", False))
        by_type = {}
        
        for question in self.questions.values():
            q_type = question.get("type", "unknown")
            by_type[q_type] = by_type.get(q_type, 0) + 1
        
        return {
            "total_questions": total,
            "verified_questions": verified,
            "unverified_questions": total - verified,
            "by_type": by_type
        }


# Global instance
_questions_bank_instance = None

def get_questions_bank() -> QuestionsBank:
    """Get global questions bank instance (singleton)"""
    global _questions_bank_instance
    if _questions_bank_instance is None:
        _questions_bank_instance = QuestionsBank()
    return _questions_bank_instance
