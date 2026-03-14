<h1 align=center>
MyNoteBookLm
</h1>

<div align=center>
    <h3><a href="README-zh.md">简体中文</a> | <a href="README.md">English</a></h3>
</div>

MyNoteBookLm 是一款受 Google’s NotebookLM 启发的开源、由人工智能驱动的笔记本及播客应用程序。
本项目为用户提供一个完全可定制且注重隐私的工具，用于笔记记录、知识管理以及专业的播客生成。

## 功能特性 🎯

- **开源且注重隐私**：可本地运行或在私有服务器上运行。你的数据，由你掌握。
- **智能知识管理**：
    - **多源输入**：支持上传 PDF、Word (Docx)、文本 (TXT) 和 PowerPoint (PPTX) 文件。
    - **URL 与 YouTube 集成**：从网页文章或 YouTube 字幕中提取内容。
    - **直接文本输入**：在界面中直接粘贴并处理内容。
- **先进的播客生成**：
    - **对话式脚本**：自动将笔记转换为两位主持人之间引人入胜的对话。
    - **自定义主持人**：可配置主持人姓名（如 "Jack" 和 "Corr"）以实现个性化体验。
    - **时长控制**：提供自动、5分钟、15分钟或30分钟的目标时长选项。
    - **脚本编辑器**：在生成音频前预览、编辑并下载文稿（支持 TXT/Markdown 格式）。
    - **并行 TTS 合成**：高速音频生成，支持配置并发量和重试逻辑。
    - **自定义片头/片尾**：上传您自己的 MP3/WAV 文件以打造专业品牌。
- **会话历史记录**：保存并重新加载之前的会话，包括脚本、音频和设置。
- **灵活的 AI 集成**：
    - **LLM 支持**：微软 Azure OpenAI（默认）、OpenAI、DeepSeek 以及通过 Ollama 支持的本地模型。
    - **TTS 支持**：Azure 文本转语音、OpenAI TTS、ElevenLabs、Edge TTS 以及 Spark TTS。
- **SEO 优化**：内置 Meta 标签、Open Graph 支持和结构化数据，适用于网页部署。
- **稳健的架构**：多阶段 Docker 构建、健康检查和全面的错误处理机制。

## 精彩播客展示 📦

收听一个完全由 MyNoteBookLm 应用创作的示例播客。

**播客封面**：

![播客封面](https://is1-ssl.mzstatic.com/image/thumb/Podcasts211/v4/d5/1d/aa/d51daa6d-b039-d949-8d8f-e6383d5a90f7/mza_15802649668481427365.png/300x300bb.webp)

**播客链接**：[点击此处前往收听](https://podcasts.apple.com/au/podcast/ai-unchained/id1778941149)

## 在线使用 🚀
无需任何配置，即可试用在线版本：
- 项目网址：[https://mynotebooklm.jackhui.com.au](https://mynotebooklm.jackhui.com.au)

## 快速入门

### 先决条件

- **Python 3.9+**
- **Docker**（可选，用于容器化部署）
- 您选择的 LLM 和 TTS 服务提供商的 **API 密钥**。

### 安装设置

#### 1. 克隆仓库

```bash
git clone https://github.com/jack-jackhui/MyNoteBookLm.git
cd MyNoteBookLm
```

#### 2. 安装依赖项
```bash
pip install -r requirements.txt
```

#### 3. 配置
项目通过 `settings.py` 使用统一的配置系统。

**A. 创建 `.env` 文件：**
```env
# LLM
AZURE_OPENAI_API_KEY=您的密钥
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_MODEL_NAME=gpt-4o

# TTS
AZURE_TTS_API_KEY=您的密钥
AZURE_TTS_REGION=eastus

# 播客默认设置
HOST_1_NAME=Jack
HOST_2_NAME=Corr
```

**B. (可选) 自定义 `config.yaml`：**
编辑 `config.yaml` 以调整路径、输出目录和高级提取设置。

#### 4. 运行应用程序

**网页界面 (推荐)：**
```bash
streamlit run webui.py
```

**命令行版本：**
```bash
python main.py --generate-podcast
```

## Docker 部署

仓库包含一个生产级别的 `Dockerfile`。

```bash
docker build -t mynotebooklm .
docker run -p 8501:8501 --env-file .env mynotebooklm
```

## 贡献

欢迎大家贡献代码！请随时提交 Pull Request。

## 鸣谢 🙏

- 灵感来源于 Google’s NotebookLM。
- 参考了 [Podcastfy](https://github.com/souzatharsis/podcastfy) 的部分代码。

## 许可证

本项目采用 MIT 许可证 - 详情请查看 [LICENSE](LICENSE) 文件。
