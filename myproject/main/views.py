from django.shortcuts import render, redirect
from .logic.ai import characterGenerate, storyGenerate, locationGenerate, storylineGenerate, narrationGenerate, PromptGenerate
import logging
logger = logging.getLogger(__name__)
from django.urls import reverse
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
    
    if not story:
        return redirect('idea')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'regenerate':
            feedback = request.POST.get('feedback')
            
            updated_story = storylineGenerate(story, feedback)
            
            request.session['story'] = updated_story
            request.session.modified = True
            story = updated_story
            logger.warning(f"Storyline regenerated with full story update")
            
        elif action == 'next':
            return redirect('personas')
    
    scenes = story.get("scenes", [])

    emotional_tones = list({
        tone
        for scene in scenes
        for tone in scene.get("emotional_tones", [])
    })
    return render(request, 'main/draft.html', {
        'draft': {
            'storyline': story.get('storyline', ''),
            'emotional_tones': emotional_tones
        }
    })

def personas(request):
    story_data = request.session.get('story', {})
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'regenerate':
            persona_id = int(request.POST.get('persona_id'))
            feedback = request.POST.get('feedback')
            
            updated_story = characterGenerate(story_data, persona_id, feedback)
            
            request.session['story'] = updated_story
            request.session.modified = True
            story_data = updated_story 
            print("DEBUG updated_story:", updated_story)
        return redirect(f"{reverse('personas')}?slide={persona_id}")
    
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
            
            updated_story = locationGenerate(story_data, location_id, feedback)
            
            request.session['story'] = updated_story
            request.session.modified = True
            print("DEBUG updated_story:", updated_story)
            story_data = updated_story
        return redirect(f"{reverse('locations')}?slide={location_id}")
    
    return render(request, 'main/locations.html', {
        'setting_description': story_data.get('setting_description', []),
    })


def scene(request):
    story_data = request.session.get('story', {})
    
    if request.method == 'POST':
        action = request.POST.get('action')
        scene_id = int(request.POST.get('scene_id'))
        
        if action == 'regenerate_narration':
            feedback = request.POST.get('narration_feedback')
            from main.logic.ai import narrationGenerate
            updated_narration = narrationGenerate(story_data, scene_id, feedback)
            
            for scene in story_data['scenes']:
                if scene['id'] == scene_id:
                    scene['narration'] = updated_narration
                    break
            
            request.session['story'] = story_data
            request.session.modified = True
            logger.warning(f"Narration updated for scene {scene_id}")
            
        elif action == 'regenerate_image':
            feedback = request.POST.get('image_prompt_feedback')
            updated_story = PromptGenerate(story_data, scene_id, feedback)
            
            request.session['story'] = updated_story
            request.session.modified = True
            story_data = updated_story
            logger.warning(f"Full story regenerated from scene {scene_id} image prompt edit")
        return redirect(f"{reverse('scene')}?slide={scene_id}")
    
    return render(request, 'main/scene.html', {
        'scenes': story_data.get('scenes', []),
        'story_data': story_data 
    })

def video(request):
    story_data = request.session.get('story', {})
    
    return render(request, 'main/video.html', {
        'scenes': story_data.get('scenes', []),
    })