from django.shortcuts import render, redirect
from .logic.ai import storyOverview, characterGenerate, locationGenerate, sceneGenerate, narrationGenerate
import logging
logger = logging.getLogger(__name__)
def idea(request):
    if request.method == 'POST':
        return redirect("draft")
    return render(request, 'main/idea.html')

def draft(request):
    if request.method == 'POST':
        idea_text = request.POST.get('story_prompt', '')
        overview = storyOverview(idea_text)
        logger.warning(f"Overview generated: {overview}")
        return render(request, 'main/draft.html', {'overview': overview})
    return redirect("idea")

def personas(request):
    return render(request, 'main/personas.html')

def locations(request):
    return render(request, 'main/locations.html')

def scene(request):
    return render(request, 'main/scene.html')

def video(request):
    return render(request, 'main/video.html')


#def viewGeneratePersonas(request):
    #if request.method == 'POST':
        

#def viewGenerateLocations(request):
    #if request.method == 'POST':
        

#def viewGenerateScene(request):
    #if request.method == 'POST':
        


#def viewStoryGenerate(request):
    #if request.method == 'POST':
        
