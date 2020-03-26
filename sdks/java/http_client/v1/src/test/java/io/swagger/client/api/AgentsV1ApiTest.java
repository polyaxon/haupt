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
 * Do not edit the class manually.
 */


package io.swagger.client.api;

import io.swagger.client.ApiException;
import io.swagger.client.model.RuntimeError;
import io.swagger.client.model.V1Agent;
import io.swagger.client.model.V1AgentStateResponse;
import io.swagger.client.model.V1AgentStatusBodyRequest;
import io.swagger.client.model.V1ListAgentsResponse;
import io.swagger.client.model.V1Status;
import org.junit.Test;
import org.junit.Ignore;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * API tests for AgentsV1Api
 */
@Ignore
public class AgentsV1ApiTest {

    private final AgentsV1Api api = new AgentsV1Api();

    
    /**
     * Create run profile
     *
     * 
     *
     * @throws ApiException
     *          if the Api call fails
     */
    @Test
    public void createAgentTest() throws ApiException {
        String owner = null;
        V1Agent body = null;
        V1Agent response = api.createAgent(owner, body);

        // TODO: test validations
    }
    
    /**
     * 
     *
     * 
     *
     * @throws ApiException
     *          if the Api call fails
     */
    @Test
    public void createAgentStatusTest() throws ApiException {
        String owner = null;
        String uuid = null;
        V1AgentStatusBodyRequest body = null;
        V1Status response = api.createAgentStatus(owner, uuid, body);

        // TODO: test validations
    }
    
    /**
     * Delete run profile
     *
     * 
     *
     * @throws ApiException
     *          if the Api call fails
     */
    @Test
    public void deleteAgentTest() throws ApiException {
        String owner = null;
        String uuid = null;
        api.deleteAgent(owner, uuid);

        // TODO: test validations
    }
    
    /**
     * Get run profile
     *
     * 
     *
     * @throws ApiException
     *          if the Api call fails
     */
    @Test
    public void getAgentTest() throws ApiException {
        String owner = null;
        String uuid = null;
        V1Agent response = api.getAgent(owner, uuid);

        // TODO: test validations
    }
    
    /**
     * 
     *
     * 
     *
     * @throws ApiException
     *          if the Api call fails
     */
    @Test
    public void getAgentStateTest() throws ApiException {
        String owner = null;
        String uuid = null;
        V1AgentStateResponse response = api.getAgentState(owner, uuid);

        // TODO: test validations
    }
    
    /**
     * 
     *
     * 
     *
     * @throws ApiException
     *          if the Api call fails
     */
    @Test
    public void getAgentStatusesTest() throws ApiException {
        String owner = null;
        String uuid = null;
        V1Status response = api.getAgentStatuses(owner, uuid);

        // TODO: test validations
    }
    
    /**
     * List run profiles names
     *
     * 
     *
     * @throws ApiException
     *          if the Api call fails
     */
    @Test
    public void listAgentNamesTest() throws ApiException {
        String owner = null;
        Integer offset = null;
        Integer limit = null;
        String sort = null;
        String query = null;
        V1ListAgentsResponse response = api.listAgentNames(owner, offset, limit, sort, query);

        // TODO: test validations
    }
    
    /**
     * List run profiles
     *
     * 
     *
     * @throws ApiException
     *          if the Api call fails
     */
    @Test
    public void listAgentsTest() throws ApiException {
        String owner = null;
        Integer offset = null;
        Integer limit = null;
        String sort = null;
        String query = null;
        V1ListAgentsResponse response = api.listAgents(owner, offset, limit, sort, query);

        // TODO: test validations
    }
    
    /**
     * Patch run profile
     *
     * 
     *
     * @throws ApiException
     *          if the Api call fails
     */
    @Test
    public void patchAgentTest() throws ApiException {
        String owner = null;
        String agentUuid = null;
        V1Agent body = null;
        V1Agent response = api.patchAgent(owner, agentUuid, body);

        // TODO: test validations
    }
    
    /**
     * 
     *
     * 
     *
     * @throws ApiException
     *          if the Api call fails
     */
    @Test
    public void syncAgentTest() throws ApiException {
        String owner = null;
        String agentUuid = null;
        V1Agent body = null;
        api.syncAgent(owner, agentUuid, body);

        // TODO: test validations
    }
    
    /**
     * Update run profile
     *
     * 
     *
     * @throws ApiException
     *          if the Api call fails
     */
    @Test
    public void updateAgentTest() throws ApiException {
        String owner = null;
        String agentUuid = null;
        V1Agent body = null;
        V1Agent response = api.updateAgent(owner, agentUuid, body);

        // TODO: test validations
    }
    
}
