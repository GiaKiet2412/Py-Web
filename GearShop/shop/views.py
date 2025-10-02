from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Order, OrderDetail, Customer, Products
from django.contrib.auth.hashers import check_password
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as auth_login
from django.utils import timezone
from django.core.mail import send_mail
import random
from .forms import ProductForm
import hashlib
import hmac
import time
import urllib.parse
from django.http import JsonResponse, HttpResponse
from django.conf import settings
import requests
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def sort_dict(d):
    """Sắp xếp dictionary theo thứ tự bảng chữ cái"""
    return dict(sorted(d.items()))

#Xử lý tạo URL thanh toán VNPay
def create_payment_url(request):
    try:
        amount = request.POST.get('amount')
        bank_code = request.POST.get('bankCode', '')
        language = request.POST.get('language', 'vn')

        if not amount:
            return JsonResponse({'error': 'Thiếu tham số bắt buộc'}, status=400)

        amount = int(amount)
        MAX_AMOUNT = 1000000000
        if amount > MAX_AMOUNT:
            return JsonResponse({'error': 'Số tiền vượt quá giới hạn tối đa'}, status=400)

        vn_pay_amount = amount * 100
        current_time = datetime.now()
        create_date = current_time.strftime('%Y%m%d%H%M%S')
        order_id = timezone.now().strftime('%Y%m%d%H%M%S%f')
        request.session['order_id'] = order_id

        customer_id = request.session.get('customer_id')
        if not customer_id:
            return JsonResponse({'error': 'Không tìm thấy ID khách hàng trong phiên'}, status=400)

        customer = get_object_or_404(Customer, id=customer_id)

        #Địa chỉ giao hàng
        shipping_address = request.POST.get('shipping_address', '')
        payment_method = 'VNPay'  #Phương thức thanh toán

        # Tạo đơn hàng mới
        order = Order.objects.create(
            order_date=timezone.now(),
            total_price=amount,
            status='Đang duyệt',
            customer_id=customer,
            shipping_address=shipping_address,
            payment_method=payment_method,
            txn_ref=order_id  # Lưu vnp_TxnRef vào đây
        )

        # Lưu các chi tiết đơn hàng
        cart = request.session.get('cart', {})
        for product_id, item in cart.items():
            product = get_object_or_404(Products, id=product_id)

            OrderDetail.objects.create(
                quantity=item['quantity'],
                price=item['price'],
                order_id=order,
                product_id=product
            )

            product.stock -= item['quantity']
            product.save()

        ip_addr = request.META.get('REMOTE_ADDR')

        vnp_params = {
            'vnp_Version': '2.1.0',
            'vnp_Command': 'pay',
            'vnp_TmnCode': settings.VNP_TMN_CODE,
            'vnp_Locale': language,
            'vnp_CurrCode': 'VND',
            'vnp_TxnRef': order_id,
            'vnp_OrderInfo': f'Thanh toan cho ma GD: {order_id}',
            'vnp_OrderType': 'other',
            'vnp_Amount': vn_pay_amount,
            'vnp_ReturnUrl': settings.VNP_RETURN_URL,
            'vnp_IpAddr': ip_addr,
            'vnp_CreateDate': create_date
        }

        if bank_code:
            vnp_params['vnp_BankCode'] = bank_code

        vnp_params = sort_dict(vnp_params)
        sign_data = urllib.parse.urlencode(vnp_params, doseq=True)
        secret_key = settings.VNP_HASH_SECRET
        secure_hash = hmac.new(secret_key.encode('utf-8'), sign_data.encode('utf-8'), hashlib.sha512).hexdigest()
        vnp_params['vnp_SecureHash'] = secure_hash

        vnp_url = f"{settings.VNP_URL}?{urllib.parse.urlencode(vnp_params, doseq=True)}"
        return redirect(vnp_url)

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

#Xử lý phản hồi từ VNPay
def vnpay_return(request):
    try:
        vnp_params = request.GET.dict()
        secure_hash = vnp_params.pop('vnp_SecureHash', None)
        sorted_params = sort_dict(vnp_params)
        sign_data = urllib.parse.urlencode(sorted_params, doseq=True)
        secret_key = settings.VNP_HASH_SECRET
        signed = hmac.new(secret_key.encode('utf-8'), sign_data.encode('utf-8'), hashlib.sha512).hexdigest()

        if secure_hash == signed:
            order_id = vnp_params.get('vnp_TxnRef')  #Lấy order_id từ vnp_TxnRef
            amount = int(vnp_params.get('vnp_Amount', '0')) / 100

            # Truy vấn đơn hàng
            order = get_object_or_404(Order, txn_ref=order_id)

            # Cập nhật tình trạng đơn hàng
            response_code = vnp_params.get('vnp_ResponseCode')
            order.status = 'Đã thanh toán' if response_code == '00' else 'Thất bại'
            order.save()

            # Xóa giỏ hàng và thông tin thanh toán
            request.session['cart'] = {}
            request.session['total_price'] = 0

            messages.success(request, f"Thanh toán thành công! Mã đơn hàng: {order_id}, Tổng tiền: {amount} VNĐ")
            return redirect('cart_detail')
        else:
            messages.error(request, 'Chữ ký không hợp lệ.')
            return redirect('cart_detail')

    except Exception as e:
        logger.error(f"Error in vnpay_return: {str(e)}")
        messages.error(request, 'Có lỗi xảy ra trong quá trình xử lý.')
        return redirect('cart_detail')

#Kết quả
def payment_success(request):
    return render(request, 'shop/payment_success.html', {})

#View thanh toán
def pay_view(request):
    cart = request.session.get('cart', {})
    if not isinstance(cart, dict) or not cart:
        return redirect('cart_detail')

    cart_items = []
    total_price = 0

    for product_id, item in cart.items():
        try:
            product = get_object_or_404(Products, id=product_id)
            total_price += item['quantity'] * item['price']
            cart_items.append({
                'product': product,
                'quantity': item['quantity'],
                'price': item['price'],
                'total_price': item['quantity'] * item['price'],
            })
        except KeyError as e:
            print(f"KeyError: {e} - Item: {item}")
            return redirect('cart_detail')

    # Tạo order_id duy nhất
    order_id = timezone.now().strftime('%Y%m%d%H%M%S%f')

    request.session['order_id'] = order_id  #Lưu order_id vào session
    request.session['total_price'] = total_price  #Lưu tổng tiền vào session

    return render(request, 'shop/pay.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'order_id': order_id,
    })

#Thanh toán khi nhận hàng
def process_payment(request):
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        shipping_address = request.POST.get('shipping_address')
        customer_id = request.session.get('customer_id')

        if not customer_id:
            return redirect('login')

        customer = get_object_or_404(Customer, id=customer_id)
        total_price = request.session.get('total_price', 0)

        if total_price <= 0:
            messages.error(request, "Tổng tiền không hợp lệ.")
            return redirect('cart_detail')

        order = Order.objects.create(
            order_date=timezone.now(),
            total_price=total_price,
            status='Đang duyệt',
            customer_id=customer,
            shipping_address=shipping_address,
            payment_method=payment_method
        )

        cart = request.session.get('cart', {})
        for product_id, item in cart.items():
            product = get_object_or_404(Products, id=product_id)

            OrderDetail.objects.create(
                quantity=item['quantity'],
                price=item['price'],
                order_id=order,
                product_id=product
            )

            product.stock -= item['quantity']
            product.save()

        # Xóa giỏ hàng và thông tin thanh toán
        request.session['cart'] = {}
        request.session['total_price'] = 0
        messages.success(request, "Thanh toán thành công!")
        
        return redirect('order_history')

    return redirect('cart_detail')

# Cập nhật giỏ hàng
def cart_detail(request):
    cart = request.session.get('cart', {})
    if not isinstance(cart, dict):
        cart = {}

    cart_items = []
    total_price = 0

    for product_id, item in cart.items():
        try:
            product = get_object_or_404(Products, id=product_id)
            if 'price' in item and 'quantity' in item:
                # Kiểm tra giá trị price
                if item['price'] is None or item['price'] <= 0:
                    print(f"Invalid price for product_id: {product_id}")
                    continue
                total_price = float(item['quantity']) * float(item['price'])
                cart_items.append({
                    'product': product,
                    'quantity': item['quantity'],
                    'price': float(item['price']),
                    'total_price': total_price
                })
            else:
                print(f"Missing 'price' or 'quantity' for product_id: {product_id}")
        except (TypeError, KeyError) as e:
            print(f"KeyError: {e} - Item: {item}")
            continue

    total_price = sum(item['total_price'] for item in cart_items)

    payment_message = request.session.get('payment_message')
    if payment_message:
        del request.session['payment_message']  # Xóa thông báo sau khi lấy

    return render(request, 'shop/cart_detail.html', {
        'cart_items': cart_items,
        'total_price': total_price,
        'payment_message': payment_message,
    })

def add_to_cart(request, product_id):
    product = get_object_or_404(Products, id=product_id)
    cart = request.session.get('cart', {})

    if str(product_id) in cart:
        # Tăng số lượng sản phẩm
        cart[str(product_id)]['quantity'] += 1
    else:
        # Lưu giá trị price khi thêm sản phẩm mới
        cart[str(product_id)] = {
            'quantity': 1,
            'price': float(product.price) if product.price is not None else 0
        }

    request.session['cart'] = cart
    request.session.modified = True

    return redirect('cart_detail')

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})

    # Kiểm tra xem sản phẩm có trong giỏ hàng không, nếu có thì xóa
    product_id = str(product_id)  # Đảm bảo product_id là chuỗi
    if product_id in cart:
        del cart[product_id]
        request.session['cart'] = cart
        request.session.modified = True  # Cập nhật session

    return redirect('cart_detail')

def update_cart(request, product_id):
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart = request.session.get('cart', {})

        if str(product_id) in cart:
            if quantity > 0:
                cart[str(product_id)]['quantity'] = quantity
            else:
                del cart[str(product_id)]  # Xóa sản phẩm nếu số lượng là 0

        request.session['cart'] = cart
    return redirect('cart_detail')

def clear_cart(request):
    """ Xóa tất cả sản phẩm trong giỏ hàng """
    request.session['cart'] = {}
    messages.info(request, "Giỏ hàng đã được xóa.")
    return redirect('cart_detail')

#Front-end
#Trang chủ
def home(request):
    featured_products = Products.objects.order_by('?')[:4]
    return render(request, 'shop/home.html', {'featured_products': featured_products})

#Asus
def asus_products_view(request):
    asus_products = Products.objects.filter(brand='Asus')
    return render(request, 'shop/asus_products.html', {'asus_products': asus_products})
def rog_products_view(request):
    rog_products = Products.objects.filter(type='Rog')
    return render(request, 'shop/rog_products.html', {'rog_products': rog_products})
def tuf_products_view(request):
    tuf_products = Products.objects.filter(type='Tuf')
    return render(request, 'shop/tuf_products.html', {'tuf_products': tuf_products})
def vivo_products_view(request):
    vivo_products = Products.objects.filter(type='Vivobook')
    return render(request, 'shop/vivo_products.html', {'vivo_products': vivo_products})

#Acer
def acer_products_view(request):
    acer_products = Products.objects.filter(brand='Acer')
    return render(request, 'shop/acer_products.html', {'acer_products': acer_products})
def ntr_products_view(request):
    ntr_products = Products.objects.filter(type='Nitro')
    return render(request, 'shop/ntr_products.html', {'ntr_products': ntr_products})
def hel_products_view(request):
    hel_products = Products.objects.filter(type='Helios')
    return render(request, 'shop/hel_products.html', {'hel_products': hel_products})
def asp_products_view(request):
    asp_products = Products.objects.filter(type='Aspire')
    return render(request, 'shop/asp_products.html', {'asp_products': asp_products})

#Lenovo
def lnv_products_view(request):
    lnv_products = Products.objects.filter(brand='Lenovo')
    return render(request, 'shop/lnv_products.html', {'lnv_products': lnv_products})
def lgn_products_view(request):
    lgn_products = Products.objects.filter(type='Legion')
    return render(request, 'shop/lgn_products.html', {'lgn_products': lgn_products})
def loq_products_view(request):
    loq_products = Products.objects.filter(type='Loq')
    return render(request, 'shop/loq_products.html', {'loq_products': loq_products})
def thk_products_view(request):
    thk_products = Products.objects.filter(type='Thinkpad')
    return render(request, 'shop/thk_products.html', {'thk_products': thk_products})

#MSI
def msi_products_view(request):
    msi_products = Products.objects.filter(brand='Msi')
    return render(request, 'shop/msi_products.html', {'msi_products': msi_products})
def ktn_products_view(request):
    ktn_products = Products.objects.filter(type='Katana')
    return render(request, 'shop/ktn_products.html', {'ktn_products': ktn_products})
def thi_products_view(request):
    thi_products = Products.objects.filter(type='Thin')
    return render(request, 'shop/thi_products.html', {'thi_products': thi_products})
def cre_products_view(request):
    cre_products = Products.objects.filter(type='Creator')
    return render(request, 'shop/cre_products.html', {'cre_products': cre_products})

#Phụ kiện
def pk_products_view(request):
    pk_products = Products.objects.filter(brand='Phukien')
    return render(request, 'shop/pk_products.html', {'pk_products': pk_products})
def hph_products_view(request):
    hph_products = Products.objects.filter(type='Tainghe')
    return render(request, 'shop/hph_products.html', {'hph_products': hph_products})
def mou_products_view(request):
    mou_products = Products.objects.filter(type='Chuot')
    return render(request, 'shop/mou_products.html', {'mou_products': mou_products})
def key_products_view(request):
    key_products = Products.objects.filter(type='Banphim')
    return render(request, 'shop/key_products.html', {'key_products': key_products})

#Chi tiết sản phẩm
def product_detail(request, id):
    product = get_object_or_404(Products, id=id)
    related_products = Products.objects.filter(brand=product.brand).exclude(id=id).order_by('?')[:4]

    return render(request, 'shop/product_detail.html', {
        'product': product,
        'related_products': related_products,
    })

#Lịch sử mua hàng (Order)
def order_history(request):
    customer_id = request.session.get('customer_id')
    orders = Order.objects.filter(customer_id=customer_id).order_by('-order_date')

    return render(request, 'shop/order_history.html', {'orders': orders})

def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_details = OrderDetail.objects.filter(order_id=order)

    return render(request, 'shop/order_detail.html', {
        'order': order,
        'order_details': order_details
    })

# Hủy đơn hàng
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.status == 'Đang duyệt':
        # Cập nhật số lượng tồn kho
        order_details = OrderDetail.objects.filter(order_id=order)
        for detail in order_details:
            product = detail.product_id
            product.stock += detail.quantity  #Hoàn số lượng
            product.save()

        order.status = 'Đã hủy'
        order.save()
        messages.success(request, 'Đơn hàng đã được hủy.')
    else:
        messages.error(request, 'Không thể hủy đơn hàng này.')
    return redirect('order_history')

#Back-end
#Đăng ký
def register(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Kiểm tra thông tin
        if not name or not email or not password:
            messages.error(request, 'Vui lòng điền đầy đủ thông tin.')
            return redirect('register')

        # Kiểm tra xem email đã tồn tại chưa
        if Customer.objects.filter(email=email).exists():
            messages.error(request, 'Email này đã được sử dụng.')
            return redirect('register')

        # Tạo mã xác nhận ngẫu nhiên
        verification_code = random.randint(100000, 999999)

        # Gửi email xác nhận
        send_mail(
            'Mã xác nhận đăng ký',
            f'Mã xác nhận của bạn là: {verification_code}',
            'your_email@gmail.com',  # Thay địa chỉ email của bạn
            [email],
            fail_silently=False,
        )

        # Lưu thông tin vào session
        request.session['verification_code'] = verification_code
        request.session['name'] = name
        request.session['email'] = email
        request.session['password'] = password  # Lưu mật khẩu để tạo tài khoản sau

        return redirect('verify_code')  # Chuyển hướng đến trang xác nhận mã

    return render(request, 'shop/register.html')  # Render lại form nếu không phải POST

#Xử lý mã xác nhận
def verify_code(request):
    if request.method == 'POST':
        entered_code = request.POST.get('code')
        verification_code = request.session.get('verification_code')

        if str(entered_code) == str(verification_code):
            # Nếu mã xác nhận đúng, lưu người dùng vào cơ sở dữ liệu
            name = request.session.get('name')
            email = request.session.get('email')
            password = request.session.get('password')  # Lấy mật khẩu từ session

            # Tạo người dùng mới
            customer = Customer(name=name, email=email, password=password)
            customer.save()

            messages.success(request, 'Đăng ký thành công! Bạn có thể đăng nhập ngay bây giờ.')
            return redirect('login')
        else:
            messages.error(request, 'Mã xác nhận không đúng!')

    return render(request, 'shop/verify_code.html')

#Đăng nhập
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            customer = Customer.objects.get(email=email)
            
            if check_password(password, customer.password):
                request.session['customer_id'] = customer.id 
                messages.success(request, 'Đăng nhập thành công!')
                return redirect('home')
            else:
                messages.error(request, 'Mật khẩu không đúng.')
        except Customer.DoesNotExist:
            messages.error(request, 'Email không tồn tại.')
        
        return redirect('login')

    return render(request, 'shop/login.html')

#Đăng xuất
def logout_view(request):
    if 'customer_id' in request.session:
        del request.session['customer_id']
        messages.success(request, 'Đăng xuất thành công!')
    return redirect('home')

#??
def some_view(request):
    customer = None
    if request.session.get('customer_id'):
        customer = get_object_or_404(Customer, id=request.session['customer_id'])

    return render(request, 'shop/some_template.html', {
        'customer': customer,
    })

#Tìm kiếm sản phẩm
def search_products(request):
    query = request.GET.get('tukhoa', '')
    products = Products.objects.filter(name__icontains=query)  # Tìm kiếm sản phẩm theo tên
    return render(request, 'shop/search_results.html', {'products': products, 'query': query})

#ADMIN
#Trang chủ admin
def home_ad(request):
    return render(request, 'admin/home_ad.html')
#Login admin
def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            auth_login(request, user)
            return redirect('home_ad')
        else:
            messages.error(request, 'Tên đăng nhập hoặc mật khẩu không đúng.')
    
    return render(request, 'admin/admin_login.html')

#Quản lí sản phảm
@login_required
def admin_products(request):
    # Lấy tất cả sản phẩm từ cơ sở dữ liệu
    products = Products.objects.all()
    return render(request, 'admin/admin_products.html', {'products': products})

#Sửa sp
@login_required
def edit_product(request, id):
    product = get_object_or_404(Products, id=id)
    if request.method == 'POST':
        product.name = request.POST.get('name')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.stock = request.POST.get('stock')
        product.brand = request.POST.get('brand')
        product.type = request.POST.get('type')
        # Nếu có ảnh mới
        if request.FILES.get('image'):
            product.image = request.FILES.get('image')
        product.save()
        return redirect('admin_products')
    return render(request, 'admin/edit_product.html', {'product': product})

#Xóa sp
@login_required
def delete_product(request, id):
    # Lấy sản phẩm cần xóa
    product = get_object_or_404(Products, id=id)
    
    # Xóa sản phẩm
    product.delete()

    # Thông báo thành công và chuyển hướng về trang quản lý sản phẩm
    messages.success(request, f'Sản phẩm "{product.name}" đã được xóa thành công.')
    return redirect('admin_products')  # Quay lại trang quản lý sản phẩm

#Thêm sp
@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)  # Chú ý sử dụng request.FILES để xử lý file hình ảnh
        if form.is_valid():
            form.save()
            messages.success(request, 'Sản phẩm mới đã được thêm thành công!')
            return redirect('admin_products')  # Quay lại trang quản lý sản phẩm
        else:
            messages.error(request, 'Đã có lỗi xảy ra khi thêm sản phẩm. Vui lòng thử lại.')
    else:
        form = ProductForm()

    return render(request, 'admin/add_product.html', {'form': form})

# Quản lý đơn hàng
@login_required
def admin_order_history(request):
    orders = Order.objects.all()
    return render(request, 'admin/admin_order_history.html', {'orders': orders})

# Chi tiết đơn hàng
@login_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_details = OrderDetail.objects.filter(order_id=order)

    return render(request, 'admin/admin_order_detail.html', {
        'order': order,
        'order_details': order_details
    })

# Xác nhận đơn hàng
@login_required
def confirm_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.status == 'Đang duyệt':
        order.status = 'Đã xác nhận'
        order.save()
        messages.success(request, 'Đơn hàng đã được xác nhận.')
    else:
        messages.error(request, 'Không thể xác nhận đơn hàng này.')
    return redirect('admin_order_history')

# Hủy đơn hàng
@login_required
def admin_cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.status == 'Đang duyệt':
        # Cập nhật số lượng tồn kho
        order_details = OrderDetail.objects.filter(order_id=order)
        for detail in order_details:
            product = detail.product_id  # Lấy sản phẩm
            product.stock += detail.quantity  # Hoàn trả số lượng
            product.save()  # Lưu thay đổi vào cơ sở dữ liệu

        order.status = 'Đã hủy'
        order.save()
        messages.success(request, 'Đơn hàng đã được hủy.')
    else:
        messages.error(request, 'Không thể hủy đơn hàng này.')
    return redirect('admin_order_history')