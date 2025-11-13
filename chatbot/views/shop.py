from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from chatbot import models
import uuid
from datetime import datetime
import jwt
from django.http import HttpResponseRedirect
from django.utils import timezone


def _auth_redirect():
    return redirect(getattr(settings, "AUTH_SERVER_BASE_URL", "/"))


def _require_page_user(request):
    user = getattr(request, "jwt_user", None)
    if user is None:
        return None
    return user


def _require_api_user(request):
    user = getattr(request, "jwt_user", None)
    if user is None:
        return None
    return user


def _api_unauthorized():
    return Response({'message': '请先登录'}, status=status.HTTP_401_UNAUTHORIZED)

# 商品列表页面
def product_list(request):
    """显示所有商品"""
    category_id = request.GET.get('category')
    search_query = request.GET.get('search', '')
    
    products = models.Product.objects.filter(is_active=True)
    
    # 分类筛选
    if category_id:
        products = products.filter(category_id=category_id)
    
    # 搜索功能
    if search_query:
        products = products.filter(name__icontains=search_query)
    
    categories = models.Category.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
        'selected_category': category_id,
        'search_query': search_query,
    }
    return render(request, 'shop/product_list.html', context)

# 商品详情页面
def product_detail(request, product_id):
    """显示商品详情"""
    product = get_object_or_404(models.Product, id=product_id, is_active=True)
    
    context = {
        'product': product,
    }
    return render(request, 'shop/product_detail.html', context)

# 购物车页面
def cart_view(request):
    """显示购物车"""
    user = _require_page_user(request)
    if user is None:
        return _auth_redirect()

    cart, _ = models.Cart.objects.get_or_create(user=user)
    cart_items = cart.items.all()
    total_price = cart.get_total_price()
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'shop/cart.html', context)

# API：添加商品到购物车
@csrf_exempt
@api_view(['POST'])
def add_to_cart(request):
    """添加商品到购物车"""
    user = _require_api_user(request)
    if user is None:
        return _api_unauthorized()
    
    product_id = request.data.get('product_id')
    quantity = int(request.data.get('quantity', 1))
    
    try:
        product = models.Product.objects.get(id=product_id, is_active=True)
        
        # 检查库存
        if product.stock < quantity:
            return Response({'message': '库存不足'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取或创建购物车
        cart, created = models.Cart.objects.get_or_create(user=user)
        
        # 添加或更新购物车项
        cart_item, created = models.CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            if cart_item.quantity > product.stock:
                return Response({'message': '超过库存数量'}, status=status.HTTP_400_BAD_REQUEST)
            cart_item.save()
        
        return Response({
            'message': '已添加到购物车',
            'cart_total': cart.get_total_price()
        }, status=status.HTTP_200_OK)
        
    except models.Product.DoesNotExist:
        return Response({'message': '商品不存在'}, status=status.HTTP_404_NOT_FOUND)

# API：更新购物车商品数量
@csrf_exempt
@api_view(['POST'])
def update_cart_item(request):
    """更新购物车商品数量"""
    user = _require_api_user(request)
    if user is None:
        return _api_unauthorized()
    
    cart_item_id = request.data.get('cart_item_id')
    quantity = int(request.data.get('quantity', 1))
    
    try:
        cart_item = models.CartItem.objects.get(id=cart_item_id, cart__user=user)
        
        if quantity <= 0:
            cart_item.delete()
            return Response({'message': '已删除商品'}, status=status.HTTP_200_OK)
        
        if quantity > cart_item.product.stock:
            return Response({'message': '超过库存数量'}, status=status.HTTP_400_BAD_REQUEST)
        
        cart_item.quantity = quantity
        cart_item.save()
        
        return Response({
            'message': '已更新数量',
            'subtotal': cart_item.get_subtotal(),
            'cart_total': cart_item.cart.get_total_price()
        }, status=status.HTTP_200_OK)
        
    except models.CartItem.DoesNotExist:
        return Response({'message': '购物车项不存在'}, status=status.HTTP_404_NOT_FOUND)

# API：删除购物车商品
@csrf_exempt
@api_view(['POST'])
def remove_from_cart(request):
    """从购物车删除商品"""
    user = _require_api_user(request)
    if user is None:
        return _api_unauthorized()
    
    cart_item_id = request.data.get('cart_item_id')
    
    try:
        cart_item = models.CartItem.objects.get(id=cart_item_id, cart__user=user)
        cart_item.delete()
        
        return Response({'message': '已删除商品'}, status=status.HTTP_200_OK)
    except models.CartItem.DoesNotExist:
        return Response({'message': '购物车项不存在'}, status=status.HTTP_404_NOT_FOUND)

# 订单确认页面
def checkout(request):
    """订单确认页面"""
    user = _require_page_user(request)
    if user is None:
        return _auth_redirect()

    try:
        cart = models.Cart.objects.get(user=user)
    except models.Cart.DoesNotExist:
        return redirect('cart_view')

    cart_items = cart.items.all()
    if not cart_items:
        return redirect('cart_view')

    total_price = cart.get_total_price()

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'shop/checkout.html', context)

# API：创建订单
@csrf_exempt
@api_view(['POST'])
def create_order(request):
    """创建订单"""
    user = _require_api_user(request)
    if user is None:
        return _api_unauthorized()
    
    shipping_address = request.data.get('shipping_address')
    contact_phone = request.data.get('contact_phone')
    
    if not shipping_address or not contact_phone:
        return Response({'message': '请填写完整的收货信息'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            cart = models.Cart.objects.get(user=user)
            cart_items = cart.items.all()
            
            if not cart_items:
                return Response({'message': '购物车为空'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 检查库存
            for item in cart_items:
                if item.product.stock < item.quantity:
                    return Response({
                        'message': f'商品 {item.product.name} 库存不足'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            # 生成订单号
            order_number = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"
            
            # 创建订单
            order = models.Order.objects.create(
                user=user,
                order_number=order_number,
                total_amount=cart.get_total_price(),
                shipping_address=shipping_address,
                contact_phone=contact_phone
            )
            
            # 创建订单项并扣减库存
            for item in cart_items:
                models.OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    quantity=item.quantity,
                    price=item.product.price
                )
                
                # 扣减库存
                item.product.stock -= item.quantity
                item.product.save()
            
            # 清空购物车
            cart_items.delete()
            
            return Response({
                'message': '订单创建成功',
                'order_number': order_number,
                'order_id': order.id
            }, status=status.HTTP_201_CREATED)
            
    except models.Cart.DoesNotExist:
        return Response({'message': '购物车不存在'}, status=status.HTTP_404_NOT_FOUND)

# 订单列表页面
def order_list(request):
    """用户订单列表"""
    user = _require_page_user(request)
    if user is None:
        return _auth_redirect()

    orders = models.Order.objects.filter(user=user)

    context = {
        'orders': orders,
    }
    return render(request, 'shop/order_list.html', context)

# 订单详情页面
def order_detail(request, order_id):
    """订单详情"""
    user = _require_page_user(request)
    if user is None:
        return _auth_redirect()

    order = get_object_or_404(models.Order, id=order_id, user=user)

    context = {
        'order': order,
    }
    return render(request, 'shop/order_detail.html', context)

# API：虚拟支付
@csrf_exempt
@api_view(['POST'])
def pay_order(request):
    """虚拟支付订单"""
    user = _require_api_user(request)
    if user is None:
        return _api_unauthorized()
    
    order_id = request.data.get('order_id')
    
    try:
        order = models.Order.objects.get(id=order_id, user=user)
        
        # 检查订单状态
        if order.status != 'pending':
            return Response({'message': '订单状态不正确，无法支付'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 更新订单状态为已支付
        order.status = 'paid'
        order.save()
        
        return Response({
            'message': '支付成功！',
            'order_status': order.get_status_display()
        }, status=status.HTTP_200_OK)
        
    except models.Order.DoesNotExist:
        return Response({'message': '订单不存在'}, status=status.HTTP_404_NOT_FOUND)

# 简单的登录页面（用于购物系统）
def shop_login(request):
    """购物系统登录页面"""
    return _auth_redirect()

# 登出
def shop_logout(request):
    """登出"""
    response = _auth_redirect()
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response

# 注册页面
def shop_register(request):
    """购物系统注册页面"""
    return _auth_redirect()


@api_view(["GET"])
def cart_data(request):
    """返回当前用户购物车 JSON 数据"""
    user = _require_api_user(request)
    if user is None:
        return _api_unauthorized()

    cart, _ = models.Cart.objects.get_or_create(user=user)
    items = cart.items.select_related("product").all()
    serialized = []
    for item in items:
        product = item.product
        serialized.append(
            {
                "id": item.id,
                "product_id": product.id,
                "name": product.name,
                "price": float(product.price),
                "quantity": item.quantity,
                "subtotal": float(item.get_subtotal()),
                "added_at": item.added_at.isoformat(),
            }
        )

    return Response(
        {
            "total": float(cart.get_total_price()),
            "items": serialized,
        }
    )


@api_view(["GET"])
def orders_data(request):
    """返回当前用户订单 JSON 数据"""
    user = _require_api_user(request)
    if user is None:
        return _api_unauthorized()

    orders = (
        models.Order.objects.filter(user=user)
        .prefetch_related("items__product")
        .order_by("-created_at")
    )

    serialized_orders = []
    for order in orders:
        order_items = []
        for item in order.items.all():
            order_items.append(
                {
                    "product_id": item.product_id,
                    "name": item.product.name if item.product else "",
                    "price": float(item.price),
                    "quantity": item.quantity,
                    "subtotal": float(item.get_subtotal()),
                }
            )
        serialized_orders.append(
            {
                "id": order.id,
                "order_number": order.order_number,
                "status": order.status,
                "status_display": order.get_status_display(),
                "total_amount": float(order.total_amount),
                "created_at": order.created_at.isoformat(),
                "items": order_items,
            }
        )

    return Response({"orders": serialized_orders})


def shop_sso(request):
    """接收 token，验证后写入 HttpOnly Cookie，并跳转到商城首页。

    用法：/chatbot/shop/sso/?token=... [&next=/shop/...]
    """
    token = request.GET.get("token")
    next_path = request.GET.get("next") or None
    if not token:
        return redirect('product_list')

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.PyJWTError:
        # token 无效则回到商城首页
        return redirect('product_list')

    # 写入 HttpOnly Cookie，端口不同仍会携带
    # 计算过期秒数（若 exp 不存在，给一个默认 1 小时）
    now_ts = int(timezone.now().timestamp())
    exp_ts = int(payload.get("exp", now_ts + 3600))
    max_age = max(exp_ts - now_ts, 300)

    if next_path and not next_path.startswith("/"):
        next_path = "/" + next_path
    redirect_to = next_path or "/chatbot/"
    resp = HttpResponseRedirect(redirect_to)
    resp.set_cookie(
        "access_token",
        token,
        max_age=max_age,
        httponly=True,
        samesite="Lax",
        path="/",
        domain=getattr(settings, "SESSION_COOKIE_DOMAIN", None) or None,
        secure=not settings.DEBUG,
    )
    return resp

