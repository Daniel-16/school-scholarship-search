#!/usr/bin/env python3
"""Canonical dedup key for a programme or funding award, and an audit for state.

`/discover` Step 4 keys every seen_programs.json entry by provider+award. The
provider is the university for a taught or research programme and the funder
for a scholarship; the award is the programme name or the scheme name. Leaving
the rule as prose would let each run slugify in its own way, and the state file
would accumulate two distinct failures:

  * Keys carrying characters that break things downstream. `/apply` and
    `/outcome` derive an archive folder name from the same provider+award pair,
    and documents/README.md's subfolder rule exists because a "/" splits that
    path across directories. The shapes that bite here are real:
    "university-of-x_msc-data-science-(ai/ml)",
    "daad_epos-development-related-postgraduate-courses,-m.sc.".

  * The same award stored twice under different keys, because one run truncated
    the name at a different point than the next. A funding call re-listed with
    "2027/28" appended is one scheme, one URL, two entries - and dedup is the
    whole point of the file.

Both are fixed by making the key a pure, deterministic function of the listing.
Truncation is length-capped *and* disambiguated by a hash of the full slug, so a
long programme name always produces the same key and two different long names
never collide.

A name that slugifies to nothing (a programme listed in a non-Latin script) has
no usable key half at all, and it would collide with every future non-Latin
listing from that provider. Those fall back to the portal's numeric id from the
URL. A name or provider that slugifies to *less* than it says is the same
problem one step on: "Информатика" and "Математика" both fold to "", "Universität
Köln" keeps its Latin fragment but "東京大学 AI" and "京都大学 AI" both fold to
"ai", so whenever the ASCII fold drops letters the surviving fragment is only a
readable prefix and the identity comes from the same fallback.

Usage:
  python3 tools/program_key.py --provider "TU Delft" --award "MSc Robotics"
  python3 tools/program_key.py --audit program_search/seen_programs.json

Exit 0 when a key is produced, or when an audit finds nothing. Exit 1 when an
audit finds violations.
"""

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "program_search" / "seen_programs.json"

PROVIDER_MAX = 40
AWARD_MAX = 60
HASH_LEN = 6

# Anything outside this set becomes a separator. Deliberately strict: "/" and
# "," are the characters that actually break archive paths, and an allowlist
# cannot be surprised by the next punctuation mark a portal invents.
_NON_SLUG = re.compile(r"[^a-z0-9]+")
_LISTING_ID = re.compile(r"(\d{4,})")


def slugify(text: str) -> str:
    """Lowercase ASCII slug. Non-Latin scripts legitimately reduce to ''."""
    if not text:
        return ""
    decomposed = unicodedata.normalize("NFKD", str(text))
    ascii_only = decomposed.encode("ascii", "ignore").decode("ascii")
    return _NON_SLUG.sub("-", ascii_only.lower()).strip("-")


def _lost_letters(text: str) -> bool:
    """True when the ASCII fold dropped non-Latin letters, so the slug under-identifies.

    NFKD turns "ü" into "u" plus a combining mark and "ﬁ" into "fi", so most
    Latin text keeps every letter. A Cyrillic, Greek, CJK or Arabic letter has
    no ASCII decomposition and vanishes; a mixed-script name then keeps only
    its Latin or digit fragment, and two different names can share it.

    Latin letters that also lack a decomposition ("ø", "æ", "ß", "ł") are
    deliberately NOT counted: "Ørsted" keys as "rsted", and treating that as
    lossy would re-key every Nordic university in a live seen_programs.json
    for a collision that does not happen in practice.
    """
    if not text:
        return False
    for ch in unicodedata.normalize("NFKD", str(text)):
        if ord(ch) < 128 or not ch.isalpha():
            continue
        if not unicodedata.name(ch, "LATIN").startswith("LATIN"):
            return True
    return False


def _cap(slug: str, limit: int) -> str:
    """Cap length without making truncation lossy across runs.

    A bare truncation is what produces duplicate entries: two runs cut the same
    programme name at different points and the file gains a second key for one
    award. Appending a hash of the *full* slug makes the result deterministic
    for a given name and distinct for any other.
    """
    if len(slug) <= limit:
        return slug
    digest = hashlib.sha1(slug.encode("utf-8")).hexdigest()[:HASH_LEN]
    return f"{slug[:limit].rstrip('-')}-{digest}"


def make_key(provider: str, award: str, url: str = "") -> str:
    """The canonical seen_programs.json key for one programme or funding award."""
    provider_slug = _cap(slugify(provider), PROVIDER_MAX)
    if not provider_slug or _lost_letters(provider):
        name = unicodedata.normalize("NFC", str(provider or "").strip().casefold())
        # An absent provider stays unknown; a non-Latin one still has an
        # identity. A mixed-script name keeps its Latin fragment as a readable
        # prefix, but the identity is the hash.
        digest = hashlib.sha1(name.encode("utf-8")).hexdigest()[:HASH_LEN]
        if not name:
            provider_slug = "unknown-provider"
        else:
            provider_slug = f"{provider_slug}-{digest}" if provider_slug else f"provider-{digest}"
    award_slug = _cap(slugify(award), AWARD_MAX)
    if not award_slug or _lost_letters(award):
        # No Latin characters in the award name, or not enough of them to
        # identify it. The portal's own numeric id is the stable handle; a
        # surviving fragment stays as a readable prefix only. Never emit a bare
        # "provider_" prefix.
        #
        # A fragment that is only digits is dropped rather than kept. On a
        # non-Latin title the digits that survive the ASCII fold are almost
        # always the intake year - "Программа 2026" folds to "2026" - so
        # keeping them made the key change when a funder re-listed the same
        # call for the next cycle, storing one award twice. That is the exact
        # failure this whole helper exists to prevent, and a year is not a
        # readable prefix worth the cost.
        fragment = "" if award_slug.replace("-", "").isdigit() else award_slug
        match = _LISTING_ID.search(url or "")
        if match:
            award_slug = f"{fragment}-{match.group(1)}" if fragment else match.group(1)
        else:
            basis = slugify(unicodedata.normalize("NFKD", str(award or url or "")))
            # Hash the URL alone when there is one. The URL is the listing's
            # identity; the name is not. Including the name made the key change
            # whenever a portal re-listed the same award with the title altered
            # ("2026 intake" -> "2027 intake"), which stores one award twice -
            # the failure this whole helper exists to prevent. With no URL, the
            # name is all that is left to key on.
            digest_basis = str(url) if url else str(award)
            digest = hashlib.sha1(digest_basis.encode("utf-8")).hexdigest()[:HASH_LEN]
            award_slug = f"{fragment}-{digest}" if fragment else (basis or f"untitled-{digest}")
    return f"{provider_slug}_{award_slug}"


# A canonical key is "<provider-slug>_<award-slug>": lowercase alphanumerics and
# hyphens on either side of exactly one underscore. The underscore is the
# separator, so it is the one character outside the slug alphabet that belongs.
_CANONICAL = re.compile(r"^[a-z0-9][a-z0-9-]*_[a-z0-9][a-z0-9-]*$")


def is_canonical(key: str) -> bool:
    """Structurally safe as a dedup key and as an archive folder name."""
    return bool(key) and bool(_CANONICAL.match(key))


def is_legacy_shape(key: str) -> bool:
    """Old three-part "provider_award_country" keys.

    Harmless - they carry no path-breaking character - but they are not what
    make_key produces, so a later run would store the same award under a new
    key and reintroduce a duplicate. Reported apart from real damage so the fix
    stays a decision rather than an automatic rename.
    """
    return bool(key) and key.count("_") > 1 and all(
        re.fullmatch(r"[a-z0-9][a-z0-9-]*", part) for part in key.split("_") if part
    )


def audit(path: Path) -> int:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read {path}: {exc}", file=sys.stderr)
        return 1
    seen = doc.get("seen", doc) if isinstance(doc, dict) else doc
    if not isinstance(seen, dict):
        print(f"{path}: expected an object of listing entries", file=sys.stderr)
        return 1
    not_objects = [k for k, v in seen.items() if not isinstance(v, dict)]
    if not_objects:
        print(f"{path}: entry is not an object: {not_objects[0]}", file=sys.stderr)
        return 1
    bad_url = [k for k, v in seen.items() if v.get("url") is not None and not isinstance(v["url"], str)]
    if bad_url:
        print(f"{path}: entry url is not a string: {bad_url[0]}", file=sys.stderr)
        return 1

    malformed = [k for k in seen if not is_canonical(k) and not is_legacy_shape(k)]
    legacy = [k for k in seen if is_legacy_shape(k)]
    by_url: dict[str, list[str]] = {}
    for key, entry in seen.items():
        url = (entry.get("url") or "").rstrip("/")
        if url:
            by_url.setdefault(url, []).append(key)
    duplicates = {u: ks for u, ks in by_url.items() if len(ks) > 1}
    # A key that does not match what make_key would produce today is drift, not
    # damage: reported separately so a rename is a choice, never automatic.
    drift = [
        k for k, v in seen.items()
        if is_canonical(k) and k != make_key(v.get("provider", ""), v.get("award", ""), v.get("url", ""))
    ]

    print(json.dumps({
        "entries": len(seen),
        "malformed_keys": malformed,
        "legacy_three_part_keys": legacy,
        "duplicate_urls": duplicates,
        "keys_not_matching_current_rule": len(drift),
    }, indent=2, ensure_ascii=False))
    return 1 if (malformed or duplicates) else 0


def _force_utf8_output() -> None:
    """Write UTF-8 whatever the host's default encoding is.

    A piped stdout on Windows defaults to the ANSI code page (cp1252 on most
    Western installs), so printing an institution, programme or file name
    outside it raised UnicodeEncodeError before the workflow saw any output.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)  # absent on a StringIO under test
        if reconfigure:
            reconfigure(encoding="utf-8")


def main() -> int:
    _force_utf8_output()
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--provider", help="University, graduate school, or funding body")
    ap.add_argument("--award", help="Programme name or scholarship scheme name")
    ap.add_argument("--url", default="")
    ap.add_argument("--audit", nargs="?", const=str(STATE), metavar="STATE_JSON")
    args = ap.parse_args()

    if args.audit:
        return audit(Path(args.audit))
    if args.provider is None or args.award is None:
        ap.error("give --provider and --award, or --audit")
    print(make_key(args.provider, args.award, args.url))
    return 0


if __name__ == "__main__":
    sys.exit(main())
