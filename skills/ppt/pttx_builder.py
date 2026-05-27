"""
Pure Python PPTX Builder — zero dependencies (no python-pptx, no Node.js)
PPTX is just a ZIP of XML files. We write them directly.
"""
import zipfile, io, os, uuid
from xml.etree.ElementTree import Element, SubElement, tostring

NS = {
    'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
}
CT = 'http://schemas.openxmlformats.org/package/2006/content-types'
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'

def _q(tag, ns='a'):
    return f'{{{NS[ns]}}}{tag}'

# ── EMU conversion (1 inch = 914400 EMU) ──
def emu(inches): return int(inches * 914400)
def emu_cm(cm): return int(cm * 360000)

class PttxBuilder:
    """Minimal pure-Python PPTX generator."""

    def __init__(self, width_inches=13.33, height_inches=7.5):
        self.slides = []
        self.slide_rels = []
        self.rid = 1
        self.w = emu(width_inches)
        self.h = emu(height_inches)

    def _next_rid(self):
        r = self.rid; self.rid += 1; return r

    def add_slide(self, bg_color=None):
        slide = Element(_q('sld', ns='p'), {
            'xmlns:a': NS['a'], 'xmlns:r': NS['r'],
            'xmlns:p': NS['p']
        })
        cSld = SubElement(slide, _q('cSld', ns='p'))
        # Background
        if bg_color:
            bg = SubElement(cSld, _q('bg', ns='p'))
            bgPr = SubElement(bg, _q('bgPr', ns='p'))
            solid = SubElement(bgPr, _q('solidFill', ns='a'))
            srgb = SubElement(solid, _q('srgbClr', ns='a'))
            srgb.set('val', bg_color)
        spTree = SubElement(cSld, _q('spTree', ns='p'))
        grpPr = SubElement(spTree, _q('grpPr', ns='p'))
        xfrm = SubElement(grpPr, _q('xfrm', ns='a'))
        off = SubElement(xfrm, _q('off', ns='a')); off.set('x','0'); off.set('y','0')
        ext = SubElement(xfrm, _q('ext', ns='a')); ext.set('cx', str(self.w)); ext.set('cy', str(self.h))
        chExt = SubElement(grpPr, _q('chExt', ns='a')); chExt.set('cx', str(self.w)); chExt.set('cy', str(self.h))

        slide_data = {'xml': slide, 'spTree': spTree, 'shapes': []}
        self.slides.append(slide_data)

        # Slide relationship
        rid = self._next_rid()
        self.slide_rels.append(rid)
        return slide_data

    def add_rect(self, slide, x, y, w, h, fill, line=None):
        sp = SubElement(slide['spTree'], _q('sp', ns='p'))
        nvPr = SubElement(sp, _q('nvSpPr', ns='p'))
        cNvPr = SubElement(nvPr, _q('cNvPr', ns='p'))
        cNvPr.set('id', str(len(slide['shapes'])+1)); cNvPr.set('name', 'rect')
        cNvSpPr = SubElement(nvPr, _q('cNvSpPr', ns='p'))
        nvPr2 = SubElement(sp, _q('nvPr', ns='p'))

        spPr = SubElement(sp, _q('spPr', ns='a'))
        xfrm = SubElement(spPr, _q('xfrm', ns='a'))
        off = SubElement(xfrm, _q('off', ns='a')); off.set('x', str(emu(x))); off.set('y', str(emu(y)))
        ext = SubElement(xfrm, _q('ext', ns='a')); ext.set('cx', str(emu(w))); ext.set('cy', str(emu(h)))
        prst = SubElement(spPr, _q('prstGeom', ns='a')); prst.set('prst', 'rect')
        avLst = SubElement(prst, _q('avLst', ns='a'))

        # Fill
        sf = SubElement(spPr, _q('solidFill', ns='a'))
        sc = SubElement(sf, _q('srgbClr', ns='a')); sc.set('val', fill)

        # No line
        ln = SubElement(spPr, _q('ln', ns='a'))
        SubElement(ln, _q('noFill', ns='a'))

        slide['shapes'].append(sp)
        return sp

    def add_text(self, slide, text, x, y, w, h, size=18, bold=False, color="FFFFFF", font="Calibri", align="l", italic=False):
        sp = SubElement(slide['spTree'], _q('sp', ns='p'))
        nvPr = SubElement(sp, _q('nvSpPr', ns='p'))
        cNvPr = SubElement(nvPr, _q('cNvPr', ns='p'))
        cNvPr.set('id', str(len(slide['shapes'])+1)); cNvPr.set('name', 'text')
        cNvSpPr = SubElement(nvPr, _q('cNvSpPr', ns='p'))
        nvPr2 = SubElement(sp, _q('nvPr', ns='p'))

        spPr = SubElement(sp, _q('spPr', ns='a'))
        xfrm = SubElement(spPr, _q('xfrm', ns='a'))
        off = SubElement(xfrm, _q('off', ns='a')); off.set('x', str(emu(x))); off.set('y', str(emu(y)))
        ext = SubElement(xfrm, _q('ext', ns='a')); ext.set('cx', str(emu(w))); ext.set('cy', str(emu(h)))
        prst = SubElement(spPr, _q('prstGeom', ns='a')); prst.set('prst', 'rect')

        # No fill for text box
        noFill = SubElement(spPr, _q('noFill', ns='a'))
        ln = SubElement(spPr, _q('ln', ns='a'))
        SubElement(ln, _q('noFill', ns='a'))

        txBody = SubElement(sp, _q('txBody', ns='p'))
        bodyPr = SubElement(txBody, _q('bodyPr', ns='a'))
        al = {'l': 'l', 'center': 'ctr', 'right': 'r'}
        bodyPr.set('anchor', al.get(align, 'l'))

        p = SubElement(txBody, _q('p', ns='a'))
        pPr = SubElement(p, _q('pPr', ns='a'))
        pPr.set('algn', al.get(align, 'l'))

        r = SubElement(p, _q('r', ns='a'))
        rPr = SubElement(r, _q('rPr', ns='a'))
        rPr.set('sz', str(size * 100))
        rPr.set('b', '1' if bold else '0')
        rPr.set('i', '1' if italic else '0')
        latin = SubElement(rPr, _q('latin', ns='a'))
        latin.set('typeface', font)
        ea = SubElement(rPr, _q('ea', ns='a'))
        ea.set('typeface', font)
        solid = SubElement(rPr, _q('solidFill', ns='a'))
        srgb = SubElement(solid, _q('srgbClr', ns='a'))
        srgb.set('val', color)

        t = SubElement(r, _q('t', ns='a'))
        t.text = str(text) if text else ''

        endParaRPr = SubElement(p, _q('endParaRPr', ns='a'))
        endParaRPr.set('lang', 'zh-CN')

        slide['shapes'].append(sp)
        return sp

    def add_bullets(self, slide, items, x, y, w, h, size=16, color="333333", font="Calibri"):
        """Add bulleted text box"""
        sp = SubElement(slide['spTree'], _q('sp', ns='p'))
        nvPr = SubElement(sp, _q('nvSpPr', ns='p'))
        cNvPr = SubElement(nvPr, _q('cNvPr', ns='p'))
        cNvPr.set('id', str(len(slide['shapes'])+1)); cNvPr.set('name', 'bullets')
        cNvSpPr = SubElement(nvPr, _q('cNvSpPr', ns='p'))
        nvPr2 = SubElement(sp, _q('nvPr', ns='p'))

        spPr = SubElement(sp, _q('spPr', ns='a'))
        xfrm = SubElement(spPr, _q('xfrm', ns='a'))
        off = SubElement(xfrm, _q('off', ns='a')); off.set('x', str(emu(x))); off.set('y', str(emu(y)))
        ext = SubElement(xfrm, _q('ext', ns='a')); ext.set('cx', str(emu(w))); ext.set('cy', str(emu(h)))
        prst = SubElement(spPr, _q('prstGeom', ns='a')); prst.set('prst', 'rect')
        noFill = SubElement(spPr, _q('noFill', ns='a'))
        ln = SubElement(spPr, _q('ln', ns='a'))
        SubElement(ln, _q('noFill', ns='a'))

        txBody = SubElement(sp, _q('txBody', ns='p'))
        bodyPr = SubElement(txBody, _q('bodyPr', ns='a'))

        if isinstance(items, str): items = [items]
        for item in items:
            p = SubElement(txBody, _q('p', ns='a'))
            pPr = SubElement(p, _q('pPr', ns='a'))
            pPr.set('marL', str(emu(0.25)))
            pPr.set('indent', str(-emu(0.25)))
            buChar = SubElement(pPr, _q('buChar', ns='a'))
            buChar.set('char', '\u2022')  # bullet

            r = SubElement(p, _q('r', ns='a'))
            rPr = SubElement(r, _q('rPr', ns='a'))
            rPr.set('sz', str(size * 100))
            latin = SubElement(rPr, _q('latin', ns='a'))
            latin.set('typeface', font)
            solid = SubElement(rPr, _q('solidFill', ns='a'))
            srgb = SubElement(solid, _q('srgbClr', ns='a'))
            srgb.set('val', color)

            t = SubElement(r, _q('t', ns='a'))
            text = str(item.get("text", item.get("label", str(item)))) if isinstance(item, dict) else str(item)
            t.text = text

        slide['shapes'].append(sp)
        return sp

    def save(self, path):
        """Write PPTX file (ZIP of XML)"""
        buf = io.BytesIO()
        zf = zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED)

        # ── [Content_Types].xml ──
        ct = Element('Types', {'xmlns': CT})
        SubElement(ct, 'Default', {'Extension':'rels','ContentType':'application/vnd.openxmlformats-package.relationships+xml'})
        SubElement(ct, 'Default', {'Extension':'xml','ContentType':'application/xml'})
        for i in range(len(self.slides)):
            SubElement(ct, 'Override', {'PartName': f'/ppt/slides/slide{i+1}.xml',
                'ContentType':'application/vnd.openxmlformats-officedocument.presentationml.slide+xml'})
        SubElement(ct, 'Override', {'PartName':'/ppt/presentation.xml',
            'ContentType':'application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml'})
        SubElement(ct, 'Override', {'PartName':'/ppt/slideMasters/slideMaster1.xml',
            'ContentType':'application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml'})
        SubElement(ct, 'Override', {'PartName':'/ppt/slideLayouts/slideLayout1.xml',
            'ContentType':'application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml'})
        SubElement(ct, 'Override', {'PartName':'/ppt/theme/theme1.xml',
            'ContentType':'application/vnd.openxmlformats-officedocument.theme+xml'})
        zf.writestr('[Content_Types].xml', _xml(ct))

        # ── _rels/.rels ──
        r = Element('Relationships', {'xmlns': REL})
        SubElement(r, 'Relationship', {'Id':'rId1','Type':f'{NS["r"]}/officeDocument','Target':'ppt/presentation.xml'})
        zf.writestr('_rels/.rels', _xml(r))

        # ── ppt/presentation.xml ──
        pres = Element(_q('presentation', ns='p'), {'xmlns:a':NS['a'],'xmlns:r':NS['r'],'xmlns:p':NS['p']})
        SubElement(pres, _q('sldMasterIdLst', ns='p'))
        sldIdLst = SubElement(pres, _q('sldIdLst', ns='p'))
        for i, rid in enumerate(self.slide_rels):
            SubElement(sldIdLst, _q('sldId', ns='p'), {'id':str(256+i), f'{{{NS["r"]}}}id':f'rId{rid}'})
        SubElement(pres, _q('sldSz', ns='p'), {'cx':str(self.w),'cy':str(self.h)})
        SubElement(pres, _q('notesSz', ns='p'), {'cx':'6858000','cy':'9144000'})
        zf.writestr('ppt/presentation.xml', _xml(pres))

        # ── ppt/_rels/presentation.xml.rels ──
        pr = Element('Relationships', {'xmlns': REL})
        for i, rid in enumerate(self.slide_rels):
            SubElement(pr, 'Relationship', {'Id':f'rId{rid}','Type':f'{NS["r"]}/slide','Target':f'slides/slide{i+1}.xml'})
        SubElement(pr, 'Relationship', {'Id':f'rId{self._next_rid()}','Type':f'{NS["r"]}/slideMaster','Target':'slideMasters/slideMaster1.xml'})
        zf.writestr('ppt/_rels/presentation.xml.rels', _xml(pr))

        # ── ppt/slides/slideN.xml ──
        for i, sd in enumerate(self.slides):
            zf.writestr(f'ppt/slides/slide{i+1}.xml', _xml(sd['xml']))
            sr = Element('Relationships', {'xmlns': REL})
            SubElement(sr, 'Relationship', {'Id':'rId1','Type':f'{NS["r"]}/slideLayout','Target':'../slideLayouts/slideLayout1.xml'})
            zf.writestr(f'ppt/slides/_rels/slide{i+1}.xml.rels', _xml(sr))

        # ── ppt/slideMasters/slideMaster1.xml ──
        sm = Element(_q('sldMaster', ns='p'), {'xmlns:a':NS['a'],'xmlns:r':NS['r'],'xmlns:p':NS['p']})
        cSld = SubElement(sm, _q('cSld', ns='p'))
        bg = SubElement(cSld, _q('bg', ns='p'))
        bgPr = SubElement(bg, _q('bgPr', ns='p'))
        solid = SubElement(bgPr, _q('solidFill', ns='a'))
        srgb = SubElement(solid, _q('srgbClr', ns='a')); srgb.set('val', 'FFFFFF')
        spTree = SubElement(cSld, _q('spTree', ns='p'))
        grpPr = SubElement(spTree, _q('grpPr', ns='p'))
        xfrm = SubElement(grpPr, _q('xfrm', ns='a'))
        off = SubElement(xfrm, _q('off', ns='a')); off.set('x','0'); off.set('y','0')
        ext = SubElement(xfrm, _q('ext', ns='a')); ext.set('cx', str(self.w)); ext.set('cy', str(self.h))
        SubElement(grpPr, _q('chExt', ns='a'), {'cx':str(self.w),'cy':str(self.h)})
        SubElement(sm, _q('sldLayoutIdLst', ns='p'))
        zf.writestr('ppt/slideMasters/slideMaster1.xml', _xml(sm))
        smr = Element('Relationships', {'xmlns': REL})
        SubElement(smr, 'Relationship', {'Id':'rId1','Type':f'{NS["r"]}/slideLayout','Target':'../slideLayouts/slideLayout1.xml'})
        SubElement(smr, 'Relationship', {'Id':'rId2','Type':f'{NS["r"]}/theme','Target':'../theme/theme1.xml'})
        zf.writestr('ppt/slideMasters/_rels/slideMaster1.xml.rels', _xml(smr))

        # ── ppt/slideLayouts/slideLayout1.xml ──
        sl = Element(_q('sldLayout', ns='p'), {'xmlns:a':NS['a'],'xmlns:r':NS['r'],'xmlns:p':NS['p']})
        SubElement(sl, _q('cSld', ns='p'), {'name':'Blank'})
        SubElement(sl, _q('clrMapOvr', ns='p'))
        zf.writestr('ppt/slideLayouts/slideLayout1.xml', _xml(sl))
        slr = Element('Relationships', {'xmlns': REL})
        SubElement(slr, 'Relationship', {'Id':'rId1','Type':f'{NS["r"]}/slideMaster','Target':'../slideMasters/slideMaster1.xml'})
        zf.writestr('ppt/slideLayouts/_rels/slideLayout1.xml.rels', _xml(slr))

        # ── ppt/theme/theme1.xml ──
        th = Element(_q('theme', ns='a'), {'xmlns:a':NS['a'], 'name':'Default'})
        themeEl = SubElement(th, _q('themeElements', ns='a'))
        clr = SubElement(themeEl, _q('clrScheme', ns='a'), {'name':'Default'})
        for name, val in [('dk1','000000'),('lt1','FFFFFF'),('dk2','44546A'),('lt2','E7E6E6'),('accent1','4472C4'),('accent2','ED7D31'),('accent3','A5A5A5'),('accent4','FFC000'),('accent5','5B9BD5'),('accent6','70AD47'),('hlink','0563C1'),('folHlink','954F72')]:
            el = SubElement(clr, _q(name, ns='a'))
            srgb = SubElement(el, _q('srgbClr', ns='a'))
            srgb.set('val', val)
        fontSch = SubElement(themeEl, _q('fontScheme', ns='a'), {'name':'Default'})
        for tag, latin, ea in [('majorFont','Calibri Light',''),('minorFont','Calibri','')]:
            f = SubElement(fontSch, _q(tag, ns='a'))
            SubElement(f, _q('latin', ns='a')).set('typeface', latin)
            if ea: SubElement(f, _q('ea', ns='a')).set('typeface', ea)
        fmtSch = SubElement(themeEl, _q('fmtScheme', ns='a'), {'name':'Default'})
        SubElement(th, _q('objectDefaults', ns='a'))
        zf.writestr('ppt/theme/theme1.xml', _xml(th))

        zf.close()
        with open(path, 'wb') as f:
            f.write(buf.getvalue())

def _xml(el):
    return b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + tostring(el, encoding='unicode').encode('utf-8')
