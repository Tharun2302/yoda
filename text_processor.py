"""
Text File Processor for HealthYoda Knowledge Base
Processes text files and extracts clinical interview patterns for RAG system
Specialized for HealthYoda Deepest Dive files with Q&A patterns, differentials, and red flags
"""
import os
import re
from typing import List, Dict, Tuple, Optional
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TextFileProcessor:
    """Processes text files for the knowledge base with specialized clinical pattern extraction"""

    def __init__(self, txt_folder: str = 'txt'):
        self.txt_folder = Path(txt_folder)
        self.processed_files = []
        self.stats = {
            'total_patterns': 0,
            'red_flags': 0,
            'differentials': 0,
            'questions': 0,
            'clinical_clues': 0
        }

    def get_text_files(self) -> List[Path]:
        """Get all text files from the txt folder"""
        if not self.txt_folder.exists():
            logger.warning(f"Folder {self.txt_folder} does not exist")
            return []

        # Support common text file extensions
        patterns = ['*.txt', '*.md', '*.rst']
        text_files = []

        for pattern in patterns:
            files = list(self.txt_folder.glob(pattern))
            text_files.extend(files)

        return sorted(text_files)

    def read_text_file(self, file_path: Path) -> Tuple[str, Dict]:
        """Read a text file and extract metadata"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract basic metadata
            metadata = {
                'filename': file_path.name,
                'filepath': str(file_path),
                'file_size': file_path.stat().st_size,
                'extension': file_path.suffix,
                'last_modified': file_path.stat().st_mtime,
            }

            return content, metadata

        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return "", {}

    def process_text_content(self, content: str, metadata: Dict) -> List[Dict]:
        """Process text content into clinical patterns for embedding"""
        filename = metadata.get('filename', 'unknown')

        # Check if this is a HealthYoda Deepest Dive file
        if 'HealthYoda_DeepestDive' in filename or 'DeepestDive' in content[:500]:
            return self._process_deepest_dive_file(content, metadata)
        else:
            # Use generic processing for other text files
            return self._process_generic_text_file(content, metadata)

    def _process_deepest_dive_file(self, content: str, metadata: Dict) -> List[Dict]:
        """Process HealthYoda Deepest Dive files with specialized extraction"""
        filename = metadata.get('filename', 'unknown')
        
        # Extract medical domain from filename
        medical_domain = self._extract_medical_domain(filename)
        
        logger.info(f"Processing {filename} - Medical Domain: {medical_domain}")

        all_patterns = []

        # Split content into sections by section headers (lines with ===)
        sections = self._split_into_sections(content)

        for section_data in sections:
            section_title = section_data['title']
            section_content = section_data['content']
            
            if not section_content.strip():
                continue

            logger.info(f"  Processing section: {section_title}")

            # Extract all pattern types from this section
            patterns = self._extract_section_patterns(
                section_content, 
                medical_domain, 
                section_title, 
                metadata
            )

            all_patterns.extend(patterns)
            logger.info(f"    Extracted {len(patterns)} patterns")

        logger.info(f"Total patterns extracted from {filename}: {len(all_patterns)}")
        return all_patterns

    def _extract_medical_domain(self, filename: str) -> str:
        """Extract medical domain from filename"""
        # Remove common suffixes
        domain = filename.replace('_Master', '').replace('_HealthYoda_DeepestDive_FULL.txt', '')
        domain = domain.replace('HealthYoda_DeepestDive_FULL.txt', '')
        domain = domain.replace('.txt', '')
        return domain

    def _split_into_sections(self, content: str) -> List[Dict]:
        """Split content into sections based on === delimiters"""
        sections = []
        
        # Split by section delimiter
        section_blocks = re.split(r'\n={3,}\n', content)
        
        for block in section_blocks:
            block = block.strip()
            if not block or len(block) < 20:
                continue
            
            # Extract section title (first line)
            lines = block.split('\n')
            section_title = lines[0].strip()
            
            # Skip header/intro sections
            if any(skip in section_title.upper() for skip in ['TABLE OF CONTENTS', 'OVERVIEW', 'CLUSTERS', 'FULL VERSION']):
                continue
            
            # Clean section title
            section_title = re.sub(r'^SECTION \d+\s*[—-]\s*', '', section_title, flags=re.IGNORECASE)
            
            # Section content is everything after first line
            section_content = '\n'.join(lines[1:])
            
            sections.append({
                'title': section_title,
                'content': section_content
            })
        
        return sections

    def _extract_section_patterns(self, section_content: str, medical_domain: str, 
                                  section_title: str, metadata: Dict) -> List[Dict]:
        """Extract all types of clinical patterns from a section"""
        patterns = []
        
        # 1. Extract RED FLAGS (highest priority)
        red_flags = self._extract_red_flags(section_content)
        if red_flags:
            for i, red_flag in enumerate(red_flags):
                pattern = {
                    'medical_domain': medical_domain,
                    'section': section_title,
                    'content_type': 'red_flag',
                    'bot_question': f"URGENT: Check for {red_flag.lower()}",
                    'clinical_context': f"RED FLAG for {section_title}: {red_flag}",
                    'expected_patient_responses': [],
                    'red_flags': [red_flag],
                    'priority': 'CRITICAL',
                    'tags': [
                        f'clinical_domain:{medical_domain}',
                        f'section:{section_title}',
                        'content_type:red_flag',
                        'priority:CRITICAL',
                        'source:deepest_dive'
                    ],
                    'tree_path': f"{medical_domain} > {section_title} > Red Flags > {i+1}",
                    'source': 'deepest_dive',
                    'metadata': metadata
                }
                patterns.append(pattern)
                self.stats['red_flags'] += 1

        # 2. Extract CLINICAL DIFFERENTIALS
        differentials = self._extract_clinical_differentials(section_content)
        if differentials:
            # Group differentials by subsection
            diff_groups = self._group_differentials(section_content)
            
            for subsection, diff_list in diff_groups.items():
                pattern = {
                    'medical_domain': medical_domain,
                    'section': section_title,
                    'content_type': 'differential',
                    'bot_question': f"What conditions should be considered for {subsection or section_title}?",
                    'clinical_context': f"Clinical differentials for {subsection or section_title}: {', '.join(diff_list)}",
                    'expected_patient_responses': [],
                    'red_flags': red_flags,  # Include red flags from section
                    'priority': 'HIGH',
                    'tags': [
                        f'clinical_domain:{medical_domain}',
                        f'section:{section_title}',
                        'content_type:differential',
                        'priority:HIGH',
                        'source:deepest_dive'
                    ],
                    'tree_path': f"{medical_domain} > {section_title} > Differentials > {subsection or 'Main'}",
                    'source': 'deepest_dive',
                    'metadata': metadata,
                    'differentials': diff_list
                }
                patterns.append(pattern)
                self.stats['differentials'] += 1

        # 3. Extract Q&A PATTERNS (interview questions)
        qa_patterns = self._extract_qa_patterns(section_content)
        if qa_patterns:
            for i, (bot_question, patient_responses) in enumerate(qa_patterns):
                pattern = {
                    'medical_domain': medical_domain,
                    'section': section_title,
                    'content_type': 'interview_question',
                    'bot_question': bot_question,
                    'clinical_context': f"Interview question for {section_title} in {medical_domain}",
                    'expected_patient_responses': patient_responses,
                    'red_flags': red_flags,  # Include red flags from section
                    'priority': 'NORMAL',
                    'tags': [
                        f'clinical_domain:{medical_domain}',
                        f'section:{section_title}',
                        'content_type:question',
                        'priority:NORMAL',
                        'source:deepest_dive'
                    ],
                    'tree_path': f"{medical_domain} > {section_title} > Interview Questions > {i+1}",
                    'source': 'deepest_dive',
                    'metadata': metadata
                }
                patterns.append(pattern)
                self.stats['questions'] += 1

        # 4. Extract CLINICAL CLUES (symptom patterns)
        clinical_clues = self._extract_clinical_clues(section_content)
        if clinical_clues:
            for subsection, clues in clinical_clues.items():
                pattern = {
                    'medical_domain': medical_domain,
                    'section': section_title,
                    'content_type': 'clinical_clue',
                    'bot_question': f"What clinical clues suggest {subsection}?",
                    'clinical_context': f"Clinical clues for {subsection}: {', '.join(clues)}",
                    'expected_patient_responses': clues,
                    'red_flags': red_flags,  # Include red flags from section
                    'priority': 'NORMAL',
                    'tags': [
                        f'clinical_domain:{medical_domain}',
                        f'section:{section_title}',
                        'content_type:clinical_clue',
                        'priority:NORMAL',
                        'source:deepest_dive'
                    ],
                    'tree_path': f"{medical_domain} > {section_title} > Clinical Clues > {subsection}",
                    'source': 'deepest_dive',
                    'metadata': metadata,
                    'clinical_clues': clues
                }
                patterns.append(pattern)
                self.stats['clinical_clues'] += 1

        self.stats['total_patterns'] += len(patterns)
        return patterns

    def _extract_red_flags(self, text: str) -> List[str]:
        """Extract red flags from text"""
        red_flags = []
        lines = text.split('\n')

        in_red_flags = False
        for line in lines:
            line = line.strip()

            # Start of red flags section
            if re.match(r'^RED FLAGS?:', line, re.IGNORECASE):
                in_red_flags = True
                continue
            
            # End of red flags section (new section starts)
            if in_red_flags and (line.startswith('=') or 
                                 (line and line[0].isupper() and ':' in line and not line.startswith('-'))):
                break
            
            # Extract red flag bullet points
            if in_red_flags and line.startswith('-'):
                red_flag = line[1:].strip()
                if red_flag and len(red_flag) > 3:
                    red_flags.append(red_flag)

        return red_flags

    def _extract_clinical_differentials(self, text: str) -> List[str]:
        """Extract clinical differentials from bullet lists"""
        differentials = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            
            # Look for bullet points that are likely differentials (not questions or red flags)
            if line.startswith('-') and len(line) > 3:
                content = line[1:].strip()
                
                # Skip if it's a question, red flag section, or very long (likely not a differential)
                if any(indicator in content.lower() for indicator in 
                       ['?', 'red flag', 'how', 'what', 'when', 'where', 'why', 'do you', 'have you']):
                    continue
                
                # Skip very long lines (likely descriptions, not differential names)
                if len(content) > 100:
                    continue
                
                # Skip if it looks like a symptom description
                if any(word in content.lower() for word in ['pain', 'fever', 'severe', 'sudden', 'worse']):
                    continue
                
                differentials.append(content)

        return differentials

    def _group_differentials(self, text: str) -> Dict[str, List[str]]:
        """Group differentials by subsection headers"""
        groups = {}
        lines = text.split('\n')
        
        current_subsection = None
        
        for line in lines:
            line = line.strip()
            
            # Look for subsection headers (ALL CAPS with colon, before red flags)
            if re.match(r'^[A-Z][A-Z\s]+:', line) and 'RED FLAG' not in line:
                current_subsection = line.rstrip(':').strip()
                groups[current_subsection] = []
            
            # Look for differential bullet points under current subsection
            elif current_subsection and line.startswith('-'):
                content = line[1:].strip()
                
                # Filter out non-differential content
                if (content and len(content) > 3 and len(content) < 100 and
                    not any(indicator in content.lower() for indicator in 
                           ['?', 'how', 'what', 'when', 'where', 'why', 'do you', 'have you'])):
                    groups[current_subsection].append(content)
        
        # Remove empty groups
        return {k: v for k, v in groups.items() if v}

    def _extract_qa_patterns(self, text: str) -> List[Tuple[str, List[str]]]:
        """Extract Q&A patterns where Q is bot question and A contains patient responses"""
        qa_patterns = []
        lines = text.split('\n')
        
        current_question = None
        current_answers = []
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Look for question markers
            if re.match(r'^Q\d*[:\.]?\s*$', line) or line.startswith('Q:') or line.startswith('Q.'):
                # Save previous Q&A if exists
                if current_question and current_answers:
                    qa_patterns.append((current_question, current_answers))
                
                # Extract question - could be on same line or next line
                if line in ['Q:', 'Q.', 'Q']:
                    # Question is on next line(s)
                    i += 1
                    question_lines = []
                    while i < len(lines) and lines[i].strip().startswith('-'):
                        question_lines.append(lines[i].strip()[1:].strip().strip('"'))
                        i += 1
                    current_question = ' '.join(question_lines) if question_lines else None
                    i -= 1  # Back up one since we'll increment at end of loop
                else:
                    # Question is on same line
                    current_question = re.sub(r'^Q\d*[:\.]?\s*', '', line).strip().strip('"')
                
                current_answers = []
            
            # Look for answer markers
            elif re.match(r'^A\d*[:\.]?\s*$', line) or line.startswith('A:') or line.startswith('A.'):
                # Extract answers - could be on same line or following lines
                if line in ['A:', 'A.', 'A']:
                    # Answers are on following lines
                    i += 1
                    while i < len(lines) and lines[i].strip().startswith('-'):
                        answer = lines[i].strip()[1:].strip().strip('"')
                        if answer:
                            current_answers.append(answer)
                        i += 1
                    i -= 1  # Back up one
                else:
                    # Answer is on same line
                    answer = re.sub(r'^A\d*[:\.]?\s*', '', line).strip().strip('"')
                    if answer:
                        current_answers.append(answer)
            
            # Continuation of answers
            elif current_question and line.startswith('-') and not any(
                keyword in text[max(0, text.find(line)-50):text.find(line)].upper() 
                for keyword in ['RED FLAG', 'CLUES:', 'COMMON:', 'TYPES:']
            ):
                answer = line[1:].strip().strip('"')
                if answer and '?' not in answer:  # Not a question
                    current_answers.append(answer)
            
            i += 1

        # Add final Q&A pattern
        if current_question and current_answers:
            qa_patterns.append((current_question, current_answers))

        return qa_patterns

    def _extract_clinical_clues(self, text: str) -> Dict[str, List[str]]:
        """Extract clinical clues (symptom patterns) organized by condition"""
        clues = {}
        lines = text.split('\n')
        
        current_condition = None
        in_clues_section = False
        
        for line in lines:
            line = line.strip()
            
            # Look for "CLUES:" section header
            if re.match(r'^CLUES?:', line, re.IGNORECASE):
                in_clues_section = True
                current_condition = "General"
                clues[current_condition] = []
                continue
            
            # Look for condition headers (ALL CAPS with colon)
            if re.match(r'^[A-Z][A-Z\s\(\)/]+:', line) and 'RED FLAG' not in line and 'Q:' not in line:
                in_clues_section = False
                current_condition = line.rstrip(':').strip()
                clues[current_condition] = []
                continue
            
            # Extract clue bullet points
            if current_condition and line.startswith('-'):
                clue = line[1:].strip()
                # Filter out questions and very long descriptions
                if clue and len(clue) > 3 and len(clue) < 150 and '?' not in clue:
                    clues[current_condition].append(clue)
            
            # Stop at red flags or Q&A section
            if re.match(r'^RED FLAGS?:|^Q\d*[:\.]?', line, re.IGNORECASE):
                break
        
        # Remove empty groups
        return {k: v for k, v in clues.items() if v}

    def _process_generic_text_file(self, content: str, metadata: Dict) -> List[Dict]:
        """Process generic text files with basic paragraph splitting"""
        filename = metadata.get('filename', 'unknown')
        patterns = []

        # Split content into paragraphs
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip() and len(p.strip()) > 50]

        for i, paragraph in enumerate(paragraphs):
            pattern = {
                'medical_domain': 'General',
                'section': filename.replace('.txt', '').replace('_', ' ').title(),
                'content_type': 'general_information',
                'bot_question': f"What information is available about {filename}?",
                'clinical_context': paragraph[:500] + '...' if len(paragraph) > 500 else paragraph,
                'expected_patient_responses': [],
                'red_flags': [],
                'priority': 'LOW',
                'tags': [
                    'clinical_domain:General',
                    f'section:{filename}',
                    'content_type:general_information',
                    'priority:LOW',
                    'source:text_file'
                ],
                'tree_path': f"Text Files > {filename} > Section {i+1}",
                'source': 'text_file',
                'metadata': metadata
            }
            patterns.append(pattern)

        return patterns

    def extract_all_text_data(self) -> List[Dict]:
        """Extract all data from text files"""
        all_patterns = []
        text_files = self.get_text_files()

        logger.info(f"[TXT] Found {len(text_files)} text files to process")

        for file_path in text_files:
            logger.info(f"[TXT] Processing: {file_path.name}")

            content, metadata = self.read_text_file(file_path)
            if content:
                patterns = self.process_text_content(content, metadata)
                all_patterns.extend(patterns)
                logger.info(f"[TXT] Extracted {len(patterns)} patterns from {file_path.name}")

        logger.info(f"[TXT] Total patterns extracted: {len(all_patterns)}")
        logger.info(f"[TXT] Stats: {self.stats}")
        
        return all_patterns

    def get_stats(self) -> Dict:
        """Get statistics about processed text files"""
        text_files = self.get_text_files()
        total_size = sum(f.stat().st_size for f in text_files) if text_files else 0

        return {
            'total_files': len(text_files),
            'total_size_bytes': total_size,
            'file_names': [f.name for f in text_files],
            'extraction_stats': self.stats
        }


def test_text_processor():
    """Test function for the text processor"""
    processor = TextFileProcessor()
    
    # Test processing
    patterns = processor.extract_all_text_data()
    stats = processor.get_stats()

    print("\n" + "="*80)
    print("TEXT PROCESSOR TEST RESULTS")
    print("="*80)
    print(f"Files found: {stats['total_files']}")
    print(f"Total patterns extracted: {len(patterns)}")
    print(f"Extraction stats: {stats['extraction_stats']}")
    
    if patterns:
        print("\n" + "-"*80)
        print("SAMPLE PATTERNS")
        print("-"*80)
        
        # Show sample of each type
        for content_type in ['red_flag', 'differential', 'interview_question', 'clinical_clue']:
            samples = [p for p in patterns if p.get('content_type') == content_type]
            if samples:
                print(f"\n{content_type.upper()} (showing 1 of {len(samples)}):")
                sample = samples[0]
                print(f"  Domain: {sample['medical_domain']}")
                print(f"  Section: {sample['section']}")
                print(f"  Question: {sample['bot_question']}")
                print(f"  Priority: {sample['priority']}")
                if sample.get('expected_patient_responses'):
                    print(f"  Sample Responses: {sample['expected_patient_responses'][:2]}")


if __name__ == "__main__":
    test_text_processor()
