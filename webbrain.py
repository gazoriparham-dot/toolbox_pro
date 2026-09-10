# -*- coding: utf-8 -*-
"""WebBrain v3 - advanced multi-engine search + extractive QA (no LLM)."""
import os, re, json, math, time, sqlite3, threading
import urllib.request, urllib.parse
from difflib import SequenceMatcher
from concurrent.futures import ThreadPoolExecutor, as_completed

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0",
      "Accept-Language": "en-US,en;q=0.8,fa;q=0.6"}


class WebBrain:
    EXACT = True  # v5.2: search with the user's EXACT query
    STOP = set("""the a an and or of to in for on with is are was were be been
    what how why when where who which do does did can should will would that
    this these those there here about into over under than then also very just
    می این آن که چه چرا چگونه کجا کی کدام را از به در با و یا هست بود شد کرده
    میکنم میکند کنید داریم دارید می خواهم باید توان برای های ها است""".split())

    def __init__(self, db_path=None):
        self.db_path = db_path or os.path.expanduser("~/.toolbox_pro_webcache.db")
        self.arc_path = os.path.expanduser("~/.toolbox_pro_archive.db")  # offline archive
        self._init_db()

    # ─────────────── memory: SQLite + TTL ───────────────
    def _db(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        try:
            with self._db() as con:
                con.execute("CREATE TABLE IF NOT EXISTS mem(q TEXT PRIMARY KEY, ans TEXT, ts REAL, hits INTEGER DEFAULT 1)")
        except Exception:
            pass

    def _mem_get(self, question, ttl_days=30):
        ql = question.lower().strip()
        try:
            with self._db() as con:
                row = con.execute("SELECT ans, ts FROM mem WHERE q=?", (ql,)).fetchone()
                if row and (time.time() - row[1]) < ttl_days * 86400:
                    con.execute("UPDATE mem SET hits=hits+1 WHERE q=?", (ql,))
                    return row[0]
                rows = con.execute("SELECT q, ans FROM mem").fetchall()
        except Exception:
            return None
        best, br = None, 0.0
        for q, ans in rows:
            r = SequenceMatcher(None, ql, q).ratio()
            if r > br:
                br, best = r, ans
        return best if br > 0.88 else None

    def _mem_set(self, question, answer):
        try:
            with self._db() as con:
                con.execute("INSERT OR REPLACE INTO mem(q,ans,ts,hits) VALUES(?,?,?,1)",
                            (question.lower().strip(), answer, time.time()))
                cnt = con.execute("SELECT COUNT(*) FROM mem").fetchone()[0]
                if cnt > 1000:
                    con.execute("DELETE FROM mem WHERE q IN (SELECT q FROM mem ORDER BY ts ASC LIMIT ?)",
                                (cnt - 1000,))
        except Exception:
            pass

    # ─────────────── query analysis ───────────────
    def _keywords(self, text):
        t = text.replace("‌", " ")
        words = re.findall(r"[a-zA-Z\u0600-\u06FF]{3,}", t.lower())
        return [w for w in words if w not in self.STOP][:12]

    def _queries(self, question, kws):
        """چند پرس‌وجوی مختلف برای پوشش بهتر"""
        base = " ".join(kws[:8]) if kws else question
        qs = [question, base]
        low = question.lower()
        if re.match(r"^(what|why|how|چرا|چه|چگونه|چیست)", low.strip()):
            qs.append(base + " explained")
        if re.search(r"(how to|چطور|چگونه)", low):
            qs.append(base + " tutorial guide")
        seen, out = set(), []
        for q in qs:
            q = q.strip()
            if q and q.lower() not in seen:
                seen.add(q.lower())
                out.append(q)
        return out[:3]

    # ─────────────── network with retry + proxy ───────────────
    def _get(self, url, timeout=10, retries=2):
        last = None
        for i in range(retries + 1):
            try:
                req = urllib.request.Request(url, headers=UA)
                return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")
            except Exception as e:
                last = e
                if i < retries:
                    time.sleep(0.7 * (i + 1))
        raise last

    # ─────────────── search engines ───────────────
    def _search_ddg(self, query, n):
        from ddgs import DDGS
        with DDGS() as d:
            return [{"title": r.get("title", ""), "url": r.get("href") or r.get("url", ""),
                     "snippet": r.get("body", "")} for r in d.text(query, max_results=n)]

    def _search_news(self, query, n):
        from ddgs import DDGS
        with DDGS() as d:
            return [{"title": r.get("title", ""), "url": r.get("url") or r.get("href", ""),
                     "snippet": r.get("body", "")} for r in d.news(query, max_results=n)]

    def _search_google(self, query, n):
        u = "https://www.google.com/search?q=%s&num=%d&hl=en" % (urllib.parse.quote_plus(query), n + 3)
        html = self._get(u)
        out = []
        for m in re.finditer(r'href="/url\?q=(https?://[^&"]+)', html):
            url = urllib.parse.unquote(m.group(1))
            if "google." not in url and "gstatic" not in url and url not in [o["url"] for o in out]:
                out.append({"title": url.split("/")[2], "url": url, "snippet": ""})
            if len(out) >= n:
                break
        return out

    def _search_brave(self, query, n):
        u = "https://search.brave.com/search?q=%s" % urllib.parse.quote_plus(query)
        html = self._get(u)
        out = []
        for m in re.finditer(r'<a[^>]+href="(https?://[^"]+)"[^>]*>.*?<div[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</div>', html, re.S):
            url, title = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
            if "brave.com" not in url and title:
                out.append({"title": title, "url": url, "snippet": ""})
            if len(out) >= n:
                break
        return out

    def _search_mojeek(self, query, n):
        u = "https://www.mojeek.com/search?q=%s" % urllib.parse.quote_plus(query)
        html = self._get(u)
        out = []
        for m in re.finditer(r'<a class="ob"[^>]+href="(https?://[^"]+)"[^>]*>(.*?)</a>', html, re.S):
            url, title = m.group(1), re.sub(r"<[^>]+>", "", m.group(2)).strip()
            if url and title:
                out.append({"title": title, "url": url, "snippet": ""})
            if len(out) >= n:
                break
        return out

    def _search_wiki(self, query, n):
        u = ("https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=%s"
             "&format=json&srlimit=%d" % (urllib.parse.quote_plus(query), n))
        data = json.loads(self._get(u))
        out = []
        for r in data.get("query", {}).get("search", []):
            t = r["title"]
            sn = re.sub(r"<[^>]+>", "", r.get("snippet", ""))
            out.append({"title": t, "url": "https://en.wikipedia.org/wiki/" + t.replace(" ", "_"),
                        "snippet": sn})
        return out

    def _instant(self, query):
        """DDG Instant Answer API - جواب فوری و دقیق برای تعاریف"""
        try:
            u = "https://api.duckduckgo.com/?q=%s&format=json&no_html=1&skip_disambig=1" % urllib.parse.quote_plus(query)
            d = json.loads(self._get(u, timeout=8))
            bits = []
            for k in ("Answer", "Definition", "AbstractText"):
                if d.get(k):
                    bits.append(d[k])
            src = d.get("AbstractURL") or d.get("DefinitionURL") or ""
            if bits and not re.search("[\u0600-\u06FF]", bits[0]):
                return bits[0], src
        except Exception:
            pass
        return None, None

    def search(self, query, max_results=5, mode="web"):
        engines = ([self._search_news] if mode == "news"
                   else [self._search_wiki] if mode == "wiki"
                   else [self._search_google, self._search_ddg, self._search_brave, self._search_mojeek])  # v5.2 google first
        for fn in engines:
            try:
                r = fn(query, max_results)
                if r:
                    return r
            except Exception:
                continue
        return []

    # ─────────────── page fetching + readability ───────────────
    def fetch_text(self, url, limit=40000):  # v5.3 fuller pages
        html = self._get(url)
        title = ""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            if soup.title:
                title = soup.title.get_text(strip=True)
            for tag in soup(["script", "style", "nav", "header", "footer",
                             "aside", "form", "noscript", "svg", "iframe"]):
                tag.decompose()
            # readability ساده: main/article را پیدا کن، وگرنه بلوک با بیشترین <p>
            main = soup.find("main") or soup.find("article")
            if main is None:
                cands = soup.find_all(["div", "section"])
                if cands:
                    main = max(cands, key=lambda c: len(c.find_all("p")))
            root = main or soup
            chunks = []
            for tag in root.find_all(["p", "li", "h2", "h3", "td", "blockquote", "pre"]):
                t = tag.get_text(" ", strip=True)
                if len(t) > 30:
                    chunks.append(t)
            text = "\n\n".join(chunks) or " ".join(soup.stripped_strings)  # v5.2 keep paragraphs
        except ImportError:
            text = re.sub(r"<[^>]+>", " ", html)
        return title, re.sub(r"\s+", " ", text)[:limit]

    def _sentences(self, text):
        parts = re.split(r"(?<=[.!?؟])\s+", text)
        out = []
        for p in parts:
            p = p.strip()
            if 40 < len(p) < 450 and not re.search("[\u0600-\u06FF]", p):
                out.append(p)
        return out

    # ─────────────── scoring ───────────────
    def _score(self, sent, kws, idf, title_words, position, rank):
        sl = sent.lower()
        words = set(re.findall(r"[a-zA-Z\u0600-\u06FF]+", sl))
        score = 0.0
        for k in kws:
            if k in words:
                score += 3.0 * idf.get(k, 1.0)
            else:
                m = SequenceMatcher(None, k, sl).find_longest_match(0, len(k), 0, len(sl))
                if m.size >= max(4, len(k) - 1):
                    score += 1.0 * idf.get(k, 1.0)
        if title_words:
            score += 0.8 * len(set(kws) & title_words)
        score += max(0.0, 1.5 - position * 0.05)          # موقعیت جمله
        score += max(0.0, 2.0 - rank * 0.4)               # رتبه‌ی صفحه در نتایج جستجو
        L = len(words)
        if L < 8:
            score -= 1.0
        elif L > 60:
            score -= 0.5
        return score

    # ─────────────── main pipeline ───────────────
    def extract_answer(self, question, mode=None, max_pages=4, top_sentences=5):
        # ── پارس حالت‌های ویژه ──
        q = question.strip()
        low = q.lower()
        if mode is None:
            for m in ("deep", "news", "wiki"):
                if low.startswith(m + " "):
                    mode, q = m, q[len(m) + 1:]
                    break
            else:
                mode = "web"
        if mode == "deep":
            max_pages, top_sentences = 8, 8

        mem = self._mem_get(q)
        if mem and mode != "deep":
            return "🧠 (from memory)\n\n" + mem

        kws = self._keywords(q)
        if not kws:
            return None

        # ── جواب فوری (Instant Answer) ──
        inst, inst_src = self._instant(q)

        # ── CVE → مستقیم به NVD ──
        cve_hits = []
        for m in re.finditer(r"CVE-\d{4}-\d{4,}", q, re.I):
            cve = m.group(0).upper()
            try:
                html = self._get("https://nvd.nist.gov/vuln/detail/" + cve, timeout=12)
                txt = re.sub(r"<[^>]+>", " ", html)
                txt = re.sub(r"\s+", " ", txt)
                i = txt.lower().find("description")
                if i > 0:
                    cve_hits.append("%s: %s" % (cve, txt[i + 12:i + 700].strip()))
            except Exception:
                pass

        # ── جستجوی موازی با چند پرس‌وجو ──
        queries = [q] if self.EXACT else self._queries(q, kws)  # v5.2 exact
        results = []
        seen_urls = set()
        try:
            with ThreadPoolExecutor(max_workers=3) as ex:
                futs = [ex.submit(self.search, qq, max_pages + 3, mode) for qq in queries]
                for f in as_completed(futs):
                    try:
                        for r in f.result():
                            u = r.get("url", "")
                            if u and u not in seen_urls:
                                seen_urls.add(u)
                                results.append(r)
                    except Exception:
                        pass
        except Exception:
            results = []
        if not results and not inst and not cve_hits:
            try:  # offline fallback: answer from local archive
                arc = self.archive_search(question)
                if arc:
                    return arc
            except Exception:
                pass
            return None

        # ── IDF ──
        idf = {}
        n = max(len(results), 1)
        for k in kws:
            cnt = sum(1 for r in results if k in (r.get("title", "") + " " + r.get("snippet", "")).lower())
            idf[k] = math.log((n + 1) / (cnt + 1)) + 1

        # ── دانلود همزمان صفحات ──
        pages = []
        ranked = [r for r in results if r.get("url")][:max_pages + 3]
        with ThreadPoolExecutor(max_workers=6) as ex:
            futs = {}
            for rank, r in enumerate(ranked):
                futs[ex.submit(self.fetch_text, r["url"])] = (rank, r)
            for f in as_completed(futs):
                try:
                    title, text = f.result()
                    if text:
                        pages.append((title, text, futs[f][1]["url"], futs[f][0]))
                        try:
                            self.archive_put(futs[f][1]["url"], title, text)  # auto-archive
                        except Exception:
                            pass
                except Exception:
                    pass
                if len(pages) >= max_pages:
                    break

        # ── امتیازدهی جملات ──
        scored = []
        for title, text, url, rank in pages:
            tw = set(re.findall(r"[a-zA-Z\u0600-\u06FF]+", title.lower()))
            for pos, s in enumerate(self._sentences(text)):
                sc = self._score(s, kws, idf, tw, pos, rank)
                if sc >= 4.0:
                    scored.append((sc, s, title, url))
        scored.sort(key=lambda x: -x[0])

        chosen, seen = [], set()
        for sc, s, t, u in scored:
            key = s[:50].lower()
            if key in seen:
                continue
            seen.add(key)
            chosen.append((sc, s, t, u))
            if len(chosen) >= top_sentences:
                break
        if not chosen:
            for r in results[:3]:
                if r.get("snippet") and not re.search("[\u0600-\u06FF]", r["snippet"]):
                    chosen.append((0, r["snippet"], r.get("title", ""), r.get("url", "")))
        if not chosen and not inst and not cve_hits:
            return None

        # ── نمره اعتماد ──
        if chosen:
            avg = sum(c[0] for c in chosen) / len(chosen)
            conf = "🟢 Confidence: HIGH" if avg >= 8 else ("🟡 Confidence: MEDIUM" if avg >= 5 else "🔴 Confidence: LOW - verify the cited sources")
        else:
            conf = "🟡 Confidence: MEDIUM"

        # ── ساخت جواب ──
        lines = [conf, ""]
        if cve_hits:
            lines.append("🛡 Official NVD data:")
            for c in cve_hits:
                lines.append("   " + c[:600])
            lines.append("")
        if inst:
            lines.append("⚡ Instant answer: " + inst)
            if inst_src:
                lines.append("   source: " + inst_src)
            lines.append("")
        if chosen:
            lines.append("🌐 Details (from %d page(s)):" % len(set(c[3] for c in chosen)))
            lines.append("")
            sources = []
            for i, (sc, s, t, u) in enumerate(chosen, 1):
                lines.append("%d. %s" % (i, s))
                if u and u not in sources:
                    sources.append(u)
            if sources:
                lines.append("")
                lines.append("📎 Sources:")
                for u in sources[:5]:
                    lines.append("   • " + u)
        answer = "\n".join(lines)

        self._mem_set(q, answer)
        return answer

    def search_and_answer(self, question):
        try:
            return self.extract_answer(question)
        except Exception as e:
            return "❌ Web search error: %s" % e

    def answer_async(self, question, callback):
        def _work():
            callback(self.search_and_answer(question) or "No web result found.")
        threading.Thread(target=_work, daemon=True).start()

    # ─────────────── 🖼 Image search (v3.1) ───────────────
    def image_search(self, query, max_images=6, save_dir=None):
        """جستجوی تصویر + ذخیره در پوشه محلی. مسیر فایل‌ها را برمی‌گرداند."""
        from ddgs import DDGS
        results = []
        with DDGS() as d:
            for r in d.images(query, max_results=max_images):
                results.append({
                    "title": r.get("title", ""),
                    "image": r.get("image") or r.get("thumbnail", ""),
                    "source": r.get("source", ""),
                    "url": r.get("url", ""),
                })
        if not results:
            return None

        save_dir = save_dir or os.path.expanduser("~/.toolbox_pro_images")
        os.makedirs(save_dir, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        safe_q = re.sub(r"[^a-zA-Z0-9؀-ۿ]+", "_", query)[:40]

        lines = ["🖼 Image results for: %s" % query, ""]
        saved = []
        for i, r in enumerate(results, 1):
            img_url = r["image"]
            if not img_url:
                continue
            # دانلود و ذخیره تصویر
            fname = os.path.join(save_dir, "%s_%s_%d.img" % (safe_q, stamp, i))
            ok = False
            try:
                req = urllib.request.Request(img_url, headers=UA)
                data = urllib.request.urlopen(req, timeout=10).read()
                if len(data) > 500:   # فایل معتبر
                    ext = ".jpg"
                    if data[:8] == b"\x89PNG\r\n\x1a\n":
                        ext = ".png"
                    elif data[:3] == b"GIF":
                        ext = ".gif"
                    elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
                        ext = ".webp"
                    fname += ext
                    with open(fname, "wb") as f:
                        f.write(data)
                    saved.append(fname)
                    ok = True
            except Exception:
                pass
            _t = r["title"]
            if re.search("[\u0600-\u06FF]", _t):
                _t = r["source"] or r["url"] or "image"
            lines.append("%d. %s" % (i, _t))
            lines.append("   💾 %s" % (fname if ok else "(download failed)"))
            lines.append("   🔗 %s" % r["url"])
            lines.append("")

        if saved:
            lines.append("📁 %d image(s) saved to: %s" % (len(saved), save_dir))
        return "\n".join(lines)

    def image_search_and_answer(self, question):
        try:
            q = question.strip()
            low = q.lower()
            if low.startswith(("img ", "image ", "/img ", "/image ")):
                q = re.sub(r"^(/?)(img|image)\s+", "", q, flags=re.I)
            r = self.image_search(q)
            return r or "❌ No images found for: %s" % q
        except Exception as e:
            return "❌ Image search error: %s" % e

    # ─────────────── 📦 Offline archive (v3.2) ───────────────
    def _arc_db(self):
        con = sqlite3.connect(self.arc_path)
        con.execute("CREATE TABLE IF NOT EXISTS pages(url TEXT PRIMARY KEY, title TEXT, text TEXT, ts REAL)")
        return con

    def archive_put(self, url, title, text):
        try:
            with self._arc_db() as con:
                con.execute("INSERT OR REPLACE INTO pages(url,title,text,ts) VALUES(?,?,?,?)",
                            (url, title or "", (text or "")[:60000], time.time()))
        except Exception:
            pass

    def archive_search(self, question, top_sentences=5):
        """Search ONLY the local archive - no internet needed."""
        kws = self._keywords(question)
        if not kws:
            return None
        try:
            with self._arc_db() as con:
                rows = con.execute("SELECT url,title,text FROM pages ORDER BY ts DESC LIMIT 500").fetchall()
        except Exception:
            return None
        if not rows:
            return "📦 Archive is empty. Use /web normally first - every page read is archived automatically."
        scored = []
        for url, title, text in rows:
            tw = set(re.findall(r"[a-zA-Z\u0600-\u06FF]+", (title or "").lower()))
            for pos, s in enumerate(self._sentences(text or "")):
                sc = self._score(s, kws, {}, tw, pos, 0)
                if sc >= 4.0:
                    scored.append((sc, s, title, url))
        scored.sort(key=lambda x: -x[0])
        chosen, seen = [], set()
        for sc, s, t, u in scored:
            k = s[:50].lower()
            if k in seen:
                continue
            seen.add(k)
            chosen.append((s, t, u))
            if len(chosen) >= top_sentences:
                break
        if not chosen:
            return None
        lines = ["📦 OFFLINE answer from local archive (%d pages stored):" % len(rows), ""]
        sources = []
        for i, (s, t, u) in enumerate(chosen, 1):
            lines.append("%d. %s" % (i, s))
            if u and u not in sources:
                sources.append(u)
        lines.append("")
        lines.append("📎 Original sources (archived):")
        for u in sources[:4]:
            lines.append("   • " + u)
        return "\n".join(lines)

    def archive_stats(self):
        try:
            with self._arc_db() as con:
                n = con.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
                sz = con.execute("SELECT SUM(LENGTH(text)) FROM pages").fetchone()[0] or 0
        except Exception:
            n, sz = 0, 0
        return ("📦 Offline Archive\n"
                "   Pages stored: %d\n"
                "   Total text: %.2f MB\n"
                "   Database: %s\n"
                "   Pages are archived automatically whenever web search reads them.\n"
                "   /offline <question>  = search archive without internet\n"
                "   To clear everything: delete the database file." % (n, sz / 1048576.0, self.arc_path))

    # ─────────────── 📖 FULL explanation (v5.2) ───────────────
    def full_explanation(self, question, max_pages=8, max_paragraphs=15, char_cap=20000):  # v5.3 long answers
        """Search with the EXACT user query and return a long, complete
        explanation built from full paragraphs of the best sources."""
        kws = self._keywords(question)
        if not kws:
            return None
        try:
            results = self.search(question, max_results=max_pages + 3)
        except Exception:
            return None
        if not results:
            return None
        pages = []
        ranked = [r for r in results if r.get("url")][:max_pages]
        with ThreadPoolExecutor(max_workers=6) as ex:
            futs = {ex.submit(self.fetch_text, r["url"]): (i, r) for i, r in enumerate(ranked)}
            for f in as_completed(futs):
                try:
                    title, text = f.result()
                    if text:
                        pages.append((title, text, futs[f][1]["url"], futs[f][0]))
                except Exception:
                    pass
        pages.sort(key=lambda x: x[3])
        min_hits = 1 if len(kws) <= 3 else 2
        scored = []
        for title, text, url, rank in pages:
            paras = [p.strip() for p in text.split("\n\n") if 80 < len(p.strip()) < 4000]
            for pos, p in enumerate(paras):
                pl = p.lower()
                hits = sum(1 for k in kws if k in pl)
                if hits < min_hits:
                    continue
                sc = hits * 3.0 + max(0.0, 2.0 - rank * 0.3) + max(0.0, 1.0 - pos * 0.03)
                scored.append((sc, p, title, url, pos))
        scored.sort(key=lambda x: -x[0])
        chosen, seen = [], set()
        for sc, p, tt, u, pos in scored:
            key = p[:60].lower()
            if key in seen:
                continue
            seen.add(key)
            chosen.append((sc, p, tt, u, pos))
            if len(chosen) >= max_paragraphs:
                break
        if not chosen:
            return None
        by_src = {}
        for sc, p, tt, u, pos in chosen:
            by_src.setdefault(u, {"title": tt, "best": sc, "paras": []})
            by_src[u]["paras"].append((pos, p))
        order = sorted(by_src.items(), key=lambda kv: -kv[1]["best"])
        lines = ['🔎 Searched for (exact query): "%s"' % question,
                 "📖 FULL explanation from %d source(s):" % len(order), ""]
        total = 0
        srcs = []
        for u, info in order:
            lines.append("━━ %s ━━" % (info["title"] or u))
            lines.append("   %s" % u)
            lines.append("")
            for pos, p in sorted(info["paras"]):
                if total + len(p) > char_cap:
                    continue
                lines.append(p)
                lines.append("")
                total += len(p)
            srcs.append(u)
        lines.append("📎 Sources:")
        for u in srcs[:5]:
            lines.append("   • " + u)
        return "\n".join(lines)
