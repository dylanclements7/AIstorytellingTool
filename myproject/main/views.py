from django.shortcuts import render, redirect
from .logic.ai import storyOverview, editOverview, characterGenerate, storyGenerate, locationGenerate
import logging
logger = logging.getLogger(__name__)
def idea(request):
    if request.method == 'POST':
        return redirect("draft")
    return render(request, 'main/idea.html')

def draft(request):
    story = request.session.get('story', {})
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'regenerate':
            feedback = request.POST.get('feedback')
            current_draft = {
                'storyline': story['storyline'],
                'tones': story['emotional_tones']
            }
            updated_draft = editOverview(current_draft, feedback)
            story['storyline'] = updated_draft['storyline']
            story['emotional_tones'] = updated_draft['emotional_tones']
            request.session['story'] = story
            request.session.modified = True
            logger.warning(f"Overview regenerated: {updated_draft}")
            return render(request, 'main/draft.html', {'draft': updated_draft})
        elif action == 'generate':
            idea_text = request.POST.get('story_prompt', '')
            draft = storyOverview(idea_text)

            request.session['story'] = {
                'storyline': draft['storyline'],
                'persona_description': [],
                'setting_description': [],
                'scenes': [],
                'emotional_tones': draft['emotional_tones']
            }

            logger.warning(f"Overview generated: {draft}")
            return render(request, 'main/draft.html', {'draft': draft})
        elif action == 'next':
            full_story = storyGenerate(story)
            story['storyline'] = full_story['storyline']
            story['persona_description'] = full_story['persona_description']
            story['setting_description'] = full_story['setting_description']
            story['scenes'] = full_story['scenes']
            story['emotional_tones'] = full_story['emotional_tones']
            request.session['story'] = story
            request.session.modified = True
            logger.warning(f"Full story generated: {full_story}")
            return render(request, 'main/personas.html', {'persona_description': story['persona_description']})
    return redirect("idea")

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
            from main.logic.ai import characterGenerate
            
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

# def locations(request):
#     story = request.session.get('story', {})
    
#     if request.method == 'POST':
#         action = request.POST.get('action')
        
#         if action == 'regenerate':
            
#             location_id = int(request.POST.get('location_id'))
#             feedback = request.POST.get('feedback')
            
#             # Regenerate character
#             updated_character = characterGenerate(story, location_id, feedback)
            
#             # Update in session
#             for i, char in enumerate(story['setting_description']):
#                 if char['id'] == location_id:
#                     story['setting_description'][i] = updated_character
#                     break
            
#             request.session['story'] = story
#             request.session.modified = True
    
#     return render(request, 'main/locations.html', {
#         'setting_description': story.get('setting_description', []),
#     })

def locations(request):
    story_data = request.session.get('story', {})
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'regenerate':
            from main.logic.ai import locationGenerate
            
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
    
    return render(request, 'main/scene.html', {
        'scenes': story_data.get('scenes', []),
    })

def video(request):
    story_data = request.session.get('story', {})
    
    return render(request, 'main/video.html', {
        'scenes': story_data.get('scenes', []),
    })