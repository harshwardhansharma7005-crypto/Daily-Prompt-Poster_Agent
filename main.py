import os
import json
import random
import textwrap
import sys
import requests
from PIL import Image, ImageDraw, ImageFont

# Local curated library of high-quality, safe AI prompts
PROMPT_LIBRARY = [
    {"id": "study_1", "cat": "Study", "text": "Design a study plan using the Feynman Technique for understanding complex topics in a short timeframe."},
    {"id": "prod_1", "cat": "Productivity", "text": "Act as a time management coach. Create a 3-day schedule for a professional balancing deep work, meetings, and exercise."},
    {"id": "write_1", "cat": "Writing", "text": "Generate an outline for a persuasive essay on the benefits of asynchronous communication in modern teams."},
    {"id": "code_1", "cat": "Coding", "text": "Review this hypothetical architecture and provide 3 concrete suggestions to improve its scalability and error handling."},
    {"id": "career_1", "cat": "Career", "text": "Draft a concise, professional follow-up email after a job interview that highlights my proactive attitude."},
    {"id": "biz_1", "cat": "Business", "text": "Create a simple one-page business plan template focused on sustainable growth and lean operations."},
    {"id": "budget_1", "cat": "Budgeting", "text": "Outline a zero-based budgeting framework suitable for a freelancer with variable monthly income."},
    {"id": "safe_1", "cat": "Digital Safety", "text": "List 5 practical habits for improving personal cybersecurity and password hygiene without overwhelming technical jargon."},
    {"id": "create_1", "cat": "Creativity", "text": "Brainstorm 10 unconventional ways to solve a creative block when working on a long-term artistic project."}
]

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def select_prompt(state, library, history_limit):
    history = state.get("used_prompts", [])
    last_cat = state.get("last_category")
    
    available = [p for p in library if p["id"] not in history]
    if not available:
        # Reset history if library exhausted
        available = library
        history = []
    
    preferred = [p for p in available if p["cat"] != last_cat]
    pool = preferred if preferred else available
    
    selected = random.choice(pool)
    return selected, history

def create_poster(prompt, config, output_dir):
    bg = config["design"]["bg_color"]
    gold = config["design"]["gold_color"]
    txt = config["design"]["text_color"]
    w, h = config["design"]["width"], config["design"]["height"]

    img = Image.new("RGB", (w, h), bg)
    draw = ImageDraw.Draw(img)

    # Decorative borders
    draw.rectangle([40, 40, w-40, h-40], outline=gold, width=8)
    draw.rectangle([60, 60, w-60, h-60], outline=gold, width=2)

    # Abstract geometry
    draw.ellipse([w-250, -50, w+50, 200], outline=gold, width=4)
    draw.polygon([(40, h-150), (200, h-40), (40, h-40)], fill=gold)

    # SAVE THIS callout
    draw.rectangle([w-260, 100, w-100, 160], fill=gold)
    
    try:
        f_callout = ImageFont.load_default(size=30)
        f_title = ImageFont.load_default(size=50)
        f_body = ImageFont.load_default(size=45)
        f_footer = ImageFont.load_default(size=35)
    except TypeError:
        # Fallback for older Pillow
        f_callout = f_title = f_body = f_footer = ImageFont.load_default()

    draw.text((w-245, 115), "SAVE THIS", fill=bg, font=f_callout)
    
    # Text contents
    draw.text((100, 250), f"AI PROMPT: {prompt['cat'].upper()}", fill=gold, font=f_title)
    
    wrapper = textwrap.TextWrapper(width=34)
    wrapped_text = wrapper.fill(f'"{prompt["text"]}"')
    draw.text((100, 360), wrapped_text, fill=txt, font=f_body, spacing=25)
    
    draw.line([100, h-200, w-100, h-200], fill=gold, width=2)
    draw.text((100, h-170), "Copy & paste this prompt for better results.", fill=gold, font=f_footer)

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, "poster.png")
    img.save(out_path)
    return out_path

def publish_to_facebook(image_path, caption):
    is_enabled = os.environ.get("PUBLISH_ENABLED", "false").lower() == "true"
    if not is_enabled:
        print("Publishing is DISABLED. Dry run successful.")
        return True

    page_id = os.environ.get("META_PAGE_ID")
    token = os.environ.get("META_PAGE_ACCESS_TOKEN")
    version = os.environ.get("META_GRAPH_API_VERSION", "v19.0")

    if not page_id or not token:
        print("ERROR: Missing Facebook API credentials (META_PAGE_ID or META_PAGE_ACCESS_TOKEN).")
        return False

    url = f"https://graph.facebook.com/{version}/{page_id}/photos"
    print("Publishing to Facebook...")
    
    try:
        with open(image_path, 'rb') as img_file:
            resp = requests.post(
                url,
                data={"message": caption, "access_token": token, "published": "true"},
                files={"source": img_file},
                timeout=30
            )
        resp.raise_for_status()
        print(f"Success! Facebook Post ID: {resp.json().get('id')}")
        return True
    except Exception as e:
        print(f"Failed to publish: {e}")
        if 'resp' in locals():
            print(f"Facebook API Response: {resp.text}")
        return False

def main():
    config = load_json("config.json")
    state_path = "data/state.json"
    state = load_json(state_path)

    prompt, history = select_prompt(state, PROMPT_LIBRARY, config["history_limit"])
    if not prompt:
        print("No valid prompts found. Exiting.")
        sys.exit(1)

    print(f"Selected Prompt ID: {prompt['id']} (Category: {prompt['cat']})")
    
    out_dir = "output"
    img_path = create_poster(prompt, config, out_dir)
    print(f"Poster generated at: {img_path}")

    caption = f"Level up your {prompt['cat'].lower()} game with this AI prompt!\n\n" \
              f"How to use: Copy the text in the image and paste it into your favorite AI assistant.\n\n" \
              f"#AI #Prompts #{prompt['cat'].replace(' ', '')} #Productivity #DailyPrompt"
    
    with open(os.path.join(out_dir, "caption.txt"), "w", encoding="utf-8") as f:
        f.write(caption)

    success = publish_to_facebook(img_path, caption)

    if success:
        history.append(prompt["id"])
        if len(history) > config["history_limit"]:
            history = history[-config["history_limit"]:]
        
        state["used_prompts"] = history
        state["last_category"] = prompt["cat"]
        save_json(state, state_path)
        
        # Create a tiny report
        with open(os.path.join(out_dir, "report.txt"), "w") as f:
            f.write(f"Status: Success\nPrompt ID: {prompt['id']}")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
