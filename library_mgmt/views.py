from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Book, BorrowRecord
from accounts.models import Role


@login_required
def catalog(request):
    query = request.GET.get("q", "")
    books = Book.objects.all()
    if query:
        books = books.filter(title__icontains=query)
    return render(request, "library_mgmt/catalog.html", {"books": books, "query": query})


@login_required
def my_borrowed_books(request):
    student = getattr(request.user, "student_profile", None) if request.user.role == Role.STUDENT else None
    records = BorrowRecord.objects.filter(student=student) if student else []
    return render(request, "library_mgmt/my_books.html", {"records": records})
