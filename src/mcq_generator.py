"""
MCQ Generator - OpenAI-powered Medical MCQ Generation
"""

import json
import random
import re
from typing import Dict, Any, Optional

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from .config import Config

class MCQGenerator:
    """Generates medical MCQs using OpenAI GPT-4o-mini"""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = None
        
        if config.enable_mcq and OPENAI_AVAILABLE and config.openai_api_key:
            try:
                self.client = OpenAI(
                    api_key=config.openai_api_key,
                    timeout=config.mcq_timeout
                )
                print("      ✅ OpenAI client initialized for MCQ generation")
            except Exception as e:
                print(f"      ⚠️  OpenAI initialization failed: {e}")
                self.config.enable_mcq = False
        else:
            print("      ⚠️  MCQ generation disabled - missing requirements")
    
    def generate_mcq(self, abstract: str, caption: str, title: str) -> Dict[str, Any]:
        """
        Generate medical MCQ from paper abstract and figure caption
        
        Args:
            abstract: Paper abstract
            caption: Figure caption
            title: Paper title
        
        Returns:
            Dictionary with MCQ data
        """
        
        if not self.client or not caption or len(caption) < self.config.min_caption_length:
            return self._get_empty_mcq("MCQ generation skipped")
        
        try:
            prompt = self._create_mcq_prompt(abstract, caption, title)
            
            response = self.client.chat.completions.create(
                model=self.config.mcq_model,
                messages=[
                    {"role": "system", "content": "You create high-quality, image-focused MCQs for medical education with USMLE alignment."},
                    {"role": "user", "content": prompt}
                ],
                timeout=self.config.mcq_timeout
            )
            
            text = response.choices[0].message.content.strip()
            
            # Extract JSON
            start = text.find('{')
            end = text.rfind('}') + 1
            payload = text[start:end] if (start >= 0 and end > start) else text
            
            mcq_data = json.loads(payload)
            
            # Validate and enhance
            mcq_data = self._validate_mcq(mcq_data, caption)
            
            return mcq_data
            
        except json.JSONDecodeError as e:
            print(f"            ⚠️  MCQ JSON parsing failed")
            return self._get_empty_mcq("JSON parsing failed")
        except Exception as e:
            print(f"            ⚠️  MCQ generation failed: {type(e).__name__}")
            return self._get_empty_mcq(f"Error: {type(e).__name__}")
    
    def _create_mcq_prompt(self, abstract: str, caption: str, title: str) -> str:
        """Create the MCQ generation prompt"""
        
        # Randomly select which option should be correct
        correct_answer = random.choice(['A', 'B', 'C', 'D', 'E'])
        
        return f"""
You are a medical education expert creating USMLE-style MCQs. Using the abstract and figure caption below, write ONE imaging-centered MCQ.

**Paper Title:** {title}

**Abstract (context only):** {abstract}

**Figure Caption (primary source):** {caption}

**Requirements:**
1. The MCQ must be about what is visible in the image/figure. Begin with brief clinical background, then ask what the image shows.
2. Use details from the caption (modality, key visual features). Do NOT invent unsupported details.
3. Keep it clinically relevant (diagnosis, hallmark sign, staging, complication, next step based on visual finding).
4. Provide exactly 5 options (A–E) with ONE best answer.
5. **CRITICAL**: Make option {correct_answer} the correct answer. Place the best/most accurate response in option {correct_answer}.
6. Add medical hashtags for searchability (max 10, comma-separated, no # symbols).
7. Choose **subject** from USMLE categories:
   - Step 1: Anatomy, Physiology, Biochemistry, Pharmacology, Microbiology & Immunology, Pathology, Behavioral Science & Biostatistics, Genetics
   - Step 2: Internal Medicine, Surgery, Pediatrics, Obstetrics & Gynecology, Psychiatry, Neurology, Emergency Medicine, Family Medicine, Radiology, Oncology
8. Choose **difficulty_level**: easy (basic recognition), intermediate (management/differential), difficult (subspecialty nuances)
9. Provide **commentary** that summarizes the key finding and explains why the answer is correct.

**Return ONLY valid JSON:**
{{
  "mcq_question": "Clinical background + what does the image show?",
  "option_a": "Option A",
  "option_b": "Option B", 
  "option_c": "Option C",
  "option_d": "Option D",
  "option_e": "Option E",
  "answer": "{correct_answer}",
  "commentary": "Summary of key finding and explanation of correct answer",
  "hashtags": "imaging modality, anatomy, pathology, findings",
  "subject": "Radiology",
  "difficulty_level": "intermediate"
}}
""".strip()
    
    def _validate_mcq(self, mcq: Dict[str, Any], caption: str) -> Dict[str, Any]:
        """Validate and enhance MCQ data"""
        
        # Ensure all required fields exist
        required_fields = [
            'mcq_question', 'option_a', 'option_b', 'option_c', 'option_d', 'option_e',
            'answer', 'commentary', 'hashtags', 'subject', 'difficulty_level'
        ]
        
        for field in required_fields:
            mcq.setdefault(field, '')
        
        # Validate answer format
        answer = mcq.get('answer', '').upper()
        if answer not in ['A', 'B', 'C', 'D', 'E']:
            mcq['answer'] = 'A'  # Default fallback
        
        # Enhance based on caption content
        mcq = self._enhance_based_on_content(mcq, caption)
        
        return mcq
    
    def _enhance_based_on_content(self, mcq: Dict[str, Any], caption: str) -> Dict[str, Any]:
        """Enhance MCQ based on caption content"""
        
        caption_lower = (caption or '').lower()
        
        # Content-based subject refinement
        if not mcq['subject']:
            if any(word in caption_lower for word in ['ct', 'mri', 'ultrasound', 'radiograph', 'imaging', 'scan']):
                mcq['subject'] = 'Radiology'
            elif any(word in caption_lower for word in ['pathology', 'biopsy', 'histology', 'tissue']):
                mcq['subject'] = 'Pathology'
            elif any(word in caption_lower for word in ['surgery', 'surgical', 'operative']):
                mcq['subject'] = 'Surgery'
            elif any(word in caption_lower for word in ['pediatric', 'child', 'infant']):
                mcq['subject'] = 'Pediatrics'
            else:
                mcq['subject'] = 'Internal Medicine'
        
        # Content-based difficulty refinement
        if mcq['difficulty_level'] not in ['easy', 'intermediate', 'difficult']:
            if any(word in caption_lower for word in ['rare', 'unusual', 'novel']):
                mcq['difficulty_level'] = 'difficult'
            elif any(word in caption_lower for word in ['management', 'treatment', 'intervention']):
                mcq['difficulty_level'] = 'intermediate'
            else:
                mcq['difficulty_level'] = 'easy'
        
        # Extract hashtags if missing
        if not mcq['hashtags']:
            mcq['hashtags'] = self._extract_medical_tags(caption)
        
        return mcq
    

    
    def _extract_medical_tags(self, caption: str) -> str:
        """Extract medical tags using regex patterns"""
        
        caption_lower = caption.lower()
        
        # Medical term patterns
        patterns = {
            'imaging': r'\b(ct|mri|ultrasound|radiograph|x-ray|mammography|pet|spect|fluoroscopy|angiography)\b',
            'anatomy': r'\b(brain|heart|lung|liver|kidney|breast|spine|abdomen|pelvis|thorax|head|neck)\b',
            'pathology': r'\b(cancer|tumor|carcinoma|adenoma|metastasis|lesion|mass|nodule|cyst|inflammation)\b',
            'findings': r'\b(enhancement|calcification|stenosis|occlusion|hemorrhage|edema|ischemia|infarct)\b',
            'procedures': r'\b(biopsy|surgery|resection|ablation|stent|catheter|injection|contrast)\b'
        }
        
        found_tags = set()
        
        for category, pattern in patterns.items():
            matches = re.findall(pattern, caption_lower)
            found_tags.update(matches)
        
        # Add disease patterns
        disease_patterns = [
            r'\b(diabetes|hypertension|pneumonia|covid|stroke)\b',
            r'\b(myocardial\s+infarction|pulmonary\s+embolism)\b'
        ]
        
        for pattern in disease_patterns:
            matches = re.findall(pattern, caption_lower)
            found_tags.update([match.replace(' ', '_') for match in matches])
        
        return ', '.join(sorted(list(found_tags))[:8])  # Limit to 8 tags
    
    def _get_empty_mcq(self, reason: str) -> Dict[str, Any]:
        """Return empty MCQ structure"""
        
        return {
            'mcq_question': reason,
            'option_a': '', 'option_b': '', 'option_c': '', 'option_d': '', 'option_e': '',
            'answer': '', 'commentary': '', 'hashtags': '', 'subject': '', 'difficulty_level': ''
        }
    
    def get_mcq_stats(self, mcq_list: list) -> Dict[str, Any]:
        """Get statistics about generated MCQs"""
        
        total_mcqs = len(mcq_list)
        valid_mcqs = sum(1 for mcq in mcq_list if mcq.get('mcq_question') and mcq.get('answer'))
        
        # Answer distribution
        answer_counts = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0}
        for mcq in mcq_list:
            answer = mcq.get('answer', '').upper()
            if answer in answer_counts:
                answer_counts[answer] += 1
        
        # Subject distribution
        subject_counts = {}
        for mcq in mcq_list:
            subject = mcq.get('subject', 'Unknown')
            subject_counts[subject] = subject_counts.get(subject, 0) + 1
        
        # Difficulty distribution
        difficulty_counts = {}
        for mcq in mcq_list:
            difficulty = mcq.get('difficulty_level', 'Unknown')
            difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1
        
        return {
            'total_mcqs': total_mcqs,
            'valid_mcqs': valid_mcqs,
            'success_rate': round(valid_mcqs / max(1, total_mcqs) * 100, 1),
            'answer_distribution': answer_counts,
            'subject_distribution': subject_counts,
            'difficulty_distribution': difficulty_counts
        }