from django.db.models import Sum

from .models import CartItem


def counter(request):
    """Count active units without creating a session on page views."""
    session_key = request.session.session_key
    if not session_key or request.path.startswith('/admin/'):
        return {'cart_count': 0}
    cart_count = CartItem.objects.filter(
        cart__cart_id=session_key,
        is_active=True,
    ).aggregate(total=Sum('quantity'))['total'] or 0
    return {'cart_count': cart_count}
