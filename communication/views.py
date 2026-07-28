from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Notice


@login_required
def notice_board(request):
    notices = [n for n in Notice.objects.all() if n.visible_to(request.user)]
    return render(request, "communication/notice_board.html", {"notices": notices})
