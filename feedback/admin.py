import csv
from django.contrib import admin
from django.http import HttpResponse
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from .models import *


class FeedbackAdmin(admin.ModelAdmin):
    raw_id_fields = ["user"]
    list_display = [
        "course_key",
        "get_course_name",
        "user",
        "get_user_mobile",
        "block_name",
        "rating",
        "feedback",
        "consent_to_share",
        "created",
        "modified",
    ]
    search_fields = [
        "course_key",
        "user__username",
    ]
    list_filter = ["consent_to_share", "course_key"]
    actions = ("export_as_csv",)

    def get_course_name(self, instance):
        try:
            course_overview = CourseOverview.get_from_id(instance.course_key)
            return course_overview.display_name
        except Exception as e:
            return ""

    get_course_name.short_description = "Course Name"

    def get_user_mobile(self, instance):
        try:
            return instance.user.profile.mobile_number
        except Exception as e:
            return ""

    get_user_mobile.short_description = "Mobile Number"

    def export_as_csv(self, request, queryset):
        field_names = [
            "Course ID",
            "Course Name",
            "User",
            "Email",
            "Mobile Number",
            "Feedback Block",
            "Rating",
            "Feedback",
            "Created",
            "Modified",
            "Consent to Share",
        ]
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=Feedbacks.csv"
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            try:
                fullname = (
                    obj.user.profile.name
                    or obj.user.get_full_name()
                    or obj.user.username
                )
                mobile_number = obj.user.profile.mobile_number
            except Exception as e:
                fullname = obj.user.username
                mobile_number = ""

            try:
                course_overview = CourseOverview.get_from_id(obj.course_key)
                course_name = course_overview.display_name
            except Exception as e:
                course_name = ""

            data = [
                obj.course_key,
                course_name,
                fullname,
                obj.user.email,
                mobile_number,
                obj.block_name,
                obj.rating,
                obj.feedback,
                obj.created.strftime("%d-%m-%Y %H:%M"),
                obj.modified.strftime("%d-%m-%Y %H:%M"),
                "Yes" if obj.consent_to_share else "No",
            ]
            row = writer.writerow(data)
        return response


admin.site.register(Feedback, FeedbackAdmin)
