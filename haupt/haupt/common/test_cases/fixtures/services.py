#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from uuid import UUID

from polyaxon.polyflow import V1RunKind


def get_fxt_service():
    return {
        "version": 1.1,
        "kind": "operation",
        "name": "foo",
        "description": "a description",
        "tags": ["tag1", "tag2"],
        "trigger": "all_succeeded",
        "component": {
            "name": "service-template",
            "tags": ["backend", "lab"],
            "run": {
                "kind": V1RunKind.SERVICE,
                "container": {"image": "jupyter"},
                "init": [{"connection": "foo", "git": {"revision": "dev"}}],
                "ports": [5555],
            },
        },
    }


def get_fxt_service_with_inputs():
    return {
        "version": 1.1,
        "kind": "operation",
        "name": "foo",
        "description": "a description",
        "params": {"image": {"value": "foo/bar"}},
        "component": {
            "name": "service-template",
            "inputs": [{"name": "image", "type": "str"}],
            "tags": ["backend", "lab"],
            "run": {
                "kind": V1RunKind.SERVICE,
                "container": {"image": "{{ image }}"},
                "init": [{"connection": "foo", "git": {"revision": "dev"}}],
                "ports": [5555],
            },
        },
    }


def get_fxt_service_with_upstream_runs(run_uuid: UUID):
    return {
        "version": 1.1,
        "kind": "operation",
        "name": "foo",
        "description": "a description",
        "params": {
            "image": {
                "value": "outputs.image-out",
                "ref": "runs.{}".format(run_uuid.hex),
            }
        },
        "component": {
            "name": "service-template",
            "inputs": [{"name": "image", "type": "str"}],
            "tags": ["backend", "lab"],
            "run": {
                "kind": V1RunKind.SERVICE,
                "container": {"image": "{{ image }}"},
                "init": [{"connection": "foo", "git": {"revision": "dev"}}],
                "ports": [5555],
            },
        },
    }


def get_fxt_job_with_hub_ref():
    return {
        "version": 1.1,
        "kind": "operation",
        "name": "foo",
        "description": "a description",
        "params": {"image": {"value": "foo/bar"}},
        "hubRef": "notebook",
    }
