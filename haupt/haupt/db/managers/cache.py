import uuid

from typing import List, Optional

from clipped.utils.lists import to_list

from haupt.db.defs import Models
from polyaxon._k8s.k8s_schemas import V1Container
from polyaxon.schemas import V1IO, V1Cache, V1CloningKind, V1Init


def get_run_io_state(
    run_state: str,
    cache: V1Cache,
    inputs: List[V1IO],
    outputs: List[V1IO],
    contexts: List[V1IO],
) -> str:
    cache_io = []
    if cache and cache.io:
        cache_io = cache.io or []

    def check_cache_io(io: V1IO, check_value: bool = False):
        if check_value and io.value is None:
            return False
        if cache_io:
            return io.name in cache_io
        return True

    inputs = sorted(inputs or [], key=lambda i: i.name)
    io_reprs = [io.get_repr() for io in inputs if check_cache_io(io)]
    if io_reprs:
        run_state += "in-" + str(io_reprs)

    outputs = sorted(outputs or [], key=lambda i: i.name)
    io_reprs = [io.get_repr() for io in outputs if check_cache_io(io, True)]
    if io_reprs:
        run_state += "out-" + str(io_reprs)

    contexts = sorted(contexts or [], key=lambda i: i.name)
    io_reprs = [io.get_repr() for io in contexts if check_cache_io(io, True)]
    if io_reprs:
        run_state += "ctx-" + str(io_reprs)

    return run_state


def get_state_from_container(container: V1Container):
    if not container:
        return None

    result = ""
    if container.command:
        result += "cmd-" + str(
            [str(c) for c in to_list(container.command, check_none=True) if c]
        )
    if container.args:
        result += "args-" + str(
            [str(c) for c in to_list(container.args, check_none=True) if c]
        )

    return result


def get_run_containers_state(
    containers: List[V1Container],
) -> Optional[str]:
    containers = containers or []
    cache_containers = [get_state_from_container(c) for c in containers]
    cache_containers = [c for c in cache_containers if c]
    if cache_containers:
        return str(cache_containers)

    return None


def get_run_connections_state(
    run_state: str,
    connections: List[str],
) -> str:
    connections = connections or []
    connections = [c for c in connections if c]
    if connections:
        return run_state + "connections-" + str(connections)

    return run_state


def get_run_init_state(
    run_state: str,
    init: List[V1Init],
) -> str:
    init = init or []
    init_reprs = [i.to_light_dict(exclude_attrs=["container"]) for i in init if i]
    if init_reprs:
        init_reprs += "init-" + str(init_reprs)

    container_reprs = get_run_containers_state(
        [i.container for i in init if i.container]
    )
    if container_reprs:
        return run_state + "init-containers-" + str(container_reprs)

    return run_state


def get_run_sections_state(
    run_state: str,
    cache: V1Cache,
    init: List[V1Init],
    connections: List[str],
    containers: List[V1Container],
) -> str:
    if cache and cache.sections is not None:
        cache_sections = cache.sections
    else:
        cache_sections = ["init", "connections", "containers"]

    if "init" in cache_sections and init:
        run_state += get_run_init_state(run_state, init)

    if "connections" in cache_sections and connections:
        run_state += get_run_connections_state(run_state, connections)

    if "containers" in cache_sections and containers:
        containers_reprs = get_run_containers_state(containers)
        if containers_reprs:
            run_state += "containers-" + str(containers_reprs)

    return run_state


def get_run_state(
    cache: V1Cache,
    inputs: List[V1IO],
    outputs: List[V1IO],
    contexts: List[V1IO],
    init: List[V1Init],
    connections: List[str],
    containers: List[V1Container],
    namespace: uuid.UUID,
    component_state: uuid.UUID = None,
) -> Optional[uuid.UUID]:
    """A string representation that is used to create hash cache"""
    run_state = ""

    run_state = get_run_io_state(
        run_state=run_state,
        cache=cache,
        inputs=inputs,
        outputs=outputs,
        contexts=contexts,
    )

    run_state = get_run_sections_state(
        run_state=run_state,
        cache=cache,
        init=init,
        connections=connections,
        containers=containers,
    )

    if not run_state:
        return None

    if component_state:
        run_state = component_state.hex + run_state
    return uuid.uuid5(namespace, run_state)


def get_cache_clones(run_id: int):
    return Models.Run.objects.filter(
        original_id=run_id, cloning_kind=V1CloningKind.CACHE
    ).values_list("id", flat=True)
