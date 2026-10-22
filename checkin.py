#!/usr/bin/env python3
"""Trae 每日自动签到脚本（由 GitHub Actions 定时触发，无需电脑开机）。

用法：
    设置环境变量 TRAE_TOKEN 为 Trae 登录令牌后运行：
        python3 checkin.py

行为：
    1. 查询今日签到状态；
    2. 若今日已签到则跳过（避免重复操作）；
    3. 若未签到则调用领取接口。
"""
import json
import os
import sys
import urllib.error
import urllib.request

API_BASE = "https://api.trae.cn/trae/api/v2/ug/checkin_credits"
TOKEN = os.environ.get("TRAE_TOKEN", "").strip()


def call(endpoint: str) -> dict:
    req = urllib.request.Request(
        f"{API_BASE}/{endpoint}",
        data=json.dumps({"req_source": 1}).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Cloud-IDE-JWT {TOKEN}",
            "x-device-brand": "Windows",
            "x-device-type": "Windows",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[FAIL] HTTP {e.code}: {body}")
        # 401/403 说明令牌失效或账号风控，需要人工刷新令牌
        sys.exit(2 if e.code in (401, 403) else 1)


def main() -> None:
    if not TOKEN:
        print("[FAIL] 缺少 TRAE_TOKEN 环境变量（GitHub Secrets 中未配置）")
        sys.exit(1)

    status = call("status")
    print(f"[状态] {json.dumps(status, ensure_ascii=False)}")

    if not status.get("enable"):
        print("[提示] 签到功能当前未开放，跳过")
        return

    if status.get("checked_in"):
        print("[跳过] 今日已签到，无需重复操作")
        return

    result = call("claim")
    print(f"[签到] {json.dumps(result, ensure_ascii=False)}")
    if result.get("code") == 0:
        print("[成功] 今日签到完成")
    else:
        print(f"[失败] 签到未成功：{result.get('message')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
