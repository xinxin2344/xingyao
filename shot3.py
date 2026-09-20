import websocket
import json
import base64
import time

WS_URL = "ws://localhost:9230/devtools/page/2DB0EC928B8C9E4CA9AB3772CD6EC899"
OUT = r"C:\Users\tang\Desktop\质量\site\screenshots"

ws = websocket.create_connection(WS_URL)
_id = 0

def send(method, params=None):
    global _id
    _id += 1
    msg = {"id": _id, "method": method, "params": params or {}}
    ws.send(json.dumps(msg))
    return _id

def wait_resp(target_id):
    while True:
        raw = ws.recv()
        try:
            o = json.loads(raw)
            if o.get("id") == target_id:
                return o
        except:
            pass

def evaluate(expr):
    mid = send("Runtime.evaluate", {"expression": expr, "returnByValue": True})
    r = wait_resp(mid)
    return r.get("result", {}).get("result", {}).get("value")

def shot_element(selector, filepath, padding=20):
    """截取指定元素区域"""
    rect = evaluate(f"""
        (function() {{
            var el = document.querySelector('{selector}');
            if (!el) return null;
            var r = el.getBoundingClientRect();
            return {{x: r.left, y: r.top, w: r.width, h: r.height}};
        }})()
    """)
    if not rect:
        print(f"element not found: {selector}")
        return False
    clip = {
        "x": max(0, rect["x"] - padding),
        "y": max(0, rect["y"] - padding),
        "width": rect["w"] + padding * 2,
        "height": rect["h"] + padding * 2,
        "scale": 1
    }
    mid = send("Page.captureScreenshot", {"format": "png", "fromSurface": True, "clip": clip})
    r = wait_resp(mid)
    data = r.get("result", {}).get("data")
    if data:
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(data))
        print(f"saved {filepath}")
        return True
    print(f"failed {filepath}")
    return False

def shot_full(filepath):
    mid = send("Page.captureScreenshot", {"format": "png", "fromSurface": True})
    r = wait_resp(mid)
    data = r.get("result", {}).get("data")
    if data:
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(data))
        print(f"saved {filepath}")

# 1. SPC - X-R 控制图（截取图表区域）
evaluate("location.hash = '#/spc'")
time.sleep(3)
# 找控制图的 canvas
shot_element("canvas", f"{OUT}\\xr-chart.png", padding=30)

# 2. QC 七大手法 - 鱼骨图
evaluate("location.hash = '#/qc-seven'")
time.sleep(3)
# 鱼骨图可能是 canvas 或 svg，截取
shot_element("canvas, svg", f"{OUT}\\fishbone.png", padding=30)

# 3. MSA - 截取图表
evaluate("location.hash = '#/msa'")
time.sleep(3)
shot_element("canvas", f"{OUT}\\msa-chart.png", padding=30)

# 4. 主界面全截
evaluate("location.hash = '/'")
time.sleep(2)
shot_full(f"{OUT}\\main.png")

ws.close()
print("done")
