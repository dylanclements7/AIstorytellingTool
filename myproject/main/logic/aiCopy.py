import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Configure Gemini
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

class Story():
    def __init__self(self):
        self.storyline = ""
        self.persona_description = []
        self.setting_description = []
        self.scenes = []
        self.emotional_tones = []

    def validate(self, json):
        #assign value and if error throw
        ai_object=json.loads(json_str)
        try:
            self.stooryline = ai_object['storyline']
        except:
            #throw
            pass

    def to_json(self):
        #convert to JSON object
        return json.dumps(self.__dict__)
    
def prompt_gemini(prompt):
    response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config={
        "response_mime_type": "application/json",
        "response_json_schema": Recipe.model_json_schema(),
    },
    )
    return response

#do one for openai as well

def gen_image(scene):
    #generate image based on scene JSON
    #switch personas in persona list out for the actual personas
    #do the same for loactions
    return 0

def updatePersona():
    #hand a persona that was editied, regenerate whole story with changes
    return 0
#do one of these for all possible edits

def storyOverview(idea_text):
    prompt = f"""
    Based on this story idea, create a <storyline> overview in 6-10 sentences. The overview should include 1-3 main characters, 1-3 settings, and a description of 6 scenes.
    
    Based off the storyline, identify the primary <emotional_tones> of the story.

    Story Idea: {idea_text}
    
    Return ONLY a JSON object in this exact format with no markdown or labels, just the following JSON:

    {{
        "storyline": <storyline>,
        "emotional_tones": ["Tone1", "Tone2"]
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
    Based on this story overview and user feedback, edit the 6-10 sentence storyline only making changes described in user feedback and then identify the primary emotional tones of the edited version. 

    Make sure the overview still includes 1-3 main characters, 1-3 settings, and a description of 6 scenes.
    
    Current overview: {current_overview}

    Feedback: {feedback}
    
    Return ONLY a JSON object in this exact format with no markdown or labels, just the following JSON:

    {{
        "storyline": <storyline>,
        "emotional_tones": ["Tone1", "Tone2"]
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


def storyGenerate(draft):
    prompt = f"""
    You are a helpful tool to create a vlog-style script based off this Storyline with these emotional tones: {draft}. The vlog should be TikTok style and around 1 minute long."""
    
    prompt+="""

    You should use chain-of-thoughts to create a script. 
    
    (1) storyline should remain the same.

    (2) Create a <persona_description> of each persona including: name, age, clothing, skin tone, hair. id should be index of character in list.

    (3) Create a <setting_description> for each setting. id should be index of setting in list.

    (4) Create 6 scenes, each scene is an <image_prompt> to generate a Gemini AI image for the video. id should be index of scene in list.

    (5) emotional_tones should remain the same.
    
    Return ONLY a JSON object in this exact format with no markdown or labels, just the follwing JSON:

    {{
        "storyline": <storyline>,
        "persona_description": [{
            "id": <id>,
            "name": "Character Name",
            "age": "Age or age range",
            "clothing": "Detailed clothing description",
            "skin": "Skin tone description",
            "hair": "Hair description"
        }],
        "setting_description": [{
            "id": <id>,
            "name": "Location Name",
            "description": "Detailed visual description of the location suitable for image generation"
        }],
        "scenes": [{
            "id": <id>,
            "image_prompt": <image_prompt>
        }],
        "emotional_tones": <emotional_tones>
    }}
    
    """
    #add to scenes a list of personas and lcoations in the scene
    try:
        #response = model.generate_content(prompt)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_json_schema": Recipe.model_json_schema(),
            },
        )
        logger.warning(response.candidates[0].content.parts[0].text.strip())
        result = json.loads(response.candidates[0].content.parts[0].text.strip())
        return result
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        return {
            "storyline": draft,
            "persona_description": [],
            "setting_description": [],
            "scenes": [],
            "emotional_tones": ["Drama"]
        }
    except Exception as e:
        print(f"Error in storyOverview: {e}")
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