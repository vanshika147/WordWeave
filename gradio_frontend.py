import gradio as gr
import requests
import asyncio
import functools
import base64
import os
import tempfile, threading, time

FASTAPI_URL = "http://127.0.0.1:8000"

LANGUAGE_NAMES = sorted([
    "English", "French", "Punjabi", "Spanish", "German", "Hindi", "Bengali", "Arabic",
    "Japanese", "Korean", "Russian", "Portuguese", "Italian", "Dutch",
    "Swedish", "Polish", "Turkish", "Vietnamese", "Thai", "Indonesian",
    "Malay", "Urdu", "Persian", "Ukrainian", "Hebrew", "Greek", "Czech",
    "Danish", "Finnish", "Norwegian", "Romanian", "Hungarian", "Bulgarian",
    "Slovak", "Slovenian", "Lithuanian", "Latvian", "Estonian", "Croatian",
    "Serbian", "Bosnian", "Albanian", "Assamese", "Azerbaijani",
    "Belarusian", "Burmese", "Catalan", "Cebuano", "Simplified Chinese",
    "Traditional Chinese", "Cantonese", "Zulu"
])

TONE_OPTIONS = ["Neutral", "Formal", "Informal", "Friendly", "Sarcastic", "Angry", "Relaxed", "Enthusiastic"]

translation_history = []
favourites = []

async def async_post(endpoint, json=None, files=None, data=None):
    loop = asyncio.get_running_loop()
    fn = functools.partial(requests.post, FASTAPI_URL + endpoint, json=json, files=files, data=data)
    response = await loop.run_in_executor(None, fn)
    response.raise_for_status()
    return response.json()

async def translate_text(text, source_lang, target_lang, tone):
    if not text.strip():
        return "Error: Please enter text to translate."
    if source_lang == target_lang:
        return "Error: Source and target languages cannot be the same."
    if source_lang not in LANGUAGE_NAMES or target_lang not in LANGUAGE_NAMES:
        return "Error: Invalid language selected."
    if tone not in TONE_OPTIONS:
        return f"Error: Invalid tone. Choose from {TONE_OPTIONS}"

    try:
        payload = {
            "text": text,
            "source_language": source_lang,
            "target_language": target_lang,
            "tone": tone
        }
        result = await async_post("/translate/", json=payload)
        translated = result.get("translated_text", "")
        _add_to_history(text, source_lang, target_lang, tone, translated)
        return translated
    except requests.exceptions.RequestException as e:
        return f"API error: {str(e)}"

def _add_to_history(input_text, src, tgt, tone, translation):
    global translation_history
    entry = {
        "input": input_text,
        "source": src,
        "target": tgt,
        "tone": tone,
        "translation": translation
    }
    translation_history.insert(0, entry)
    if len(translation_history) > 3:
        translation_history.pop()

def save_to_favourites():
    if not translation_history:
        return "No translations to save."
    latest = translation_history[0]  
    if latest in favourites:
        return "Already in favourites."
    favourites.append(latest)
    return "Saved to favourites."

def get_history_text():
    if not translation_history:
        return "No history yet."
    out = ""
    for i, entry in enumerate(translation_history, 1):
        out += f"#{i}: [{entry['source']} → {entry['target']} | Tone: {entry['tone']}]\n"
        out += f"Input: {entry['input']}\nTranslated: {entry['translation']}\n\n"
    return out.strip()

def get_favourites_text():
    if not favourites:
        return "No favourites saved."
    out = ""
    for i, entry in enumerate(favourites, 1):
        out += f"#{i}: [{entry['source']} → {entry['target']} | Tone: {entry['tone']}]\n"
        out += f"Input: {entry['input']}\nTranslated: {entry['translation']}\n\n"
    return out.strip()

def format_history():
    if not translation_history:
        return "No history yet."
    out = ""
    for i, entry in enumerate(translation_history, 1):
        out += f"#{i}: [{entry['source']} → {entry['target']} | Tone: {entry['tone']}]\n"
        out += f"Input: {entry['input']}\nTranslated: {entry['translation']}\n\n"
    return out.strip()

async def translate_image(file, source_lang, target_lang, tone):
    if file is None:
        return "Error: Please upload an image file."
    if source_lang == target_lang:
        return "Error: Source and target languages cannot be the same."
    if source_lang not in LANGUAGE_NAMES or target_lang not in LANGUAGE_NAMES:
        return "Error: Invalid language selected."
    if tone not in TONE_OPTIONS:
        return f"Error: Invalid tone. Choose from {TONE_OPTIONS}"

    try:
        filename = os.path.basename(file)
        with open(file, "rb") as f:
            file_bytes = f.read()
        files = {"file": (filename, file_bytes)}
        data = {
            "source_language": source_lang,
            "target_language": target_lang,
            "tone": tone
        }
        result = await async_post("/upload_and_translate_image/", files=files, data=data)
        translated = result.get("translated_text", "")
        _add_to_history(f"[Image OCR: {filename}]", source_lang, target_lang, tone, translated)
        return translated
    except requests.exceptions.RequestException as e:
        return f"API error: {str(e)}"

async def translate_document(file, source_lang, target_lang, tone):
    if file is None:
        return "Error: Please upload a document file (.pdf or .txt)."
    if source_lang == target_lang:
        return "Error: Source and target languages cannot be the same."
    if source_lang not in LANGUAGE_NAMES or target_lang not in LANGUAGE_NAMES:
        return "Error: Invalid language selected."
    if tone not in TONE_OPTIONS:
        return f"Error: Invalid tone. Choose from {TONE_OPTIONS}"

    ext = file.name.lower().split('.')[-1]
    if ext not in ["pdf", "txt"]:
        return "Error: Only .pdf and .txt documents are supported."

    try:
        filename = os.path.basename(file)
        with open(file, "rb") as f:
            file_bytes = f.read()
        files = {"file": (filename, file_bytes)}
        data = {
            "source_language": source_lang,
            "target_language": target_lang,
            "tone": tone
        }
        result = await async_post("/upload_and_translate_document/", files=files, data=data)
        translated = result.get("translated_text", "")
        _add_to_history(f"[Document OCR: {filename}]", source_lang, target_lang, tone, translated)
        return translated
    except requests.exceptions.RequestException as e:
        return f"API error: {str(e)}"

async def speech_to_text(audio_file):
    if (audio_file is None or 
        not os.path.exists(audio_file) or 
        os.path.getsize(audio_file) < 100):
        return "Error: Please upload an audio file."
    try:
        filename = os.path.basename(audio_file)
        with open(audio_file, "rb") as f:
            audio_bytes = f.read()

        files = {"audio_file": (filename, audio_bytes, "audio/wav")}  # you can change MIME if needed
        
        result = await async_post("/speech_to_text/", files=files)
        return result.get("transcribed_text", "")
    except requests.exceptions.RequestException as e:
        return f"API error: {str(e)}"
    
def delete_file_later(path, delay=15):
    def _delete():
        time.sleep(delay)
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"Deleted temp audio file: {path}")
            except Exception as e:
                print(f"Error deleting audio file: {e}")
    threading.Thread(target=_delete, daemon=True).start()

async def text_to_speech(translated_text, tts_language):
    if not translated_text.strip():
        return "Error: Please enter text for TTS."
    if tts_language not in LANGUAGE_NAMES:
        return "Error: Invalid language selected."

    try:
        payload = {
            "text": translated_text,
            "language": tts_language
        }
        result = await async_post("/text_to_speech/", json=payload)

        if not translated_text:
            return "Translation failed before TTS."

        payload = {"text": translated_text, "language": tts_language}
        result = await async_post("/text_to_speech/", json=payload)
        audio_base64 = result.get("audio_base64", "")
        if not audio_base64:
            return "TTS failed: no audio returned."

        audio_bytes = base64.b64decode(audio_base64)

        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
            tmp_audio.write(audio_bytes)
            temp_path = tmp_audio.name

        delete_file_later(temp_path, delay=15)
        return temp_path

    except requests.exceptions.RequestException as e:
        return f"API error: {str(e)}"

async def explain_translation(text, source_lang, target_lang):
    if not text.strip():
        return "Nothing to explain."
    try:
        payload = {
            "text": text,
            "source_language": source_lang,
            "target_language": target_lang
        }
        result = await async_post("/explain_translation/", json=payload)
        return result.get("explanation", "")
    except requests.exceptions.RequestException as e:
        return f"API error: {str(e)}"

theme = gr.themes.Citrus(
    primary_hue="blue",
    secondary_hue="purple",
    font=['Comic Sans', 'ui-sans-serif', 'system-ui', gr.themes.GoogleFont('Comic Neue')],
    font_mono=['Roboto Mono', 'ui-monospace', gr.themes.GoogleFont('Consolas'), 'monospace'],
).set(
    border_color_accent_dark='*color_accent_soft',
    border_color_primary_dark='*block_label_background_fill',
    color_accent='*primary_800',
    block_border_color_dark='*border_color_accent_subdued'
)

    
with gr.Blocks(title="Ollama Multilingual Translator", analytics_enabled=False, theme=theme, css=".scrollbox { overflow-y: auto; height: 200px; }") as demo:
    with gr.Row():
        with gr.Column(scale=1, min_width=600):
            gr.Markdown(
                """
                <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@600&display=swap" rel="stylesheet">
                <div style="
                    padding: 20px;
                    border-radius: 12px;
                    background: linear-gradient(145deg, #1f1f1f, #292929);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.6);
                    text-align: center;
                    font-family: 'Orbitron', sans-serif;
                ">
                    <h1 style="color:#00bfff; font-size: 2.5rem; margin-bottom: 10px;">
                          Welcome to WordWeave 
                    </h1>
                    <p style="color: #cccccc; font-size: 1.1rem; margin: 0;">
                        An AI-Powered Multi Language Translator that can translate text, images, documents, and speech using a local Ollama backend.
                    </p>
                </div>
                """,
                elem_id="header"
            )

    with gr.Row():
        # Sidebar column with buttons
        with gr.Sidebar(open=False):
            gr.Markdown("### ☰ Menu")
            history_btn = gr.Button("Show History")
            favourites_btn = gr.Button("Show Favourites")
            with gr.Column(visible=False) as history_col:
                history_output = gr.Textbox(lines=15, label="History", interactive=False)
            
            with gr.Column(visible=False) as favourites_col:
                favourites_output = gr.Textbox(lines=15, label="Favourites", interactive=False)
            
            # Hidden state variables for changing labels
            show_history_state = gr.State(False)    
            show_favourites_state = gr.State(False)

        # Main UI column
        with gr.Column(scale=4): 
            with gr.Tab("Text Translation") as text_tab:
                with gr.Row():
                    source_lang = gr.Dropdown(choices=LANGUAGE_NAMES, value="English", label="Source Language")
                    target_lang = gr.Dropdown(choices=LANGUAGE_NAMES, value="French", label="Target Language")

                with gr.Row():
                    text_input = gr.Textbox(lines=5, label="Input Text", placeholder="Enter text to translate...", show_copy_button=True)
                    with gr.Column(scale=1):
                        mic_audio = gr.Audio(sources=["microphone"], type="filepath", label="Record your voice")
                        translate_btn = gr.Button("Translate")

                with gr.Row():
                    with gr.Column(scale=3):
                        tone = gr.Dropdown(choices=TONE_OPTIONS, value="Neutral", label="Tone")
                        text_output = gr.Textbox(lines=5, label="Translated Text", interactive=False, show_copy_button=True)
                        with gr.Row():
                            explain_btn = gr.Button("Explain the Translation")
                            save_fav_btn = gr.Button("Save to Favourites")
                            tts_btn = gr.Button("🔊")

                    with gr.Column(scale=2):
                        explanation_output = gr.Textbox(lines=5, label="Explanation", interactive=False, elem_classes="scrollbox")
                        tts_audio_output = gr.Audio(label="TTS Output")

            with gr.Tab("Image/Document Translation") as ocr_tab:
                with gr.Row():
                    ocr_source_lang = gr.Dropdown(choices=LANGUAGE_NAMES, value="English", label="Source Language")
                    ocr_target_lang = gr.Dropdown(choices=LANGUAGE_NAMES, value="French", label="Target Language")
                file_input = gr.File(label="Upload Image (.jpg, .jpeg, .png) or Document (.pdf, .txt)", file_types=[".jpg", ".jpeg", ".png", ".pdf", ".txt"])
        
                ocr_tone = gr.Dropdown(choices=TONE_OPTIONS, value="Neutral", label="Tone")
                with gr.Row():
                    ocr_translate_btn = gr.Button("Translate Uploaded File")
                    ocr_explain_btn = gr.Button("Explain the Translation")
                with gr.Row():
                    ocr_text_output = gr.Textbox(lines=5, label="Translated Text", interactive=False)
                    ocr_explanation_output = gr.Textbox(lines=5, label="Explanation", interactive=False, elem_classes="scrollbox")

            # Define callbacks
            translate_btn.click(translate_text, inputs=[text_input, source_lang, target_lang, tone], outputs=[text_output])

            mic_audio.change(speech_to_text, inputs=mic_audio, outputs=text_input)

            tts_btn.click(
            text_to_speech,
            inputs=[text_output, target_lang],
            outputs=tts_audio_output
            )

            explain_btn.click(explain_translation, inputs=[text_output, source_lang, target_lang], outputs=explanation_output)

            history_btn.click(get_history_text, outputs=[history_output])
            favourites_btn.click(get_favourites_text, outputs=[favourites_output])
            save_fav_btn.click(save_to_favourites, outputs=[favourites_output])

            async def route_ocr_translation(file, src, tgt, tone):
                if file is None:
                    return "Please upload a file."
                ext = file.name.lower().split('.')[-1]
                if ext in ["jpg", "jpeg", "png"]:
                    return await translate_image(file, src, tgt, tone)
                elif ext in ["pdf", "txt"]:
                    return await translate_document(file, src, tgt, tone)
                else:
                    return "Unsupported file type."


            ocr_translate_btn.click(route_ocr_translation, inputs=[file_input, ocr_source_lang, ocr_target_lang, ocr_tone], outputs=[ocr_text_output])
            ocr_explain_btn.click(explain_translation, inputs=[ocr_text_output, ocr_source_lang, ocr_target_lang], outputs=ocr_explanation_output)

            # Track visibility states
            show_history_state = gr.State(False)
            show_favourites_state = gr.State(False)
            
            def toggle_history_combined(show):
                new_state = not show
                return (
                    gr.update(visible=new_state),    # Show/hide the container
                    gr.update(value="Hide History" if new_state else "Show History"),      # Change button label
                    format_history() if new_state else "",                 # Set new textbox content
                    new_state                        # Update state
                )

            def toggle_favourites_combined(show):
                new_state = not show
                return (
                    gr.update(visible=new_state),
                    gr.update(value="Hide Favourites" if new_state else "Show Favourites"),
                    get_favourites_text() if new_state else "",
                    new_state
                )

            favourites_btn.click(
                toggle_favourites_combined,
                inputs=[show_favourites_state],
                outputs=[favourites_col, favourites_btn, favourites_output, show_favourites_state]
            )

            history_btn.click(
                toggle_history_combined,
                inputs=[show_history_state],
                outputs=[history_col, history_btn, history_output, show_history_state]
            )

            history_btn.click(lambda: format_history(), outputs=history_output)

demo.launch()
