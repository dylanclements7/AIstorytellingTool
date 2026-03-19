import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
import logging
from pathlib import Path
import time

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=api_key)


story_schema = {
    "type": "object",
    "properties": {
        "storyline": {
            "type": "array",
            "items": {"type": "string"}
            },
        "persona_description": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "species": {"type": "string"},
                    "name": {"type": "string"},
                    "age": {"type": "string"},
                    "clothing": {"type": "string"},
                    "disability": {"type": "string"},
                    "skin": {"type": "string"},
                    "hair": {"type": "string"}
                },
                "required": ["id", "species", "name", "age", "clothing", "disability", "skin", "hair"]
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
                    "narration": {"type": "string"},
                    "emotional_tones": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "characters": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "location": {"type": "string"}
                },
                "required": ["id", "image_prompt", "narration", "emotional_tones", "characters", "location"]
            }
        },
    },
    "required": ["storyline", "persona_description", "setting_description", "scenes"]
}


# CHAT_HISTORY_SCHEMA = {
#     "draft": [],
#     "personas": {},
#     "locations": {},
#     "scenes_image": {},
#     "scenes_narration": {}
# }

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
    
    Characters:
    {json.dumps(story_data['persona_description'], indent=2)}
    
    Locations:
    {json.dumps(story_data['setting_description'], indent=2)}
    
    Current Scenes:
    {json.dumps(story_data['scenes'], indent=2)}
    
    User Feedback for Storyline: {feedback}
    
    IMPORTANT:
    1. Update the storyline based on the user feedback
    2. Keep characters and locations generally the same unless the storyline change requires modification
    4. Regenerate all 6 scenes to match the updated storyline
    5. Maintain story coherence and flow
    """
    
    try:
        model = genai.GenerativeModel(
            'models/gemini-2.5-pro',
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": story_schema
            }
        )
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        logger.warning(f"storylineGenerate result: {result}")
        
        # Regenerate images for updated scenes
        result['scenes'] = generate_all_scene_images(result['scenes'], result, old_scenes=story_data.get('scenes'))
        
        return result
    except Exception as e:
        logger.error(f"Error in storylineGenerate: {e}")
        raise


def storyGenerate(conflict, moments="", resolution=""):
    """
    Generate a full story from structured inputs.
    `conflict` (the event/what it's about) is required.
    `resolution` (ending/message) is optional.
    `moments` is unused but kept for signature compatibility.
    """
    user_inputs = f"What the story is about / the event (required): {conflict}"

    if resolution and resolution.strip():
        user_inputs += f"\nHow it ends / the message (provided by user — must be used): {resolution}"
    else:
        user_inputs += "\nHow it ends / the message: not specified — invent a satisfying ending and clear emotional message."

    prompt = f"""
    You are a helpful tool to create a story for a 1-minute shortform video.

    The user has provided the following story inputs:
    {user_inputs}

    IMPORTANT: You MUST use the event/subject exactly as given. If an ending or message was provided,
    you MUST incorporate it faithfully. Only invent what was left blank.

    Use chain-of-thought to build the full story:

    (1) Create a 6-scene storyline (6–10 sentences total) including 1–3 main characters and
        1–3 key locations. Store the storyline of each scene as a string in the storyline array.
        The storyline must honour the event, and end with the provided resolution if given.

    (2) Identify the primary emotional tones of the story.

    (3) Create a persona_description for each persona (1–3) including: id (starting from 1),
        name, species, age, clothing, skin tone, hair, and disability.
        Be specific so AI image generation stays consistent across scenes.

    (4) Create a setting_description for each setting (1–3) including: id (starting from 1),
        name, and a detailed description for consistent image generation.

    (5) Create exactly 6 scenes. Each scene must have: id (starting from 1), narration,
        and an image_prompt describing a detailed visual for AI image generation.
        Each image_prompt must specify a consistent image style across all scenes.
        Each scene must also include 1–3 emotional tones, the personas present by name,
        and the setting by name.

    Ensure the storyline includes all personas and settings by exact name at least once.
    """

    try:
        model = genai.GenerativeModel(
            'models/gemini-2.5-pro',
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": story_schema
            }
        )
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        logger.info(f"storyGenerate result: {result}")
        result['scenes'] = generate_all_scene_images(result['scenes'], result, old_scenes=None)
        return result
    except Exception as e:
        logger.error(f"Error in storyGenerate: {e}")
        raise


import time
import re

def generate_scene_image(image_prompt, emotional_tones, scene_id, story_data, max_retries=3):
    # Replace character names with full descriptions
    enhanced_prompt = image_prompt
    
    for persona in story_data.get('persona_description', []):
        name = persona['name']
        description = f"a {persona['species']} with {persona['disability']}, {persona['age']} years old, with {persona['hair']} hair, {persona['skin']} skin, wearing {persona['clothing']}"
        enhanced_prompt = re.sub(r'\b' + re.escape(name) + r'\b', description, enhanced_prompt, flags=re.IGNORECASE)
    
    for location in story_data.get('setting_description', []):
        name = location['name']
        description = location['description']
        enhanced_prompt = re.sub(r'\b' + re.escape(name) + r'\b', description, enhanced_prompt, flags=re.IGNORECASE)
    
    tone_text = ", ".join(emotional_tones)
    enhanced_prompt += f". The image should reflect the emotional tones: {tone_text}."

    print(f"Enhanced prompt for scene {scene_id}: {enhanced_prompt}")
    for attempt in range(max_retries):
        try:
            from google import genai as google_genai
            from google.genai import types
            # Create client with API key
            client = google_genai.Client(api_key=api_key)
            
            # Generate image flash
            # response = client.models.generate_content(
            #     model="gemini-2.5-flash-image",
            #     contents=[enhanced_prompt],
            # )

            #Generate image pro
            response = client.models.generate_content(
                model="gemini-3-pro-image-preview",
                contents=[enhanced_prompt],
                config=types.GenerateContentConfig(
                    image_config=types.ImageConfig(
                        aspect_ratio="16:9"
                    )
                )
            )
            
            # Extract and save image
            for part in response.parts:
                if part.inline_data is not None:
                    image = part.as_image()
                    
                    image_dir = Path("main/static/main/images/generated")
                    image_dir.mkdir(parents=True, exist_ok=True)
                    
                    timestamp = int(time.time())
                    image_path = image_dir / f"scene_{scene_id}_{timestamp}.png"
                    image.save(str(image_path))
                    logger.info(f"Generated image for scene {scene_id} on attempt {attempt + 1}")
                    
                    # Return path 
                    return f"main/images/generated/scene_{scene_id}_{timestamp}.png", enhanced_prompt
            
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
                return f"main/images/generated/scene_{scene_id}.png"
    
    # Fallback if loop completes without returning
    return "main/images/exampleImage.png", enhanced_prompt


from concurrent.futures import ThreadPoolExecutor, as_completed

def generate_all_scene_images(scenes, story_data, old_scenes=None):
    """Generate images for scenes in parallel, only regenerating changed prompts."""
    updated_scenes = []
    scenes_to_generate = []
    
    # First pass: identify which scenes need new images
    for i, scene in enumerate(scenes):
        should_generate = True
        
        if old_scenes:
            old_scene = next((s for s in old_scenes if s['id'] == scene['id']), None)
            if old_scene and 'enhanced_prompt' in old_scene:
                # Generate the new enhanced prompt for comparison
                test_enhanced = scene.get('image_prompt', '')
                for persona in story_data.get('persona_description', []):
                    name = persona['name']
                    description = f"a {persona['species']} with {persona['disability']}, {persona['age']} years old, with {persona['hair']} hair, {persona['skin']} skin, wearing {persona['clothing']}"
                    test_enhanced = re.sub(r'\b' + re.escape(name) + r'\b', description, test_enhanced, flags=re.IGNORECASE)
                
                for location in story_data.get('setting_description', []):
                    name = location['name']
                    description = location['description']
                    test_enhanced = re.sub(r'\b' + re.escape(name) + r'\b', description, test_enhanced, flags=re.IGNORECASE)
                
                tone_text = ", ".join(scene['emotional_tones'])
                test_enhanced += f". The image should reflect the emotional tones: {tone_text}."
                
                # Compare enhanced prompts
                if test_enhanced == old_scene.get('enhanced_prompt') and 'image_path' in old_scene:
                    should_generate = False
                    scene['image_path'] = old_scene['image_path']
                    scene['enhanced_prompt'] = old_scene['enhanced_prompt']
                    logger.info(f"Reusing image for scene {scene['id']} - enhanced prompt unchanged")
        
        if should_generate:
            scenes_to_generate.append((i, scene))
        
        updated_scenes.append(scene)
    
    # Second pass: generate images in parallel
    if scenes_to_generate:
        logger.info(f"Generating {len(scenes_to_generate)} images in parallel...")
        
        def generate_single_scene(scene_tuple):
            """Helper function to generate a single scene's image"""
            index, scene = scene_tuple
            try:
                image_path, enhanced_prompt = generate_scene_image(
                    scene['image_prompt'],
                    scene['emotional_tones'],
                    scene['id'],
                    story_data
                )
                return (index, scene['id'], image_path, enhanced_prompt, None)
            except Exception as e:
                logger.error(f"Failed to generate image for scene {scene['id']}: {e}")
                return (index, scene['id'], "main/images/exampleImage.png", None, e)
        
        # Use ThreadPoolExecutor to generate images in parallel
        # Max workers = number of scenes to generate (but cap at 6 to avoid rate limits)
        max_workers = min(len(scenes_to_generate), 6)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_scene = {
                executor.submit(generate_single_scene, scene_tuple): scene_tuple 
                for scene_tuple in scenes_to_generate
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_scene):
                index, scene_id, image_path, enhanced_prompt, error = future.result()
                
                # Update the scene in our list
                updated_scenes[index]['image_path'] = image_path
                if enhanced_prompt:
                    updated_scenes[index]['enhanced_prompt'] = enhanced_prompt
                
                if error:
                    logger.error(f"Error generating image for scene {scene_id}: {error}")
                else:
                    logger.info(f"Generated NEW image for scene {scene_id}")
    
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
    2. Regenerate only the parts of the storyline and all 6 scenes that need to be changed to reflect the updated character naturally (updating apperance, name, etc.), leave the rest exactly the same.
    3. Maintain the same story flow, structure, and scene ordering.
    4. Minimize changes to unaffected parts of the story. Do not change anything that does not need to be changed in order to guarantee consistency.
    """
    
    try:
        model = genai.GenerativeModel(
            'models/gemini-2.5-pro',
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": story_schema
            }
        )
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        logger.info(f"characterGenerate result: {result}")

        logger.info("Regenerating all scene images with updated character...")
        result['scenes'] = generate_all_scene_images(result['scenes'], result, old_scenes=story_data.get('scenes'))
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
    2. Regenerate only the parts of the storyline and all 6 scenes that need to be changed to reflect the updated location naturally (updating description, name, etc.), leave the rest exactly the same.
    3. Maintain the same story flow, structure, and scene ordering.
    4. Minimize changes to unaffected parts of the story. Do not change anything that does not need to be changed in order to guarantee consistency.
    """

    try:
        model = genai.GenerativeModel(
            "models/gemini-2.5-pro",
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": story_schema  
            }
        )

        response = model.generate_content(prompt)
        result = json.loads(response.text)

        logger.info(f"locationGenerate result: {result}")

        logger.info("Regenerating all scene images with updated character...")
        result['scenes'] = generate_all_scene_images(result['scenes'], result, old_scenes=story_data.get('scenes'))
        return result

    except Exception as e:
        logger.error(f"Error in locationGenerate: {e}")
        raise

def sceneGenerate(story_data, scene_id, feedback):
    current_scene = next(
        (s for s in story_data['scenes'] if s['id'] == scene_id), None
    )
    if not current_scene:
        raise ValueError(f"Scene with id {scene_id} not found")

    scene_index = scene_id - 1
    scenes = story_data['scenes']
    prev_scene = scenes[scene_index - 1] if scene_index > 0 else None
    next_scene = scenes[scene_index + 1] if scene_index < len(scenes) - 1 else None

    change_schema = {
        "type": "object",
        "properties": {
            "image_prompt_changed": {"type": "boolean"},
            "narration_changed":    {"type": "boolean"},
            "storyline":            story_schema["properties"]["storyline"],
            "persona_description":  story_schema["properties"]["persona_description"],
            "setting_description":  story_schema["properties"]["setting_description"],
            "scenes":               story_schema["properties"]["scenes"]
        },
        "required": [
            "image_prompt_changed", "narration_changed",
            "storyline", "persona_description", "setting_description", "scenes"
        ]
    }

    prompt = f"""
    A user wants to edit Scene {scene_id} of their story. Decide what needs to change
    based on their feedback, then make the minimal changes required to keep the story consistent.

    RULES:
    1. If the feedback is purely about narration/dialogue/voiceover text → set image_prompt_changed=false,
       update only the narration for this scene, do NOT change image_prompt at all.
    2. If the feedback changes visuals (appearance, setting, action, lighting, style) → set image_prompt_changed=true,
       update image_prompt. Also update narration ONLY if it no longer makes sense after the visual change.
    3. If characters or locations change visually, update persona_description / setting_description for consistency.
    4. Always return the full scenes array with the final image_prompt and narration for every scene.
    5. Minimize changes to everything that doesn't need to change.

    Story context:
    Storyline: {json.dumps(story_data['storyline'], indent=2)}

    Characters:
    {json.dumps(story_data['persona_description'], indent=2)}

    Locations:
    {json.dumps(story_data['setting_description'], indent=2)}

    All scenes:
    {json.dumps(story_data['scenes'], indent=2)}

    Scene {scene_id} being edited:
    image_prompt : {current_scene['image_prompt']}
    narration    : {current_scene['narration']}
    {"Previous scene narration: " + prev_scene['narration'] if prev_scene else "This is the first scene."}
    {"Next scene narration: " + next_scene['narration'] if next_scene else "This is the last scene."}

    User feedback: {feedback}

    Return the complete updated story. Use image_prompt_changed and narration_changed flags
    to indicate what actually changed for scene {scene_id}.
    """

    try:
        model = genai.GenerativeModel(
            'models/gemini-2.5-pro',
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": change_schema
            }
        )
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        logger.info(
            f"sceneGenerate scene {scene_id}: "
            f"image_changed={result['image_prompt_changed']}, "
            f"narration_changed={result['narration_changed']}"
        )

        updated = {
            "storyline":           result["storyline"],
            "persona_description": result["persona_description"],
            "setting_description": result["setting_description"],
            "scenes":              result["scenes"]
        }

        if result["image_prompt_changed"]:
            logger.info(f"Regenerating image(s) for scene {scene_id}")
            updated["scenes"] = generate_all_scene_images(
                updated["scenes"], updated, old_scenes=story_data.get("scenes")
            )
        else:
            # Reuse all existing images — no regeneration needed
            for new_s in updated["scenes"]:
                old_s = next((s for s in story_data["scenes"] if s["id"] == new_s["id"]), None)
                if old_s:
                    new_s["image_path"]      = old_s.get("image_path", "")
                    new_s["enhanced_prompt"] = old_s.get("enhanced_prompt", "")

        return updated

    except Exception as e:
        logger.error(f"Error in sceneGenerate: {e}")
        raise

def deleteSceneGenerate(story_data, scene_id):
    """
    Delete a scene and regenerate the story to maintain coherency.
    Merges the deleted scene's content into adjacent scenes.
    """
    scenes = story_data.get('scenes', [])
    
    # Don't trust Gemini id handling so handling manually
    scene_to_delete = None
    scene_index = None
    for i, scene in enumerate(scenes):
        if scene['id'] == scene_id:
            scene_to_delete = scene
            scene_index = i
            break
    
    if not scene_to_delete:
        logger.error(f"Scene {scene_id} not found for deletion")
        return story_data
    
    # Get adjacent scenes context
    prev_scene = scenes[scene_index - 1] if scene_index > 0 else None
    next_scene = scenes[scene_index + 1] if scene_index < len(scenes) - 1 else None
    
    deleted_narration = scene_to_delete.get('narration', '')
    
    # Build prompt for storyline regeneration
    storyline_text = '\n'.join(story_data.get('storyline', []))
    
    prompt = f"""The user wants to delete a scene from their story. You need to update the storyline and regenerate all scenes to maintain story coherency by merging the deleted scene's content into the remaining narrative flow.

    Current Story:
    Storyline: {storyline_text}

    Characters:
    {json.dumps(story_data['persona_description'], indent=2)}

    Locations:
    {json.dumps(story_data['setting_description'], indent=2)}

    All Current Scenes:
    {json.dumps(scenes, indent=2)}

    Scene being deleted (Scene {scene_id}):
    Narration: {deleted_narration}
    Image Prompt: {scene_to_delete.get('image_prompt', '')}

    {"Previous scene (Scene " + str(prev_scene['id']) + "): " + prev_scene.get('narration', '') if prev_scene else "This is the first scene."}
    {"Next scene (Scene " + str(next_scene['id']) + "): " + next_scene.get('narration', '') if next_scene else "This is the last scene."}

    IMPORTANT:
    1. Remove Scene {scene_id} completely
    2. You must now have exactly {len(scenes) - 1} scenes (one fewer than before)
    3. Update the storyline to smoothly incorporate essential elements from the deleted scene into the surrounding narrative
    4. Adjust adjacent scenes to maintain narrative flow and coherency
    5. Keep characters and locations the same
    6. Renumber all scene IDs sequentially starting from 1
    7. Maintain the overall story arc but adjust pacing to account for the missing scene

    Return the complete updated story with the deleted scene removed."""
    
    try:
        model = genai.GenerativeModel(
            'models/gemini-2.5-pro',
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": story_schema
            }
        )
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        
        logger.info(f"Scene {scene_id} deleted. Story now has {len(result.get('scenes', []))} scenes")
        
        # Regenerate images for all scenes
        result['scenes'] = generate_all_scene_images(result['scenes'], result, old_scenes=story_data.get('scenes'))
        
        return result
    except Exception as e:
        logger.error(f"Error in deleteSceneGenerate: {e}")
        raise


def addSceneGenerate(story_data, after_scene_id):
    """
    Add a new scene between two existing scenes.
    Creates a bridging scene that connects the narrative flow.
    """
    scenes = story_data.get('scenes', [])
    
    # Find the scenes before and after the insertion point
    left_scene = None
    right_scene = None
    
    for i, scene in enumerate(scenes):
        if scene['id'] == after_scene_id:
            left_scene = scene
            if i + 1 < len(scenes):
                right_scene = scenes[i + 1]
            break
    
    if not left_scene:
        logger.error(f"Scene {after_scene_id} not found for insertion")
        return story_data
    
    # Build prompt for adding a scene
    storyline_text = '\n'.join(story_data.get('storyline', []))
    
    prompt = f"""The user wants to add a new scene between two existing scenes in their story.

    Current Story:
    Storyline: {storyline_text}

    Characters:
    {json.dumps(story_data['persona_description'], indent=2)}

    Locations:
    {json.dumps(story_data['setting_description'], indent=2)}

    All Current Scenes:
    {json.dumps(scenes, indent=2)}

    Left scene (Scene {left_scene['id']}):
    Narration: {left_scene.get('narration', '')}
    Image Prompt: {left_scene.get('image_prompt', '')}
    Location: {left_scene.get('location', '')}
    Characters: {', '.join(left_scene.get('characters', []))}

    {"Right scene (Scene " + str(right_scene['id']) + "):" if right_scene else "This is after the last scene."}
    {("Narration: " + right_scene.get('narration', '')) if right_scene else "Add an appropriate ending scene."}
    {("Image Prompt: " + right_scene.get('image_prompt', '')) if right_scene else ""}
    {("Location: " + right_scene.get('location', '')) if right_scene else ""}
    {("Characters: " + ', '.join(right_scene.get('characters', []))) if right_scene else ""}

    IMPORTANT:
    1. Create a new scene that bridges the left and right scenes naturally
    2. The new scene should logically connect the narrative flow between these two scenes
    3. You must now have exactly {len(scenes) + 1} scenes (one more than before)
    4. Update the storyline to include this new scene
    5. Maintain the story's pacing and tone
    6. Include appropriate characters and location based on context
    7. Renumber all scene IDs sequentially starting from 1
    8. The bridging scene should feel natural and not forced

    Example: If left scene is "John getting dressed" and right scene is "John arriving at work", 
    the new scene should be something like "John driving to work" or "John stopping for coffee on the way".

    Return the complete updated story with the new scene inserted."""
    
    try:
        model = genai.GenerativeModel(
            'models/gemini-2.5-pro',
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": story_schema
            }
        )
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        
        logger.info(f"New scene added after scene {after_scene_id}. Story now has {len(result.get('scenes', []))} scenes")
        
        # Regenerate images for all scenes
        result['scenes'] = generate_all_scene_images(result['scenes'], result, old_scenes=story_data.get('scenes'))
        
        return result
    except Exception as e:
        logger.error(f"Error in addSceneGenerate: {e}")
        raise


def splitSceneGenerate(story_data, scene_id):
    """
    Split a scene into two scenes that together cover the original scene's content.
    """
    scenes = story_data.get('scenes', [])
    
    # Find the scene to split
    scene_to_split = None
    scene_index = None
    for i, scene in enumerate(scenes):
        if scene['id'] == scene_id:
            scene_to_split = scene
            scene_index = i
            break
    
    if not scene_to_split:
        logger.error(f"Scene {scene_id} not found for splitting")
        return story_data
    
    # Build prompt for splitting the scene
    storyline_text = '\n'.join(story_data.get('storyline', []))
    
    prompt = f"""The user wants to split a scene into two separate scenes that together cover the same narrative content.

    Current Story:
    Storyline: {storyline_text}

    Characters:
    {json.dumps(story_data['persona_description'], indent=2)}

    Locations:
    {json.dumps(story_data['setting_description'], indent=2)}

    All Current Scenes:
    {json.dumps(scenes, indent=2)}

    Scene to split (Scene {scene_id}):
    Narration: {scene_to_split.get('narration', '')}
    Image Prompt: {scene_to_split.get('image_prompt', '')}
    Emotional Tones: {', '.join(scene_to_split.get('emotional_tones', []))}
    Characters: {', '.join(scene_to_split.get('characters', []))}
    Location: {scene_to_split.get('location', '')}

    IMPORTANT:
    1. Split Scene {scene_id} into TWO scenes that together tell the same story
    2. First scene: The beginning/setup/action starting
    3. Second scene: The middle-to-end/conclusion/result of the action
    4. You must now have exactly {len(scenes) + 1} scenes (one more than before)
    5. Both scenes should have distinct visual moments suitable for image generation
    6. Both scenes should maintain the same characters and location (unless the action involves movement)
    7. The two scenes should flow naturally into each other
    8. Update the storyline to reflect this split
    9. Renumber all scene IDs sequentially starting from 1
    10. Together, the two new scenes must cover ALL the narrative content of the original scene

    Example: If the scene is "John taking his lunch break", split it into:
    - Scene A: "John leaving his desk and heading to the cafeteria"  
    - Scene B: "John finishing his meal and returning to work"

    Return the complete updated story with this one scene replaced by two scenes."""
    
    try:
        model = genai.GenerativeModel(
            'models/gemini-2.5-pro',
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": story_schema
            }
        )
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        
        logger.info(f"Scene {scene_id} split into two scenes. Story now has {len(result.get('scenes', []))} scenes")
        
        # Regenerate images for all scenes
        result['scenes'] = generate_all_scene_images(result['scenes'], result, old_scenes=story_data.get('scenes'))
        
        return result
    except Exception as e:
        logger.error(f"Error in splitSceneGenerate: {e}")
        raise


def draftChat(story_data, chat_history):
    storyline_text = '\n'.join(
        f"Scene {i + 1}: {s}"
        for i, s in enumerate(story_data.get('storyline', []))
    )

    system_prompt = (
        """You are a helpful storyline editing assistant for a storyboard creation tool. 
        Have a natural, friendly conversation to understand what changes the user wants. 
        Ask clarifying questions if needed. Keep responses short (2-4 sentences). Use simple language.
        When the user seems satisfied, remind them to hit 'Done — Apply Changes'.\n\n
        fCurrent storyline:\n{storyline_text}"""
    )

    prompt_parts = [system_prompt, "\n\n"]
    for msg in chat_history:
        role_label = "User" if msg['role'] == 'user' else "Assistant"
        prompt_parts.append(f"{role_label}: {msg['content']}\n")
    prompt_parts.append("Assistant:")

    try:
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        response = model.generate_content("".join(prompt_parts))
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error in draftChat: {e}")
        raise


def personaChat(story_data, persona_id, chat_history):
    persona = next(
        (p for p in story_data.get('persona_description', []) if p['id'] == persona_id),
        None
    )
    if not persona:
        return "I couldn't find that character. Please try again."

    persona_text = (
        f"Name: {persona.get('name')}\n"
        f"Age: {persona.get('age')}\n"
        f"Clothing: {persona.get('clothing')}\n"
        f"Disability: {persona.get('disability')}\n"
        f"Skin: {persona.get('skin')}\n"
        f"Hair: {persona.get('hair')}"
    )

    system_prompt = (
        """You are a helpful character editing assistant for a storyboard creation tool. 
        The user wants to refine the appearance of a character. Have a natural, friendly conversation 
        to understand what changes they want. Ask clarifying questions if needed. 
        Keep responses short (2-4 sentences). Use simple language.
        When the user seems satisfied, remind them to hit 'Done — Apply Changes'.\n\n
        f"Current character:\n{persona_text}"""
    )

    prompt_parts = [system_prompt, "\n\n"]
    for msg in chat_history:
        role_label = "User" if msg['role'] == 'user' else "Assistant"
        prompt_parts.append(f"{role_label}: {msg['content']}\n")
    prompt_parts.append("Assistant:")

    try:
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        response = model.generate_content("".join(prompt_parts))
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error in personaChat: {e}")
        raise


def locationChat(story_data, location_id, chat_history):
    location = next(
        (l for l in story_data.get('setting_description', []) if l['id'] == location_id),
        None
    )
    if not location:
        return "I couldn't find that location. Please try again."

    location_text = (
        f"Name: {location.get('name')}\n"
        f"Description: {location.get('description')}"
    )

    system_prompt = (
        """You are a helpful location editing assistant for a storyboard creation tool. 
        The user wants to refine the appearance of a character. Have a natural, friendly conversation 
        to understand what changes they want. Ask clarifying questions if needed. 
        Keep responses short (2-4 sentences). Use simple language.
        When the user seems satisfied, remind them to hit 'Done — Apply Changes'.\n\n
        f"Current character:\n{location_text}"""
    )

    prompt_parts = [system_prompt, "\n\n"]
    for msg in chat_history:
        role_label = "User" if msg['role'] == 'user' else "Assistant"
        prompt_parts.append(f"{role_label}: {msg['content']}\n")
    prompt_parts.append("Assistant:")

    try:
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        response = model.generate_content("".join(prompt_parts))
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error in locationChat: {e}")
        raise


def sceneChat(story_data, scene_id, chat_history):
    scene = next(
        (s for s in story_data.get('scenes', []) if s['id'] == scene_id),
        None
    )
    if not scene:
        return "I couldn't find that scene. Please try again."

    scene_text = (
        f"Narration: {scene.get('narration')}\n"
        f"Image prompt: {scene.get('image_prompt')}\n"
        f"Location: {scene.get('location')}\n"
        f"Characters: {', '.join(scene.get('characters', []))}"
    )

    system_prompt = (
        """"You are a helpful character assistant for a storyboard creation tool. 
        The user wants to refine a scene in the storyboard, this could be editing the image prompt, narration, or both.
        Have a natural, friendly conversation 
        to understand what changes they want. Ask clarifying questions if needed. 
        Keep responses short (2-4 sentences). Use simple language.
        When the user seems satisfied, remind them to hit 'Done — Apply Changes'.\n\n
        f"Current character:\n{scene_text}"""
    )

    prompt_parts = [system_prompt, "\n\n"]
    for msg in chat_history:
        role_label = "User" if msg['role'] == 'user' else "Assistant"
        prompt_parts.append(f"{role_label}: {msg['content']}\n")
    prompt_parts.append("Assistant:")

    try:
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        response = model.generate_content("".join(prompt_parts))
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error in sceneChat: {e}")
        raise

def reflectionChat(story_data, chat_history):
    storyline_lines = "\n".join(
        f"  Scene {i + 1}: {s}"
        for i, s in enumerate(story_data.get("storyline", []))
    )

    characters_lines = "\n".join(
        f"  - {p['name']}, {p.get('age', '?')} years old. "
        f"Clothing: {p.get('clothing', 'n/a')}. "
        f"Disability: {p.get('disability', 'none')}. "
        f"Skin: {p.get('skin', 'n/a')}. Hair: {p.get('hair', 'n/a')}."
        for p in story_data.get("persona_description", [])
    )

    locations_lines = "\n".join(
        f"  - {l['name']}: {l.get('description', '')}"
        for l in story_data.get("setting_description", [])
    )

    scenes_lines = "\n".join(
        f"  Scene {s['id']}: {s.get('narration', '')}\n"
        f"    Emotional tones: {', '.join(s.get('emotional_tones', []))}\n"
        f"    Characters present: {', '.join(s.get('characters', []))}\n"
        f"    Location: {s.get('location', '')}"
        for s in story_data.get("scenes", [])
    )

    system_prompt = f"""You are a warm, gentle reflection assistant for a storyboard creation tool.
        Your role is to help the user see their story from a new, more hopeful perspective using
        evidence-based principles from Cognitive Behavioural Therapy (CBT) and narrative therapy.

        CORE PRINCIPLES TO WEAVE INTO THE CONVERSATION:
        1. Cognitive reframing: Gently invite the user to consider alternative interpretations of
        events in the story. ("What might a different character have been thinking in that moment?")
        2. Positive rendition: Explore how the story could have unfolded with better outcomes for
        the characters. ("If things had gone slightly differently, what might have changed?")
        3. Externalising: Help the user see problems as separate from the characters, not fixed traits.
        ("The conflict is something that happened to them, not who they are.")
        4. Identifying thinking patterns: If the story reflects black-and-white thinking,
        catastrophising, or hopelessness, gently name it and explore alternatives.
        5. Finding exceptions and strengths: Highlight moments of resilience, kindness, or courage
        already present in the story, even small ones.
        6. Preferred story: Guide the user toward imagining and articulating a more hopeful version
        of events — this will inform the story regeneration.

        CONVERSATION STYLE:
        - Warm, curious, and non-judgemental.
        - Ask one open question at a time — do not overwhelm.
        - Keep every response to 2–4 sentences maximum.
        - Never diagnose, prescribe, or give medical advice.
        - Use simple, accessible language.
        - Draw on specific details from the story — character names, scene moments, locations,
        emotional tones — to make the conversation feel personal and grounded.
        - When the conversation feels rich enough, gently suggest the user hit
        "Regenerate Story" to create a new version based on their insights.

        FULL STORY CONTEXT:

        Storyline:
        {storyline_lines}

        Characters:
        {characters_lines}

        Locations:
        {locations_lines}

        Scenes (with narration, emotional tone, and who is present):
        {scenes_lines}
        """

    prompt_parts = [system_prompt, "\n\n"]
    if not chat_history:
        # No history — this is the opening turn. Ask the model to start the conversation.
        prompt_parts.append(
            "This is the start of the conversation. Open with a warm, specific observation "
            "drawn from the story above — reference a particular scene, character, or emotional "
            "moment — then ask one open question to begin the reflection.\n\n"
        )
    else:
        for msg in chat_history:
            role_label = "User" if msg["role"] == "user" else "Assistant"
            prompt_parts.append(f"{role_label}: {msg['content']}\n")
    prompt_parts.append("Assistant:")

    try:
        model = genai.GenerativeModel("models/gemini-2.5-flash")
        response = model.generate_content("".join(prompt_parts))
        return response.text.strip()
    except Exception as e:
        logger.error(f"Error in reflectionChat: {e}")
        raise


def reflectionGenerate(story_data, reflection_summary):
    storyline_text = "\n".join(
        f"Scene {i + 1}: {s}"
        for i, s in enumerate(story_data.get("storyline", []))
    )

    prompt = f"""You are regenerating a story based on a therapeutic reflection conversation.

        The user has just completed a guided reflection using Cognitive Behavioural Therapy and
        narrative therapy principles. During the reflection they explored:
        - Alternative interpretations of events
        - How the story could have gone differently (positive rendition)
        - Strengths and moments of resilience in the characters
        - A more hopeful, preferred version of the story

        Your task is to regenerate the ENTIRE story — storyline, scenes, characters, and locations —
        guided by the insights from the reflection conversation below.

        REFLECTION CONVERSATION:
        {reflection_summary}

        ORIGINAL STORY:
        Storyline:
        {storyline_text}

        Characters:
        {json.dumps(story_data.get('persona_description', []), indent=2)}

        Locations:
        {json.dumps(story_data.get('setting_description', []), indent=2)}

        Scenes:
        {json.dumps(story_data.get('scenes', []), indent=2)}

        REGENERATION RULES:
        1. Keep the same characters and locations unless the reflection clearly called for changes.
        2. Maintain the same number of scenes unless there is a strong narrative reason.
        3. Shift the emotional tone toward the more hopeful, positive rendition discussed in the
        reflection — without making the story unrealistic or dismissive of difficulty.
        4. Apply cognitive reframes surfaced in the conversation: alternative perspectives,
        externalised problems, moments of strength.
        5. The new story should feel like a meaningful evolution of the original, not a
        completely different story, just seen through a gentler, more positive lens.
        6. Maintain story coherence and a clear arc across all scenes.
        """

    try:
        model = genai.GenerativeModel(
            "models/gemini-2.5-pro",
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": story_schema,
            },
        )
        response = model.generate_content(prompt)
        result = json.loads(response.text)
        logger.info(f"reflectionGenerate result: {result}")

        result["scenes"] = generate_all_scene_images(
            result["scenes"], result, old_scenes=story_data.get("scenes")
        )
        return result

    except Exception as e:
        logger.error(f"Error in reflectionGenerate: {e}")
        raise