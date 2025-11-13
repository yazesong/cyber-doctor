from django import forms
from django.core.exceptions import ValidationError
from chatbot import models
from chatbot.encrypt import md5

class UserForm(forms.ModelForm):
    class Meta:
        model=models.UserInfo
        fields=["username","password"]
    # 对密码进行md5加密
    def clean_password(self):
        pwd = self.cleaned_data.get("password")
        return md5(pwd)

    # 确认密码是否一致 判断
    ''' 
    def clean_confirm_password(self):
        pwd =self.cleaned_data.get("password")
        confirm =md5(self.cleaned_data.get("confirm_password"))
        if(confirm!=pwd):
            raise ValidationError("前后密码不一致")
        return confirm
    '''
   