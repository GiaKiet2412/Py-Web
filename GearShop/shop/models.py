from django.db import models
from django.contrib.auth.hashers import make_password
class Products(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=0)
    stock = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='static/image')
    brand = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    def __str__(self):
        return self.name

    
class Admin(models.Model):
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)

    def __str__(self):
        return self.username

class Customer(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, unique=True)
    password = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Order(models.Model):
    order_date = models.DateField()
    total_price = models.BigIntegerField()
    status = models.CharField(max_length=20)
    customer_id = models.ForeignKey(Customer, on_delete=models.CASCADE)
    shipping_address = models.TextField(null=True, blank=True)
    payment_method = models.CharField(max_length=50, null=True)
    txn_ref = models.CharField(max_length=50, unique=True, null=True)  # Thêm trường này

class OrderDetail(models.Model):
    quantity = models.IntegerField()
    price = models.IntegerField()
    order_id = models.ForeignKey(Order, on_delete=models.CASCADE)
    product_id = models.ForeignKey(Products, on_delete=models.CASCADE)


class CartItem(models.Model):
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def total_price(self):
        return self.product.price * self.quantity