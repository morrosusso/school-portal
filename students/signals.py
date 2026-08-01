"""
students/signals.py

The heart of the "automatic ID on acceptance" requirement.

We hook into Application's pre_save to detect a status change into
ACCEPTED, then create (or reuse) the linked Student record with a
freshly generated student_id, and auto-create a login account for
the student so they can access the portal immediately.
"""

from django.db import transaction
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone

from .models import Application, Student

User = get_user_model()


@receiver(pre_save, sender=Application)
def create_student_on_acceptance(sender, instance: Application, **kwargs):
    if not instance.pk:
        return  # brand new application, nothing to compare against yet

    previous = Application.objects.filter(pk=instance.pk).first()
    if not previous:
        return

    just_got_accepted = previous.status != Application.Status.ACCEPTED and instance.status == Application.Status.ACCEPTED
    if not just_got_accepted:
        return

    with transaction.atomic():
        # Lock the Student table's id sequence logic against races
        # from two applications being accepted at the same instant.
        Student.objects.select_for_update().filter(pk__isnull=False)

        if hasattr(instance, "student_record"):
            return  # already has one, avoid duplicates

        student_id = Student.generate_student_id()

        # If the applicant signed up for their own account (the normal
        # path: signup -> complete application -> track status), reuse
        # that SAME account and just convert it into their official
        # student login -- username and password both become the new
        # Student ID, and the role flips from APPLICANT to STUDENT.
        # This avoids ending up with two separate logins for one person.
        #
        # If there's no linked applicant account (e.g. an application
        # entered directly by staff in /admin/ on someone's behalf),
        # fall back to creating a brand new login as before.
        if instance.user_id:
            user = instance.user
            user.username = student_id.lower()
            user.set_password(student_id)
            user.role = "STUDENT"
            user.first_name = instance.first_name
            user.last_name = instance.last_name
            user.save()
        else:
            user = User.objects.create_user(
                username=student_id.lower(),
                password=student_id,
                first_name=instance.first_name,
                last_name=instance.last_name,
                role="STUDENT",
                email=instance.guardian_email or "",
            )

        Student.objects.create(
            application=instance,
            student_id=student_id,
            user=user,
            first_name=instance.first_name,
            last_name=instance.last_name,
            date_of_birth=instance.date_of_birth,
            gender=instance.gender,
            guardian_name=instance.guardian_name,
            guardian_phone=instance.guardian_phone,
            address=instance.address,
            passport_photo=instance.passport_photo,
            current_class=Student.auto_arrange_class(instance.applying_for_grade, instance.applying_for_track),
        )

        instance.reviewed_on = timezone.now()
