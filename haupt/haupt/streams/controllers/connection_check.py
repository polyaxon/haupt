import logging
import os
import traceback
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from rest_framework import status

from clipped.utils.enums import get_enum_value
from haupt.streams.connections.fs import AppFS
from polyaxon import settings
from polyaxon._connections import V1Connection, V1ConnectionKind
from polyaxon._fs.async_manager import ensure_async_execution
from polyaxon._fs.utils import get_store_path
from polyaxon._k8s.manager.async_manager import AsyncK8sManager
from polyaxon._schemas.lifecycle import V1ProjectFeature


logger = logging.getLogger("haupt.streams.connection_checks")

AGENT_KUBERNETES_CHECK = "agent_kubernetes"

STATUS_PASSED = "passed"
STATUS_FAILED = "failed"

CATEGORY_CONFIGURATION = "configuration"
CATEGORY_KUBERNETES = "kubernetes"
CATEGORY_STORAGE = "storage"
CATEGORY_UNSUPPORTED = "unsupported"

MOUNTINFO_PATH = "/proc/self/mountinfo"


class MountPathMissingError(FileNotFoundError):
    pass


class MountPathNotMountedError(RuntimeError):
    pass


class MountPathCheckError(RuntimeError):
    pass


def _configured_sources(connection: Optional[V1Connection]) -> List[str]:
    if not connection:
        return []

    sources = []
    if connection.schema_:
        sources.append("schema")
    if connection.secret:
        sources.append("secret")
    if connection.config_map:
        sources.append("config_map")
    if connection.env:
        sources.append("env")
    return sources


def _connection_data(
    name: str,
    kind: str,
    connection: Optional[V1Connection] = None,
    configured_sources: Optional[List[str]] = None,
) -> Dict:
    return {
        "name": name,
        "kind": kind,
        "configured_sources": (
            configured_sources
            if configured_sources is not None
            else _configured_sources(connection)
        ),
    }


def _passed_check(name: str, category: str, message: str) -> Dict:
    return {
        "name": name,
        "status": STATUS_PASSED,
        "code": "ok",
        "category": category,
        "message": message,
    }


def _safe_hints(category: str, connection_kind: str, exception: Exception) -> List[str]:
    exception_name = exception.__class__.__name__
    if connection_kind == V1ConnectionKind.GCS:
        return [
            "Check that the streams pod can resolve GCS credentials through "
            "Workload Identity, GOOGLE_APPLICATION_CREDENTIALS, or the configured "
            "artifact-store secret.",
            "Check that the GCS identity has read and write access to the configured "
            "bucket.",
        ]
    if connection_kind == V1ConnectionKind.S3:
        return [
            "Check that the streams pod has AWS credentials through env vars, "
            "mounted credentials, IAM role, or the configured artifact-store secret.",
            "Check that the AWS identity has read and write access to the configured "
            "bucket.",
        ]
    if connection_kind == V1ConnectionKind.WASB:
        return [
            "Check that the streams pod has Azure storage credentials from the "
            "configured secret or environment.",
            "Check that the Azure identity has read and write access to the "
            "configured container.",
        ]
    if category == CATEGORY_KUBERNETES:
        return [
            "Check that the streams pod has Kubernetes credentials and RBAC for the "
            "agent namespace.",
        ]
    if exception_name == "PermissionError":
        return ["Check filesystem permissions for the configured path."]
    return [
        "Check the connection configuration and credentials available to the streams pod."
    ]


def _failed_check(
    name: str,
    category: str,
    code: str,
    message: str,
    connection_kind: str,
    exception: Optional[Exception] = None,
    hints: Optional[List[str]] = None,
) -> Dict:
    check = {
        "name": name,
        "status": STATUS_FAILED,
        "code": code,
        "category": category,
        "message": message,
        "hints": hints or [],
    }
    if exception:
        check["exception"] = exception.__class__.__name__
        check["hints"] = hints or _safe_hints(category, connection_kind, exception)
    return check


def _result(connection: Dict, checks: List[Dict]) -> Dict:
    return {
        "status": (
            STATUS_PASSED
            if all(check["status"] == STATUS_PASSED for check in checks)
            else STATUS_FAILED
        ),
        "connection": connection,
        "checks": checks,
    }


def _response(results: List[Dict]) -> Dict:
    return {
        "status": (
            STATUS_PASSED
            if all(result["status"] == STATUS_PASSED for result in results)
            else STATUS_FAILED
        ),
        "results": results,
    }


def _log_check_exception(
    connection_name: str,
    check_name: str,
    category: str,
) -> None:
    logger.error(
        "Agent connection check failed: connection=%s check=%s category=%s\n%s",
        connection_name,
        check_name,
        category,
        traceback.format_exc(),
    )


def _normalize_mount_path(path: str) -> str:
    return os.path.normpath(path)


def _decode_mountinfo_path(path: str) -> str:
    return (
        path.replace("\\040", " ")
        .replace("\\011", "\t")
        .replace("\\012", "\n")
        .replace("\\134", "\\")
    )


def _read_mount_points() -> List[str]:
    mount_points = []
    with open(MOUNTINFO_PATH) as mountinfo:
        for line in mountinfo:
            parts = line.split()
            if len(parts) >= 5:
                mount_points.append(_decode_mountinfo_path(parts[4]))
    return mount_points


def _is_mount_point(path: str) -> bool:
    path = _normalize_mount_path(path)
    return path in {_normalize_mount_path(p) for p in _read_mount_points()}


def _check_mount_artifact_store_root(store_path: str) -> None:
    if not os.path.isdir(store_path):
        raise MountPathMissingError(store_path)
    try:
        mounted = _is_mount_point(store_path)
    except Exception as e:
        raise MountPathCheckError(store_path) from e
    if not mounted:
        raise MountPathNotMountedError(store_path)


def _get_mount_path_failure(exception: Exception) -> Tuple[str, str, List[str]]:
    if isinstance(exception, MountPathMissingError):
        return (
            "connection_mount_path_missing",
            (
                "Connection check failed because the configured mount path does not "
                "exist in the streams pod."
            ),
            [
                "Mount this connection into the streams pod before checking it.",
                "Check the connection mount path in the agent configuration.",
            ],
        )
    if isinstance(exception, MountPathNotMountedError):
        return (
            "connection_mount_path_not_mounted",
            (
                "Connection check failed because the configured mount path is not "
                "mounted in the streams pod."
            ),
            [
                "Add this connection to mountConnections for the agent deployment.",
                "Check that the streams pod has the expected volume mount.",
            ],
        )
    return (
        "connection_mount_path_check_failed",
        "Connection check failed while verifying the configured mount path.",
        ["Check the streams pod mount configuration."],
    )


async def _check_artifacts_store_access(fs, store_path: str, agent_uuid: str) -> None:
    payload = "polyaxon-agent-connection-check:{}".format(uuid4().hex).encode()
    subpath = ".agents/{}/checks/{}.txt".format(agent_uuid, uuid4().hex)
    path = get_store_path(
        store_path=store_path, subpath=subpath, entity=V1ProjectFeature.RUNTIME
    )
    is_async = getattr(fs, "async_impl", False)
    created = False
    try:
        await ensure_async_execution(
            fs=fs,
            fct="pipe",
            is_async=is_async,
            path=path,
            value=payload,
        )
        created = True
        data = await ensure_async_execution(
            fs=fs, fct="cat", is_async=is_async, path=path
        )
        if isinstance(data, dict):
            data = data.get(path)
        if data != payload:
            raise ValueError("Connection check read back unexpected data.")
        await ensure_async_execution(
            fs=fs,
            fct="rm",
            is_async=is_async,
            path=path,
            recursive=False,
        )
        created = False
    finally:
        if created:
            try:
                await ensure_async_execution(
                    fs=fs,
                    fct="rm",
                    is_async=is_async,
                    path=path,
                    recursive=False,
                )
            except Exception:
                logger.warning(
                    "Agent connection check cleanup failed: connection_path=%s\n%s",
                    path,
                    traceback.format_exc(),
                )


async def _check_artifacts_store(
    connection: V1Connection,
    agent_uuid: str,
) -> Dict:
    connection_name = connection.name
    kind = get_enum_value(connection.kind)
    connection_data = _connection_data(
        name=connection_name,
        kind=kind,
        connection=connection,
    )

    try:
        fs = await AppFS.get_fs(connection=connection_name)
        store_path = AppFS.get_fs_root_path(connection=connection_name)
        if connection.is_mount:
            _check_mount_artifact_store_root(store_path=store_path)
        await _check_artifacts_store_access(
            fs=fs, store_path=store_path, agent_uuid=agent_uuid
        )
    except (MountPathMissingError, MountPathNotMountedError, MountPathCheckError) as e:
        code, message, hints = _get_mount_path_failure(e)
        _log_check_exception(connection_name, "mount_path", CATEGORY_STORAGE)
        check = _failed_check(
            name="mount_path",
            category=CATEGORY_STORAGE,
            code=code,
            message=message,
            connection_kind=kind,
            exception=e,
            hints=hints,
        )
    except Exception as e:
        _log_check_exception(connection_name, "access", CATEGORY_STORAGE)
        check = _failed_check(
            name="access",
            category=CATEGORY_STORAGE,
            code="artifacts_store_access_failed",
            message=(
                "Could not write, read, and delete a test object in the artifacts "
                "store."
            ),
            connection_kind=kind,
            exception=e,
        )
    else:
        check = _passed_check(
            name="access",
            category=CATEGORY_STORAGE,
            message="Test object was written, read, and deleted.",
        )
    return _result(connection_data, [check])


async def _check_kubernetes_connection(namespace: str) -> Tuple[Dict, int]:
    configured_sources = [
        "service_account" if settings.CLIENT_CONFIG.in_cluster else "kube_config"
    ]
    connection_data = _connection_data(
        name=AGENT_KUBERNETES_CHECK,
        kind=CATEGORY_KUBERNETES,
        configured_sources=configured_sources,
    )

    manager = AsyncK8sManager(
        namespace=namespace,
        in_cluster=settings.CLIENT_CONFIG.in_cluster,
    )
    try:
        try:
            await manager.setup()
        except Exception as e:
            _log_check_exception(AGENT_KUBERNETES_CHECK, "setup", CATEGORY_KUBERNETES)
            return (
                _result(
                    connection_data,
                    [
                        _failed_check(
                            name="setup",
                            category=CATEGORY_KUBERNETES,
                            code="kubernetes_setup_failed",
                            message=(
                                "Connection check failed while loading Kubernetes "
                                "client configuration."
                            ),
                            connection_kind=CATEGORY_KUBERNETES,
                            exception=e,
                        )
                    ],
                ),
                status.HTTP_200_OK,
            )

        checks = [
            _passed_check(
                name="setup",
                category=CATEGORY_KUBERNETES,
                message="Kubernetes client configuration loaded.",
            )
        ]
        try:
            await manager.list_pods(namespace=namespace, reraise=True, limit=1)
        except Exception as e:
            _log_check_exception(
                AGENT_KUBERNETES_CHECK, "list_pods", CATEGORY_KUBERNETES
            )
            checks.append(
                _failed_check(
                    name="list_pods",
                    category=CATEGORY_KUBERNETES,
                    code="kubernetes_list_pods_failed",
                    message="Connection check failed while listing pods in the agent namespace.",
                    connection_kind=CATEGORY_KUBERNETES,
                    exception=e,
                )
            )
            return _result(connection_data, checks), status.HTTP_200_OK

        checks.append(
            _passed_check(
                name="list_pods",
                category=CATEGORY_KUBERNETES,
                message="Pods can be listed in the agent namespace.",
            )
        )
        return _result(connection_data, checks), status.HTTP_200_OK
    finally:
        try:
            await manager.close()
        except Exception:
            logger.warning(
                "Agent connection check Kubernetes client close failed:\n%s",
                traceback.format_exc(),
            )


async def check_named_agent_connection(connection_name: str) -> Dict:
    result = _result(
        _connection_data(
            name=connection_name,
            kind="unknown",
            configured_sources=[],
        ),
        [
            _failed_check(
                name="resolve_connection",
                category=CATEGORY_UNSUPPORTED,
                code="named_connection_check_unsupported",
                message="Named connection checks are not supported yet.",
                connection_kind="unknown",
                hints=[
                    "Run the check without a connection to validate the services "
                    "required by the agent."
                ],
            )
        ],
    )
    return _response([result])


async def check_default_agent_connections(
    namespace: str,
    agent_uuid: str,
) -> Dict:
    results = []
    artifacts_store = (
        settings.AGENT_CONFIG.artifacts_store if settings.AGENT_CONFIG else None
    )
    if artifacts_store:
        artifacts_result = await _check_artifacts_store(
            connection=artifacts_store,
            agent_uuid=agent_uuid,
        )
        results.append(artifacts_result)
    else:
        results.append(
            _result(
                _connection_data(
                    name="artifacts_store",
                    kind="unknown",
                    configured_sources=[],
                ),
                [
                    _failed_check(
                        name="resolve_connection",
                        category=CATEGORY_CONFIGURATION,
                        code="default_artifacts_store_not_found",
                        message=(
                            "Default artifacts store was not found in the agent "
                            "configuration."
                        ),
                        connection_kind="unknown",
                        hints=[
                            "Check the default artifacts store in the agent configuration."
                        ],
                    )
                ],
            )
        )
    kubernetes_result, _ = await _check_kubernetes_connection(namespace=namespace)
    results.append(kubernetes_result)
    return _response(results)
