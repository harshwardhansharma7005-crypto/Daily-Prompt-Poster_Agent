import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import os
import pytest
from PIL import Image
from main import select_prompt, create_poster, PROMPT_LIBRARY

def test_select_prompt_uniqueness():
    state = {"used_prompts": ["study_1"], "last_category": "Study"}
    config_limit = 30
    prompt, history = select_prompt(state, PROMPT_LIBRARY, config_limit)
    
    assert prompt is not None
    assert prompt["id"] != "study_1"
    assert prompt["cat"] != "Study"

def test_poster_dimensions_and_mode(tmp_path):
    config = {
        "design": {
            "bg_color": "#0d0d0d", "gold_color": "#d4af37",
            "text_color": "#ffffff", "width": 1080, "height": 1350
        }
    }
    prompt = PROMPT_LIBRARY[0]
    out_dir = tmp_path / "output"
    
    out_path = create_poster(prompt, config, str(out_dir))
    
    assert os.path.exists(out_path)
    with Image.open(out_path) as img:
        assert img.size == (1080, 1350)
        assert img.mode == "RGB"
