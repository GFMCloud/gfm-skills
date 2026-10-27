"""Patterns for things that must never reach a brag video, plan, brief or caption.

Shared by scan_project.py, check_plan.py and render_light.py. Standard library only.
These catch common slips, not every secret: a value that looks ordinary passes.
"""
import re

SECRET = re.compile(
    r"(sk-[A-Za-z0-9_-]{16,}|sk_(?:live|test)_[A-Za-z0-9]{10,}|rk_(?:live|test)_[A-Za-z0-9]{10,}|"
    r"ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|glpat-[A-Za-z0-9_-]{16,}|"
    r"xox[abprs]-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{30,}|"
    r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY|"
    r"[a-z][a-z0-9+.-]*://[^/\s:@'\"]+:[^@\s'\"]+@)", re.I)
# key = value with a literal value: 8+ key-like characters including a digit, not a placeholder.
# Labels ("Password:"), variables ({password}, request.headers...) and env reads don't match.
_KEY = r"(password|passwd|pwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|client[_-]?secret)"
_NOT_PLACEHOLDER = r"(?!your\b|your[-_]|xxx|changeme|change[-_]me|example|placeholder|dummy|enter\b|<|\{|\$)"
ASSIGNED = re.compile(
    _KEY + r"[\"']?\s*[:=]\s*(?:"
    # quoted literal: any 8+ characters inside matching quotes
    r"\"" + _NOT_PLACEHOLDER + r"[^\"\n]{8,}\"|'" + _NOT_PLACEHOLDER + r"[^'\n]{8,}'|"
    # unquoted literal: 8+ key-like characters including a digit
    + _NOT_PLACEHOLDER + r"(?=[A-Za-z0-9+/=_.\-]*\d)[A-Za-z0-9+/=_.\-]{8,}(?=[\s,;)}]|$))", re.I)
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
SAFE_EMAIL = re.compile(r"@(?:[A-Za-z0-9-]+\.)*(?:example\.(?:com|org|net)|example|test|invalid)$", re.I)
IMAGE_AT = re.compile(r"\.(png|jpe?g|gif|svg|webp|avif)$", re.I)
INTERNAL = re.compile(r"\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:internal|corp|lan|intranet|local)\b(?![.-][A-Za-z0-9])", re.I)
PRIVATE_IP = re.compile(r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b")
HOME_PATH = re.compile(r"(?:^|[\s\"'`(=:])(?:/Users/|/home/|/private/|/tmp/|/var/folders/|/Volumes/|/root/)[^\s\"'`)]+|[A-Za-z]:\\Users\\", re.I)


def emails(line):
    """Real-looking email addresses in a line (not image@2x names, not example/test domains)."""
    return [e for e in EMAIL.findall(line) if not IMAGE_AT.search(e) and not SAFE_EMAIL.search(e)]


def find(line):
    """Names of the kinds of leak found in one line, most serious first."""
    kinds = []
    if SECRET.search(line) or ASSIGNED.search(line):
        kinds.append("a key, token or password")
    if INTERNAL.search(line) or PRIVATE_IP.search(line):
        kinds.append("an internal hostname or private address")
    if HOME_PATH.search(line):
        kinds.append("a path on this machine")
    if emails(line):
        kinds.append("an email address")
    return kinds
