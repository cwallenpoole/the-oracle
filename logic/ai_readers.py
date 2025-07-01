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


def generate_runic_reading(question: str, runic_reading, user, logger=None) -> str:
    """
    Generate a runic reading using OpenAI.

    Args:
        question: The user's question
        runic_reading: The RunicReading object from logic.runes
        user: User object with history property
        logger: Optional logger for debugging

    Returns:
        Generated reading text from OpenAI
    """

    # Get history text for AI prompt using the lazy-loaded history property
    history_text = user.history.get_history_text_for_prompt(limit=3)

    # Build rune details for the prompt
    rune_details = []
    for i, rune in enumerate(runic_reading.runes, 1):
        position_key = f"position_{i}"
        position_name = runic_reading.spread_positions.get(position_key, f"Position {i}")
        orientation = " (Reversed)" if rune.is_reversed else ""

        rune_details.append(f"""
Position {i} - {position_name}: {rune.symbol} {rune.name}{orientation}
- Phonetic: {rune.phonetic}
- Element: {rune.element}
- Deity: {rune.deity}
- Meaning: {rune.get_display_meaning()}
        """.strip())

    runes_text = "\n\n".join(rune_details)

    prompt = f"""
    You are a wise runic diviner with deep knowledge of the Elder Futhark and Norse mythology. You are laid back and
    friendly and care deeply about the user. You are a storyteller and mystic and a bit of a poet. Many people seek your
    guidance but you do not grow prideful or arrogant. You want to help guide each person through their life.
    You have cast runes for someone who asked: "{question}"

    The runic casting resulted in:

    Spread Type: {runic_reading.spread_type}

    {runes_text}

    User's recent divination history:
    {history_text}

    Please provide a thoughtful, personalized runic reading that:

    1. Interprets each rune in the context of its position in the spread
    2. Considers reversed meanings where applicable
    3. Weaves together the elemental and deity associations
    4. Relates the reading to their specific question
    5. Takes into account their recent divination history and patterns
    6. Provides practical guidance based on the runic wisdom
    7. Uses Norse mythological references when possible
    8. Maintains a mystical but grounded tone
    9. Do not refer to yourself as "I" or "me" in your responses.
    10. Speak in complete sentences.

    Format your response as a flowing narrative reading, not just individual rune meanings.
    Use the actual rune symbols in your response where relevant.

    Remember: You are channeling ancient Norse wisdom through the runes to provide guidance.
    """

    if logger:
        logger.info(f"Runic reading prompt: {prompt}")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
                    You are a mystical runic oracle with deep knowledge of the Elder Futhark and Norse
                    mythology. You are a practitioner of seidr magic and have deep connections to the
                    ancient wisdom of the Norse peoples. You are considered wise and truthful, unafraid
                    to give a reading which reveals difficult truths. Instead you focus on authentic
                    spiritual guidance. You look for the patterns and challenges in the user's life and
                    use the runic wisdom to help them understand their path.

                    You are also a master of the English language, and you are able to write in a way
                    that is informative and engaging but also mystical and evocative. You draw upon the
                    rich tapestry of Norse mythology and the primal wisdom of the runes.

                    You are able to use markdown to format your responses.
                    You are able to use runic symbols to represent the runes in your responses.
                    You weave together the meanings of individual runes into a cohesive narrative.
                    You reference the associated Norse deities and elemental correspondences.
                    You connect the reading to the user's question and life circumstances.
                """
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=1200,
        temperature=0.5,        # Slightly creative for mystical feel
        frequency_penalty=0.2,  # Reduce repetition
        presence_penalty=0.4,   # Encourage diverse topics
    )

    if logger:
        logger.info(f"OpenAI API Response: {response.choices[0].message.content}")

    return response.choices[0].message.content
