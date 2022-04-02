#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.

from polyaxon.polyflow import V1RunKind
from polyaxon.polyflow.matrix.kinds import V1MatrixKind


def get_fxt_backfill_with_inputs_outputs():
    return {
        "version": 1.1,
        "kind": "operation",
        "name": "run",
        "tags": ["key1", "value1"],
        "params": {"image": {"value": "test"}, "lr": {"value": 0.001}},
        "matrix": {
            "kind": V1MatrixKind.GRID,
            "params": {
                "dts": {"kind": "daterange", "value": ["2012-01-01", "2012-01-20", 5]},
            },
        },
        "component": {
            "name": "experiment-template",
            "description": "experiment to predict something",
            "tags": ["key", "value"],
            "inputs": [
                {"name": "lr", "type": "float", "value": 0.1, "isOptional": True},
                {"name": "image", "type": "str"},
                {"name": "dts", "type": "date"},
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
                    "args": ["--lr={{ lr }}", "{{ params.dts.as_arg }}"],
                    "resources": {"requests": {"cpu": 1}},
                },
            },
        },
    }
