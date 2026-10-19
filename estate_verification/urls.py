
from django.urls import path

from . import views

app_name = "estate_verification"

urlpatterns = [
    path(
        "",
        views.dashboard,
        name="dashboard",
    ),
    path(
        "submission/<uuid:submission_id>/",
        views.estate_review,
        name="estate_review",
    ),
    path(
        "submission/<uuid:submission_id>/page/<int:page_id>/verify/",
        views.verify_page,
        name="verify_page",
    ),
    path(
        "submission/<uuid:submission_id>/comment/",
        views.add_comment,
        name="add_comment",
    ),
    path(
        "submission/<uuid:submission_id>/action/",
        views.workflow_action,
        name="workflow_action",
    ),
    path(
        "submission/<uuid:submission_id>/history/",
        views.submission_history,
        name="submission_history",
    ),
    #=====================================================
    # Deadline Management   
    #=====================================================
        path(
        "deadlines/",
        views.deadline_management,
        name="deadline_management",
    ),
    path(
        "deadlines/<int:pk>/extend/",
        views.deadline_extend,
        name="deadline_extend",
    ),
    path(
        "my-report-deadlines/",
        views.report_deadline_dashboard,
        name="report_deadline_dashboard",
    ),
]
