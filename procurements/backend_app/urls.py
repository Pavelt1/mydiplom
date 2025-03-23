from django.urls import path
from . import views

urlpatterns = [
    path('api/user/login/', views.CustomAuthToken.as_view(), name='login'),
    path('api/user/register/', views.UserRegistration.as_view(), name='register'),
    
    path('api/products/', views.ProductListView.as_view(), name='product-list'),
    path('api/products/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    
    path('api/cart/', views.CartView.as_view(), name='cart'),
    path('api/cart/<int:product_id>/', views.CartView.as_view(), name='cart-item'),
    
    path('api/user/contacts/', views.ContactView.as_view(), name='contacts'),
    
    path('api/orders/confirm/', views.OrderConfirmView.as_view(), name='order-confirm'),
    path('api/orders/', views.OrderListView.as_view(), name='order-list'),
    path('api/orders/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('api/orders/<int:pk>/status/', views.OrderStatusView.as_view(), name='order-status'),

    path('partner/update/', views.PartnerUpdate.as_view(), name='partner-update'),
]