# views.py
import requests
import gradio as gr
from django.shortcuts import render
from django.shortcuts import redirect
from fastapi import FastAPI
from django.http import HttpResponse
from django.core.handlers.asgi import ASGIHandler
from model.RAG.retrieve_model import Retrievemodel
INSTANCE = Retrievemodel()
# from app import start_gradio
import threading


def grodio_chat_view(request):
    # thread = threading.Thread(target=start_gradio)
    # thread.daemon = True
    # thread.start()
    return render(request, 'chat.html')

