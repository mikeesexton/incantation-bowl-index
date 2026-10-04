"""robots.txt matching with wildcards, as RFC 9309 and the major crawlers read it.

Python's ``urllib.robotparser`` treats ``*`` and ``$`` inside a path literally, so
a rule such as ``Disallow: */archivelot*`` never matches. This reads the group for
our user agent (or ``*``), then applies the longest matching rule; on a tie,
Allow wins.
"""

import re
import urllib.parse


def _groups(text):
    groups, agents, rules, in_rules = [], [], [], False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        field, value = (part.strip() for part in line.split(":", 1))
        field = field.casefold()
        if field == "user-agent":
            if in_rules:
                groups.append((agents, rules))
                agents, rules, in_rules = [], [], False
            agents.append(value.casefold())
        elif field in ("allow", "disallow") and agents:
            in_rules = True
            rules.append((field == "allow", value))
    if agents:
        groups.append((agents, rules))
    return groups


def _pattern(path):
    anchored = path.endswith("$")
    body = re.escape(path[:-1] if anchored else path).replace(r"\*", ".*")
    return re.compile(body + ("$" if anchored else ""))


def can_fetch(robots_text, user_agent, url):
    token = re.split(r"[/\s]", user_agent.strip(), 1)[0].casefold()
    groups = _groups(robots_text)
    chosen = [rules for agents, rules in groups if any(a != "*" and a in token for a in agents)]
    if not chosen:
        chosen = [rules for agents, rules in groups if "*" in agents]
    rules = [rule for group in chosen for rule in group]
    parts = urllib.parse.urlsplit(url)
    target = (parts.path or "/") + ("?" + parts.query if parts.query else "")
    best = None
    for allow, path in rules:
        if not path:
            continue  # "Disallow:" with no path allows everything
        if _pattern(path).match(target):
            key = (len(path), allow)
            if best is None or key > best:
                best = key
    return True if best is None else best[1]
