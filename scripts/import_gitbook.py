#!/usr/bin/env python3
"""
Import de la documentation GitBook de la Ruche numérique vers MkDocs.

À lancer une seule fois, depuis la racine du dépôt :

    python scripts/import_gitbook.py

Le script :
  1. lit l'index https://ruche-numerique.gitbook.io/documentation/llms.txt ;
  2. télécharge chaque page au format Markdown (.md) ;
  3. convertit la syntaxe propre à GitBook (encadrés, étapes, onglets,
     renvois, embeds) en syntaxe MkDocs Material ;
  4. réécrit les liens internes en liens relatifs ;
  5. écrit les fichiers dans docs/ et génère les fichiers .pages
     qui fixent l'ordre du menu.

Aucune dépendance externe : bibliothèque standard Python 3.8+.
"""

import os
import re
import sys
import time
import urllib.request
from urllib.parse import urlparse

BASE = "https://ruche-numerique.gitbook.io/documentation"
SPACE_PREFIX = "/documentation/"
DOCS_DIR = os.path.join(os.path.dirname(__file__), "..", "docs")
# Page d'accueil GitBook -> docs/index.md
HOME_SLUG = "bienvenue-a-la-ruche"
# Pages déjà rédigées à la main dans le dépôt, à ne pas écraser
PROTECTED = {"index.md", "contribuer.md"}

HINT_TYPES = {
    "info": "info",
    "success": "success",
    "warning": "warning",
    "danger": "danger",
    "tip": "tip",
}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "ruche-doc-import/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


# ---------------------------------------------------------------- index

def parse_llms(txt: str):
    """Retourne une liste ordonnée de (slug, titre, section)."""
    pages, section = [], None
    for line in txt.splitlines():
        h = re.match(r"^#{2,3}\s+(.+)", line)
        if h:
            section = h.group(1).strip()
            continue
        m = re.search(r"\[([^\]]+)\]\((https?://[^)]+)\)", line)
        if not m:
            continue
        title, url = m.group(1), m.group(2)
        path = urlparse(url).path
        if not path.startswith(SPACE_PREFIX):
            continue
        slug = path[len(SPACE_PREFIX):]
        slug = re.sub(r"\.md$", "", slug).strip("/")
        if slug and slug not in [p[0] for p in pages]:
            pages.append((slug, title, section))
    return pages


# ----------------------------------------------------------- conversion

def strip_agent_footer(md: str) -> str:
    # Supprime le bloc « Agent Instructions » ajouté par GitBook
    md = re.split(r"\n---\s*\n+# Agent Instructions", md)[0]
    # Supprime l'en-tête « For the complete documentation index… »
    md = re.sub(r"^>\s*For the complete documentation index.*?\n\n", "", md, flags=re.S)
    return md.strip() + "\n"


def indent(text: str, n: int = 4) -> str:
    pad = " " * n
    return "\n".join(pad + l if l.strip() else "" for l in text.strip("\n").splitlines())


def convert_hints(md: str) -> str:
    pat = re.compile(r'{%\s*hint\s+style="(\w+)"\s*%}(.*?){%\s*endhint\s*%}', re.S)

    def repl(m):
        kind = HINT_TYPES.get(m.group(1), "note")
        body = m.group(2).strip()
        # Si l'encadré commence par une ligne en gras, on en fait le titre
        t = re.match(r"^\*\*(.+?)\*\*\s*(.*)$", body, re.S)
        if t and "\n" not in t.group(1):
            title, rest = t.group(1).rstrip(" :."), t.group(2).strip()
            return f'!!! {kind} "{title}"\n{indent(rest or title)}\n'
        return f"!!! {kind}\n{indent(body)}\n"

    return pat.sub(repl, md)


def convert_steppers(md: str) -> str:
    step_pat = re.compile(r"{%\s*step\s*%}(.*?){%\s*endstep\s*%}", re.S)

    def stepper(m):
        steps = step_pat.findall(m.group(1))
        out = []
        for i, s in enumerate(steps, 1):
            s = s.strip()
            h = re.match(r"^#{1,6}\s+(.+?)\n+(.*)$", s, re.S)
            if h:
                title, rest = h.group(1).strip(), h.group(2).strip()
                out.append(f"{i}. **{title}**" + (f" —\n{indent(rest, 3)}" if rest else ""))
            else:
                out.append(f"{i}. {indent(s, 3).lstrip()}")
        return "\n".join(out) + "\n"

    return re.sub(r"{%\s*stepper\s*%}(.*?){%\s*endstepper\s*%}", stepper, md, flags=re.S)


def convert_tabs(md: str) -> str:
    tab_pat = re.compile(r'{%\s*tab\s+title="([^"]+)"\s*%}(.*?){%\s*endtab\s*%}', re.S)

    def tabs(m):
        return "\n".join(
            f'=== "{t}"\n\n{indent(b)}\n' for t, b in tab_pat.findall(m.group(1))
        )

    return re.sub(r"{%\s*tabs\s*%}(.*?){%\s*endtabs\s*%}", tabs, md, flags=re.S)


def convert_expandables(md: str) -> str:
    # <details><summary>…</summary> … </details> -> ??? note
    pat = re.compile(r"<details>\s*<summary>(.*?)</summary>(.*?)</details>", re.S)
    return pat.sub(lambda m: f'??? note "{m.group(1).strip()}"\n{indent(m.group(2))}\n', md)


def convert_content_refs(md: str) -> str:
    pat = re.compile(r'{%\s*content-ref\s+url="[^"]*"\s*%}(.*?){%\s*endcontent-ref\s*%}', re.S)
    return pat.sub(lambda m: f":material-arrow-right: {m.group(1).strip()}\n", md)


def convert_embeds(md: str) -> str:
    md = re.sub(r'{%\s*embed\s+url="([^"]+)"\s*%}(.*?){%\s*endembed\s*%}',
                lambda m: f"[{m.group(2).strip() or m.group(1)}]({m.group(1)})", md, flags=re.S)
    md = re.sub(r'{%\s*embed\s+url="([^"]+)"\s*%}', r"<\1>", md)
    return md


def convert_file_blocks(md: str) -> str:
    return re.sub(r'{%\s*file\s+src="([^"]+)"\s*%}(.*?){%\s*endfile\s*%}',
                  lambda m: f"[{m.group(2).strip() or 'Fichier'}]({m.group(1)})", md, flags=re.S)


def rewrite_links(md: str, target: str, sections=frozenset()) -> str:
    depth = target.count("/")
    up = "../" * depth

    def fix(target: str) -> str:
        t = target
        if t.startswith(BASE):
            t = t[len(BASE):]
        if t.startswith(SPACE_PREFIX):
            t = t[len(SPACE_PREFIX):]
        elif t.startswith("/") and not t.startswith("//"):
            t = t[1:]
        else:
            return target
        anchor = ""
        if "#" in t:
            t, anchor = t.split("#", 1)
            anchor = "#" + anchor
        t = t.strip("/")
        t = re.sub(r"\.md$", "", t)
        if t in ("", HOME_SLUG):
            t = "index"
        elif t in sections:
            # une page de section vit dans son dossier : embarquer -> embarquer/index
            t = t + "/index"
        return f"{up}{t}.md{anchor}"

    return re.sub(r"\]\(([^)\s]+)\)", lambda m: f"]({fix(m.group(1))})", md)


def cleanup(md: str) -> str:
    md = re.sub(r"{%\s*[^%]*%}", "", md)          # balises GitBook restantes
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip() + "\n"


def convert(md: str, target: str, sections=frozenset()) -> str:
    md = strip_agent_footer(md)
    for f in (convert_hints, convert_steppers, convert_tabs, convert_expandables,
              convert_content_refs, convert_embeds, convert_file_blocks):
        md = f(md)
    md = rewrite_links(md, target, sections)
    return cleanup(md)


# ------------------------------------------------------------------ main

def find_sections(pages):
    """Slugs qui ont des pages filles : leur page devient l'accueil du dossier."""
    slugs = [s for s, _, _ in pages]
    return {s for s in slugs if any(o.startswith(s + "/") for o in slugs)}


def target_for(slug: str, sections) -> str:
    if slug == HOME_SLUG:
        return "index.md"
    if slug in sections:
        return slug + "/index.md"
    return slug + ".md"


def write_pages_files(pages, sections):
    """Écrit les fichiers .pages qui fixent l'ordre du menu, dossier par dossier."""
    order = {}
    titles = {}
    for slug, title, _ in pages:
        target = target_for(slug, sections)
        if slug in sections:
            titles[slug] = title
        parts = target.split("/")
        for i in range(len(parts)):
            folder = "/".join(parts[:i])
            entry = parts[i]
            order.setdefault(folder, [])
            if entry not in order[folder]:
                order[folder].append(entry)
    for folder, entries in order.items():
        path = os.path.join(DOCS_DIR, folder, ".pages")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        extra = [] if folder else ["contribuer.md"]
        # index.md en tête : c'est la page d'accueil de la section
        if "index.md" in entries:
            entries = ["index.md"] + [e for e in entries if e != "index.md"]
        with open(path, "w", encoding="utf-8") as f:
            # sans ça le menu afficherait le nom du dossier, sans accents
            if folder in titles:
                f.write(f"title: {titles[folder]}\n")
            f.write("nav:\n")
            for e in entries + [x for x in extra if x not in entries]:
                f.write(f"  - {e}\n")
            f.write("  - ...\n")


def main():
    print("Lecture de l'index…")
    pages = parse_llms(fetch(f"{BASE}/llms.txt"))
    if not pages:
        sys.exit("Aucune page trouvée dans llms.txt — vérifie que le site est public.")
    print(f"{len(pages)} pages trouvées.")
    sections = find_sections(pages)

    errors = []
    for slug, title, _ in pages:
        target = target_for(slug, sections)
        dest = os.path.join(DOCS_DIR, target)
        if target in PROTECTED and os.path.exists(dest):
            print(f"  = {target} (conservé)")
            continue
        try:
            raw = fetch(f"{BASE}/{slug}.md")
        except Exception as e:  # noqa: BLE001
            errors.append((slug, str(e)))
            print(f"  ! {slug} : {e}")
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(convert(raw, target, sections))
        print(f"  + {target}")
        time.sleep(0.3)

    write_pages_files(pages, sections)

    leftovers = []
    for root, _, files in os.walk(DOCS_DIR):
        for fn in files:
            if fn.endswith(".md"):
                p = os.path.join(root, fn)
                if "{%" in open(p, encoding="utf-8").read():
                    leftovers.append(os.path.relpath(p, DOCS_DIR))

    print("\nTerminé.")
    if errors:
        print(f"{len(errors)} page(s) non récupérée(s) : " + ", ".join(s for s, _ in errors))
    if leftovers:
        print("Syntaxe GitBook résiduelle à vérifier à la main : " + ", ".join(leftovers))
    print("Les images restent hébergées chez GitBook : à rapatrier dans docs/assets/ "
          "si le site GitBook doit être fermé.")


if __name__ == "__main__":
    main()
