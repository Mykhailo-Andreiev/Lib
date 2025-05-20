from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('admin/', admin.site.urls),                         # Панель администратора
    path('', include('catalog.urls')),                       # Пути из приложения catalog
    path('', include('django.contrib.auth.urls')),           # Авторизация/логин/логаут
]

# Подключение обработки медіафайлів (изображений) во время разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

