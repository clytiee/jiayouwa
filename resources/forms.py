from django import forms
from django.conf import settings
from .models import Resource
import re


class ResourceUploadForm(forms.ModelForm):
    """资源发布表单"""
    
    class Meta:
        model = Resource
        fields = ['title', 'description', 'download_url', 'extract_code', 'price']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': '请输入资源标题'
            }),
            'description': forms.Textarea(attrs={
                'class': 'input-field',
                'rows': 4,
                'placeholder': '请详细描述资源内容'
            }),
            'download_url': forms.URLInput(attrs={
                'class': 'input-field',
                'placeholder': 'https://pan.baidu.com/s/xxxxx 或 https://example.com/file.pdf'
            }),
            'extract_code': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': '提取码（如：abcd，留空自动识别）',
                'maxlength': 20,
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
        self.fields['extract_code'].label = '提取码'
        self.fields['extract_code'].help_text = '粘贴链接后自动识别，也可手动填写'
         # 🆕 价格字段不必填（由视图层控制）
        self.fields['price'].required = False
        self.fields['extract_code'].required = False   

    def clean_download_url(self):
        """验证下载链接格式，并自动提取提取码"""
        url = self.cleaned_data.get('download_url')
        if not url:
            return url
        
        # 如果提取码字段为空，尝试从链接中自动提取
        extract_code = self.data.get('extract_code', '').strip()
        if not extract_code:
            extracted = self._extract_code_from_url(url)
            if extracted:
                # 将提取到的码存入 cleaned_data，供 save 使用
                self.cleaned_data['extract_code'] = extracted
        
        return url
    
    def _extract_code_from_url(self, text):
        """
        从链接或文本中提取提取码
        支持格式：
        1. https://pan.baidu.com/s/xxx?pwd=abcd
        2. https://pan.baidu.com/s/xxx 提取码: abcd
        3. 链接: https://pan.baidu.com/s/xxx 提取码: abcd
        4. 纯文本中的 abcd（4-6位字母数字）
        """
        if not text:
            return None
        
        # 格式1: URL参数中的 pwd=xxx
        pwd_match = re.search(r'[?&]pwd=([a-zA-Z0-9]{4,6})', text)
        if pwd_match:
            return pwd_match.group(1).upper()
        
        # 格式2: 提取码: xxxx 或 提取码：xxxx
        code_match = re.search(r'提取码[：:]\s*([a-zA-Z0-9]{4,6})', text)
        if code_match:
            return code_match.group(1).upper()
        
        # 格式3: 链接末尾的 4-6 位字母数字（百度网盘常见）
        # 匹配类似: /s/1abcde? 或 /s/1abcde 结尾
        code_match2 = re.search(r'/s/[a-zA-Z0-9]+\?pwd=([a-zA-Z0-9]{4,6})', text)
        if code_match2:
            return code_match2.group(1).upper()
        
        # 格式4: 单独的4-6位字母数字（谨慎匹配，避免误判）
        # 只在文本中查找看起来像提取码的独立词
        standalone_match = re.search(r'\b([a-zA-Z0-9]{4,6})\b', text)
        if standalone_match:
            code = standalone_match.group(1)
            # 排除常见的非提取码词（如 http, https, www, com 等）
            exclude = {'http', 'https', 'www', 'com', 'cn', 'net', 'org', 'html', 'php', 'asp', 'jsp'}
            if code.lower() not in exclude and not code.isdigit():
                return code.upper()
        
        return None
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        min_price = settings.DEFAULT_SETTINGS.get('oil_price_min', 0)
        max_price = settings.DEFAULT_SETTINGS.get('oil_price_max', 10)
        if price is None:
            return 0
        if price < min_price or price > max_price:
            raise forms.ValidationError(f'价格必须在 {min_price} 到 {max_price} 油滴之间')
        return price
    
    def clean(self):
        """全局校验：收费资源必须有提取码"""
        cleaned_data = super().clean()
        price = cleaned_data.get('price', 0)
        extract_code = cleaned_data.get('extract_code', '').strip()
        
        # 🔒 如果价格 > 0，必须填写提取码字段
        if price > 0 and not extract_code:
            raise forms.ValidationError({
                'extract_code': '收费资源必须填写提取码，确保用户能正常下载'
            })
        
        return cleaned_data

    def clean_download_url(self):
        url = self.cleaned_data.get('download_url')
        if url and not url.startswith(('http://', 'https://')):
            raise forms.ValidationError('请输入有效的链接地址（以 http:// 或 https:// 开头）')
        return url
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.ai_tags_generated = False
        instance.status = 'published'
        
        # 如果提取码从链接中提取到了，但表单中没有，使用提取的值
        if not instance.extract_code and self.cleaned_data.get('extract_code'):
            instance.extract_code = self.cleaned_data['extract_code']
        
        if commit:
            instance.save()
        return instance