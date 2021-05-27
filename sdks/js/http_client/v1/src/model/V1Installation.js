// Copyright 2018-2021 Polyaxon, Inc.
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

/**
 * Polyaxon SDKs and REST API specification.
 * Polyaxon SDKs and REST API specification.
 *
 * The version of the OpenAPI document: 1.9.2
 * Contact: contact@polyaxon.com
 *
 * NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).
 * https://openapi-generator.tech
 * Do not edit the class manually.
 *
 */

import ApiClient from '../ApiClient';

/**
 * The V1Installation model module.
 * @module model/V1Installation
 * @version 1.9.2
 */
class V1Installation {
    /**
     * Constructs a new <code>V1Installation</code>.
     * @alias module:model/V1Installation
     */
    constructor() { 
        
        V1Installation.initialize(this);
    }

    /**
     * Initializes the fields of this object.
     * This method is used by the constructors of any subclasses, in order to implement multiple inheritance (mix-ins).
     * Only for internal use.
     */
    static initialize(obj) { 
    }

    /**
     * Constructs a <code>V1Installation</code> from a plain JavaScript object, optionally creating a new instance.
     * Copies all relevant properties from <code>data</code> to <code>obj</code> if supplied or a new instance if not.
     * @param {Object} data The plain JavaScript object bearing properties of interest.
     * @param {module:model/V1Installation} obj Optional instance to populate.
     * @return {module:model/V1Installation} The populated <code>V1Installation</code> instance.
     */
    static constructFromObject(data, obj) {
        if (data) {
            obj = obj || new V1Installation();

            if (data.hasOwnProperty('key')) {
                obj['key'] = ApiClient.convertToType(data['key'], 'String');
            }
            if (data.hasOwnProperty('version')) {
                obj['version'] = ApiClient.convertToType(data['version'], 'String');
            }
            if (data.hasOwnProperty('dist')) {
                obj['dist'] = ApiClient.convertToType(data['dist'], 'String');
            }
            if (data.hasOwnProperty('host')) {
                obj['host'] = ApiClient.convertToType(data['host'], 'String');
            }
            if (data.hasOwnProperty('hmac')) {
                obj['hmac'] = ApiClient.convertToType(data['hmac'], 'String');
            }
            if (data.hasOwnProperty('auth')) {
                obj['auth'] = ApiClient.convertToType(data['auth'], ['String']);
            }
        }
        return obj;
    }


}

/**
 * @member {String} key
 */
V1Installation.prototype['key'] = undefined;

/**
 * @member {String} version
 */
V1Installation.prototype['version'] = undefined;

/**
 * @member {String} dist
 */
V1Installation.prototype['dist'] = undefined;

/**
 * @member {String} host
 */
V1Installation.prototype['host'] = undefined;

/**
 * @member {String} hmac
 */
V1Installation.prototype['hmac'] = undefined;

/**
 * @member {Array.<String>} auth
 */
V1Installation.prototype['auth'] = undefined;






export default V1Installation;

