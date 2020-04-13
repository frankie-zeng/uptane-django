import uptane.services.timeserver as timeserver
from django.http import JsonResponse,HttpResponse,QueryDict

# Create your views here.
def get_signed_time(request):
    try:
        nonces=request.GET['nonces']
        nonces_list=list(map(int,nonces.split(',')))
        siged=timeserver.get_signed_time(nonces_list)
        # return reponse
        return JsonResponse(siged)
    except Exception as e:
        ret=HttpResponse(str(e))
        ret.status_code=500
        return ret
