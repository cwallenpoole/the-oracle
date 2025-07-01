"""
AI-powered reading generation for various divination systems.

This module contains functions that use OpenAI to generate personalized
readings based on divination results and user context.
"""

from openai import OpenAI
from dotenv import load_dotenv
import os
from logic import iching
from llm.memory import search

load_dotenv()

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)


def generate_iching_reading(question: str, legacy_reading, user, logger=None) -> str:
    """
    Generate an I Ching reading using OpenAI.

    Args:
        question: The user's question
        legacy_reading: The legacy Reading object from iching.cast_hexagrams()
        user: User object with history property
        logger: Optional logger for debugging

    Returns:
        Generated reading text from OpenAI
    """

    # Get vector database content
    vector_results = search(str(legacy_reading))
    vector_context = "\n\n".join([str(result['metadata']) for result in vector_results])

    if logger:
        logger.info(f"Vector context: {vector_context}")

    s = ''
    future = 'Your current casting does not have a transition.'
    if legacy_reading.has_transition():
        s = 's'
        secondary_text = iching.get_hgram_text(legacy_reading.Future)
        future = f'''
        The hexagram had transitional form{s}. The hexagram for the future is {secondary_text}
        '''

    hex_text = iching.get_hgram_text(legacy_reading.Current)

    # Get history text for AI prompt using the lazy-loaded history property
    history_text = user.history.get_history_text_for_prompt(limit=3)

    prompt = f"""
    You are a wise I Ching diviner with access to comprehensive knowledge.

    The user has asked: "{question}"
    The newly cast hexagram is {legacy_reading}.

    Traditional hexagram text:
    {hex_text}

    Relevant knowledge from the I Ching corpus:
    {vector_context}

    {future}

    {history_text}

    Based on all this information, provide a deep, insightful reading that connects the traditional wisdom with the user's specific question. When mentioning hexagrams, use the format "Hexagram [number]" or "[number]: [Title]" so they can be properly linked.
    """

    if logger:
        logger.info(f"Generated prompt: {prompt}")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
                    You are a mystical I Ching oracle with deep knowledge of the classic text and its
                    interpretations. You are considered tough, unafraid to give a reading which is not what the user
                    wants to hear. Instead you focus on truth. You look for the grief in the user and use the
                    truth of the reading to help the user express that grief.
                    You are also a master of the English language, and you are able to write in a way that is
                    informative and engaging but also a bit poetic and sometimes a bit cryptic.
                    You are also able to use markdown to format your responses.
                    You are also able to use hexagram symbols to represent the hexagrams in your responses.
                    DO NOT USE THE CHINESE NAME OF THE HEXAGRAMS IN YOUR RESPONSES, ONLY USE THE ENGLISH NAME.
                    You are also able to use trigram symbols to represent the trigrams in your responses.
                    Mention the trigrams in your responses.
                    You are also able to use the I Ching corpus to support your responses.
                    You are also able to use the user's question to support your responses.
                    You are also able to use the user's history to support your responses.
                """
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=1200,
        temperature=0.8,        # Slightly creative for mystical feel
        frequency_penalty=0.2,  # Reduce repetition
        presence_penalty=0.1,   # Encourage diverse topics
    )

    return response.choices[0].message.content
