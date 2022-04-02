#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from polyaxon.polyflow import V1RunKind
from polyaxon.polyflow.matrix.kinds import V1MatrixKind


def get_fxt_mapping_with_inputs_outputs():
    return {
        "version": 1.1,
        "kind": "operation",
        "name": "run",
        "tags": ["key1", "value1"],
        "params": {"image": {"value": "test"}, "lr": {"value": 0.001}},
        "matrix": {
            "kind": V1MatrixKind.MAPPING,
            "values": [
                {"param1": "test1", "param2": 1, "param3": 1.1},
                {"param1": "test2", "param2": 2, "param3": 2.1},
            ],
        },
        "component": {
            "name": "experiment-template",
            "description": "experiment to predict something",
            "tags": ["key", "value"],
            "inputs": [
                {"name": "lr", "type": "float", "value": 0.1, "isOptional": True},
                {"name": "image", "type": "str"},
                {"name": "param1", "type": "str"},
                {"name": "param2", "type": "int"},
                {"name": "param3", "type": "float"},
            ],
            "outputs": [
                {"name": "result1", "type": "str"},
                {
                    "name": "result2",
                    "type": "str",
                    "isOptional": True,
                    "value": "{{ image }}",
                },
            ],
            "termination": {"maxRetries": 2},
            "run": {
                "kind": V1RunKind.JOB,
                "environment": {
                    "nodeSelector": {"polyaxon": "experiments"},
                    "serviceAccountName": "service",
                    "imagePullSecrets": ["secret1", "secret2"],
                },
                "container": {
                    "image": "{{ image }}",
                    "command": ["python3", "main.py"],
                    "args": "--lr={{ lr }}",
                    "resources": {"requests": {"cpu": 1}},
                },
            },
        },
    }


def get_fxt_mapping_with_run_patch():
    return {
        "version": 1.1,
        "kind": "operation",
        "name": "foo",
        "description": "a description",
        "params": {"image": {"value": "test"}},
        "matrix": {
            "kind": V1MatrixKind.MAPPING,
            "values": [
                {"param1": "test1", "param2": 1, "param3": 1.1},
                {"param1": "test2", "param2": 2, "param3": 2.1},
            ],
        },
        "termination": {"maxRetries": 2},
        "runPatch": {
            "kind": V1RunKind.JOB,
            "environment": {
                "nodeSelector": {"polyaxon": "experiments"},
                "serviceAccountName": "service",
                "imagePullSecrets": ["secret1", "secret2"],
            },
        },
        "component": {
            "name": "experiment-template",
            "inputs": [
                {"name": "image", "type": "str"},
                {"name": "param1", "type": "str"},
                {"name": "param2", "type": "int"},
                {"name": "param3", "type": "float"},
            ],
            "tags": ["tag1", "tag2"],
            "run": {
                "kind": V1RunKind.JOB,
                "container": {"image": "{{ image }}"},
                "init": [{"connection": "foo", "git": {"revision": "dev"}}],
            },
        },
    }
