## E6Data AI Database Backend

This is the FastAPI backend for the AI Database Assistant. It analyzes database performance logs and provides optimization suggestions using OpenAI.

---

### Prerequisites

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) (Python package manager)

---

## Setup Instructions

1. Install `uv` (if not already installed):

   ```sh
   pip install uv
   # or
   curl -sSf https://astral.sh/uv/install.sh | sh
   ```

2. Install dependencies:

   ```sh
   uv sync
   ```

3. Set your Gemini API key in a `.env` file:

   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

---

## Running the Backend

Start the FastAPI server with uvicorn:

```sh
fastapi dev main.py
```

The backend will be available at [http://127.0.0.1:8000](http://127.0.0.1:8000).

---

## Usage

1. Connect your frontend to the backend URL (default: `http://127.0.0.1:8000`).
2. Use the `/chat` endpoint to analyze database logs and chat with the assistant.

---

## Troubleshooting

- Ensure your `.env` file contains a valid OpenAI API key.
- Make sure all dependencies are installed using `uv`.
- If you see CORS errors, check that the frontend URL is allowed in `main.py`.
