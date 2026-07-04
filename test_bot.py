import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
STORE_NAME = os.environ.get("GEMINI_STORE_NAME")

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """You are OptiBot, the customer-support bot for OptiSigns.com.
- Tone: helpful, factual, concise.
- Only answer using the uploaded docs.
- Max 5 bullet points; else link to the doc.
- Cite up to 3 "Article URL:" lines per reply."""

def ask_optibot(question):
    print(f"Khách hàng: {question}")
    print("OptiBot đang truy xuất dữ liệu từ Vector Store...\n")

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=question,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[
                types.Tool(
                    file_search=types.FileSearch(
                        file_search_store_names=[STORE_NAME]
                    )
                )
            ]
        )
    )

    print("OptiBot trả lời:")
    print(response.text)

    print("\nBẰNG CHỨNG TRÍCH DẪN (GROUNDING):")
    for candidate in response.candidates:
        if candidate.grounding_metadata:
            for chunk in candidate.grounding_metadata.grounding_chunks:
                if hasattr(chunk, 'retrieved_context'):
                    context = chunk.retrieved_context
                    source_name = getattr(context, 'title', None) or getattr(context, 'uri', 'N/A')
                    print(f" - Lấy từ file: {source_name}")

if __name__ == "__main__":
    ask_optibot("How do I add a YouTube video?")