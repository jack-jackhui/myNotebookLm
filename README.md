<h1 align=center>
MyNoteBookLm
</h1>

<div align=center>
    <h3><a href="README-zh.md">简体中文</a> | <a href="README.md">English</a></h3>
</div>

MyNoteBookLm is an open-source, AI-powered notebook & podcast application inspired by Google’s NotebookLM. 
This project provides a fully customizable and privacy-focused tool for note-taking, knowledge management, and professional podcast generation. 

## Features

- **Open Source & Privacy-Focused**: Run locally or on your own server. Your data, your rules.
- **Smart Knowledge Management**: 
    - **Multi-Source Input**: Upload PDF, Word (Docx), Text, and PowerPoint (PPTX) files.
    - **URL & YouTube Integration**: Extract content from web articles or YouTube transcripts.
    - **Direct Text Input**: Paste and process content directly in the UI.
- **Advanced Podcast Generation**:
    - **Conversational Scripts**: Automatically transforms notes into engaging dialogues between two hosts.
    - **Customizable Hosts**: Configure host names (e.g., "Jack" and "Corr") to personalize the experience.
    - **Episode Length Control**: Choose from Auto, 5min, 15min, or 30min target durations.
    - **Script Editor**: Preview, edit, and download transcripts (TXT/Markdown) before audio generation.
    - **Parallel TTS Synthesis**: High-speed audio generation with configurable concurrency and retry logic.
    - **Custom Intro/Outro**: Upload your own MP3/WAV files for professional branding.
- **Session History**: Save and reload previous sessions, including scripts, audio, and settings.
- **Flexible AI Integrations**:
    - **LLM Support**: Microsoft Azure OpenAI (default), OpenAI, DeepSeek, and local LLMs via Ollama.
    - **TTS Support**: Azure Text-to-Speech, OpenAI TTS, ElevenLabs, Edge TTS, and Spark TTS.
- **SEO Optimized**: Built-in meta tags, Open Graph support, and structured data for web deployments.
- **Robust Architecture**: Multi-stage Docker builds, health checks, and comprehensive error handling.

## Sample Podcast
### Podcast: AI Unchained

Listen to an example podcast created entirely with the MyNoteBookLm app.

**Podcast Cover**:

![Podcast Cover](https://is1-ssl.mzstatic.com/image/thumb/Podcasts211/v4/d5/1d/aa/d51daa6d-b039-d949-8d8f-e6383d5a90f7/mza_15802649668481427365.png/300x300bb.webp)

**Podcast Link**: [Click here to listen](https://podcasts.apple.com/au/podcast/ai-unchained/id1778941149)

## Online Usage 🚀
Try the live version without any setup:
- Project URL: [https://mynotebooklm.jackhui.com.au](https://mynotebooklm.jackhui.com.au)

## Getting Started

### Prerequisites

- **Python 3.9+**
- **Docker** (optional, for containerized deployment)
- **API Keys** for your chosen LLM and TTS providers.

### Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/jack-jackhui/MyNoteBookLm.git
cd MyNoteBookLm
```

#### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 3. Configuration
The project uses a unified configuration system via `settings.py`.

**A. Create a `.env` file:**
```env
# LLM
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_MODEL_NAME=gpt-4o

# TTS
AZURE_TTS_API_KEY=your_key
AZURE_TTS_REGION=eastus

# Podcast Defaults
HOST_1_NAME=Jack
HOST_2_NAME=Corr
```

**B. (Optional) Customize `config.yaml`:**
Edit `config.yaml` to adjust paths, output directories, and advanced extraction settings.

#### 4. Run the Application

**Web Interface (Recommended):**
```bash
streamlit run webui.py
```

**CLI Version:**
```bash
python main.py --generate-podcast
```

## Docker Deployment

The repository includes a production-ready `Dockerfile`.

```bash
docker build -t mynotebooklm .
docker run -p 8501:8501 --env-file .env mynotebooklm
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgements

- Inspired by Google’s NotebookLM.
- References code from [Podcastfy](https://github.com/souzatharsis/podcastfy).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
