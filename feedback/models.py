"""
Models for Feedback

Migration Notes

If you make changes to this model, be sure to create an appropriate migration
file and check it in at the same time as your model changes. To do that,

1. Go to the edx-platform dir
2. ./manage.py lms makemigrations --settings=production 
3. ./manage.py lms migrate --settings=production
"""

import logging
from django.db import models
from model_utils.models import TimeStampedModel
from django.contrib.auth.models import User
from opaque_keys.edx.django.models import CourseKeyField

log = logging.getLogger(__name__)


class Feedback(TimeStampedModel):
    """
    Model for storing course-wise feedback submitted by users.

    This model captures user feedback and ratings for specific course blocks, with options
    for sharing consent and approval for public display.
    """

    course_key = CourseKeyField(db_index=True, max_length=255)
    user = models.ForeignKey(
        User,
        related_name="feedback_submitted_by",
        db_index=True,
        on_delete=models.CASCADE,
    )
    block_id = models.CharField(
        max_length=1024,
    )
    rating = models.IntegerField(verbose_name="Rating", default=0)
    block_name = models.CharField(max_length=1024, null=True, blank=True)
    feedback = models.TextField(verbose_name="User Feedback", null=True, blank=True)
    consent_to_share = models.BooleanField(
        verbose_name="Consent to Share Feedback",
        help_text="Check this box to consent to your feedback being shared publicly by the EBC Learning on its website, social media, and promotional materials.",
        default=True,
    )
    is_approved = models.BooleanField(
        verbose_name="Approved for Display",
        help_text="Check this box to approve this feedback for public display on the course page.",
        default=False,
    )

    def __str__(self):
        return "{}-{}".format(str(self.course_key), self.user.username)

    def __repr__(self):
        return self.__str__()

    class Meta:
        app_label = "feedback"
        verbose_name = "Feedback"
        verbose_name_plural = "Course Feedback"
        indexes = [
            models.Index(fields=["course_key", "is_approved", "consent_to_share"]),
        ]

    @classmethod
    def create_or_update(
        cls,
        course_key,
        user_id,
        block_id,
        block_name,
        rating,
        feedback_message,
        consent_to_share,
    ):
        """
        Update user feedback record
        """
        try:
            feedback, _ = cls.objects.get_or_create(
                course_key=course_key, user_id=user_id, block_id=block_id
            )
            if rating is not None:
                feedback.rating = rating
            if feedback_message is not None:
                feedback.feedback = feedback_message
            feedback.block_name = block_name
            feedback.consent_to_share = consent_to_share
            feedback.save()
        except Exception as e:
            log.info(
                "Failed to save course feedback for {course_key} by {user_id}, Error: {error}".format(
                    course_key=course_key, user_id=user_id, error=str(e)
                )
            )


class ShareFeedbackWith(TimeStampedModel):
    """
    Model to associate feedback with multiple course versions.

    This model enables feedback submitted for one course version (e.g., V1) to be shared
    with other course versions (e.g., V2, V3) for display purposes.
    """

    feedback = models.ForeignKey(Feedback, on_delete=models.CASCADE)
    course_key = CourseKeyField(
        db_index=True,
        max_length=255,
        help_text="The course key of the course version with which the feedback is shared.",
    )

    def __str__(self):
        return "{}-{}".format(str(self.course_key), self.feedback.user.username)

    def __repr__(self):
        return self.__str__()

    class Meta:
        app_label = "feedback"
        verbose_name = "Shared Feedback Course"
        verbose_name_plural = "Shared Feedback Courses"
        db_table = "feedback_shared_courses"
        constraints = [
            models.UniqueConstraint(
                fields=["feedback", "course_key"], name="unique_feedback_course_key"
            )
        ]
        indexes = [
            models.Index(fields=["course_key"]),
        ]
