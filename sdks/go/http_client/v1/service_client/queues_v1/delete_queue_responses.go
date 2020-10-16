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

package queues_v1

// This file was generated by the swagger tool.
// Editing this file might prove futile when you re-run the swagger generate command

import (
	"fmt"
	"io"

	"github.com/go-openapi/runtime"
	"github.com/go-openapi/strfmt"

	"github.com/polyaxon/polyaxon/sdks/go/http_client/v1/service_model"
)

// DeleteQueueReader is a Reader for the DeleteQueue structure.
type DeleteQueueReader struct {
	formats strfmt.Registry
}

// ReadResponse reads a server response into the received o.
func (o *DeleteQueueReader) ReadResponse(response runtime.ClientResponse, consumer runtime.Consumer) (interface{}, error) {
	switch response.Code() {
	case 200:
		result := NewDeleteQueueOK()
		if err := result.readResponse(response, consumer, o.formats); err != nil {
			return nil, err
		}
		return result, nil
	case 204:
		result := NewDeleteQueueNoContent()
		if err := result.readResponse(response, consumer, o.formats); err != nil {
			return nil, err
		}
		return result, nil
	case 403:
		result := NewDeleteQueueForbidden()
		if err := result.readResponse(response, consumer, o.formats); err != nil {
			return nil, err
		}
		return nil, result
	case 404:
		result := NewDeleteQueueNotFound()
		if err := result.readResponse(response, consumer, o.formats); err != nil {
			return nil, err
		}
		return nil, result
	default:
		result := NewDeleteQueueDefault(response.Code())
		if err := result.readResponse(response, consumer, o.formats); err != nil {
			return nil, err
		}
		if response.Code()/100 == 2 {
			return result, nil
		}
		return nil, result
	}
}

// NewDeleteQueueOK creates a DeleteQueueOK with default headers values
func NewDeleteQueueOK() *DeleteQueueOK {
	return &DeleteQueueOK{}
}

/*DeleteQueueOK handles this case with default header values.

A successful response.
*/
type DeleteQueueOK struct {
}

func (o *DeleteQueueOK) Error() string {
	return fmt.Sprintf("[DELETE /api/v1/orgs/{owner}/agents/{agent}/queues/{uuid}][%d] deleteQueueOK ", 200)
}

func (o *DeleteQueueOK) readResponse(response runtime.ClientResponse, consumer runtime.Consumer, formats strfmt.Registry) error {

	return nil
}

// NewDeleteQueueNoContent creates a DeleteQueueNoContent with default headers values
func NewDeleteQueueNoContent() *DeleteQueueNoContent {
	return &DeleteQueueNoContent{}
}

/*DeleteQueueNoContent handles this case with default header values.

No content.
*/
type DeleteQueueNoContent struct {
	Payload interface{}
}

func (o *DeleteQueueNoContent) Error() string {
	return fmt.Sprintf("[DELETE /api/v1/orgs/{owner}/agents/{agent}/queues/{uuid}][%d] deleteQueueNoContent  %+v", 204, o.Payload)
}

func (o *DeleteQueueNoContent) GetPayload() interface{} {
	return o.Payload
}

func (o *DeleteQueueNoContent) readResponse(response runtime.ClientResponse, consumer runtime.Consumer, formats strfmt.Registry) error {

	// response payload
	if err := consumer.Consume(response.Body(), &o.Payload); err != nil && err != io.EOF {
		return err
	}

	return nil
}

// NewDeleteQueueForbidden creates a DeleteQueueForbidden with default headers values
func NewDeleteQueueForbidden() *DeleteQueueForbidden {
	return &DeleteQueueForbidden{}
}

/*DeleteQueueForbidden handles this case with default header values.

You don't have permission to access the resource.
*/
type DeleteQueueForbidden struct {
	Payload interface{}
}

func (o *DeleteQueueForbidden) Error() string {
	return fmt.Sprintf("[DELETE /api/v1/orgs/{owner}/agents/{agent}/queues/{uuid}][%d] deleteQueueForbidden  %+v", 403, o.Payload)
}

func (o *DeleteQueueForbidden) GetPayload() interface{} {
	return o.Payload
}

func (o *DeleteQueueForbidden) readResponse(response runtime.ClientResponse, consumer runtime.Consumer, formats strfmt.Registry) error {

	// response payload
	if err := consumer.Consume(response.Body(), &o.Payload); err != nil && err != io.EOF {
		return err
	}

	return nil
}

// NewDeleteQueueNotFound creates a DeleteQueueNotFound with default headers values
func NewDeleteQueueNotFound() *DeleteQueueNotFound {
	return &DeleteQueueNotFound{}
}

/*DeleteQueueNotFound handles this case with default header values.

Resource does not exist.
*/
type DeleteQueueNotFound struct {
	Payload interface{}
}

func (o *DeleteQueueNotFound) Error() string {
	return fmt.Sprintf("[DELETE /api/v1/orgs/{owner}/agents/{agent}/queues/{uuid}][%d] deleteQueueNotFound  %+v", 404, o.Payload)
}

func (o *DeleteQueueNotFound) GetPayload() interface{} {
	return o.Payload
}

func (o *DeleteQueueNotFound) readResponse(response runtime.ClientResponse, consumer runtime.Consumer, formats strfmt.Registry) error {

	// response payload
	if err := consumer.Consume(response.Body(), &o.Payload); err != nil && err != io.EOF {
		return err
	}

	return nil
}

// NewDeleteQueueDefault creates a DeleteQueueDefault with default headers values
func NewDeleteQueueDefault(code int) *DeleteQueueDefault {
	return &DeleteQueueDefault{
		_statusCode: code,
	}
}

/*DeleteQueueDefault handles this case with default header values.

An unexpected error response
*/
type DeleteQueueDefault struct {
	_statusCode int

	Payload *service_model.RuntimeError
}

// Code gets the status code for the delete queue default response
func (o *DeleteQueueDefault) Code() int {
	return o._statusCode
}

func (o *DeleteQueueDefault) Error() string {
	return fmt.Sprintf("[DELETE /api/v1/orgs/{owner}/agents/{agent}/queues/{uuid}][%d] DeleteQueue default  %+v", o._statusCode, o.Payload)
}

func (o *DeleteQueueDefault) GetPayload() *service_model.RuntimeError {
	return o.Payload
}

func (o *DeleteQueueDefault) readResponse(response runtime.ClientResponse, consumer runtime.Consumer, formats strfmt.Registry) error {

	o.Payload = new(service_model.RuntimeError)

	// response payload
	if err := consumer.Consume(response.Body(), o.Payload); err != nil && err != io.EOF {
		return err
	}

	return nil
}
