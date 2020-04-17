import uptane.services.timeserver as timeserver
from django.http import JsonResponse,HttpResponse,HttpResponseBadRequest
from django.conf import settings
from django.template import loader
# Create your views here.
def index(request):
    template = loader.get_template('index.html')
    f=open(settings.README_PATH,'rb')
    content=f.read().decode("utf-8") 
    # content.replace('\\r\\n','\\n')
    context = {
        'content': content,
    }
    return HttpResponse(template.render(context, request))

def get_signed_time(request):
    if request.method!='GET':
        return HttpResponseBadRequest()
    else:
        try:
            nonces=request.GET['nonces']
            nonces_list=list(map(int,nonces.split(',')))
            siged=timeserver.get_signed_time(nonces_list)
            # return reponse
            return JsonResponse(siged)
        except Exception as e:
            return HttpResponseBadRequest()
