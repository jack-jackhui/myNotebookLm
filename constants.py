"""Constants for MyNotebookLM."""

class EpisodeLength:
    SHORT = 750       # ~5 minutes (~750 words)
    MEDIUM = 2250     # ~15 minutes (~2,250 words)
    LONG = 4500       # ~30 minutes (~4,500 words)

class TokenLimits:
    DEFAULT = 1500
    SHORT_EPISODE = 1200
    MEDIUM_EPISODE = 3500
    LONG_EPISODE = 6000
    SUMMARY = 200
    ANSWER = 150
    TITLE = 50
    DESCRIPTION = 150

class Defaults:
    HOST_1_NAME = "Jack"
    HOST_2_NAME = "Corr"
    PODCAST_NAME = "AI Unchained"
    PODCAST_TAGLINE = "Your Guide to AI, Web 3.0, and the Cutting Edge of Tech"
    CREATIVITY = 0.7
    WORD_COUNT = 3000
