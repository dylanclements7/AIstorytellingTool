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

def scene1(request):
    return render(request, 'main/scene1.html')

def scene2(request):
    return render(request, 'main/scene2.html')

def scene3(request):
    return render(request, 'main/scene3.html')

def scene4(request):
    return render(request, 'main/scene4.html')

def scene5(request):
    return render(request, 'main/scene5.html')

def scene6(request):
    return render(request, 'main/scene6.html')

def video(request):
    return render(request, 'main/video.html')