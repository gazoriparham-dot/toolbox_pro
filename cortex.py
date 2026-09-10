# -*- coding: utf-8 -*-
"""Cortex v5 - intent-aware orchestrator over WebBrain + AIBrain."""
import os, re, json

class Cortex:
    INTENTS = [
        ("howto",      re.compile(r"\b(how (to|do|can|does)|steps|tutorial|guide|setup|install|configure|fix)\b", re.I)),
        ("compare",    re.compile(r"\b(vs\.?|versus|difference between|compare)\b", re.I)),
        ("why",        re.compile(r"\b(why|cause|reason)\b", re.I)),
        ("list",       re.compile(r"\b(list|top \d+|best|examples of|types of)\b", re.I)),
        ("news",       re.compile(r"\b(latest|news|recent|new in 20\d\d)\b", re.I)),
        ("yesno",      re.compile(r"^(is|are|can|does|do|will|was|were)\b", re.I)),
        ("definition", re.compile(r"\b(what (is|are|was)|define|definition|meaning of)\b", re.I)),
    ]
    SYNONYMS = {
        "hack": ["penetration testing", "exploit"],
        "hacking": ["penetration testing"],
        "password": ["credential", "authentication"],
        "wifi": ["wireless", "wi-fi", "802.11"],
        "wireless": ["wifi", "wi-fi"],
        "virus": ["malware"],
        "malware": ["virus", "trojan"],
        "encrypt": ["encryption", "cryptography"],
        "firewall": ["packet filter", "network security"],
        "scan": ["scanning", "reconnaissance"],
        "vulnerability": ["exploit", "security flaw", "CVE"],
        "sql injection": ["sqli", "database injection"],
        "xss": ["cross-site scripting"],
        "phishing": ["social engineering email"],
        "brute force": ["password cracking"],
        "ddos": ["denial of service"],
        "port": ["network port", "socket"],
        "shell": ["reverse shell", "command shell"],
    }
    AUTHORITY = {
        "nist.gov": 2.0, "cisa.gov": 2.0, "owasp.org": 1.8,
        "wikipedia.org": 1.6, "gov": 1.6, "edu": 1.5,
        "microsoft.com": 1.5, "apple.com": 1.5, "python.org": 1.5,
        "google.com": 1.4, "github.com": 1.3, "amazon.com": 1.3,
        "stackoverflow.com": 1.2, "medium.com": 0.8,
        "quora.com": 0.7, "blogspot.com": 0.6,
    }
    STEP_RE = re.compile(
        r"^(first|then|next|finally|use|run|open|type|install|configure|create|"
        r"add|check|verify|enable|disable|set|enter|click|select|navigate|"
        r"go to|make sure|ensure|download|copy|edit|restart)\b", re.I)
    QV = re.compile(r"\b(what|how|why|which|who|is|are|can|does|do|explain|show|list)\b", re.I)

    def __init__(self, web, brain, path=None):
        self.web = web
        self.brain = brain
        self.path = path or os.path.expanduser("~/.toolbox_pro_cortex.json")
        self.st = self._load()
        self.topic = self.st.get("topic", "")
        self.last_suggestions = []

    def _load(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"counts": {}, "topic": ""}

    def _save(self):
        try:
            self.st["topic"] = self.topic
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.st, f, indent=1)
        except Exception:
            pass

    def _bump(self, k):
        c = self.st.setdefault("counts", {})
        c[k] = c.get(k, 0) + 1

    # ── intent ──
    def detect_intent(self, q):
        for name, rx in self.INTENTS:
            if rx.search(q):
                return name
        return "general"

    # ── synonym expansion ──
    def expand(self, q):
        ql = q.lower()
        extra = []
        for k, vs in self.SYNONYMS.items():
            if re.search(r"\b" + re.escape(k) + r"\b", ql):
                for v in vs:
                    if v not in ql and v not in extra:
                        extra.append(v)
        return (q + " " + " ".join(extra[:3])).strip() if extra else q

    # ── multi-hop decomposition ──
    def decompose(self, q):
        low = q.lower()
        if " and " not in low:
            return [q]
        idx = low.index(" and ")
        a, b = q[:idx], q[idx + 5:]
        if self.QV.search(a) and self.QV.search(b) and len(b.split()) >= 3:
            return [a.strip(), b.strip()]
        return [q]

    # ── source authority ──
    def authority(self, url):
        try:
            host = url.split("/")[2].lower()
        except Exception:
            return 1.0, "unknown"
        for dom, w in self.AUTHORITY.items():
            if host == dom or host.endswith("." + dom):
                return w, host
        if host.endswith(".edu") or host.endswith(".gov"):
            return 1.5, host
        return 1.0, host

    # ── suggestions ──
    def suggestions(self, q):
        kws = self.web._keywords(q)
        base = " ".join(kws[:3]) if kws else q
        intent = self.detect_intent(q)
        pool = []
        if intent != "howto":
            pool.append("how to use " + base)
        if intent != "definition":
            pool.append("what is " + base)
        pool += [base + " best practices", base + " examples",
                 "common mistakes with " + base]
        out = []
        for p in pool:
            if p.lower() != q.lower() and p not in out:
                out.append(p)
            if len(out) >= 3:
                break
        return out

    # ── main entry ──
    def answer(self, q, force=None, brief=False):
        q = (q or "").strip()
        if not q:
            return "Empty question."
        self._bump("questions")
        rec = self.brain.recall(q)
        if rec and not brief:
            self._bump("memory_hits")
            self._save()
            return rec + "\n\n💡 Try next:\n" + "\n".join("   • " + s for s in self.suggestions(q))
        intent = force or self.detect_intent(q)
        subs = self.decompose(q)
        if len(subs) > 1:
            outs = []
            for i, s in enumerate(subs, 1):
                outs.append("── Part %d: %s ──\n%s" % (i, s, self._single(s, intent, brief)))
            full = "\n\n".join(outs)
        else:
            full = self._single(q, intent, brief)
        kws = self.web._keywords(q)
        if kws:
            self.topic = " ".join(kws[:4])
        self._save()
        return full

    def _single(self, q, intent, brief):
        eq = q if getattr(self.web, 'EXACT', False) else self.expand(q)  # v5.2 exact
        ts = 1 if brief else (8 if intent == "howto" else 5)
        mp = 2 if brief else 4
        try:
            ans = self.web.extract_answer(eq, max_pages=mp, top_sentences=ts)
        except Exception:
            ans = None
        if not ans:
            self._bump("web_miss")
            self._save()
            return "No web result found."
        self._bump("web_hits")
        head = ["🎯 Intent: %s" % intent.upper()]
        if eq != q:
            head.append("🔎 Expanded query: %s" % eq)
        body = ans
        # step extraction for how-to intent
        if intent == "howto":
            steps, rest = [], []
            for L in body.split("\n"):
                m = re.match(r"^\d+\.\s+(.*)$", L)
                if m and self.STEP_RE.match(m.group(1)):
                    steps.append(m.group(1))
                else:
                    rest.append(L)
            if steps:
                body = "\n".join(rest)
                body += "\n\n📋 Detected steps:\n" + "\n".join(
                    "%d. %s" % (i, s) for i, s in enumerate(steps, 1))
        # authority badges
        srcs = re.findall(r"^\s*•\s+(\S+)$", ans, re.M)
        if srcs:
            badges = []
            for u in srcs[:4]:
                w, host = self.authority(u)
                tag = "HIGH" if w >= 1.4 else ("MEDIUM" if w >= 1.0 else "LOW")
                badges.append("   • %s -> authority %s (%.1f)" % (host, tag, w))
            body += "\n\n🏛 Source authority:\n" + "\n".join(badges)
        try:
            self.brain.learn(q, body)
        except Exception:
            pass
        sugg = self.suggestions(q)
        self.last_suggestions = sugg
        tail = "\n\n💡 Try next:\n" + "\n".join("   • " + s for s in sugg)
        if brief:
            lines = [L for L in body.split("\n") if L.strip()]
            keep = [L for L in lines if L.startswith(("🟢", "🟡", "🔴"))]
            first = next((L for L in lines if re.match(r"^\d+\.", L)), "")
            return "\n".join(head + keep + ([first] if first else [])) + tail
        return "\n".join(head) + "\n\n" + body + tail

    # ── reports ─
    def stats_report(self):
        c = self.st.get("counts", {})
        lines = ["📊 Cortex stats", ""]
        for k in ("questions", "web_hits", "web_miss", "memory_hits"):
            lines.append("   %s: %d" % (k, c.get(k, 0)))
        lines.append("   current topic: %s" % (self.topic or "-"))
        lines.append("   learned knowledge: %d entries" % len(self.brain.knowledge))
        try:
            lines.append("   " + self.web.archive_stats().split("\n")[1].strip())
        except Exception:
            pass
        return "\n".join(lines)

    def topic_report(self):
        return ("🧭 Current topic: %s\n"
                "Follow-up questions are merged with this topic automatically."
                % (self.topic or "(none yet)"))

    def related_report(self):
        if not self.last_suggestions:
            return "No suggestions yet - ask a question first, or see 'Try next' under each answer."
        return "💡 Suggested follow-ups:\n" + "\n".join("   • " + s for s in self.last_suggestions)
