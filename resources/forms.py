from django import forms
from django.conf import settings
from .models import Resource
import re

class TagsInput(forms.TextInput):
    """自定义 tags 输入框，把 list 转成逗号分隔字符串"""
    
    def format_value(self, value):
        """把各种形式的值转为干净的逗号分隔字符串"""
        if value is None:
            return ''
        
        # list：直接 join
        if isinstance(value, list):
            return ', '.join(value) if value else ''
        
        # 字符串：清理引号、方括号
        if isinstance(value, str):
            v = value.strip()
            # 去掉首尾引号
            v = v.strip('"').strip("'")
            # 去掉方括号
            v = v.strip('[').strip(']')
            if not v:
                return ''
            # 分割后逐项清理
            items = [item.strip().strip('"').strip("'") for item in v.split(',')]
            return ', '.join([i for i in items if i])
        
        return ''

class ResourceUploadForm(forms.ModelForm):
    """资源发布表单"""
    
    class Meta:
        model = Resource
        fields = ['title', 'description', 'download_url', 'extract_code', 'price', 'tags']
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
            'tags': TagsInput(attrs={
                'class': 'input-field',
                'placeholder': '输入标签，用逗号分隔，如：数学, 三年级, 思维训练',
                'id': 'id_tags',
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
        # ✅ tags 字段：可选，用逗号分隔的字符串
        self.fields['tags'].required = False
        self.fields['tags'].label = '标签'
        self.fields['tags'].help_text = '用逗号分隔，如：数学, 三年级, 思维训练'
        
        # 编辑时，把 list 转成逗号分隔的字符串
        if self.instance and self.instance.pk:
            instance_tags = self.instance.tags
            # 处理各种可能的值
            if isinstance(instance_tags, list) and instance_tags:
                self.initial['tags'] = ', '.join(instance_tags)
            else:
                self.initial['tags'] = ''
        else:
            self.initial['tags'] = ''

        # ✅ 把 tags 字段改为普通文本输入，避免 JSON 校验
        self.fields['tags'] = forms.CharField(
            required=False,
            label='标签',
            help_text='用逗号分隔，如：数学, 三年级, 思维训练',
            widget=forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': '输入标签，用逗号分隔，如：数学, 三年级, 思维训练',
                'id': 'id_tags',
                'maxlength': '100',
            })
        )

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
    
    def clean_tags(self):
        """把逗号分隔的字符串转为 list"""
        tags = self.cleaned_data.get('tags')
        
        # 如果是 list，直接返回
        if isinstance(tags, list):
            return tags
        
        # 如果是字符串
        if isinstance(tags, str):
            tags = tags.strip()
            # 空字符串返回空列表
            if not tags:
                return []
            # 去掉可能的引号
            tags = tags.strip('"').strip("'")
            tags = tags.replace('，', ',')
            tag_list = [t.strip() for t in tags.split(',') if t.strip()]
            return tag_list[:5]
        
        # 其他情况返回空列表
        return []

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