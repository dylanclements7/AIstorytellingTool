from django.shortcuts import render, redirect

def idea(request):
    if request.method == 'POST':
        return redirect("draft")
    return render(request, 'main/idea.html')

def draft(request):
    return render(request, 'main/draft.html')

def personas(request):
    return render(request, 'main/personas.html')

def locations(request):
    return render(request, 'main/locations.html')

def scene(request):
    return render(request, 'main/scene.html')

def video(request):
    return render(request, 'main/video.html')
