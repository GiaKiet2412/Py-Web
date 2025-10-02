import hashlib
from datetime import datetime
import urllib.parse

# Thông tin VNPay
merchant_id = 'JFFZU84P'
hash_key = '5E9C6GG4VX6IVXCBYPOWM8B4UB10A7HA'
amount = '40380000'  # Số tiền cần thanh toán (403.800 VND)
order_id = 'ORDER123'
return_url = 'http://yourdomain.com/vnpay_callback/'

# Tạo dữ liệu thanh toán
params = {
    'vnp_Version': '2.0.0',
    'vnp_TmnCode': merchant_id,
    'vnp_Amount': amount,
    'vnp_CurrCode': 'VND',
    'vnp_TxnRef': order_id,
    'vnp_OrderInfo': f'Thanh toán đơn hàng #{order_id}',
    'vnp_ReturnUrl': return_url,
    'vnp_IpAddr': '127.0.0.1',
    'vnp_CreateDate': datetime.now().strftime('%Y%m%d%H%M%S'),
}

# Tạo chữ ký
sorted_params = sorted(params.items())
query_string = '&'.join(['{}={}'.format(k, v) for k, v in sorted_params])
hash_data = query_string + '&key=' + hash_key
vnp_secure_hash = hashlib.sha256(hash_data.encode('utf-8')).hexdigest()
params['vnp_SecureHash'] = vnp_secure_hash

# Tạo URL thanh toán
vnp_payment_url = 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html?' + urllib.parse.urlencode(params)
print(vnp_payment_url)