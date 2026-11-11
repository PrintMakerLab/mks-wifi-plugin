# Copyright (c) 2026
# MKS Plugin is released under the terms of the AGPLv3 or higher.

# Tests for MKSUploader against a minimal fake MKS WiFi HTTP server.
# MKSUploader has no Cura/Uranium dependencies, run with: python -m pytest

import socket
import threading
import time

from MKSUploader import MKSUploader, UploadResult

DATA = ("G1 X10 Y10 ; test\n" * 50000).encode()  # ~900 KB


def start_fake_module(mode, store):
    """Accepts one upload and answers like the module (or misbehaves, depending on mode)."""
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)

    def run():
        conn, _ = srv.accept()
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += conn.recv(4096)
        head, body = buf.split(b"\r\n\r\n", 1)
        store["head"] = head.decode()
        length = int([l for l in store["head"].split("\r\n")
                      if l.lower().startswith("content-length")][0].split(":")[1])
        while len(body) < length:
            chunk = conn.recv(65536)
            if not chunk:
                break
            body += chunk
            if mode == "slow":
                time.sleep(0.01)
        store["body"] = body
        answers = {
            "ok": b'HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: 9\r\n\r\n{"err":0}',
            "err1": b'HTTP/1.1 200 OK\r\nContent-Length: 9\r\n\r\n{"err":1}',
            "plain200": b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok",
            "garbage": b"OK\r\n",
            "500": b"HTTP/1.1 500 Error\r\nContent-Length: 4\r\n\r\nfail",
        }
        if mode in answers:
            conn.sendall(answers[mode])
        conn.close()
        srv.close()

    threading.Thread(target=run, daemon=True).start()
    return srv.getsockname()[1]


def upload(mode, data=DATA, filename="test.gcode", cancel_after=None):
    store, result, progress = {}, {}, []
    done = threading.Event()

    def on_finished(res, status, detail):
        result.update(result=res, status=status, detail=detail)
        done.set()

    port = start_fake_module(mode, store)
    uploader = MKSUploader("127.0.0.1", filename, data,
                           dispatch=lambda func, *args: func(*args),
                           on_progress=lambda sent, total: progress.append((sent, total)),
                           on_finished=on_finished, port=port)
    uploader.start()
    if cancel_after:
        time.sleep(cancel_after)
        uploader.cancel()
    assert done.wait(15), "upload did not finish"
    return result, store, progress


def test_sanitize_filename():
    assert MKSUploader.sanitize_filename("y-rail-cover-v3.gcode") == "y-rail-cover-v3.gcode"
    assert MKSUploader.sanitize_filename("new test ds sdf.gcode") == "new_test_ds_sdf.gcode"
    assert MKSUploader.sanitize_filename("mein teil ö.gcode") == "mein_teil_.gcode"
    assert MKSUploader.sanitize_filename("part") == "part.gcode"
    assert MKSUploader.sanitize_filename("ööö.gcode") == "cura_file.gcode"


def test_parse_answer():
    assert MKSUploader.parse_answer('{"err":0}') == 0
    assert MKSUploader.parse_answer('{"err" : 1}') == 1
    assert MKSUploader.parse_answer('junk "err":2 junk') == 2
    assert MKSUploader.parse_answer("ok") is None


def test_upload_ok():
    result, store, progress = upload("ok", filename="new_test.gcode")
    assert result["result"] == UploadResult.OK
    assert store["body"] == DATA
    assert store["head"].startswith("POST /upload?X-Filename=new_test.gcode HTTP/1.1")
    assert "Content-Length: %d" % len(DATA) in store["head"]
    assert progress[-1] == (len(DATA), len(DATA))


def test_upload_rejected_by_module():
    result, _, _ = upload("err1")
    assert result["result"] == UploadResult.REJECTED


def test_upload_http_200_without_json_is_unconfirmed():
    result, _, _ = upload("plain200")
    assert result["result"] == UploadResult.OK_NO_RESPONSE


def test_upload_connection_dropped_after_body_is_unconfirmed():
    result, store, _ = upload("drop")
    assert result["result"] == UploadResult.OK_NO_RESPONSE
    assert store["body"] == DATA


def test_upload_invalid_answer_is_unconfirmed():
    result, _, _ = upload("garbage")
    assert result["result"] == UploadResult.OK_NO_RESPONSE


def test_upload_http_error():
    result, _, _ = upload("500")
    assert result["result"] == UploadResult.HTTP_ERROR
    assert result["status"] == 500


def test_upload_cancel():
    result, _, _ = upload("slow", data=DATA * 4, cancel_after=0.3)
    assert result["result"] == UploadResult.CANCELLED


def test_upload_connection_refused():
    done = threading.Event()
    result = {}
    uploader = MKSUploader("127.0.0.1", "x.gcode", b"abc",
                           dispatch=lambda func, *args: func(*args),
                           on_finished=lambda res, *_: (result.setdefault("result", res), done.set()),
                           port=1)
    uploader.start()
    assert done.wait(5)
    assert result["result"] == UploadResult.FAILED
