from django.db import models
from django.utils import timezone


class AccountUser(models.Model):
    """只读映射 authserver.users.models.User（user 表）"""

    uid = models.CharField(max_length=10, primary_key=True)
    account = models.CharField(max_length=20, unique=True)
    nickname = models.CharField(max_length=20, blank=True)
    email = models.CharField(max_length=30, blank=True)
    password = models.CharField(max_length=128)
    wx_id = models.CharField(max_length=30, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField()
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "user"
        managed = False

    def __str__(self) -> str:  # pragma: no cover - admin display
        return self.account

    @property
    def username(self) -> str:
        """兼容旧代码，使用 account 作为 username."""
        return self.account


class UserInfo(models.Model):
    username = models.CharField(verbose_name="用户名", max_length=32)
    password = models.CharField(verbose_name="密码", max_length=64)

# 商品分类模型
class Category(models.Model):
    name = models.CharField(verbose_name="分类名称", max_length=100)
    description = models.TextField(verbose_name="分类描述", blank=True)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    
    class Meta:
        verbose_name = "商品分类"
        verbose_name_plural = "商品分类"
    
    def __str__(self):
        return self.name

# 商品模型
class Product(models.Model):
    name = models.CharField(verbose_name="商品名称", max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, verbose_name="分类", related_name="products")
    description = models.TextField(verbose_name="商品描述")
    price = models.DecimalField(verbose_name="价格", max_digits=10, decimal_places=2)
    stock = models.IntegerField(verbose_name="库存数量", default=0)
    image_url = models.URLField(verbose_name="商品图片", blank=True, max_length=500)
    is_active = models.BooleanField(verbose_name="是否上架", default=True)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)
    
    class Meta:
        verbose_name = "商品"
        verbose_name_plural = "商品"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name

# 购物车模型
class Cart(models.Model):
    user = models.ForeignKey(
        AccountUser,
        on_delete=models.CASCADE,
        verbose_name="用户",
        related_name="cart",
        db_column="user_uid",
        to_field="uid",
    )
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)
    
    class Meta:
        verbose_name = "购物车"
        verbose_name_plural = "购物车"
    
    def __str__(self):
        return f"{self.user.username}的购物车"
    
    def get_total_price(self):
        return sum(item.get_subtotal() for item in self.items.all())

# 购物车项目
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, verbose_name="购物车", related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="商品")
    quantity = models.IntegerField(verbose_name="数量", default=1)
    added_at = models.DateTimeField(verbose_name="添加时间", auto_now_add=True)
    
    class Meta:
        verbose_name = "购物车项目"
        verbose_name_plural = "购物车项目"
        unique_together = ['cart', 'product']
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    def get_subtotal(self):
        return self.product.price * self.quantity

# 订单模型
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', '待支付'),
        ('paid', '已支付'),
        ('shipping', '配送中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    
    user = models.ForeignKey(
        AccountUser,
        on_delete=models.CASCADE,
        verbose_name="用户",
        related_name="orders",
        db_column="user_uid",
        to_field="uid",
    )
    order_number = models.CharField(verbose_name="订单号", max_length=50, unique=True)
    status = models.CharField(verbose_name="订单状态", max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(verbose_name="订单总额", max_digits=10, decimal_places=2)
    shipping_address = models.TextField(verbose_name="收货地址")
    contact_phone = models.CharField(verbose_name="联系电话", max_length=20)
    created_at = models.DateTimeField(verbose_name="创建时间", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="更新时间", auto_now=True)
    
    class Meta:
        verbose_name = "订单"
        verbose_name_plural = "订单"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"订单 {self.order_number}"

# 订单项目
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, verbose_name="订单", related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name="商品")
    quantity = models.IntegerField(verbose_name="数量")
    price = models.DecimalField(verbose_name="单价", max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = "订单项目"
        verbose_name_plural = "订单项目"
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    def get_subtotal(self):
        return self.price * self.quantity
