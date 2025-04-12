# utils/gpt_utils.py

import logging
from g4f.client import Client

# Set up logging
log = logging.getLogger('MyBot.GPTUtils')

def create_gpt_client():
    """Creates and returns a new g4f Client instance."""
    return Client()

def generate_response(messages, model="gpt-4o-mini"):
    """
    Generate a response using the g4f client.

    Args:
        messages (list): List of message dictionaries with 'role' and 'content' keys
        model (str): The model to use for generation (note: g4f may not respect this parameter)

    Returns:
        str: The generated response text
    """
    try:
        client = create_gpt_client()
        # Note: g4f doesn't support most parameters like temperature, tokens, etc.
        # Only model and messages are passed, and even model might be ignored
        response = client.chat.completions.create(
            model=model,
            messages=messages
        )
        return response.choices[0].message.content
    except Exception as e:
        log.error(f"Error generating GPT response: {e}")
        return f":x: Error communicating with the AI model: {str(e)}"

async def async_generate_response(messages, model="gpt-4o-mini"):
    """
    Asynchronous wrapper for generate_response.

    Args:
        messages (list): List of message dictionaries with 'role' and 'content' keys
        model (str): The model to use for generation

    Returns:
        str: The generated response text
    """
    # This is a simple wrapper that can be expanded with proper async implementation if needed
    return generate_response(messages, model)
