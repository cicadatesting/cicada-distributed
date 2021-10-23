# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: cicadad/protos/container_service.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import wrappers_pb2 as google_dot_protobuf_dot_wrappers__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='cicadad/protos/container_service.proto',
  package='container_service',
  syntax='proto3',
  serialized_options=b'Z.github.com/cicadatesting/container-service/api',
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n&cicadad/protos/container_service.proto\x12\x11\x63ontainer_service\x1a\x1bgoogle/protobuf/empty.proto\x1a\x1egoogle/protobuf/wrappers.proto\"\xce\x01\n\x13\x44ockerContainerArgs\x12\r\n\x05image\x18\x01 \x01(\t\x12\x0f\n\x07\x63ommand\x18\x02 \x03(\t\x12<\n\x03\x65nv\x18\x03 \x03(\x0b\x32/.container_service.DockerContainerArgs.EnvEntry\x12-\n\x07network\x18\x04 \x01(\x0b\x32\x1c.google.protobuf.StringValue\x1a*\n\x08\x45nvEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\"\x9b\x01\n\x11KubeContainerArgs\x12\r\n\x05image\x18\x01 \x01(\t\x12\x0f\n\x07\x63ommand\x18\x02 \x03(\t\x12:\n\x03\x65nv\x18\x03 \x03(\x0b\x32-.container_service.KubeContainerArgs.EnvEntry\x1a*\n\x08\x45nvEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\"\xc8\x02\n\x15StartContainerRequest\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x11\n\tnamespace\x18\x02 \x01(\t\x12\x44\n\x06labels\x18\x03 \x03(\x0b\x32\x34.container_service.StartContainerRequest.LabelsEntry\x12\x45\n\x13\x64ockerContainerArgs\x18\x04 \x01(\x0b\x32&.container_service.DockerContainerArgsH\x00\x12\x41\n\x11kubeContainerArgs\x18\x05 \x01(\x0b\x32$.container_service.KubeContainerArgsH\x00\x1a-\n\x0bLabelsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\x42\x0f\n\rcontainerArgs\"7\n\x14StopContainerRequest\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x11\n\tnamespace\x18\x02 \x01(\t\"\x9f\x01\n\x15StopContainersRequest\x12\x11\n\tnamespace\x18\x01 \x01(\t\x12\x44\n\x06labels\x18\x02 \x03(\x0b\x32\x34.container_service.StopContainersRequest.LabelsEntry\x1a-\n\x0bLabelsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\";\n\x18\x44\x65scribeContainerRequest\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x11\n\tnamespace\x18\x02 \x01(\t\"+\n\x18\x43ontainerRunningResponse\x12\x0f\n\x07running\x18\x01 \x01(\x08\x32\xfa\x02\n\x10\x43ontainerService\x12R\n\x0eStartContainer\x12(.container_service.StartContainerRequest\x1a\x16.google.protobuf.Empty\x12P\n\rStopContainer\x12\'.container_service.StopContainerRequest\x1a\x16.google.protobuf.Empty\x12R\n\x0eStopContainers\x12(.container_service.StopContainersRequest\x1a\x16.google.protobuf.Empty\x12l\n\x10\x43ontainerRunning\x12+.container_service.DescribeContainerRequest\x1a+.container_service.ContainerRunningResponseB0Z.github.com/cicadatesting/container-service/apib\x06proto3'
  ,
  dependencies=[google_dot_protobuf_dot_empty__pb2.DESCRIPTOR,google_dot_protobuf_dot_wrappers__pb2.DESCRIPTOR,])




_DOCKERCONTAINERARGS_ENVENTRY = _descriptor.Descriptor(
  name='EnvEntry',
  full_name='container_service.DockerContainerArgs.EnvEntry',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='key', full_name='container_service.DockerContainerArgs.EnvEntry.key', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='value', full_name='container_service.DockerContainerArgs.EnvEntry.value', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=b'8\001',
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=287,
  serialized_end=329,
)

_DOCKERCONTAINERARGS = _descriptor.Descriptor(
  name='DockerContainerArgs',
  full_name='container_service.DockerContainerArgs',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='image', full_name='container_service.DockerContainerArgs.image', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='command', full_name='container_service.DockerContainerArgs.command', index=1,
      number=2, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='env', full_name='container_service.DockerContainerArgs.env', index=2,
      number=3, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='network', full_name='container_service.DockerContainerArgs.network', index=3,
      number=4, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[_DOCKERCONTAINERARGS_ENVENTRY, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=123,
  serialized_end=329,
)


_KUBECONTAINERARGS_ENVENTRY = _descriptor.Descriptor(
  name='EnvEntry',
  full_name='container_service.KubeContainerArgs.EnvEntry',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='key', full_name='container_service.KubeContainerArgs.EnvEntry.key', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='value', full_name='container_service.KubeContainerArgs.EnvEntry.value', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=b'8\001',
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=287,
  serialized_end=329,
)

_KUBECONTAINERARGS = _descriptor.Descriptor(
  name='KubeContainerArgs',
  full_name='container_service.KubeContainerArgs',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='image', full_name='container_service.KubeContainerArgs.image', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='command', full_name='container_service.KubeContainerArgs.command', index=1,
      number=2, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='env', full_name='container_service.KubeContainerArgs.env', index=2,
      number=3, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[_KUBECONTAINERARGS_ENVENTRY, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=332,
  serialized_end=487,
)


_STARTCONTAINERREQUEST_LABELSENTRY = _descriptor.Descriptor(
  name='LabelsEntry',
  full_name='container_service.StartContainerRequest.LabelsEntry',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='key', full_name='container_service.StartContainerRequest.LabelsEntry.key', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='value', full_name='container_service.StartContainerRequest.LabelsEntry.value', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=b'8\001',
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=756,
  serialized_end=801,
)

_STARTCONTAINERREQUEST = _descriptor.Descriptor(
  name='StartContainerRequest',
  full_name='container_service.StartContainerRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='name', full_name='container_service.StartContainerRequest.name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='namespace', full_name='container_service.StartContainerRequest.namespace', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='labels', full_name='container_service.StartContainerRequest.labels', index=2,
      number=3, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='dockerContainerArgs', full_name='container_service.StartContainerRequest.dockerContainerArgs', index=3,
      number=4, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='kubeContainerArgs', full_name='container_service.StartContainerRequest.kubeContainerArgs', index=4,
      number=5, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[_STARTCONTAINERREQUEST_LABELSENTRY, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
    _descriptor.OneofDescriptor(
      name='containerArgs', full_name='container_service.StartContainerRequest.containerArgs',
      index=0, containing_type=None,
      create_key=_descriptor._internal_create_key,
    fields=[]),
  ],
  serialized_start=490,
  serialized_end=818,
)


_STOPCONTAINERREQUEST = _descriptor.Descriptor(
  name='StopContainerRequest',
  full_name='container_service.StopContainerRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='name', full_name='container_service.StopContainerRequest.name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='namespace', full_name='container_service.StopContainerRequest.namespace', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=820,
  serialized_end=875,
)


_STOPCONTAINERSREQUEST_LABELSENTRY = _descriptor.Descriptor(
  name='LabelsEntry',
  full_name='container_service.StopContainersRequest.LabelsEntry',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='key', full_name='container_service.StopContainersRequest.LabelsEntry.key', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='value', full_name='container_service.StopContainersRequest.LabelsEntry.value', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=b'8\001',
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=756,
  serialized_end=801,
)

_STOPCONTAINERSREQUEST = _descriptor.Descriptor(
  name='StopContainersRequest',
  full_name='container_service.StopContainersRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='namespace', full_name='container_service.StopContainersRequest.namespace', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='labels', full_name='container_service.StopContainersRequest.labels', index=1,
      number=2, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[_STOPCONTAINERSREQUEST_LABELSENTRY, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=878,
  serialized_end=1037,
)


_DESCRIBECONTAINERREQUEST = _descriptor.Descriptor(
  name='DescribeContainerRequest',
  full_name='container_service.DescribeContainerRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='name', full_name='container_service.DescribeContainerRequest.name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='namespace', full_name='container_service.DescribeContainerRequest.namespace', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1039,
  serialized_end=1098,
)


_CONTAINERRUNNINGRESPONSE = _descriptor.Descriptor(
  name='ContainerRunningResponse',
  full_name='container_service.ContainerRunningResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='running', full_name='container_service.ContainerRunningResponse.running', index=0,
      number=1, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1100,
  serialized_end=1143,
)

_DOCKERCONTAINERARGS_ENVENTRY.containing_type = _DOCKERCONTAINERARGS
_DOCKERCONTAINERARGS.fields_by_name['env'].message_type = _DOCKERCONTAINERARGS_ENVENTRY
_DOCKERCONTAINERARGS.fields_by_name['network'].message_type = google_dot_protobuf_dot_wrappers__pb2._STRINGVALUE
_KUBECONTAINERARGS_ENVENTRY.containing_type = _KUBECONTAINERARGS
_KUBECONTAINERARGS.fields_by_name['env'].message_type = _KUBECONTAINERARGS_ENVENTRY
_STARTCONTAINERREQUEST_LABELSENTRY.containing_type = _STARTCONTAINERREQUEST
_STARTCONTAINERREQUEST.fields_by_name['labels'].message_type = _STARTCONTAINERREQUEST_LABELSENTRY
_STARTCONTAINERREQUEST.fields_by_name['dockerContainerArgs'].message_type = _DOCKERCONTAINERARGS
_STARTCONTAINERREQUEST.fields_by_name['kubeContainerArgs'].message_type = _KUBECONTAINERARGS
_STARTCONTAINERREQUEST.oneofs_by_name['containerArgs'].fields.append(
  _STARTCONTAINERREQUEST.fields_by_name['dockerContainerArgs'])
_STARTCONTAINERREQUEST.fields_by_name['dockerContainerArgs'].containing_oneof = _STARTCONTAINERREQUEST.oneofs_by_name['containerArgs']
_STARTCONTAINERREQUEST.oneofs_by_name['containerArgs'].fields.append(
  _STARTCONTAINERREQUEST.fields_by_name['kubeContainerArgs'])
_STARTCONTAINERREQUEST.fields_by_name['kubeContainerArgs'].containing_oneof = _STARTCONTAINERREQUEST.oneofs_by_name['containerArgs']
_STOPCONTAINERSREQUEST_LABELSENTRY.containing_type = _STOPCONTAINERSREQUEST
_STOPCONTAINERSREQUEST.fields_by_name['labels'].message_type = _STOPCONTAINERSREQUEST_LABELSENTRY
DESCRIPTOR.message_types_by_name['DockerContainerArgs'] = _DOCKERCONTAINERARGS
DESCRIPTOR.message_types_by_name['KubeContainerArgs'] = _KUBECONTAINERARGS
DESCRIPTOR.message_types_by_name['StartContainerRequest'] = _STARTCONTAINERREQUEST
DESCRIPTOR.message_types_by_name['StopContainerRequest'] = _STOPCONTAINERREQUEST
DESCRIPTOR.message_types_by_name['StopContainersRequest'] = _STOPCONTAINERSREQUEST
DESCRIPTOR.message_types_by_name['DescribeContainerRequest'] = _DESCRIBECONTAINERREQUEST
DESCRIPTOR.message_types_by_name['ContainerRunningResponse'] = _CONTAINERRUNNINGRESPONSE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

DockerContainerArgs = _reflection.GeneratedProtocolMessageType('DockerContainerArgs', (_message.Message,), {

  'EnvEntry' : _reflection.GeneratedProtocolMessageType('EnvEntry', (_message.Message,), {
    'DESCRIPTOR' : _DOCKERCONTAINERARGS_ENVENTRY,
    '__module__' : 'cicadad.protos.container_service_pb2'
    # @@protoc_insertion_point(class_scope:container_service.DockerContainerArgs.EnvEntry)
    })
  ,
  'DESCRIPTOR' : _DOCKERCONTAINERARGS,
  '__module__' : 'cicadad.protos.container_service_pb2'
  # @@protoc_insertion_point(class_scope:container_service.DockerContainerArgs)
  })
_sym_db.RegisterMessage(DockerContainerArgs)
_sym_db.RegisterMessage(DockerContainerArgs.EnvEntry)

KubeContainerArgs = _reflection.GeneratedProtocolMessageType('KubeContainerArgs', (_message.Message,), {

  'EnvEntry' : _reflection.GeneratedProtocolMessageType('EnvEntry', (_message.Message,), {
    'DESCRIPTOR' : _KUBECONTAINERARGS_ENVENTRY,
    '__module__' : 'cicadad.protos.container_service_pb2'
    # @@protoc_insertion_point(class_scope:container_service.KubeContainerArgs.EnvEntry)
    })
  ,
  'DESCRIPTOR' : _KUBECONTAINERARGS,
  '__module__' : 'cicadad.protos.container_service_pb2'
  # @@protoc_insertion_point(class_scope:container_service.KubeContainerArgs)
  })
_sym_db.RegisterMessage(KubeContainerArgs)
_sym_db.RegisterMessage(KubeContainerArgs.EnvEntry)

StartContainerRequest = _reflection.GeneratedProtocolMessageType('StartContainerRequest', (_message.Message,), {

  'LabelsEntry' : _reflection.GeneratedProtocolMessageType('LabelsEntry', (_message.Message,), {
    'DESCRIPTOR' : _STARTCONTAINERREQUEST_LABELSENTRY,
    '__module__' : 'cicadad.protos.container_service_pb2'
    # @@protoc_insertion_point(class_scope:container_service.StartContainerRequest.LabelsEntry)
    })
  ,
  'DESCRIPTOR' : _STARTCONTAINERREQUEST,
  '__module__' : 'cicadad.protos.container_service_pb2'
  # @@protoc_insertion_point(class_scope:container_service.StartContainerRequest)
  })
_sym_db.RegisterMessage(StartContainerRequest)
_sym_db.RegisterMessage(StartContainerRequest.LabelsEntry)

StopContainerRequest = _reflection.GeneratedProtocolMessageType('StopContainerRequest', (_message.Message,), {
  'DESCRIPTOR' : _STOPCONTAINERREQUEST,
  '__module__' : 'cicadad.protos.container_service_pb2'
  # @@protoc_insertion_point(class_scope:container_service.StopContainerRequest)
  })
_sym_db.RegisterMessage(StopContainerRequest)

StopContainersRequest = _reflection.GeneratedProtocolMessageType('StopContainersRequest', (_message.Message,), {

  'LabelsEntry' : _reflection.GeneratedProtocolMessageType('LabelsEntry', (_message.Message,), {
    'DESCRIPTOR' : _STOPCONTAINERSREQUEST_LABELSENTRY,
    '__module__' : 'cicadad.protos.container_service_pb2'
    # @@protoc_insertion_point(class_scope:container_service.StopContainersRequest.LabelsEntry)
    })
  ,
  'DESCRIPTOR' : _STOPCONTAINERSREQUEST,
  '__module__' : 'cicadad.protos.container_service_pb2'
  # @@protoc_insertion_point(class_scope:container_service.StopContainersRequest)
  })
_sym_db.RegisterMessage(StopContainersRequest)
_sym_db.RegisterMessage(StopContainersRequest.LabelsEntry)

DescribeContainerRequest = _reflection.GeneratedProtocolMessageType('DescribeContainerRequest', (_message.Message,), {
  'DESCRIPTOR' : _DESCRIBECONTAINERREQUEST,
  '__module__' : 'cicadad.protos.container_service_pb2'
  # @@protoc_insertion_point(class_scope:container_service.DescribeContainerRequest)
  })
_sym_db.RegisterMessage(DescribeContainerRequest)

ContainerRunningResponse = _reflection.GeneratedProtocolMessageType('ContainerRunningResponse', (_message.Message,), {
  'DESCRIPTOR' : _CONTAINERRUNNINGRESPONSE,
  '__module__' : 'cicadad.protos.container_service_pb2'
  # @@protoc_insertion_point(class_scope:container_service.ContainerRunningResponse)
  })
_sym_db.RegisterMessage(ContainerRunningResponse)


DESCRIPTOR._options = None
_DOCKERCONTAINERARGS_ENVENTRY._options = None
_KUBECONTAINERARGS_ENVENTRY._options = None
_STARTCONTAINERREQUEST_LABELSENTRY._options = None
_STOPCONTAINERSREQUEST_LABELSENTRY._options = None

_CONTAINERSERVICE = _descriptor.ServiceDescriptor(
  name='ContainerService',
  full_name='container_service.ContainerService',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_start=1146,
  serialized_end=1524,
  methods=[
  _descriptor.MethodDescriptor(
    name='StartContainer',
    full_name='container_service.ContainerService.StartContainer',
    index=0,
    containing_service=None,
    input_type=_STARTCONTAINERREQUEST,
    output_type=google_dot_protobuf_dot_empty__pb2._EMPTY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='StopContainer',
    full_name='container_service.ContainerService.StopContainer',
    index=1,
    containing_service=None,
    input_type=_STOPCONTAINERREQUEST,
    output_type=google_dot_protobuf_dot_empty__pb2._EMPTY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='StopContainers',
    full_name='container_service.ContainerService.StopContainers',
    index=2,
    containing_service=None,
    input_type=_STOPCONTAINERSREQUEST,
    output_type=google_dot_protobuf_dot_empty__pb2._EMPTY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='ContainerRunning',
    full_name='container_service.ContainerService.ContainerRunning',
    index=3,
    containing_service=None,
    input_type=_DESCRIBECONTAINERREQUEST,
    output_type=_CONTAINERRUNNINGRESPONSE,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
])
_sym_db.RegisterServiceDescriptor(_CONTAINERSERVICE)

DESCRIPTOR.services_by_name['ContainerService'] = _CONTAINERSERVICE

# @@protoc_insertion_point(module_scope)
