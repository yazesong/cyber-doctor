from django.shortcuts import render
from django.contrib.auth.decorators import login_required  
from model.RAG.retrieve_model import Retrievemodel
INSTANCE = Retrievemodel()
import threading
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
import os
from django.http import FileResponse, Http404
from django.conf import settings

def upload_and_build( uploaded_file):
    # 先上传文件
    INSTANCE.upload_user_file(uploaded_file)
    # 然后更新知识库
    INSTANCE.build_user_vector_store()



@api_view(['POST'])
def build_knowledge_view(request):
    action = request.data.get('action')

    if action == 'upload':
        uploaded_file = request.FILES.get('file')
        if uploaded_file:
            thread = threading.Thread(target=upload_and_build, args=(uploaded_file,))
            thread.start()
            uploaded_files = INSTANCE.list_uploaded_files()
            return JsonResponse({'success': '知识库文件上传成功！', 'uploaded_files': uploaded_files}, status=200)
        else:
            return JsonResponse({'error': '请上传文件。'}, status=400)

@api_view(['GET'])
def list_uploaded_files(request):
    uploaded_files = INSTANCE.list_uploaded_files()
    # 将文件名字符串转换为对象，带有 `name` 属性
    uploaded_files_with_name = [{'name': file} for file in uploaded_files]
    return JsonResponse({'uploaded_files': uploaded_files_with_name}, status=200)

@api_view(['DELETE'])
def delete_file(request, filename):
    try:
        INSTANCE.delete_uploaded_file(filename)
        uploaded_files = INSTANCE.list_uploaded_files()
        return JsonResponse({'success': f'文件 {filename} 删除成功！', 'uploaded_files': uploaded_files}, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# @api_view(['GET'])
# def view_uploaded_file_view(request, filename):
#     """根据文件名返回用户上传的文件内容"""
#     try:
#         file_content = INSTANCE.view_uploaded_file(filename)
#         if file_content:
#             return JsonResponse({'file_content': file_content}, status=200)
#         else:
#             return JsonResponse({'error': f'文件 {filename} 不存在或无法读取'}, status=404)
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)
    
@api_view(['GET'])
def view_uploaded_file_view(request, filename):
    """根据文件名返回文件用于下载或预览"""

    file_path = INSTANCE.view_uploaded_file(filename)

    if not os.path.exists(file_path):
        raise Http404(f"文件 {filename} 不存在")

    # 自动检测文件的类型
    content_type = ''
    if filename.endswith('.pdf'):
        content_type = 'application/pdf'
    elif filename.endswith('.docx'):
        content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    elif filename.endswith('.txt'):
        content_type = 'text/plain'
    else:
        content_type = 'application/octet-stream'  # 通用文件类型

    return FileResponse(open(file_path, 'rb'), content_type=content_type)