from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.validators import RegexValidator
import re

User = get_user_model()


class RegisterForm(UserCreationForm):
    """注册表单"""
    
    username = forms.CharField(
        label='用户名',
        max_length=20,
        min_length=4,
        help_text='4-20位字母、数字或下划线，以字母开头',
        widget=forms.TextInput(attrs={'placeholder': '请输入用户名', 'class': 'w-full px-4 py-2 border rounded-lg'})
    )
    
    email = forms.EmailField(
        label='邮箱',
        widget=forms.EmailInput(attrs={'placeholder': '请输入邮箱地址', 'class': 'w-full px-4 py-2 border rounded-lg'})
    )
    
    nickname = forms.CharField(
        label='昵称',
        max_length=12,
        min_length=2,
        help_text='2-12位中英文、数字或下划线',
        widget=forms.TextInput(attrs={'placeholder': '请输入显示昵称', 'class': 'w-full px-4 py-2 border rounded-lg'})
    )
    
    password1 = forms.CharField(
        label='密码',
        min_length=8,
        help_text='至少8位，需包含字母和数字',
        widget=forms.PasswordInput(attrs={'placeholder': '请设置密码', 'class': 'w-full px-4 py-2 border rounded-lg'})
    )
    
    password2 = forms.CharField(
        label='确认密码',
        widget=forms.PasswordInput(attrs={'placeholder': '请再次输入密码', 'class': 'w-full px-4 py-2 border rounded-lg'})
    )
    
    invite_code = forms.CharField(
        label='邀请码',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': '选填，如果有邀请码请填写', 'class': 'w-full px-4 py-2 border rounded-lg'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]{3,19}$', username):
            raise forms.ValidationError('用户名格式不正确，请使用4-20位字母数字或下划线，以字母开头')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('该用户名已被使用')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('该邮箱已被注册')
        return email
    
    def clean_nickname(self):
        nickname = self.cleaned_data.get('nickname')
        if not re.match(r'^[\w\u4e00-\u9fa5]{2,12}$', nickname):
            raise forms.ValidationError('昵称格式不正确')
        return nickname
    
    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
            raise forms.ValidationError('密码必须包含字母和数字')
        return password
    
    def save(self, commit=True):
        user = super().save(commit=False)
        # 使用昵称作为first_name
        user.first_name = self.cleaned_data.get('nickname')
        user.is_active = False  # 需要邮箱验证激活
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    """登录表单"""
    username = forms.CharField(
        label='用户名 / 邮箱',
        widget=forms.TextInput(attrs={'placeholder': '请输入用户名或邮箱', 'class': 'w-full px-4 py-2 border rounded-lg'})
    )
    password = forms.CharField(
        label='密码',
        widget=forms.PasswordInput(attrs={'placeholder': '请输入密码', 'class': 'w-full px-4 py-2 border rounded-lg'})
    )
    remember_me = forms.BooleanField(
        label='记住我',
        required=False,
        initial=False
    )