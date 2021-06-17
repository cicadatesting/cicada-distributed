// Code generated by protoc-gen-go-grpc. DO NOT EDIT.

package api

import (
	context "context"
	empty "github.com/golang/protobuf/ptypes/empty"
	grpc "google.golang.org/grpc"
	codes "google.golang.org/grpc/codes"
	status "google.golang.org/grpc/status"
)

// This is a compile-time assertion to ensure that this generated file
// is compatible with the grpc package it is being compiled against.
// Requires gRPC-Go v1.32.0 or later.
const _ = grpc.SupportPackageIsVersion7

// DatastoreClient is the client API for Datastore service.
//
// For semantics around ctx use and closing/ending streaming RPCs, please refer to https://pkg.go.dev/google.golang.org/grpc/?tab=doc#ClientConn.NewStream.
type DatastoreClient interface {
	AddUserResult(ctx context.Context, in *AddUserResultRequest, opts ...grpc.CallOption) (*empty.Empty, error)
	SetScenarioResult(ctx context.Context, in *SetScenarioResultRequest, opts ...grpc.CallOption) (*empty.Empty, error)
	MoveUserResults(ctx context.Context, in *MoveUserResultsRequest, opts ...grpc.CallOption) (*MoveUserResultsResponse, error)
	MoveScenarioResult(ctx context.Context, in *MoveScenarioResultRequest, opts ...grpc.CallOption) (*MoveScenarioResultResponse, error)
	DistributeWork(ctx context.Context, in *DistributeWorkRequest, opts ...grpc.CallOption) (*empty.Empty, error)
	GetUserWork(ctx context.Context, in *GetUserWorkRequest, opts ...grpc.CallOption) (*GetUserWorkResponse, error)
}

type datastoreClient struct {
	cc grpc.ClientConnInterface
}

func NewDatastoreClient(cc grpc.ClientConnInterface) DatastoreClient {
	return &datastoreClient{cc}
}

func (c *datastoreClient) AddUserResult(ctx context.Context, in *AddUserResultRequest, opts ...grpc.CallOption) (*empty.Empty, error) {
	out := new(empty.Empty)
	err := c.cc.Invoke(ctx, "/datastore.Datastore/AddUserResult", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *datastoreClient) SetScenarioResult(ctx context.Context, in *SetScenarioResultRequest, opts ...grpc.CallOption) (*empty.Empty, error) {
	out := new(empty.Empty)
	err := c.cc.Invoke(ctx, "/datastore.Datastore/SetScenarioResult", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *datastoreClient) MoveUserResults(ctx context.Context, in *MoveUserResultsRequest, opts ...grpc.CallOption) (*MoveUserResultsResponse, error) {
	out := new(MoveUserResultsResponse)
	err := c.cc.Invoke(ctx, "/datastore.Datastore/MoveUserResults", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *datastoreClient) MoveScenarioResult(ctx context.Context, in *MoveScenarioResultRequest, opts ...grpc.CallOption) (*MoveScenarioResultResponse, error) {
	out := new(MoveScenarioResultResponse)
	err := c.cc.Invoke(ctx, "/datastore.Datastore/MoveScenarioResult", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *datastoreClient) DistributeWork(ctx context.Context, in *DistributeWorkRequest, opts ...grpc.CallOption) (*empty.Empty, error) {
	out := new(empty.Empty)
	err := c.cc.Invoke(ctx, "/datastore.Datastore/DistributeWork", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

func (c *datastoreClient) GetUserWork(ctx context.Context, in *GetUserWorkRequest, opts ...grpc.CallOption) (*GetUserWorkResponse, error) {
	out := new(GetUserWorkResponse)
	err := c.cc.Invoke(ctx, "/datastore.Datastore/GetUserWork", in, out, opts...)
	if err != nil {
		return nil, err
	}
	return out, nil
}

// DatastoreServer is the server API for Datastore service.
// All implementations must embed UnimplementedDatastoreServer
// for forward compatibility
type DatastoreServer interface {
	AddUserResult(context.Context, *AddUserResultRequest) (*empty.Empty, error)
	SetScenarioResult(context.Context, *SetScenarioResultRequest) (*empty.Empty, error)
	MoveUserResults(context.Context, *MoveUserResultsRequest) (*MoveUserResultsResponse, error)
	MoveScenarioResult(context.Context, *MoveScenarioResultRequest) (*MoveScenarioResultResponse, error)
	DistributeWork(context.Context, *DistributeWorkRequest) (*empty.Empty, error)
	GetUserWork(context.Context, *GetUserWorkRequest) (*GetUserWorkResponse, error)
	mustEmbedUnimplementedDatastoreServer()
}

// UnimplementedDatastoreServer must be embedded to have forward compatible implementations.
type UnimplementedDatastoreServer struct {
}

func (UnimplementedDatastoreServer) AddUserResult(context.Context, *AddUserResultRequest) (*empty.Empty, error) {
	return nil, status.Errorf(codes.Unimplemented, "method AddUserResult not implemented")
}
func (UnimplementedDatastoreServer) SetScenarioResult(context.Context, *SetScenarioResultRequest) (*empty.Empty, error) {
	return nil, status.Errorf(codes.Unimplemented, "method SetScenarioResult not implemented")
}
func (UnimplementedDatastoreServer) MoveUserResults(context.Context, *MoveUserResultsRequest) (*MoveUserResultsResponse, error) {
	return nil, status.Errorf(codes.Unimplemented, "method MoveUserResults not implemented")
}
func (UnimplementedDatastoreServer) MoveScenarioResult(context.Context, *MoveScenarioResultRequest) (*MoveScenarioResultResponse, error) {
	return nil, status.Errorf(codes.Unimplemented, "method MoveScenarioResult not implemented")
}
func (UnimplementedDatastoreServer) DistributeWork(context.Context, *DistributeWorkRequest) (*empty.Empty, error) {
	return nil, status.Errorf(codes.Unimplemented, "method DistributeWork not implemented")
}
func (UnimplementedDatastoreServer) GetUserWork(context.Context, *GetUserWorkRequest) (*GetUserWorkResponse, error) {
	return nil, status.Errorf(codes.Unimplemented, "method GetUserWork not implemented")
}
func (UnimplementedDatastoreServer) mustEmbedUnimplementedDatastoreServer() {}

// UnsafeDatastoreServer may be embedded to opt out of forward compatibility for this service.
// Use of this interface is not recommended, as added methods to DatastoreServer will
// result in compilation errors.
type UnsafeDatastoreServer interface {
	mustEmbedUnimplementedDatastoreServer()
}

func RegisterDatastoreServer(s grpc.ServiceRegistrar, srv DatastoreServer) {
	s.RegisterService(&Datastore_ServiceDesc, srv)
}

func _Datastore_AddUserResult_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(AddUserResultRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(DatastoreServer).AddUserResult(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/datastore.Datastore/AddUserResult",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(DatastoreServer).AddUserResult(ctx, req.(*AddUserResultRequest))
	}
	return interceptor(ctx, in, info, handler)
}

func _Datastore_SetScenarioResult_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(SetScenarioResultRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(DatastoreServer).SetScenarioResult(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/datastore.Datastore/SetScenarioResult",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(DatastoreServer).SetScenarioResult(ctx, req.(*SetScenarioResultRequest))
	}
	return interceptor(ctx, in, info, handler)
}

func _Datastore_MoveUserResults_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(MoveUserResultsRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(DatastoreServer).MoveUserResults(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/datastore.Datastore/MoveUserResults",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(DatastoreServer).MoveUserResults(ctx, req.(*MoveUserResultsRequest))
	}
	return interceptor(ctx, in, info, handler)
}

func _Datastore_MoveScenarioResult_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(MoveScenarioResultRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(DatastoreServer).MoveScenarioResult(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/datastore.Datastore/MoveScenarioResult",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(DatastoreServer).MoveScenarioResult(ctx, req.(*MoveScenarioResultRequest))
	}
	return interceptor(ctx, in, info, handler)
}

func _Datastore_DistributeWork_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(DistributeWorkRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(DatastoreServer).DistributeWork(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/datastore.Datastore/DistributeWork",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(DatastoreServer).DistributeWork(ctx, req.(*DistributeWorkRequest))
	}
	return interceptor(ctx, in, info, handler)
}

func _Datastore_GetUserWork_Handler(srv interface{}, ctx context.Context, dec func(interface{}) error, interceptor grpc.UnaryServerInterceptor) (interface{}, error) {
	in := new(GetUserWorkRequest)
	if err := dec(in); err != nil {
		return nil, err
	}
	if interceptor == nil {
		return srv.(DatastoreServer).GetUserWork(ctx, in)
	}
	info := &grpc.UnaryServerInfo{
		Server:     srv,
		FullMethod: "/datastore.Datastore/GetUserWork",
	}
	handler := func(ctx context.Context, req interface{}) (interface{}, error) {
		return srv.(DatastoreServer).GetUserWork(ctx, req.(*GetUserWorkRequest))
	}
	return interceptor(ctx, in, info, handler)
}

// Datastore_ServiceDesc is the grpc.ServiceDesc for Datastore service.
// It's only intended for direct use with grpc.RegisterService,
// and not to be introspected or modified (even as a copy)
var Datastore_ServiceDesc = grpc.ServiceDesc{
	ServiceName: "datastore.Datastore",
	HandlerType: (*DatastoreServer)(nil),
	Methods: []grpc.MethodDesc{
		{
			MethodName: "AddUserResult",
			Handler:    _Datastore_AddUserResult_Handler,
		},
		{
			MethodName: "SetScenarioResult",
			Handler:    _Datastore_SetScenarioResult_Handler,
		},
		{
			MethodName: "MoveUserResults",
			Handler:    _Datastore_MoveUserResults_Handler,
		},
		{
			MethodName: "MoveScenarioResult",
			Handler:    _Datastore_MoveScenarioResult_Handler,
		},
		{
			MethodName: "DistributeWork",
			Handler:    _Datastore_DistributeWork_Handler,
		},
		{
			MethodName: "GetUserWork",
			Handler:    _Datastore_GetUserWork_Handler,
		},
	},
	Streams:  []grpc.StreamDesc{},
	Metadata: "api/datastore.proto",
}