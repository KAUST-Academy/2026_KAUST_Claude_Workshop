# How to actually use Claude: workshop website

The website for **"How to actually use Claude"**, a 90-minute hands-on workshop for the KAUST community by Ali Habibullah, KAUST Academy. Attendees use it to get set up before the session, to download the slides, handout and practice files, and to find the feedback form afterwards.

It is built from the KAUST Academy course-website template, so it looks like the other course sites. **Everything comes from one file.** Edit [`course.toml`](course.toml), run `python build.py --check`, and every page is rebuilt. Never hand-edit the HTML in `_site/`: the next build deletes it.

## The pages

| Page | What is on it |
|---|---|
| Home | The title, three cards (Before, During, After) and a short summary. |
| **Before**: Get set up | The setup guide (PDF), the Claude download page, and the practice files. |
| **During**: The workshop | The slides (PDF), the one-page handout, and the practice files again. |
| **After**: Keep going | The feedback form (shows "Coming soon" until it exists), and Claude's official help, Claude Code docs, privacy and pricing pages. |

The template's "days" are used for the three steps. There is no Extra page, because `course.toml` has no `[[extra]]` blocks.

## Layout

```
.
├── course.toml                 # ALL content. The only file most edits touch.
├── build.py                    # the generator. Standard library only.
├── Slides/How_to_Actually_Use_Claude.pdf
├── Extra/Setup_Guide.pdf       # the setup steps from the pre-workshop email
├── Extra/Handout.pdf           # the one-page cheat sheet
├── Labs/practice-files.zip     # made-up practice files; keep this exact name
├── theme/                      # the KAUST Academy theme, copied to _site/assets/
├── OFFLINE.md                  # handing the files out on a USB stick
├── _site/  dist/               # built output, git-ignored
└── .github/workflows/pages.yml # build and link-check on every push; deploy when enabled
```

**Keep the name `practice-files.zip`.** The setup guide, the email and the slides all tell people to right-click `practice-files.zip`, so the name on disk must match.

## Updating the materials

The PDFs and the zip are made in the workshop kit, not in this repo. After you change the deck, the handout, the email or the practice files there:

1. In the kit, run `python tools/export_pdf.py`. It rebuilds the deck PDF, `handout.pdf` and `setup-guide.pdf`. The setup guide is generated from `pre-workshop.md`, so it always matches the email.
2. If you changed the practice files, run `python tools/build_practice.py`.
3. Copy the files into this repo with `python tools/copy_to_website.py <this repo's folder>`, also from the kit. It renames them to the names above.
4. Here, run `python build.py --check`.

Only these four files come from the kit. Never copy in the kit's plans, notes, presenter folder or tools: they are for the presenter only.

## Building

You need **Python 3.11 or newer**, and nothing else.

```bash
python build.py --check      # build _site/ and verify every link  <- use this one
python build.py --serve      # build, then preview at http://localhost:8000
python build.py --offline    # build, check, then zip dist/How_to_actually_use_Claude_offline.zip
```

On a Mac or Linux, type `python3` instead of `python`.

`--check` fails the build if a page links to a file that doesn't exist, or if a ready row has neither a file nor a link. Test both ways the site is used: `--serve` is closest to GitHub Pages, and double-clicking `_site/index.html` is closest to the USB copy.

## Editing `course.toml`

A resource row looks like this:

```toml
  [[days.resources]]
  name   = "Slides"
  detail = "The whole deck, one slide per page"
  kind   = "slides"
  file   = "Slides/How_to_Actually_Use_Claude.pdf"
  status = "ready"
```

- `status = "todo"` shows the row greyed out as *Coming soon*. `status = "ready"` shows a button.
- `file` is a path in this repo. It is copied into the site, so it also works offline.

This site adds a few optional fields to the template. They are backward compatible: a `course.toml` without them builds as before.

| Field | Where | What it does |
|---|---|---|
| `link` | a resource | An outside page (`https://…` only), opened in a new tab. Use it for the feedback form and the official help pages. |
| `button` | a resource | The button's label, such as "Download". Default: "Open". |
| `schedule_label`, `schedule_title` | `[course]` | The heading above the home-page cards. Defaults: "COURSE SCHEDULE", "Daily Breakdown". |
| `summary` | `[course]` | Now shown as a paragraph under the home-page cards (the template read it but never showed it). |
| no `[[extra]]` blocks | — | No Extra page and no Extra link in the menu. |

### When the feedback form exists

In the After page's "Feedback form" row, add `link = "https://…"` and change `status` to `"ready"`, then build with `--check`.

### When the date and room are fixed

Add them to `tagline` in `[course]`, e.g. `"A 90-minute hands-on workshop by Ali Habibullah, KAUST Academy · 12 October, Building 19."`

## Deploying

`.github/workflows/pages.yml` runs `build.py --check` and `--offline` on every push and pull request to `main`. It deploys `_site/` to GitHub Pages only when both switches are on:

| Switch | Where |
|---|---|
| Repo **public** | Settings > General > Change visibility (Pages on the org's free plan needs it) |
| `DEPLOY_PAGES` = `true` | Settings > Secrets and variables > Actions > Variables |

With the repo `KAUST-Academy/2026_KAUST_Claude_Workshop`, the site address is `https://kaust-academy.github.io/2026_KAUST_Claude_Workshop/`. If you change the repo name, also change `repo` in `course.toml`, since it drives the footer licence link.

> Going public publishes everything in the repo, not just the site. Check that nothing here is private first. Going private again unpublishes the site.

## Conventions

- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/), for example `feat(during): add the updated slides` or `fix(before): correct the setup guide link`.
- **File names:** underscores, never spaces (`Title_Case_With_Underscores.pdf`). The one exception is `practice-files.zip`, whose name the instructions depend on.

## Known quirks from the template

- The label above the home-page cards uses `var(--primary-red)`, which the theme never defines, so it shows in the theme's orange heading style instead.
- The theme asks for the Raleway font but doesn't load it, so pages use the system font, like the other course sites.
- The Before, During and After pages have no footer. The copyright and the "recording not permitted" note appear on the home page only.

## License

GPL-3.0, as with other KAUST Academy course material. Recording and uploading lectures online is not permitted.
