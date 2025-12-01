from django.shortcuts import render, redirect
from .logic.ai import characterGenerate, storyGenerate, locationGenerate, storylineGenerate, narrationGenerate, PromptGenerate
import logging
logger = logging.getLogger(__name__)
def idea(request):
    if request.method == 'POST':
        idea_text = request.POST.get('story_prompt', '')
        
        # Generate FULL story directly from the raw idea
        full_story = storyGenerate(idea_text)
        
        # Store complete story in session
        request.session['story'] = full_story
        request.session.modified = True
        
        logger.warning(f"Full story generated from idea")
        return redirect('draft')
    
    return render(request, 'main/idea.html')

def draft(request):
    story = request.session.get('story', {})
    
    # If no story exists, redirect back to idea
    if not story:
        return redirect('idea')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'regenerate':
            feedback = request.POST.get('feedback')
            
            # Regenerate ENTIRE story with updated storyline
            updated_story = storylineGenerate(story, feedback)
            
            # Replace entire story in session
            request.session['story'] = updated_story
            request.session.modified = True
            story = updated_story
            logger.warning(f"Storyline regenerated with full story update")
            
        elif action == 'next':
            return redirect('personas')
    
    # Display current storyline
    return render(request, 'main/draft.html', {
        'draft': {
            'storyline': story.get('storyline', ''),
            'emotional_tones': story.get('emotional_tones', [])
        }
    })

# def personas(request):
#     story = request.session.get('story', {})
    
#     if request.method == 'POST':
#         action = request.POST.get('action')
        
#         if action == 'regenerate':
            
#             persona_id = int(request.POST.get('persona_id'))
#             feedback = request.POST.get('feedback')
            
#             # Regenerate character
#             updated_character = characterGenerate(story, persona_id, feedback)
            
#             # Update in session
#             for i, char in enumerate(story['persona_description']):
#                 if char['id'] == persona_id:
#                     story['persona_description'][i] = updated_character
#                     break
            
#             request.session['story'] = story
#             request.session.modified = True
    
#     return render(request, 'main/personas.html', {
#         'persona_description': story.get('persona_description', []),
#     })

def personas(request):
    story_data = request.session.get('story', {})
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'regenerate':
            persona_id = int(request.POST.get('persona_id'))
            feedback = request.POST.get('feedback')
            
            # Get ENTIRE regenerated story
            updated_story = characterGenerate(story_data, persona_id, feedback)
            
            # Replace entire story in session
            request.session['story'] = updated_story
            request.session.modified = True
            story_data = updated_story  # Update local variable to reflect changes
            print("DEBUG updated_story:", updated_story)
    
    return render(request, 'main/personas.html', {
        'persona_description': story_data.get('persona_description', []),
    })



def locations(request):
    story_data = request.session.get('story', {})
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'regenerate':
            location_id = int(request.POST.get('location_id'))
            feedback = request.POST.get('feedback')
            
            # Get ENTIRE regenerated story
            updated_story = locationGenerate(story_data, location_id, feedback)
            
            # Replace entire story in session
            request.session['story'] = updated_story
            request.session.modified = True
            print("DEBUG updated_story:", updated_story)
            story_data = updated_story  # Update local variable to reflect changes
    
    return render(request, 'main/locations.html', {
        'setting_description': story_data.get('setting_description', []),
    })

def scene(request):
    story_data = request.session.get('story', {})
    
    if request.method == 'POST':
        action = request.POST.get('action')
        scene_id = int(request.POST.get('scene_id'))
        
        if action == 'regenerate_narration':
            # Only update narration for this scene
            feedback = request.POST.get('narration_feedback')
            
            updated_narration = narrationGenerate(story_data, scene_id, feedback)
            
            # Update only this scene's narration
            for scene in story_data['scenes']:
                if scene['id'] == scene_id:
                    scene['narration'] = updated_narration
                    break
            
            request.session['story'] = story_data
            request.session.modified = True
            logger.warning(f"Narration updated for scene {scene_id}")
            
        elif action == 'regenerate_image':
            # Regenerate ENTIRE story
            feedback = request.POST.get('image_prompt_feedback')
            
            updated_story = PromptGenerate(story_data, scene_id, feedback)
            
            # Replace entire story
            request.session['story'] = updated_story
            request.session.modified = True
            story_data = updated_story
            logger.warning(f"Full story regenerated from scene {scene_id} image prompt edit")
    
    return render(request, 'main/scene.html', {
        'scenes': story_data.get('scenes', []),
    })

def video(request):
    story_data = request.session.get('story', {})
    
    return render(request, 'main/video.html', {
        'scenes': story_data.get('scenes', []),
    })