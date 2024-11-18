import csv
from django.contrib import admin
from django.http import HttpResponse
from .models import *


class FeedbackAdmin(admin.ModelAdmin):
    raw_id_fields = ["user"]
    list_display = ["course_key", "user", "block_name", "rating", "feedback"]
    search_fields = [
        "course_key",
        "user__username",
    ]
    list_filter = ["course_key"]
    actions = ("export_as_csv",)

    def export_as_csv(self, request, queryset):
        field_names = [
            "Course ID",
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
            data = [
                obj.course_key,
                fullname,
                obj.user.email,
                obj.block_name,
                obj.rating,
                obj.feedback,
            ]
            row = writer.writerow(data)
        return response


admin.site.register(Feedback, FeedbackAdmin)
