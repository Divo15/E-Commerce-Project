from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    fields = ('product', 'product_name', 'size', 'unit_price', 'quantity', 'subtotal')
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'shipping_name', 'shipping_email', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('shipping_name', 'shipping_email', 'shipping_phone', 'shipping_postal_code')
    ordering = ('-created_at',)
    readonly_fields = tuple(field.name for field in Order._meta.fields)
    inlines = (OrderItemInline,)
    fieldsets = (
        ('Order', {'fields': ('id', 'user', 'cart', 'status', 'total_amount', 'created_at')}),
        ('Shipping contact', {'fields': ('shipping_name', 'shipping_email', 'shipping_phone')}),
        ('Delivery address', {'fields': (
            'shipping_address_line1', 'shipping_address_line2', 'shipping_city',
            'shipping_state', 'shipping_postal_code', 'shipping_country',
            'shipping_landmark', 'shipping_instructions',
        )}),
        ('Payment references', {'fields': (
            'stripe_checkout_session_id', 'stripe_payment_intent_id', 'paid_at',
        )}),
    )

    def has_add_permission(self, request):
        return False
