#!/usr/bin/env python3
"""
Build the course website from course.toml.

The markup and stylesheet are a faithful replication of the existing KAUST
Academy course sites (ported from 2026_Aramco_Data_Science): same class names,
same structure, byte-identical style.css. The difference is that the pages are
generated from one data file instead of hand-written seven times.

Zero dependencies — Python 3.11+ standard library only. No Ruby, no npm, no
network access at any point, so the site can be rebuilt on a locked-down
laptop in a classroom.

    python3 build.py              # build _site/
    python3 build.py --check      # build, then verify every link resolves
    python3 build.py --offline    # build, then zip a USB-ready bundle
    python3 build.py --serve      # build, then serve on http://localhost:8000

Every path it emits is relative, so the same output tree works served by
GitHub Pages and opened straight off a USB stick.
"""

from __future__ import annotations

import argparse
import html
import shutil
import sys
import zipfile
from pathlib import Path
from urllib.parse import quote

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
    sys.exit(
        "This needs Python 3.11 or newer (for tomllib).\n"
        f"You are running {sys.version.split()[0]} from {sys.executable}"
    )

ROOT = Path(__file__).resolve().parent
SITE = ROOT / "_site"
DIST = ROOT / "dist"

# Copied verbatim into the built site. They are what makes the bundle work
# with no network: the PDFs and notebooks travel with the HTML.
CONTENT_DIRS = ("Slides", "Labs", "Extra")

# The inline script from the original pages. style.css defines .navbar-mobile
# in nine places, so this is load-bearing — it is what opens the mobile menu.
NAV_SCRIPT = """  <script>
    const on = (type, el, listener, all = false) => {
      let selectEl = document.querySelector(el);
      if (selectEl) {
        selectEl.addEventListener(type, listener);
      }
    }

    on('click', '.mobile-nav-toggle', function (e) {
      document.querySelector('#navbar').classList.toggle('navbar-mobile')
      this.classList.toggle('bi-list')
      this.classList.toggle('bi-x')
    })
  </script>"""


def e(text: object) -> str:
    """Escape for HTML. Everything from course.toml goes through this."""
    return html.escape(str(text), quote=True)


def para(text: str) -> str:
    """Collapse a TOML multi-line string into one paragraph."""
    return " ".join(str(text).split())


def url(path: str) -> str:
    """Encode a repo-relative path for href, keeping '/' separators."""
    return quote(path.replace("\\", "/"), safe="/")


# --------------------------------------------------------------------------
# Chrome — replicated from the original pages
# --------------------------------------------------------------------------

def head(title: str, remixicon: bool) -> str:
    """The <head>. Only the home page loads remixicon (only it uses ri-* icons)."""
    ri = '\n  <link href="assets/vendor/remixicon/remixicon.css" rel="stylesheet">' if remixicon else ""
    return f"""<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="utf-8">
  <meta content="width=device-width, initial-scale=1.0" name="viewport">
  <title>{e(title)}</title>

  <!-- CSS Files -->
  <link href="assets/vendor/bootstrap/css/bootstrap.min.css" rel="stylesheet">
  <link href="assets/vendor/bootstrap-icons/bootstrap-icons.css" rel="stylesheet">{ri}
  <link href="assets/css/style.css" rel="stylesheet">
</head>

<body>
"""


def header(days: list[dict], current: str, show_extra: bool = True) -> str:
    """Home page centres the nav; inner pages push the logo left. As in the original."""
    items = [("index", "Home", "index.html")]
    items += [(d["slug"], d["label"], f'{d["slug"]}.html') for d in days]
    if show_extra:
        items += [("extra", "Extra", "extra.html")]

    links = "\n".join(
        f'          <li><a{" class=\"active\"" if slug == current else ""} href="{href}">{e(label)}</a></li>'
        for slug, label, href in items
    )

    if current == "index":
        container = '<div class="container d-flex align-items-center justify-content-between">'
        logo_cls, nav_cls = "logo", "navbar"
    else:
        container = '<div class="container d-flex align-items-center">'
        logo_cls, nav_cls = "logo me-auto", "navbar order-last order-lg-0"

    return f"""  <!-- ======= Header ======= -->
  <header id="header" class="fixed-top">
    {container}

      <div class="{logo_cls}">
        <a href="index.html">
          <img src="assets/img/kaust-academy-logo.png" alt="KAUST Academy">
        </a>
      </div>

      <nav id="navbar" class="{nav_cls}">
        <ul>
{links}
        </ul>
        <i class="bi bi-list mobile-nav-toggle"></i>
      </nav>

    </div>
  </header>
"""


def footer(course: dict) -> str:
    repo = course.get("repo", "")
    lic = e(course.get("license", "GPL-3.0"))
    link = (
        f'<a\n            href="https://github.com/{e(repo)}?tab=GPL-3.0-1-ov-file#readme"\n'
        f'            target="_blank" rel="noopener">{lic}</a>'
        if repo else lic
    )
    return f"""  <footer id="footer">
    <div class="container d-md-flex py-4">
      <div class="me-md-auto text-center w-100">
        <div class="copyright">
          &copy; Copyright <strong><span>{e(course.get('provider', 'KAUST Academy'))}</span></strong>. All Rights Reserved
        </div>
        <div class="license" style="font-size: 13px; margin-top: 8px; color: #555;">
          Licensed under {link}.
          {e(course.get('license_note', ''))}
        </div>
      </div>
    </div>
  </footer>
"""


# --------------------------------------------------------------------------
# Resource table — .table-container / .custom-table / .table-btn
# --------------------------------------------------------------------------

def resource_row(r: dict) -> str:
    name = e(r.get("name", "Untitled"))
    detail = e(r.get("detail", ""))
    status = r.get("status", "todo")

    if status != "ready":
        action = (
            '<span style="color: #888; font-size: 14px; font-style: italic;">Coming soon</span>'
        )
    else:
        btns = []
        if r.get("file"):
            label = r.get("button") or ("Notebook" if r.get("kind") == "lab" else "Open")
            btns.append(f'<a href="{url(r["file"])}" class="table-btn">{e(label)}</a>')
        if r.get("link"):
            # An outside page (a form, official docs). It needs internet, so it
            # opens in a new tab and never replaces a file that should travel
            # with the site.
            btns.append(
                f'<a href="{e(r["link"])}" class="table-btn" target="_blank" rel="noopener">'
                f'{e(r.get("button") or "Open")}</a>'
            )
        if r.get("colab"):
            # Kept alongside the local file, not instead of it: this course is
            # delivered with no internet, and Colab needs some.
            btns.append(
                f'<a href="{e(r["colab"])}" class="table-btn" target="_blank" rel="noopener">Colab</a>'
            )
        action = " ".join(btns) or '<span style="color: #888;">Coming soon</span>'

    return f"""            <tr>
              <td><strong>{name}</strong></td>
              <td>{detail}</td>
              <td class="text-center">{action}</td>
            </tr>"""


def resource_table(resources: list[dict]) -> str:
    rows = "\n".join(resource_row(r) for r in resources)
    return f"""    <div class="container mb-5 animate-up delay-100">
      <div class="table-container">
        <table class="custom-table">
          <thead>
            <tr>
              <th scope="col" style="width: 25%">Topic</th>
              <th scope="col">Description &amp; Objectives</th>
              <th scope="col" style="width: 20%; text-align: center;">Resource</th>
            </tr>
          </thead>
          <tbody>
{rows}
          </tbody>
        </table>
      </div>
    </div>"""


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------

DELAYS = ["delay-100", "delay-200", "delay-300"]


def render_index(course: dict, days: list[dict], show_extra: bool = True) -> str:
    confetti = "\n".join(
        f'      <div class="confetti-shape confetti-{i}"></div>' for i in range(1, 13)
    )
    cards = "\n\n".join(
        f"""          <div class="col-lg-4 col-md-6 d-flex align-items-stretch mb-4 animate-up {DELAYS[i % 3]}">
            <div class="icon-box w-100">
              <i class="{e(d.get('icon', 'ri-function-line'))}"></i>
              <h3><a href="{d['slug']}.html">{e(d['label'])}: {e(d['title'])}</a></h3>
              <p>{e(para(d.get('blurb', '')))}</p>
            </div>
          </div>"""
        for i, d in enumerate(days)
    )

    summary = para(course.get("summary", ""))
    summary_html = (
        f"""
        <div class="row justify-content-center animate-up delay-200">
          <div class="col-lg-9 text-center">
            <p style="font-size: 17px; line-height: 1.7; color: var(--text-grey); margin-top: 16px;">{e(summary)}</p>
          </div>
        </div>
"""
        if summary else ""
    )

    return f"""{head(course.get('title', 'Course'), remixicon=True)}
{header(days, 'index', show_extra)}
  <!-- ======= Hero Section ======= -->
  <section id="hero">
    <!-- Confetti shapes -->
    <div class="hero-confetti">
{confetti}
    </div>
    <div class="container text-center animate-up">
      <h1><span>{e(course.get('title_lead', ''))}</span> <br>{e(course.get('title_rest', ''))}</h1>
      <h2 class="animate-up delay-100">{e(para(course.get('tagline', '')))}</h2>
    </div>
  </section>

  <main id="main">

    <section id="features" class="features" style="padding: 60px 0;">
      <div class="container">

        <div class="section-title text-center mb-5 animate-up">
          <p style="color: var(--primary-red); font-weight: bold; letter-spacing: 1px;">{e(course.get('schedule_label', 'COURSE SCHEDULE'))}</p>
          <h3>{e(course.get('schedule_title', 'Daily Breakdown'))}</h3>
        </div>

        <div class="row">
{cards}

        </div>
{summary_html}      </div>
    </section>

  </main>

{footer(course)}
{NAV_SCRIPT}

</body>

</html>
"""


def render_day(course: dict, days: list[dict], day: dict, show_extra: bool = True) -> str:
    title = f"{day['label']} - {day['title']}"
    return f"""{head(title, remixicon=False)}
{header(days, day['slug'], show_extra)}
  <main id="main">
    <div class="breadcrumbs animate-up">
      <div class="container">
        <h2>{e(day['label'])}: {e(day['title'])}</h2>
        <p>{e(para(day.get('blurb', '')))}</p>
      </div>
    </div>

{resource_table(day.get('resources', []))}
  </main>

{NAV_SCRIPT}

</body>

</html>
"""


def render_extra(course: dict, days: list[dict], extra: list[dict]) -> str:
    return f"""{head('Extra - Additional Resources', remixicon=False)}
{header(days, 'extra')}
  <main id="main">
    <div class="breadcrumbs animate-up">
      <div class="container">
        <h2>Extra Resources</h2>
        <p>Additional materials and references shared during the course.</p>
      </div>
    </div>

{resource_table(extra)}
  </main>

{NAV_SCRIPT}

</body>

</html>
"""


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------

def load() -> dict:
    with open(ROOT / "course.toml", "rb") as fh:
        return tomllib.load(fh)


def build() -> dict:
    data = load()
    course = data.get("course", {})
    days = data.get("days", [])
    extra = data.get("extra", [])

    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)

    # theme/ -> _site/assets/, preserving the css/ img/ vendor/ layout the
    # markup references.
    shutil.copytree(
        ROOT / "theme", SITE / "assets",
        ignore=shutil.ignore_patterns(".DS_Store", ".gitkeep"),
    )

    for name in CONTENT_DIRS:
        src = ROOT / name
        if src.is_dir():
            shutil.copytree(
                src, SITE / name,
                ignore=shutil.ignore_patterns(".gitkeep", ".DS_Store", ".ipynb_checkpoints"),
            )

    # No [[extra]] blocks -> no Extra page and no Extra link in the nav.
    show_extra = bool(extra)
    (SITE / "index.html").write_text(render_index(course, days, show_extra), encoding="utf-8")
    for d in days:
        (SITE / f"{d['slug']}.html").write_text(render_day(course, days, d, show_extra), encoding="utf-8")
    if show_extra:
        (SITE / "extra.html").write_text(render_extra(course, days, extra), encoding="utf-8")
    (SITE / ".nojekyll").write_text("", encoding="utf-8")

    print(f"built {1 + len(days) + show_extra} pages -> {SITE.relative_to(ROOT)}/")
    return data


def check(data: dict) -> int:
    """Verify every ready resource points at a file that exists."""
    problems: list[str] = []
    todo = ready = 0

    groups = [(d["label"], d.get("resources", [])) for d in data.get("days", [])]
    groups.append(("Extra", data.get("extra", [])))

    for label, resources in groups:
        for r in resources:
            name = r.get("name", "?")
            if r.get("status", "todo") != "ready":
                todo += 1
                continue
            ready += 1
            f, link = r.get("file"), r.get("link")
            if not f and not link:
                problems.append(f"{label}: '{name}' is ready but has no `file` or `link`")
            if f and not (ROOT / f).exists():
                problems.append(f"{label}: '{name}' -> missing file {f}")
            if link and not str(link).startswith("https://"):
                problems.append(f"{label}: '{name}' -> link must start with https:// ({link})")

    linked = {r["file"] for _, rs in groups for r in rs if r.get("file")}
    # as_posix(): course.toml paths use '/', and on Windows str() would give '\'.
    orphans = [
        p.relative_to(ROOT).as_posix()
        for name in ("Slides", "Labs")
        for p in sorted((ROOT / name).rglob("*"))
        if p.is_file() and p.name not in (".gitkeep", ".DS_Store")
        and p.relative_to(ROOT).as_posix() not in linked
    ]

    print(f"\nlinks: {ready} ready, {todo} coming soon")
    for o in orphans:
        print(f"  orphan (in repo, not on any page): {o}")
    for p in problems:
        print(f"  BROKEN: {p}")

    if problems:
        print(f"\n{len(problems)} broken link(s).")
        return 1
    print("all links resolve.")
    return 0


def offline(data: dict) -> None:
    DIST.mkdir(exist_ok=True)
    course = data.get("course", {})
    stem = course.get("title", "course").replace(" ", "_").replace("(", "").replace(")", "")
    target = DIST / f"{stem}_offline.zip"
    extras = [p for p in (ROOT / "OFFLINE.md", ROOT / "requirements.txt") if p.exists()]

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(SITE.rglob("*")):
            if p.is_file():
                z.write(p, Path(stem) / p.relative_to(SITE))
        for p in extras:
            z.write(p, Path(stem) / p.name)

    print(f"\noffline bundle -> {target.relative_to(ROOT)} ({target.stat().st_size / 1_048_576:.1f} MB)")
    print("  unzip it, open index.html — no server and no internet needed.")


def serve() -> None:
    import http.server
    import socketserver

    handler = lambda *a, **k: http.server.SimpleHTTPRequestHandler(  # noqa: E731
        *a, directory=str(SITE), **k
    )
    with socketserver.TCPServer(("", 8000), handler) as httpd:
        print("serving _site/ at http://localhost:8000  (ctrl-c to stop)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print()


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--check", action="store_true", help="verify every link resolves")
    ap.add_argument("--offline", action="store_true", help="zip a USB-ready bundle")
    ap.add_argument("--serve", action="store_true", help="preview on localhost:8000")
    args = ap.parse_args()

    data = build()
    rc = check(data) if (args.check or args.offline) else 0
    if args.offline and rc == 0:
        offline(data)
    if args.serve and rc == 0:
        serve()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
