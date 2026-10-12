import time

from mmbot.exchange.popdex import NonceSource, client_order_id, pack_order_params


def test_order_params_layout():
    b = pack_order_params(category=2, order_type=0, side=1, tif=1, reduce_only=True)
    assert len(b) == 32
    assert b[0] == 2 and b[1] == 0 and b[2] == 1 and b[3] == 1
    assert b[6] == 1
    assert all(x == 0 for x in b[10:])


def test_client_order_id_is_alnum_hyphen_32_bytes():
    cid = client_order_id("mm_x.y")
    assert len(cid) == 32
    s = cid.rstrip(b"\0").decode()
    assert "_" not in s and "." not in s
    assert s.startswith("mmxy-")


def test_nonce_strictly_increasing_within_same_ms():
    n = NonceSource()
    a = [n.next() for _ in range(50)]
    assert all(y > x for x, y in zip(a, a[1:]))
    assert a[0] >= int(time.time() * 1000) - 1000
