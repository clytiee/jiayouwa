from django import forms
from django.conf import settings
from .models import Resource


class ResourceUploadForm(forms.ModelForm):
    """资源发布表单"""
    
    class Meta:
        model = Resource
        fields = ['title', 'description', 'download_url', 'price']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': '请输入资源标题，如"10分钟搞定一年级退位减法"',
            }),
            'description': forms.Textarea(attrs={
                'class': 'input-field',
                'rows': 4,
                'placeholder': '请详细描述资源内容，帮助其他家长了解这个资源...'
            }),
            'download_url': forms.URLInput(attrs={
                'class': 'input-field',
                'placeholder': '请输入资源的下载链接（如百度网盘链接、网站链接等）',
            }),
            'price': forms.NumberInput(attrs={
                'class': 'input-field',
                'min': 0,
                'max': 10,
                'placeholder': '0-10油滴'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['price'].label = '油滴价格'
        self.fields['price'].help_text = f'建议价格：1-5油滴（系统限制 0-{settings.DEFAULT_SETTINGS.get("oil_price_max", 10)}）'
        # 添加图片数量验证（前端会传递images_data）
        self.fields['title'].required = True
        self.fields['description'].required = True
        self.fields['download_url'].required = True
    
    def clean_price(self):
        """验证价格在范围内"""
        price = self.cleaned_data.get('price')
        min_price = settings.DEFAULT_SETTINGS.get('oil_price_min', 0)
        max_price = settings.DEFAULT_SETTINGS.get('oil_price_max', 10)
        if price is None:
            price = 0
        if price < min_price or price > max_price:
            raise forms.ValidationError(f'价格必须在 {min_price} 到 {max_price} 油滴之间')
        return price
    
    def clean_download_url(self):
        """验证下载链接格式"""
        url = self.cleaned_data.get('download_url')
        if url and not url.startswith(('http://', 'https://')):
            raise forms.ValidationError('请输入有效的链接地址（以 http:// 或 https:// 开头）')
        return url
    
    def save(self, commit=True):
        """保存资源"""
        instance = super().save(commit=False)
        instance.ai_tags_generated = False
        instance.status = 'published'
        
        if commit:
            instance.save()
        return instance