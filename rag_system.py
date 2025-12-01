"""
RAG System for HealthYoda Question Book
Extracts questions and answers from the .docx file and provides semantic retrieval using vector database
"""
import docx
import os
from typing import List, Dict, Optional, Tuple
import json

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("[WARNING] ChromaDB not installed - vector database features disabled")

class QuestionBookRAG:
    """RAG system for retrieving relevant questions from the Question Book"""
    
    def __init__(self, docx_path: str = 'docx/Question BOOK.docx', openai_client=None):
        self.docx_path = docx_path
        self.questions = []
        self.sections = []
        self.openai_client = openai_client
        
        # Initialize ChromaDB for vector storage (if available)
        self.chroma_client = None
        self.collection = None
        
        if CHROMADB_AVAILABLE:
            try:
                # Use new ChromaDB client API (no deprecated Settings)
                self.chroma_client = chromadb.PersistentClient(path="./chroma_db")
                
                # Create or get collection
                self.collection = self.chroma_client.get_or_create_collection(
                    name="question_book",
                    metadata={"description": "HealthYoda Question Book embeddings"}
                )
            except Exception as e:
                print(f"[WARNING] ChromaDB initialization failed: {e}")
                import traceback
                traceback.print_exc()
                self.chroma_client = None
                self.collection = None
        
        # Load document and create embeddings
        self.load_document()
        
        # Check if rebuild is requested via environment variable
        rebuild_vectorstore = os.getenv('REBUILD_VECTORSTORE', 'false').lower() == 'true'
        
        if self.collection:
            self.create_embeddings(force_rebuild=rebuild_vectorstore)
    
    def load_document(self):
        """Load and parse the .docx document"""
        if not os.path.exists(self.docx_path):
            raise FileNotFoundError(f"Question book not found at {self.docx_path}")
        
        doc = docx.Document(self.docx_path)
        current_system = None
        current_symptom = None
        current_category = None
        current_question = None
        current_answers = []
        
        # Categories that indicate question sections
        categories = ['Chief Complaint', 'Onset/Duration', 'Quality/Severity', 
                     'Aggravating/Relieving', 'Associated Symptoms', 'Red Flags', 
                     'ROS', 'Context']
        
        # Exclude patterns
        exclude_patterns = ['Table of Contents', 'HealthYoda History-Taking Handbook', 
                           'comprehensive system-wise', 'A comprehensive', '[page]']
        
        for i, para in enumerate(doc.paragraphs):
            text = para.text.strip()
            
            if not text:
                continue
            
            # Skip excluded patterns
            if any(pattern in text for pattern in exclude_patterns):
                continue
            
            # Detect system headers - look for "HealthYoda History Framework" pattern
            if 'HealthYoda History Framework' in text:
                # Extract system name - it comes after the framework text
                if 'Cardiac' in text:
                    current_system = 'Cardiac System'
                elif 'Respiratory' in text:
                    current_system = 'Respiratory System'
                elif 'GI System' in text or ('GI' in text and 'System' in text):
                    current_system = 'GI System'
                elif 'Neurologic' in text:
                    current_system = 'Neurologic System'
                elif 'Musculoskeletal' in text:
                    current_system = 'Musculoskeletal System'
                elif 'GU System' in text or ('GU' in text and 'System' in text):
                    current_system = 'GU System'
                elif 'Dermatologic' in text:
                    current_system = 'Dermatologic System'
                elif 'Endocrine' in text or 'General' in text:
                    current_system = 'General/Endocrine/Infectious Disease System'
                elif 'ENT' in text or 'Eye' in text:
                    current_system = 'ENT/Eye System'
                
                if current_system:
                    current_symptom = None
                    current_category = None
                    current_question = None
                    current_answers = []
            
            # Detect symptom/complaint headers - standalone lines that aren't categories or questions
            elif current_system and text not in categories and \
                 not text.startswith('Q') and not text.startswith('Possible') and \
                 not text.startswith('-') and len(text) < 100 and \
                 text != current_system and 'System' not in text and \
                 'HealthYoda' not in text and text != 'Wrap-up':
                # This is likely a symptom/complaint name
                # Save previous question before changing symptom
                if current_question and current_system:
                    self._save_question(current_system, current_symptom, current_category,
                                      current_question, current_answers.copy(), i)
                    current_question = None
                    current_answers = []
                
                current_symptom = text
                current_category = None
            
            # Detect category headers
            elif text in categories:
                # Save previous question before changing category
                if current_question and current_system:
                    self._save_question(current_system, current_symptom, current_category,
                                      current_question, current_answers.copy(), i)
                    current_question = None
                    current_answers = []
                
                current_category = text
            
            # Detect questions - lines starting with Q: or Q.
            elif text.startswith('Q:') or text.startswith('Q.'):
                # Save previous question if exists
                if current_question and current_system:
                    self._save_question(current_system, current_symptom, current_category,
                                      current_question, current_answers.copy(), i)
                
                current_question = text.replace('Q:', '').replace('Q.', '').strip()
                current_answers = []
            
            # Detect possible answers
            elif text.startswith('Possible Answers:') or text.startswith('Possible answers:'):
                current_answers = []
            
            elif text.startswith('-') and current_question:
                answer = text[1:].strip()
                if answer:
                    current_answers.append(answer)
        
        # Save last question
        if current_question and current_system:
            self._save_question(current_system, current_symptom, current_category,
                              current_question, current_answers.copy(), len(doc.paragraphs))
        
        systems_found = len(set(q['system'] for q in self.questions if q.get('system')))
        print(f"Loaded {len(self.questions)} questions from {systems_found} systems")
    
    def _save_question(self, system, symptom, category, question, answers, line_number):
        """Helper method to save a question with tags"""
        tags = []
        if system:
            tags.append(f"system:{system}")
        if symptom:
            tags.append(f"symptom:{symptom}")
        if category:
            tags.append(f"category:{category}")
        
        tree_path = " > ".join(filter(None, [system, symptom, category]))
        
        self.questions.append({
            'system': system,
            'symptom': symptom,
            'category': category,
            'question': question,
            'possible_answers': answers,
            'line_number': line_number,
            'tags': tags,
            'tree_path': tree_path
        })
    
    def create_embeddings(self, force_rebuild: bool = False):
        """
        Create embeddings for all questions and store in vector database
        
        Args:
            force_rebuild: If True, rebuild embeddings even if they exist
        """
        if not self.collection:
            print("[WARNING] Vector database not available - skipping embeddings. Using keyword search only.")
            return
            
        if not self.openai_client:
            print("[WARNING] OpenAI client not available - skipping embeddings. Using keyword search only.")
            return
        
        # Check if collection already has data (unless force rebuild)
        if not force_rebuild and self.collection.count() > 0:
            print(f"[OK] Vector database already has {self.collection.count()} embeddings")
            print(f"   Set REBUILD_VECTORSTORE=true in .env to rebuild")
            return
        
        if force_rebuild and self.collection.count() > 0:
            print(f"[INFO] Rebuilding vector database (current: {self.collection.count()} embeddings)...")
            # Delete existing collection and recreate
            self.chroma_client.delete_collection(name="question_book")
            self.collection = self.chroma_client.create_collection(
                name="question_book",
                metadata={"description": "HealthYoda Question Book embeddings"}
            )
        
        print(f"Creating embeddings for {len(self.questions)} questions...")
        
        # Create text for embedding (combine question + context)
        texts_to_embed = []
        ids = []
        metadatas = []
        
        for idx, q in enumerate(self.questions):
            # Create rich text for embedding: question + system + symptom + category + answers
            text_parts = []
            if q.get('question'):
                text_parts.append(q['question'])
            if q.get('system'):
                text_parts.append(f"System: {q['system']}")
            if q.get('symptom'):
                text_parts.append(f"Symptom: {q['symptom']}")
            if q.get('category'):
                text_parts.append(f"Category: {q['category']}")
            if q.get('possible_answers'):
                text_parts.append(f"Possible answers: {', '.join(q['possible_answers'][:5])}")
            
            full_text = " | ".join(text_parts)
            texts_to_embed.append(full_text)
            ids.append(f"q_{idx}")
            metadatas.append({
                'system': q.get('system', ''),
                'symptom': q.get('symptom', ''),
                'category': q.get('category', ''),
                'question': q.get('question', ''),
                'tree_path': q.get('tree_path', ''),
                'index': idx
            })
        
        # Create embeddings in batches
        batch_size = 100
        for i in range(0, len(texts_to_embed), batch_size):
            batch_texts = texts_to_embed[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            batch_metadatas = metadatas[i:i+batch_size]
            
            try:
                # Get embeddings from OpenAI
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",  # Cost-effective embedding model
                    input=batch_texts
                )
                
                embeddings = [item.embedding for item in response.data]
                
                # Add to ChromaDB
                self.collection.add(
                    embeddings=embeddings,
                    documents=batch_texts,
                    ids=batch_ids,
                    metadatas=batch_metadatas
                )
                
                print(f"  Processed {min(i+batch_size, len(texts_to_embed))}/{len(texts_to_embed)} questions...")
            except Exception as e:
                print(f"  Error creating embeddings for batch {i}: {e}")
                continue
        
        print(f"[OK] Created {self.collection.count()} embeddings in vector database")
    
    def search_by_system(self, system_name: str) -> List[Dict]:
        """Retrieve all questions for a specific system"""
        return [q for q in self.questions if system_name.lower() in q['system'].lower()]
    
    def search_by_symptom(self, symptom: str) -> List[Dict]:
        """Retrieve questions for a specific symptom/complaint"""
        symptom_lower = symptom.lower()
        return [q for q in self.questions 
                if q['symptom'] and symptom_lower in q['symptom'].lower()]
    
    def search_by_category(self, category: str) -> List[Dict]:
        """Retrieve questions for a specific category (e.g., 'Onset/Duration', 'Red Flags')"""
        return [q for q in self.questions if q['category'] == category]
    
    def search_by_keywords(self, keywords: List[str], system: Optional[str] = None) -> List[Dict]:
        """Search questions by keywords in question text"""
        results = []
        keywords_lower = [k.lower() for k in keywords]
        
        for q in self.questions:
            if system and system.lower() not in q['system'].lower():
                continue
            
            question_lower = q['question'].lower()
            if any(kw in question_lower for kw in keywords_lower):
                results.append(q)
        
        return results
    
    def get_next_question(self, conversation_context: str, current_category: Optional[str] = None,
                         symptom: Optional[str] = None, system: Optional[str] = None, 
                         use_semantic_search: bool = True) -> Optional[Dict]:
        """
        Get the next relevant question based on conversation context
        Uses semantic search (vector DB) if available, otherwise falls back to keyword search
        Returns question with tags and tree_path for logging
        """
        # Try semantic search first if embeddings are available
        if use_semantic_search and self.openai_client and self.collection and self.collection.count() > 0:
            try:
                # Create embedding for the conversation context
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=conversation_context
                )
                query_embedding = response.data[0].embedding
                
                # Build where clause for filtering (ChromaDB syntax)
                where_clause = None
                if system or symptom or current_category:
                    where_clause = {}
                    if system:
                        # Find questions matching system name
                        where_clause['system'] = {'$contains': system}
                    if symptom:
                        where_clause['symptom'] = {'$contains': symptom}
                    if current_category:
                        where_clause['category'] = current_category
                
                # Query vector database
                query_kwargs = {
                    'query_embeddings': [query_embedding],
                    'n_results': 5  # Get top 5 most similar
                }
                if where_clause:
                    query_kwargs['where'] = where_clause
                
                results = self.collection.query(**query_kwargs)
                
                if results['ids'] and len(results['ids'][0]) > 0:
                    # Get the most relevant question
                    top_result_idx = int(results['ids'][0][0].replace('q_', ''))
                    question = self.questions[top_result_idx].copy()
                    
                    # Log semantic search results
                    print(f"[RAG] Semantic search found {len(results['ids'][0])} relevant questions")
                    if results.get('distances'):
                        print(f"[RAG] Top match similarity score: {results['distances'][0][0]:.4f}")
                    
                    return question
            except Exception as e:
                print(f"[RAG] Semantic search failed: {e}, falling back to keyword search")
        
        # Fallback to keyword-based search
        context_lower = conversation_context.lower()
        
        # Determine which system/symptom we're discussing
        systems_keywords = {
            'cardiac': ['chest', 'heart', 'cardiac', 'palpitation', 'shortness of breath'],
            'respiratory': ['breathing', 'cough', 'respiratory', 'lung', 'wheeze'],
            'gi': ['stomach', 'abdominal', 'nausea', 'vomiting', 'diarrhea', 'gi', 'gastro'],
            'neurologic': ['headache', 'dizziness', 'seizure', 'neurologic', 'neurological'],
            'musculoskeletal': ['joint', 'muscle', 'bone', 'pain', 'musculoskeletal'],
            'gu': ['urinary', 'bladder', 'kidney', 'gu', 'genitourinary'],
            'dermatologic': ['skin', 'rash', 'dermatologic', 'dermatological'],
            'endocrine': ['diabetes', 'thyroid', 'endocrine', 'hormone'],
            'ent': ['ear', 'nose', 'throat', 'ent', 'hearing', 'vision']
        }
        
        detected_system = system
        if not detected_system:
            for sys_name, keywords in systems_keywords.items():
                if any(kw in context_lower for kw in keywords):
                    detected_system = sys_name
                    break
        
        # Filter questions
        candidates = self.questions
        
        if detected_system:
            candidates = [q for q in candidates if detected_system.lower() in q['system'].lower()]
        
        if symptom:
            candidates = [q for q in candidates if q['symptom'] and symptom.lower() in q['symptom'].lower()]
        
        if current_category:
            candidates = [q for q in candidates if q['category'] == current_category]
        
        # Return first relevant question with tags
        if candidates:
            question = candidates[0].copy()
            # Ensure tags and tree_path exist
            if 'tags' not in question:
                tags = []
                if question.get('system'):
                    tags.append(f"system:{question['system']}")
                if question.get('symptom'):
                    tags.append(f"symptom:{question['symptom']}")
                if question.get('category'):
                    tags.append(f"category:{question['category']}")
                question['tags'] = tags
                question['tree_path'] = " > ".join(filter(None, [
                    question.get('system'),
                    question.get('symptom'),
                    question.get('category')
                ]))
            return question
        
        return None
    
    def get_all_categories_for_symptom(self, symptom: str) -> List[str]:
        """Get all question categories available for a symptom"""
        questions = self.search_by_symptom(symptom)
        categories = list(set(q['category'] for q in questions if q['category']))
        return categories
    
    def get_questions_by_phase(self, phase: str) -> List[Dict]:
        """
        Get questions based on intake phase
        Maps intake phases to question categories
        """
        phase_mapping = {
            'greeting': ['Chief Complaint'],
            'symptom_discovery': ['Chief Complaint', 'Onset/Duration', 'Quality/Severity', 
                                 'Aggravating/Relieving', 'Associated Symptoms'],
            'red_flags': ['Red Flags'],
            'review_of_systems': ['ROS'],
            'context': ['Context']
        }
        
        categories = phase_mapping.get(phase.lower(), [])
        return [q for q in self.questions if q['category'] in categories]
    
    def export_to_json(self, output_path: str = 'question_book_data.json'):
        """Export parsed questions to JSON for easier access"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.questions, f, indent=2, ensure_ascii=False)
        print(f"Exported {len(self.questions)} questions to {output_path}")

# Test the RAG system
if __name__ == '__main__':
    rag = QuestionBookRAG()
    
    print("\n" + "="*80)
    print("RAG SYSTEM TEST")
    print("="*80)
    
    # Test searches
    print("\n1. Cardiac system questions:")
    cardiac_qs = rag.search_by_system('Cardiac')
    print(f"   Found {len(cardiac_qs)} questions")
    if cardiac_qs:
        print(f"   Sample: {cardiac_qs[0]['question']}")
    
    print("\n2. Chest pain questions:")
    chest_pain_qs = rag.search_by_symptom('Chest Pain')
    print(f"   Found {len(chest_pain_qs)} questions")
    
    print("\n3. Red flag questions:")
    red_flag_qs = rag.search_by_category('Red Flags')
    print(f"   Found {len(red_flag_qs)} questions")
    if red_flag_qs:
        print(f"   Sample: {red_flag_qs[0]['question']}")
        print(f"   Possible answers: {red_flag_qs[0]['possible_answers'][:3]}")
    
    print("\n4. Questions for symptom discovery phase:")
    symptom_qs = rag.get_questions_by_phase('symptom_discovery')
    print(f"   Found {len(symptom_qs)} questions")
    
    # Export to JSON
    rag.export_to_json()

