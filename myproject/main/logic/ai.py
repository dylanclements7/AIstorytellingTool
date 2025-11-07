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
model = genai.GenerativeModel('gemini-2.5-flash')


def storyOverview(idea_text):
    prompt = f"""
    Based on this story idea, create a 4-5 sentence overview and identify the primary tones. Common tones include: Frustration, Hopeful, Dramatic, Inspirational, Tense, Light-hearted, etc.
    
    Story Idea: {idea_text}
    
    Return ONLY a JSON object in this exact format with no markdown or labels, just the JSON:

    {{
        "overview": "A 2-3 sentence summary of the story",
        "tone": ["Tone1", "Tone2"]
    }}
    
    """
    
    try:
        response = model.generate_content(prompt)
        logger.warning(response.candidates[0].content.parts[0].text.strip())
        result = json.loads(response.candidates[0].content.parts[0].text.strip())
        return result
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        return {
            "overview": idea_text,
            "tone": ["Drama"]
        }
    except Exception as e:
        print(f"Error in storyOverview: {e}")
        raise

def editOverview(current_overview, feedback):
    prompt = f"""
    Based on this story overview and user feedback, create a 4-5 sentence overview and identify the primary tones. Common tones include: Frustration, Hopeful, Dramatic, Inspirational, Tense, Light-hearted, etc.
    
    Current overview: {current_overview}

    Feedback: {feedback}
    
    Return ONLY a JSON object in this exact format with no markdown or labels, just the JSON:

    {{
        "overview": "A 2-3 sentence summary of the story",
        "tone": ["Tone1", "Tone2"]
    }}
    
    """
    
    try:
        response = model.generate_content(prompt)
        logger.warning(response.candidates[0].content.parts[0].text.strip())
        result = json.loads(response.candidates[0].content.parts[0].text.strip())
        return result
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        return {
            "overview": feedback,
            "tone": ["Drama"]
        }
    except Exception as e:
        print(f"Error in storyOverview: {e}")
        raise


def storyGenerate(overview, tone):
    """
    Generate complete story structure with characters, locations, and scenes.
    
    Args:
        overview (str): Story overview
        tone (list): List of tone descriptors
        
    Returns:
        dict: Complete story structure with characters, locations, scenes
    """
    tone_str = ", ".join(tone)
    
    prompt = f"""
    Create a complete visual story structure based on this overview and tone.
    
    Overview: {overview}
    Tone: {tone_str}
    
    Generate 1-3 main characters, 1-3 key locations, and exactly 6 scenes that tell this story visually.
    
    Return ONLY a JSON object in this exact format:
    {{
        "characters": [
            {{
                "id": 1,
                "name": "Character Name",
                "age": "Age or age range",
                "clothing": "Detailed clothing description",
                "skin": "Skin tone description",
                "hair": "Hair description"
            }}
        ],
        "locations": [
            {{
                "id": 1,
                "name": "Location Name",
                "description": "Detailed visual description of the location suitable for image generation"
            }}
        ],
        "scenes": [
            {{
                "id": 1,
                "image_prompt": "Detailed visual description for image generation, including character appearance, location details, lighting, mood, and composition. Be specific and cinematic.",
                "narration": "The narrative text for this scene, including dialogue if appropriate. This should advance the story.",
                "image_path": ""
            }}
        ]
    }}
    
    Important:
    - Create exactly 6 scenes that tell a complete story arc
    - Each image_prompt should be detailed and cinematic (50-100 words)
    - Include specific visual details: lighting, camera angle, mood, colors
    - Narration should complement the visual and move the story forward
    - Characters should be consistent across scenes
    - Leave image_path as empty string (will be filled later)
    """
    
    try:
        response = model.generate_content(prompt)
        result = json.loads(response.text.strip())
        return result
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error in storyGenerate: {e}")
        print(f"Response text: {response.text}")
        raise
    except Exception as e:
        print(f"Error in storyGenerate: {e}")
        raise


def characterGenerate(story_data, character_id, feedback):
    """
    Regenerate a specific character based on feedback.
    
    Args:
        story_data (dict): Complete story data for context
        character_id (int): ID of character to regenerate
        feedback (str): User feedback on what to change
        
    Returns:
        dict: Updated character object
    """
    # Find the current character
    current_character = next(
        (char for char in story_data['characters'] if char['id'] == character_id),
        None
    )
    
    if not current_character:
        raise ValueError(f"Character with id {character_id} not found")
    
    prompt = f"""
    You are updating a character in a story with this context:
    
    Story Overview: {story_data['overview']}
    Tone: {', '.join(story_data['tone'])}
    
    Current Character:
    {json.dumps(current_character, indent=2)}
    
    User Feedback: {feedback}
    
    Other Characters in Story:
    {json.dumps([c for c in story_data['characters'] if c['id'] != character_id], indent=2)}
    
    Update this character based on the feedback while maintaining consistency with the story.
    
    Return ONLY a JSON object in this exact format:
    {{
        "id": {character_id},
        "name": "Character Name",
        "age": "Age or age range",
        "clothing": "Detailed clothing description",
        "skin": "Skin tone description",
        "hair": "Hair description"
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        result = json.loads(response.text.strip())
        return result
    except Exception as e:
        print(f"Error in characterGenerate: {e}")
        raise


def locationGenerate(story_data, location_id, feedback):
    """
    Regenerate a specific location based on feedback.
    
    Args:
        story_data (dict): Complete story data for context
        location_id (int): ID of location to regenerate
        feedback (str): User feedback on what to change
        
    Returns:
        dict: Updated location object
    """
    current_location = next(
        (loc for loc in story_data['locations'] if loc['id'] == location_id),
        None
    )
    
    if not current_location:
        raise ValueError(f"Location with id {location_id} not found")
    
    prompt = f"""
    You are updating a location in a story with this context:
    
    Story Overview: {story_data['overview']}
    Tone: {', '.join(story_data['tone'])}
    
    Current Location:
    {json.dumps(current_location, indent=2)}
    
    User Feedback: {feedback}
    
    Update this location based on the feedback. Make it detailed and suitable for visual image generation.
    
    Return ONLY a JSON object in this exact format:
    {{
        "id": {location_id},
        "name": "Location Name",
        "description": "Detailed visual description suitable for image generation, including atmosphere, lighting, key features, and mood"
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        result = json.loads(response.text.strip())
        return result
    except Exception as e:
        print(f"Error in locationGenerate: {e}")
        raise


def sceneGenerate(story_data, scene_id, image_feedback):
    """
    Regenerate a complete scene (image prompt, narration, and image path).
    
    Args:
        story_data (dict): Complete story data for context
        scene_id (int): ID of scene to regenerate
        image_feedback (str): User feedback on the image/visuals
        
    Returns:
        dict: Updated scene object with new image_prompt, narration, image_path
    """
    current_scene = next(
        (scene for scene in story_data['scenes'] if scene['id'] == scene_id),
        None
    )
    
    if not current_scene:
        raise ValueError(f"Scene with id {scene_id} not found")
    
    # Get previous and next scenes for context
    scene_index = scene_id - 1
    prev_scene = story_data['scenes'][scene_index - 1] if scene_index > 0 else None
    next_scene = story_data['scenes'][scene_index + 1] if scene_index < len(story_data['scenes']) - 1 else None
    
    prompt = f"""
    You are updating Scene {scene_id} in a 6-scene visual story.
    
    Story Overview: {story_data['overview']}
    Tone: {', '.join(story_data['tone'])}
    
    Characters:
    {json.dumps(story_data['characters'], indent=2)}
    
    Locations:
    {json.dumps(story_data['locations'], indent=2)}
    
    Current Scene {scene_id}:
    {json.dumps(current_scene, indent=2)}
    
    {"Previous Scene: " + json.dumps(prev_scene, indent=2) if prev_scene else "This is the first scene."}
    
    {"Next Scene: " + json.dumps(next_scene, indent=2) if next_scene else "This is the final scene."}
    
    User Feedback on Visuals: {image_feedback}
    
    Update this scene based on the feedback. The image_prompt and narration should work together to tell this part of the story.
    Maintain consistency with character appearances and the overall story arc.
    
    Return ONLY a JSON object in this exact format:
    {{
        "id": {scene_id},
        "image_prompt": "Detailed visual description for image generation (50-100 words). Include: character details, location, lighting, mood, camera angle, composition. Be cinematic and specific.",
        "narration": "The narrative text for this scene. Include dialogue if appropriate. Should advance the story and complement the visual.",
        "image_path": ""
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        result = json.loads(response.text.strip())
        return result
    except Exception as e:
        print(f"Error in sceneGenerate: {e}")
        raise


def narrationGenerate(story_data, scene_id, narration_feedback):
    """
    Regenerate only the narration for a scene.
    
    Args:
        story_data (dict): Complete story data for context
        scene_id (int): ID of scene to update
        narration_feedback (str): User feedback on the narration
        
    Returns:
        dict: {"narration": str}
    """
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
    You are updating the narration for Scene {scene_id} in a visual story.
    
    Story Overview: {story_data['overview']}
    Tone: {', '.join(story_data['tone'])}
    
    Scene {scene_id} Visual:
    {current_scene['image_prompt']}
    
    Current Narration:
    {current_scene['narration']}
    
    {"Previous Scene Narration: " + prev_scene['narration'] if prev_scene else "This is the first scene."}
    
    {"Next Scene Narration: " + next_scene['narration'] if next_scene else "This is the final scene."}
    
    User Feedback: {narration_feedback}
    
    Update the narration based on the feedback. It should complement the visual and maintain story continuity.
    
    Return ONLY a JSON object in this exact format:
    {{
        "narration": "Updated narrative text that advances the story and fits the visual context"
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        result = json.loads(response.text.strip())
        return result
    except Exception as e:
        print(f"Error in narrationGenerate: {e}")
        raise