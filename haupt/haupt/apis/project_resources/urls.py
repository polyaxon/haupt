from rest_framework.urlpatterns import format_suffix_patterns

from django.urls import re_path

from haupt.apis.project_resources.views import runs as runs_views
from haupt.apis.project_resources.views import versions as versions_views
from haupt.common.apis.urls import project_versions, projects

projects_urlpatterns = [
    re_path(
        projects.URLS_PROJECTS_RUNS_TAG,
        runs_views.ProjectRunsTagView.as_view(),
    ),
    re_path(
        projects.URLS_PROJECTS_RUNS_ARTIFACTS_LINEAGE_V0,
        runs_views.ProjectRunsArtifactsView.as_view(),
    ),
    re_path(
        projects.URLS_PROJECTS_RUNS_ARTIFACTS_LINEAGE,
        runs_views.ProjectRunsArtifactsView.as_view(),
    ),
    re_path(
        projects.URLS_PROJECTS_RUNS_STOP,
        runs_views.ProjectRunsStopView.as_view(),
    ),
    re_path(
        projects.URLS_PROJECTS_RUNS_SKIP,
        runs_views.ProjectRunsSkipView.as_view(),
    ),
    re_path(
        projects.URLS_PROJECTS_RUNS_APPROVE,
        runs_views.ProjectRunsApproveView.as_view(),
    ),
    re_path(
        projects.URLS_PROJECTS_RUNS_DELETE,
        runs_views.ProjectRunsDeleteView.as_view(),
    ),
    re_path(
        projects.URLS_PROJECTS_RUNS_SYNC,
        runs_views.ProjectRunsSyncView.as_view(),
    ),
    re_path(
        projects.URLS_PROJECTS_RUNS_LIST,
        runs_views.ProjectRunsListView.as_view(),
    ),
    re_path(
        projects.URLS_PROJECTS_RUNS_ARCHIVE,
        runs_views.ProjectRunsArchiveView.as_view(),
    ),
    re_path(
        projects.URLS_PROJECTS_RUNS_RESTORE,
        runs_views.ProjectRunsRestoreView.as_view(),
    ),
    re_path(
        projects.URLS_PROJECTS_RUNS_TRANSFER,
        runs_views.ProjectRunsTransferView.as_view(),
    ),
    re_path(
        projects.URLS_PROJECTS_RUNS_INVALIDATE,
        runs_views.ProjectRunsInvalidateView.as_view(),
    ),
    re_path(
        projects.URLS_PROJECTS_RUNS_BOOKMARK,
        runs_views.ProjectRunsBookmarkView.as_view(),
    ),
    re_path(
        project_versions.URLS_PROJECT_COMPONENT_VERSIONS_LIST,
        versions_views.ProjectComponentVersionListView.as_view(),
    ),
    # Component Versions
    re_path(
        project_versions.URLS_PROJECT_COMPONENT_VERSIONS_NAMES,
        versions_views.ProjectComponentVersionNameListView.as_view(),
    ),
    re_path(
        project_versions.URLS_PROJECT_COMPONENT_VERSIONS_DETAILS,
        versions_views.ProjectComponentVersionDetailView.as_view(),
    ),
    re_path(
        project_versions.URLS_PROJECT_COMPONENT_VERSIONS_TRANSFER,
        versions_views.ProjectComponentVersionTransferView.as_view(),
    ),
    re_path(
        project_versions.URLS_PROJECT_COMPONENT_VERSIONS_STAGES,
        versions_views.ProjectComponentVersionStageListView.as_view(),
    ),
    # Model Versions
    re_path(
        project_versions.URLS_PROJECT_MODEL_VERSIONS_LIST,
        versions_views.ProjectModelVersionListView.as_view(),
    ),
    re_path(
        project_versions.URLS_PROJECT_MODEL_VERSIONS_NAMES,
        versions_views.ProjectModelVersionNameListView.as_view(),
    ),
    re_path(
        project_versions.URLS_PROJECT_MODEL_VERSIONS_DETAILS,
        versions_views.ProjectModelVersionDetailView.as_view(),
    ),
    re_path(
        project_versions.URLS_PROJECT_MODEL_VERSIONS_TRANSFER,
        versions_views.ProjectModelVersionTransferView.as_view(),
    ),
    re_path(
        project_versions.URLS_PROJECT_MODEL_VERSIONS_STAGES,
        versions_views.ProjectModelVersionStageListView.as_view(),
    ),
    # Artifact Versions
    re_path(
        project_versions.URLS_PROJECT_ARTIFACT_VERSIONS_LIST,
        versions_views.ProjectArtifactVersionListView.as_view(),
    ),
    re_path(
        project_versions.URLS_PROJECT_ARTIFACT_VERSIONS_NAMES,
        versions_views.ProjectArtifactVersionNameListView.as_view(),
    ),
    re_path(
        project_versions.URLS_PROJECT_ARTIFACT_VERSIONS_DETAILS,
        versions_views.ProjectArtifactVersionDetailView.as_view(),
    ),
    re_path(
        project_versions.URLS_PROJECT_ARTIFACT_VERSIONS_TRANSFER,
        versions_views.ProjectArtifactVersionTransferView.as_view(),
    ),
    re_path(
        project_versions.URLS_PROJECT_ARTIFACT_VERSIONS_STAGES,
        versions_views.ProjectArtifactVersionStageListView.as_view(),
    ),
]

# Order is important, because the patterns could swallow other urls
urlpatterns = format_suffix_patterns(projects_urlpatterns)
