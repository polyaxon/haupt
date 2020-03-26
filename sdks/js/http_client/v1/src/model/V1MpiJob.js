// Copyright 2018-2020 Polyaxon, Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

/*
 * Polyaxon SDKs and REST API specification.
 * Polyaxon SDKs and REST API specification.
 *
 * OpenAPI spec version: 1.0.71
 * Contact: contact@polyaxon.com
 *
 * NOTE: This class is auto generated by the swagger code generator program.
 * https://github.com/swagger-api/swagger-codegen.git
 *
 * Swagger Codegen version: 2.4.10
 *
 * Do not edit the class manually.
 *
 */

(function(root, factory) {
  if (typeof define === 'function' && define.amd) {
    // AMD. Register as an anonymous module.
    define(['ApiClient', 'model/V1CleanPodPolicy', 'model/V1KFReplica'], factory);
  } else if (typeof module === 'object' && module.exports) {
    // CommonJS-like environments that support module.exports, like Node.
    module.exports = factory(require('../ApiClient'), require('./V1CleanPodPolicy'), require('./V1KFReplica'));
  } else {
    // Browser globals (root is window)
    if (!root.PolyaxonSdk) {
      root.PolyaxonSdk = {};
    }
    root.PolyaxonSdk.V1MPIJob = factory(root.PolyaxonSdk.ApiClient, root.PolyaxonSdk.V1CleanPodPolicy, root.PolyaxonSdk.V1KFReplica);
  }
}(this, function(ApiClient, V1CleanPodPolicy, V1KFReplica) {
  'use strict';

  /**
   * The V1MPIJob model module.
   * @module model/V1MPIJob
   * @version 1.0.71
   */

  /**
   * Constructs a new <code>V1MPIJob</code>.
   * @alias module:model/V1MPIJob
   * @class
   */
  var exports = function() {
  };

  /**
   * Constructs a <code>V1MPIJob</code> from a plain JavaScript object, optionally creating a new instance.
   * Copies all relevant properties from <code>data</code> to <code>obj</code> if supplied or a new instance if not.
   * @param {Object} data The plain JavaScript object bearing properties of interest.
   * @param {module:model/V1MPIJob} obj Optional instance to populate.
   * @return {module:model/V1MPIJob} The populated <code>V1MPIJob</code> instance.
   */
  exports.constructFromObject = function(data, obj) {
    if (data) {
      obj = obj || new exports();
      if (data.hasOwnProperty('kind'))
        obj.kind = ApiClient.convertToType(data['kind'], 'String');
      if (data.hasOwnProperty('cleanPodPolicy'))
        obj.cleanPodPolicy = V1CleanPodPolicy.constructFromObject(data['cleanPodPolicy']);
      if (data.hasOwnProperty('slots_per_worker'))
        obj.slots_per_worker = ApiClient.convertToType(data['slots_per_worker'], 'Number');
      if (data.hasOwnProperty('launcher'))
        obj.launcher = V1KFReplica.constructFromObject(data['launcher']);
      if (data.hasOwnProperty('worker'))
        obj.worker = V1KFReplica.constructFromObject(data['worker']);
    }
    return obj;
  }

  /**
   * @member {String} kind
   * @default 'mpi_job'
   */
  exports.prototype.kind = 'mpi_job';

  /**
   * @member {module:model/V1CleanPodPolicy} cleanPodPolicy
   */
  exports.prototype.cleanPodPolicy = undefined;

  /**
   * @member {Number} slots_per_worker
   */
  exports.prototype.slots_per_worker = undefined;

  /**
   * @member {module:model/V1KFReplica} launcher
   */
  exports.prototype.launcher = undefined;

  /**
   * @member {module:model/V1KFReplica} worker
   */
  exports.prototype.worker = undefined;

  return exports;

}));
