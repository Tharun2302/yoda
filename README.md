# HealthYoda Chatbot

A simple Python-based chatbot with a web frontend. This chatbot provides health-related assistance without requiring authentication.

## Features

- Simple chatbot interface
- Streaming responses
- No authentication required
- Session-based conversation history
- Markdown support for responses

## Setup Instructions

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up OpenAI API Key

You need an OpenAI API key to use the chatbot. Get one from [OpenAI Platform](https://platform.openai.com/api-keys).

**Option A: Using .env file (Recommended)**

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API key:
   ```
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

**Option B: Using Environment Variable**

On Windows (PowerShell):
```powershell
$env:OPENAI_API_KEY="sk-your-actual-api-key-here"
```

On Windows (Command Prompt):
```cmd
set OPENAI_API_KEY=sk-your-actual-api-key-here
```

On Linux/Mac:
```bash
export OPENAI_API_KEY='sk-your-actual-api-key-here'
```

### 3. Start the Backend Server

Open a terminal and run:
```bash
python app.py
```

The server will start on `http://127.0.0.1:8002`

**Note:** The server will warn you if the API key is not set.

### 4. Serve the Frontend

**IMPORTANT:** You cannot open `index.html` directly from the file system due to CORS restrictions. You need to serve it via HTTP.

**Option A: Use the provided Python HTTP server (Recommended)**

Open a second terminal and run:
```bash
python serve.py
```

Then open `http://localhost:8000/index.html` in your browser.

**Option B: Use Python's built-in HTTP server**

```bash
python -m http.server 8000
```

Then open `http://localhost:8000/index.html` in your browser.

**Option C: Use any other HTTP server**

You can use any HTTP server (like Live Server in VS Code, or any other web server) to serve the `index.html` file.

## Usage

1. Start the Python backend server (`python app.py`)
2. Open `index.html` in your browser
3. Type your questions in the input box
4. The chatbot will respond with health-related information

## Customization

### Change the OpenAI Model

In `app.py`, you can change the model from `gpt-4o-mini` to `gpt-4`, `gpt-4-turbo`, or any other available model:

```python
stream = client.chat.completions.create(
    model="gpt-4",  # Change this line (currently using gpt-4o-mini)
    messages=messages,
    stream=True,
    temperature=0.7,
    max_tokens=1000
)
```

### Adjust Temperature and Max Tokens

- `temperature`: Controls randomness (0.0 = deterministic, 1.0 = creative). Default: 0.7
- `max_tokens`: Maximum length of response. Default: 1000

### Customize System Prompt

Edit the `SYSTEM_PROMPT` variable in `app.py` to change the chatbot's personality and behavior.

## Notes

- Authentication has been removed from the frontend
- The chatbot uses in-memory conversation history (resets on server restart)
- For production use, consider adding proper error handling and persistence

