"""uptane_django URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from image.views import repo_targets,repo_metadata
from director.views import director_targets,director_metadata
urlpatterns = [
    path('admin/', admin.site.urls),
    path('get_signed_time/',include('timeserver.urls')),
    path('repo/metadata/<str:filename>',repo_metadata),
    path('repo/targets/<str:filename>',repo_targets),
    path('director/<str:vin>/metadata/<str:filename>',director_metadata),
    path('director/<str:vin>/targets/<str:filename>',director_targets),
]
