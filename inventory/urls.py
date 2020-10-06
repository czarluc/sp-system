"""inventory URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
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
from invsys.views import invsys, assembly, planner, warehouse

urlpatterns = [
    path('admin/', admin.site.urls),

    path('logout/', invsys.logoutuser, name='logoutuser'),

    path('', include('invsys.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/signup/', invsys.SignUpView.as_view(), name='signup'),
    path('accounts/signup/warehouse/', warehouse.WarehouseSignUpView.as_view(), name='warehouse_signup'),
    path('accounts/signup/planner/', planner.PlannerSignUpView.as_view(), name='planner_signup'),
    path('accounts/signup/assembly/', assembly.AssemblySignUpView.as_view(), name='assembly_signup'),

]