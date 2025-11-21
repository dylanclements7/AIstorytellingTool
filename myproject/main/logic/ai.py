import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=api_key)

# JSON Schemas for structured output
overview_schema = {
    "type": "object",
    "properties": {
        "storyline": {"type": "string"},
        "emotional_tones": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["storyline", "emotional_tones"]
}

story_schema = {
    "type": "object",
    "properties": {
        "storyline": {"type": "string"},
        "persona_description": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "age": {"type": "string"},
                    "clothing": {"type": "string"},
                    "skin": {"type": "string"},
                    "hair": {"type": "string"}
                },
                "required": ["id", "name", "age", "clothing", "skin", "hair"]
            }
        },
        "setting_description": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "description": {"type": "string"}
                },
                "required": ["id", "name", "description"]
            }
        },
        "scenes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "image_prompt": {"type": "string"}
                },
                "required": ["id", "image_prompt"]
            }
        },
        "emotional_tones": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["storyline", "persona_description", "setting_description", "scenes", "emotional_tones"]
}


def storyOverview(idea_text):
    prompt = f"""
    Based on this story idea, create a storyline overview in 6-10 sentences. The overview should include 1-3 main characters, 1-3 settings, and a description of 6 scenes.
    
    Based off the storyline, identify the primary emotional tones of the story.

    Story Idea: {idea_text}
    """
    
    try:
        model = genai.GenerativeModel(
            'models/gemini-2.5-flash',
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": overview_schema
            }
        )
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        logger.info(f"storyOverview result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in storyOverview: {e}")
        raise


def editOverview(current_overview, feedback):
    prompt = f"""
    Based on this story overview and user feedback, edit the 6-10 sentence storyline only making changes described in user feedback and then identify the primary emotional tones of the edited version. 

    Make sure the overview still includes 1-3 main characters, 1-3 settings, and a description of 6 scenes.
    
    Current overview: {current_overview}

    Feedback: {feedback}
    """
    
    try:
        model = genai.GenerativeModel(
            'models/gemini-2.5-flash',
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": overview_schema
            }
        )
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        logger.info(f"editOverview result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in editOverview: {e}")
        raise


def storyGenerate(draft):
    prompt = f"""
    You are a helpful tool to create a vlog-style script based off this Storyline with these emotional tones: {draft}. The vlog should be TikTok style and around 1 minute long."""
    prompt += f"""
    You should use chain-of-thoughts to create a script. 
    
    (1) Keep the storyline the same.

    (2) Create a persona_description of each persona (1-3 personas) including: id (starting from 1), name, age, clothing, skin tone, hair.

    (3) Create a setting_description for each setting (1-3 settings) including: id (starting from 1), name, and detailed description.

    (4) Create exactly 6 scenes. Each scene should have: id (starting from 1) and an image_prompt that describes a detailed visual for AI image generation using the persona and setting descriptions.

    (5) Keep the emotional_tones the same.
    """
    
    try:
        model = genai.GenerativeModel(
            'models/gemini-2.5-flash',
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": story_schema
            }
        )
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        logger.info(f"storyGenerate result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in storyGenerate: {e}")
        raise


def characterGenerate(story_data, character_id, feedback):
    current_character = next(
        (char for char in story_data['persona_description'] if char['id'] == character_id),
        None
    )
    
    if not current_character:
        raise ValueError(f"Character with id {character_id} not found")
    
    other_characters = [c for c in story_data['persona_description'] if c['id'] != character_id]
    
    prompt = f"""
    You are updating a character in a story and must regenerate the ENTIRE story to reflect this change consistently throughout.
    
    Current Story:
    Storyline: {story_data['storyline']}
    Emotional Tones: {', '.join(story_data['emotional_tones'])}
    
    Character Being Updated (ID {character_id}):
    {json.dumps(current_character, indent=2)}
    
    User Feedback for This Character: {feedback}
    
    Other Characters (keep these the same):
    {json.dumps(other_characters, indent=2)}
    
    Settings (keep these the same):
    {json.dumps(story_data['setting_description'], indent=2)}
    
    Current Scenes:
    {json.dumps(story_data['scenes'], indent=2)}
    
    IMPORTANT:
    1. Update character {character_id} based on the user feedback
    2. Keep the emotional tones, other characters, and settings the same
    3. Regenerate the storyline and all 6 scenes to reflect the updated character consistently
    4. If the character's name changed, update it everywhere in the scenes
    5. Maintain the same story flow and scene structure
    """
    
    try:
        model = genai.GenerativeModel(
            'models/gemini-2.5-flash',
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": story_schema
            }
        )
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        logger.info(f"characterGenerate result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in characterGenerate: {e}")
        raise


def locationGenerate(story_data, location_id, feedback):

    current_location = next(
        (loc for loc in story_data['setting_description'] if loc['id'] == location_id),
        None
    )

    if not current_location:
        raise ValueError(f"Location with id {location_id} not found")

    other_locations = [
        loc for loc in story_data['setting_description']
        if loc['id'] != location_id
    ]

    prompt = f"""
    You are updating a location in a story and must regenerate the ENTIRE story 
    to reflect this environmental change consistently throughout.

    Current Story:
    Storyline: {story_data['storyline']}
    Emotional Tones: {', '.join(story_data['emotional_tones'])}

    Location Being Updated (ID {location_id}):
    {json.dumps(current_location, indent=2)}

    User Feedback for This Location:
    {feedback}

    Other Locations (keep these the same):
    {json.dumps(other_locations, indent=2)}

    Characters (keep these the same):
    {json.dumps(story_data['persona_description'], indent=2)}

    Current Scenes:
    {json.dumps(story_data['scenes'], indent=2)}

    IMPORTANT:
    1. Update location {location_id} based on the user feedback.
    2. Keep the emotional tones, other characters, and other settings unchanged.
    3. Regenerate the storyline and all 6 scenes to reflect the updated location naturally.
    4. If this location's description changes significantly, update how scenes describe it.
    5. Maintain the same story flow, structure, and scene ordering.
    """

    try:
        model = genai.GenerativeModel(
            "models/gemini-2.5-flash",
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": story_schema   # <-- FULL STORY SCHEMA
            }
        )

        response = model.generate_content(prompt)
        result = json.loads(response.text)

        logger.info(f"locationGenerate result: {result}")
        return result

    except Exception as e:
        logger.error(f"Error in locationGenerate: {e}")
        raise
