"""Verify RAG system extraction"""
import json

with open('question_book_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total questions extracted: {len(data)}")
print("\n" + "="*80)
print("Sample questions with tags and tree paths:")
print("="*80)

for i, q in enumerate(data[:5]):
    print(f"\n{i+1}. Tree Path: {q['tree_path']}")
    print(f"   Question: {q['question'][:100]}")
    print(f"   Tags: {', '.join(q['tags'])}")
    if q.get('possible_answers'):
        print(f"   Possible Answers: {len(q['possible_answers'])} options")
        print(f"      Sample: {q['possible_answers'][:3]}")

print("\n" + "="*80)
print("Statistics:")
print("="*80)
systems = set(q['system'] for q in data if q.get('system'))
symptoms = set(q['symptom'] for q in data if q.get('symptom'))
categories = set(q['category'] for q in data if q.get('category'))

print(f"Systems: {len(systems)}")
print(f"Symptoms: {len(symptoms)}")
print(f"Categories: {len(categories)}")

print(f"\nSample systems: {list(systems)[:5]}")
print(f"Sample symptoms: {list(symptoms)[:10]}")

