# MyNoteBookLm

MyNoteBookLm is an open-source, AI-powered notebook & podcast application inspired by Google’s NotebookLM. 
This project aims to provide users with a fully customizable and privacy-focused tool for note-taking, knowledge management, and podcast generation. 
Users can set up their own environment and integrate various LLM and TTS services. 
By default, MyNoteBookLm assumes Microsoft Azure OpenAI as the LLM provider. 
User can also use alternative LLMs such as OpenAI, or local LLMs via Ollama. 

## Features

- **Open Source**: Fully open-source code, enabling users to customize as needed.
- **LLM-Powered Knowledge Management**: Uses a large language model to provide contextual insights, organize information, and offer AI-driven suggestions.
- **Podcast Generation**: Automatically generates podcasts from notes and curated content with multiple TTS provider options.
- **Flexible API Integrations**: Supports a range of LLM and TTS providers, with Microsoft Azure OpenAI as the default LLM provider.
- **User Interface**: A web-based UI powered by Streamlit for an intuitive and accessible experience.
- **Multi-LLM Support**: Supports multiple LLMs such as MS Azure, OpenAI or local LLMs via Ollama.

## Getting Started

### Prerequisites

- **Python 3.7+**
- **API Keys** for the LLM and TTS services you wish to use

### Supported Services

#### Large Language Model (LLM) Providers
- **Microsoft Azure OpenAI** (default)
- **OpenAI API**
- **Ollama** (local model support)

#### Text-to-Speech (TTS) Providers
- **ElevenLabs**
- **Microsoft Azure Text-to-Speech**
- **Edge TTS**
- **OpenAI TTS**

### Setup

#### 1. Clone the Repository

```bash
git clone https://github.com/your-username/MyNoteBookLm.git
cd MyNoteBookLm
```

#### 2. Install Dependencies
Install the necessary packages:

```bash
pip install -r requirements.txt
```

#### 3. Configure API Keys in .env File
Create a .env file in the root directory to store your API keys and configuration.

```bash
touch .env
```

Add your API keys and settings in the .env file. Here’s an example:
```
AZURE_OPENAI_API_KEY=<Your Azure OpenAI API Key>
AZURE_OPENAI_ENDPOINT=<Your Azure OpenAI Endpoint>
AZURE_OPENAI_MODEL_NAME=<Your Model Name>
AZURE_OPENAI_API_VERSION=<Your API Version>

OPENAI_API_KEY=<Your OpenAI API Key>

OLLAMA_HOST=<Ollama Host URL>
OLLAMA_PORT=<Ollama Port>

ELEVENLABS_API_KEY=<Your ElevenLabs API Key>

PODCAST_TITLE="Your Podcast Title"
PODCAST_DESCRIPTION="Description of your podcast content"
```

Replace <Your Azure OpenAI API Key>, etc., with your actual API keys.

#### 4. Configure YAML Settings
Provide a config.yaml file in the root directory with your personal settings. Here’s an example:
```yaml
output_directories:
  transcripts: "./data/transcripts"
  audio: "./data/audio"

conversation_config_path: "./configs/conversation_config.yaml"
INTRO_MUSIC_PATH: "./music/intro_music2.mp3"
OUTRO_MUSIC_PATH: "./music/intro_music2.mp3"

llm_provider:
  # Set the LLM provider, options: "azure", "openai", "ollama"
  provider: "openai"
  azure:
    endpoint: "your-azure-endpoint"
    model_name: "gpt-4"
    api_version: "2023-05-15"
  openai:
    model_name: "gpt-4"
  ollama:
    model_name: "llama3.2"  # Example local LLM model
    host: "localhost"
    port: 11434

content_extractor:
  youtube_url_patterns:
    - "youtube.com"
    - "youtu.be"

youtube_transcriber:
  remove_phrases:
    - "[music]"

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

website_extractor:
  markdown_cleaning:
    remove_patterns:
      - '\[.*?\]'  # Remove square brackets and their contents
      - '\(.*?\)'  # Remove parentheses and their contents
      - '^\s*[-*]\s'  # Remove list item markers
      - '^\s*\d+\.\s'  # Remove numbered list markers
      - '^\s*#+'  # Remove markdown headers
  unwanted_tags:
    - 'script'
    - 'style'
    - 'nav'
    - 'footer'
    - 'header'
    - 'aside'
    - 'noscript'
  user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
  timeout: 10  # Request timeout in seconds
```


#### 5. Run MyNoteBookLm

To start the app, run:
```
python main.py
```

To start the Streamlit-based web UI, run:
```
Streamlit run webui.py
```

## Usage

### Note-Taking and Knowledge Management (Coming Soon)

- **Use** the LLM to organize your notes, get insights, suggest tags, summarize, and answer questions based on your notes.

### Podcast Generation

MyNoteBookLm offers an automated podcast feature that converts notes or curated content into audio episodes. You can choose your preferred TTS provider in the .env file.

Supported TTS Providers:
- OpenAI TTS: High-quality, natural-sounding TTS
- ElevenLabs: High-quality, natural-sounding TTS
- Microsoft Azure Text-to-Speech: Provides various voices and languages
- Edge TTS and OpenAI TTS: Additional TTS options with good flexibility

To generate and upload a podcast episode:
```
python main.py --generate-podcast
```

## Configuration

Configurations are controlled via the `.env` file and a YAML configuration file. 

### `.env` File

Key settings for the `.env` file include:

- `AZURE_OPENAI_API_KEY`: API key for Microsoft Azure OpenAI (default LLM provider).
- `ELEVENLABS_API_KEY`: API key for ElevenLabs TTS.
- `PODCAST_TITLE` and `PODCAST_DESCRIPTION`: Customize your podcast episode title and description.

You can add more configuration keys as needed for each API provider.

### YAML Configuration File

In addition to the `.env` file, you will also need to provide a YAML configuration file (`config.yaml`) with your personal settings. Here’s an example configuration:

```yaml
word_count: 4096
conversation_style: 
  - "engaging"
  - "casual"
  - "enthusiastic"
  - "analytical"
  - "humorous"
roles_person1: "main summarizer"
roles_person2: "questioner/clarifier"
dialogue_structure: 
  - "Introduction"
  - "Main Content Summary"
  - "Market and Economic Analysis"
  - "Current Events Discussion"
  - "Debate Segment"
  - "Conclusion"
podcast_name: "Your Podcast Name"
podcast_tagline: "Your Podcast Tagline"
output_language: "English"
engagement_techniques: 
  - "rhetorical questions"
  - "anecdotes"
  - "analogies"
  - "humor"
  - "playful debates"
creativity: 1
user_instructions: "Emulate the style of the All-In Podcast with hosts discussing recent technology, business, and political events. Encourage dynamic interactions, debates, and include humorous exchanges."

text_to_speech:
  default_tts_provider: "azure"  # Options: "elevenlabs", "openai", "edge", "azure"
  default_tts_model: "tts-1-hd"
  elevenlabs:
    default_voices:
      question: "Brian"
      answer: "Jessica"
    model: "eleven_multilingual_v2"
  openai:
    default_voices:
      question: "echo"
      answer: "nova"
    model: "tts-1-hd"
    deployment_name: "tts-hd"
  edge:
    default_voices:
      question: "en-US-EricNeural"
      answer: "en-US-JennyNeural"
  azure:
    default_voices:
      question: "en-US-Andrew:DragonHDLatestNeural"
      answer: "en-US-Ava:DragonHDLatestNeural"
    audio_format: "mp3"
  audio_format: "mp3"
  temp_audio_dir: "data/audio/tmp/"
  ending_message: "Thank you for listening!"
 ```
#### Instructions:

1. **Add your own configuration**: Replace the placeholders in the above YAML file with your own configuration (e.g., your API keys, podcast name, voices, etc.).
2. **Save the YAML file**: Save the configuration in a file named `conversation_config.yaml` in the root directory of the project.

This file will control various aspects of your podcast generation, including the dialogue structure, speech synthesis options, and more.
## Contributing

Contributions are welcome! To contribute:

1. Fork the repository.
2. Create a feature branch.
3. Make your changes and test them.
4. Submit a pull request.

## Acknowledgements

This project is inspired by and makes reference to the code from **Podcastfy**. 
We would like to acknowledge their contributions and the open-source nature of their project. 
Thank you to the Podcastfy team for providing a foundation that helped shape this project.

## License

This project is licensed under the MIT License.