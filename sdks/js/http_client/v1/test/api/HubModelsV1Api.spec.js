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
    // AMD.
    define(['expect.js', '../../src/index'], factory);
  } else if (typeof module === 'object' && module.exports) {
    // CommonJS-like environments that support module.exports, like Node.
    factory(require('expect.js'), require('../../src/index'));
  } else {
    // Browser globals (root is window)
    factory(root.expect, root.PolyaxonSdk);
  }
}(this, function(expect, PolyaxonSdk) {
  'use strict';

  var instance;

  beforeEach(function() {
    instance = new PolyaxonSdk.HubModelsV1Api();
  });

  describe('(package)', function() {
    describe('HubModelsV1Api', function() {
      describe('createHubModel', function() {
        it('should call createHubModel successfully', function(done) {
          // TODO: uncomment, update parameter values for createHubModel call and complete the assertions
          /*
          var owner = "owner_example";
          var body = new PolyaxonSdk.V1HubModel();
          body.uuid = "";
          body.name = "";
          body.tag = "";
          body.framework = "";
          body.description = "";
          body.tags = [""];
          body.disabled = false;
          body.deleted = false;
          body.created_at = new Date();
          body.updated_at = new Date();

          instance.createHubModel(owner, body, function(error, data, response) {
            if (error) {
              done(error);
              return;
            }
            // TODO: update response assertions
            expect(data).to.be.a(PolyaxonSdk.V1HubModel);
            expect(data.uuid).to.be.a('string');
            expect(data.uuid).to.be("");
            expect(data.name).to.be.a('string');
            expect(data.name).to.be("");
            expect(data.tag).to.be.a('string');
            expect(data.tag).to.be("");
            expect(data.framework).to.be.a('string');
            expect(data.framework).to.be("");
            expect(data.description).to.be.a('string');
            expect(data.description).to.be("");
            {
              let dataCtr = data.tags;
              expect(dataCtr).to.be.an(Array);
              expect(dataCtr).to.not.be.empty();
              for (let p in dataCtr) {
                let data = dataCtr[p];
                expect(data).to.be.a('string');
                expect(data).to.be("");
              }
            }
            expect(data.disabled).to.be.a('boolean');
            expect(data.disabled).to.be(false);
            expect(data.deleted).to.be.a('boolean');
            expect(data.deleted).to.be(false);
            expect(data.created_at).to.be.a(Date);
            expect(data.created_at).to.be(new Date());
            expect(data.updated_at).to.be.a(Date);
            expect(data.updated_at).to.be(new Date());

            done();
          });
          */
          // TODO: uncomment and complete method invocation above, then delete this line and the next:
          done();
        });
      });
      describe('deleteHubModel', function() {
        it('should call deleteHubModel successfully', function(done) {
          // TODO: uncomment, update parameter values for deleteHubModel call
          /*
          var owner = "owner_example";
          var uuid = "uuid_example";

          instance.deleteHubModel(owner, uuid, function(error, data, response) {
            if (error) {
              done(error);
              return;
            }

            done();
          });
          */
          // TODO: uncomment and complete method invocation above, then delete this line and the next:
          done();
        });
      });
      describe('getHubModel', function() {
        it('should call getHubModel successfully', function(done) {
          // TODO: uncomment, update parameter values for getHubModel call and complete the assertions
          /*
          var owner = "owner_example";
          var uuid = "uuid_example";

          instance.getHubModel(owner, uuid, function(error, data, response) {
            if (error) {
              done(error);
              return;
            }
            // TODO: update response assertions
            expect(data).to.be.a(PolyaxonSdk.V1HubModel);
            expect(data.uuid).to.be.a('string');
            expect(data.uuid).to.be("");
            expect(data.name).to.be.a('string');
            expect(data.name).to.be("");
            expect(data.tag).to.be.a('string');
            expect(data.tag).to.be("");
            expect(data.framework).to.be.a('string');
            expect(data.framework).to.be("");
            expect(data.description).to.be.a('string');
            expect(data.description).to.be("");
            {
              let dataCtr = data.tags;
              expect(dataCtr).to.be.an(Array);
              expect(dataCtr).to.not.be.empty();
              for (let p in dataCtr) {
                let data = dataCtr[p];
                expect(data).to.be.a('string');
                expect(data).to.be("");
              }
            }
            expect(data.disabled).to.be.a('boolean');
            expect(data.disabled).to.be(false);
            expect(data.deleted).to.be.a('boolean');
            expect(data.deleted).to.be(false);
            expect(data.created_at).to.be.a(Date);
            expect(data.created_at).to.be(new Date());
            expect(data.updated_at).to.be.a(Date);
            expect(data.updated_at).to.be(new Date());

            done();
          });
          */
          // TODO: uncomment and complete method invocation above, then delete this line and the next:
          done();
        });
      });
      describe('listHubModelNames', function() {
        it('should call listHubModelNames successfully', function(done) {
          // TODO: uncomment, update parameter values for listHubModelNames call and complete the assertions
          /*
          var owner = "owner_example";
          var opts = {};
          opts.offset = 56;
          opts.limit = 56;
          opts.sort = "sort_example";
          opts.query = "query_example";

          instance.listHubModelNames(owner, opts, function(error, data, response) {
            if (error) {
              done(error);
              return;
            }
            // TODO: update response assertions
            expect(data).to.be.a(PolyaxonSdk.V1ListHubModelsResponse);
            expect(data.count).to.be.a('number');
            expect(data.count).to.be(0);
            {
              let dataCtr = data.results;
              expect(dataCtr).to.be.an(Array);
              expect(dataCtr).to.not.be.empty();
              for (let p in dataCtr) {
                let data = dataCtr[p];
                expect(data).to.be.a(PolyaxonSdk.V1HubModel);
                expect(data.uuid).to.be.a('string');
                expect(data.uuid).to.be("");
                expect(data.name).to.be.a('string');
                expect(data.name).to.be("");
                expect(data.tag).to.be.a('string');
                expect(data.tag).to.be("");
                expect(data.framework).to.be.a('string');
                expect(data.framework).to.be("");
                expect(data.description).to.be.a('string');
                expect(data.description).to.be("");
                {
                  let dataCtr = data.tags;
                  expect(dataCtr).to.be.an(Array);
                  expect(dataCtr).to.not.be.empty();
                  for (let p in dataCtr) {
                    let data = dataCtr[p];
                    expect(data).to.be.a('string');
                    expect(data).to.be("");
                  }
                }
                expect(data.disabled).to.be.a('boolean');
                expect(data.disabled).to.be(false);
                expect(data.deleted).to.be.a('boolean');
                expect(data.deleted).to.be(false);
                expect(data.created_at).to.be.a(Date);
                expect(data.created_at).to.be(new Date());
                expect(data.updated_at).to.be.a(Date);
                expect(data.updated_at).to.be(new Date());
              }
            }
            expect(data.previous).to.be.a('string');
            expect(data.previous).to.be("");
            expect(data.next).to.be.a('string');
            expect(data.next).to.be("");

            done();
          });
          */
          // TODO: uncomment and complete method invocation above, then delete this line and the next:
          done();
        });
      });
      describe('listHubModels', function() {
        it('should call listHubModels successfully', function(done) {
          // TODO: uncomment, update parameter values for listHubModels call and complete the assertions
          /*
          var owner = "owner_example";
          var opts = {};
          opts.offset = 56;
          opts.limit = 56;
          opts.sort = "sort_example";
          opts.query = "query_example";

          instance.listHubModels(owner, opts, function(error, data, response) {
            if (error) {
              done(error);
              return;
            }
            // TODO: update response assertions
            expect(data).to.be.a(PolyaxonSdk.V1ListHubModelsResponse);
            expect(data.count).to.be.a('number');
            expect(data.count).to.be(0);
            {
              let dataCtr = data.results;
              expect(dataCtr).to.be.an(Array);
              expect(dataCtr).to.not.be.empty();
              for (let p in dataCtr) {
                let data = dataCtr[p];
                expect(data).to.be.a(PolyaxonSdk.V1HubModel);
                expect(data.uuid).to.be.a('string');
                expect(data.uuid).to.be("");
                expect(data.name).to.be.a('string');
                expect(data.name).to.be("");
                expect(data.tag).to.be.a('string');
                expect(data.tag).to.be("");
                expect(data.framework).to.be.a('string');
                expect(data.framework).to.be("");
                expect(data.description).to.be.a('string');
                expect(data.description).to.be("");
                {
                  let dataCtr = data.tags;
                  expect(dataCtr).to.be.an(Array);
                  expect(dataCtr).to.not.be.empty();
                  for (let p in dataCtr) {
                    let data = dataCtr[p];
                    expect(data).to.be.a('string');
                    expect(data).to.be("");
                  }
                }
                expect(data.disabled).to.be.a('boolean');
                expect(data.disabled).to.be(false);
                expect(data.deleted).to.be.a('boolean');
                expect(data.deleted).to.be(false);
                expect(data.created_at).to.be.a(Date);
                expect(data.created_at).to.be(new Date());
                expect(data.updated_at).to.be.a(Date);
                expect(data.updated_at).to.be(new Date());
              }
            }
            expect(data.previous).to.be.a('string');
            expect(data.previous).to.be("");
            expect(data.next).to.be.a('string');
            expect(data.next).to.be("");

            done();
          });
          */
          // TODO: uncomment and complete method invocation above, then delete this line and the next:
          done();
        });
      });
      describe('patchHubModel', function() {
        it('should call patchHubModel successfully', function(done) {
          // TODO: uncomment, update parameter values for patchHubModel call and complete the assertions
          /*
          var owner = "owner_example";
          var model_uuid = "model_uuid_example";
          var body = new PolyaxonSdk.V1HubModel();
          body.uuid = "";
          body.name = "";
          body.tag = "";
          body.framework = "";
          body.description = "";
          body.tags = [""];
          body.disabled = false;
          body.deleted = false;
          body.created_at = new Date();
          body.updated_at = new Date();

          instance.patchHubModel(owner, model_uuid, body, function(error, data, response) {
            if (error) {
              done(error);
              return;
            }
            // TODO: update response assertions
            expect(data).to.be.a(PolyaxonSdk.V1HubModel);
            expect(data.uuid).to.be.a('string');
            expect(data.uuid).to.be("");
            expect(data.name).to.be.a('string');
            expect(data.name).to.be("");
            expect(data.tag).to.be.a('string');
            expect(data.tag).to.be("");
            expect(data.framework).to.be.a('string');
            expect(data.framework).to.be("");
            expect(data.description).to.be.a('string');
            expect(data.description).to.be("");
            {
              let dataCtr = data.tags;
              expect(dataCtr).to.be.an(Array);
              expect(dataCtr).to.not.be.empty();
              for (let p in dataCtr) {
                let data = dataCtr[p];
                expect(data).to.be.a('string');
                expect(data).to.be("");
              }
            }
            expect(data.disabled).to.be.a('boolean');
            expect(data.disabled).to.be(false);
            expect(data.deleted).to.be.a('boolean');
            expect(data.deleted).to.be(false);
            expect(data.created_at).to.be.a(Date);
            expect(data.created_at).to.be(new Date());
            expect(data.updated_at).to.be.a(Date);
            expect(data.updated_at).to.be(new Date());

            done();
          });
          */
          // TODO: uncomment and complete method invocation above, then delete this line and the next:
          done();
        });
      });
      describe('updateHubModel', function() {
        it('should call updateHubModel successfully', function(done) {
          // TODO: uncomment, update parameter values for updateHubModel call and complete the assertions
          /*
          var owner = "owner_example";
          var model_uuid = "model_uuid_example";
          var body = new PolyaxonSdk.V1HubModel();
          body.uuid = "";
          body.name = "";
          body.tag = "";
          body.framework = "";
          body.description = "";
          body.tags = [""];
          body.disabled = false;
          body.deleted = false;
          body.created_at = new Date();
          body.updated_at = new Date();

          instance.updateHubModel(owner, model_uuid, body, function(error, data, response) {
            if (error) {
              done(error);
              return;
            }
            // TODO: update response assertions
            expect(data).to.be.a(PolyaxonSdk.V1HubModel);
            expect(data.uuid).to.be.a('string');
            expect(data.uuid).to.be("");
            expect(data.name).to.be.a('string');
            expect(data.name).to.be("");
            expect(data.tag).to.be.a('string');
            expect(data.tag).to.be("");
            expect(data.framework).to.be.a('string');
            expect(data.framework).to.be("");
            expect(data.description).to.be.a('string');
            expect(data.description).to.be("");
            {
              let dataCtr = data.tags;
              expect(dataCtr).to.be.an(Array);
              expect(dataCtr).to.not.be.empty();
              for (let p in dataCtr) {
                let data = dataCtr[p];
                expect(data).to.be.a('string');
                expect(data).to.be("");
              }
            }
            expect(data.disabled).to.be.a('boolean');
            expect(data.disabled).to.be(false);
            expect(data.deleted).to.be.a('boolean');
            expect(data.deleted).to.be(false);
            expect(data.created_at).to.be.a(Date);
            expect(data.created_at).to.be(new Date());
            expect(data.updated_at).to.be.a(Date);
            expect(data.updated_at).to.be(new Date());

            done();
          });
          */
          // TODO: uncomment and complete method invocation above, then delete this line and the next:
          done();
        });
      });
    });
  });

}));
