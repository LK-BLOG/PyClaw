"""PPT 生成：标题 + 要点，输出到 out/。"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

def make_ppt(args, ctx=None):
    try:
        from pptx import Presentation
        from pptx.util import Pt
    except ImportError:
        return "没装 python-pptx：pip install python-pptx"
    title = args.get("title") or "未命名演示"
    slides = args.get("slides") or []
    prs = Presentation()
    cover = prs.slides.add_slide(prs.slide_layouts[0])
    cover.shapes.title.text = title
    if len(cover.placeholders) > 1:
        cover.placeholders[1].text = args.get("subtitle") or ""
    for item in slides:
        layout = prs.slide_layouts[1]
        slide = prs.slides.add_slide(layout)
        slide.shapes.title.text = str(item.get("title") or "")
        body = slide.placeholders[1].text_frame
        body.text = ""
        for i, point in enumerate(item.get("bullets") or []):
            para = body.paragraphs[0] if i == 0 else body.add_paragraph()
            para.text = str(point)
            para.font.size = Pt(18)
    out_dir = ROOT / "out"
    out_dir.mkdir(exist_ok=True)
    name = (args.get("filename") or title).replace("/", "_").replace("\\", "_")[:40]
    path = out_dir / f"{name}.pptx"
    prs.save(path)
    return f"已生成 {path}（{len(slides) + 1} 页）"

def register(ctx):
    ctx.add_tool("make_ppt", "生成一个 PPTX 文件", {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "subtitle": {"type": "string"},
            "filename": {"type": "string"},
            "slides": {"type": "array", "items": {"type": "object"}}
        },
        "required": ["title"]}, make_ppt)
