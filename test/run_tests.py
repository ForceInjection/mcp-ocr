import os
import json
import sys
import time
from typing import Dict, Any, List

# 将 src 加入路径，便于导入包
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mcp_ocr_server.mcp_server import KimiFileOCR, validate_api_key_format, mask_key, get_api_key
from urllib import request, error


def api_connection_test(base_url: str, api_key: str, timeout: int = 5) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}/files"
    req = request.Request(url=url, method="GET")
    req.add_header("Authorization", f"Bearer {api_key}")
    try:
        t0 = time.monotonic()
        with request.urlopen(req, timeout=timeout) as resp:
            _ = resp.read()
            dt = time.monotonic() - t0
            return {"success": True, "status": resp.status, "latency_ms": int(dt * 1000)}
    except error.HTTPError as e:
        return {"success": False, "status": e.code, "error": e.reason}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_extract_text(ocr: KimiFileOCR, file_path: str) -> Dict[str, Any]:
    t0 = time.monotonic()
    try:
        text = ocr.extract_text_from_image(file_path)
        dt = time.monotonic() - t0
        ok = isinstance(text, str) and len(text.strip()) > 0
        return {"success": ok, "length": len(text) if isinstance(text, str) else 0, "latency_ms": int(dt * 1000)}
    except Exception as e:
        dt = time.monotonic() - t0
        return {"success": False, "error": str(e), "latency_ms": int(dt * 1000)}


def main() -> None:
    proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    test_dir = os.path.join(proj_root, "image")
    img_paths: List[str] = [os.path.join(test_dir, "1.png"), os.path.join(test_dir, "2.png")]

    results: Dict[str, Any] = {
        "key": {"present": False, "valid": False},
        "api_connection": {"success": False},
        "cases": [],
        "summary": {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "success_rate": 0.0,
            "avg_upload_ms": None,
            "avg_extract_ms": None,
        },
    }

    env_key = os.environ.get("MOONSHOT_API_KEY", "")

    api_key = get_api_key() or ""
    results["key"]["present"] = bool(api_key)
    results["key"]["valid"] = validate_api_key_format(api_key) if api_key else False

    base_url = os.environ.get("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
    if api_key:
        conn = api_connection_test(base_url, api_key)
        results["api_connection"] = conn

    ocr = None
    if api_key:
        try:
            ocr = KimiFileOCR(api_key=api_key, base_url=base_url, timeout_seconds=int(os.environ.get("REQUEST_TIMEOUT_SECONDS", "10")))
        except Exception as e:
            results["api_connection"] = {"success": False, "error": str(e)}

    extract_times: List[int] = []

    for p in img_paths:
        case: Dict[str, Any] = {"file": os.path.basename(p), "exists": os.path.exists(p)}
        if not case["exists"]:
            case["extract"] = {"success": False, "error": "file not found"}
            results["cases"].append(case)
            continue
        if not ocr:
            case["extract"] = {"success": False, "error": "no client"}
            results["cases"].append(case)
            continue
        
        ex = test_extract_text(ocr, p)
        case["extract"] = ex
        if ex.get("success"):
            extract_times.append(ex.get("latency_ms", 0))
        results["cases"].append(case)

    total = len(results["cases"])
    passed = sum(1 for c in results["cases"] if c.get("upload", {}).get("success") and c.get("extract", {}).get("success"))
    failed = total - passed
    sr = (passed / total) if total else 0.0
    results["summary"]["total"] = total
    results["summary"]["passed"] = passed
    results["summary"]["failed"] = failed
    results["summary"]["success_rate"] = round(sr * 100.0, 2)
    results["summary"]["avg_upload_ms"] = None
    results["summary"]["avg_extract_ms"] = int(sum(extract_times) / len(extract_times)) if extract_times else None

    print(json.dumps(results, ensure_ascii=False))


if __name__ == "__main__":
    main()