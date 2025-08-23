import os
from datetime import datetime
from typing import Optional, Dict, Any

from loguru import logger

from structured_output_kit.utils.visualization import run_visualization_core


class VisualizationService:
    async def generate_html(
        self,
        eval_result_path: str,
        output_dir: Optional[str] = None,
        html_filename: str = "visualization.html",
    ) -> Dict[str, Any]:
        """Generate visualization HTML for a given evaluation result.

        Returns dict containing html_path, output_dir, overall_score
        """
        # Default output dir under result/visualization/<timestamp>
        if not output_dir:
            log_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = os.path.join("result", "visualization", log_time)

        try:
            result = run_visualization_core(
                eval_result_path=eval_result_path,
                output_dir=output_dir,
                html_filename=html_filename,
            )
            return result
        except Exception as e:
            logger.error(f"Visualization failed: {e}")
            raise
