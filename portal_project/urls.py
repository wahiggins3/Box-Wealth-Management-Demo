"""
URL configuration for portal_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from core import views as core_views

urlpatterns = [
    # Admin URL
    path('admin/', admin.site.urls),
    
    # Authentication URLs
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', core_views.logout_view, name='logout'),
    path('register/', core_views.register, name='register'),
    
    # Include all core app URLs
    path('', include('core.urls')),
    
    # Main application URLs
    path('accounts/', core_views.accounts, name='accounts'),
    path('documents/', core_views.documents, name='documents'),
    path('profile/', core_views.profile, name='profile'),
    path('products/', core_views.products, name='products'),
    path('support/', core_views.support, name='support'),
    
    # Wealth management onboarding
    path('wealth-onboarding/', core_views.wealth_onboarding, name='wealth_onboarding'),
    path('document-upload/', core_views.document_upload, name='document_upload'),
    
    # Box API integration endpoints
    path('api/box/client-folder/', core_views.box_client_folder, name='box_client_folder'),
    path('api/box/onboarding-folder/', core_views.box_onboarding_folder, name='box_onboarding_folder'),
    path('api/box/explorer-token/', core_views.box_explorer_token, name='box_explorer_token'),
    path('api/box/process-document/', core_views.process_document_metadata, name='process_document_metadata'),
    path('api/box/ensure-template/', core_views.ensure_metadata_template, name='ensure_metadata_template'),
    path('api/box/get-metadata/', core_views.get_file_metadata, name='get_file_metadata'),
    path('api/box/test-metadata/', core_views.get_file_metadata, name='test_metadata'),
    
    # Diagnostic endpoints
    path('api/box/check-uploads/', core_views.check_uploaded_files, name='check_uploaded_files'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
