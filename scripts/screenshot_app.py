import time
from playwright.sync_api import sync_playwright
PTS=[(90,232),(275,232),(275,262),(90,262)]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"]); pg=b.new_page(viewport={"width":1500,"height":1100})
    pg.goto("http://127.0.0.1:7861/"); pg.wait_for_timeout(3000)
    pg.locator("input[type=file]").first.set_input_files("data/gaithersburg_20s.mp4")
    pg.wait_for_timeout(6000)
    im=pg.locator("img").filter(has=pg.locator("xpath=.")).all()
    # tim anh khung hinh dau (anh lon nhat)
    imgs=[e for e in pg.locator("img").all() if (e.bounding_box() or {}).get("width",0)>300]
    el=imgs[0]; bb=el.bounding_box(); nw=el.evaluate("e=>e.naturalWidth"); nh=el.evaluate("e=>e.naturalHeight")
    for x,y in PTS:
        pg.mouse.click(bb["x"]+x*bb["width"]/nw, bb["y"]+y*bb["height"]/nh); pg.wait_for_timeout(900)
    pg.screenshot(path="docs/screenshots/01_zone_drawn.png", full_page=True)
    t0=time.time(); pg.get_by_role("button", name="4) Chạy").click()
    pg.get_by_text("Xong trong").wait_for(timeout=900000)
    print("run_s", round(time.time()-t0,1)); pg.wait_for_timeout(4000)
    pg.screenshot(path="docs/screenshots/02_results.png", full_page=True)
    print(pg.get_by_text("Xong trong").inner_text())
    b.close()
