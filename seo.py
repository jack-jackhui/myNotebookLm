"""SEO utilities for MyNotebookLM."""

import streamlit as st
import streamlit.components.v1 as components

# SEO Configuration
SEO_CONFIG = {
    "title": "MyNotebookLM - Open Source AI Podcast Generator",
    "description": "Turn any document into a podcast with AI. Open source alternative to Google NotebookLM. Multi-LLM support (OpenAI, Azure, Ollama, DeepSeek) and multiple TTS providers.",
    "canonical_url": "https://mynotebooklm.jackhui.com.au",
    "og_image": "https://mynotebooklm.jackhui.com.au/og-image.png",
    "author": "Jack Hui",
    "keywords": "notebooklm alternative, open source podcast generator, ai podcast maker, document to podcast, AI notes, podcast generator",
}


def inject_meta_tags():
    """Inject SEO meta tags and Open Graph tags into the page."""
    meta_tags = f"""
    <head>
        <!-- Primary Meta Tags -->
        <meta name="title" content="{SEO_CONFIG['title']}">
        <meta name="description" content="{SEO_CONFIG['description']}">
        <meta name="keywords" content="{SEO_CONFIG['keywords']}">
        <meta name="author" content="{SEO_CONFIG['author']}">
        <link rel="canonical" href="{SEO_CONFIG['canonical_url']}">

        <!-- Open Graph / Facebook -->
        <meta property="og:type" content="website">
        <meta property="og:url" content="{SEO_CONFIG['canonical_url']}">
        <meta property="og:title" content="{SEO_CONFIG['title']}">
        <meta property="og:description" content="{SEO_CONFIG['description']}">
        <meta property="og:image" content="{SEO_CONFIG['og_image']}">

        <!-- Twitter Card -->
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:url" content="{SEO_CONFIG['canonical_url']}">
        <meta name="twitter:title" content="{SEO_CONFIG['title']}">
        <meta name="twitter:description" content="{SEO_CONFIG['description']}">
        <meta name="twitter:image" content="{SEO_CONFIG['og_image']}">
    </head>
    """
    st.markdown(meta_tags, unsafe_allow_html=True)


def inject_structured_data():
    """Inject JSON-LD structured data for SEO."""
    json_ld = """
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": "MyNotebookLM",
        "description": "Open source AI podcast generator. Turn documents into podcasts.",
        "applicationCategory": "Multimedia",
        "operatingSystem": "Web",
        "offers": {
            "@type": "Offer",
            "price": "0",
            "priceCurrency": "USD"
        },
        "author": {
            "@type": "Person",
            "name": "Jack Hui"
        }
    }
    </script>
    """
    st.markdown(json_ld, unsafe_allow_html=True)


def render_seo_landing():
    """Render SEO-friendly landing content with headings and keywords."""
    st.markdown("# MyNotebookLM")
    st.markdown("## Turn Documents Into Podcasts with AI")

    with st.expander("About MyNotebookLM", expanded=False):
        st.markdown("""
**MyNotebookLM** is an open source AI podcast generator and a free alternative to Google NotebookLM.
Transform any document into an engaging podcast conversation using state-of-the-art AI.

**Features:**
- **Document to Podcast**: Convert PDFs, Word docs, web pages, and YouTube videos into audio
- **Multi-LLM Support**: Choose from OpenAI, Azure OpenAI, Ollama, or DeepSeek
- **Multiple TTS Providers**: Natural-sounding voices with OpenAI TTS, Azure Speech, or Edge TTS
- **Customizable Episodes**: Control episode length, host names, and intro/outro music

**Keywords**: notebooklm alternative, open source podcast generator, ai podcast maker, document to podcast
        """)


def init_seo():
    """Initialize all SEO components. Call this after st.set_page_config."""
    inject_meta_tags()
    inject_structured_data()
    render_seo_landing()
