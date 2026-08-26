import os
import json
import asyncio
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError

class AIProvider:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)

    async def generate_summary(self, repository: dict, dimensions: list) -> str:
        if not self.api_key:
            return "AI summary unavailable."

        prompt = f"""Based on this repository data and analysis dimensions, provide a 2-3 sentence summary:
Repository: {json.dumps(repository, indent=2)}
Dimensions: {json.dumps(dimensions, indent=2)}

What is the overall health of this repository?"""
        try:
            return await self._call_gemini(prompt)
        except Exception as e:
            print(f"[Gemini] generate_summary error: {e}")
            return "AI summary temporarily unavailable."

    async def generate_rizz_verdict(self, repository: dict, classification: dict, dimensions: list) -> str:
        if not self.api_key:
            return "AI verdict unavailable."

        prompt = f"""You are analyzing a GitHub repository. Answer this question: "What do you think about this project as a project idea?"

Judge the PROJECT IDEA and VALUE based on real repository evidence. Do NOT invent features or praise the project solely because it uses common technologies (like AI, React, Python). 
Focus on whether it solves a real problem, its practical utility, or its learning value.

Repository Data:
Name: {repository.get('name')}
Description: {repository.get('description', '')}
Type: {classification.get('type')}
Analysis: {json.dumps([d for d in dimensions if d.get('id') == 'documentation'], indent=2)}

If the project is genuinely useful or solves a real problem, explicitly say what makes it useful.
If the project is a common student or tutorial project (like a weather app, basic blog, etc.), explicitly say it is a common category and suggest ONE meaningful direction to differentiate it.
If it's a curated list or resource, acknowledge its utility.

Keep it strictly concise: 1–2 sentences maximum.

Examples:
"More than a repository — this gives developers a reusable resource they can build on. Strong practical value."
"Useful, but this is a common project idea. Add a meaningful differentiator or real-world capability to make it stand out."
"This solves a real developer problem and has clear practical value. A strong portfolio project with room to grow."
"Technically interesting with strong learning value. Its real strength is the problem it tackles, but stronger documentation would make the work easier to appreciate."
"The project works, but the core idea is fairly common. A stronger real-world problem or a meaningful differentiator would give it more impact."

Generate the verdict for this repository:"""
        try:
            return await self._call_gemini(prompt)
        except Exception as e:
            print(f"[Gemini] generate_rizz_verdict error: {e}")
            return "AI verdict temporarily unavailable."

    async def generate_recommendations(self, findings: list, dimensions: list) -> str:
        if not self.api_key:
            return "AI recommendations unavailable."

        prompt = f"""Based on these findings and dimension scores, provide 3-5 prioritized recommendations:
Findings: {json.dumps(findings[:10], indent=2)}
Dimensions: {json.dumps(dimensions, indent=2)}

What should the developer fix first? Be specific and actionable."""
        try:
            return await self._call_gemini(prompt)
        except Exception:
            return "AI recommendations temporarily unavailable."

    async def _call_gemini(self, prompt: str) -> str:
        models = ["gemini-1.5-flash", "gemini-1.5-pro"]
        last_error = ""

        for model_name in models:
            try:
                # Add 20s timeout by using asyncio.wait_for
                model = genai.GenerativeModel(model_name)
                # google-generativeai sync generate_content inside a thread
                response = await asyncio.wait_for(
                    asyncio.to_thread(model.generate_content, prompt),
                    timeout=20.0
                )
                if response and response.text:
                    return response.text.strip().replace('"', '')
            except asyncio.TimeoutError:
                print(f"[Gemini] Model {model_name} failed: Timeout (20s)")
                raise Exception("Timeout after 20 seconds")
            except Exception as e:
                last_error = str(e)
                print(f"[Gemini] Model {model_name} failed: {last_error[:100]}")
                if "503" not in last_error and "404" not in last_error:
                    break

        raise Exception(f"All models failed: {last_error}")
