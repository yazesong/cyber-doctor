from django.shortcuts import render, redirect
#from model.RAG.retrieve_model import INSTANCE
INSTANCE = None
import threading
from rest_framework.decorators import api_view
from rest_framework.response import Response

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from django.contrib.auth.hashers import check_password
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from app import start_gradio

from chatbot.encrypt import md5
from chatbot import forms
from chatbot import models

# 建议Views分文件存储


# 登录函数
@csrf_exempt
@api_view(['POST'])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    print(username,password)
    # 查找用户
    try:
        user = models.UserInfo.objects.get(username=username)
    except models.UserInfo.DoesNotExist:
        return Response({'message': '用户名或密码错误'}, status=status.HTTP_401_UNAUTHORIZED)

    # 检查密码是否匹配
    if md5(password) == user.password:
        # 用户名和密码匹配成功
        INSTANCE.set_user_id(username)

        # 启动构建用户向量存储的线程
        thread = threading.Thread(target=INSTANCE.build_user_vector_store(), args=(username,))
        thread.start()

        thread_2 = threading.Thread(target=start_gradio)
        thread_2.daemon = True
        thread_2.start()
        
        # 返回成功响应
        return Response({'message': '登录成功'}, status=status.HTTP_200_OK)
    else:
        # 登录失败，返回错误信息
        return Response({'message': '用户名或密码错误'}, status=status.HTTP_401_UNAUTHORIZED)

# 注册函数
@csrf_exempt
@api_view(['POST'])
def register(request):
    data = request.data  # 使用 request.data 获取 JSON 数据
    form = forms.UserForm(data=data)

    # 检查表单是否有效
    if form.is_valid():
        # 检查用户名是否已存在
        if models.UserInfo.objects.filter(username=form.cleaned_data['username']).exists():
            return JsonResponse({'message': '用户名已存在'}, status=status.HTTP_400_BAD_REQUEST)

        # 保存新用户
        form.save()
        return JsonResponse({'message': '注册成功'}, status=status.HTTP_201_CREATED)
    else:
        # 表单无效，返回错误信息
        return JsonResponse({'message': '注册失败', 'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST)

# 选择页面视图
def choice_view(request):
    if request.method == 'POST':
        # 根据用户的选择跳转到不同的页面
        if 'dialogue' in request.POST:
            return redirect('chat_view')  # 重定向到对话页面
        elif 'build_knowledge' in request.POST:
            return redirect('build_knowledge_view')  # 重定向到构建知识库页面

    # 显示选择页面
    return render(request, 'choice.html')

