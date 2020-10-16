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

// Code generated by go-swagger; DO NOT EDIT.

package component_hub_v1

// This file was generated by the swagger tool.
// Editing this file might prove futile when you re-run the swagger generate command

import (
	"fmt"
	"io"

	"github.com/go-openapi/runtime"
	"github.com/go-openapi/strfmt"

	"github.com/polyaxon/polyaxon/sdks/go/http_client/v1/service_model"
)

// DeleteComponentHubReader is a Reader for the DeleteComponentHub structure.
type DeleteComponentHubReader struct {
	formats strfmt.Registry
}

// ReadResponse reads a server response into the received o.
func (o *DeleteComponentHubReader) ReadResponse(response runtime.ClientResponse, consumer runtime.Consumer) (interface{}, error) {
	switch response.Code() {
	case 200:
		result := NewDeleteComponentHubOK()
		if err := result.readResponse(response, consumer, o.formats); err != nil {
			return nil, err
		}
		return result, nil
	case 204:
		result := NewDeleteComponentHubNoContent()
		if err := result.readResponse(response, consumer, o.formats); err != nil {
			return nil, err
		}
		return result, nil
	case 403:
		result := NewDeleteComponentHubForbidden()
		if err := result.readResponse(response, consumer, o.formats); err != nil {
			return nil, err
		}
		return nil, result
	case 404:
		result := NewDeleteComponentHubNotFound()
		if err := result.readResponse(response, consumer, o.formats); err != nil {
			return nil, err
		}
		return nil, result
	default:
		result := NewDeleteComponentHubDefault(response.Code())
		if err := result.readResponse(response, consumer, o.formats); err != nil {
			return nil, err
		}
		if response.Code()/100 == 2 {
			return result, nil
		}
		return nil, result
	}
}

// NewDeleteComponentHubOK creates a DeleteComponentHubOK with default headers values
func NewDeleteComponentHubOK() *DeleteComponentHubOK {
	return &DeleteComponentHubOK{}
}

/*DeleteComponentHubOK handles this case with default header values.

A successful response.
*/
type DeleteComponentHubOK struct {
}

func (o *DeleteComponentHubOK) Error() string {
	return fmt.Sprintf("[DELETE /api/v1/orgs/{owner}/components/{uuid}][%d] deleteComponentHubOK ", 200)
}

func (o *DeleteComponentHubOK) readResponse(response runtime.ClientResponse, consumer runtime.Consumer, formats strfmt.Registry) error {

	return nil
}

// NewDeleteComponentHubNoContent creates a DeleteComponentHubNoContent with default headers values
func NewDeleteComponentHubNoContent() *DeleteComponentHubNoContent {
	return &DeleteComponentHubNoContent{}
}

/*DeleteComponentHubNoContent handles this case with default header values.

No content.
*/
type DeleteComponentHubNoContent struct {
	Payload interface{}
}

func (o *DeleteComponentHubNoContent) Error() string {
	return fmt.Sprintf("[DELETE /api/v1/orgs/{owner}/components/{uuid}][%d] deleteComponentHubNoContent  %+v", 204, o.Payload)
}

func (o *DeleteComponentHubNoContent) GetPayload() interface{} {
	return o.Payload
}

func (o *DeleteComponentHubNoContent) readResponse(response runtime.ClientResponse, consumer runtime.Consumer, formats strfmt.Registry) error {

	// response payload
	if err := consumer.Consume(response.Body(), &o.Payload); err != nil && err != io.EOF {
		return err
	}

	return nil
}

// NewDeleteComponentHubForbidden creates a DeleteComponentHubForbidden with default headers values
func NewDeleteComponentHubForbidden() *DeleteComponentHubForbidden {
	return &DeleteComponentHubForbidden{}
}

/*DeleteComponentHubForbidden handles this case with default header values.

You don't have permission to access the resource.
*/
type DeleteComponentHubForbidden struct {
	Payload interface{}
}

func (o *DeleteComponentHubForbidden) Error() string {
	return fmt.Sprintf("[DELETE /api/v1/orgs/{owner}/components/{uuid}][%d] deleteComponentHubForbidden  %+v", 403, o.Payload)
}

func (o *DeleteComponentHubForbidden) GetPayload() interface{} {
	return o.Payload
}

func (o *DeleteComponentHubForbidden) readResponse(response runtime.ClientResponse, consumer runtime.Consumer, formats strfmt.Registry) error {

	// response payload
	if err := consumer.Consume(response.Body(), &o.Payload); err != nil && err != io.EOF {
		return err
	}

	return nil
}

// NewDeleteComponentHubNotFound creates a DeleteComponentHubNotFound with default headers values
func NewDeleteComponentHubNotFound() *DeleteComponentHubNotFound {
	return &DeleteComponentHubNotFound{}
}

/*DeleteComponentHubNotFound handles this case with default header values.

Resource does not exist.
*/
type DeleteComponentHubNotFound struct {
	Payload interface{}
}

func (o *DeleteComponentHubNotFound) Error() string {
	return fmt.Sprintf("[DELETE /api/v1/orgs/{owner}/components/{uuid}][%d] deleteComponentHubNotFound  %+v", 404, o.Payload)
}

func (o *DeleteComponentHubNotFound) GetPayload() interface{} {
	return o.Payload
}

func (o *DeleteComponentHubNotFound) readResponse(response runtime.ClientResponse, consumer runtime.Consumer, formats strfmt.Registry) error {

	// response payload
	if err := consumer.Consume(response.Body(), &o.Payload); err != nil && err != io.EOF {
		return err
	}

	return nil
}

// NewDeleteComponentHubDefault creates a DeleteComponentHubDefault with default headers values
func NewDeleteComponentHubDefault(code int) *DeleteComponentHubDefault {
	return &DeleteComponentHubDefault{
		_statusCode: code,
	}
}

/*DeleteComponentHubDefault handles this case with default header values.

An unexpected error response
*/
type DeleteComponentHubDefault struct {
	_statusCode int

	Payload *service_model.RuntimeError
}

// Code gets the status code for the delete component hub default response
func (o *DeleteComponentHubDefault) Code() int {
	return o._statusCode
}

func (o *DeleteComponentHubDefault) Error() string {
	return fmt.Sprintf("[DELETE /api/v1/orgs/{owner}/components/{uuid}][%d] DeleteComponentHub default  %+v", o._statusCode, o.Payload)
}

func (o *DeleteComponentHubDefault) GetPayload() *service_model.RuntimeError {
	return o.Payload
}

func (o *DeleteComponentHubDefault) readResponse(response runtime.ClientResponse, consumer runtime.Consumer, formats strfmt.Registry) error {

	o.Payload = new(service_model.RuntimeError)

	// response payload
	if err := consumer.Consume(response.Body(), o.Payload); err != nil && err != io.EOF {
		return err
	}

	return nil
}
