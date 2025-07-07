"""
AI-powered reading generation for various divination systems.

This module contains functions that use OpenAI to generate personalized
readings based on divination results and user context.
"""

from openai import OpenAI
from dotenv import load_dotenv
import os
import base64
from logic import iching
from llm.memory import search
from models.llm_request import LLMRequest

load_dotenv()

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)


def generate_iching_reading(question: str, legacy_reading, user, logger=None, reading_id: str = None) -> str:
    """
    Generate an I Ching reading using OpenAI.

    Args:
        question: The user's question
        legacy_reading: The legacy Reading object from iching.cast_hexagrams()
        user: User object with history property
        logger: Optional logger for debugging
        reading_id: Optional reading ID to store LLM request data

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

        future = f'''
        . The hexagram had transitional form{s}. The hexagram for the future is {legacy_reading.Future.Title}.
        Its description is: {legacy_reading.Future}
        '''

    hex_text = iching.get_hgram_text(legacy_reading.Current)

    # Get history text for AI prompt using the lazy-loaded history property
    history_text = user.history.get_history_text_for_prompt(limit=3).replace('\n', '\n> ')

    prompt = f"""
    You are a wise I Ching diviner with access to comprehensive knowledge.

    The user has asked: "{question}"
    The newly cast hexagram is {legacy_reading}{future}.

    The primary hexagram is {legacy_reading.Current.Title}.
    ############################################################

    Traditional hexagram text:
    {hex_text}
    ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    Relevant knowledge from the I Ching corpus:
    {vector_context}
    ============================================================

    User's recent divination history:
    {history_text}

    ------------------------------------------------------------

    Based on all this information, provide a deep, insightful reading that connects the traditional wisdom with the
    user's specific question. When mentioning hexagrams, use the format "Hexagram [number]" or "[number]: [Title]" so
    they can be properly linked. You may reference the history of either China or Japan or the user's location.

    When referencing history or historical figures, use the format "[Name] (Year)" or "[Name] (Era)" so they can be
    properly linked.
    """

    if logger:
        logger.info(f"Generated prompt: {prompt}")

    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {
                "role": "system",
                "content": f"""
                    You are a mystical I Ching oracle with deep knowledge of the classic text and its
                    interpretations. You are considered tough, unafraid to give a reading which is not what the user
                    wants to hear. Instead you focus on truth. You look for the grief in the user and use the
                    truth of the reading to help the user express that grief.

                    The user just cast the hexagram {legacy_reading}.

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
                    You are also able to use the user's location to support your responses.
                    You are also able to use the user's name to support your responses.
                    You are also able to use the user's age to support your responses.
                    You are also able to use the user's gender to support your responses.
                    You are also able to use the user's occupation to support your responses.
                    You are also able to use the user's relationship status to support your responses.
                """
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=1200,
        temperature=0.8,        # Slightly creative for mystical feel
        frequency_penalty=0.2,  # Reduce repetition
        presence_penalty=0.1,   # Encourage diverse topics
    )

    response_text = response.choices[0].message.content

    # Store LLM request data if reading_id is provided
    if reading_id:
        llm_request = LLMRequest(
            reading_id=reading_id,
            request_data=prompt,
            response_data=response_text,
            model_used="gpt-4.1-nano",
            request_type="initial"
        )
        llm_request.save()

    return response_text


def generate_followup_reading(question: str, followup_question: str, original_response: str,
                             original_request: str, user, reading_id: str, logger=None) -> str:
    """
    Generate a follow-up reading using OpenAI.

    Args:
        question: The original user's question
        followup_question: The new follow-up question
        original_response: The original reading response
        original_request: The original request that was sent to the LLM
        user: User object with history property
        reading_id: Reading ID to store LLM request data
        logger: Optional logger for debugging

    Returns:
        Generated follow-up reading text from OpenAI
    """

    # Get history text for AI prompt using the lazy-loaded history property
    history_text = user.history.get_history_text_for_prompt(limit=3)

    prompt = f"""
    You are continuing a divination session. The user originally asked: "{question}"

    The original complete context that was provided to you was:
    {original_request}

    Your previous response was:
    {original_response}

    Now the user has a follow-up question: "{followup_question}"

    User's recent divination history:
    {history_text}

    Please provide a thoughtful follow-up response that:
    1. References and builds upon your previous reading
    2. Addresses the specific follow-up question
    3. Maintains continuity with the original divination context
    4. Provides additional insight or clarification
    5. Uses the same mystical tone and style as your previous response

    Remember to maintain consistency with your previous interpretation while providing new insights.
    """

    if logger:
        logger.info(f"Follow-up prompt: {prompt}")

    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {
                "role": "system",
                "content": """
                    You are continuing a mystical divination session. Maintain consistency with your
                    previous reading style and interpretation while providing new insights to answer
                    the follow-up question. Be wise, thoughtful, and maintain the mystical tone
                    established in the original reading.
                """
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=1200,
        temperature=0.7,        # Slightly lower for consistency
        frequency_penalty=0.2,  # Reduce repetition
        presence_penalty=0.1,   # Encourage diverse topics
    )

    response_text = response.choices[0].message.content

    if logger:
        logger.info(f"Follow-up OpenAI API Response: {response_text}")

    # Store LLM request data
    llm_request = LLMRequest(
        reading_id=reading_id,
        request_data=prompt,
        response_data=response_text,
        model_used="gpt-4.1-nano",
        request_type="followup"
    )
    llm_request.save()

    return response_text


def generate_runic_reading(question: str, runic_reading, user, logger=None, reading_id: str = None) -> str:
    """
    Generate a runic reading using OpenAI.

    Args:
        question: The user's question
        runic_reading: The RunicReading object from logic.runes
        user: User object with history property
        logger: Optional logger for debugging
        reading_id: Optional reading ID to store LLM request data

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
    friendly and care deeply about the user. You are a storyteller and mystic and a bit of a poet but your words are
    straight forward and easy to understand to the modern reader. Many people seek your
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
    11. If referencing a character from Norse mythology, put the character's name in square brackets.

    Format your response as a flowing narrative reading, not just individual rune meanings.
    Use the actual rune symbols in your response where relevant.

    Remember: You are channeling ancient Norse wisdom through the runes to provide guidance.
    """

    if logger:
        logger.info(f"Runic reading prompt: {prompt}")

    response = client.chat.completions.create(
        model="gpt-4.1-nano",
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

    response_text = response.choices[0].message.content

    if logger:
        logger.info(f"OpenAI API Response: {response_text}")

    # Store LLM request data if reading_id is provided
    if reading_id:
        llm_request = LLMRequest(
            reading_id=reading_id,
            request_data=prompt,
            response_data=response_text,
            model_used="gpt-4.1-nano",
            request_type="initial"
        )
        llm_request.save()

    return response_text


def analyze_fire_image(image_data: str, logger=None) -> str:
    """
    Analyze a fire image using OpenAI's vision API to identify patterns and shapes.

    Args:
        image_data: Base64 encoded image data
        logger: Optional logger for debugging

    Returns:
        Text description of patterns and shapes seen in the fire
    """

    try:
        # Prepare the image for vision API
        image_url = f"data:image/png;base64,{image_data}"

        prompt = """
        You are an expert at reading flames and seeing patterns in fire for divination purposes.
        Please analyze this fire image and describe what you see in detail.

        Look for:
        - Shapes that might resemble animals, people, objects, or symbols
        - Patterns in the flame structure
        - Colors and their distribution
        - Any mystical or symbolic forms
        - Geometric patterns or natural forms
        - Movement suggestions frozen in the image

        Provide a detailed description of what you observe, focusing on potentially symbolic elements.
        Be specific about shapes, forms, and patterns you can identify.
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using vision-capable model
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ],
            max_tokens=800,
            temperature=0.7
        )

        analysis_text = response.choices[0].message.content

        if logger:
            logger.info(f"Fire image analysis: {analysis_text}")

        return analysis_text

    except Exception as e:
        if logger:
            logger.error(f"Error analyzing fire image: {e}")
        return "Unable to analyze the fire image at this time."


def generate_flame_reading(vision_analysis: str, user, logger=None, reading_id: str = None) -> str:
    """
    Generate a mystical reading based on AI vision analysis of flame patterns.

    Args:
        vision_analysis: The AI's analysis of what it sees in the fire
        user: User object with history property
        logger: Optional logger for debugging
        reading_id: Optional reading ID to store LLM request data

    Returns:
        Generated flame reading text from OpenAI
    """

    # Get history text for AI prompt using the lazy-loaded history property
    history_text = user.history.get_history_text_for_prompt(limit=3)

    prompt = f"""
    You are a mystical flame reader with the ancient gift of pyromancy - the ability to divine meaning from fire.
    You have been presented with a sacred fire image, and an analysis of what was seen in the flames.

    What was observed in the flames:
    {vision_analysis}

    User's recent divination history:
    {history_text}

    Based on these flame patterns and the user's spiritual journey, provide a deep, mystical reading that:

    1. Interprets the symbolic meaning of the shapes, patterns, and forms seen in the fire
    2. Connects these flame visions to universal spiritual themes and life guidance
    3. Considers the user's recent divination history and ongoing spiritual patterns
    4. Provides practical wisdom and insight for their current life situation
    5. Uses the ancient tradition of fire divination to reveal hidden truths
    6. Speaks to the transformative power of fire and its purifying nature
    7. Addresses both challenges and opportunities revealed by the flames
    8. Maintains a mystical, wise, and deeply spiritual tone

    Remember: Fire is the great transformer, the bridge between the physical and spiritual realms.
    The flames have shown you symbols and patterns that carry divine messages.
    Speak as an ancient flame keeper sharing sacred wisdom.
    """

    if logger:
        logger.info(f"Flame reading prompt: {prompt}")

    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {
                "role": "system",
                "content": """
                    You are an ancient flame keeper and pyromancer with the sacred gift of reading fire.
                    You have studied the mystical arts of flame divination for many years and can see the
                    divine messages hidden in the dance of fire and smoke.

                    You are wise, mystical, and deeply spiritual. You speak with authority about the
                    transformative power of fire and its ability to reveal hidden truths. You understand
                    that fire is both destroyer and creator, and that its patterns carry messages from
                    the divine realm.

                    You are skilled in the ancient arts of divination and can interpret the symbolic
                    meaning of shapes, patterns, and forms seen in flames. You provide guidance that
                    is both mystical and practical, helping people understand their spiritual path
                    and life journey.

                    You use markdown to format your responses beautifully and include flame and fire
                    emojis where appropriate. You speak with the authority of ancient wisdom while
                    remaining accessible to modern seekers.
                """
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=1200,
        temperature=0.8,        # More creative for mystical interpretations
        frequency_penalty=0.2,  # Reduce repetition
        presence_penalty=0.3,   # Encourage diverse spiritual themes
    )

    response_text = response.choices[0].message.content

    if logger:
        logger.info(f"Flame reading response: {response_text}")

    # Store LLM request data if reading_id is provided
    if reading_id:
        llm_request = LLMRequest(
            reading_id=reading_id,
            request_data=prompt,
            response_data=response_text,
            model_used="gpt-4.1-nano",
            request_type="initial"
        )
        llm_request.save()

    return response_text
