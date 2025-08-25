from django.urls import path
from . import views
from .services.box_webhook_handler import handle_box_webhook
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('', views.index, name='index'), # Maps the root URL of the app to the index view
    path('accounts/', views.accounts, name='accounts'),
    path('profile/', views.profile, name='profile'),
    path('documents/', views.documents, name='documents'),
    path('products/', views.products, name='products'),
    path('register/', views.register, name='register'),
    path('support/', views.support, name='support'),
    path('logout/', views.logout_view, name='logout'),  # Custom logout view
    path('wealth-onboarding/', views.wealth_onboarding, name='wealth_onboarding'),  # Wealth onboarding page
    path('document-upload/', views.document_upload, name='document_upload'),  # Document upload page
    path('submission-complete/', views.submission_complete, name='submission_complete'),  # Submission completion page
    path('financial-plan-preview/', views.financial_plan_preview, name='financial_plan_preview'),  # Financial plan preview page
    path('test-horizon-plan/', views.test_horizon_plan, name='test_horizon_plan'),  # Test horizon plan creation
    path('financial-analysis/', views.financial_analysis_view, name='financial_analysis'), # Financial analysis page
    
    # Box API endpoints
    path('api/box/client-folder/', views.box_client_folder, name='box_client_folder'),
    path('api/box/onboarding-folder/', views.box_onboarding_folder, name='box_onboarding_folder'),
    path('api/box/explorer-token/', views.box_explorer_token, name='box_explorer_token'),
    path('api/box/metadata-config/', views.box_metadata_config, name='box_metadata_config'),
    path('api/box/preview-token/', views.get_box_preview_token, name='preview_token'),
    path('api/box/process-document/', views.process_document_metadata, name='process_document_metadata'),
    path('api/box/process-documents-batch/', views.process_documents_metadata_batch, name='process_documents_metadata_batch'),
    path('api/box/process-address-validation/', views.process_address_validation_metadata, name='process_address_validation_metadata'),
    path('api/box/ensure-template/', views.ensure_metadata_template, name='ensure_metadata_template'),
    path('api/box/get-metadata/', views.get_file_metadata, name='get_file_metadata'),
    path('api/box/check-uploads/', views.check_uploaded_files, name='check_uploads'),
    path('api/box/template-details/', views.get_metadata_template_details, name='get_metadata_template_details'),
    path('api/box/generate-financial-summary/', views.generate_financial_summary, name='generate_financial_summary'),
    path('api/box/create-horizon-plan/', views.create_horizon_plan, name='create_horizon_plan'),
    path('api/box/plan-preview-token/', views.get_plan_preview_token, name='get_plan_preview_token'),
    path('api/box/reset-demo/', views.reset_demo, name='reset_demo'),
    path('api/box/direct-file-url/', views.direct_file_url, name='direct_file_url'),
    path('api/box/test-metadata-query/', views.test_metadata_query, name='test_metadata_query'),
    path('api/address-mismatches/', views.get_address_mismatches, name='get_address_mismatches'),
    path('api/update-client-address/', views.update_client_address, name='update_client_address'),
    path('api/update-client-address-group/', views.update_client_address_group, name='update_client_address_group'),
    
    # Debug route to test URL routing
    path('api/box/test-metadata/', views.get_file_metadata, name='test_metadata'),
    
    # Box webhook handler
    path('api/box/webhook/', handle_box_webhook, name='box_webhook'),

    # Authentication routes
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
] 