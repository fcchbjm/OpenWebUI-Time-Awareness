"""Local smoke tests for the Open WebUI time awareness filter."""

import asyncio
from datetime import datetime
from importlib.machinery import SourceFileLoader
from pathlib import Path

import pytz

FUNCTION_PATH = Path(__file__).resolve().parent / "function"


def load_filter():
    module = SourceFileLoader("owui_filter", str(FUNCTION_PATH)).load_module()
    return module.Filter


async def run_tests():
    filter_cls = load_filter()
    filt = filter_cls()
    tz = pytz.timezone("Asia/Shanghai")

    body = {"messages": [{"role": "user", "content": "今天星期几？"}]}
    out = await filt.inlet(body)
    content = out["messages"][0]["content"]
    assert "当前系统时间" in content
    assert "星期" in content
    assert content.endswith("今天星期几？")
    print("Test 1 OK: basic injection")

    out2 = await filt.inlet(out)
    assert out2["messages"][0]["content"] == content
    print("Test 2 OK: dedupe")

    body3 = {
        "messages": [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
            {"role": "user", "content": "now?"},
        ]
    }
    out3 = await filt.inlet(body3)
    assert "当前系统时间" not in out3["messages"][0]["content"]
    assert "当前系统时间" in out3["messages"][2]["content"]
    print("Test 3 OK: last message only")

    ts = int(tz.localize(datetime(2026, 6, 1, 15, 30, 21)).timestamp() * 1000)
    filt.valves.template = "当前系统时间：{time}（{timezone}）"
    body4 = {"messages": [{"role": "user", "content": "q", "timestamp": ts}]}
    out4 = await filt.inlet(body4)
    assert "2026-06-01 15:30:21" in out4["messages"][0]["content"]
    print("Test 4 OK: ms timestamp")

    filt.valves.enabled = False
    body5 = {"messages": [{"role": "user", "content": "q"}]}
    out5 = await filt.inlet(body5)
    assert out5["messages"][0]["content"] == "q"
    filt.valves.enabled = True
    print("Test 5 OK: disabled")

    filt.valves.timezone = "Invalid/Zone"
    body6 = {"messages": [{"role": "user", "content": "q"}]}
    out6 = await filt.inlet(body6)
    assert "UTC" in out6["messages"][0]["content"]
    filt.valves.timezone = "Asia/Shanghai"
    print("Test 6 OK: invalid tz fallback")

    filt.valves.use_iso8601 = True
    body7 = {"messages": [{"role": "user", "content": "q"}]}
    out7 = await filt.inlet(body7)
    assert "T" in out7["messages"][0]["content"]
    filt.valves.use_iso8601 = False
    print("Test 7 OK: iso8601")

    body8 = {
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": "hello"}]}
        ]
    }
    out8 = await filt.inlet(body8)
    assert "当前系统时间" in out8["messages"][0]["content"][0]["text"]
    print("Test 8 OK: multimodal")

    filt.valves.template = "<system_time>{iso_time}</system_time>"
    body9 = {"messages": [{"role": "user", "content": "q"}]}
    out9a = await filt.inlet(body9)
    out9b = await filt.inlet(out9a)
    assert out9b["messages"][0]["content"].count("<system_time>") == 1
    print("Test 9 OK: custom template dedupe")

    filt.valves.template = "Time: {time}"
    body9c = {"messages": [{"role": "user", "content": "q"}]}
    out9c = await filt.inlet(body9c)
    out9d = await filt.inlet(out9c)
    assert out9d["messages"][0]["content"].count("Time:") == 1
    filt.valves.template = "当前系统时间：{time}（{timezone}）"
    print("Test 9b OK: generic template dedupe across seconds")

    body11 = {
        "messages": [{"role": "user", "content": "q", "timestamp": "1780299021000"}]
    }
    out11 = await filt.inlet(body11)
    assert "2026-06-01 15:30:21" in out11["messages"][0]["content"]
    print("Test 11 OK: string timestamp")

    filt.valves.inject_last_message_only = False
    filt.valves.template = "当前系统时间：{time}（{timezone}）"
    body10 = {
        "messages": [
            {"role": "user", "content": "first"},
            {"role": "user", "content": "second"},
        ]
    }
    out10 = await filt.inlet(body10)
    assert "当前系统时间" in out10["messages"][0]["content"]
    assert "当前系统时间" in out10["messages"][1]["content"]
    print("Test 10 OK: inject all user messages")

    # 纯图片：在 list 头部插入 text 块
    body12 = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.com/a.png"},
                    }
                ],
            }
        ]
    }
    out12 = await filt.inlet(body12)
    parts = out12["messages"][0]["content"]
    assert len(parts) == 2
    assert parts[0]["type"] == "text"
    assert "当前系统时间" in parts[0]["text"]
    assert parts[1]["type"] == "image_url"
    print("Test 12 OK: image-only injection")

    # 图文混合：prepend 到已有 text，保留图片
    body13 = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "这是什么？"},
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.com/b.png"},
                    },
                ],
            }
        ]
    }
    out13 = await filt.inlet(body13)
    parts13 = out13["messages"][0]["content"]
    assert len(parts13) == 2
    assert "当前系统时间" in parts13[0]["text"]
    assert parts13[0]["text"].endswith("这是什么？")
    assert parts13[1]["type"] == "image_url"
    print("Test 13 OK: text + image injection")

    # 纯图片防重复
    out12b = await filt.inlet(out12)
    assert len(out12b["messages"][0]["content"]) == 2
    print("Test 14 OK: image-only dedupe")

    # 空 text + 图片
    body15 = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": ""},
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.com/c.png"},
                    },
                ],
            }
        ]
    }
    out15 = await filt.inlet(body15)
    assert "当前系统时间" in out15["messages"][0]["content"][0]["text"]
    assert out15["messages"][0]["content"][1]["type"] == "image_url"
    print("Test 15 OK: empty text + image")

    print("ALL TESTS PASSED")


if __name__ == "__main__":
    asyncio.run(run_tests())
