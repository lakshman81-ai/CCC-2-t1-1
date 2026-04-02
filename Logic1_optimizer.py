"""
Logic1_optimizer.py — Format optimizer for Logic 1.
Ported from P1 optimizer.py. Changes: all imports use Logic1_* prefixes.
"""
from Logic1_parser import CIIParser, ParserSettings
from Logic1_serializer import CIISerializer, SerializerSettings
from Logic1_comparator import compare_files
from Logic1_logger import get_logger
import random

logger = get_logger("Logic1_optimizer")

from Logic1_optimizer_settings import OptimizationSettings


class SerializationOptimizer:
    def __init__(self, original_path: str, data: dict, settings: OptimizationSettings):
        self.original_path = original_path
        self.data = data
        self.settings = settings

        with open(original_path, 'rb') as f:
            self.original_bytes = f.read()

    def optimize(self) -> dict:
        """
        Tries different format string parameters to minimize byte diff.
        """
        logger.info("[OPTIMIZE] Logic1: Starting format optimization loop...")

        best_diff = len(self.original_bytes)
        best_format = "{:13.6G}"

        param_space = []
        for width in [13]:
            for prec in [4, 5, 6, 7]:
                for type_char in ['G', 'E', 'f']:
                    param_space.append(f"{{:{width}.{prec}{type_char}}}")

        param_space.extend(["{:13.6g}", "{:13.5g}"])

        for idx, fmt in enumerate(param_space):
            if idx >= self.settings.max_iterations:
                break
            s_settings = SerializerSettings(real_format=fmt)
            serializer = CIISerializer(s_settings)

            gen_str = serializer.serialize(self.data)
            gen_bytes = gen_str.encode('latin-1')

            diff_result = compare_files(self.original_path, gen_bytes)
            diff_lines = diff_result.generate_diff_report().count('\n')

            logger.info(f"[OPTIMIZE] Logic1: Format '{fmt}' → diff: {diff_lines} lines")

            if diff_lines < best_diff:
                best_diff = diff_lines
                best_format = fmt

            if diff_result.is_exact_match:
                logger.info("[OPTIMIZE] Logic1: Exact match found!")
                return {"exact_match": True, "best_format": best_format}

        logger.info(f"[OPTIMIZE] Logic1: Done. Best: {best_format} (diff: {best_diff})")
        return {"exact_match": False, "best_format": best_format, "min_diff": best_diff}
