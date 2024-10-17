from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, CartItem
from django.contrib.auth.decorators import login_required

fake_products = [
    {'id': 1, 'name': 'Laptop A', 'price': 15000000, 'image_url': './static/image/49310_laptop_asus_gaming_vivobook_k3605zc_rp564w__intel_core_i5_12500h__16gb__512gb_.jpg'},
    {'id': 2, 'name': 'PC B', 'price': 12000000, 'image_url': './static/image/49364_laptop_lenovo_yoga_pro_7_14imh9_83e2005dvn__2_.jpg'},
    {'id': 3, 'name': 'Phụ kiện C', 'price': 500000, 'image_url': '/static/img/accessory_c.jpg'}
]
def get_fake_cart_items():
    return [
        {'product': fake_products[0], 'quantity': 1, 'total_price': fake_products[0]['price']},
        {'product': fake_products[1], 'quantity': 2, 'total_price': fake_products[1]['price'] * 2}
    ]
# VIEW TRANG CHỦ
def home(request):
    return render(request, 'shop/home.html')

#VIEW LOGIN
def login_view(request):
    return render(request, 'shop/login.html')

#VIEW REGISTER
def register_view(request):
    return render(request, 'shop/register.html')

#VIEW PRODUCTS
def products_view(request):
    return render(request, 'shop/products.html')

# VIEW CHI TIẾT SẢN PHẨM
def product_detail(request, id=None):
    # Dữ liệu sản phẩm mẫu
    product = {
        'name': 'Laptop Gaming Gigabyte G5',
        'price': 19290000,
        'description': 'Laptop mạnh mẽ với hiệu năng vượt trội cho game thủ.',
        'image': 'media/products/laptop1.jpg',  # Đường dẫn tạm thời
    }

    return render(request, 'shop/product_detail.html', {'product': product})

# VIEW GIỎ HÀNG
def cart_view(request):
    cart_items = get_fake_cart_items()
    total_price = sum(item['total_price'] for item in cart_items)
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

#@login_required
def pay_view(request):
    cart_items = get_fake_cart_items()
    total_price = sum(item['total_price'] for item in cart_items)
    return render(request, 'shop/pay.html', {'cart_items': cart_items, 'total_price': total_price})

# Xử lý thanh toán (yêu cầu đăng nhập)
#@login_required
def process_payment(request):
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        # Xử lý logic thanh toán ở đây (dữ liệu giả lập)
        return redirect('success_page')  # Chuyển hướng đến trang thành công
    return redirect('checkout')