"""Diagnose the document structure to fix parsing"""
import docx
import json

doc = docx.Document('docx/Question BOOK.docx')

# Find patterns
print("Analyzing document structure...\n")
print("="*80)

# Look for questions and their context
questions_found = []
current_context = {"system": None, "symptom": None, "category": None}

for i, para in enumerate(doc.paragraphs):
    text = para.text.strip()
    
    if not text:
        continue
    
    # Check for system headers
    if 'System' in text and len(text) < 150:
        if any(sys in text for sys in ['Cardiac', 'Respiratory', 'GI', 'Neurologic', 
                                       'Musculoskeletal', 'GU', 'Dermatologic', 'Endocrine', 'ENT']):
            current_context["system"] = text
            current_context["symptom"] = None
            print(f"\n[{i}] SYSTEM: {text}")
    
    # Check for symptoms (standalone lines that aren't questions or categories)
    elif text and not text.startswith('Q') and not text.startswith('Possible') and \
         not text.startswith('-') and text not in ['Chief Complaint', 'Onset/Duration', 
         'Quality/Severity', 'Aggravating/Relieving', 'Associated Symptoms', 'Red Flags', 
         'ROS', 'Context', 'Table of Contents', 'HealthYoda', 'comprehensive'] and \
         len(text) < 100 and current_context["system"]:
        # Check if it's likely a symptom (not a system, not too long)
        if text != current_context["system"] and 'System' not in text:
            current_context["symptom"] = text
            print(f"[{i}] SYMPTOM: {text}")
    
    # Check for categories
    elif text in ['Chief Complaint', 'Onset/Duration', 'Quality/Severity', 
                  'Aggravating/Relieving', 'Associated Symptoms', 'Red Flags', 'ROS', 'Context']:
        current_context["category"] = text
        print(f"[{i}] CATEGORY: {text}")
    
    # Check for questions
    if text.startswith('Q:') or text.startswith('Q.'):
        question_text = text.replace('Q:', '').replace('Q.', '').strip()
        questions_found.append({
            "line": i,
            "system": current_context["system"],
            "symptom": current_context["symptom"],
            "category": current_context["category"],
            "question": question_text
        })
        if len(questions_found) <= 20:  # Show first 20
            print(f"[{i}] QUESTION: {question_text[:80]}")

print(f"\n{'='*80}")
print(f"Total questions found: {len(questions_found)}")
print(f"\nSample questions:")
for q in questions_found[:10]:
    print(f"  Line {q['line']}: [{q['system']}] > [{q['symptom']}] > [{q['category']}]")
    print(f"    Q: {q['question'][:100]}")

