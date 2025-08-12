#!/usr/bin/env python3
import os
import re
import sys
import time
import requests
from urllib.parse import urlparse, unquote

PROD_VERSION = "9999.0.0.0"
UA_CHROME = "Mozilla/5.0 (Linux; Android 12; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
UA_EDGE = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"

def get_save_dir():
    candidates = [
        os.path.join(os.path.expanduser("~"), "storage", "shared", "Extensions"),
        "/sdcard/Extensions",
        "/storage/emulated/0/Extensions",
    ]
    for path in candidates:
        try:
            os.makedirs(path, exist_ok=True)
            # test write permission
            tf = os.path.join(path, ".write_test")
            with open(tf, "w") as f:
                f.write("ok")
            os.remove(tf)
            return path
        except Exception:
            continue
    raise RuntimeError("Cannot write to shared storage. Run: termux-setup-storage")

def build_url(kind, ext_id):
    x = f"id%3D{ext_id}%26installsource%3Dondemand%26uc"
    qs = f"response=redirect&acceptformat=crx3&prodversion={PROD_VERSION}&x={x}"
    if kind == "chrome":
        return f"https://clients2.google.com/service/update2/crx?{qs}"
    elif kind == "edge":
        return f"https://edge.microsoft.com/extensionwebstorebase/v1/crx?{qs}"
    else:
        raise ValueError("Unknown store")

def pick_filename(headers, ext_id, dest_dir):
    cd = headers.get("Content-Disposition") or ""
    name = None
    m = re.search(r'filename\*=(?:UTF-8|utf-8)\'\'([^;]+)', cd)
    if m:
        name = unquote(m.group(1))
    else:
        m = re.search(r'filename="?([^";]+)"?', cd)
        if m:
            name = m.group(1)
    if not name:
        name = f"{ext_id}.crx"
    name = re.sub(r'[\\/:*?"<>|]+', "_", name)  # sanitize
    base, ext = os.path.splitext(name)
    final = name
    i = 1
    while os.path.exists(os.path.join(dest_dir, final)):
        final = f"{base} ({i}){ext}"
        i += 1
    return final

def print_progress(downloaded, total, start_time):
    mb_dl = downloaded / (1024 * 1024)
    if total:
        mb_total = total / (1024 * 1024)
        percent = downloaded * 100.0 / total
        bar_len = 30
        done = int(bar_len * downloaded / total)
        bar = "#" * done + "-" * (bar_len - done)
        elapsed = max(1e-6, time.time() - start_time)
        speed = (downloaded / (1024 * 1024)) / elapsed
        msg = f"[{bar}] {mb_dl:.2f} MB / {mb_total:.2f} MB ({percent:.1f}%)  {speed:.2f} MB/s"
    else:
        elapsed = max(1e-6, time.time() - start_time)
        speed = (downloaded / (1024 * 1024)) / elapsed
        msg = f"{mb_dl:.2f} MB  {speed:.2f} MB/s"
    print("\r" + msg + " " * 8, end="", flush=True)

def download_crx(url, dest_dir, ext_id, ua):
    with requests.Session() as s:
        s.headers.update({"User-Agent": ua})
        with s.get(url, stream=True, allow_redirects=True, timeout=60) as r:
            if r.status_code != 200:
                raise RuntimeError(f"HTTP {r.status_code} from server")
            total = int(r.headers.get("Content-Length", "0") or 0)
            filename = pick_filename(r.headers, ext_id, dest_dir)
            out_path = os.path.join(dest_dir, filename)
            chunk = 64 * 1024
            downloaded = 0
            start = time.time()
            try:
                with open(out_path, "wb") as f:
                    for data in r.iter_content(chunk_size=chunk):
                        if not data:
                            continue
                        f.write(data)
                        downloaded += len(data)
                        print_progress(downloaded, total, start)
                print()  # newline after progress
            except KeyboardInterrupt:
                print("\nCanceled. Removing partial file.")
                try:
                    os.remove(out_path)
                except Exception:
                    pass
                raise SystemExit(1)
    return out_path, total

def choose_menu():
    print("\nChoose store:")
    print("  1) Chrome Extensions (Web Store)")
    print("  2) Edge Extensions (Add-ons)")
    while True:
        choice = input("> ").strip()
        if choice == "1":
            return "chrome"
        if choice == "2":
            return "edge"
        print("Please enter 1 or 2.")

def extract_id(s):
    s = s.strip()
    if s.startswith("http://") or s.startswith("https://"):
        path = urlparse(s).path
        segs = [seg for seg in path.split("/") if seg]
        for seg in reversed(segs):
            if re.fullmatch(r"[a-z]{32}", seg.lower()):
                return seg.lower()
        # if not found, fall back
        return s
    return s.lower()

def ask_id():
    raw = input("Enter the extension ID (or paste the store URL): ").strip()
    ext_id = extract_id(raw)
    if not re.fullmatch(r"[a-z]{32}", ext_id):
        print("Note: extension IDs are usually 32 lowercase letters. Continuing anyway...")
    return ext_id

def main():
    print("Extension Fetcher v2.0 By GrayWizard888")
    print("------------------------------")
    try:
        dest_dir = get_save_dir()
    except Exception as e:
        print(f"Error: {e}")
        print("Tip: run 'termux-setup-storage' and re-run.")
        sys.exit(1)

    print(f"Save directory: {dest_dir}")
    kind = choose_menu()
    ext_id = ask_id()
    url = build_url(kind, ext_id)
    ua = UA_CHROME if kind == "chrome" else UA_EDGE

    print(f"\nDownloading from {kind.title()}...")
    try:
        path, total = download_crx(url, dest_dir, ext_id, ua)
        size_info = f" ({total / (1024*1024):.2f} MB)" if total else ""
        print(f"Saved: {path}{size_info}")
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
