"""Native CAD primitives extracted from the successful Rev 06 workflow."""
import json
from math import sqrt
from pathlib import Path

import ezdxf
import pymupdf as fitz
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.config import BackgroundPolicy, Configuration
from ezdxf.addons.drawing.layout import Page, Settings
from ezdxf.addons.drawing.pymupdf import PyMuPdfBackend
from ezdxf.enums import TextEntityAlignment as Align
from ezdxf.fonts import fonts
from ezdxf.math import BoundingBox2d, Vec2
from ezdxf.render.mleader import ConnectionSide

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
PROFILE = json.loads((ROOT / "profiles/professional-cad-v1.0.json").read_text())
FONT_STYLE = PROFILE["font"]["cad_style"]
CTB = ASSETS / "professional-cad.ctb"


def setup():
    doc = ezdxf.new("R2013", setup=True, units=4)
    doc.header["$MEASUREMENT"] = 1
    doc.header["$PSLTSCALE"] = PROFILE["linetypes"]["psltscale"]
    font = ASSETS / "fonts" / PROFILE["font"]["file"]
    if not font.is_file():
        raise FileNotFoundError(f"Required font missing; fallback disabled: {font}")
    fonts.font_manager.build(folders=[str(font.parent)])
    if not fonts.font_manager.has_font(font.name):
        raise RuntimeError(f"ezdxf could not resolve required font: {font.name}")
    doc.styles.new(FONT_STYLE, dxfattribs={"font": font.name, "width": PROFILE["font"]["width_factor"]})
    for name, layer in PROFILE["layers"].items():
        doc.layers.new(name, dxfattribs={"lineweight": layer["lineweight_hundredths_mm"], "color": layer["aci"]})
    doc.layers.get("VIEW").dxf.plot = 0
    for name in ("JOINERY-HIDDEN", "JOINERY-CENTRE"):
        doc.linetypes.new(name, dxfattribs={"description": name, "pattern": PROFILE["linetypes"][name]})
    doc.layers.get("HIDDEN").dxf.linetype = "JOINERY-HIDDEN"
    doc.layers.get("AXIS").dxf.linetype = "JOINERY-CENTRE"
    params = {key: value for key, value in PROFILE["dimensions"].items() if key.startswith("dim")}
    doc.dimstyles.new("SHOP", dxfattribs={"dimtxsty": FONT_STYLE, **params}).set_arrows(blk=PROFILE["dimensions"]["arrow"])
    return doc

def at(k,**kw): return {'layer':k,**kw}
def txt(e,s,x,y,h=PROFILE["font"]["general_mm"],align=Align.LEFT,layer='ANNO'):
    return e.add_text(s.upper(),dxfattribs=at(layer,height=h,style=FONT_STYLE)).set_placement((x,y),align=align)
def line(e,a,b,k): return e.add_line(a,b,dxfattribs=at(k))
def poly(e,p,k,closed): return e.add_lwpolyline(p,close=closed,dxfattribs=at(k))
def outline(e,x,y,w,h,k):
    return poly(e,[(x,y),(x+w,y),(x+w,y+h),(x,y+h)],k,True)
class View:
    def __init__(self,api,l,x,y,w,h,s,label,origin):
        self.api=api; self.l=l; self.s=s
        self.dx=100000*(len(api.views)+1); self.dy=15000
        self.paper=(x,y,w,h)
        self.y_sign=1
        self.bounds=(origin[0],origin[1],origin[0]+s*w,origin[1]+s*h)
        self.viewport=l.add_viewport((x+w/2,y+h/2),(w,h),self.p(origin[0]+s*w/2,origin[1]+s*h/2),s*h,dxfattribs=at('VIEW'))
        self.viewport.dxf.flags|=16384
        self.viewport.dxf.id=len(l.viewports())+1
        self.e=api.d.modelspace()
        api.views.append(self)
        if label:
            number=api.view_counts.get(l.name,0)+1;api.view_counts[l.name]=number
            l.add_circle((x+3,y-3.6),2.9,dxfattribs=at('SHEET'))
            txt(l,str(number),x+3,y-3.6,2.35,Align.MIDDLE_CENTER)
            txt(l,label,x+8,y-4.8,3.5)
            txt(l,f'1:{s}',x+w-2,y-4.8,2.15,Align.RIGHT)
            if w>=185 and s>=10:
                xx=x+w-65
                span=PROFILE['sheet']['scale_bar_model_mm']
                length=span/s
                line(l,(xx,y-3.7),(xx+length,y-3.7),'DIM')
                for x_tick in (xx,xx+length/2,xx+length):
                    line(l,(x_tick,y-5),(x_tick,y-2.45),'DIM')
                txt(l,'500',xx+length+2,y-4.45,1.7)
                api.scale_bars.append((l.name,s,length,span))
        api.meta.append((l.name,s,x,y,w,h,label))
    def flip_plan(self):
        self.y_sign=-1
        x0,y0,x1,y1=self.bounds
        self.viewport.dxf.view_center_point=self.p((x0+x1)/2,(y0+y1)/2)
    def p(self,x,y):return (self.dx+x,self.dy+self.y_sign*y)
    def rect(self,x,y,w,h,layer='JOINERY'):
        return self.poly([(x,y),(x+w,y),(x+w,y+h),(x,y+h)],layer,True)
    def line(self,a,b,layer='JOINERY'):return line(self.e,self.p(*a),self.p(*b),layer)
    def poly(self,points,layer='JOINERY',closed=False):return poly(self.e,[self.p(*p) for p in points],layer,closed)
    def circ(self,x,y,r,layer='DETAIL'):return self.e.add_circle(self.p(x,y),r,dxfattribs=at(layer))
    def arc(self,x,y,r,a,b,layer='HIDDEN'):
        if self.y_sign<0:a,b=(360-b)%360,(360-a)%360
        return self.e.add_arc(self.p(x,y),r,a,b,dxfattribs=at(layer))
    def label(self,text,x,y,h=PROFILE["font"]["general_mm"],align=Align.LEFT):
        return txt(self.e,text,*self.p(x,y),h*self.s,align)
    def hidden(self,a,b,layer='HIDDEN',paper_dash=PROFILE["linetypes"]["segment_pitch_mm_on_paper"]):
        length=sqrt((b[0]-a[0])**2+(b[1]-a[1])**2)
        if not length:return
        step=paper_dash*self.s
        for i in range(int(length//step)+1):
            lo=i*step/length;hi=min(1,(i+PROFILE["linetypes"]["segment_on_fraction"])*step/length)
            if hi>lo:
                self.line(tuple(a[j]+(b[j]-a[j])*lo for j in (0,1)),tuple(a[j]+(b[j]-a[j])*hi for j in (0,1)),layer).dxf.linetype='CONTINUOUS'
    def dim(self,a,b,base,angle=0,precision=0):
        model_length=abs(b[int(angle==90)]-a[int(angle==90)])
        if model_length==0:return
        dm=self.e.add_linear_dim(base=self.p(*base),p1=self.p(*a),p2=self.p(*b),angle=angle,dimstyle='SHOP',
              override={'dimscale':self.s,'dimdec':precision},dxfattribs=at('DIM'))
        dm.render()
        measured=dm.dimension.get_measurement()
        assert abs(measured-model_length)<1e-5,(measured,model_length)
        self.api.dimension_checks.append((self.l.name,dm.dimension.dxf.handle,model_length,measured))
        return dm.dimension
    def ord(self,x,y,offset):
        dm=self.e.add_ordinate_x_dim(self.p(x,y),(0,offset*self.y_sign),origin=self.p(0,y),dimstyle='SHOP',
            override={'dimscale':self.s},dxfattribs=at('DIM'))
        dm.render(); assert abs(dm.dimension.get_measurement().x-x)<1e-5
        self.api.dimension_checks.append((self.l.name,dm.dimension.dxf.handle,x,dm.dimension.get_measurement().x))
    def hatch(self,points,pattern='ANSI31',spacing=2.5):
        h=self.e.add_hatch(dxfattribs=at('HATCH'))
        h.set_pattern_fill(pattern,color=256,scale=spacing/3.175)
        h.paths.add_polyline_path([self.p(*p) for p in points],is_closed=True)
        return h
    def faced(self,x,y,w,h,layer='JCUT',pattern='ANSI31',spacing=None):
        self.rect(x,y,w,h,layer)
        return self.hatch([(x,y),(x+w,y),(x+w,y+h),(x,y+h)],pattern,spacing or self.s*1.45)
    def leader(self,points):
        return self.e.add_leader([self.p(*p) for p in points],dimstyle='SHOP',dxfattribs=at('ANNO'),override={'dimscale':self.s})
    def mleader(self,text,anchor,landing,h=2.05,frame=False):
        builder=self.e.add_multileader_mtext(dxfattribs=at('ANNO'))
        builder.set_content(text.upper(),color=7,char_height=h*self.s,style='ISO-JOINERY')
        builder.add_leader_line(ConnectionSide.left,[Vec2(self.p(*anchor))])
        builder.build(Vec2(self.p(*landing)))
        if frame: builder.multileader.dxf.has_text_frame=1
        return builder.multileader
    def tag(self,text,x,y):
        w=(len(text)*1.41+2.6)*self.s
        self.rect(x,y-.8*self.s*self.y_sign,w,4.05*self.s*self.y_sign,'ANNO')
        self.label(text,x+1.15*self.s,y,2.5)
        return w
    def ref(self,x,y,label,sheet):
        r=3.65*self.s
        self.circ(x,y,r,'ANNO');self.line((x-r,y),(x+r,y),'ANNO')
        self.label(label,x,y+1.65*self.s*self.y_sign,2.05,Align.MIDDLE_CENTER)
        self.label(sheet,x,y-1.55*self.s*self.y_sign,1.55,Align.MIDDLE_CENTER)
    def dashbox(self,x,y,w,h):
        for a,b in [((x,y),(x+w,y)),((x+w,y),(x+w,y+h)),((x+w,y+h),(x,y+h)),((x,y+h),(x,y))]: self.hidden(a,b)
    def ins(self,block,x,y):
        return self.e.add_blockref(block,self.p(x,y))
class API:
    def __init__(self):
        self.d=setup();self.layouts=[];self.views=[];self.meta=[];self.info={}
        self.view_counts={};self.dimension_checks=[];self.scale_bars=[]
    def sheet(self,id,title,subtitle=''):
        l=self.d.layouts.new(id)
        l.page_setup(size=(420,297),margins=(0,0,0,0),units='mm')
        l.set_plot_style(CTB.name,show=True)
        l.dxf.taborder=len(self.layouts)+1
        self.info[id]=(title,subtitle)
        self.layouts.append(l)
        return l
    def view(self,sheet,x,y,w,h,scale,label='',origin=(0,0)):return View(self,sheet,x,y,w,h,scale,label,origin)
    def paper(self,l,text,x,y,h=2.5):return txt(l,text,x,y,h)
    def notes(self,l,x,y,title,lines,step=4.25):
        txt(l,title,x,y,2.65)
        for i,s in enumerate(lines,1):txt(l,s,x,y-i*step,1.95)
    def table(self,l,title,headers,rows,x,y,cols,step=5.1):
        txt(l,title,x,y+5.5,3.2)
        for i,h in enumerate(headers):txt(l,h,x+cols[i]+1,y,2.35)
        line(l,(x,y-1.8),(x+cols[-1],y-1.8),'SHEET')
        for n,row in enumerate(rows,1):
            yy=y-n*step
            for i,t in enumerate(row):txt(l,str(t),x+cols[i]+1,yy,2.18)
            line(l,(x,yy-1.7),(x+cols[-1],yy-1.7),'BACKGROUND')

    def frame(self, layout, title, revision, status, rail):
        sheet = PROFILE["sheet"]
        outline(layout, *sheet["border_mm"], "BORDER")
        rail_x = sheet["rail_x_mm"]
        line(layout, (rail_x, 8), (rail_x, 289), "SHEET")
        line(layout, (8, 277), (rail_x, 277), "SHEET")
        txt(layout, self.info[layout.name][0], 13, 282, 3.5)
        for y, heading in zip((289, 244, 199, 163), ("FINISHES", "FITTINGS", "APPLIANCES", "NOTES"), strict=True):
            line(layout, (rail_x, y), (412, y), "SHEET")
            txt(layout, heading, 346, y - 5.8, 2.65)
            for index, item in enumerate(rail.get(heading, [])):
                txt(layout, item, 346, y - 14 - index * 4.6, 1.95)
        line(layout, (rail_x, 64), (412, 64), "SHEET")
        txt(layout, title, 346, 55, 2.5)
        txt(layout, f"{layout.name} / REV {revision}", 346, 46, 2.5)
        txt(layout, "A3 / MM / AS SHOWN", 346, 39, 1.95)
        txt(layout, status, 346, 32, 1.95)
        txt(layout, "CHECK ALL FIGURED DIMENSIONS ON SITE", 13, 9.8, 1.8)

    def save(self, out, title, revision, status, rail, proof=True):
        out.mkdir(parents=True, exist_ok=True)
        self.d.layouts.delete("Layout1")
        for layout in self.layouts:
            self.frame(layout, title, revision, status, rail)
            layout.reset_main_viewport(center=(210, 148.5), size=(420, 297))
        self.d.layouts.set_active_layout(self.layouts[0].name)
        audit = self.d.audit()
        if audit.errors or audit.fixes:
            raise ValueError("Generated native CAD failed structural audit")
        self.d.saveas(out / "drawing.dxf")
        plot(self, out, proof)


def plot(api, out, proof=True):
    with fitz.open() as package:
        for layout in api.layouts:
            backend = PyMuPdfBackend()
            context = RenderContext(api.d, ctb=str(CTB))
            Frontend(context, backend, config=Configuration(background_policy=BackgroundPolicy.WHITE)).draw_layout(layout)
            raw = backend.get_pdf_bytes(
                Page(420, 297), settings=Settings(fit_page=False),
                render_box=BoundingBox2d([(0, 0), (420, 297)]),
            )
            with fitz.open(stream=raw, filetype="pdf") as source, fitz.open() as single:
                page = single.new_page(width=420 * 72 / 25.4, height=297 * 72 / 25.4)
                page.show_pdf_page(source[0].rect, source, 0)
                single.save(out / f"{layout.name}.pdf", deflate=True)
                package.insert_pdf(single)
                if proof:
                    page.get_pixmap(dpi=PROFILE["sheet"]["proof_dpi"], alpha=False).save(out / f"{layout.name}.png")
        package.set_toc([[1, layout.name, i] for i, layout in enumerate(api.layouts, 1)])
        package.save(out / "package.pdf", deflate=True)
