# Copyright (c) 2026
# MKS Plugin is released under the terms of the AGPLv3 or higher.
"""Raw HTTP upload to the MKS Robin WiFi module, independent of Qt networking.

Why: since Cura 5.14 (Qt 6.6 -> 6.10) the upload through
QNetworkAccessManager / HttpRequestManager fails against the very minimal
HTTP server of the MKS WiFi module, while a plain `curl --data-binary` works.
This module sends the request exactly like curl does: one POST with a
Content-Length header and the raw G-code as body, using Python's http.client
in a worker thread.

All callbacks are dispatched through `dispatch` (normally
Application.callLater) so that they run on the Qt main thread.
"""

import http.client
import json
import re
import socket
import threading
import time
import urllib.parse

CHUNK_SIZE = 8 * 1024          # small chunks, the ESP8266 has tiny buffers
CONNECT_TIMEOUT = 10           # seconds
RESPONSE_TIMEOUT = 120         # module answers after writing to SD -> may be slow
PROGRESS_INTERVAL = 0.2        # seconds between progress callbacks
HEADER_BODY_PAUSE = 0.15       # seconds; send headers alone before the body (like curl's
                               # Expect/100-continue round trip). Cura 5.14 / Qt 6.10 pushed
                               # headers + 16 KB body in one burst and the module stalled.


class UploadResult:
    OK = "ok"                          # HTTP 2xx received
    OK_NO_RESPONSE = "ok_no_response"  # all bytes sent, module closed without valid answer
    HTTP_ERROR = "http_error"          # non 2xx status
    REJECTED = "rejected"              # module answered, but with "err" != 0
    FAILED = "failed"                  # connect / send error
    CANCELLED = "cancelled"


class MKSUploader:
    def __init__(self, host, filename, data, dispatch,
                 on_progress=None, on_finished=None, logger=None, port=80):
        self._host = host
        self._port = port
        self._filename = filename
        self._data = data if isinstance(data, (bytes, bytearray)) else data.encode("utf-8")
        self._dispatch = dispatch
        self._on_progress = on_progress
        self._on_finished = on_finished
        self._log = logger or (lambda level, msg: None)
        self._cancel = threading.Event()
        self._conn = None
        self._thread = None

    @staticmethod
    def sanitize_filename(filename):
        """Same rule as upload_mks.sh: spaces -> '_', keep only A-Za-z0-9._-
        and make sure the name ends with a G-code extension."""
        name = filename.replace(" ", "_")
        name = re.sub(r"[^A-Za-z0-9._-]", "", name)
        if not name or name.startswith("."):
            name = "cura_file" + name
        if not name.lower().endswith((".gcode", ".gco", ".g")):
            name += ".gcode"
        return name

    @staticmethod
    def build_path(filename):
        # filename is already sanitized, quoting is only a safety net
        return "/upload?X-Filename=" + urllib.parse.quote(filename, safe="._-")

    @staticmethod
    def parse_answer(text):
        """The module answers e.g. {"err":0}. Returns the err value or None."""
        try:
            obj = json.loads(text)
            if isinstance(obj, dict) and "err" in obj:
                return int(obj["err"])
        except (ValueError, TypeError):
            pass
        m = re.search(r'"err"\s*:\s*(-?\d+)', text)
        return int(m.group(1)) if m else None

    def start(self):
        self._thread = threading.Thread(target=self._run, name="MKSUpload", daemon=True)
        self._thread.start()

    def cancel(self):
        self._cancel.set()
        conn = self._conn
        if conn is not None:
            # shutdown() wakes up a send()/recv() blocked in the worker thread
            # immediately; close() alone does not (it waited for the 10 s timeout).
            sock = getattr(conn, "sock", None)
            if sock is not None:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
            try:
                conn.close()
            except Exception:
                pass

    def join(self, timeout=None):
        if self._thread:
            self._thread.join(timeout)

    # -- worker thread -------------------------------------------------------

    def _emit_progress(self, sent, total):
        if self._on_progress:
            self._dispatch(self._on_progress, sent, total)

    def _finish(self, result, status=None, detail=""):
        self._log("i" if result in (UploadResult.OK, UploadResult.OK_NO_RESPONSE) else "w",
                  "MKS upload finished: result=%s status=%s detail=%s" % (result, status, detail))
        if self._on_finished:
            self._dispatch(self._on_finished, result, status, detail)

    def _run(self):
        total = len(self._data)
        path = self.build_path(self._filename)
        self._log("d", "MKS upload: POST http://%s:%d%s (%d bytes)" % (self._host, self._port, path, total))
        sent = 0
        t0 = time.monotonic()
        next_log_pct = 25
        try:
            self._conn = http.client.HTTPConnection(self._host, self._port, timeout=CONNECT_TIMEOUT)
            self._conn.putrequest("POST", path, skip_accept_encoding=True)
            self._conn.putheader("Accept", "*/*")
            self._conn.putheader("Content-Type", "application/octet-stream")
            self._conn.putheader("Content-Length", str(total))
            self._conn.putheader("Connection", "close")
            self._conn.endheaders()
            if self._cancel.wait(HEADER_BODY_PAUSE):
                self._finish(UploadResult.CANCELLED, None, "cancelled by user")
                self._close()
                return

            last_report = 0.0
            view = memoryview(self._data)
            while sent < total:
                if self._cancel.is_set():
                    self._finish(UploadResult.CANCELLED, None, "cancelled by user")
                    return
                chunk = view[sent:sent + CHUNK_SIZE]
                self._conn.send(chunk)
                sent += len(chunk)
                pct = sent * 100 // total if total else 100
                if pct >= next_log_pct:
                    el = time.monotonic() - t0
                    self._log("d", "MKS upload: %d%% (%d/%d bytes) after %.1fs, %.1f KB/s"
                              % (pct, sent, total, el, sent / 1024 / max(el, 0.001)))
                    next_log_pct = (pct // 25 + 1) * 25
                now = time.monotonic()
                if now - last_report >= PROGRESS_INTERVAL or sent == total:
                    last_report = now
                    self._emit_progress(sent, total)
        except Exception as e:
            if self._cancel.is_set():
                self._finish(UploadResult.CANCELLED, None, "cancelled by user")
            else:
                self._finish(UploadResult.FAILED, None,
                             "sending failed after %d/%d bytes, %.1fs: %r"
                             % (sent, total, time.monotonic() - t0, e))
            self._close()
            return

        # Body completely sent -> wait for the module's answer.
        try:
            if self._conn.sock is not None:
                self._conn.sock.settimeout(RESPONSE_TIMEOUT)
            t_body = time.monotonic()
            response = self._conn.getresponse()
            body = response.read(512)
            status = response.status
            detail = body.decode("utf-8", "replace").strip()
            self._log("d", "MKS upload: answer after %.1fs: HTTP %s %s, headers=%s, body=%r"
                      % (time.monotonic() - t_body, status, response.reason,
                         dict(response.getheaders()), detail))
            if 200 <= status < 300:
                err = self.parse_answer(detail)
                if err == 0:
                    self._finish(UploadResult.OK, status, detail)
                elif err is None:
                    # HTTP OK but no recognizable answer -> not confirmed
                    self._finish(UploadResult.OK_NO_RESPONSE, status, detail)
                else:
                    self._finish(UploadResult.REJECTED, status, detail)
            else:
                self._finish(UploadResult.HTTP_ERROR, status, detail)
        except (http.client.HTTPException, ConnectionError, socket.timeout, OSError) as e:
            if self._cancel.is_set():
                self._finish(UploadResult.CANCELLED, None, "cancelled by user")
            else:
                # All bytes went out but no answer arrived. Not confirmed: the
                # caller shows a warning and re-reads the SD file list.
                self._finish(UploadResult.OK_NO_RESPONSE, None, "no valid HTTP response: %r" % (e,))
        finally:
            self._close()

    def _close(self):
        conn, self._conn = self._conn, None
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
