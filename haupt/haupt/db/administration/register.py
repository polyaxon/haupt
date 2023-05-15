from django.contrib.admin import site
from django.contrib.auth.admin import UserAdmin

from haupt.db.administration.artifacts import ArtifactAdmin
from haupt.db.administration.projects import ProjectAdmin
from haupt.db.administration.runs import RunLightAdmin
from haupt.db.defs import Models

site.register(Models.User, UserAdmin)
site.register(Models.Artifact, ArtifactAdmin)
site.register(Models.Project, ProjectAdmin)
site.register(Models.Run, RunLightAdmin)
