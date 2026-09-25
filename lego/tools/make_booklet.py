#!/usr/bin/env python3
"""
Builds lego/booklet/index.html (the instruction booklet) from booklet/steps.json
and the pictures render.mjs made in booklet/img/.

  python3 lego/tools/make_booklet.py
"""
import base64, collections, html, json, os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOK = os.path.join(HERE, "booklet")
D = json.load(open(os.path.join(BOOK, "steps.json")))
COL, PARTS = D["colors"], D["parts"]
E = html.escape


def part_img(part, color):
    f = os.path.join(BOOK, "img", f"part_{part}_{color}.webp")
    if not os.path.exists(f):
        return ""
    return "data:image/webp;base64," + base64.b64encode(open(f, "rb").read()).decode()


IMG = {}
for model in D["bom"]:
    for r in D["bom"][model]:
        IMG[(r["part"], r["color"])] = part_img(r["part"], r["color"])


def swatch(color):
    c = COL[str(color)]
    cls = " any" if color < 0 else ""
    return f'<span class="sw{cls}" style="--c:{c["hex"]}"></span>'


def callout(parts):
    if not parts:
        return ""
    cells = []
    for p in parts:
        c = COL[str(p["color"])]
        name = PARTS[p["part"]]["name"]
        cells.append(
            f'<figure class="pc" title="{E(name)}, {E(c["name"])}">'
            f'<img src="{IMG[(p["part"], p["color"])]}" alt="{E(name)} in {E(c["name"])}" width="110" height="90">'
            f'<figcaption><b>{p["qty"]}x</b><span>{E(c["name"] if p["color"] >= 0 else "any colour")}</span></figcaption></figure>')
    return f'<div class="callout">{"".join(cells)}</div>'


def bom_table(model):
    rows = D["bom"][model]
    groups = collections.OrderedDict()
    for r in sorted(rows, key=lambda r: (r["color"] < 0, r["color_name"], {"brick": 0, "plate": 1, "tile": 2, "hinge": 3}[PARTS[r["part"]]["kind"]], r["part"])):
        groups.setdefault(r["color_name"], []).append(r)
    out = []
    for cname, rs in groups.items():
        n = sum(r["qty"] for r in rs)
        color = rs[0]["color"]
        label = "Hidden inside: any colour works" if color < 0 else cname
        out.append(f'<tr class="grp"><th colspan="5">{swatch(color)} {E(label)} <span class="n">{n} parts</span></th></tr>')
        for r in rs:
            key = f"{model}-{r['part']}-{r['color']}"
            blc = f" · colour {r['bl_color']}" if r["bl_color"] is not None else ""
            out.append(
                f'<tr><td class="ck"><input type="checkbox" id="ck-{key}" data-k="{key}" aria-label="Got these"></td>'
                f'<td class="im"><img src="{IMG[(r["part"], r["color"])]}" alt="" width="66" height="54" loading="lazy"></td>'
                f'<td class="q">{r["qty"]}x</td><td>{E(r["name"])}</td>'
                f'<td class="id">{E(r["bl"])}{blc}</td></tr>')
    return f'<div class="tw"><table class="bom"><tbody>{"".join(out)}</tbody></table></div>'


def steps_html(model):
    out, n, section = [], 0, None
    for i, s in enumerate(D["steps"]):
        if s["model"] != model:
            continue
        n += 1
        if s["section"] != section:
            section = s["section"]
            sub = s["asm"] in ("scrawny_tail", "buff_tail", "buff_arm_l", "buff_arm_r") and s["kind"] == "build"
            out.append(f'<h3 class="sec{" subbuild" if sub else ""}" id="{model}-{n}">{E(section.split(": ", 1)[-1])}'
                       f'{"<small>separate sub-build</small>" if sub else ""}</h3>')
        note = f'<p class="note">{E(s["note"])}</p>' if s.get("note") else ""
        prog = f'<span class="prog">{E(s["sub"])}</span>' if s.get("sub") else ""
        out.append(
            f'<article class="step{" attach" if s["kind"] == "attach" else ""}">'
            f'<div class="sn">{n}</div>{prog}{callout(s["parts"])}{note}'
            f'<img class="shot" src="img/step_{i + 1:03d}.webp" alt="Step {n}" width="960" height="720" loading="lazy">'
            f'</article>')
    return "\n".join(out)


st = D["stats"]
buff_in = st["buff"]["height_mm"] / 25.4
scr_in = st["scrawny"]["height_mm"] / 25.4
nsteps = {m: sum(1 for s in D["steps"] if s["model"] == m) for m in ("scrawny", "buff")}

page = f"""<title>Squirrel Power Suit</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Pixelify+Sans:wght@500;700&family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400&family=JetBrains+Mono:wght@500&display=swap">
<style>
:root {{
  --paper:#ffffff; --ink:#1d232b; --muted:#5d6874; --line:#d9e0e7;
  --callout:#e4eef6; --callout-edge:#b9cfe0; --fur:#7a3d1c; --grass:#4f8a35; --sub:#fff6e9; --sub-edge:#e7cfa8;
  --shot:#ffffff;
  --display:"Pixelify Sans", "Courier New", monospace;
  --body:"Atkinson Hyperlegible", system-ui, sans-serif;
  --mono:"JetBrains Mono", ui-monospace, monospace;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    color-scheme: dark;
    --paper:#15191e; --ink:#e8ecf0; --muted:#9aa6b2; --line:#2c343d;
    --callout:#1f2d3a; --callout-edge:#34506a; --fur:#e0a079; --grass:#8cc46d; --sub:#2a2219; --sub-edge:#5a4629;
  }}
}}
:root[data-theme="dark"] {{
  color-scheme: dark;
  --paper:#15191e; --ink:#e8ecf0; --muted:#9aa6b2; --line:#2c343d;
  --callout:#1f2d3a; --callout-edge:#34506a; --fur:#e0a079; --grass:#8cc46d; --sub:#2a2219; --sub-edge:#5a4629;
}}
* {{ box-sizing:border-box; }}
body {{ background:var(--paper); color:var(--ink); font:16px/1.55 var(--body); padding-inline:16px; }}
.wrap {{ max-width:1000px; margin:0 auto; padding-block:24px 80px; display:grid; gap:48px; }}
h1,h2,h3 {{ font-family:var(--display); font-weight:700; line-height:1.1; text-wrap:balance; margin:0; }}
h1 {{ font-size:clamp(40px,8vw,76px); color:var(--fur); letter-spacing:.5px; }}
h2 {{ font-size:34px; color:var(--fur); }}
p {{ margin:0; max-width:65ch; }}
.eyebrow {{ font-family:var(--mono); font-size:12px; letter-spacing:.12em; text-transform:uppercase; color:var(--grass); }}
header.cover {{ display:grid; gap:14px; }}
.hero {{ width:100%; height:auto; background:var(--shot); border-radius:6px; }}
.facts {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:12px; }}
.fact {{ border:2px solid var(--line); border-radius:6px; padding:14px 16px; display:grid; gap:4px; }}
.fact b {{ font-family:var(--display); font-size:22px; }}
.fact span {{ color:var(--muted); font-size:14px; font-variant-numeric:tabular-nums; }}
nav.toc {{ display:flex; flex-wrap:wrap; gap:8px; }}
nav.toc a {{ font-family:var(--display); font-size:17px; color:var(--ink); text-decoration:none; border:2px solid var(--line); border-radius:4px; padding:6px 12px; }}
nav.toc a:hover, nav.toc a:focus-visible {{ border-color:var(--fur); outline:none; }}
section {{ display:grid; gap:18px; }}
.two {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); gap:16px; align-items:start; }}
.two figure {{ margin:0; display:grid; gap:6px; }}
.two figcaption {{ color:var(--muted); font-size:14px; }}
ul.tips {{ margin:0; padding-left:20px; display:grid; gap:8px; max-width:70ch; }}
.sw {{ display:inline-block; width:14px; height:14px; border-radius:3px; background:var(--c); border:1px solid rgba(0,0,0,.35); vertical-align:-2px; }}
.sw.any {{ background:repeating-linear-gradient(45deg,#a0a5a9 0 3px,#d4d8db 3px 6px); }}
.colors {{ display:flex; flex-wrap:wrap; gap:8px 18px; font-size:15px; }}
.tw {{ overflow-x:auto; }}
table.bom {{ border-collapse:collapse; width:100%; font-size:15px; }}
.bom td {{ border-bottom:1px solid var(--line); padding:4px 8px; vertical-align:middle; }}
.bom tr.grp th {{ text-align:left; font-family:var(--display); font-size:19px; padding:18px 8px 6px; }}
.bom .n {{ font-family:var(--body); font-size:13px; color:var(--muted); font-weight:400; margin-left:6px; }}
.bom .q {{ font-weight:700; font-variant-numeric:tabular-nums; white-space:nowrap; }}
.bom .id {{ font-family:var(--mono); font-size:12.5px; color:var(--muted); white-space:nowrap; }}
.bom .im img {{ display:block; background:#fff; border-radius:4px; }}
.bom input {{ width:20px; height:20px; accent-color:var(--grass); }}
.bom tr.got td {{ opacity:.45; }}
details.model > summary {{ cursor:pointer; font-family:var(--display); font-size:20px; padding:8px 0; }}
h3.sec {{ font-size:26px; padding:10px 0 4px; border-bottom:3px solid var(--fur); display:flex; align-items:baseline; gap:12px; flex-wrap:wrap; }}
h3.sec small {{ font-family:var(--mono); font-size:12px; letter-spacing:.1em; text-transform:uppercase; color:var(--muted); }}
h3.subbuild {{ border-bottom-color:var(--sub-edge); }}
.step {{ position:relative; border-bottom:1px solid var(--line); padding-block:14px; display:grid; gap:10px; }}
.step .sn {{ font-family:var(--display); font-weight:700; font-size:44px; line-height:1; }}
.step .prog {{ position:absolute; right:0; top:18px; font-family:var(--mono); font-size:12px; color:var(--muted); }}
.step .shot {{ width:100%; height:auto; background:var(--shot); border-radius:6px; }}
.step.attach {{ background:var(--sub); border:2px solid var(--sub-edge); border-radius:8px; padding:14px; }}
.callout {{ display:flex; flex-wrap:wrap; gap:6px; background:var(--callout); border:2px solid var(--callout-edge); border-radius:8px; padding:8px; width:fit-content; max-width:100%; }}
.pc {{ margin:0; display:grid; justify-items:center; gap:0; width:110px; }}
.pc img {{ background:#fff; border-radius:4px; width:110px; height:auto; }}
.pc figcaption {{ display:grid; justify-items:center; font-size:13px; line-height:1.2; padding-top:3px; }}
.pc b {{ font-size:17px; font-variant-numeric:tabular-nums; }}
.pc span {{ color:var(--muted); font-size:11.5px; }}
.note {{ font-size:17px; font-weight:700; }}
.small {{ color:var(--muted); font-size:14px; }}
code {{ font-family:var(--mono); font-size:.9em; }}
@media (max-width:520px) {{ .pc {{ width:84px; }} .pc img {{ width:84px; }} .step .sn {{ font-size:34px; }} }}
</style>

<div class="wrap">
<header class="cover">
  <span class="eyebrow">LEGO build · from the Minecraft squirrel mod</span>
  <h1>Squirrel Power Suit</h1>
  <p>Two builds in one box. The little scrawny squirrel is a Minecraft squirrel made of bricks. The buff squirrel is what he turns into when a monster shows up, and he's hollow: lift off his top half and the scrawny squirrel rides inside.</p>
  <img class="hero" src="img/hero_pair.webp" alt="The buff squirrel standing next to the little scrawny squirrel" width="1600" height="1100">
  <div class="facts">
    <div class="fact"><b>Scrawny squirrel</b><span>{st['scrawny']['parts']} parts · {nsteps['scrawny']} steps · {scr_in:.1f} in tall with tail up</span></div>
    <div class="fact"><b>Buff squirrel</b><span>{st['buff']['parts']} parts · {nsteps['buff']} steps · {buff_in:.1f} in tall · about {st['buff']['grams'] / 1000 * 2.2046:.1f} lb</span></div>
    <div class="fact"><b>Moves</b><span>Tails click up and down. Buff arms click out sideways to flex.</span></div>
  </div>
  <nav class="toc" aria-label="Sections">
    <a href="#suit">How the suit works</a><a href="#start">Before you start</a><a href="#parts">Parts lists</a>
    <a href="#scrawny">Build the scrawny squirrel</a><a href="#buff">Build the buff squirrel</a><a href="#play">Posing</a>
  </nav>
</header>

<section id="suit">
  <h2>How the suit works</h2>
  <p>The buff squirrel splits at the chest. The bottom half is a cup the scrawny squirrel stands in, with his tail clicked straight up. The top half (chest, head and arms) drops on like a lid. Four little stud patches on the rim line it up and hold it; everywhere else on the rim is smooth tiles, so it lifts off without a fight.</p>
  <div class="two">
    <figure><img class="hero" src="img/hero_suit.webp" alt="Scrawny squirrel standing inside the bottom half" width="1200" height="1000" loading="lazy"><figcaption>Scrawny squirrel in the bottom half, tail up.</figcaption></figure>
    <figure><img class="hero" src="img/hero_lid.webp" alt="The top half lifted above the bottom half" width="1100" height="1500" loading="lazy"><figcaption>Lower the top half straight down.</figcaption></figure>
  </div>
</section>

<section id="start">
  <h2>Before you start</h2>
  <div class="colors">{"".join(f'<span>{swatch(int(k))} {E(v["name"])}</span>' for k, v in COL.items() if int(k) in (70, 308, 19, 84, 0, 15, -1))}</div>
  <ul class="tips">
    <li><b>Grey in the pictures means any colour.</b> Those parts are hidden inside the walls, so use whatever you have lots of.</li>
    <li><b>Faded parts</b> in a picture are from earlier steps. The bright ones are what you add now.</li>
    <li><b>Pale boxes</b> are sub-builds: tails and arms get built on their own, then clicked on.</li>
    <li><b>Parts that hang in the air</b> (like the underside of the head) show up in the step where the part above them is ready. Press them on from underneath.</li>
    <li><b>Medium Nougat</b> (the tail colour) is the rarest colour here. Nougat, Dark Orange or plain Reddish Brown all look fine instead.</li>
    <li>The black hinge pieces are locking click hinges: 30364 / 30365 bricks and 44301 / 44302 plates.</li>
  </ul>
</section>

<section id="parts">
  <h2>Parts lists</h2>
  <p class="small">Tick parts off as you pull them from the bins. Ticks are saved in this browser. Numbers on the right are BrickLink part and colour numbers; the repo has BrickLink wanted-list files in <code>lego/bricklink/</code>.</p>
  <details class="model"><summary>Scrawny squirrel: {st['scrawny']['parts']} parts</summary>{bom_table('scrawny')}</details>
  <details class="model"><summary>Buff squirrel: {st['buff']['parts']} parts</summary>{bom_table('buff')}</details>
</section>

<section id="scrawny">
  <h2>Build the scrawny squirrel</h2>
  {steps_html('scrawny')}
</section>

<section id="buff">
  <h2>Build the buff squirrel</h2>
  <p>Build the bottom half first, then the tail, then the top half and both arms. The top half is built right side up, starting from the ring that sits on the rim.</p>
  {steps_html('buff')}
</section>

<section id="play">
  <h2>Posing</h2>
  <div class="two">
    <figure><img class="hero" src="img/hero_buff.webp" alt="Buff squirrel flexing with arms raised" width="1200" height="1300" loading="lazy"><figcaption>Arms click out sideways from hanging down to straight out.</figcaption></figure>
    <figure><img class="hero" src="img/hero_scrawny.webp" alt="Scrawny squirrel" width="1200" height="900" loading="lazy"><figcaption>Tails tilt back a few clicks. Swing the scrawny tail straight up before he suits up.</figcaption></figure>
  </div>
  <p class="small">Designed by a script that turns the Minecraft squirrel's boxes into bricks: <code>lego/tools/squirrel_lego.py</code>. Open <code>lego/models/*.mpd</code> in BrickLink Studio to spin the models in 3D.</p>
</section>
</div>

<script>
(function () {{
  var boxes = document.querySelectorAll('.bom input[type=checkbox]');
  var saved = {{}};
  try {{ saved = JSON.parse(localStorage.getItem('squirrel-parts') || '{{}}'); }} catch (e) {{}}
  boxes.forEach(function (b) {{
    if (saved[b.dataset.k]) {{ b.checked = true; b.closest('tr').classList.add('got'); }}
    b.addEventListener('change', function () {{
      saved[b.dataset.k] = b.checked;
      b.closest('tr').classList.toggle('got', b.checked);
      try {{ localStorage.setItem('squirrel-parts', JSON.stringify(saved)); }} catch (e) {{}}
    }});
  }});
}})();
</script>
"""
open(os.path.join(BOOK, "index.html"), "w").write(page)
print("wrote", os.path.join(BOOK, "index.html"), f"{len(page) / 1e6:.1f} MB")
