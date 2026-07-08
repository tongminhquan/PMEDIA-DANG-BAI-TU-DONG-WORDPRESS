from __future__ import annotations

import base64
import ctypes
import sys
from ctypes import wintypes


_DPAPI_PREFIX = "dpapi:"
_FALLBACK_PREFIX = "plain64:"
_ENTROPY = b"PMEDIA WordPress Auto Poster connection profiles v1"


class _DataBlob(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_char)),
    ]


def protect_secret(value: str) -> str:
    if not value:
        return ""
    raw = value.encode("utf-8")
    if sys.platform == "win32":
        try:
            return _DPAPI_PREFIX + base64.b64encode(_dpapi_protect(raw)).decode("ascii")
        except Exception:
            pass
    return _FALLBACK_PREFIX + base64.b64encode(raw).decode("ascii")


def unprotect_secret(value: str) -> str:
    if not value:
        return ""
    if value.startswith(_DPAPI_PREFIX):
        encrypted = base64.b64decode(value[len(_DPAPI_PREFIX) :])
        return _dpapi_unprotect(encrypted).decode("utf-8")
    if value.startswith(_FALLBACK_PREFIX):
        return base64.b64decode(value[len(_FALLBACK_PREFIX) :]).decode("utf-8")
    return value


def _dpapi_protect(raw: bytes) -> bytes:
    crypt32 = ctypes.windll.crypt32
    in_blob, in_buffer = _blob_from_bytes(raw)
    entropy_blob, entropy_buffer = _blob_from_bytes(_ENTROPY)
    out_blob = _DataBlob()
    ok = crypt32.CryptProtectData(
        ctypes.byref(in_blob),
        None,
        ctypes.byref(entropy_blob),
        None,
        None,
        0,
        ctypes.byref(out_blob),
    )
    del in_buffer, entropy_buffer
    if not ok:
        raise ctypes.WinError()
    return _bytes_from_blob(out_blob)


def _dpapi_unprotect(encrypted: bytes) -> bytes:
    crypt32 = ctypes.windll.crypt32
    in_blob, in_buffer = _blob_from_bytes(encrypted)
    entropy_blob, entropy_buffer = _blob_from_bytes(_ENTROPY)
    out_blob = _DataBlob()
    ok = crypt32.CryptUnprotectData(
        ctypes.byref(in_blob),
        None,
        ctypes.byref(entropy_blob),
        None,
        None,
        0,
        ctypes.byref(out_blob),
    )
    del in_buffer, entropy_buffer
    if not ok:
        raise ctypes.WinError()
    return _bytes_from_blob(out_blob)


def _blob_from_bytes(data: bytes) -> tuple[_DataBlob, ctypes.Array]:
    buffer = ctypes.create_string_buffer(data)
    blob = _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char)))
    return blob, buffer


def _bytes_from_blob(blob: _DataBlob) -> bytes:
    try:
        return ctypes.string_at(blob.pbData, blob.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(blob.pbData)
