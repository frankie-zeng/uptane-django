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
def repo_targets(request,filename):
    filepath=os.path.join(settings.IMAGE_REPO, 'targets',filename)
    if not os.path.exists(filepath):
        return HttpResponseNotFound()
    response = FileResponse(open(filepath, 'rb'))
    return response


def repo_metadata(request,filename):
    if filename not in metaname:
        return HttpResponseForbidden()
    filepath=os.path.join(settings.IMAGE_REPO, 'metadata',filename)
    if not os.path.exists(filepath):
        return HttpResponseNotFound()
    response = FileResponse(open(filepath, 'rb'))
    return response
