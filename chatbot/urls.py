from django.urls import path

from chatbot.views import view, chat, knowledge, shop

urlpatterns=[
    # 原有的API端点
    path('api/login/', view.login, name='login'),
    path('api/register/', view.register, name='register'),
    path('upload/', knowledge.build_knowledge_view, name='upload_file'),
    path('files/', knowledge.list_uploaded_files, name='list_files'),
    path('files/<str:filename>/', knowledge.delete_file, name='delete_file'),
    path('view_file/<str:filename>/', knowledge.view_uploaded_file_view, name='view_uploaded_file'),
    
    # 聊天页面（内嵌 Gradio）
    path('chat/', chat.grodio_chat_view, name='chat_view'),

    # 购物系统路由
    path('', shop.product_list, name='product_list'),
    path('shop/login/', shop.shop_login, name='shop_login'),
    path('shop/register/', shop.shop_register, name='shop_register'),
    path('shop/logout/', shop.shop_logout, name='shop_logout'),
    path('shop/products/', shop.product_list, name='product_list'),
    path('shop/products/<int:product_id>/', shop.product_detail, name='product_detail'),
    path('shop/cart/', shop.cart_view, name='cart_view'),
    path('shop/cart/add/', shop.add_to_cart, name='add_to_cart'),
    path('shop/cart/update/', shop.update_cart_item, name='update_cart_item'),
    path('shop/cart/remove/', shop.remove_from_cart, name='remove_from_cart'),
    path('shop/api/cart/', shop.cart_data, name='cart_data'),
    path('shop/checkout/', shop.checkout, name='checkout'),
    path('shop/order/create/', shop.create_order, name='create_order'),
    path('shop/order/pay/', shop.pay_order, name='pay_order'),
    path('shop/api/orders/', shop.orders_data, name='orders_data'),
    path('shop/orders/', shop.order_list, name='order_list'),
    path('shop/orders/<int:order_id>/', shop.order_detail, name='order_detail'),
    path('shop/sso/', shop.shop_sso, name='shop_sso'),
]
