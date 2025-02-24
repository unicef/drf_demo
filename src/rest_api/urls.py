"""
URL configuration for demo_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path, include
from django.urls import include, path
from rest_framework_nested import routers

from . import api

router = routers.DefaultRouter()
router.register(r'offices', api.OfficeViewSet)
office_router = routers.NestedSimpleRouter(router, r'offices', lookup='office')
office_router.register(r'programs', api.ProgramViewSet, basename='office-program')

program_router = routers.NestedSimpleRouter(office_router, r'programs', lookup='program')
program_router.register(r'plans', api.PlanViewSet, basename='office-program-plan')

plan_router = routers.NestedSimpleRouter(program_router, r'plans', lookup='plan')
plan_router.register(r'records', api.RecordViewSet, basename='office-program-plan-record')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(office_router.urls)),
    path('', include(program_router.urls)),
    path('', include(plan_router.urls)),
    path('admin/', admin.site.urls),
]
