import csv
from django.contrib import admin
from django.http import HttpResponse
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from .models import *


class FeedbackAdmin(admin.ModelAdmin):
    raw_id_fields = ["user"]
    list_display = ["course_key","get_course_name", "user", "block_name", "rating", "feedback"]
    search_fields = [
        "course_key",
        "user__username",
    ]
    list_filter = ["course_key"]
    actions = ("export_as_csv",)


    def get_course_name(self, instance):
        try:
            course_overview = CourseOverview.get_from_id(instance.course_key)
            return course_overview.display_name
        except Exception as e:
            return ""
    get_course_name.short_description = "Course Name"

    def export_as_csv(self, request, queryset):
        field_names = [
            "Course ID",
            "Course Name",
            "User",
            "Email",
            "Feedback Block",
            "Rating",
            "Feedback",
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
            except Exception as e:
                fullname = obj.user.username

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
                obj.block_name,
                obj.rating,
                obj.feedback,
            ]
            row = writer.writerow(data)
        return response


admin.site.register(Feedback, FeedbackAdmin)
