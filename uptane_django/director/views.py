from django.shortcuts import render
from django.http import FileResponse,HttpResponseForbidden,HttpResponseNotFound
from django.conf import settings
import os
from uptane_django.basic_auth import logged_in_or_basicauth
# Create your views here.

metaname=[
    'root.json',
    'root.json.gz',
    'snapshot.json',
    'snapshot.json.gz',
    'targets.json',
    'targets.json.gz',
    'timestamp.json',
    'timestamp.json.gz'
]

@logged_in_or_basicauth()
def director_targets(request,vin,filename):
    if vin not in settings.DIRECTOR.vehicle_repositories:
        return HttpResponseNotFound()
    repo = settings.DIRECTOR.vehicle_repositories[vin]
    repo_dir = repo._repository_directory
    filepath=os.path.join(repo_dir, 'targets',filename)
    if not os.path.exists(filepath):
        return HttpResponseNotFound()
    response = FileResponse(open(filepath, 'rb'))
    return response


def director_metadata(request,vin,filename):
    if filename not in metaname:
        return HttpResponseForbidden()
    if vin not in settings.DIRECTOR.vehicle_repositories:
        return HttpResponseNotFound()
    repo = settings.DIRECTOR.vehicle_repositories[vin]
    repo_dir = repo._repository_directory
    filepath=os.path.join(repo_dir, 'metadata',filename)
    if not os.path.exists(filepath):
        return HttpResponseNotFound()
    response = FileResponse(open(filepath, 'rb'))
    return response
