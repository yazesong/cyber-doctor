from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from chatbot import models
import uuid
from datetime import datetime

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
    # 这里简化处理，从 session 中获取用户名
    username = request.session.get('username')
    if not username:
        return redirect('shop_login')
    
    try:
        user = models.UserInfo.objects.get(username=username)
        cart, created = models.Cart.objects.get_or_create(user=user)
        cart_items = cart.items.all()
        total_price = cart.get_total_price()
    except models.UserInfo.DoesNotExist:
        cart_items = []
        total_price = 0
    
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
    username = request.session.get('username')
    if not username:
        return Response({'message': '请先登录'}, status=status.HTTP_401_UNAUTHORIZED)
    
    product_id = request.data.get('product_id')
    quantity = int(request.data.get('quantity', 1))
    
    try:
        user = models.UserInfo.objects.get(username=username)
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
        
    except models.UserInfo.DoesNotExist:
        return Response({'message': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
    except models.Product.DoesNotExist:
        return Response({'message': '商品不存在'}, status=status.HTTP_404_NOT_FOUND)

# API：更新购物车商品数量
@csrf_exempt
@api_view(['POST'])
def update_cart_item(request):
    """更新购物车商品数量"""
    username = request.session.get('username')
    if not username:
        return Response({'message': '请先登录'}, status=status.HTTP_401_UNAUTHORIZED)
    
    cart_item_id = request.data.get('cart_item_id')
    quantity = int(request.data.get('quantity', 1))
    
    try:
        user = models.UserInfo.objects.get(username=username)
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
    username = request.session.get('username')
    if not username:
        return Response({'message': '请先登录'}, status=status.HTTP_401_UNAUTHORIZED)
    
    cart_item_id = request.data.get('cart_item_id')
    
    try:
        user = models.UserInfo.objects.get(username=username)
        cart_item = models.CartItem.objects.get(id=cart_item_id, cart__user=user)
        cart_item.delete()
        
        return Response({'message': '已删除商品'}, status=status.HTTP_200_OK)
    except models.CartItem.DoesNotExist:
        return Response({'message': '购物车项不存在'}, status=status.HTTP_404_NOT_FOUND)

# 订单确认页面
def checkout(request):
    """订单确认页面"""
    username = request.session.get('username')
    if not username:
        return redirect('shop_login')
    
    try:
        user = models.UserInfo.objects.get(username=username)
        cart = models.Cart.objects.get(user=user)
        cart_items = cart.items.all()
        
        if not cart_items:
            return redirect('cart_view')
        
        total_price = cart.get_total_price()
        
        context = {
            'cart_items': cart_items,
            'total_price': total_price,
        }
        return render(request, 'shop/checkout.html', context)
    except (models.UserInfo.DoesNotExist, models.Cart.DoesNotExist):
        return redirect('cart_view')

# API：创建订单
@csrf_exempt
@api_view(['POST'])
def create_order(request):
    """创建订单"""
    username = request.session.get('username')
    if not username:
        return Response({'message': '请先登录'}, status=status.HTTP_401_UNAUTHORIZED)
    
    shipping_address = request.data.get('shipping_address')
    contact_phone = request.data.get('contact_phone')
    
    if not shipping_address or not contact_phone:
        return Response({'message': '请填写完整的收货信息'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        with transaction.atomic():
            user = models.UserInfo.objects.get(username=username)
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
            
    except models.UserInfo.DoesNotExist:
        return Response({'message': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
    except models.Cart.DoesNotExist:
        return Response({'message': '购物车不存在'}, status=status.HTTP_404_NOT_FOUND)

# 订单列表页面
def order_list(request):
    """用户订单列表"""
    username = request.session.get('username')
    if not username:
        return redirect('shop_login')
    
    try:
        user = models.UserInfo.objects.get(username=username)
        orders = models.Order.objects.filter(user=user)
        
        context = {
            'orders': orders,
        }
        return render(request, 'shop/order_list.html', context)
    except models.UserInfo.DoesNotExist:
        return redirect('shop_login')

# 订单详情页面
def order_detail(request, order_id):
    """订单详情"""
    username = request.session.get('username')
    if not username:
        return redirect('shop_login')
    
    try:
        user = models.UserInfo.objects.get(username=username)
        order = get_object_or_404(models.Order, id=order_id, user=user)
        
        context = {
            'order': order,
        }
        return render(request, 'shop/order_detail.html', context)
    except models.UserInfo.DoesNotExist:
        return redirect('shop_login')

# API：虚拟支付
@csrf_exempt
@api_view(['POST'])
def pay_order(request):
    """虚拟支付订单"""
    username = request.session.get('username')
    if not username:
        return Response({'message': '请先登录'}, status=status.HTTP_401_UNAUTHORIZED)
    
    order_id = request.data.get('order_id')
    
    try:
        user = models.UserInfo.objects.get(username=username)
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
        
    except models.UserInfo.DoesNotExist:
        return Response({'message': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
    except models.Order.DoesNotExist:
        return Response({'message': '订单不存在'}, status=status.HTTP_404_NOT_FOUND)

# 简单的登录页面（用于购物系统）
def shop_login(request):
    """购物系统登录页面"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        try:
            from chatbot.encrypt import md5
            user = models.UserInfo.objects.get(username=username)
            if md5(password) == user.password:
                request.session['username'] = username
                return redirect('product_list')
            else:
                context = {'error': '用户名或密码错误'}
                return render(request, 'shop/login.html', context)
        except models.UserInfo.DoesNotExist:
            context = {'error': '用户名或密码错误'}
            return render(request, 'shop/login.html', context)
    
    return render(request, 'shop/login.html')

# 登出
def shop_logout(request):
    """登出"""
    request.session.flush()
    return redirect('shop_login')

# 注册页面
def shop_register(request):
    """购物系统注册页面"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        # 验证输入
        if not username or not password:
            context = {'error': '用户名和密码不能为空'}
            return render(request, 'shop/register.html', context)
        
        if password != confirm_password:
            context = {'error': '两次输入的密码不一致'}
            return render(request, 'shop/register.html', context)
        
        if len(password) < 6:
            context = {'error': '密码长度不能少于6位'}
            return render(request, 'shop/register.html', context)
        
        # 检查用户名是否已存在
        if models.UserInfo.objects.filter(username=username).exists():
            context = {'error': '用户名已存在，请换一个'}
            return render(request, 'shop/register.html', context)
        
        try:
            from chatbot.encrypt import md5
            # 创建新用户
            models.UserInfo.objects.create(
                username=username,
                password=md5(password)
            )
            # 注册成功，直接登录
            request.session['username'] = username
            context = {'success': '注册成功！即将跳转到首页...'}
            return render(request, 'shop/register.html', context)
        except Exception as e:
            context = {'error': f'注册失败：{str(e)}'}
            return render(request, 'shop/register.html', context)
    
    return render(request, 'shop/register.html')

