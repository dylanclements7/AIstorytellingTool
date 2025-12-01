import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=api_key)


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
                    "image_prompt": {"type": "string"},
                    "narration": {"type": "string"}
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


def storylineGenerate(story_data, feedback):
    """
    Regenerate the entire story with an updated storyline.
    
    Args:
        story_data (dict): Complete story data
        feedback (str): User feedback on storyline
        
    Returns:
        dict: Complete regenerated story with updated storyline
    """
    prompt = f"""
    You are updating the storyline of a story and must regenerate the ENTIRE story to reflect this change.
    
    Current Story:
    Storyline: {story_data['storyline']}
    Emotional Tones: {', '.join(story_data['emotional_tones'])}
    
    Characters:
    {json.dumps(story_data['persona_description'], indent=2)}
    
    Locations:
    {json.dumps(story_data['setting_description'], indent=2)}
    
    Current Scenes:
    {json.dumps(story_data['scenes'], indent=2)}
    
    User Feedback for Storyline: {feedback}
    
    IMPORTANT:
    1. Update the storyline based on the user feedback
    2. Update emotional tones if the storyline changes warrant it
    3. Keep characters and locations generally the same unless the storyline change requires modification
    4. Regenerate all 6 scenes to match the updated storyline
    5. Maintain story coherence and flow
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
        logger.info(f"storylineGenerate result: {result}")
        
        # Regenerate images for updated scenes
        result['scenes'] = generate_all_scene_images(result['scenes'])
        
        return result
    except Exception as e:
        logger.error(f"Error in storylineGenerate: {e}")
        raise


def storyGenerate(idea):
    prompt = f"""
    You are a helpful tool to create a vlog-style script based off this story idea: {idea}. The vlog should be in a 1 minute long shortform video style."""
    prompt += f"""
    Use chain-of-thoughts to create a script. 
    
    (1) Create a storyline in 6-10 sentences inlcuding 1-3 main characters and 1-3 key locations.

    (2) Identify the primary emotional tones of the story.

    (3) Create a persona_description of each persona (1-3 personas) including: id (starting from 1), name, age, clothing, skin tone, hair. Be detailed and specific so that image generation is consistent.

    (4) Create a setting_description for each setting (1-3 settings) including: id (starting from 1), name, and a detailed description so that image generation is consistent.

    (5) Create exactly 6 scenes. Each scene should have: id (starting from 1), the narration for the scene, and an image_prompt that describes a detailed visual for AI image generation using exactly the persona and setting descriptions.
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
        result['scenes'] = generate_all_scene_images(result['scenes'])
        return result
    except Exception as e:
        logger.error(f"Error in storyGenerate: {e}")
        raise


import time

def generate_scene_image(image_prompt, scene_id, max_retries=3):
    for attempt in range(max_retries):
        try:
            # Import here to avoid conflicts
            from google import genai as google_genai
            
            # Create client with API key
            client = google_genai.Client(api_key=api_key)
            
            # Generate image
            response = client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[image_prompt],
            )
            
            # Extract and save image
            for part in response.parts:
                if part.inline_data is not None:
                    image = part.as_image()
                    
                    # Create directory if it doesn't exist
                    image_dir = Path("main/static/main/images/generated")
                    image_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Save with scene_id as filename
                    image_path = image_dir / f"scene_{scene_id}.png"
                    image.save(str(image_path))
                    
                    logger.info(f"Generated image for scene {scene_id} on attempt {attempt + 1}")
                    
                    # Return path relative to static folder
                    return f"main/images/generated/scene_{scene_id}.png"
            
            # If no image in response
            logger.warning(f"No image generated for scene {scene_id} on attempt {attempt + 1}")
            
        except Exception as e:
            logger.warning(f"Error generating image for scene {scene_id} (attempt {attempt + 1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                # Exponential backoff: wait 2^attempt seconds
                wait_time = 2 ** attempt
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                # All retries failed
                logger.error(f"Failed to generate image for scene {scene_id} after {max_retries} attempts")
                return "main/images/exampleImage.png"
    
    # Fallback if loop completes without returning
    return "main/images/exampleImage.png"

def generate_all_scene_images(scenes):
    updated_scenes = []
    
    for scene in scenes:
        try:
            # Generate image for this scene
            image_path = generate_scene_image(scene['image_prompt'], scene['id'])
            
            # Update scene with image path
            scene['image_path'] = image_path
            updated_scenes.append(scene)
            
            logger.info(f"Generated image for scene {scene['id']}: {image_path}")
            
        except Exception as e:
            logger.error(f"Failed to generate image for scene {scene['id']}: {e}")
            # Use placeholder if generation fails
            scene['image_path'] = "main/images/exampleImage.png"
            updated_scenes.append(scene)
    
    return updated_scenes

def characterGenerate(story_data, character_id, feedback):
    current_character = next(
        (char for char in story_data['persona_description'] if char['id'] == character_id),
        None
    )
    
    if not current_character:
        raise ValueError(f"Character with id {character_id} not found")
    
    other_characters = [c for c in story_data['persona_description'] if c['id'] != character_id]
    
    prompt = f"""
    You are updating a character in a story and must edit any part of the story necessary to reflect this change consistently throughout.
    
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
    IMPORTANT:
    1. Update character {character_id} based on the user feedback.
    2. Keep the emotional tones, other characters, and other settings unchanged.
    3. Regenerate the parts of the storyline and all 6 scenes that need to be changed to reflect the updated location naturally.
    4. If this character's description changes significantly, update how scenes describe it.
    5. Maintain the same story flow, structure, and scene ordering.
    6. Minimize changes to unaffected parts of the story. Do not change anything that does not need to be changed in order to guarantee consistency.
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

        logger.info("Regenerating all scene images with updated character...")
        result['scenes'] = generate_all_scene_images(result['scenes'])
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
    You are updating a location in a story and must minimally regenerate any parts of the story 
    that need changes to reflect this environmental change consistently throughout.

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
    3. Regenerate the parts of the storyline and all 6 scenes that need to be changed to reflect the updated location naturally.
    4. If this location's description changes significantly, update how scenes describe it.
    5. Maintain the same story flow, structure, and scene ordering.
    6. Minimize changes to unaffected parts of the story. Do not change anything that does not need to be changed in order to guarantee consistency.
    """

    try:
        model = genai.GenerativeModel(
            "models/gemini-2.5-flash",
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": story_schema  
            }
        )

        response = model.generate_content(prompt)
        result = json.loads(response.text)

        logger.info(f"locationGenerate result: {result}")

        logger.info("Regenerating all scene images with updated character...")
        result['scenes'] = generate_all_scene_images(result['scenes'])
        return result

    except Exception as e:
        logger.error(f"Error in locationGenerate: {e}")
        raise

def narrationGenerate(story_data, scene_id, narration_feedback):
    current_scene = next(
        (scene for scene in story_data['scenes'] if scene['id'] == scene_id),
        None
    )
    
    if not current_scene:
        raise ValueError(f"Scene with id {scene_id} not found")
    
    scene_index = scene_id - 1
    prev_scene = story_data['scenes'][scene_index - 1] if scene_index > 0 else None
    next_scene = story_data['scenes'][scene_index + 1] if scene_index < len(story_data['scenes']) - 1 else None
    
    prompt = f"""
    You are updating ONLY the narration for Scene {scene_id}. Do not change anything else.
    
    Story Context:
    Storyline: {story_data['storyline']}
    Emotional Tones: {', '.join(story_data['emotional_tones'])}
    
    Scene {scene_id} Image:
    {current_scene['image_prompt']}
    
    Current Narration:
    {current_scene['narration']}
    
    {"Previous Scene Narration: " + prev_scene['narration'] if prev_scene else "This is the first scene."}
    {"Next Scene Narration: " + next_scene['narration'] if next_scene else "This is the final scene."}
    
    User Feedback: {narration_feedback}
    
    Update ONLY the narration based on the feedback. Maintain story continuity and match the visual description.
    
    Return as plain text, not JSON.
    """
    
    try:
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        response = model.generate_content(prompt)
        updated_narration = response.text.strip()
        logger.info(f"narrationGenerate for scene {scene_id}: updated")
        return updated_narration
    except Exception as e:
        logger.error(f"Error in narrationGenerate: {e}")
        raise


def PromptGenerate(story_data, scene_id, image_prompt_feedback):
    current_scene = next(
        (scene for scene in story_data['scenes'] if scene['id'] == scene_id),
        None
    )
    
    if not current_scene:
        raise ValueError(f"Scene with id {scene_id} not found")
    
    prompt = f"""
    A user is editing the image prompt for Scene {scene_id}. This change may affect character descriptions, 
    locations, or other story elements. You must regenerate any element in the story that needs to be changed to ensure
    complete consistency throughout the entire story.
    
    Current Story:
    Storyline: {story_data['storyline']}
    Emotional Tones: {', '.join(story_data['emotional_tones'])}
    
    Characters:
    {json.dumps(story_data['persona_description'], indent=2)}
    
    Locations:
    {json.dumps(story_data['setting_description'], indent=2)}
    
    Current Scene {scene_id}:
    Image Prompt: {current_scene['image_prompt']}
    Narration: {current_scene['narration']}
    
    All Scenes:
    {json.dumps(story_data['scenes'], indent=2)}
    
    User's Change to Scene {scene_id} Image Prompt: {image_prompt_feedback}
    
    IMPORTANT:
    1. If the feedback changes a character's appearance (hair color, clothing, age, etc.), 
       update that character in persona_description
    2. If the feedback changes a location's details, update that location in setting_description
    3. Update the storyline if the visual change affects the narrative
    4. Regenerate any of the image prompts that need to be changed to reflect the updated story elements.
    5. Update the narrations of any scenes affected by these changes.
    6. Maintain the same story flow, structure, and scene ordering.
    7. Make minimal changes necessary to ensure consistency after making the user's changes.
    
    The goal is complete consistency: if something changes visually in one scene, 
    it must be reflected everywhere in the story.
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
        logger.info(f"sceneImagePromptGenerate: full story regenerated from scene {scene_id} edit")
        
        # Regenerate ALL images with updated prompts
        logger.info("Regenerating all scene images...")
        result['scenes'] = generate_all_scene_images(result['scenes'])
        
        return result
    except Exception as e:
        logger.error(f"Error in sceneImagePromptGenerate: {e}")
        raise