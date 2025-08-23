import os
from typing import Optional

from structured_output_kit.extraction.utils import get_compatible_frameworks


def select_llm():
    print("=== Provider 선택 ===")
    print("1. OpenAI")
    print("2. Anthropic")
    print("3. OpenAI-Compatible")
    print("4. Ollama")
    print("5. Google")
    choice = input("번호를 입력하세요 (1/2/3/4/5): ").strip()
    if choice == "1":
        return {
            "provider": "openai",
            "base_url": "https://api.openai.com/v1",
            "model": os.getenv("OPENAI_MODELS", "gpt-4.1-nano"),
            "api_key": os.getenv("OPENAI_API_KEY"),
        }
    elif choice == "2":
        return {
            "provider": "anthropic",
            "base_url": "https://api.anthropic.com/v1",
            "model": os.getenv("ANTHROPIC_MODELS", "claude-sonnet-4-20250514"),
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
        }
    elif choice == "3":
        return {
            "provider": "openai_compatible",
            "base_url": os.getenv("OPENAI_COMPATIBLE_BASEURL"),
            "model": os.getenv("OPENAI_COMPATIBLE_MODELS", "openai/gpt-oss-120b"),
            "api_key": os.getenv("OPENAI_COMPATIBLE_API_KEY", "dummy"),
        }
    elif choice == "4":
        return {
            "provider": "ollama",
            "base_url": os.getenv("OLLAMA_BASEURL", "http://localhost:11434/v1"),
            "model": os.getenv("OLLAMA_MODELS", "llama3.1:8b"),
            "api_key": os.getenv("OLLAMA_API_KEY", "dummy"),
        }
    elif choice == "5":
        return {
            "provider": "google",
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "model": os.getenv("GOOGLE_MODELS", "gemini-1.5-flash"),
            "api_key": os.getenv("GOOGLE_API_KEY"),
        }
    else:
        raise ValueError("Invalid provider selection")


def select_embed():
    print("=== Provider 선택 ===")
    print("1. OpenAI")
    print("2. OpenAI-Compatible")
    print("3. HuggingFace")
    choice = input("번호를 입력하세요 (1/2/3): ").strip()
    if choice == "1":
        return {
            "provider": "openai",
            "base_url": "https://api.openai.com/v1",
            "model": os.getenv("OPENAI_EMBED_MODELS", "text-embedding-3-small"),
            "api_key": os.getenv("OPENAI_API_KEY"),
        }
    elif choice == "2":
        return {
            "provider": "openai_compatible",
            "base_url": os.getenv("OPENAI_COMPATIBLE_EMBED_BASEURL"),
            "model": os.getenv("OPENAI_COMPATIBLE_EMBED_MODELS", "Qwen/Qwen3-Embedding-8B"),
            "api_key": os.getenv("OPENAI_COMPATIBLE_EMBED_API_KEY", None),
        }
    elif choice == "3":
        return {
            "provider": "huggingface",
            "base_url": "",
            "model": os.getenv("HUGGINGFACE_EMBED_MODELS", "bert-base-uncased"),
            "api_key": "",
        }
    else:
        raise ValueError("Invalid provider selection")


def select_framework(provider: str) -> Optional[str]:
    """provider에 호환되는 프레임워크 목록에서 선택.

    API/자동화에서는 사용하지 말고 CLI에서만 사용하세요.
    """
    compatible_frameworks = get_compatible_frameworks(provider)
    if not compatible_frameworks:
        print(f"선택한 provider '{provider}'에 호환되는 프레임워크가 없습니다.")
        return None

    print(f"\n=== {provider}에 호환되는 프레임워크 목록 ===")
    for i, framework in enumerate(compatible_frameworks, 1):
        print(f"{i}. {framework}")
    while True:
        try:
            choice = input(f"번호를 입력하세요 (1-{len(compatible_frameworks)}): ").strip()
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(compatible_frameworks):
                return compatible_frameworks[choice_idx]
            else:
                print("잘못된 번호입니다. 다시 입력해주세요.")
        except ValueError:
            print("숫자를 입력해주세요.")
