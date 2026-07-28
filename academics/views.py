from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import SchoolClass, TimetableSlot


@login_required
def timetable_view(request):
    """Shows the timetable for the logged-in teacher, or lets any
    staff pick a class to view."""
    school_classes = SchoolClass.objects.all()
    selected_class_id = request.GET.get("class_id")
    slots = None
    if selected_class_id:
        slots = TimetableSlot.objects.filter(school_class_id=selected_class_id)
    elif request.user.is_teacher:
        slots = TimetableSlot.objects.filter(teacher=request.user)
    return render(request, "academics/timetable.html", {
        "school_classes": school_classes, "slots": slots, "selected_class_id": selected_class_id
    })
