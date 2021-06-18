# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: cicadad/protos/hub.proto

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2


DESCRIPTOR = _descriptor.FileDescriptor(
  name='cicadad/protos/hub.proto',
  package='cicada_distributed',
  syntax='proto3',
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x18\x63icadad/protos/hub.proto\x12\x12\x63icada_distributed\x1a\x1bgoogle/protobuf/empty.proto\"\x1e\n\x0eRunTestRequest\x12\x0c\n\x04tags\x18\x01 \x03(\t\"N\n\nTestStatus\x12\x0c\n\x04type\x18\x01 \x01(\t\x12\x10\n\x08scenario\x18\x02 \x01(\t\x12\x0f\n\x07message\x18\x03 \x01(\t\x12\x0f\n\x07\x63ontext\x18\x04 \x01(\t\"!\n\x10HealthcheckReply\x12\r\n\x05ready\x18\x01 \x01(\x08\x32\x9f\x01\n\x03Hub\x12K\n\x03Run\x12\".cicada_distributed.RunTestRequest\x1a\x1e.cicada_distributed.TestStatus0\x01\x12K\n\x0bHealthcheck\x12\x16.google.protobuf.Empty\x1a$.cicada_distributed.HealthcheckReplyb\x06proto3'
  ,
  dependencies=[google_dot_protobuf_dot_empty__pb2.DESCRIPTOR,])




_RUNTESTREQUEST = _descriptor.Descriptor(
  name='RunTestRequest',
  full_name='cicada_distributed.RunTestRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='tags', full_name='cicada_distributed.RunTestRequest.tags', index=0,
      number=1, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
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
  serialized_start=77,
  serialized_end=107,
)


_TESTSTATUS = _descriptor.Descriptor(
  name='TestStatus',
  full_name='cicada_distributed.TestStatus',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='type', full_name='cicada_distributed.TestStatus.type', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='scenario', full_name='cicada_distributed.TestStatus.scenario', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='message', full_name='cicada_distributed.TestStatus.message', index=2,
      number=3, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='context', full_name='cicada_distributed.TestStatus.context', index=3,
      number=4, type=9, cpp_type=9, label=1,
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
  serialized_start=109,
  serialized_end=187,
)


_HEALTHCHECKREPLY = _descriptor.Descriptor(
  name='HealthcheckReply',
  full_name='cicada_distributed.HealthcheckReply',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='ready', full_name='cicada_distributed.HealthcheckReply.ready', index=0,
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
  serialized_start=189,
  serialized_end=222,
)

DESCRIPTOR.message_types_by_name['RunTestRequest'] = _RUNTESTREQUEST
DESCRIPTOR.message_types_by_name['TestStatus'] = _TESTSTATUS
DESCRIPTOR.message_types_by_name['HealthcheckReply'] = _HEALTHCHECKREPLY
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

RunTestRequest = _reflection.GeneratedProtocolMessageType('RunTestRequest', (_message.Message,), {
  'DESCRIPTOR' : _RUNTESTREQUEST,
  '__module__' : 'cicadad.protos.hub_pb2'
  # @@protoc_insertion_point(class_scope:cicada_distributed.RunTestRequest)
  })
_sym_db.RegisterMessage(RunTestRequest)

TestStatus = _reflection.GeneratedProtocolMessageType('TestStatus', (_message.Message,), {
  'DESCRIPTOR' : _TESTSTATUS,
  '__module__' : 'cicadad.protos.hub_pb2'
  # @@protoc_insertion_point(class_scope:cicada_distributed.TestStatus)
  })
_sym_db.RegisterMessage(TestStatus)

HealthcheckReply = _reflection.GeneratedProtocolMessageType('HealthcheckReply', (_message.Message,), {
  'DESCRIPTOR' : _HEALTHCHECKREPLY,
  '__module__' : 'cicadad.protos.hub_pb2'
  # @@protoc_insertion_point(class_scope:cicada_distributed.HealthcheckReply)
  })
_sym_db.RegisterMessage(HealthcheckReply)



_HUB = _descriptor.ServiceDescriptor(
  name='Hub',
  full_name='cicada_distributed.Hub',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  create_key=_descriptor._internal_create_key,
  serialized_start=225,
  serialized_end=384,
  methods=[
  _descriptor.MethodDescriptor(
    name='Run',
    full_name='cicada_distributed.Hub.Run',
    index=0,
    containing_service=None,
    input_type=_RUNTESTREQUEST,
    output_type=_TESTSTATUS,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
  _descriptor.MethodDescriptor(
    name='Healthcheck',
    full_name='cicada_distributed.Hub.Healthcheck',
    index=1,
    containing_service=None,
    input_type=google_dot_protobuf_dot_empty__pb2._EMPTY,
    output_type=_HEALTHCHECKREPLY,
    serialized_options=None,
    create_key=_descriptor._internal_create_key,
  ),
])
_sym_db.RegisterServiceDescriptor(_HUB)

DESCRIPTOR.services_by_name['Hub'] = _HUB

# @@protoc_insertion_point(module_scope)
