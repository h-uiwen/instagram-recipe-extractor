from fastapi.middleware.cors import CORSMiddleware
import instaloader
from fastapi import FastAPI
import ollama

# Initialize FastAPI app
app = FastAPI()

# Allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev, allow all. Later restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Instaloader
L = instaloader.Instaloader()


@app.get("/")
def home():
    return {"message": "Instagram Recipe Extractor API (Ollama) is running!"}


import json
import re

@app.get("/extract_recipe")
def extract_recipe(insta_url: str):
    try:
        # Step 1: Extract shortcode from URL
        shortcode = insta_url.split("/")[-2]
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        caption = post.caption or ""

        # Step 2: Send caption to local LLaMA 3 model
        prompt = f"""
        You are a recipe extractor. Given this Instagram caption:
        {caption}

        Respond with ONLY valid JSON in this format:

        {{
          "title": "Recipe title",
          "ingredients": ["ingredient 1", "ingredient 2"],
          "steps": ["step 1", "step 2"]
        }}

        If no recipe is found, return:
        {{"recipe": false}}
        """

        response = ollama.chat(
            model="llama3",
            messages=[{"role": "user", "content": prompt}],
        )

        raw_output = response["message"]["content"]

        # ✅ Extract JSON substring using regex
        match = re.search(r"\{.*\}", raw_output, re.DOTALL)
        if match:
            json_str = match.group(0)
            try:
                recipe_json = json.loads(json_str)
            except json.JSONDecodeError:
                recipe_json = {"raw_output": raw_output}
        else:
            recipe_json = {"raw_output": raw_output}

        return {
            "caption": caption,
            "recipe": recipe_json,
        }

    except Exception as e:
        return {"error": str(e)}