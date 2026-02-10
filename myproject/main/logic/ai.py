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

# def suggestionGenerate():
#     prompt = """
#     You are a helpful tool that suggests story ideas.
    
#     Generate exactly four unique engaging story ideas suitable for a 1 minute-long shortform video style.

#     Sugesstions should be no more than 80 characters.

#     Return the result strictly as JSON in the following format:
#     {
#     "suggestions": ["idea 1", "idea 2", "idea 3", "idea 4"]
#     }
#     """
    
#     try:
#         model = genai.GenerativeModel(
#             'models/gemini-2.5-flash',
#             generation_config={
#                 "response_mime_type": "application/json",
#                 "response_schema": {
#                     "type": "object",
#                     "properties": {
#                         "suggestions": {
#                             "type": "array",
#                             "items": {"type": "string"}
#                         }
#                     },
#                     "required": ["suggestions"]
#                 }
#             }
#         )
#         response = model.generate_content(prompt)
#         result = json.loads(response.text)
        
#         return result
#     except Exception as e:
#         logger.error(f"Error in suggestionGenerate: {e}")
#         raise

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


def storyGenerate(idea):
    prompt = f"""
    You are a helpful tool to create a story based off this story idea: {idea}. The story should be in a 1 minute-long shortform video style."""
    prompt += f"""
    Use chain-of-thoughts to create a script. 
    
    (1) Create a 6 scene storyline in 6-10 sentences inlcuding 1-3 main characters and 1-3 key locations, storing the storyline of each scene as a string in the storyline array.

    (2) Identify the primary emotional tones of the story.

    (3) Create a persona_description of each persona (1-3 personas) including: id (starting from 1), name, species, age, clothing, skin tone, hair. Be detailed and specific so that AI image generation is consistent with appearance repeatedly when handed this description.

    (4) Create a setting_description for each setting (1-3 settings) including: id (starting from 1), name, and a detailed description so that image generation is consistent with appearance repeatedly when handed this description.

    (5) Create exactly 6 scenes. Each scene should have: id (starting from 1), the narration for the scene, and an image_prompt that describes a detailed visual for AI image generation. Descriptions of characters and locations do not need to repeat details already included in persona_description and setting_description.
        Ensure each image prompt specifies the image style, it should be consistent across all scenes unless specifically requested otherwise.
        Each scene should also include 1-3 emotional tones in the scene, the personas present in the scene by name, and the setting in the scene by name.

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

# def generate_scene_image(image_prompt, emotional_tones, scene_id, story_data, max_retries=3):
#     # Replace character names with full descriptions
#     enhanced_prompt = image_prompt
    
#     for persona in story_data.get('persona_description', []):
#         name = persona['name']
#         description = f"{persona['name']}, {persona['age']} years old, with {persona['hair']} hair, {persona['skin']} skin, wearing {persona['clothing']}"
#         # Replace name with full description
#         enhanced_prompt = re.sub(r'\b' + re.escape(name) + r'\b', description, enhanced_prompt, flags=re.IGNORECASE)
    
#     # Replace location names with full descriptions
#     for location in story_data.get('setting_description', []):
#         name = location['name']
#         description = location['description']
#         enhanced_prompt = re.sub(r'\b' + re.escape(name) + r'\b', description, enhanced_prompt, flags=re.IGNORECASE)
#     tone_text = ", ".join(emotional_tones)
#     enhanced_prompt += f". The image should reflect the emotional tones: {tone_text}."

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
                        aspect_ratio="3:4"
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

def generate_all_scene_images(scenes, story_data, old_scenes=None):
    """Only regenerate images for scenes with changed enhanced prompts."""
    updated_scenes = []
    
    for i, scene in enumerate(scenes):
        try:
            should_generate = True
            
            if old_scenes:
                old_scene = next((s for s in old_scenes if s['id'] == scene['id']), None)
                if old_scene and 'enhanced_prompt' in old_scene:
                    # Generate the new enhanced prompt for comparison
                    test_enhanced = scene.get('image_prompt', '')
                    for persona in story_data.get('persona_description', []):
                        name = persona['name']
                        description = f"{persona['name']}, {persona['age']} years old, with {persona['hair']} hair, {persona['skin']} skin, wearing {persona['clothing']}"
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
                if i > 0:
                    time.sleep(1)
                
                image_path, enhanced_prompt = generate_scene_image(
                    scene['image_prompt'],
                    scene['emotional_tones'],
                    scene['id'],
                    story_data
                )
                scene['image_path'] = image_path
                scene['enhanced_prompt'] = enhanced_prompt  # Store for future comparisons
                logger.info(f"Generated NEW image for scene {scene['id']}")
            
            updated_scenes.append(scene)
            
        except Exception as e:
            logger.error(f"Failed to generate image for scene {scene['id']}: {e}")
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
        model = genai.GenerativeModel('models/gemini-2.5-pro')
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
    1. only if the feedback changes a character's appearance (hair color, clothing, age, etc.), 
       update that character in persona_description
    2. Only if the feedback changes a location's details, update that location in setting_description
    3. Update the storyline only if the change affects the narrative to guarantee consistency.
    4. Change only the image prompt for this scene, only change others if neccesary to maintain consitency and storyline.
    5. Maintain the same story flow, structure, and scene ordering.
    6. Make minimal changes necessary to ensure consistency after making the user's changes.
    
    The goal is complete consistency: if something changes visually in one scene, 
    it must be reflected everywhere in the story.
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
        logger.info(f"sceneImagePromptGenerate: full story regenerated from scene {scene_id} edit")
        
        # Regenerate ALL images with updated prompts
        logger.info("Regenerating all scene images...")
        result['scenes'] = generate_all_scene_images(result['scenes'], result, old_scenes=story_data.get('scenes'))
        
        return result
    except Exception as e:
        logger.error(f"Error in sceneImagePromptGenerate: {e}")
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