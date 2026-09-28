# Offline copy: handing the files out on a USB stick

**Claude itself needs the internet.** The workshop can't run without Wi-Fi, because Claude runs on Anthropic's servers. The offline copy is for the case where the Wi-Fi works but is slow, or the website can't be reached: the slides (16 MB), the handout, the setup guide and the practice files still reach everyone.

---

## 1. Build the bundle

```bash
python build.py --offline
```

This makes `dist/How_to_actually_use_Claude_offline.zip`, with the whole site and every file it links to. It refuses to build if any page links to a missing file, so if the bundle exists, all its links work.

The official help pages on the After page are outside links, so they still need the internet.

## 2. Hand it out

Copy the zip to a few USB sticks and pass them round. People unzip it anywhere and **double-click `index.html`**. They need no web server and no internet.

The practice files are inside, at `Labs/practice-files.zip`. People extract that zip into **Documents**, as in step 7 of the setup guide.

To serve it over the room's network instead, run this in the unzipped folder:

```bash
python -m http.server 8000
```

People then go to `http://<your-laptop-ip>:8000`.

## Pre-flight checklist (the day before)

- [ ] `python build.py --check` passes.
- [ ] Unzip the bundle into a new folder and open `index.html` by double-clicking it.
- [ ] Every page loads, with the logo and styling.
- [ ] The slides, handout and setup guide open.
- [ ] `practice-files.zip` downloads and extracts to a `Claude-Practice` folder.
- [ ] Spare USB sticks are ready.

## Known limits

- **Outside links** (the Claude download page and the official help pages) need the internet.
- **PDFs** open in the browser's built-in viewer. A few locked-down laptops block PDFs opened from `file://`. If that happens, use the `python -m http.server` route.
