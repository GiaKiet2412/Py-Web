from django.contrib import admin
from .models import Admin, Customer, Products, Order, OrderDetail, CartItem

class AdminAdmin(admin.ModelAdmin):
    list_display = ('username',)  # Chỉ hiển thị username
    search_fields = ('username',)  # Tìm kiếm theo username

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'email')  # Hiển thị tên và email
    search_fields = ('name', 'email')  # Tìm kiếm theo tên và email

class ProductsAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'brand', 'type')  # Hiển thị các trường chính
    search_fields = ('name', 'description', 'brand', 'type')  # Tìm kiếm theo các trường
    list_filter = ('brand', 'type')  # Lọc theo thương hiệu và loại

class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_date', 'total_price', 'status', 'customer_id')  # Hiển thị thông tin đơn hàng
    search_fields = ('customer_id__name', 'status')  # Tìm kiếm theo tên khách hàng và trạng thái
    list_filter = ('status',)  # Lọc theo trạng thái

class OrderDetailAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'product_id', 'quantity', 'price')  # Hiển thị thông tin chi tiết đơn hàng
    search_fields = ('order_id__id', 'product_id__name')  # Tìm kiếm theo ID đơn hàng và tên sản phẩm

class CartItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'total_price')  # Hiển thị thông tin giỏ hàng
    search_fields = ('product__name',)  # Tìm kiếm theo tên sản phẩm

# Đăng ký các mô hình với admin
admin.site.register(Admin, AdminAdmin)
admin.site.register(Customer, CustomerAdmin)
admin.site.register(Products, ProductsAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderDetail, OrderDetailAdmin)
admin.site.register(CartItem, CartItemAdmin)