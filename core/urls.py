from django.urls import path
from . import views

urlpatterns = [
    # Public browsing & items
    path('', views.home_view, name='home'),
    path('item/<int:pk>/', views.item_detail_view, name='item_detail'),
    path('report/', views.report_item_view, name='report_item'),
    path('item/<int:pk>/claim/', views.claim_item_view, name='claim_item'),
    
    # Student portal
    path('my-items/', views.my_items_view, name='my_items'),
    
    # Custom Administrator Dashboard
    path('dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('dashboard/claim/<int:claim_id>/<str:action>/', views.admin_claim_action_view, name='admin_claim_action'),
    path('dashboard/item/<int:item_id>/<str:action>/', views.admin_item_action_view, name='admin_item_action'),
    
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
