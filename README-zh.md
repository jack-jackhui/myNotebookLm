<h1 align="center">
MyNoteBookLm
</h1>

<div align="center">
<h3>
    <a href="README-zh.md">简体中文</a> |
    <a href="README.md">English</a>
</h3>
</div>

MyNoteBookLm 是一款受 Google’s NotebookLM 启发的开源、由人工智能驱动的笔记本及播客应用程序。
本项目旨在为用户提供一个完全可定制且注重隐私的工具，用于笔记记录、知识管理以及播客生成。
用户可以自行搭建环境，并集成各类大语言模型（LLM）和文本转语音（TTS）服务。
默认情况下，MyNoteBookLm 将微软 Azure OpenAI 作为大语言模型（LLM）的提供方。
用户也可以使用其他替代的大语言模型，比如 OpenAI，或者通过 Ollama 使用本地的大语言模型。

## 功能特性 🎯

- **开源**：代码完全开源，用户可按需进行定制。
- **基于大语言模型的知识管理**：利用大语言模型提供上下文相关的见解、整理信息，并提供由人工智能驱动的建议。
- **播客生成**：能从笔记和精选内容中自动生成播客，且有多个文本转语音（TTS）服务提供商可供选择。
- **灵活的 API 集成**：支持一系列大语言模型（LLM）和文本转语音（TTS）服务提供商，默认的大语言模型（LLM）提供方为微软 Azure OpenAI。
- **用户界面**：基于 Streamlit 的网页用户界面，带来直观且易用的使用体验。
- **多语言模型支持**：支持多个大语言模型，如微软 Azure、OpenAI 或者通过 Ollama 使用本地大语言模型。

## 精彩播客展示 📦

使用 MyNotebookLm 应用创作的播客现已上线！欢迎大家收听并分享您的感受。

**播客封面**：

![播客封面](https://is1-ssl.mzstatic.com/image/thumb/Podcasts211/v4/d5/1d/aa/d51daa6d-b039-d949-8d8f-e6383d5a90f7/mza_15802649668481427365.png/300x300bb.webp)

**播客链接**：[点击此处前往收听](https://podcasts.apple.com/au/podcast/ai-unchained/id1778941149)

在这个播客中，您将领略到 MyNotebookLm 强大的功能与魅力，深入探讨各种有趣的话题，感受知识与声音的完美融合。无论是在通勤路上、运动健身时，还是在闲暇时光，都可以打开播客，开启一段精彩的听觉之旅。快来一起体验吧！ 

## 在线使用 🚀
由于项目的部署和使用，对于一些小白用户来说，还是有一定的门槛，在此提供线上的免费服务，可以不用部署，直接在线使用，非常方便。
- 项目网址：https://mynotebooklm.jackhui.com.au

## 快速入门

### 先决条件

- **Python 3.7 及以上版本**
- 您希望使用的大语言模型（LLM）和文本转语音（TTS）服务的 **API 密钥**

### 支持的服务

#### 大语言模型（LLM）提供方
- **微软 Azure OpenAI**（默认）
- **OpenAI API**
- **Ollama**（支持本地模型）

#### 文本转语音（TTS）提供方
- **ElevenLabs**
- **微软 Azure 文本转语音**
- **Edge TTS**
- **OpenAI TTS**

### 安装设置

#### 1. 克隆仓库

```bash
git clone https://github.com/你的用户名/MyNoteBookLm.git
cd MyNoteBookLm
```

#### 2. 安装依赖项
安装所需的软件包：

```bash
pip install -r requirements.txt
```

#### 3. 在.env 文件中配置 API 密钥
在项目根目录下创建一个.env 文件，用于存储您的 API 密钥及配置信息。

```bash
touch.env
```

在.env 文件中添加您的 API 密钥和相关设置。以下是一个示例：

```
AZURE_OPENAI_API_KEY=<您的微软 Azure OpenAI API 密钥>
AZURE_OPENAI_ENDPOINT=<您的微软 Azure OpenAI 终端节点>
AZURE_OPENAI_MODEL_NAME=<您的模型名称>
AZURE_OPENAI_API_VERSION=<您的 API 版本>

OPENAI_API_KEY=<您的 OpenAI API 密钥>

OLLAMA_HOST=<Ollama 主机 URL>
OLLAMA_PORT=<Ollama 端口>

ELEVENLABS_API_KEY=<您的 ElevenLabs API 密钥>

PODCAST_TITLE="您的播客标题"
PODCAST_DESCRIPTION="您的播客内容描述"
```

将 `<您的微软 Azure OpenAI API 密钥>` 等内容替换为您实际的 API 密钥。

#### 4. 配置 YAML 设置
在项目根目录下提供一个 config.yaml 文件，填入您的个人设置。以下是一个示例：

```yaml
output_directories:
  transcripts: "./data/transcripts"
  audio: "./data/audio"

conversation_config_path: "./configs/conversation_config.yaml"
INTRO_MUSIC_PATH: "./music/intro_music2.mp3"
OUTRO_MUSIC_PATH: "./music/intro_music2.mp3"

llm_provider:
  # 设置大语言模型（LLM）提供方，选项有："azure"、"openai"、"ollama"
  provider: "openai"
  azure:
    endpoint: "您的微软 Azure 终端节点"
    model_name: "gpt-4"
    api_version: "2023-05-15"
  openai:
    model_name: "gpt-4"
  ollama:
    model_name: "llama3.2"  # 示例本地大语言模型
    host: "localhost"
    port: 11434

content_extractor:
  youtube_url_patterns:
    - "youtube.com"
    - "youtu.be"

youtube_transcriber:
  remove_phrases:
    - "[音乐]"

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

website_extractor:
  markdown_cleaning:
    remove_patterns:
      - '\[.*?\]'  # 移除方括号及其内容
      - '\(.*?\)'  # 移除圆括号及其内容
      - '^\s*[-*]\s'  # 移除列表项标记
      - '^\s*\d+\.\s'  # 移除编号列表标记
      - '^\s*#+'  # 移除 Markdown 标题
  unwanted_tags:
    - 'script'
    - 'style'
    - 'nav'
    - 'footer'
    - 'header'
    - 'aside'
    - 'noscript'
  user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
  timeout: 10  # 请求超时时间（单位：秒）
```


#### 5. 运行 MyNoteBookLm

要启动应用程序，请运行：

```
python main.py
```

要启动基于 Streamlit 的网页用户界面，请运行：

```
Streamlit run webui.py
```

- 默认情况下，Streamlit 用户界面需要通过后端进行身份验证。
- 可以通过更新 `config.py` 文件来禁用此功能：

```python
REQUIRE_LOGIN = True  # 设置为 False 可禁用登录要求
```

## 使用方法

### 笔记记录与知识管理（通过网页用户界面）

- **使用**大语言模型来整理您的笔记、获取见解、建议标签、进行总结以及根据您的笔记回答问题。

### 播客生成

MyNoteBookLm 提供了自动化的播客功能，可将笔记或精选内容转换为音频节目。您可以在.env 文件中选择您偏好的文本转语音（TTS）服务提供商。

支持的文本转语音（TTS）服务提供商：
- OpenAI TTS：高质量、发音自然的文本转语音服务。
- ElevenLabs：高质量、发音自然的文本转语音服务。
- 微软 Azure 文本转语音：提供多种语音和语言选项。
- Edge TTS 和 OpenAI TTS：具备良好灵活性的其他文本转语音选项。

要生成并上传播客节目，请运行：

```
python main.py --generate-podcast
```

## 配置

配置通过 `.env` 文件和一个 YAML 配置文件来控制。

### `.env` 文件

`.env` 文件中的关键设置包括：

- `AZURE_OPENAI_API_KEY`：微软 Azure OpenAI（默认大语言模型提供方）的 API 密钥。
- `ELEVENLABS_API_KEY`：ElevenLabs 文本转语音服务的 API 密钥。
- `PODCAST_TITLE` 和 `PODCAST_DESCRIPTION`：自定义您的播客节目标题和描述。

您可以根据每个 API 服务提供商的需求添加更多配置项。

### YAML 配置文件

除了 `.env` 文件外，您还需要提供一个 YAML 配置文件（`config.yaml`），其中包含您的个人设置。以下是一个示例配置：

```yaml
word_count: 4096
conversation_style: 
  - "引人入胜"
  - "随意"
  - "热情"
  - "分析性"
  - "幽默"
roles_person1: "主要总结者"
roles_person2: "提问者/澄清者"
dialogue_structure: 
  - "引言"
  - "主要内容总结"
  - "市场与经济分析"
  - "时事讨论"
  - "辩论环节"
  - "结论"
podcast_name: "您的播客名称"
podcast_tagline: "您的播客宣传语"
output_language: "英语"
engagement_techniques: 
  - "反问"
  - "轶事"
  - "类比"
  - "幽默"
  - "趣味辩论"
creativity: 1
user_instructions: "模仿《All-In》播客的风格，由主持人讨论近期的科技、商业和政治事件。鼓励动态互动、辩论，并包含幽默的交流内容。"

text_to_speech:
  default_tts_provider: "azure"  # 选项："elevenlabs"、"openai"、"edge"、"azure"
  default_tts_model: "tts-1-hd"
  elevenlabs:
    default_voices:
      question: "布莱恩"
      answer: "杰西卡"
    model: "eleven_multilingual_v2"
  openai:
    default_voices:
      question: "回声"
      answer: "新星"
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
  ending_message: "感谢收听！"
```

#### 操作说明：

1. **添加您自己的配置**：将上述 YAML 文件中的占位符替换为您自己的配置（例如，您的 API 密钥、播客名称、语音等）。
2. **保存 YAML 文件**：将配置保存到项目根目录下名为 `conversation_config.yaml` 的文件中。

该文件将控制您的播客生成的各个方面，包括对话结构、语音合成选项等等。

## 贡献

欢迎大家贡献代码！贡献步骤如下：

1. 克隆仓库。
2. 创建一个功能分支。
3. 进行更改并测试。
4. 提交拉取请求。

## 鸣谢 🙏

本项目受 **Podcastfy** 的启发，并参考了其部分代码。
我们要感谢他们所做出的贡献以及其项目的开源性质。
感谢 Podcastfy 团队提供的基础框架，助力本项目的成型。

## 许可证

本项目的许可证详情请查看 [LICENSE](LICENSE) 文件。 