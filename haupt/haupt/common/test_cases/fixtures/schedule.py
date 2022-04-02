#!/usr/bin/python
#
# Copyright 2018-2022 Polyaxon, Inc.
# This file and its contents are licensed under the AGPLv3 License.
# Please see the included NOTICE for copyright information and
# LICENSE-AGPL for a copy of the license.
from datetime import timedelta

from django.utils.timezone import now

from polyaxon.polyflow import V1RunKind
from polyaxon.polyflow.matrix.kinds import V1MatrixKind


def get_fxt_schedule_with_inputs_outputs(start_at=None, delta=7):
    start_at = start_at or now()
    start_at = start_at.replace(hour=0, minute=0, second=0, microsecond=0)
    return {
        "version": 1.1,
        "kind": "operation",
        "name": "run",
        "tags": ["key1", "value1"],
        "params": {"image": {"value": "test"}, "lr": {"value": 0.001}},
        "schedule": {
            "kind": "cron",
            "cron": "0 0 * * *",
            "startAt": start_at.isoformat(),
            "endAt": (start_at + timedelta(days=delta)).isoformat(),
            "dependsOnPast": True,
        },
        "matrix": {
            "kind": V1MatrixKind.BAYES,
            "numInitialRuns": 5,
            "maxIterations": 5,
            "metric": {"name": "loss", "optimization": "minimize"},
            "params": {
                "param1": {"kind": "choice", "value": ["test1", "test2"]},
                "param2": {"kind": "range", "value": [1, 2, 1]},
                "param3": {"kind": "uniform", "value": [0, 0.9]},
            },
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
