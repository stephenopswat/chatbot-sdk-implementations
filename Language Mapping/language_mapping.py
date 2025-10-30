from dotenv import load_dotenv
from openai import OpenAI
import os
import requests
import json 


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(BASE_DIR, "example.json")
with open(json_path, "r", encoding="utf-8") as f:
    example = json.load(f)

  
prompt = """
        You are a language detection and mapping system.
        You will need to do the following task for each string in the input, and return at a dictionary list: list[defaultdict(list)]
        Analyze the given text and identify:
        1. The document type (choose from: documentation, code snippet, faq, example, or other).
        2. The language(s) present. Include "English" if there is natural language text, and detect any programming language used (e.g., Python, JavaScript, C++, etc.).
        3. The tag(s) are keywords that is related to that piece of writing. It can be error-related or implementations,...

        Output strictly in JSON format:
        {
          "doc_type": "documentation" | "code snippet" | "faq" | "example" | "other",
          "languages": ["English", "Python"]
          "tags": ["404", "error-handling", "implementation"]
        }

        Now analyze this text:
        """


load_dotenv()
chatgpt_api = os.getenv("OPENAI_API")
if chatgpt_api is None:
    raise ValueError("OpenAI API Key not found")
client = OpenAI(api_key=chatgpt_api)

def language_mapping(file_content):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You analyze text for language composition."},
            {"role": "user", "content": prompt + f'\n\nText:\n"""{file_content}"""'}
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

content = []
for data in example:
    content.append(data["content"])
print(content)

return_data = language_mapping(content)["results"]

for i in range(len(example)):
    example[i]["content_info"] = return_data[i]

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(example, f, indent=2, ensure_ascii=False)