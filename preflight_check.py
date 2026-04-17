#!/usr/bin/env python3
"""
Pre-flight check for MyNotebookLM deployment.
Run this before starting the container to verify all required files and configs are present.
"""

import os
import sys
from pathlib import Path

# Colors for terminal output
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def check_file(path: str, description: str, required: bool = True) -> bool:
    """Check if a file exists."""
    exists = os.path.exists(path)
    status = f"{GREEN}✓{RESET}" if exists else (f"{RED}✗{RESET}" if required else f"{YELLOW}○{RESET}")
    req_label = "REQUIRED" if required else "optional"
    print(f"  {status} {description}: {path} [{req_label}]")
    return exists

def check_env_var(name: str, description: str, required: bool = True, secret: bool = True) -> bool:
    """Check if an environment variable is set."""
    value = os.getenv(name)
    exists = bool(value)
    status = f"{GREEN}✓{RESET}" if exists else (f"{RED}✗{RESET}" if required else f"{YELLOW}○{RESET}")
    req_label = "REQUIRED" if required else "optional"
    display_value = "***" if (exists and secret) else (value[:30] + "..." if value and len(value) > 30 else value or "NOT SET")
    print(f"  {status} {description}: {name}={display_value} [{req_label}]")
    return exists

def main():
    print("\n" + "=" * 60)
    print("MyNotebookLM Pre-flight Check")
    print("=" * 60)
    
    errors = []
    warnings = []
    
    # Determine base path
    base_path = Path(__file__).parent
    if (base_path / "main.py").exists():
        pass  # Running from project root
    elif (Path("/mynotebooklm") / "main.py").exists():
        base_path = Path("/mynotebooklm")
    
    print(f"\nBase path: {base_path}")
    
    # 1. Check required files
    print(f"\n{YELLOW}[1/4] Checking required files...{RESET}")
    
    required_files = [
        (base_path / "config.yaml", "Main config"),
        (base_path / "configs" / "conversation_config.yaml", "Conversation config"),
        (base_path / "main.py", "Main script"),
        (base_path / "settings.py", "Settings module"),
    ]
    
    optional_files = [
        (base_path / "music" / "intro.mp3", "Intro music"),
        (base_path / "music" / "outro.mp3", "Outro music"),
        (base_path / ".env", "Environment file"),
    ]
    
    for path, desc in required_files:
        if not check_file(str(path), desc, required=True):
            errors.append(f"Missing required file: {path}")
    
    for path, desc in optional_files:
        check_file(str(path), desc, required=False)
    
    # 2. Check required environment variables
    print(f"\n{YELLOW}[2/4] Checking environment variables...{RESET}")
    
    # Load .env if present
    env_file = base_path / ".env"
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file)
    
    required_env = [
        ("AZURE_OPENAI_API_KEY", "Azure OpenAI API Key"),
        ("AZURE_OPENAI_ENDPOINT", "Azure OpenAI Endpoint"),
    ]
    
    optional_env = [
        ("AZURE_TTS_API_KEY", "Azure TTS API Key"),
        ("AZURE_TTS_REGION", "Azure TTS Region"),
        ("ELEVENLABS_API_KEY", "ElevenLabs API Key"),
        ("TELEGRAM_BOT_TOKEN", "Telegram Bot Token"),
        ("TELEGRAM_CHAT_ID", "Telegram Chat ID"),
    ]
    
    for name, desc in required_env:
        if not check_env_var(name, desc, required=True):
            errors.append(f"Missing required env var: {name}")
    
    for name, desc in optional_env:
        if not check_env_var(name, desc, required=False):
            warnings.append(f"Optional env var not set: {name}")
    
    # 3. Validate config structure
    print(f"\n{YELLOW}[3/4] Validating config structure...{RESET}")
    
    try:
        import yaml
        config_path = base_path / "config.yaml"
        if config_path.exists():
            with open(config_path) as f:
                config = yaml.safe_load(f)
            
            required_keys = ["llm_provider", "output_directories", "rss_feeds"]
            for key in required_keys:
                if key in config:
                    print(f"  {GREEN}✓{RESET} config.yaml has '{key}'")
                else:
                    print(f"  {RED}✗{RESET} config.yaml missing '{key}'")
                    errors.append(f"config.yaml missing required key: {key}")
        
        conv_config_path = base_path / "configs" / "conversation_config.yaml"
        if conv_config_path.exists():
            with open(conv_config_path) as f:
                conv_config = yaml.safe_load(f)
            
            if "text_to_speech" in conv_config:
                print(f"  {GREEN}✓{RESET} conversation_config.yaml has 'text_to_speech'")
                tts = conv_config["text_to_speech"]
                provider = tts.get("default_tts_provider", "unknown")
                print(f"  {GREEN}✓{RESET} TTS provider: {provider}")
            else:
                print(f"  {RED}✗{RESET} conversation_config.yaml missing 'text_to_speech'")
                errors.append("conversation_config.yaml missing 'text_to_speech' section")
                
    except Exception as e:
        print(f"  {RED}✗{RESET} Error validating configs: {e}")
        errors.append(f"Config validation error: {e}")
    
    # 4. Test imports
    print(f"\n{YELLOW}[4/4] Testing Python imports...{RESET}")
    
    try:
        sys.path.insert(0, str(base_path))
        from settings import load_llm_config, load_conversation_config
        print(f"  {GREEN}✓{RESET} settings module imports OK")
        
        config = load_llm_config()
        print(f"  {GREEN}✓{RESET} load_llm_config() works")
        
        conv_config = load_conversation_config()
        print(f"  {GREEN}✓{RESET} load_conversation_config() works")
        
    except Exception as e:
        print(f"  {RED}✗{RESET} Import error: {e}")
        errors.append(f"Import error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    if errors:
        print(f"{RED}PREFLIGHT CHECK FAILED{RESET}")
        print(f"\n{len(errors)} error(s):")
        for err in errors:
            print(f"  • {err}")
        if warnings:
            print(f"\n{len(warnings)} warning(s):")
            for warn in warnings:
                print(f"  • {warn}")
        print("=" * 60 + "\n")
        sys.exit(1)
    else:
        print(f"{GREEN}PREFLIGHT CHECK PASSED{RESET}")
        if warnings:
            print(f"\n{len(warnings)} warning(s):")
            for warn in warnings:
                print(f"  • {warn}")
        print("=" * 60 + "\n")
        sys.exit(0)

if __name__ == "__main__":
    main()
