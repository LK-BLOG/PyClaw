"""Approval modes, command segmentation and prefix rules."""

from __future__ import annotations

import datetime
import re

MODES = ("request", "auto", "full")
DECISIONS = ("allow", "prompt", "forbidden")
SEVERITY = {"allow": 0, "prompt": 1, "forbidden": 2}

# Built-in refusals: never run, regardless of mode.
BLOCKED_PATTERNS = [
    r"\brm\s+(-[a-z]*\s+)*-(r|rf|fr)\s+(/|/\*|/\.)(\s|$)",
    r"\brm\s+(-[a-z]*\s+)*-(r|rf|fr)\s+/(bin|boot|dev|etc|home|lib|lib64|proc|root|sbin|sys|usr|var)(/|\s|$)",
    r"\brm\s+(-[a-z]*\s+)*-rf?\s+[a-zA-Z]:[\\/](windows|system32|program\s*files)([\\/]|\s|$)",
    r"\b(del|erase|rd|rmdir)\s+(/(f|s|q)|\s)+[a-zA-Z]:[\\/]",
    r"\bformat\s+[a-zA-Z]:",
    r"\bmkfs(\.\w+)?\s+",
    r"\bdd\s+if=.*of=/(dev/(sd|hd|nvme)|[a-zA-Z]:)",
    r"\bshutdown\b|\breboot\b|\bhalt\b|\bpoweroff\b|\binit\s+0\b",
    r":\(\)\s*\{",
    r"%0\s*\|\s*%0",
    r"\bdiskpart\b",
]

_OPERATORS = ("&&", "||", ";;", "|", ";", "&")


def segment(command):
    """Split on | && || ; ( ) $() so `ls && rm -rf /` cannot hide behind `ls`."""
    text = command or ""
    parts, buf, i, n = [], [], 0, len(text)
    depth = 0
    substitution = 0
    quote = ""
    at_command_start = True
    while i < n:
        ch = text[i]
        if quote:
            buf.append(ch)
            if ch == quote and text[i - 1] != "\\":
                quote = ""
            i += 1
            continue
        if ch in "'\"":
            quote = ch
            buf.append(ch)
            i += 1
            at_command_start = False
            continue
        two = text[i:i + 2]
        if two in ("&&", "||"):
            _push(parts, buf)
            i += 2
            at_command_start = True
            continue
        if two == "$(":
            # A command substitution is a command of its own: it is split out, but
            # the marker and its closing paren stay attached to it.
            _push(parts, buf)
            buf.append(two)
            substitution += 1
            at_command_start = False
            i += 2
            continue
        if ch in "|;&\n":
            _push(parts, buf)
            i += 1
            at_command_start = True
            continue
        if ch == "(":
            # Only a parenthesis that starts a command is a separator. `foo(bar)`
            # and `printf(a,b)` are ordinary words and must stay in one piece.
            if at_command_start:
                depth += 1
                _push(parts, buf)
                i += 1
                at_command_start = True
                continue
            buf.append(ch)
            i += 1
            continue
        if ch == ")":
            if substitution > 0:
                substitution -= 1
                buf.append(ch)
                if substitution == 0:
                    _push(parts, buf)
                    at_command_start = True
                i += 1
                continue
            if depth > 0:
                depth -= 1
                _push(parts, buf)
                i += 1
                at_command_start = True
                continue
            buf.append(ch)
            i += 1
            continue
        if not ch.isspace():
            at_command_start = False
        buf.append(ch)
        i += 1
    _push(parts, buf)
    return [part for part in parts if part.strip()]


def _push(parts, buf):
    piece = "".join(buf).strip()
    if piece:
        parts.append(piece)
    buf.clear()


def tokenize(text):
    tokens, buf, quote = [], [], ""
    for ch in text or "":
        if quote:
            if ch == quote:
                quote = ""
            else:
                buf.append(ch)
        elif ch in "'\"":
            quote = ch
        elif ch.isspace():
            if buf:
                tokens.append("".join(buf))
                buf = []
        else:
            buf.append(ch)
    if buf:
        tokens.append("".join(buf))
    return tokens


# Words that continue a command invocation (subcommands) rather than name a target.
_SUBCOMMANDS = {
    "install", "uninstall", "add", "remove", "update", "upgrade", "list", "show", "info", "search",
    "status", "commit", "push", "pull", "fetch", "merge", "rebase", "checkout", "switch", "branch",
    "clone", "init", "log", "diff", "stash", "tag", "remote", "config", "run", "build", "test",
    "start", "stop", "restart", "serve", "dev", "sync", "publish", "pack", "deploy", "apply",
    "compose", "up", "down", "ps", "exec", "get", "set", "create", "delete", "describe", "logs",
}


def _looks_like_value(token):
    if not token:
        return True
    if token[0] in "-/\\." or "=" in token:
        return True
    return bool(re.search(r"[\\/.]", token)) or token.isdigit()


def derive_rule(command, scope="session", decision="allow", justification=""):
    """Guess the reusable prefix for 'structure-similar commands'."""
    first = segment(command)
    tokens = tokenize(first[0] if first else command)
    if not tokens:
        return None
    pattern = [tokens[0]]
    for token in tokens[1:4]:
        if _looks_like_value(token) or token.lower() not in _SUBCOMMANDS:
            break
        pattern.append(token)
        if len(pattern) >= 3:
            break
    return {"pattern": pattern, "decision": decision, "scope": scope,
            "justification": justification, "created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "source": (command or "")[:200]}


def rule_matches(rule, tokens):
    pattern = rule.get("pattern") or []
    if not pattern or len(tokens) < len(pattern):
        return False
    for expected, actual in zip(pattern, tokens):
        options = expected if isinstance(expected, list) else [expected]
        if not any(str(option).lower() == str(actual).lower() for option in options):
            return False
    return True


class Decision:
    def __init__(self, decision, reason="", rule=None, segment_text=""):
        self.decision = decision
        self.reason = reason
        self.rule = rule
        self.segment = segment_text

    @property
    def allowed(self):
        return self.decision == "allow"

    def __repr__(self):
        return f"<Decision {self.decision} {self.reason!r}>"


class Policy:
    """Evaluates every segment of a command; the strictest verdict wins."""

    def __init__(self, rules=None, extra_blocked=None):
        self.persistent = list(rules or [])
        self.session_rules = []
        self.extra_blocked = [str(x).lower() for x in (extra_blocked or [])]

    @property
    def rules(self):
        return self.persistent + self.session_rules

    def grant(self, rule):
        if not rule:
            return None
        if rule.get("scope") == "persistent":
            self.persistent.append(rule)
        else:
            self.session_rules.append(rule)
        return rule

    def revoke(self, index, scope=None):
        target = self.persistent if scope == "persistent" else self.session_rules
        if 0 <= index < len(target):
            return target.pop(index)
        return None

    def revoke_combined(self, index):
        """Revoke by index into the combined list (persistent + session rules).

        The CLI shows one list of every rule, so the index it hands back has to be
        interpreted against that same combined order.
        """
        try:
            index = int(index)
        except (TypeError, ValueError):
            return None
        rules = self.rules
        if not 0 <= index < len(rules):
            return None
        rule = rules[index]
        if rule in self.persistent:
            self.persistent.remove(rule)
        elif rule in self.session_rules:
            self.session_rules.remove(rule)
        else:
            return None
        return rule

    def is_blocked(self, command):
        low = (command or "").lower()
        if any(fragment and fragment in low for fragment in self.extra_blocked):
            return True
        return any(re.search(pattern, low) for pattern in BLOCKED_PATTERNS)

    def evaluate(self, command, flagged=False, mode="auto"):
        """flagged = the model itself marked this call as needing confirmation."""
        if self.is_blocked(command):
            return Decision("forbidden", "blocked by policy", segment_text=command or "")
        verdicts = []
        for piece in segment(command) or [command]:
            tokens = tokenize(piece)
            verdict = self._evaluate_segment(piece, tokens, flagged, mode)
            if verdict.decision == "forbidden" or verdict.decision == "prompt":
                return verdict
            verdicts.append(verdict)
        if not verdicts:
            return Decision("allow", "empty command")
        # A matched rule carries more information than the blanket mode verdict, so
        # prefer it: otherwise `ls && git status` reports "auto mode" and the rule
        # that actually authorised `git status` is lost.
        for verdict in verdicts:
            if verdict.rule is not None:
                return verdict
        return verdicts[-1]

    def _evaluate_segment(self, piece, tokens, flagged, mode):
        if self.is_blocked(piece):
            return Decision("forbidden", "blocked by policy", segment_text=piece)
        matched = [rule for rule in self.rules if rule_matches(rule, tokens)]
        if matched:
            strictest = max(matched, key=lambda rule: SEVERITY.get(rule.get("decision", "allow"), 0))
            decision = strictest.get("decision", "allow")
            if decision == "allow":
                return Decision("allow", "matched allow rule", strictest, piece)
            return Decision(decision, strictest.get("justification") or "matched rule", strictest, piece)
        if flagged:
            return Decision("prompt", "the agent flagged this as destructive", segment_text=piece)
        if mode == "full":
            return Decision("allow", "full access", segment_text=piece)
        if mode == "request":
            return Decision("prompt", "every command needs approval", segment_text=piece)
        return Decision("allow", "auto mode", segment_text=piece)


def mode_label(mode, lang="zh-CN"):
    table = {
        "request": ("请求批准", "Ask every time", "每条命令都要你点头"),
        "auto": ("帮我批准", "Approve for me", "只对检测到的风险操作请求批准"),
        "full": ("完全访问权限", "Full access", "不再询问，直接执行"),
    }
    zh, en, zh_help = table.get(mode, (mode, mode, ""))
    return {"label": zh if lang == "zh-CN" else en, "help": zh_help, "id": mode}
