from django.contrib import admin
from chatbot.models import UserInfo, Category, Product, Cart, CartItem, Order, OrderItem

# 用户管理
@admin.register(UserInfo)
class UserInfoAdmin(admin.ModelAdmin):
    list_display = ['id', 'username']
    search_fields = ['username']

# 商品分类管理
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created_at']
    search_fields = ['name']
    list_filter = ['created_at']

# 商品管理
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'category', 'price', 'stock', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_filter = ['category', 'is_active', 'created_at']
    list_editable = ['price', 'stock', 'is_active']
    ordering = ['-created_at']

# 购物车管理
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created_at']
    search_fields = ['user__username']
    list_filter = ['created_at']

# 购物车项目管理
@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'cart', 'product', 'quantity', 'added_at']
    search_fields = ['product__name', 'cart__user__username']
    list_filter = ['added_at']

# 订单管理
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'order_number', 'user', 'status', 'total_amount', 'created_at']
    search_fields = ['order_number', 'user__username']
    list_filter = ['status', 'created_at']
    list_editable = ['status']
    ordering = ['-created_at']

# 订单项目管理
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'product', 'quantity', 'price']
    search_fields = ['order__order_number', 'product__name']
