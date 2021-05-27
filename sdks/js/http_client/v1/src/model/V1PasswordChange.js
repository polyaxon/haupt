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
 * The V1PasswordChange model module.
 * @module model/V1PasswordChange
 * @version 1.9.2
 */
class V1PasswordChange {
    /**
     * Constructs a new <code>V1PasswordChange</code>.
     * @alias module:model/V1PasswordChange
     */
    constructor() { 
        
        V1PasswordChange.initialize(this);
    }

    /**
     * Initializes the fields of this object.
     * This method is used by the constructors of any subclasses, in order to implement multiple inheritance (mix-ins).
     * Only for internal use.
     */
    static initialize(obj) { 
    }

    /**
     * Constructs a <code>V1PasswordChange</code> from a plain JavaScript object, optionally creating a new instance.
     * Copies all relevant properties from <code>data</code> to <code>obj</code> if supplied or a new instance if not.
     * @param {Object} data The plain JavaScript object bearing properties of interest.
     * @param {module:model/V1PasswordChange} obj Optional instance to populate.
     * @return {module:model/V1PasswordChange} The populated <code>V1PasswordChange</code> instance.
     */
    static constructFromObject(data, obj) {
        if (data) {
            obj = obj || new V1PasswordChange();

            if (data.hasOwnProperty('old_password')) {
                obj['old_password'] = ApiClient.convertToType(data['old_password'], 'String');
            }
            if (data.hasOwnProperty('new_password1')) {
                obj['new_password1'] = ApiClient.convertToType(data['new_password1'], 'String');
            }
            if (data.hasOwnProperty('new_password2')) {
                obj['new_password2'] = ApiClient.convertToType(data['new_password2'], 'String');
            }
        }
        return obj;
    }


}

/**
 * @member {String} old_password
 */
V1PasswordChange.prototype['old_password'] = undefined;

/**
 * @member {String} new_password1
 */
V1PasswordChange.prototype['new_password1'] = undefined;

/**
 * @member {String} new_password2
 */
V1PasswordChange.prototype['new_password2'] = undefined;






export default V1PasswordChange;

