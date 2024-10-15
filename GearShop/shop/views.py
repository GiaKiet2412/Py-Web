from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, CartItem

# VIEW TRANG CHỦ
def home(request):
    return render(request, 'shop/home.html')

# VIEW CHI TIẾT SẢN PHẨM
def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    return render(request, 'shop/product_detail.html', {'product': product})

# VIEW GIỎ HÀNG
def cart_view(request):
    cart_items = CartItem.objects.all()
    total_price = sum(item.total_price() for item in cart_items)
    return render(request, 'shop/cart.html', {'cart_items': cart_items, 'total_price': total_price})

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = CartItem.objects.get_or_create(product=product)
    if not created:
        cart_item.quantity += 1
    cart_item.save()
    return redirect('cart_view')

def remove_from_cart(request, product_id):
    cart_item = get_object_or_404(CartItem, product_id=product_id)
    cart_item.delete()
    return redirect('cart_view')

def update_cart(request, product_id):
    cart_item = get_object_or_404(CartItem, product_id=product_id)
    new_quantity = int(request.POST.get('quantity'))
    if new_quantity > 0:
        cart_item.quantity = new_quantity
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart_view')