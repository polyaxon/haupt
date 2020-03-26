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


class V1Spark(object):
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
        "connections": "list[str]",
        "volumes": "list[V1Volume]",
        "type": "V1SparkType",
        "spark_version": "str",
        "python_version": "str",
        "deploy_mode": "SparkDeployMode",
        "main_class": "str",
        "main_application_file": "str",
        "arguments": "list[str]",
        "hadoop_conf": "dict(str, str)",
        "spark_conf": "dict(str, str)",
        "spark_config_map": "str",
        "hadoop_config_map": "str",
        "executor": "V1SparkReplica",
        "driver": "V1SparkReplica",
    }

    attribute_map = {
        "kind": "kind",
        "connections": "connections",
        "volumes": "volumes",
        "type": "type",
        "spark_version": "spark_version",
        "python_version": "python_version",
        "deploy_mode": "deploy_mode",
        "main_class": "main_class",
        "main_application_file": "main_application_file",
        "arguments": "arguments",
        "hadoop_conf": "hadoop_conf",
        "spark_conf": "spark_conf",
        "spark_config_map": "spark_config_map",
        "hadoop_config_map": "hadoop_config_map",
        "executor": "executor",
        "driver": "driver",
    }

    def __init__(
        self,
        kind="spark",
        connections=None,
        volumes=None,
        type=None,
        spark_version=None,
        python_version=None,
        deploy_mode=None,
        main_class=None,
        main_application_file=None,
        arguments=None,
        hadoop_conf=None,
        spark_conf=None,
        spark_config_map=None,
        hadoop_config_map=None,
        executor=None,
        driver=None,
    ):  # noqa: E501
        """V1Spark - a model defined in Swagger"""  # noqa: E501

        self._kind = None
        self._connections = None
        self._volumes = None
        self._type = None
        self._spark_version = None
        self._python_version = None
        self._deploy_mode = None
        self._main_class = None
        self._main_application_file = None
        self._arguments = None
        self._hadoop_conf = None
        self._spark_conf = None
        self._spark_config_map = None
        self._hadoop_config_map = None
        self._executor = None
        self._driver = None
        self.discriminator = None

        if kind is not None:
            self.kind = kind
        if connections is not None:
            self.connections = connections
        if volumes is not None:
            self.volumes = volumes
        if type is not None:
            self.type = type
        if spark_version is not None:
            self.spark_version = spark_version
        if python_version is not None:
            self.python_version = python_version
        if deploy_mode is not None:
            self.deploy_mode = deploy_mode
        if main_class is not None:
            self.main_class = main_class
        if main_application_file is not None:
            self.main_application_file = main_application_file
        if arguments is not None:
            self.arguments = arguments
        if hadoop_conf is not None:
            self.hadoop_conf = hadoop_conf
        if spark_conf is not None:
            self.spark_conf = spark_conf
        if spark_config_map is not None:
            self.spark_config_map = spark_config_map
        if hadoop_config_map is not None:
            self.hadoop_config_map = hadoop_config_map
        if executor is not None:
            self.executor = executor
        if driver is not None:
            self.driver = driver

    @property
    def kind(self):
        """Gets the kind of this V1Spark.  # noqa: E501


        :return: The kind of this V1Spark.  # noqa: E501
        :rtype: str
        """
        return self._kind

    @kind.setter
    def kind(self, kind):
        """Sets the kind of this V1Spark.


        :param kind: The kind of this V1Spark.  # noqa: E501
        :type: str
        """

        self._kind = kind

    @property
    def connections(self):
        """Gets the connections of this V1Spark.  # noqa: E501


        :return: The connections of this V1Spark.  # noqa: E501
        :rtype: list[str]
        """
        return self._connections

    @connections.setter
    def connections(self, connections):
        """Sets the connections of this V1Spark.


        :param connections: The connections of this V1Spark.  # noqa: E501
        :type: list[str]
        """

        self._connections = connections

    @property
    def volumes(self):
        """Gets the volumes of this V1Spark.  # noqa: E501

        Volumes is a list of volumes that can be mounted.  # noqa: E501

        :return: The volumes of this V1Spark.  # noqa: E501
        :rtype: list[V1Volume]
        """
        return self._volumes

    @volumes.setter
    def volumes(self, volumes):
        """Sets the volumes of this V1Spark.

        Volumes is a list of volumes that can be mounted.  # noqa: E501

        :param volumes: The volumes of this V1Spark.  # noqa: E501
        :type: list[V1Volume]
        """

        self._volumes = volumes

    @property
    def type(self):
        """Gets the type of this V1Spark.  # noqa: E501

        Type tells the type of the Spark application.  # noqa: E501

        :return: The type of this V1Spark.  # noqa: E501
        :rtype: V1SparkType
        """
        return self._type

    @type.setter
    def type(self, type):
        """Sets the type of this V1Spark.

        Type tells the type of the Spark application.  # noqa: E501

        :param type: The type of this V1Spark.  # noqa: E501
        :type: V1SparkType
        """

        self._type = type

    @property
    def spark_version(self):
        """Gets the spark_version of this V1Spark.  # noqa: E501

        Spark version is the version of Spark the application uses.  # noqa: E501

        :return: The spark_version of this V1Spark.  # noqa: E501
        :rtype: str
        """
        return self._spark_version

    @spark_version.setter
    def spark_version(self, spark_version):
        """Sets the spark_version of this V1Spark.

        Spark version is the version of Spark the application uses.  # noqa: E501

        :param spark_version: The spark_version of this V1Spark.  # noqa: E501
        :type: str
        """

        self._spark_version = spark_version

    @property
    def python_version(self):
        """Gets the python_version of this V1Spark.  # noqa: E501

        Spark version is the version of Spark the application uses.  # noqa: E501

        :return: The python_version of this V1Spark.  # noqa: E501
        :rtype: str
        """
        return self._python_version

    @python_version.setter
    def python_version(self, python_version):
        """Sets the python_version of this V1Spark.

        Spark version is the version of Spark the application uses.  # noqa: E501

        :param python_version: The python_version of this V1Spark.  # noqa: E501
        :type: str
        """

        self._python_version = python_version

    @property
    def deploy_mode(self):
        """Gets the deploy_mode of this V1Spark.  # noqa: E501

        Mode is the deployment mode of the Spark application.  # noqa: E501

        :return: The deploy_mode of this V1Spark.  # noqa: E501
        :rtype: SparkDeployMode
        """
        return self._deploy_mode

    @deploy_mode.setter
    def deploy_mode(self, deploy_mode):
        """Sets the deploy_mode of this V1Spark.

        Mode is the deployment mode of the Spark application.  # noqa: E501

        :param deploy_mode: The deploy_mode of this V1Spark.  # noqa: E501
        :type: SparkDeployMode
        """

        self._deploy_mode = deploy_mode

    @property
    def main_class(self):
        """Gets the main_class of this V1Spark.  # noqa: E501

        MainClass is the fully-qualified main class of the Spark application. This only applies to Java/Scala Spark applications.  # noqa: E501

        :return: The main_class of this V1Spark.  # noqa: E501
        :rtype: str
        """
        return self._main_class

    @main_class.setter
    def main_class(self, main_class):
        """Sets the main_class of this V1Spark.

        MainClass is the fully-qualified main class of the Spark application. This only applies to Java/Scala Spark applications.  # noqa: E501

        :param main_class: The main_class of this V1Spark.  # noqa: E501
        :type: str
        """

        self._main_class = main_class

    @property
    def main_application_file(self):
        """Gets the main_application_file of this V1Spark.  # noqa: E501

        MainFile is the path to a bundled JAR, Python, or R file of the application.  # noqa: E501

        :return: The main_application_file of this V1Spark.  # noqa: E501
        :rtype: str
        """
        return self._main_application_file

    @main_application_file.setter
    def main_application_file(self, main_application_file):
        """Sets the main_application_file of this V1Spark.

        MainFile is the path to a bundled JAR, Python, or R file of the application.  # noqa: E501

        :param main_application_file: The main_application_file of this V1Spark.  # noqa: E501
        :type: str
        """

        self._main_application_file = main_application_file

    @property
    def arguments(self):
        """Gets the arguments of this V1Spark.  # noqa: E501

        Arguments is a list of arguments to be passed to the application.  # noqa: E501

        :return: The arguments of this V1Spark.  # noqa: E501
        :rtype: list[str]
        """
        return self._arguments

    @arguments.setter
    def arguments(self, arguments):
        """Sets the arguments of this V1Spark.

        Arguments is a list of arguments to be passed to the application.  # noqa: E501

        :param arguments: The arguments of this V1Spark.  # noqa: E501
        :type: list[str]
        """

        self._arguments = arguments

    @property
    def hadoop_conf(self):
        """Gets the hadoop_conf of this V1Spark.  # noqa: E501

        HadoopConf carries user-specified Hadoop configuration properties as they would use the  the \"--conf\" option in spark-submit.  The SparkApplication controller automatically adds prefix \"spark.hadoop.\" to Hadoop configuration properties.  # noqa: E501

        :return: The hadoop_conf of this V1Spark.  # noqa: E501
        :rtype: dict(str, str)
        """
        return self._hadoop_conf

    @hadoop_conf.setter
    def hadoop_conf(self, hadoop_conf):
        """Sets the hadoop_conf of this V1Spark.

        HadoopConf carries user-specified Hadoop configuration properties as they would use the  the \"--conf\" option in spark-submit.  The SparkApplication controller automatically adds prefix \"spark.hadoop.\" to Hadoop configuration properties.  # noqa: E501

        :param hadoop_conf: The hadoop_conf of this V1Spark.  # noqa: E501
        :type: dict(str, str)
        """

        self._hadoop_conf = hadoop_conf

    @property
    def spark_conf(self):
        """Gets the spark_conf of this V1Spark.  # noqa: E501

        HadoopConf carries user-specified Hadoop configuration properties as they would use the  the \"--conf\" option in spark-submit.  The SparkApplication controller automatically adds prefix \"spark.hadoop.\" to Hadoop configuration properties.  # noqa: E501

        :return: The spark_conf of this V1Spark.  # noqa: E501
        :rtype: dict(str, str)
        """
        return self._spark_conf

    @spark_conf.setter
    def spark_conf(self, spark_conf):
        """Sets the spark_conf of this V1Spark.

        HadoopConf carries user-specified Hadoop configuration properties as they would use the  the \"--conf\" option in spark-submit.  The SparkApplication controller automatically adds prefix \"spark.hadoop.\" to Hadoop configuration properties.  # noqa: E501

        :param spark_conf: The spark_conf of this V1Spark.  # noqa: E501
        :type: dict(str, str)
        """

        self._spark_conf = spark_conf

    @property
    def spark_config_map(self):
        """Gets the spark_config_map of this V1Spark.  # noqa: E501

        SparkConfigMap carries the name of the ConfigMap containing Spark configuration files such as log4j.properties. The controller will add environment variable SPARK_CONF_DIR to the path where the ConfigMap is mounted to.  # noqa: E501

        :return: The spark_config_map of this V1Spark.  # noqa: E501
        :rtype: str
        """
        return self._spark_config_map

    @spark_config_map.setter
    def spark_config_map(self, spark_config_map):
        """Sets the spark_config_map of this V1Spark.

        SparkConfigMap carries the name of the ConfigMap containing Spark configuration files such as log4j.properties. The controller will add environment variable SPARK_CONF_DIR to the path where the ConfigMap is mounted to.  # noqa: E501

        :param spark_config_map: The spark_config_map of this V1Spark.  # noqa: E501
        :type: str
        """

        self._spark_config_map = spark_config_map

    @property
    def hadoop_config_map(self):
        """Gets the hadoop_config_map of this V1Spark.  # noqa: E501

        HadoopConfigMap carries the name of the ConfigMap containing Hadoop configuration files such as core-site.xml. The controller will add environment variable HADOOP_CONF_DIR to the path where the ConfigMap is mounted to.  # noqa: E501

        :return: The hadoop_config_map of this V1Spark.  # noqa: E501
        :rtype: str
        """
        return self._hadoop_config_map

    @hadoop_config_map.setter
    def hadoop_config_map(self, hadoop_config_map):
        """Sets the hadoop_config_map of this V1Spark.

        HadoopConfigMap carries the name of the ConfigMap containing Hadoop configuration files such as core-site.xml. The controller will add environment variable HADOOP_CONF_DIR to the path where the ConfigMap is mounted to.  # noqa: E501

        :param hadoop_config_map: The hadoop_config_map of this V1Spark.  # noqa: E501
        :type: str
        """

        self._hadoop_config_map = hadoop_config_map

    @property
    def executor(self):
        """Gets the executor of this V1Spark.  # noqa: E501


        :return: The executor of this V1Spark.  # noqa: E501
        :rtype: V1SparkReplica
        """
        return self._executor

    @executor.setter
    def executor(self, executor):
        """Sets the executor of this V1Spark.


        :param executor: The executor of this V1Spark.  # noqa: E501
        :type: V1SparkReplica
        """

        self._executor = executor

    @property
    def driver(self):
        """Gets the driver of this V1Spark.  # noqa: E501


        :return: The driver of this V1Spark.  # noqa: E501
        :rtype: V1SparkReplica
        """
        return self._driver

    @driver.setter
    def driver(self, driver):
        """Sets the driver of this V1Spark.


        :param driver: The driver of this V1Spark.  # noqa: E501
        :type: V1SparkReplica
        """

        self._driver = driver

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
        if issubclass(V1Spark, dict):
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
        if not isinstance(other, V1Spark):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
