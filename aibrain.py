# -*- coding: utf-8 -*-
"""AIBrain v4 - conversation memory, follow-up merging, learning, summarizer."""
import os, re, json, time
from collections import deque
from difflib import SequenceMatcher

class AIBrain:
    FA = re.compile(r"[\u0600-\u06FF]")
    FOLLOWUP = re.compile(
        r"^(and\b|but\b|also\b|what about\b|how about\b|tell me more|more\b|explain\b|why\b|really\b|"
        r"و\s|خب\s|حالا\s|چطور|چرا|بیشتر|توضیح|یعنی)", re.I)

    def __init__(self, path=None):
        self.path = path or os.path.expanduser("~/.toolbox_pro_aibrain.json")
        self.data = self._load()
        self.history = deque(self.data.get("history", []), maxlen=20)
        self.knowledge = self.data.get("knowledge", {})

    # ── persistence ──
    def _load(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"history": [], "knowledge": {}}

    def _persist(self):
        try:
            self.data = {"history": list(self.history), "knowledge": self.knowledge}
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=1)
        except Exception:
            pass

    # ── language ──
    def detect_lang(self, t):
        return "fa" if self.FA.search(t or "") else "en"

    # ── follow-up merging: "and why?" -> prev question + "why" ──
    def preprocess(self, q):
        q = (q or "").strip()
        if not q or q.startswith("/"):
            return q
        if self.history:
            prev = self.history[-1].get("q", "")
            words = len(q.split())
            if prev and (self.FOLLOWUP.match(q) or words <= 3):
                tail = self.FOLLOWUP.sub("", q, count=1).strip()
                return (prev + " " + tail).strip() if tail else prev
        return q

    # ── conversation memory ──
    def remember(self, q):
        if q and not q.startswith("/"):
            self.history.append({"q": q, "ts": time.time()})
            self._persist()

    # ── permanent learning from web answers ──
    def learn(self, q, a):
        if not q or not a or q.startswith("/"):
            return
        self.knowledge[q.lower().strip()] = {"a": a, "ts": time.time()}
        if len(self.knowledge) > 300:
            oldest = sorted(self.knowledge, key=lambda k: self.knowledge[k]["ts"])
            for k in oldest[:len(self.knowledge) - 300]:
                del self.knowledge[k]
        self._persist()

    def recall(self, q):
        ql = (q or "").lower().strip()
        if not ql:
            return None
        if ql in self.knowledge:
            return "🧠 (learned knowledge)\n\n" + self.knowledge[ql]["a"]
        best, br = None, 0.0
        for k, v in self.knowledge.items():
            r = SequenceMatcher(None, ql, k).ratio()
            if r > br:
                br, best = r, v["a"]
        if br > 0.90:
            return "🧠 (learned knowledge, fuzzy match)\n\n" + best
        return None

    def forget_all(self):
        n = len(self.knowledge)
        self.knowledge = {}
        self._persist()
        return "🗑 All learned knowledge cleared (%d entries removed)." % n

    def memory_report(self):
        if not self.knowledge:
            return "🧠 Memory is empty. Ask questions that go to the web - answers are learned automatically."
        lines = ["🧠 Learned knowledge (%d entries):" % len(self.knowledge), ""]
        for i, (k, v) in enumerate(sorted(self.knowledge.items(), key=lambda x: -x[1]["ts"])[:20], 1):
            lines.append("%d. %s" % (i, k[:80]))
        lines.append("")
        lines.append("File: ~/.toolbox_pro_aibrain.json  |  /forgetall to clear")
        return "\n".join(lines)

    # ── URL summarizer ──
    def summarize_url(self, url, n=6):
        try:
            from webbrain import WebBrain
            wb = WebBrain()
            title, text = wb.fetch_text(url)
            sents = wb._sentences(text)
            if not sents:
                return "❌ Could not extract text from: %s" % url
            # informative sentences: prefer early + medium-length
            scored = []
            for i, s in enumerate(sents):
                sc = max(0.0, 2.0 - i * 0.05) + (1.0 if 60 < len(s) < 300 else 0.0)
                scored.append((sc, s))
            scored.sort(key=lambda x: -x[0])
            picks = [s for _, s in scored[:n]]
            # restore original order for readability
            picks = [s for s in sents if s in picks]
            lines = ["📄 Summary of: %s" % url, ""]
            if title:
                lines.append("Title: " + title)
                lines.append("")
            for i, s in enumerate(picks, 1):
                lines.append("%d. %s" % (i, s))
            lines.append("")
            lines.append("(extractive summary - %d sentences from %d)" % (len(picks), len(sents)))
            return "\n".join(lines)
        except Exception as e:
            return "❌ Summarize error: %s" % e
