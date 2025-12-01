# MongoDB Integration for Session Data Management

**Date:** December 2024  
**Status:** ✅ **Implemented**

---

## Overview

MongoDB integration stores **only structured medical data** (not full chat history) and prevents the bot from asking duplicate questions by checking what data has already been collected.

---

## How It Works

### 1. Data Storage Structure

Each session stores structured medical data in MongoDB:

```json
{
  "session_id": "cf.conversation.20241201.abc123",
  "complaint_name": "Chest pain",
  "hpi": {
    "onset": "Started 2 hours ago",
    "location": "Left side of chest",
    "duration": "2 hours",
    "quality": "Sharp, stabbing",
    "severity": "7/10",
    "timing": "Constant",
    "context": "While resting",
    "modifying_factors": "Worse with deep breath",
    "progression": "Getting worse",
    "associated_symptoms": "Shortness of breath",
    "chief_complaint": "Chest pain"
  },
  "ros": {
    "respiratory": "Shortness of breath",
    "cardiovascular": "Palpitations",
    "gi": "No nausea",
    "neuro": "No dizziness"
  },
  "past_history": {
    "pmh": "Hypertension, diabetes",
    "psh": "Appendectomy 2010",
    "medications": ["Lisinopril 10mg", "Metformin 500mg"],
    "allergies": ["Penicillin"],
    "family_history": "Father had heart attack at 55",
    "social_history": {
      "smoking": "Never",
      "alcohol": "Occasional",
      "occupation": "Office worker"
    }
  },
  "red_flags": [
    {
      "question": "Do you have chest pain?",
      "response": "Yes, severe",
      "timestamp": "2024-12-01T10:30:00"
    }
  ],
  "created_at": "2024-12-01T10:00:00",
  "updated_at": "2024-12-01T10:45:00"
}
```

### 2. Question Prevention Flow

**Before asking a question:**
1. RAG system retrieves a relevant question
2. System checks MongoDB: `is_data_already_collected(session_id, category, system)`
3. If data exists → Skip question, try next one
4. If data missing → Ask question

**After user responds:**
1. Extract data from user response
2. Map RAG question category to data field
3. Store in MongoDB: `extract_and_store_data(session_id, user_response, rag_question_info)`

### 3. Category Mapping

RAG question categories are mapped to MongoDB fields:

| RAG Category | MongoDB Field | Data Type |
|-------------|---------------|-----------|
| `Onset/Duration` | `hpi.onset` | String |
| `Location` | `hpi.location` | String |
| `Quality/Severity` | `hpi.quality` | String |
| `Chief Complaint` | `hpi.chief_complaint` | String |
| `ROS` + System | `ros.{system}` | String |
| `Medications` | `past_history.medications` | Array |
| `Allergies` | `past_history.allergies` | Array |
| `Red Flags` | `red_flags` | Array |

---

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=healthyoda
```

**For MongoDB Atlas (Cloud):**
```bash
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DB=healthyoda
```

**For Local MongoDB:**
```bash
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=healthyoda
```

### Installation

```bash
pip install pymongo>=4.6.0
```

---

## API Endpoints

### Get Session Data (For Doctors)

**Endpoint:** `GET /session/<session_id>/data`

**Response:**
```json
{
  "session_id": "cf.conversation.20241201.abc123",
  "complaint_name": "Chest pain",
  "hpi": {...},
  "ros": {...},
  "past_history": {...},
  "red_flags": [...],
  "created_at": "2024-12-01T10:00:00",
  "updated_at": "2024-12-01T10:45:00"
}
```

**Use Case:** Doctors can retrieve structured patient data without full chat history.

---

## Key Functions

### `get_or_create_session_data(session_id)`
- Gets existing session or creates new one
- Returns structured data dictionary
- Falls back to in-memory if MongoDB unavailable

### `is_data_already_collected(session_id, category, system, question_text)`
- Checks if data for a category/system is already collected
- Returns `True` if data exists, `False` if needs collection
- Used before asking questions

### `extract_and_store_data(session_id, user_response, rag_question_info)`
- Extracts structured data from user response
- Maps to correct MongoDB field based on RAG category
- Stores in MongoDB

### `format_collected_data_for_llm(session_id)`
- Formats already collected data as context for LLM
- Tells LLM what NOT to ask again
- Added to system prompt

---

## Benefits

1. **No Duplicate Questions** ✅
   - Bot checks MongoDB before asking
   - Skips questions if data already collected

2. **Structured Data Storage** ✅
   - Only stores medical data doctors need
   - No full chat history stored
   - Easy to query and export

3. **Persistent Storage** ✅
   - Survives server restarts
   - Data available across sessions
   - Scalable for multiple servers

4. **HIPAA Compliant** ✅
   - Structured data easier to encrypt
   - Can implement access controls
   - Audit trail possible

---

## How Questions Are Prevented

### Example Flow:

1. **User says:** "I have chest pain"
2. **Bot asks:** "When did the chest pain start?" (Onset question)
3. **User responds:** "About 2 hours ago"
4. **System stores:** `hpi.onset = "About 2 hours ago"` in MongoDB
5. **Next question:** RAG suggests another onset question
6. **System checks:** `is_data_already_collected(session_id, "Onset/Duration", ...)`
7. **Result:** Returns `True` → Question skipped
8. **Bot asks:** Different question (e.g., location)

---

## Fallback Behavior

If MongoDB is not available:
- System falls back to in-memory storage
- Bot still works but won't prevent duplicates
- Warning message displayed at startup
- No data persistence

---

## Testing

### Test MongoDB Connection:

```python
# In Python shell
from pymongo import MongoClient
client = MongoClient('mongodb://localhost:27017/')
client.admin.command('ping')
# Should print: {'ok': 1.0}
```

### Test Data Collection:

1. Start conversation
2. Answer questions
3. Check MongoDB:
```python
from pymongo import MongoClient
db = MongoClient()['healthyoda']
session = db['patient_sessions'].find_one({'session_id': 'your_session_id'})
print(session)
```

### Test Question Prevention:

1. Answer a question (e.g., "When did it start?")
2. Bot should store: `hpi.onset`
3. Bot should NOT ask onset questions again
4. Check logs for: `[MongoDB] Data already collected for category 'Onset/Duration'`

---

## Limitations & Future Enhancements

### Current Limitations:

1. **Simple Data Extraction**
   - Currently stores user response directly
   - Could use LLM to extract structured data

2. **Category Mapping**
   - Manual mapping of categories to fields
   - May need adjustment for your question categories

3. **No Question Exclusion in RAG**
   - RAG system doesn't know which categories are collected
   - Could enhance RAG to filter out collected categories

### Future Enhancements:

1. **LLM-Based Data Extraction**
   - Use LLM to extract structured data from free-form responses
   - More accurate data storage

2. **Enhanced RAG Filtering**
   - Pass collected categories to RAG system
   - RAG excludes questions for collected data

3. **Data Validation**
   - Validate extracted data format
   - Ensure completeness

4. **Export Functionality**
   - Export to FHIR format
   - Generate PDF reports for doctors

---

## Troubleshooting

### MongoDB Not Connecting

**Error:** `⚠️ MongoDB connection failed`

**Solutions:**
1. Check if MongoDB is running: `mongod --version`
2. Verify connection string in `.env`
3. Check firewall/network settings
4. For Atlas: Verify IP whitelist

### Questions Still Repeating

**Possible Causes:**
1. MongoDB not connected (check startup messages)
2. Category mapping incorrect (check `map_category_to_data_field`)
3. Data not being stored (check logs for `[MongoDB] Stored data`)

**Debug:**
```python
# Check if data is stored
session_data = get_or_create_session_data('your_session_id')
print(session_data)

# Check if function returns True
result = is_data_already_collected('your_session_id', 'Onset/Duration', None)
print(f"Data collected: {result}")
```

---

## Security Notes

- **No Authentication:** Current implementation has no auth on `/session/<session_id>/data` endpoint
- **Session ID Security:** Session IDs are predictable (add random component)
- **Data Encryption:** MongoDB data not encrypted at rest (add encryption for production)
- **Access Control:** No role-based access (add authentication for doctor endpoints)

**For Production:**
- Add authentication to `/session/<session_id>/data` endpoint
- Encrypt MongoDB data at rest
- Implement audit logging
- Add rate limiting on data retrieval

---

## Summary

✅ **MongoDB integration complete!**

- Stores only structured medical data (not chat history)
- Prevents duplicate questions by checking collected data
- Provides endpoint for doctors to retrieve patient data
- Falls back gracefully if MongoDB unavailable

**Next Steps:**
1. Install MongoDB locally or set up MongoDB Atlas
2. Add `MONGODB_URI` to `.env`
3. Test the integration
4. Monitor logs for data collection

---

**Last Updated:** December 2024

