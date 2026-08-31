#!/usr/bin/env python3
"""Store the shared Typecast API key without printing it."""

from __future__ import annotations

import argparse
import getpass
import shutil
import subprocess
import sys

from core.typecast import TYPECAST_KEYCHAIN_SERVICE


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Store the shared Typecast API key in the existing Shorts keychain service."
    )
    parser.parse_args()
    if sys.platform != "darwin":
        print("macOS가 아니면 TYPECAST_API_KEY 환경변수를 사용하세요.", file=sys.stderr)
        return 1
    security = shutil.which("security")
    if not security:
        print("macOS security 명령을 찾을 수 없습니다.", file=sys.stderr)
        return 1
    print("표시되는 password 프롬프트에 Typecast API 키를 입력하세요. 입력값은 표시되지 않습니다.")
    result = subprocess.run(
        [
            security,
            "add-generic-password",
            "-U",
            "-a",
            getpass.getuser(),
            "-s",
            TYPECAST_KEYCHAIN_SERVICE,
            "-l",
            "AX YouTube Shorts Typecast API Key",
            "-w",
        ],
        check=False,
    )
    if result.returncode:
        print("Typecast API 키를 키체인에 저장하지 못했습니다.", file=sys.stderr)
        return result.returncode
    print("공통 Typecast API 키를 키체인에 저장했습니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
