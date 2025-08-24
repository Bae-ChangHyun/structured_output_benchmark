from __future__ import annotations

import os
import importlib.util
from typing import Optional, Any
from enum import Enum
from dataclasses import asdict, is_dataclass
from pydantic import BaseModel

import yaml
import pandas as pd
from importlib import resources


def load_prompt() -> str:
    """Load extraction prompt with canonical path and fallbacks.

    Priority:
      1) package resource: resources/prompts/prompt.yaml
      2) legacy package root: prompt.yaml
      3) cwd: ./prompt.yaml
    """
    try:
        with resources.files("structured_output_kit").joinpath("prompt.yaml").open("r", encoding="utf-8") as f:
            prompt_yaml = yaml.safe_load(f)
        return prompt_yaml.get("Extract_prompt", "Extract information from the given content.")
    except Exception:
        pass
    if os.path.exists("prompt.yaml"):
        with open("prompt.yaml", "r", encoding="utf-8") as f:
            prompt_yaml = yaml.safe_load(f)
        return prompt_yaml.get("Extract_prompt", "Extract information from the given content.")
    return "Extract information from the given content."


def get_compatible_frameworks(provider: str):
    """Return compatible frameworks for a provider with canonical path and fallbacks.

        Priority for YAML location:
            1) structured_output_kit/extraction/compatibility.yaml
            2) ./extraction/compatibility.yaml (cwd fallback)
    """
    candidates = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "extraction", "compatibility.yaml"),
        os.path.join("extraction", "compatibility.yaml"),
    ]
    compatibility_data = None
    for yaml_path in candidates:
        try:
            with open(os.path.abspath(yaml_path), 'r', encoding='utf-8') as f:
                import yaml as _yaml
                compatibility_data = _yaml.safe_load(f)
                break
        except FileNotFoundError:
            continue
    if compatibility_data is None:
        return []

    compatible_frameworks = []
    for framework_name, framework_info in compatibility_data.items():
        if 'providers' in framework_info and provider in framework_info['providers']:
            compatible_frameworks.append(framework_name)
    return compatible_frameworks


def convert_schema(schema_name: str):
    """Dynamically import ExtractInfo class from a schema file.

    Accepts either a bare schema name or a file path ending with .py
    """
    if schema_name.endswith('.py') or '/' in schema_name or '\\' in schema_name:
        file_path = schema_name
        module_name = os.path.splitext(os.path.basename(file_path))[0]
    else:
        file_path = os.path.join(os.path.dirname(__file__), 'schema', f'{schema_name}.py')
        file_path = os.path.abspath(file_path)
        module_name = schema_name
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return getattr(mod, 'ExtractInfo')


def record_extraction(
    log_filename: str,
    provider: str,
    model: str,
    prompt: str,
    framework: str,
    success: bool,
    latency: float | int | None,
    langfuse_url: str | None,
    csv_path: str = "result/extraction_result.csv",
    result_json_path: Optional[str] = None,
    save: Optional[bool] = False,
):
    """Append a single extraction run record to CSV (creates file/dir if missing)."""
    record = {
        "log_filename": log_filename,
        "provider": provider,
        "model": model,
        "prompt": prompt,
        "framework": framework,
        "success": success,
        "latency": latency,
        "langfuse_url": langfuse_url,
        "result_json_path": result_json_path,
        "save": save,
    }
    if save:
        if os.path.isfile(csv_path):
            import pandas as pd  # local import in case optional
            df = pd.read_csv(csv_path)
            df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
        else:
            os.makedirs(os.path.dirname(csv_path), exist_ok=True)
            df = pd.DataFrame([record])
        df.to_csv(csv_path, index=False)


def response_parsing(response: Any) -> Any:
    if isinstance(response, list):
        response = {
            member.value if isinstance(member, Enum) else member for member in response
        }
    elif is_dataclass(response):
        response = asdict(response)
    elif isinstance(response, BaseModel):
        response = response.model_dump(exclude_none=True)
    return response
