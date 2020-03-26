#!/usr/bin/python
#
# Copyright 2018-2020 Polyaxon, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# coding: utf-8

"""
    Polyaxon SDKs and REST API specification.

    Polyaxon SDKs and REST API specification.  # noqa: E501

    OpenAPI spec version: 1.0.71
    Contact: contact@polyaxon.com
    Generated by: https://github.com/swagger-api/swagger-codegen.git
"""


import pprint
import re  # noqa: F401

import six


class V1MPIJob(object):
    """NOTE: This class is auto generated by the swagger code generator program.

    Do not edit the class manually.
    """

    """
    Attributes:
      swagger_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    swagger_types = {
        "kind": "str",
        "clean_pod_policy": "V1CleanPodPolicy",
        "slots_per_worker": "int",
        "launcher": "V1KFReplica",
        "worker": "V1KFReplica",
    }

    attribute_map = {
        "kind": "kind",
        "clean_pod_policy": "cleanPodPolicy",
        "slots_per_worker": "slots_per_worker",
        "launcher": "launcher",
        "worker": "worker",
    }

    def __init__(
        self,
        kind="mpi_job",
        clean_pod_policy=None,
        slots_per_worker=None,
        launcher=None,
        worker=None,
    ):  # noqa: E501
        """V1MPIJob - a model defined in Swagger"""  # noqa: E501

        self._kind = None
        self._clean_pod_policy = None
        self._slots_per_worker = None
        self._launcher = None
        self._worker = None
        self.discriminator = None

        if kind is not None:
            self.kind = kind
        if clean_pod_policy is not None:
            self.clean_pod_policy = clean_pod_policy
        if slots_per_worker is not None:
            self.slots_per_worker = slots_per_worker
        if launcher is not None:
            self.launcher = launcher
        if worker is not None:
            self.worker = worker

    @property
    def kind(self):
        """Gets the kind of this V1MPIJob.  # noqa: E501


        :return: The kind of this V1MPIJob.  # noqa: E501
        :rtype: str
        """
        return self._kind

    @kind.setter
    def kind(self, kind):
        """Sets the kind of this V1MPIJob.


        :param kind: The kind of this V1MPIJob.  # noqa: E501
        :type: str
        """

        self._kind = kind

    @property
    def clean_pod_policy(self):
        """Gets the clean_pod_policy of this V1MPIJob.  # noqa: E501


        :return: The clean_pod_policy of this V1MPIJob.  # noqa: E501
        :rtype: V1CleanPodPolicy
        """
        return self._clean_pod_policy

    @clean_pod_policy.setter
    def clean_pod_policy(self, clean_pod_policy):
        """Sets the clean_pod_policy of this V1MPIJob.


        :param clean_pod_policy: The clean_pod_policy of this V1MPIJob.  # noqa: E501
        :type: V1CleanPodPolicy
        """

        self._clean_pod_policy = clean_pod_policy

    @property
    def slots_per_worker(self):
        """Gets the slots_per_worker of this V1MPIJob.  # noqa: E501


        :return: The slots_per_worker of this V1MPIJob.  # noqa: E501
        :rtype: int
        """
        return self._slots_per_worker

    @slots_per_worker.setter
    def slots_per_worker(self, slots_per_worker):
        """Sets the slots_per_worker of this V1MPIJob.


        :param slots_per_worker: The slots_per_worker of this V1MPIJob.  # noqa: E501
        :type: int
        """

        self._slots_per_worker = slots_per_worker

    @property
    def launcher(self):
        """Gets the launcher of this V1MPIJob.  # noqa: E501


        :return: The launcher of this V1MPIJob.  # noqa: E501
        :rtype: V1KFReplica
        """
        return self._launcher

    @launcher.setter
    def launcher(self, launcher):
        """Sets the launcher of this V1MPIJob.


        :param launcher: The launcher of this V1MPIJob.  # noqa: E501
        :type: V1KFReplica
        """

        self._launcher = launcher

    @property
    def worker(self):
        """Gets the worker of this V1MPIJob.  # noqa: E501


        :return: The worker of this V1MPIJob.  # noqa: E501
        :rtype: V1KFReplica
        """
        return self._worker

    @worker.setter
    def worker(self, worker):
        """Sets the worker of this V1MPIJob.


        :param worker: The worker of this V1MPIJob.  # noqa: E501
        :type: V1KFReplica
        """

        self._worker = worker

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.swagger_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(
                    map(lambda x: x.to_dict() if hasattr(x, "to_dict") else x, value)
                )
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(
                    map(
                        lambda item: (item[0], item[1].to_dict())
                        if hasattr(item[1], "to_dict")
                        else item,
                        value.items(),
                    )
                )
            else:
                result[attr] = value
        if issubclass(V1MPIJob, dict):
            for key, value in self.items():
                result[key] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, V1MPIJob):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
