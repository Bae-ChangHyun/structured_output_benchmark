from __future__ import annotations

import os
import json
from typing import Optional, Dict, Any

from loguru import logger

from structured_output_kit.utils.logging import setup_logger


def _build_simple_html(eval_result: Dict[str, Any]) -> str:
    """Build a minimal self-contained HTML snippet for visualization.

    This intentionally avoids heavy dependencies and keeps output portable.
    """
    overall = float(eval_result.get("overall_score", 0.0) or 0.0)
    # Basic safety for missing fields
    fields = eval_result.get("fields", {}) or {}

    # Create a simple list of top-level field scores if available
    rows = []
    for name, data in fields.items():
        try:
            score = float(data.get("score", 0.0) or 0.0)
        except Exception:
            score = 0.0
        ftype = data.get("type", "-")
        rows.append((name, score, ftype))

    rows.sort(key=lambda x: x[1], reverse=True)

    table_rows = "\n".join(
        f"<tr><td>{name}</td><td>{score:.3f}</td><td>{ftype}</td></tr>" for name, score, ftype in rows
    ) if rows else "<tr><td colspan='3' style='text-align:center;color:#666;'>No field details</td></tr>"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset=\"utf-8\" />
        <title>Evaluation Visualization</title>
        <style>
            :root {{ --ok: #2E8B57; --warn: #FFD700; --bad: #DC143C; }}
            body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 32px; }}
            .score {{ font-size: 28px; font-weight: 700; }}
            .box {{ background: #fafafa; border: 1px solid #eee; border-radius: 8px; padding: 16px; margin: 16px 0; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ border-bottom: 1px solid #eee; padding: 8px 12px; text-align: left; }}
            th {{ background: #f6f6f6; }}
            .badge {{ display:inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px; border:1px solid #ddd; color:#333; }}
        </style>
    </head>
    <body>
        <h1>평가 결과 시각화</h1>
        <div class=\"box\">
            <div>전체 점수</div>
            <div class=\"score\">{overall:.3f}</div>
        </div>
        <div class=\"box\">
            <div style=\"display:flex;align-items:center;gap:10px;\"> 
                <h3 style=\"margin:0;\">필드별 점수</h3>
                <span class=\"badge\">Top-level</span>
            </div>
            <table>
                <thead>
                    <tr><th>Field</th><th>Score</th><th>Type</th></tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    """


def run_visualization_core(
    eval_result_path: str,
    output_dir: Optional[str] = None,
    html_filename: str = "visualization.html",
) -> Dict[str, Any]:
    """Generate a static HTML visualization from an evaluation result JSON file.

    Returns a dictionary with keys: success, html_path, output_dir, overall_score
    """
    # Configure logging to a run folder; but default HTML location remains next to eval_result
    log_dir, _ = setup_logger(task="visualization")

    if not os.path.exists(eval_result_path):
        raise FileNotFoundError(f"Evaluation result not found: {eval_result_path}")

    logger.info(f"Loading evaluation result: {eval_result_path}")
    with open(eval_result_path, "r", encoding="utf-8") as f:
        eval_result = json.load(f)

    html_content = _build_simple_html(eval_result)

    # Prefer same folder as eval_result when output_dir not explicitly provided
    target_dir = output_dir or os.path.dirname(os.path.abspath(eval_result_path))
    os.makedirs(target_dir, exist_ok=True)
    html_path = os.path.join(target_dir, html_filename)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.success(f"Visualization HTML generated: {html_path}")

    return {
        "success": True,
        "html_path": html_path,
        "output_dir": target_dir,
        "overall_score": float(eval_result.get("overall_score", 0.0) or 0.0),
    }
