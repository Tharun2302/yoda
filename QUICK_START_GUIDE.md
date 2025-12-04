# Quick Start Guide - Text Knowledge Base System

## For End Users

### Adding New Text Files

1. **Place your file in the `txt/` folder**
   ```
   txt/YourDomain_HealthYoda_DeepestDive_FULL.txt
   ```

2. **Set environment variable in `.env`**
   ```bash
   REBUILD_VECTORSTORE=true
   ```

3. **Restart the application**
   ```bash
   python app.py
   ```

4. **Monitor the logs**
   ```
   INFO: Processing YourDomain_HealthYoda_DeepestDive_FULL.txt
   INFO: Extracted 150 patterns from YourDomain_HealthYoda_DeepestDive_FULL.txt
   INFO: Total patterns extracted: 1587
   ```

That's it! Your new patterns are now available.

## For Developers

### Understanding the Schema

Every extracted pattern follows this structure:

```python
{
    'medical_domain': str,        # e.g., "AbdominalPain"
    'section': str,               # e.g., "RUQ PAIN"
    'content_type': str,          # red_flag, differential, interview_question, clinical_clue
    'bot_question': str,          # What the bot should ask
    'expected_patient_responses': list,  # Example patient answers
    'clinical_context': str,      # Rich context for understanding
    'red_flags': list,           # Urgent symptoms to check
    'priority': str,              # CRITICAL, HIGH, NORMAL, LOW
    'tags': list,                # Searchable tags
    'tree_path': str,            # Hierarchical path
    'source': str,               # deepest_dive, docx, etc.
    'metadata': dict             # Additional info
}
```

### Using Priority-Based Retrieval

```python
from rag_system import QuestionBookRAG

rag = QuestionBookRAG()

# Get next question with priority ordering
next_q = rag.get_next_question(
    conversation_context="Patient says: severe abdominal pain",
    prioritize_red_flags=True  # Red flags will surface first
)

print(f"Priority: {next_q['priority']}")
print(f"Question: {next_q['bot_question']}")
```

### Searching by Content Type

```python
# Get all red flags
red_flags = rag.search_by_content_type('red_flag')

# Get all differentials
differentials = rag.search_by_content_type('differential')

# Get all interview questions
questions = rag.search_by_content_type('interview_question')
```

### Searching by Priority

```python
# Get CRITICAL patterns (red flags)
critical = rag.search_by_priority('CRITICAL')

# Get HIGH priority patterns (differentials)
high_priority = rag.search_by_priority('HIGH')
```

### Searching by Domain

```python
# Get all patterns for a specific domain
abdominal = rag.search_by_system('AbdominalPain')
cardiac = rag.search_by_system('Cardiac')
```

## File Format Requirements

### Structure Your Text Files Like This:

```
DOMAIN NAME — HealthYoda RAG DEEPEST DIVE
===========================================================

SECTION 1 — SECTION TITLE
===========================================================

SUBSECTION HEADER:
- Differential 1
- Differential 2

Q:
- "Question for bot to ask?"
A:
- "Patient response 1"
- "Patient response 2"

CLUES:
- Clinical clue 1
- Clinical clue 2

RED FLAGS:
- Urgent symptom 1
- Urgent symptom 2
```

### Key Elements:

1. **Section Delimiters:** Use `===` (3+ equals) to separate sections
2. **Subsection Headers:** ALL CAPS with colon (e.g., `RUQ PAIN:`)
3. **Questions:** Start with `Q:` or `Q.`
4. **Answers:** Start with `A:` or `A.`
5. **Red Flags:** Section labeled `RED FLAGS:`
6. **Bullet Points:** Use `-` for lists

## Troubleshooting

### No Patterns Extracted?

**Check:**
1. File is in `txt/` folder
2. File uses `===` section delimiters
3. Content has bullet points with `-`
4. Sections are properly structured

**Fix:** Review sample files in `txt/` folder for format examples

### Wrong Priority Assigned?

**Check:**
1. Red flags section labeled `RED FLAGS:`
2. Questions have proper `Q:` and `A:` markers
3. Differentials are bullet lists without questions

**Fix:** Ensure content follows format conventions

### Extraction Count Low?

**Check logs:**
```
INFO: Processing section: YOUR_SECTION
INFO:   Extracted 0 patterns  <-- Check why 0
```

**Common issues:**
- Missing `===` delimiters
- Questions without `Q:` markers
- Mixed content types in same section

## Performance Tips

### For Large Files (>1MB)

1. **Split into logical sections** - One file per domain
2. **Use clear section headers** - Helps extraction accuracy
3. **Avoid very long sections** - Break into subsections

### For Many Files (50+)

1. **Incremental processing** - Add files gradually
2. **Monitor memory** - Check logs for issues
3. **Consider batch processing** - Process in groups

## Testing Your Files

### Quick Test Script

```python
from text_processor import TextFileProcessor

processor = TextFileProcessor('txt')
patterns = processor.extract_all_text_data()

print(f"Total patterns: {len(patterns)}")
print(f"Stats: {processor.stats}")

# Check first pattern
if patterns:
    sample = patterns[0]
    print(f"\nSample pattern:")
    print(f"  Domain: {sample['medical_domain']}")
    print(f"  Type: {sample['content_type']}")
    print(f"  Priority: {sample['priority']}")
```

## Common Patterns

### Red Flag Pattern
```python
{
    'content_type': 'red_flag',
    'priority': 'CRITICAL',
    'bot_question': 'URGENT: Check for [symptom]',
    'red_flags': ['symptom1', 'symptom2']
}
```

### Differential Pattern
```python
{
    'content_type': 'differential',
    'priority': 'HIGH',
    'bot_question': 'What conditions should be considered for [section]?',
    'differentials': ['condition1', 'condition2', 'condition3']
}
```

### Interview Question Pattern
```python
{
    'content_type': 'interview_question',
    'priority': 'NORMAL',
    'bot_question': 'Specific question?',
    'expected_patient_responses': ['response1', 'response2']
}
```

## Getting Help

### Check Logs
```bash
# View extraction logs
tail -f app.log | grep "TXT"

# View pattern counts
grep "Extracted.*patterns" app.log
```

### Export Patterns
```python
from rag_system import QuestionBookRAG

rag = QuestionBookRAG()
rag.export_to_json('my_patterns.json')
# Review patterns in JSON format
```

### Run Demo
```bash
python demo_priority_retrieval.py
```

## Best Practices

### ✅ Do:
- Use consistent formatting across files
- Include red flags for critical symptoms
- Provide realistic patient responses
- Group related content in sections
- Test extraction after adding files

### ❌ Don't:
- Mix different content types in same bullets
- Use inconsistent section delimiters
- Forget `Q:` and `A:` markers
- Create extremely long sections (>500 lines)
- Skip testing before deploying

## Support

For issues or questions:
1. Check this guide first
2. Review sample files in `txt/`
3. Run `demo_priority_retrieval.py`
4. Check `TEXT_KB_IMPLEMENTATION_SUMMARY.md` for details

