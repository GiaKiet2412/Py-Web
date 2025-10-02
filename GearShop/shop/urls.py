from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Session
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('verify_code/', views.verify_code, name='verify_code'),

    # Product
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path('products/asus/', views.asus_products_view, name='asus_products'),
    path('products/rog/', views.rog_products_view, name='rog_products'),
    path('products/tuf/', views.tuf_products_view, name='tuf_products'),
    path('products/vivo/', views.vivo_products_view, name='vivo_products'),
    path('products/acer/', views.acer_products_view, name='acer_products'),
    path('products/ntr/', views.ntr_products_view, name='ntr_products'),
    path('products/hel/', views.hel_products_view, name='hel_products'),
    path('products/asp/', views.asp_products_view, name='asp_products'),
    path('products/lnv/', views.lnv_products_view, name='lnv_products'),
    path('products/lgn/', views.lgn_products_view, name='lgn_products'),
    path('products/loq/', views.loq_products_view, name='loq_products'),
    path('products/thk/', views.thk_products_view, name='thk_products'),
    path('products/msi/', views.msi_products_view, name='msi_products'),
    path('products/ktn/', views.ktn_products_view, name='ktn_products'),
    path('products/thi/', views.thi_products_view, name='thi_products'),
    path('products/cre/', views.cre_products_view, name='cre_products'),
    path('products/pk/', views.pk_products_view, name='pk_products'),
    path('products/hph/', views.hph_products_view, name='hph_products'),
    path('products/mou/', views.mou_products_view, name='mou_products'),
    path('products/key/', views.key_products_view, name='key_products'),

    # Cart
    path('cart/', views.cart_detail, name='cart_detail'),
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update/<int:product_id>/', views.update_cart, name='update_cart'),
    path('clear/', views.clear_cart, name='clear_cart'),

    # Payment
    path('pay/', views.pay_view, name='pay'),
    path('process_payment/', views.process_payment, name='process_payment'),
    path('create_payment_url/', views.create_payment_url, name='create_payment_url'),
    path('vnpay_return/', views.vnpay_return, name='vnpay_return'),
    path('payment/success/', views.payment_success, name='payment_success'),

    # User's Order
    path('order-history/', views.order_history, name='order_history'),
    path('order/<int:order_id>/', views.order_detail, name='order_detail'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),

    # Find
    path('tim-kiem/', views.search_products, name='search_products'),

    # Admin
    path('admin_home/', views.home_ad, name='home_ad'),
    path('admin_login/', views.admin_login, name='admin_login'),
    path('admin_products/', views.admin_products, name='admin_products'),
    path('admin_products/edit/<int:id>/', views.edit_product, name='edit_product'),
    path('admin_products/delete/<int:id>/', views.delete_product, name='delete_product'),
    path('admin_products/add/', views.add_product, name='add_product'),
    path('admin_order_history/', views.admin_order_history, name='admin_order_history'),
    path('admin_order/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('admin_order/confirm/<int:order_id>/', views.confirm_order, name='confirm_order'),
    path('admin_order/cancel/<int:order_id>/', views.cancel_order, name='admin_cancel_order'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)