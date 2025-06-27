import csv
from django.contrib import admin
from django.http import HttpResponse
from django.urls import reverse
from django.http import HttpResponseRedirect
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from .models import Feedback, ShareFeedbackWith


class ShareFeedbackWithInline(admin.TabularInline):
    """
    Inline admin interface for managing courses with which feedback is shared.
    """

    model = ShareFeedbackWith
    extra = 1  # Number of empty forms to display
    verbose_name = "Share Feedback with other Courses"
    verbose_name_plural = "Share Feedback with other Courses"


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    """
    Admin interface for managing Feedback entries.
    """

    raw_id_fields = ["user"]
    inlines = [ShareFeedbackWithInline]
    list_display = [
        "course_key",
        "get_course_name",
        "user",
        "get_user_mobile",
        "block_name",
        "get_rating_display",
        "feedback",
        "consent_to_share",
        "is_approved",
        "created",
        "modified",
    ]
    search_fields = [
        "course_key",
        "user__username",
    ]
    list_filter = ["consent_to_share", "is_approved", "course_key"]
    list_editable = ["is_approved"]
    actions = ["export_as_csv", "toggle_approval"]
    readonly_fields = [
        "course_key",
        "user",
        "block_name",
        "rating",
        "created",
        "modified",
        "rating_display",
    ]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "course_key",
                    "user",
                    "block_name",
                    "rating",
                    "rating_display",
                    "feedback",
                    "consent_to_share",
                    "is_approved",
                ),
                "description": (
                    '<p><strong>Note:</strong> To toggle approval status, use the "is_approved" checkbox in the list view '
                    'or the "Toggle approval status" bulk action. Editing individual feedback here is only necessary for '
                    "specific updates to consent or approval. Ratings are displayed on a 1–5 scale (1=Poor, 5=Excellent) in "
                    "the list view and CSV export, while the raw rating (0–4) is shown below for reference.</p>"
                ),
            },
        ),
    )

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

    def get_rating_display(self, instance):
        """
        Display rating on a 1–5 scale (1=Poor, 5=Excellent) instead of 0–4.
        """
        if instance.rating is not None and 0 <= instance.rating <= 4:
            rating_map = {
                4: "5 (Excellent)",
                3: "4 (Good)",
                2: "3 (Average)",
                1: "2 (Fair)",
                0: "1 (Poor)",
            }
            return rating_map.get(instance.rating, str(instance.rating + 1))
        return "-"

    get_rating_display.short_description = "Rating"

    def rating_display(self, instance):
        """
        Read-only field for change form to show 1–5 rating.
        """
        return self.get_rating_display(instance)

    rating_display.short_description = "Rating (1–5 Scale)"

    def toggle_approval(self, request, queryset):
        """
        Toggle the approval status of selected feedback entries.
        """
        count = 0
        for feedback in queryset:
            feedback.is_approved = not feedback.is_approved
            feedback.save()
            count += 1
        self.message_user(
            request, f"Toggled approval status for {count} feedback entries."
        )

    toggle_approval.short_description = "Toggle approval status for selected feedback"

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
            "Approved for Display",
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

            rating_display = (
                str(obj.rating + 1)
                if obj.rating is not None and 0 <= obj.rating <= 4
                else "-"
            )

            data = [
                obj.course_key,
                course_name,
                fullname,
                obj.user.email,
                mobile_number,
                obj.block_name,
                rating_display,
                obj.feedback,
                obj.created.strftime("%d-%m-%Y %H:%M"),
                obj.modified.strftime("%d-%m-%Y %H:%M"),
                "Yes" if obj.consent_to_share else "No",
                "Yes" if obj.is_approved else "No",
            ]
            writer.writerow(data)
        return response

    def get_readonly_fields(self, request, obj=None):
        """
        Make most fields read-only in the change form to encourage list view editing.
        """
        if obj:  # Editing an existing object
            return self.readonly_fields
        return []
