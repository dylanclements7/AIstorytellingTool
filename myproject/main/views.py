from django.shortcuts import render, redirect
from .logic.ai import characterGenerate, storyGenerate, locationGenerate, storylineGenerate, sceneGenerate, addSceneGenerate, splitSceneGenerate, deleteSceneGenerate, draftChat, personaChat, locationChat, sceneChat, reflectionChat, reflectionGenerate
import logging
import json
from datetime import datetime
from pathlib import Path
logger = logging.getLogger(__name__)
from django.urls import reverse
from django.http import JsonResponse
import time
from django.views.decorators.http import require_POST

from datetime import datetime

@require_POST
def set_participant(request):
    data = json.loads(request.body)
    pid = data.get('participant_id')
    if pid and isinstance(pid, int) and pid > 0:
        request.session['participant_id'] = pid
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False}, status=400)

def save_interaction_log(user_input, output_data, images, action_type, participant_id=None):
    log_dir = Path("user_logs")
    log_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().isoformat()
    log_entry = {
        'timestamp': timestamp,
        'participant_id': participant_id,   # ← NEW
        'action_type': action_type,
        'user_input': user_input,
        'output_data': output_data,
        'images': images
    }

    log_file = log_dir / f"interaction_{timestamp.replace(':', '-')}.json"
    with open(log_file, 'w') as f:
        json.dump(log_entry, f, indent=2)

    logger.info(f"Saved interaction log: {log_file}")

def participant(request):
    return render(request, 'main/participant.html')

def idea(request):
    if request.method == 'POST':
        challenges   = request.POST.get('challenges', '').strip()
        moments    = request.POST.get('moments', '').strip()
        mainCharacter = request.POST.get('mainCharacter', '').strip()

        full_story = storyGenerate(challenges, moments, mainCharacter)

        request.session['story'] = full_story
        request.session.modified = True
        save_interaction_log(
            user_input={'challenges': challenges, 'moments': moments, 'mainCharacter': mainCharacter},
            output_data=full_story,
            images=[s.get('image_path') for s in full_story.get('scenes', [])],
            action_type='idea_generate',
            participant_id=request.session.get('participant_id')
        )
        return redirect('video')
    
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
            save_interaction_log(
                user_input=feedback,
                output_data=updated_story,
                images=[s.get('image_path') for s in updated_story.get('scenes', [])],
                action_type='storyline_regenerate',
                participant_id=request.session.get('participant_id')
            )
            request.session['story'] = updated_story
            request.session.modified = True
            story = updated_story
            logger.warning(f"Storyline regenerated with full story update")

        elif action == 'chat':
            history = json.loads(request.POST.get('history', '[]'))
            reply = draftChat(story, history)
            return JsonResponse({'reply': reply})

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
        },
        'story_data': story
    })

def personas(request):
    story_data = request.session.get('story', {})
    
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'chat':
            persona_id = int(request.POST.get('persona_id'))
            history = json.loads(request.POST.get('history', '[]'))
            reply = personaChat(story_data, persona_id, history)
            return JsonResponse({'reply': reply})

        elif action == 'regenerate':
            persona_id = int(request.POST.get('persona_id'))
            feedback = request.POST.get('feedback')
            updated_story = characterGenerate(story_data, persona_id, feedback)
            save_interaction_log(
                user_input=feedback,
                output_data=updated_story,
                images=[s.get('image_path') for s in updated_story.get('scenes', [])],
                action_type='persona_regenerate',
                participant_id=request.session.get('participant_id')
            )
            request.session['story'] = updated_story
            request.session.modified = True
            story_data = updated_story
            return redirect(f"{reverse('personas')}?slide={persona_id}")

    # Pre-process personas to add preview images
    personas = story_data.get('persona_description', [])
    scenes = story_data.get('scenes', [])
    
    for persona in personas:
        persona['preview_image'] = None
        persona['preview_scene_id'] = None
        for scene in scenes:
            if persona['name'] in scene.get('characters', []):
                persona['preview_image'] = scene.get('image_path')
                persona['preview_scene_id'] = scene.get('id')
                break

    return render(request, 'main/personas.html', {
        'persona_description': personas,
        'scenes': scenes,
    })

def locations(request):
    story_data = request.session.get('story', {})
    
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'chat':
            location_id = int(request.POST.get('location_id'))
            history = json.loads(request.POST.get('history', '[]'))
            reply = locationChat(story_data, location_id, history)
            return JsonResponse({'reply': reply})

        elif action == 'regenerate':
            location_id = int(request.POST.get('location_id'))
            feedback = request.POST.get('feedback')
            updated_story = locationGenerate(story_data, location_id, feedback)
            save_interaction_log(
                user_input=feedback,
                output_data=updated_story,
                images=[s.get('image_path') for s in updated_story.get('scenes', [])],
                action_type='location_regenerate',
                participant_id=request.session.get('participant_id')
            )
            request.session['story'] = updated_story
            request.session.modified = True
            story_data = updated_story
            return redirect(f"{reverse('locations')}?slide={location_id}")
    
    # Pre-process locations to add preview images
    locations = story_data.get('setting_description', [])
    scenes = story_data.get('scenes', [])
    
    for location in locations:
        location['preview_image'] = None
        location['preview_scene_id'] = None
        for scene in scenes:
            if location['name'] == scene.get('location'):
                location['preview_image'] = scene.get('image_path')
                location['preview_scene_id'] = scene.get('id')
                break
    
    return render(request, 'main/locations.html', {
        'setting_description': locations,
        'scenes': scenes,
    })

def scene(request):
    story_data = request.session.get('story', {})
    
    if request.method == 'POST':
        action   = request.POST.get('action')
        scene_id = int(request.POST.get('scene_id'))

        if action == 'chat':
            history = json.loads(request.POST.get('history', '[]'))
            reply = sceneChat(story_data, scene_id, history)
            return JsonResponse({'reply': reply})

        elif action == 'regenerate_scene':
            feedback = request.POST.get('feedback')
            updated_story = sceneGenerate(story_data, scene_id, feedback)
            save_interaction_log(
                user_input=feedback,
                output_data=updated_story,
                images=[s.get('image_path') for s in updated_story.get('scenes', [])],
                action_type='scene_regenerate',
                participant_id=request.session.get('participant_id')
            )
            request.session['story'] = updated_story
            request.session.modified = True
            story_data = updated_story
            logger.warning(f"Scene {scene_id} updated via sceneGenerate")
            return redirect(f"{reverse('scene')}?slide={scene_id}")
    
    return render(request, 'main/scene.html', {
        'scenes': story_data.get('scenes', []),
        'story_data': story_data
    })

def video(request):
    story_data = request.session.get('story', {})
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'delete':
            scene_id = int(request.POST.get('scene_id'))
            updated_story = deleteSceneGenerate(story_data, scene_id)
            save_interaction_log(
                user_input=f"Delete scene {scene_id}",
                output_data=updated_story,
                images=[s.get('image_path') for s in updated_story.get('scenes', [])],
                action_type='scene_delete',
                participant_id=request.session.get('participant_id')
            )
            request.session['story'] = updated_story
            request.session.modified = True
            logger.info(f"Scene {scene_id} deleted")
            return redirect('video')
        
        elif action == 'add':
            after_scene_id = int(request.POST.get('after_scene_id'))
            updated_story = addSceneGenerate(story_data, after_scene_id)
            save_interaction_log(
                user_input=f"Add scene after scene {after_scene_id}",
                output_data=updated_story,
                images=[s.get('image_path') for s in updated_story.get('scenes', [])],
                action_type='scene_add',
                participant_id=request.session.get('participant_id')
            )
            request.session['story'] = updated_story
            request.session.modified = True
            logger.info(f"Scene added after scene {after_scene_id}")
            return redirect('video')
        
        elif action == 'split':
            scene_id = int(request.POST.get('scene_id'))
            updated_story = splitSceneGenerate(story_data, scene_id)
            save_interaction_log(
                user_input=f"Split scene {scene_id}",
                output_data=updated_story,
                images=[s.get('image_path') for s in updated_story.get('scenes', [])],
                action_type='scene_split',
                participant_id=request.session.get('participant_id')
            )
            request.session['story'] = updated_story
            request.session.modified = True
            logger.info(f"Scene {scene_id} split into two scenes")
            return redirect('video')
    
    return render(request, 'main/video.html', {
        'scenes': story_data.get('scenes', []),
        'story_data': story_data
    })

def reflection(request):
    story_data = request.session.get('story', {})
 
    if not story_data:
        return redirect('idea')
 
    if request.method == 'POST' and request.POST.get('action') == 'chat':
        try:
            history = json.loads(request.POST.get('history', '[]'))
            result  = reflectionChat(story_data, history)
            return JsonResponse(result)
        except Exception as e:
            logger.error(f'reflectionChat error: {e}')
            return JsonResponse({
                'question': 'Something went wrong. Please try again.',
                'stage':    1,
                'options':  [],
                'complete': False
            }, status=500)
 
    if request.method == 'POST' and request.POST.get('action') == 'regenerate':
        feedback = request.POST.get('feedback', '')
        try:
            updated = reflectionGenerate(story_data, feedback)
            save_interaction_log(
                user_input=feedback,
                output_data=updated,
                images=[s.get('image_path') for s in updated.get('scenes', [])],
                action_type='reflection_regenerate',
                participant_id=request.session.get('participant_id')
            )
            story_data.update(updated)
            request.session['story'] = story_data
            request.session.modified = True
            return redirect('video')
        except Exception as e:
            logger.error(f'reflectionGenerate error: {e}')
            return render(request, 'main/reflection.html', {
                'draft':      story_data,
                'story_data': story_data,
                'error':      'Something went wrong regenerating the story. Please try again.',
            })
 
    return render(request, 'main/reflection.html', {
        'draft':      story_data,
        'story_data': story_data,
    })