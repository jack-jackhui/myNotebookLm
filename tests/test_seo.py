"""Tests for SEO module."""

import pytest


class TestSEOModule:
    """Tests for SEO module structure."""

    @pytest.fixture
    def seo_content(self):
        with open('seo.py', 'r') as f:
            return f.read()

    def test_seo_config_exists(self, seo_content):
        """SEO configuration should exist."""
        assert 'SEO_CONFIG' in seo_content

    def test_has_title(self, seo_content):
        """Should have SEO title."""
        assert 'MyNotebookLM - Open Source AI Podcast Generator' in seo_content

    def test_has_description(self, seo_content):
        """Should have SEO description."""
        assert 'Turn any document into a podcast with AI' in seo_content
        assert 'Open source alternative to Google NotebookLM' in seo_content

    def test_has_canonical_url(self, seo_content):
        """Should have canonical URL."""
        assert 'https://mynotebooklm.jackhui.com.au' in seo_content

    def test_has_author(self, seo_content):
        """Should have author."""
        assert 'Jack Hui' in seo_content


class TestMetaTags:
    """Tests for meta tag injection."""

    @pytest.fixture
    def seo_content(self):
        with open('seo.py', 'r') as f:
            return f.read()

    def test_inject_meta_tags_function(self, seo_content):
        """Should have inject_meta_tags function."""
        assert 'def inject_meta_tags' in seo_content

    def test_open_graph_tags(self, seo_content):
        """Should include Open Graph tags."""
        assert 'og:type' in seo_content
        assert 'og:url' in seo_content
        assert 'og:title' in seo_content
        assert 'og:description' in seo_content
        assert 'og:image' in seo_content

    def test_twitter_card_tags(self, seo_content):
        """Should include Twitter Card tags."""
        assert 'twitter:card' in seo_content
        assert 'twitter:url' in seo_content
        assert 'twitter:title' in seo_content
        assert 'twitter:description' in seo_content
        assert 'twitter:image' in seo_content

    def test_canonical_link(self, seo_content):
        """Should include canonical link."""
        assert 'rel="canonical"' in seo_content


class TestStructuredData:
    """Tests for JSON-LD structured data."""

    @pytest.fixture
    def seo_content(self):
        with open('seo.py', 'r') as f:
            return f.read()

    def test_inject_structured_data_function(self, seo_content):
        """Should have inject_structured_data function."""
        assert 'def inject_structured_data' in seo_content

    def test_json_ld_script(self, seo_content):
        """Should include JSON-LD script tag."""
        assert 'application/ld+json' in seo_content

    def test_software_application_schema(self, seo_content):
        """Should use SoftwareApplication schema."""
        assert '@type' in seo_content
        assert 'SoftwareApplication' in seo_content

    def test_schema_context(self, seo_content):
        """Should include schema.org context."""
        assert 'https://schema.org' in seo_content

    def test_schema_offers(self, seo_content):
        """Should include offers with free price."""
        assert '"price": "0"' in seo_content
        assert '"priceCurrency": "USD"' in seo_content

    def test_schema_author(self, seo_content):
        """Should include author in schema."""
        assert '"@type": "Person"' in seo_content


class TestSEOLandingContent:
    """Tests for SEO-friendly landing content."""

    @pytest.fixture
    def seo_content(self):
        with open('seo.py', 'r') as f:
            return f.read()

    def test_render_seo_landing_function(self, seo_content):
        """Should have render_seo_landing function."""
        assert 'def render_seo_landing' in seo_content

    def test_h1_heading(self, seo_content):
        """Should have H1 heading."""
        assert '# MyNotebookLM' in seo_content

    def test_h2_heading(self, seo_content):
        """Should have H2 subheading."""
        assert '## Turn Documents Into Podcasts' in seo_content

    def test_keywords_in_content(self, seo_content):
        """Should include SEO keywords."""
        assert 'notebooklm alternative' in seo_content
        assert 'open source podcast generator' in seo_content
        assert 'ai podcast maker' in seo_content
        assert 'document to podcast' in seo_content


class TestSEOInitialization:
    """Tests for SEO initialization function."""

    @pytest.fixture
    def seo_content(self):
        with open('seo.py', 'r') as f:
            return f.read()

    def test_init_seo_function(self, seo_content):
        """Should have init_seo function."""
        assert 'def init_seo' in seo_content

    def test_init_seo_calls_all_functions(self, seo_content):
        """init_seo should call all SEO functions."""
        assert 'inject_meta_tags()' in seo_content
        assert 'inject_structured_data()' in seo_content
        assert 'render_seo_landing()' in seo_content


class TestWebUISEOIntegration:
    """Tests for SEO integration in WebUI."""

    @pytest.fixture
    def webui_content(self):
        with open('webui.py', 'r') as f:
            return f.read()

    def test_imports_seo_module(self, webui_content):
        """WebUI should import seo module."""
        assert 'from seo import' in webui_content

    def test_calls_init_seo(self, webui_content):
        """WebUI should call init_seo."""
        assert 'init_seo()' in webui_content

    def test_page_title_updated(self, webui_content):
        """Page title should be SEO-optimized."""
        assert 'MyNotebookLM - Open Source AI Podcast Generator' in webui_content
