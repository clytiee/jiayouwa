from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from .models import ContactMessage


@login_required
def contact_create(request):
    """提交联系消息"""
    if request.method == 'POST':
        msg_type = request.POST.get('type', 'other')
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        contact_info = request.POST.get('contact', '').strip()
        
        if not title or not content:
            messages.error(request, '请填写完整信息')
            return render(request, 'contact/contact.html')
        
        message = ContactMessage.objects.create(
            user=request.user,
            type=msg_type,
            title=title,
            content=content,
            contact=contact_info,
        )
        
        # 发送通知给管理员
        from notifications.models import Notification
        from users.models import User
        
        admin = User.objects.filter(is_superuser=True).first()
        if admin:
            Notification.objects.create(
                recipient=admin,
                sender=request.user,
                title=f'📝 新消息：{title[:30]}',
                content=f'用户 {request.user.username} 发来消息：\n{content[:200]}',
                message_type='system',
            )
        
        messages.success(request, '✅ 消息已发送，感谢你的联系！')
        return redirect('contact:history')
    
    return render(request, 'contact/contact.html')


@login_required
def contact_history(request):
    """我的联系记录"""
    contact_messages = ContactMessage.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(contact_messages, 20)
    page = request.GET.get('page', 1)
    contact_messages_page = paginator.get_page(page)
    
    return render(request, 'contact/history.html', {'contact_messages': contact_messages_page})