# Quick Test - Safety Scoring

## Run This Command

```bash
python test_safety_scoring.py
```

## Expected Output

```
[OK] All tests passed!

New Features Implemented:
  1. Safety Score - Separate score for safety-related rubrics
  2. Tag Scores - Granular scores by category
  3. Red Flag Detection - Identifies critical safety violations
  4. Critical Failure Flag - Immediate alert for dangerous responses
  5. Negative Point Rubrics - Deducts points for bad behaviors

Rubric Summary:
  - Total rubrics: 13
  - Positive rubrics: 8
  - Red flag rubrics: 5
```

## What Gets Tested

1. ✅ Import modules
2. ✅ Rubric structure (13 rubrics: 8 positive, 5 negative)
3. ✅ Tag score calculation
4. ✅ Red flag detection
5. ✅ EvaluationResult with all new fields

## If All Tests Pass

Your safety scoring system is **fully operational**! 🎉

Start your chatbot:
```bash
python app.py
```

Every response will now include:
- Safety score
- Tag scores
- Red flag detection
- Critical failure alerts

