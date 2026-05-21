from django.http import Http404

from haupt.db.defs import Models
from polyaxon.schemas import LifeCycle, V1CompiledOperation


def get_active_ssh_key_or_404(fingerprint: str):
    key = Models.UserSshKey.objects.lookup_by_fingerprint(fingerprint, query_user=True)
    if not key:
        raise Http404
    return key


def require_run_on_k8s(run) -> None:
    if not LifeCycle.is_k8s_stoppable(run.status):
        raise Http404


def require_ssh_plugin(run) -> None:
    try:
        compiled_operation = V1CompiledOperation.read(run.content)
    except Exception as e:
        raise Http404 from e

    plugins = getattr(compiled_operation, "plugins", None)
    if not plugins or not getattr(plugins, "ssh", None):
        raise Http404


def validate_ssh_access_base(run, fingerprint: str):
    require_run_on_k8s(run)
    require_ssh_plugin(run)
    return get_active_ssh_key_or_404(fingerprint=fingerprint)


def build_ssh_access_validation_response(key, agent_uuid=None):
    return {
        "key_uuid": key.uuid.hex,
        "username": key.user.username if key.user_id else None,
        "agent_uuid": agent_uuid,
    }
