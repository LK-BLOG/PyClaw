"""联网工具：抓网页 + 搜索。"""
import html, json, re, urllib.parse, urllib.request
from html.parser import HTMLParser

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) PyClaw/1.0"

class Text(HTMLParser):
    SKIP = {"script", "style", "noscript", "svg", "head", "template"}
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.parts = []
    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        if t in self.SKIP:
            self.depth += 1
        elif self.depth == 0 and t in {"p", "div", "br", "li", "h1", "h2", "h3", "tr"}:
            self.parts.append("\n")
    def handle_endtag(self, tag):
        if tag.lower() in self.SKIP and self.depth:
            self.depth -= 1
    def handle_data(self, data):
        if self.depth == 0 and data.strip():
            self.parts.append(data)
    def text(self):
        raw = html.unescape(" ".join(self.parts))
        raw = re.sub(r"[ \t\r\f\v]+", " ", raw)
        return re.sub(r"\n{3,}", "\n\n", raw).strip()

def fetch_url(args, ctx=None):
    url = (args.get("url") or "").strip()
    if not url.startswith(("http://", "https://")):
        return "只支持 http/https"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as resp:
        raw = resp.read(2_000_000)
        charset = resp.headers.get_content_charset() or "utf-8"
    body = raw.decode(charset, "replace")
    if "html" not in (args.get("format") or "text"):
        return body[:200_000]
    p = Text()
    p.feed(body)
    return p.text()[:20000]

def web_search(args, ctx=None):
    q = (args.get("query") or "").strip()
    if not q:
        return "缺少 query"
    url = "https://duckduckgo.com/html/?q=" + urllib.parse.quote(q)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = resp.read(1_500_000).decode("utf-8", "replace")
    rows = []
    for m in re.finditer(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', body, re.S):
        link, title = m.group(1), re.sub(r"<[^>]+>", "", m.group(2))
        rows.append(f"- {html.unescape(title).strip()}\n  {html.unescape(link)}")
        if len(rows) >= 10:
            break
    return "\n".join(rows) or "没搜到结果（可能被限流，换个关键词）"

def register(ctx):
    ctx.add_tool("fetch_url", "抓取网页并返回正文文本", {
        "type": "object",
        "properties": {"url": {"type": "string"}, "format": {"type": "string"}},
        "required": ["url"]}, fetch_url)
    ctx.add_tool("web_search", "搜索网页，返回标题和链接", {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"]}, web_search)
