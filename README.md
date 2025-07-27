# WordWeave: An AI Powered Multilingual AI Translator
WordWeave is a robust multilingual AI translator leveraging local Ollama LLMs, like Gemma. It offers text, speech-to-text, image OCR, and document translation, all accessible via a user-friendly Gradio interface and a high-performance FastAPI backend.

## 🌟 Project Overview

**WordWeave** is a cutting-edge multilingual translation application designed to facilitate seamless communication across various languages and input formats. Leveraging local Large Language Models (LLMs) served by **Ollama**, it offers robust translation capabilities for text, audio (Speech-to-Text), images (OCR), and documents (PDF/TXT). The application prioritizes privacy and customization, featuring advanced functionalities like tone-controlled translations, cultural explanations, and an intuitive user interface.

Built with a high-performance **FastAPI** backend to handle intensive processing and a responsive **Gradio** frontend for user interaction, WordWeave provides a comprehensive and efficient translation experience powered entirely by your local machine.

## 📂 Project Structure 
project/
├── fastapi_backend.py       # FastAPI backend server
├── gradio_frontend.py       # Gradio frontend interface
├── GemmaModelFile           # Gemma language model file
├── README.md                # Project documentation
└──requirements.txt          # Python dependencies

## ✨ Key Features

* **Multilingual Text Translation:** Translate text between a wide array of languages.
* **Customizable Tone:** Control the translation's tone (e.g., Neutral, Formal, Sarcastic, Relaxed, Enthusiastic, Angry, Friendly, Informal).
* **Speech-to-Text (STT):** Transcribe spoken audio (via microphone input) into text using OpenAI's `faster-whisper` model.
* **Text-to-Speech (TTS):** Convert translated text into audible speech using Google Text-to-Speech (`gTTS`) for improved user experience.
* **Image Translation (OCR):** Upload image files (.jpg, .jpeg, .png) for text extraction using **EasyOCR** and subsequent translation.
* **Document Translation:** Upload PDF (.pdf) and plain text (.txt) files for content extraction and translation.
* **Translation Explanation:** Get detailed insights into translated phrases, including cultural nuances, alternative word choices, and the LLM's reasoning.
* **Session History:** A mini, in-memory history log of your recent translations for quick reference within the session.
* **Favorites:** Save your most important translations to a separate "Favourites" list for easy access.
* **Intuitive Tabbed UI:** A clean and organized Gradio interface with dedicated tabs for "Text Translation" and "Image/Document Translation".

## 🚀 Technologies Used

* **Backend (`fastapi_backend.py`):**
    * **FastAPI:** Modern, fast web framework for building APIs.
    * **LangChain:** For orchestrating LLM interactions and prompt engineering.
    * **Ollama:** For locally serving LLMs (`Gemma3n:e4b` for translation/text tasks).
    * **`faster-whisper`**: For efficient and fast Speech-to-Text transcription.
    * **EasyOCR:** For Optical Character Recognition from images.
    * **PyPDF2:** For extracting text from PDF documents.
    * **gTTS (Google Text-to-Speech):** For text-to-speech conversion.
    * **Pydantic:** For data validation and settings management.
    
* **Frontend (`gradio_frontend.py`):**
    * **Gradio:** For rapid prototyping and building the web-based user interface.
    * **`requests`:** For making HTTP requests to the FastAPI backend.
    * `asyncio`, `functools`, `threading`, `time` (for asynchronous operations and temporary file management).

## 🌐 Architecture

WordWeave employs a three-tiered architecture:

1.  **Ollama Server:** Runs locally in the background, hosting the large language models which perform the core AI tasks (translation, explanation, speech-to-text).
2.  **FastAPI Backend (`fastapi_backend.py`):** Acts as the central processing unit.
    * Receives requests from the Gradio frontend.
    * Orchestrates interactions with Ollama via LangChain.
    * Handles file processing (OCR for images, text extraction for PDFs/TXTs).
    * Manages Text-to-Speech generation.
    * Exposes various REST API endpoints for different translation functionalities.
3.  **Gradio Frontend (`gradio_frontend.py`):** Provides the interactive web user interface.
    * Collects user input and displays results.
    * Communicates with the FastAPI backend asynchronously to send requests and retrieve responses.

This design ensures efficient resource management and a smooth, responsive user experience by separating the UI from heavy computational tasks.

## ⚙️ Setup and Installation

### Prerequisites

* **Python 3.9+** (ensure it's added to your PATH)
* **Ollama:**
    1.  [Download and install Ollama](https://ollama.com/) for your operating system.
    2.  Once installed, open your terminal/command prompt and pull the necessary models:
        ```bash
        ollama pull gemma3n:e4b 
        ```
    3.  Create your custom `Gemma_Translator` model using the provided Modelfile:
        Place the `GemmaModelFile` in the same directory as your `fastapi_backend.py`. Then run:
        ```bash
        ollama create Gemma_Translator -f GemmaModelFile
        ```

### Installation Steps

1.  **Clone the Repository (or setup your project directory):**
    Ensure all your project files (`fastapi_backend.py`, `gradio_frontend.py`, `GemmaModelFile`, `requirements.txt`, etc.) are in the same main project directory.

2.  **Install Python Dependencies:**
    It's highly recommended to use a virtual environment.
    ```bash
    python -m venv venv
    .\venv\Scripts\activate # On Windows
    source venv/bin/activate # On macOS/Linux
    ```
    Now, install the required packages:
    ```bash
    pip install -r requirements.txt
    ```
    *(If you don't have a `requirements.txt` yet, create one with the contents below, or install individually)*:
    ```bash
    # Sample requirements.txt content :
    fastapi
    uvicorn
    langchain-ollama
    langchain-core
    easyocr
    PyPDF2
    gtts
    faster-whisper
    gradio
    requests
    Pydantic
    python-multipart
    ```
    * **Important for GPU (NVIDIA users):** If you have an NVIDIA GPU and want to leverage it for `faster-whisper` and `easyocr`, you *must* install the correct PyTorch version for your CUDA setup. For example, for CUDA 12.1:
        ```bash
        pip install torch torchvision torchaudio --index-url [https://download.pytorch.org/whl/cu121](https://download.pytorch.org/whl/cu121)
        ```
        If you are on CPU only, the `pip install -r requirements.txt` or `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu` should suffice, but confirm your `faster_whisper.WhisperModel` device is set to `"cpu"` in `fastapi_backend.py`.

### Running the Application

1.  **Start the Ollama Server:**
    Ensure Ollama is running in the background. You can usually verify this by running `ollama list` in your terminal or checking your system's background processes.

2.  **Start the FastAPI Backend:**
    Open your terminal or command prompt, navigate to your project directory (where `fastapi_backend.py` is located), and run:
    ```bash
    uvicorn fastapi_backend:app --host 0.0.0.0 --port 8000 --reload
    ```
    *(The `--reload` flag is useful during development as it automatically restarts the server when code changes are detected.)*

3.  **Start the Gradio Frontend:**
    Open a **separate** terminal or command prompt, navigate to your project directory (where `gradio_frontend.py` is located), and run:
    ```bash
    python gradio_frontend.py
    ```

4.  **Access the Application:**
    Once both servers are running, open your web browser and go to the URL provided by Gradio (typically `http://127.0.0.1:7860`).

## 👨‍💻 Usage

The WordWeave interface is designed for ease of use and is divided into intuitive tabs:

* **Text Translation:** Input text, select your source and target languages, choose a tone, and get instant translations. You can also record audio to transcribe to text first.
* **Image/Document Translation:** Upload an image (.jpg, .jpeg, .png) or a document (.pdf, .txt). The application will extract the text and provide a translation based on your language and tone selections.
* **Sidebar Menu:** Use the sidebar buttons to view your session's translation history or your saved favorite translations.

## 🤝 Contributing

We welcome contributions to WordWeave! If you'd like to contribute, please follow these steps:

1.  Fork the repository
2.  Create a feature branch (`git checkout -b feature/new-feature`)
3.  Commit your changes (`git commit -am 'Add new feature'`)
4.  Push to the branch (`git push origin feature/new-feature`)
5.  Create a Pull Request

## 🙌 Acknowledgements

* **Ollama Community:** For developing an excellent platform for local LLM inference.
* **LangChain:** For providing powerful tools for building LLM applications.
* **FastAPI & Gradio Teams:** For their robust and developer-friendly frameworks.
* **EasyOCR, PyPDF2, gTTS, faster-whisper:** For the essential libraries that power core functionalities.

---
