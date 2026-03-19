from groq import Groq
import os
from dotenv import load_dotenv
load_dotenv()

groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])

# def get_short_summary(title: str, description: str) -> str:
#     prompt = f"""
#     You are a helpful summarizer. Using the following YouTube video title and description, provide a brief 4-point summary with marker point for html paget to show. Each point should be concise and informative.

#     ### Title:
#     {title}

#     ### Description:
#     {description}

#     ### Summary:"""

#     response = groq_client.chat.completions.create(
#         model="meta-llama/llama-4-maverick-17b-128e-instruct",
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0.3
#     )

#     return response.choices[0].message.content.strip()


def get_short_summary(title: str, description: str) -> str:
    prompt = f"""
    You are a helpful summarizer. Based on the YouTube video title and description, generate a clear 4-point summary.

    Each point MUST:
    - Start with **Point 1:**, **Point 2:**, etc. (exact format)
    - Be on a separate line
    - Avoid combining points into a paragraph

    ### Title:
    {title}

    ### Description:
    {description}

    ### Summary:
    """
    response = groq_client.chat.completions.create(
        model="meta-llama/llama-4-maverick-17b-128e-instruct",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

