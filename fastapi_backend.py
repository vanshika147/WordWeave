from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import easyocr, io, os, PyPDF2, base64, tempfile
from gtts import gTTS
from faster_whisper import WhisperModel
import re 

app = FastAPI(title="My Translator")

# --- Constants ---
LANGUAGE_NAMES = sorted(["English", "French", "Punjabi", "Spanish", "German", "Hindi", "Bengali", "Arabic", "Japanese", "Korean", "Russian", "Portuguese", "Italian", "Dutch", "Swedish", "Polish", "Turkish", "Vietnamese", "Thai", "Indonesian", "Malay", "Urdu", "Persian", "Ukrainian", "Hebrew", "Greek", "Czech", "Danish", "Finnish", "Norwegian", "Romanian", "Hungarian", "Bulgarian", "Slovak", "Slovenian", "Lithuanian", "Latvian", "Estonian", "Croatian", "Serbian", "Bosnian", "Albanian", "Assamese", "Azerbaijani", "Belarusian", "Burmese", "Catalan", "Cebuano", "Simplified Chinese", "Traditional Chinese", "Cantonese", "Zulu"])
TONE_OPTIONS = ["Neutral", "Formal", "Informal", "Friendly", "Sarcastic", "Angry", "Relaxed", "Enthusiastic"]
LANG_MAP = {"English": "en", "French": "fr", "Punjabi": "pa", "Spanish": "es", "Persian": "fa", "German": "de", "Hindi": "hi", "Bengali": "bn", "Arabic": "ar", "Japanese": "ja", "Korean": "ko", "Russian": "ru", "Portuguese": "pt", "Italian": "it", "Dutch": "nl", "Swedish": "sv", "Polish": "pl", "Turkish": "tr", "Vietnamese": "vi", "Thai": "th", "Indonesian": "id", "Malay": "ms", "Urdu": "ur", "Ukrainian": "uk", "Hebrew": "iw", "Greek": "el", "Czech": "cs", "Danish": "da", "Finnish": "fi", "Norwegian": "no", "Romanian": "ro", "Hungarian": "hu", "Bulgarian": "bg", "Slovak": "sk", "Slovenian": "sl", "Lithuanian": "lt", "Latvian": "lv", "Estonian": "et", "Croatian": "hr", "Serbian": "sr", "Bosnian": "bs", "Albanian": "sq", "Assamese": "as", "Azerbaijani": "az", "Belarusian": "be", "Burmese": "my", "Catalan": "ca", "Cebuano": "ceb", "Simplified Chinese": "zh-CN", "Traditional Chinese": "zh-TW", "Cantonese": "yue", "Zulu": "zu"}

# --- Models ---
class TranslateRequest(BaseModel): text: str; source_language: str; target_language: str; tone: str
class TranslateResponse(BaseModel): translated_text: str
class DetectLanguageRequest(BaseModel): text: str
class DetectLanguageResponse(BaseModel): detected_language: str
class ExplainRequest(BaseModel): text: str; source_language: str; target_language: str
class ExplainResponse(BaseModel): explanation: str
class TTSRequest(BaseModel): text: str; language: str
class TTSResponse(BaseModel): audio_base64: str
class STTResponse(BaseModel): transcribed_text: str

# --- EasyOCR ---
ocr_reader = easyocr.Reader(['en', 'hi'], gpu=True)

# --- LangChain ---
def build_chain(model, prompt):
    return ChatPromptTemplate.from_messages([("user", prompt)]) | ChatOllama(model=model) | StrOutputParser()

translation_chain = build_chain("Gemma_Translator", "Translate the following {source_language} text to {target_language} in a {tone} tone:\n\n{text_to_translate}")
# detection_chain = build_chain("Gemma_Translator", "Detect the language of the following text and respond with only the language name:\n\n{text_to_detect}")
explanation_chain = build_chain("Gemma_Translator", "Explain the cultural nuances and word choices for this translation from {source_language} to {target_language}:\n\n{text_to_explain}")
# Removed ChatOllama Whisper
# llm_stt = ChatOllama(model="whisper")

# Initialize faster-whisper model once
whisper_model = WhisperModel("small", device="cuda")  # Change device to "cpu" if no GPU

# --- Utilities ---
def validate_langs(source, target, tone=None):
    if source == target: raise HTTPException(400, "Source and target languages cannot be the same.")
    if source not in LANGUAGE_NAMES: raise HTTPException(400, f"Unsupported source language: {source}")
    if target not in LANGUAGE_NAMES: raise HTTPException(400, f"Unsupported target language: {target}")
    if tone and tone not in TONE_OPTIONS: raise HTTPException(400, f"Unsupported tone: {tone}")

async def process_translation_request(text, source, target, tone):
    validate_langs(source, target, tone)
    out = await translation_chain.ainvoke({"text_to_translate": text, "source_language": source, "target_language": target, "tone": tone})
    return TranslateResponse(translated_text=out.strip())

# --- Endpoints ---
@app.post("/translate/", response_model=TranslateResponse)
async def translate(req: TranslateRequest): 
    return await process_translation_request(req.text, req.source_language, req.target_language, req.tone)

# @app.post("/detect_language/", response_model=DetectLanguageResponse)
# async def detect(req: DetectLanguageRequest):
#     if not req.text.strip(): raise HTTPException(400, "Text is empty.")
#     lang = (await detection_chain.ainvoke({"text_to_detect": req.text})).strip()
#     detected = next((l for l in LANGUAGE_NAMES if l.lower() == lang.lower()), lang)
#     return DetectLanguageResponse(detected_language=detected)

@app.post("/upload_and_translate_image/", response_model=TranslateResponse)
async def image_translate(file: UploadFile = File(...), source_language: str = Form(...), target_language: str = Form(...), tone: str = Form(...)):
    if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')): raise HTTPException(400, "Only image files supported.")
    content = await file.read()
    text = " ".join([res[1] for res in ocr_reader.readtext(content)]).strip()
    if not text: raise HTTPException(400, "No text detected.")
    return await process_translation_request(text, source_language, target_language, tone)

@app.post("/upload_and_translate_document/", response_model=TranslateResponse)
async def doc_translate(file: UploadFile = File(...), source_language: str = Form(...), target_language: str = Form(...), tone: str = Form(...)):
    ext = file.filename.lower().split('.')[-1]
    content = await file.read()
    if ext == "pdf":
        reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = "".join([p.extract_text() or "" for p in reader.pages]).strip()
    elif ext == "txt":
        text = content.decode("utf-8").strip()
    else:
        raise HTTPException(400, "Only .pdf and .txt files supported.")
    if not text: raise HTTPException(400, "No readable text.")
    return await process_translation_request(text, source_language, target_language, tone)

@app.post("/text_to_speech/", response_model=TTSResponse)
async def tts(req: TTSRequest):
    code = LANG_MAP.get(req.language)
    if not code: raise HTTPException(400, f"TTS not supported for: {req.language}")

    cleaned_text = re.sub(r'\s*\([^)]*\)', '', req.text).strip()

    fp = io.BytesIO()
    gTTS(cleaned_text, lang=code).write_to_fp(fp)
    fp.seek(0)
    return TTSResponse(audio_base64=base64.b64encode(fp.read()).decode())

@app.post("/speech_to_text/", response_model=STTResponse)
async def stt(audio_file: UploadFile = File(...)):
    if not audio_file or not getattr(audio_file, "content_type", "").startswith("audio/"):
        raise HTTPException(400, "Audio files only.")
    
    # Save uploaded audio to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tf:
        tf.write(await audio_file.read())
        temp_path = tf.name
    
    try:
        # Use faster-whisper to transcribe
        segments, _ = whisper_model.transcribe(temp_path)
        transcribed_text = " ".join(segment.text for segment in segments).strip()
        return STTResponse(transcribed_text=transcribed_text)
    finally:
        os.unlink(temp_path)

@app.post("/explain_translation/", response_model=ExplainResponse)
async def explain(req: ExplainRequest):
    validate_langs(req.source_language, req.target_language)
    out = await explanation_chain.ainvoke({
        "text_to_explain": req.text,
        "source_language": req.source_language,
        "target_language": req.target_language
    })
    return ExplainResponse(explanation=out.strip())
