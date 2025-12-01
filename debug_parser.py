"""Debug the parser step by step"""
import docx

doc = docx.Document('docx/Question BOOK.docx')

current_system = None
current_symptom = None
current_category = None
questions_found = []

categories = ['Chief Complaint', 'Onset/Duration', 'Quality/Severity', 
             'Aggravating/Relieving', 'Associated Symptoms', 'Red Flags', 
             'ROS', 'Context']

for i, para in enumerate(doc.paragraphs[:200]):  # First 200 paragraphs
    text = para.text.strip()
    
    if not text:
        continue
    
    # Skip excluded
    if any(x in text for x in ['Table of Contents', '[page]', 'HealthYoda History-Taking Handbook']):
        continue
    
    # System detection
    if 'HealthYoda History Framework' in text:
        if 'Cardiac' in text:
            current_system = 'Cardiac System'
            print(f"\n[{i}] SYSTEM SET: {current_system}")
        elif 'Respiratory' in text:
            current_system = 'Respiratory System'
            print(f"\n[{i}] SYSTEM SET: {current_system}")
    
    # Symptom detection
    elif current_system and text not in categories and \
         not text.startswith('Q') and not text.startswith('Possible') and \
         not text.startswith('-') and len(text) < 100 and \
         text != current_system and 'System' not in text and \
         'HealthYoda' not in text:
        current_symptom = text
        print(f"[{i}] SYMPTOM SET: {current_symptom}")
    
    # Category detection
    elif text in categories:
        current_category = text
        print(f"[{i}] CATEGORY SET: {current_category}")
    
    # Question detection
    elif text.startswith('Q:') or text.startswith('Q.'):
        question_text = text.replace('Q:', '').replace('Q.', '').strip()
        questions_found.append({
            'line': i,
            'system': current_system,
            'symptom': current_symptom,
            'category': current_category,
            'question': question_text
        })
        print(f"[{i}] QUESTION FOUND: {question_text[:60]}")

print(f"\n\nTotal questions found in first 200 paragraphs: {len(questions_found)}")
print("\nFirst 5 questions:")
for q in questions_found[:5]:
    print(f"  [{q['system']}] > [{q['symptom']}] > [{q['category']}]")
    print(f"    Q: {q['question']}")

