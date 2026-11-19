"""
URL configuration for HealthcareConfig project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
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
from HealthcareProject import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('comptes/', include('django.contrib.auth.urls')),
    path('api/', include('HealthcareProject.api_urls')),
    path('', views.tableau, name='tableau'),
    path('mesures/', views.mesures, name='mesures'),
    path('journal/', views.journal, name='journal'),
    path('commande/<int:pk>/', views.commande, name='commande'),
    path('inventaire/<str:type_element>/', views.liste, name='liste'),
    path('inventaire/<str:type_element>/ajouter/', views.editer, name='ajouter'),
    path('inventaire/<str:type_element>/<int:pk>/', views.fiche, name='fiche'),
    path('inventaire/<str:type_element>/<int:pk>/modifier/', views.editer, name='modifier'),
    path('inventaire/<str:type_element>/<int:pk>/supprimer/', views.supprimer, name='supprimer'),
]
