from django.db.models import Sum

from .models import CartItem
from .services import get_cart


def counter(request):
    """Count active units without creating a session on page views."""
    if request.path.startswith('/admin/'):
        return {'cart_count': 0}
    cart = get_cart(request)
    if cart is None:
        return {'cart_count': 0}
    cart_count = CartItem.objects.filter(
        cart=cart,
        is_active=True,
    ).aggregate(total=Sum('quantity'))['total'] or 0
    return {'cart_count': cart_count}
