from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path


def healthz(_request):
    return HttpResponse('ok', content_type='text/plain')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('healthz', healthz),
    path('', include('core.urls')),
]

handler404 = 'django.views.defaults.page_not_found'
handler500 = 'django.views.defaults.server_error'
