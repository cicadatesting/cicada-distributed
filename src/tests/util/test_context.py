from cicadad.util import context


def test_encode_decode_dict():
    ctx = {"foo": "bar"}

    assert context.decode_context(context.encode_context(ctx)) == ctx


def test_encode_decode_non_dict():
    ctx = "foo"

    assert context.decode_context(context.encode_context(ctx)) == ctx
