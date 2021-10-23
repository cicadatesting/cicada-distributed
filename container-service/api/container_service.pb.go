// Code generated by protoc-gen-go. DO NOT EDIT.
// versions:
// 	protoc-gen-go v1.26.0
// 	protoc        v3.6.1
// source: api/container_service.proto

package api

import (
	empty "github.com/golang/protobuf/ptypes/empty"
	wrappers "github.com/golang/protobuf/ptypes/wrappers"
	protoreflect "google.golang.org/protobuf/reflect/protoreflect"
	protoimpl "google.golang.org/protobuf/runtime/protoimpl"
	reflect "reflect"
	sync "sync"
)

const (
	// Verify that this generated code is sufficiently up-to-date.
	_ = protoimpl.EnforceVersion(20 - protoimpl.MinVersion)
	// Verify that runtime/protoimpl is sufficiently up-to-date.
	_ = protoimpl.EnforceVersion(protoimpl.MaxVersion - 20)
)

type DockerContainerArgs struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	Image   string                `protobuf:"bytes,1,opt,name=image,proto3" json:"image,omitempty"`
	Command []string              `protobuf:"bytes,2,rep,name=command,proto3" json:"command,omitempty"`
	Env     map[string]string     `protobuf:"bytes,3,rep,name=env,proto3" json:"env,omitempty" protobuf_key:"bytes,1,opt,name=key,proto3" protobuf_val:"bytes,2,opt,name=value,proto3"`
	Network *wrappers.StringValue `protobuf:"bytes,4,opt,name=network,proto3" json:"network,omitempty"`
}

func (x *DockerContainerArgs) Reset() {
	*x = DockerContainerArgs{}
	if protoimpl.UnsafeEnabled {
		mi := &file_api_container_service_proto_msgTypes[0]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *DockerContainerArgs) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*DockerContainerArgs) ProtoMessage() {}

func (x *DockerContainerArgs) ProtoReflect() protoreflect.Message {
	mi := &file_api_container_service_proto_msgTypes[0]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use DockerContainerArgs.ProtoReflect.Descriptor instead.
func (*DockerContainerArgs) Descriptor() ([]byte, []int) {
	return file_api_container_service_proto_rawDescGZIP(), []int{0}
}

func (x *DockerContainerArgs) GetImage() string {
	if x != nil {
		return x.Image
	}
	return ""
}

func (x *DockerContainerArgs) GetCommand() []string {
	if x != nil {
		return x.Command
	}
	return nil
}

func (x *DockerContainerArgs) GetEnv() map[string]string {
	if x != nil {
		return x.Env
	}
	return nil
}

func (x *DockerContainerArgs) GetNetwork() *wrappers.StringValue {
	if x != nil {
		return x.Network
	}
	return nil
}

type KubeContainerArgs struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	Image   string            `protobuf:"bytes,1,opt,name=image,proto3" json:"image,omitempty"`
	Command []string          `protobuf:"bytes,2,rep,name=command,proto3" json:"command,omitempty"`
	Env     map[string]string `protobuf:"bytes,3,rep,name=env,proto3" json:"env,omitempty" protobuf_key:"bytes,1,opt,name=key,proto3" protobuf_val:"bytes,2,opt,name=value,proto3"`
}

func (x *KubeContainerArgs) Reset() {
	*x = KubeContainerArgs{}
	if protoimpl.UnsafeEnabled {
		mi := &file_api_container_service_proto_msgTypes[1]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *KubeContainerArgs) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*KubeContainerArgs) ProtoMessage() {}

func (x *KubeContainerArgs) ProtoReflect() protoreflect.Message {
	mi := &file_api_container_service_proto_msgTypes[1]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use KubeContainerArgs.ProtoReflect.Descriptor instead.
func (*KubeContainerArgs) Descriptor() ([]byte, []int) {
	return file_api_container_service_proto_rawDescGZIP(), []int{1}
}

func (x *KubeContainerArgs) GetImage() string {
	if x != nil {
		return x.Image
	}
	return ""
}

func (x *KubeContainerArgs) GetCommand() []string {
	if x != nil {
		return x.Command
	}
	return nil
}

func (x *KubeContainerArgs) GetEnv() map[string]string {
	if x != nil {
		return x.Env
	}
	return nil
}

type StartContainerRequest struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	Name      string            `protobuf:"bytes,1,opt,name=name,proto3" json:"name,omitempty"`
	Namespace string            `protobuf:"bytes,2,opt,name=namespace,proto3" json:"namespace,omitempty"`
	Labels    map[string]string `protobuf:"bytes,3,rep,name=labels,proto3" json:"labels,omitempty" protobuf_key:"bytes,1,opt,name=key,proto3" protobuf_val:"bytes,2,opt,name=value,proto3"`
	// Types that are assignable to ContainerArgs:
	//	*StartContainerRequest_DockerContainerArgs
	//	*StartContainerRequest_KubeContainerArgs
	ContainerArgs isStartContainerRequest_ContainerArgs `protobuf_oneof:"containerArgs"`
}

func (x *StartContainerRequest) Reset() {
	*x = StartContainerRequest{}
	if protoimpl.UnsafeEnabled {
		mi := &file_api_container_service_proto_msgTypes[2]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *StartContainerRequest) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*StartContainerRequest) ProtoMessage() {}

func (x *StartContainerRequest) ProtoReflect() protoreflect.Message {
	mi := &file_api_container_service_proto_msgTypes[2]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use StartContainerRequest.ProtoReflect.Descriptor instead.
func (*StartContainerRequest) Descriptor() ([]byte, []int) {
	return file_api_container_service_proto_rawDescGZIP(), []int{2}
}

func (x *StartContainerRequest) GetName() string {
	if x != nil {
		return x.Name
	}
	return ""
}

func (x *StartContainerRequest) GetNamespace() string {
	if x != nil {
		return x.Namespace
	}
	return ""
}

func (x *StartContainerRequest) GetLabels() map[string]string {
	if x != nil {
		return x.Labels
	}
	return nil
}

func (m *StartContainerRequest) GetContainerArgs() isStartContainerRequest_ContainerArgs {
	if m != nil {
		return m.ContainerArgs
	}
	return nil
}

func (x *StartContainerRequest) GetDockerContainerArgs() *DockerContainerArgs {
	if x, ok := x.GetContainerArgs().(*StartContainerRequest_DockerContainerArgs); ok {
		return x.DockerContainerArgs
	}
	return nil
}

func (x *StartContainerRequest) GetKubeContainerArgs() *KubeContainerArgs {
	if x, ok := x.GetContainerArgs().(*StartContainerRequest_KubeContainerArgs); ok {
		return x.KubeContainerArgs
	}
	return nil
}

type isStartContainerRequest_ContainerArgs interface {
	isStartContainerRequest_ContainerArgs()
}

type StartContainerRequest_DockerContainerArgs struct {
	DockerContainerArgs *DockerContainerArgs `protobuf:"bytes,4,opt,name=dockerContainerArgs,proto3,oneof"`
}

type StartContainerRequest_KubeContainerArgs struct {
	KubeContainerArgs *KubeContainerArgs `protobuf:"bytes,5,opt,name=kubeContainerArgs,proto3,oneof"`
}

func (*StartContainerRequest_DockerContainerArgs) isStartContainerRequest_ContainerArgs() {}

func (*StartContainerRequest_KubeContainerArgs) isStartContainerRequest_ContainerArgs() {}

type StopContainerRequest struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	Name      string `protobuf:"bytes,1,opt,name=name,proto3" json:"name,omitempty"`
	Namespace string `protobuf:"bytes,2,opt,name=namespace,proto3" json:"namespace,omitempty"`
}

func (x *StopContainerRequest) Reset() {
	*x = StopContainerRequest{}
	if protoimpl.UnsafeEnabled {
		mi := &file_api_container_service_proto_msgTypes[3]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *StopContainerRequest) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*StopContainerRequest) ProtoMessage() {}

func (x *StopContainerRequest) ProtoReflect() protoreflect.Message {
	mi := &file_api_container_service_proto_msgTypes[3]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use StopContainerRequest.ProtoReflect.Descriptor instead.
func (*StopContainerRequest) Descriptor() ([]byte, []int) {
	return file_api_container_service_proto_rawDescGZIP(), []int{3}
}

func (x *StopContainerRequest) GetName() string {
	if x != nil {
		return x.Name
	}
	return ""
}

func (x *StopContainerRequest) GetNamespace() string {
	if x != nil {
		return x.Namespace
	}
	return ""
}

type StopContainersRequest struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	Namespace string            `protobuf:"bytes,1,opt,name=namespace,proto3" json:"namespace,omitempty"`
	Labels    map[string]string `protobuf:"bytes,2,rep,name=labels,proto3" json:"labels,omitempty" protobuf_key:"bytes,1,opt,name=key,proto3" protobuf_val:"bytes,2,opt,name=value,proto3"`
}

func (x *StopContainersRequest) Reset() {
	*x = StopContainersRequest{}
	if protoimpl.UnsafeEnabled {
		mi := &file_api_container_service_proto_msgTypes[4]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *StopContainersRequest) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*StopContainersRequest) ProtoMessage() {}

func (x *StopContainersRequest) ProtoReflect() protoreflect.Message {
	mi := &file_api_container_service_proto_msgTypes[4]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use StopContainersRequest.ProtoReflect.Descriptor instead.
func (*StopContainersRequest) Descriptor() ([]byte, []int) {
	return file_api_container_service_proto_rawDescGZIP(), []int{4}
}

func (x *StopContainersRequest) GetNamespace() string {
	if x != nil {
		return x.Namespace
	}
	return ""
}

func (x *StopContainersRequest) GetLabels() map[string]string {
	if x != nil {
		return x.Labels
	}
	return nil
}

type DescribeContainerRequest struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	Name      string `protobuf:"bytes,1,opt,name=name,proto3" json:"name,omitempty"`
	Namespace string `protobuf:"bytes,2,opt,name=namespace,proto3" json:"namespace,omitempty"`
}

func (x *DescribeContainerRequest) Reset() {
	*x = DescribeContainerRequest{}
	if protoimpl.UnsafeEnabled {
		mi := &file_api_container_service_proto_msgTypes[5]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *DescribeContainerRequest) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*DescribeContainerRequest) ProtoMessage() {}

func (x *DescribeContainerRequest) ProtoReflect() protoreflect.Message {
	mi := &file_api_container_service_proto_msgTypes[5]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use DescribeContainerRequest.ProtoReflect.Descriptor instead.
func (*DescribeContainerRequest) Descriptor() ([]byte, []int) {
	return file_api_container_service_proto_rawDescGZIP(), []int{5}
}

func (x *DescribeContainerRequest) GetName() string {
	if x != nil {
		return x.Name
	}
	return ""
}

func (x *DescribeContainerRequest) GetNamespace() string {
	if x != nil {
		return x.Namespace
	}
	return ""
}

type ContainerRunningResponse struct {
	state         protoimpl.MessageState
	sizeCache     protoimpl.SizeCache
	unknownFields protoimpl.UnknownFields

	Running bool `protobuf:"varint,1,opt,name=running,proto3" json:"running,omitempty"`
}

func (x *ContainerRunningResponse) Reset() {
	*x = ContainerRunningResponse{}
	if protoimpl.UnsafeEnabled {
		mi := &file_api_container_service_proto_msgTypes[6]
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		ms.StoreMessageInfo(mi)
	}
}

func (x *ContainerRunningResponse) String() string {
	return protoimpl.X.MessageStringOf(x)
}

func (*ContainerRunningResponse) ProtoMessage() {}

func (x *ContainerRunningResponse) ProtoReflect() protoreflect.Message {
	mi := &file_api_container_service_proto_msgTypes[6]
	if protoimpl.UnsafeEnabled && x != nil {
		ms := protoimpl.X.MessageStateOf(protoimpl.Pointer(x))
		if ms.LoadMessageInfo() == nil {
			ms.StoreMessageInfo(mi)
		}
		return ms
	}
	return mi.MessageOf(x)
}

// Deprecated: Use ContainerRunningResponse.ProtoReflect.Descriptor instead.
func (*ContainerRunningResponse) Descriptor() ([]byte, []int) {
	return file_api_container_service_proto_rawDescGZIP(), []int{6}
}

func (x *ContainerRunningResponse) GetRunning() bool {
	if x != nil {
		return x.Running
	}
	return false
}

var File_api_container_service_proto protoreflect.FileDescriptor

var file_api_container_service_proto_rawDesc = []byte{
	0x0a, 0x1b, 0x61, 0x70, 0x69, 0x2f, 0x63, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x5f,
	0x73, 0x65, 0x72, 0x76, 0x69, 0x63, 0x65, 0x2e, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x12, 0x11, 0x63,
	0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x5f, 0x73, 0x65, 0x72, 0x76, 0x69, 0x63, 0x65,
	0x1a, 0x1b, 0x67, 0x6f, 0x6f, 0x67, 0x6c, 0x65, 0x2f, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x62, 0x75,
	0x66, 0x2f, 0x65, 0x6d, 0x70, 0x74, 0x79, 0x2e, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x1a, 0x1e, 0x67,
	0x6f, 0x6f, 0x67, 0x6c, 0x65, 0x2f, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x62, 0x75, 0x66, 0x2f, 0x77,
	0x72, 0x61, 0x70, 0x70, 0x65, 0x72, 0x73, 0x2e, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x22, 0xf8, 0x01,
	0x0a, 0x13, 0x44, 0x6f, 0x63, 0x6b, 0x65, 0x72, 0x43, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65,
	0x72, 0x41, 0x72, 0x67, 0x73, 0x12, 0x14, 0x0a, 0x05, 0x69, 0x6d, 0x61, 0x67, 0x65, 0x18, 0x01,
	0x20, 0x01, 0x28, 0x09, 0x52, 0x05, 0x69, 0x6d, 0x61, 0x67, 0x65, 0x12, 0x18, 0x0a, 0x07, 0x63,
	0x6f, 0x6d, 0x6d, 0x61, 0x6e, 0x64, 0x18, 0x02, 0x20, 0x03, 0x28, 0x09, 0x52, 0x07, 0x63, 0x6f,
	0x6d, 0x6d, 0x61, 0x6e, 0x64, 0x12, 0x41, 0x0a, 0x03, 0x65, 0x6e, 0x76, 0x18, 0x03, 0x20, 0x03,
	0x28, 0x0b, 0x32, 0x2f, 0x2e, 0x63, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x5f, 0x73,
	0x65, 0x72, 0x76, 0x69, 0x63, 0x65, 0x2e, 0x44, 0x6f, 0x63, 0x6b, 0x65, 0x72, 0x43, 0x6f, 0x6e,
	0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x41, 0x72, 0x67, 0x73, 0x2e, 0x45, 0x6e, 0x76, 0x45, 0x6e,
	0x74, 0x72, 0x79, 0x52, 0x03, 0x65, 0x6e, 0x76, 0x12, 0x36, 0x0a, 0x07, 0x6e, 0x65, 0x74, 0x77,
	0x6f, 0x72, 0x6b, 0x18, 0x04, 0x20, 0x01, 0x28, 0x0b, 0x32, 0x1c, 0x2e, 0x67, 0x6f, 0x6f, 0x67,
	0x6c, 0x65, 0x2e, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x62, 0x75, 0x66, 0x2e, 0x53, 0x74, 0x72, 0x69,
	0x6e, 0x67, 0x56, 0x61, 0x6c, 0x75, 0x65, 0x52, 0x07, 0x6e, 0x65, 0x74, 0x77, 0x6f, 0x72, 0x6b,
	0x1a, 0x36, 0x0a, 0x08, 0x45, 0x6e, 0x76, 0x45, 0x6e, 0x74, 0x72, 0x79, 0x12, 0x10, 0x0a, 0x03,
	0x6b, 0x65, 0x79, 0x18, 0x01, 0x20, 0x01, 0x28, 0x09, 0x52, 0x03, 0x6b, 0x65, 0x79, 0x12, 0x14,
	0x0a, 0x05, 0x76, 0x61, 0x6c, 0x75, 0x65, 0x18, 0x02, 0x20, 0x01, 0x28, 0x09, 0x52, 0x05, 0x76,
	0x61, 0x6c, 0x75, 0x65, 0x3a, 0x02, 0x38, 0x01, 0x22, 0xbc, 0x01, 0x0a, 0x11, 0x4b, 0x75, 0x62,
	0x65, 0x43, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x41, 0x72, 0x67, 0x73, 0x12, 0x14,
	0x0a, 0x05, 0x69, 0x6d, 0x61, 0x67, 0x65, 0x18, 0x01, 0x20, 0x01, 0x28, 0x09, 0x52, 0x05, 0x69,
	0x6d, 0x61, 0x67, 0x65, 0x12, 0x18, 0x0a, 0x07, 0x63, 0x6f, 0x6d, 0x6d, 0x61, 0x6e, 0x64, 0x18,
	0x02, 0x20, 0x03, 0x28, 0x09, 0x52, 0x07, 0x63, 0x6f, 0x6d, 0x6d, 0x61, 0x6e, 0x64, 0x12, 0x3f,
	0x0a, 0x03, 0x65, 0x6e, 0x76, 0x18, 0x03, 0x20, 0x03, 0x28, 0x0b, 0x32, 0x2d, 0x2e, 0x63, 0x6f,
	0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x5f, 0x73, 0x65, 0x72, 0x76, 0x69, 0x63, 0x65, 0x2e,
	0x4b, 0x75, 0x62, 0x65, 0x43, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x41, 0x72, 0x67,
	0x73, 0x2e, 0x45, 0x6e, 0x76, 0x45, 0x6e, 0x74, 0x72, 0x79, 0x52, 0x03, 0x65, 0x6e, 0x76, 0x1a,
	0x36, 0x0a, 0x08, 0x45, 0x6e, 0x76, 0x45, 0x6e, 0x74, 0x72, 0x79, 0x12, 0x10, 0x0a, 0x03, 0x6b,
	0x65, 0x79, 0x18, 0x01, 0x20, 0x01, 0x28, 0x09, 0x52, 0x03, 0x6b, 0x65, 0x79, 0x12, 0x14, 0x0a,
	0x05, 0x76, 0x61, 0x6c, 0x75, 0x65, 0x18, 0x02, 0x20, 0x01, 0x28, 0x09, 0x52, 0x05, 0x76, 0x61,
	0x6c, 0x75, 0x65, 0x3a, 0x02, 0x38, 0x01, 0x22, 0x95, 0x03, 0x0a, 0x15, 0x53, 0x74, 0x61, 0x72,
	0x74, 0x43, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73,
	0x74, 0x12, 0x12, 0x0a, 0x04, 0x6e, 0x61, 0x6d, 0x65, 0x18, 0x01, 0x20, 0x01, 0x28, 0x09, 0x52,
	0x04, 0x6e, 0x61, 0x6d, 0x65, 0x12, 0x1c, 0x0a, 0x09, 0x6e, 0x61, 0x6d, 0x65, 0x73, 0x70, 0x61,
	0x63, 0x65, 0x18, 0x02, 0x20, 0x01, 0x28, 0x09, 0x52, 0x09, 0x6e, 0x61, 0x6d, 0x65, 0x73, 0x70,
	0x61, 0x63, 0x65, 0x12, 0x4c, 0x0a, 0x06, 0x6c, 0x61, 0x62, 0x65, 0x6c, 0x73, 0x18, 0x03, 0x20,
	0x03, 0x28, 0x0b, 0x32, 0x34, 0x2e, 0x63, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x5f,
	0x73, 0x65, 0x72, 0x76, 0x69, 0x63, 0x65, 0x2e, 0x53, 0x74, 0x61, 0x72, 0x74, 0x43, 0x6f, 0x6e,
	0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x2e, 0x4c, 0x61,
	0x62, 0x65, 0x6c, 0x73, 0x45, 0x6e, 0x74, 0x72, 0x79, 0x52, 0x06, 0x6c, 0x61, 0x62, 0x65, 0x6c,
	0x73, 0x12, 0x5a, 0x0a, 0x13, 0x64, 0x6f, 0x63, 0x6b, 0x65, 0x72, 0x43, 0x6f, 0x6e, 0x74, 0x61,
	0x69, 0x6e, 0x65, 0x72, 0x41, 0x72, 0x67, 0x73, 0x18, 0x04, 0x20, 0x01, 0x28, 0x0b, 0x32, 0x26,
	0x2e, 0x63, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x5f, 0x73, 0x65, 0x72, 0x76, 0x69,
	0x63, 0x65, 0x2e, 0x44, 0x6f, 0x63, 0x6b, 0x65, 0x72, 0x43, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e,
	0x65, 0x72, 0x41, 0x72, 0x67, 0x73, 0x48, 0x00, 0x52, 0x13, 0x64, 0x6f, 0x63, 0x6b, 0x65, 0x72,
	0x43, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x41, 0x72, 0x67, 0x73, 0x12, 0x54, 0x0a,
	0x11, 0x6b, 0x75, 0x62, 0x65, 0x43, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x41, 0x72,
	0x67, 0x73, 0x18, 0x05, 0x20, 0x01, 0x28, 0x0b, 0x32, 0x24, 0x2e, 0x63, 0x6f, 0x6e, 0x74, 0x61,
	0x69, 0x6e, 0x65, 0x72, 0x5f, 0x73, 0x65, 0x72, 0x76, 0x69, 0x63, 0x65, 0x2e, 0x4b, 0x75, 0x62,
	0x65, 0x43, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x41, 0x72, 0x67, 0x73, 0x48, 0x00,
	0x52, 0x11, 0x6b, 0x75, 0x62, 0x65, 0x43, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x41,
	0x72, 0x67, 0x73, 0x1a, 0x39, 0x0a, 0x0b, 0x4c, 0x61, 0x62, 0x65, 0x6c, 0x73, 0x45, 0x6e, 0x74,
	0x72, 0x79, 0x12, 0x10, 0x0a, 0x03, 0x6b, 0x65, 0x79, 0x18, 0x01, 0x20, 0x01, 0x28, 0x09, 0x52,
	0x03, 0x6b, 0x65, 0x79, 0x12, 0x14, 0x0a, 0x05, 0x76, 0x61, 0x6c, 0x75, 0x65, 0x18, 0x02, 0x20,
	0x01, 0x28, 0x09, 0x52, 0x05, 0x76, 0x61, 0x6c, 0x75, 0x65, 0x3a, 0x02, 0x38, 0x01, 0x42, 0x0f,
	0x0a, 0x0d, 0x63, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x41, 0x72, 0x67, 0x73, 0x22,
	0x48, 0x0a, 0x14, 0x53, 0x74, 0x6f, 0x70, 0x43, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72,
	0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x12, 0x12, 0x0a, 0x04, 0x6e, 0x61, 0x6d, 0x65, 0x18,
	0x01, 0x20, 0x01, 0x28, 0x09, 0x52, 0x04, 0x6e, 0x61, 0x6d, 0x65, 0x12, 0x1c, 0x0a, 0x09, 0x6e,
	0x61, 0x6d, 0x65, 0x73, 0x70, 0x61, 0x63, 0x65, 0x18, 0x02, 0x20, 0x01, 0x28, 0x09, 0x52, 0x09,
	0x6e, 0x61, 0x6d, 0x65, 0x73, 0x70, 0x61, 0x63, 0x65, 0x22, 0xbe, 0x01, 0x0a, 0x15, 0x53, 0x74,
	0x6f, 0x70, 0x43, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x73, 0x52, 0x65, 0x71, 0x75,
	0x65, 0x73, 0x74, 0x12, 0x1c, 0x0a, 0x09, 0x6e, 0x61, 0x6d, 0x65, 0x73, 0x70, 0x61, 0x63, 0x65,
	0x18, 0x01, 0x20, 0x01, 0x28, 0x09, 0x52, 0x09, 0x6e, 0x61, 0x6d, 0x65, 0x73, 0x70, 0x61, 0x63,
	0x65, 0x12, 0x4c, 0x0a, 0x06, 0x6c, 0x61, 0x62, 0x65, 0x6c, 0x73, 0x18, 0x02, 0x20, 0x03, 0x28,
	0x0b, 0x32, 0x34, 0x2e, 0x63, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x5f, 0x73, 0x65,
	0x72, 0x76, 0x69, 0x63, 0x65, 0x2e, 0x53, 0x74, 0x6f, 0x70, 0x43, 0x6f, 0x6e, 0x74, 0x61, 0x69,
	0x6e, 0x65, 0x72, 0x73, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x2e, 0x4c, 0x61, 0x62, 0x65,
	0x6c, 0x73, 0x45, 0x6e, 0x74, 0x72, 0x79, 0x52, 0x06, 0x6c, 0x61, 0x62, 0x65, 0x6c, 0x73, 0x1a,
	0x39, 0x0a, 0x0b, 0x4c, 0x61, 0x62, 0x65, 0x6c, 0x73, 0x45, 0x6e, 0x74, 0x72, 0x79, 0x12, 0x10,
	0x0a, 0x03, 0x6b, 0x65, 0x79, 0x18, 0x01, 0x20, 0x01, 0x28, 0x09, 0x52, 0x03, 0x6b, 0x65, 0x79,
	0x12, 0x14, 0x0a, 0x05, 0x76, 0x61, 0x6c, 0x75, 0x65, 0x18, 0x02, 0x20, 0x01, 0x28, 0x09, 0x52,
	0x05, 0x76, 0x61, 0x6c, 0x75, 0x65, 0x3a, 0x02, 0x38, 0x01, 0x22, 0x4c, 0x0a, 0x18, 0x44, 0x65,
	0x73, 0x63, 0x72, 0x69, 0x62, 0x65, 0x43, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x52,
	0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x12, 0x12, 0x0a, 0x04, 0x6e, 0x61, 0x6d, 0x65, 0x18, 0x01,
	0x20, 0x01, 0x28, 0x09, 0x52, 0x04, 0x6e, 0x61, 0x6d, 0x65, 0x12, 0x1c, 0x0a, 0x09, 0x6e, 0x61,
	0x6d, 0x65, 0x73, 0x70, 0x61, 0x63, 0x65, 0x18, 0x02, 0x20, 0x01, 0x28, 0x09, 0x52, 0x09, 0x6e,
	0x61, 0x6d, 0x65, 0x73, 0x70, 0x61, 0x63, 0x65, 0x22, 0x34, 0x0a, 0x18, 0x43, 0x6f, 0x6e, 0x74,
	0x61, 0x69, 0x6e, 0x65, 0x72, 0x52, 0x75, 0x6e, 0x6e, 0x69, 0x6e, 0x67, 0x52, 0x65, 0x73, 0x70,
	0x6f, 0x6e, 0x73, 0x65, 0x12, 0x18, 0x0a, 0x07, 0x72, 0x75, 0x6e, 0x6e, 0x69, 0x6e, 0x67, 0x18,
	0x01, 0x20, 0x01, 0x28, 0x08, 0x52, 0x07, 0x72, 0x75, 0x6e, 0x6e, 0x69, 0x6e, 0x67, 0x32, 0xfa,
	0x02, 0x0a, 0x10, 0x43, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x53, 0x65, 0x72, 0x76,
	0x69, 0x63, 0x65, 0x12, 0x52, 0x0a, 0x0e, 0x53, 0x74, 0x61, 0x72, 0x74, 0x43, 0x6f, 0x6e, 0x74,
	0x61, 0x69, 0x6e, 0x65, 0x72, 0x12, 0x28, 0x2e, 0x63, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65,
	0x72, 0x5f, 0x73, 0x65, 0x72, 0x76, 0x69, 0x63, 0x65, 0x2e, 0x53, 0x74, 0x61, 0x72, 0x74, 0x43,
	0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x1a,
	0x16, 0x2e, 0x67, 0x6f, 0x6f, 0x67, 0x6c, 0x65, 0x2e, 0x70, 0x72, 0x6f, 0x74, 0x6f, 0x62, 0x75,
	0x66, 0x2e, 0x45, 0x6d, 0x70, 0x74, 0x79, 0x12, 0x50, 0x0a, 0x0d, 0x53, 0x74, 0x6f, 0x70, 0x43,
	0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x12, 0x27, 0x2e, 0x63, 0x6f, 0x6e, 0x74, 0x61,
	0x69, 0x6e, 0x65, 0x72, 0x5f, 0x73, 0x65, 0x72, 0x76, 0x69, 0x63, 0x65, 0x2e, 0x53, 0x74, 0x6f,
	0x70, 0x43, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73,
	0x74, 0x1a, 0x16, 0x2e, 0x67, 0x6f, 0x6f, 0x67, 0x6c, 0x65, 0x2e, 0x70, 0x72, 0x6f, 0x74, 0x6f,
	0x62, 0x75, 0x66, 0x2e, 0x45, 0x6d, 0x70, 0x74, 0x79, 0x12, 0x52, 0x0a, 0x0e, 0x53, 0x74, 0x6f,
	0x70, 0x43, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x73, 0x12, 0x28, 0x2e, 0x63, 0x6f,
	0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x5f, 0x73, 0x65, 0x72, 0x76, 0x69, 0x63, 0x65, 0x2e,
	0x53, 0x74, 0x6f, 0x70, 0x43, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x73, 0x52, 0x65,
	0x71, 0x75, 0x65, 0x73, 0x74, 0x1a, 0x16, 0x2e, 0x67, 0x6f, 0x6f, 0x67, 0x6c, 0x65, 0x2e, 0x70,
	0x72, 0x6f, 0x74, 0x6f, 0x62, 0x75, 0x66, 0x2e, 0x45, 0x6d, 0x70, 0x74, 0x79, 0x12, 0x6c, 0x0a,
	0x10, 0x43, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x52, 0x75, 0x6e, 0x6e, 0x69, 0x6e,
	0x67, 0x12, 0x2b, 0x2e, 0x63, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x5f, 0x73, 0x65,
	0x72, 0x76, 0x69, 0x63, 0x65, 0x2e, 0x44, 0x65, 0x73, 0x63, 0x72, 0x69, 0x62, 0x65, 0x43, 0x6f,
	0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x52, 0x65, 0x71, 0x75, 0x65, 0x73, 0x74, 0x1a, 0x2b,
	0x2e, 0x63, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x5f, 0x73, 0x65, 0x72, 0x76, 0x69,
	0x63, 0x65, 0x2e, 0x43, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65, 0x72, 0x52, 0x75, 0x6e, 0x6e,
	0x69, 0x6e, 0x67, 0x52, 0x65, 0x73, 0x70, 0x6f, 0x6e, 0x73, 0x65, 0x42, 0x30, 0x5a, 0x2e, 0x67,
	0x69, 0x74, 0x68, 0x75, 0x62, 0x2e, 0x63, 0x6f, 0x6d, 0x2f, 0x63, 0x69, 0x63, 0x61, 0x64, 0x61,
	0x74, 0x65, 0x73, 0x74, 0x69, 0x6e, 0x67, 0x2f, 0x63, 0x6f, 0x6e, 0x74, 0x61, 0x69, 0x6e, 0x65,
	0x72, 0x2d, 0x73, 0x65, 0x72, 0x76, 0x69, 0x63, 0x65, 0x2f, 0x61, 0x70, 0x69, 0x62, 0x06, 0x70,
	0x72, 0x6f, 0x74, 0x6f, 0x33,
}

var (
	file_api_container_service_proto_rawDescOnce sync.Once
	file_api_container_service_proto_rawDescData = file_api_container_service_proto_rawDesc
)

func file_api_container_service_proto_rawDescGZIP() []byte {
	file_api_container_service_proto_rawDescOnce.Do(func() {
		file_api_container_service_proto_rawDescData = protoimpl.X.CompressGZIP(file_api_container_service_proto_rawDescData)
	})
	return file_api_container_service_proto_rawDescData
}

var file_api_container_service_proto_msgTypes = make([]protoimpl.MessageInfo, 11)
var file_api_container_service_proto_goTypes = []interface{}{
	(*DockerContainerArgs)(nil),      // 0: container_service.DockerContainerArgs
	(*KubeContainerArgs)(nil),        // 1: container_service.KubeContainerArgs
	(*StartContainerRequest)(nil),    // 2: container_service.StartContainerRequest
	(*StopContainerRequest)(nil),     // 3: container_service.StopContainerRequest
	(*StopContainersRequest)(nil),    // 4: container_service.StopContainersRequest
	(*DescribeContainerRequest)(nil), // 5: container_service.DescribeContainerRequest
	(*ContainerRunningResponse)(nil), // 6: container_service.ContainerRunningResponse
	nil,                              // 7: container_service.DockerContainerArgs.EnvEntry
	nil,                              // 8: container_service.KubeContainerArgs.EnvEntry
	nil,                              // 9: container_service.StartContainerRequest.LabelsEntry
	nil,                              // 10: container_service.StopContainersRequest.LabelsEntry
	(*wrappers.StringValue)(nil),     // 11: google.protobuf.StringValue
	(*empty.Empty)(nil),              // 12: google.protobuf.Empty
}
var file_api_container_service_proto_depIdxs = []int32{
	7,  // 0: container_service.DockerContainerArgs.env:type_name -> container_service.DockerContainerArgs.EnvEntry
	11, // 1: container_service.DockerContainerArgs.network:type_name -> google.protobuf.StringValue
	8,  // 2: container_service.KubeContainerArgs.env:type_name -> container_service.KubeContainerArgs.EnvEntry
	9,  // 3: container_service.StartContainerRequest.labels:type_name -> container_service.StartContainerRequest.LabelsEntry
	0,  // 4: container_service.StartContainerRequest.dockerContainerArgs:type_name -> container_service.DockerContainerArgs
	1,  // 5: container_service.StartContainerRequest.kubeContainerArgs:type_name -> container_service.KubeContainerArgs
	10, // 6: container_service.StopContainersRequest.labels:type_name -> container_service.StopContainersRequest.LabelsEntry
	2,  // 7: container_service.ContainerService.StartContainer:input_type -> container_service.StartContainerRequest
	3,  // 8: container_service.ContainerService.StopContainer:input_type -> container_service.StopContainerRequest
	4,  // 9: container_service.ContainerService.StopContainers:input_type -> container_service.StopContainersRequest
	5,  // 10: container_service.ContainerService.ContainerRunning:input_type -> container_service.DescribeContainerRequest
	12, // 11: container_service.ContainerService.StartContainer:output_type -> google.protobuf.Empty
	12, // 12: container_service.ContainerService.StopContainer:output_type -> google.protobuf.Empty
	12, // 13: container_service.ContainerService.StopContainers:output_type -> google.protobuf.Empty
	6,  // 14: container_service.ContainerService.ContainerRunning:output_type -> container_service.ContainerRunningResponse
	11, // [11:15] is the sub-list for method output_type
	7,  // [7:11] is the sub-list for method input_type
	7,  // [7:7] is the sub-list for extension type_name
	7,  // [7:7] is the sub-list for extension extendee
	0,  // [0:7] is the sub-list for field type_name
}

func init() { file_api_container_service_proto_init() }
func file_api_container_service_proto_init() {
	if File_api_container_service_proto != nil {
		return
	}
	if !protoimpl.UnsafeEnabled {
		file_api_container_service_proto_msgTypes[0].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*DockerContainerArgs); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_api_container_service_proto_msgTypes[1].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*KubeContainerArgs); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_api_container_service_proto_msgTypes[2].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*StartContainerRequest); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_api_container_service_proto_msgTypes[3].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*StopContainerRequest); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_api_container_service_proto_msgTypes[4].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*StopContainersRequest); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_api_container_service_proto_msgTypes[5].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*DescribeContainerRequest); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
		file_api_container_service_proto_msgTypes[6].Exporter = func(v interface{}, i int) interface{} {
			switch v := v.(*ContainerRunningResponse); i {
			case 0:
				return &v.state
			case 1:
				return &v.sizeCache
			case 2:
				return &v.unknownFields
			default:
				return nil
			}
		}
	}
	file_api_container_service_proto_msgTypes[2].OneofWrappers = []interface{}{
		(*StartContainerRequest_DockerContainerArgs)(nil),
		(*StartContainerRequest_KubeContainerArgs)(nil),
	}
	type x struct{}
	out := protoimpl.TypeBuilder{
		File: protoimpl.DescBuilder{
			GoPackagePath: reflect.TypeOf(x{}).PkgPath(),
			RawDescriptor: file_api_container_service_proto_rawDesc,
			NumEnums:      0,
			NumMessages:   11,
			NumExtensions: 0,
			NumServices:   1,
		},
		GoTypes:           file_api_container_service_proto_goTypes,
		DependencyIndexes: file_api_container_service_proto_depIdxs,
		MessageInfos:      file_api_container_service_proto_msgTypes,
	}.Build()
	File_api_container_service_proto = out.File
	file_api_container_service_proto_rawDesc = nil
	file_api_container_service_proto_goTypes = nil
	file_api_container_service_proto_depIdxs = nil
}
