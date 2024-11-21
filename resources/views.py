from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .utility import is_malicious_url
from django.contrib import messages
from .models import Links, Files
def check_url(url):
    if not url:
        return JsonResponse({'error': 'No URL provided'}, status=400)
        
    # Check if the URL is malicious
    is_malicious = is_malicious_url(url)
    if is_malicious:
        return False
    return True


def resources(request):
    links = Links.objects.all()
    documents = Files.objects.all()

    context = {
        'links': links,
        'documents': documents
    }
    
    return HttpResponse("Hi")
    pass


def new_resource_link(request):
    if request.method == 'POST':
        link = request.POST['link']
        course = request.POST['course']
        name = request.POST['name']

        if check_url(link):
            safelink = link

        else:
            return messages.error(request, 'Malicious Link Detected')

        Links.object.create(
            name=name,
            link=safelink,
            course=course
        )
    return HttpResponse("addlink")

def new_resource_file(request):
    if request.method == 'POST':
        document = request.POST['document']
        course = request.POST['course']
        name = request.POST['name']
        description = request.POST['description']

        Files.object.create(
            name=name,
            document=document,
            description=description,
            course=course,
        )    

    return HttpResponse("addfile")