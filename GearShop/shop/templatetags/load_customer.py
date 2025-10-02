from django import template
from ..models import Customer

register = template.Library()

@register.filter
def load_customer(customer_id):
    try:
        return Customer.objects.get(id=customer_id)
    except Customer.DoesNotExist:
        return None