# src/utils/common.py
import ast
import json
import logging
import sys
from pathlib import Path


def setup_logger(name="hf_supply_chain"):
    """Create and return a standard logger."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    return logger


logger = setup_logger()


def save_json(data, filepath: Path):
    """Save data to a JSON file."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    logger.info(f"Data successfully saved to {filepath}")


def load_json(filepath: Path):
    """Load data from a JSON file."""
    if not filepath.exists():
        logger.warning(f"File {filepath} does not exist.")
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def clean_license(license_data):
    """Normalize license formats into a single string."""
    if not license_data or license_data == "unknown":
        return "unknown"

    if isinstance(license_data, str) and license_data.startswith("["):
        try:
            license_data = ast.literal_eval(license_data)
        except Exception:
            pass

    if isinstance(license_data, list):
        parts = [str(x).strip().lower() for x in license_data if x]
        return ", ".join(parts) if parts else "unknown"

    return str(license_data).strip().lower()
