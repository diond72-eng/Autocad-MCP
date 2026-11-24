"""Dimensioned, project-neutral cabinet assemblies."""
from dataclasses import dataclass
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Size = Annotated[float, Field(gt=0, le=18000)]
Coordinate = Annotated[float, Field(ge=0, le=18000)]
Key = Annotated[str, Field(pattern=r"^[A-Z][A-Z0-9-]{0,15}$")]


class Spec(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Cabinet(Spec):
    id: Key
    kind: Literal["base", "overhead", "pantry", "drawer", "sink", "appliance", "open", "credenza", "wardrobe", "locker", "vanity", "island", "custom"]
    x: Coordinate
    y: Coordinate = 0
    z: Coordinate
    width: Size
    depth: Size
    height: Size
    board: Size = 18
    back: Size = 18
    front: Size = 22
    reveal: Size = 2
    doors: int = Field(default=2, ge=0, le=6)
    drawers: int = Field(default=0, ge=0, le=9)
    shelves: list[Size] = Field(default_factory=list, max_length=12)
    stile: Size = 40
    plinth_setback: Coordinate = 60
    plinth: Size = 18
    service_void: Coordinate = 0
    recessed: bool = True
    body_material: Key = "ML01"
    front_material: Key = "DF01"
    product: str = Field(default="PROVISIONAL GENERIC", max_length=36)

    @model_validator(mode="after")
    def proportions(self):
        if self.kind == "appliance":
            if self.doors or self.drawers or self.shelves:
                raise ValueError("Appliance bays are clear openings: set doors=0 and omit drawers/shelves")
            return self
        if min(self.width, self.height) <= 2 * self.board or self.depth <= self.back + self.service_void + 30:
            raise ValueError("Cabinet dimensions cannot accommodate configured panels")
        if self.doors and self.drawers:
            raise ValueError("Mixed drawer and door stacks require individually modelled assemblies")
        if self.doors and (self.width/self.doors - self.reveal <= 2*self.stile or self.height - self.reveal <= 2*self.stile):
            raise ValueError("Door module is too small for the configured stiles and reveals")
        if self.drawers and (self.height/self.drawers <= 3*self.board or self.width < 6*self.board):
            raise ValueError("Drawer module is too small for the configured boxes")
        if any(not self.board <= s <= self.height - 2*self.board for s in self.shelves):
            raise ValueError("Shelf elevations must fit between the bottom and top panels")
        if any(b-a < self.board for a,b in zip(sorted(self.shelves),sorted(self.shelves)[1:])):
            raise ValueError("Shelf boards overlap")
        if self.z and self.plinth_setback + self.plinth + self.service_void >= self.depth:
            raise ValueError("Plinth setback and rear void exceed cabinet depth")
        return self


class Service(Spec):
    id: Key
    kind: Literal["power", "light", "water", "waste"]
    x: Coordinate
    y: Coordinate
    z: Coordinate


class Project(Spec):
    title: str = Field(min_length=1, max_length=28)
    revision: str = Field(default="01", pattern=r"^[A-Z0-9]{1,5}$")
    width: Size
    depth: Size
    ceiling: Size
    cabinets: list[Cabinet] = Field(default_factory=list, max_length=36)
    services: list[Service] = Field(default_factory=list, max_length=24)
    notes: list[Annotated[str, Field(max_length=43)]] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def fit(self):
        ids = [c.id for c in self.cabinets] + [s.id for s in self.services]
        if len(ids) != len(set(ids)):
            raise ValueError("Assembly and service identifiers must be unique")
        for cabinet in self.cabinets:
            if (cabinet.x+cabinet.width > self.width or
                    cabinet.y+cabinet.depth+cabinet.front > self.depth or cabinet.z+cabinet.height > self.ceiling):
                raise ValueError(f"{cabinet.id} exceeds room envelope")
        for i, c in enumerate(self.cabinets):
            for b in self.cabinets[i+1:]:
                if all(min(a+size,q+other)>max(a,q) for a,size,q,other in
                    ((c.x,c.width,b.x,b.width),(c.y,c.depth,b.y,b.depth),(c.z,c.height,b.z,b.height))):
                    raise ValueError(f"Cabinet bodies overlap: {c.id}, {b.id}")
        for service in self.services:
            if service.x > self.width or service.y > self.depth or service.z > self.ceiling:
                raise ValueError(f"{service.id} is outside the room")
        return self


@dataclass(frozen=True)
class Part:
    id: str
    assembly: str
    role: str
    x: float
    y: float
    z: float
    w: float
    d: float
    h: float
    layer: str
    material: str
    status: str = "PROVISIONAL"

    def bounds(self, axes):
        bounds = ((self.x,self.x+self.w),(self.y,self.y+self.d),(self.z,self.z+self.h))
        return tuple(bounds[axis] for axis in axes)


def components(c):
    parts=[]
    x,y,z,w,d,h=c.x,c.y,c.z,c.width,c.depth,c.height
    t,b,f,r=c.board,c.back,c.front,c.reveal
    back_y = y + c.service_void
    if c.kind == "appliance":
        return [Part(f"{c.id}/opening",c.id,"opening",x,y,z,w,d,h,"HIDDEN","BAY")]

    def add(role,px,py,pz,pw,pd,ph,material=None,layer="JCUT"):
        if min(pw,pd,ph)<=0:
            raise ValueError(f"Invalid physical component: {c.id}/{role}")
        parts.append(Part(f"{c.id}/{role}",c.id,role,px,py,pz,pw,pd,ph,layer,material or c.body_material))

    for label,side_x in (("left",x),("right",x+w-t)):
        add(f"side-{label}",side_x,back_y,z,t,d-c.service_void,h)
    add("bottom",x+t,back_y,z,w-2*t,d-c.service_void,t)
    add("back",x+t,back_y,z+t,w-2*t,b,h-2*t,"BK01")
    if c.kind in ("sink","vanity"):
        rail=min(70,(d-c.service_void)/3)
        for label,ry in (("back",back_y),("front",y+d-rail)):
            add(f"top-rail-{label}",x+t,ry,z+h-t,w-2*t,rail,t)
    else:
        add("top",x+t,back_y,z+h-t,w-2*t,d-c.service_void,t)
    add("fixing-rail",x+t,back_y+b,z+h-2*t,w-2*t,min(20,d-c.service_void-b),t,"FX01","DETAIL")
    for i,shelf in enumerate(c.shelves):
        add(f"shelf-{i+1}",x+t,back_y+b,z+shelf,w-2*t,d-c.service_void-b-16,t)
        for side,xx in enumerate((x+t,x+w-t-5)):
            for row,yy in enumerate((back_y+b+12,y+d-24)):
                add(f"shelf-pin-{i}-{side}-{row}",xx,yy,z+shelf-5,5,5,5,"FX01","DETAIL")
    if 0<z<=250:
        add("plinth",x,y+d+f-c.plinth_setback-c.plinth,0,w,c.plinth,z,"KP01")
        foot_inset=max(t+15,min(w,d)/7)
        for i,xx in enumerate((x+foot_inset,x+w-foot_inset)):
            for j,yy in enumerate((back_y+20,y+d-40)):
                add(f"foot-{i}-{j}",xx-8,yy,0,16,16,z,"FX01","DETAIL")
                add(f"pad-{i}-{j}",xx-18,yy-10,0,36,36,min(z,8),"FX01","DETAIL")
    for i in range(c.doors):
        door_width=w/c.doors-r
        dx=x+r/2+i*(door_width+r)
        dz=z+r/2
        dh=h-r
        s=c.stile
        if c.recessed:
            for tag,off in (("left",0),("right",door_width-s)):
                add(f"door-{i}-{tag}",dx+off,y+d,dz,s,f,dh,c.front_material)
            for tag,off in (("bottom",0),("top",dh-s)):
                add(f"door-{i}-{tag}",dx+s,y+d,dz+off,door_width-2*s,f,s,c.front_material)
            add(f"door-{i}-panel",dx+s,y+d,dz+s,door_width-2*s,f*.65,dh-2*s,c.front_material,"DETAIL")
        else:
            add(f"door-{i}-panel",dx,y+d,dz,door_width,f,dh,c.front_material)
        handle_x=dx+door_width-23 if i%2==0 else dx+15
        handle_height=min(128,dh/2)
        add(f"handle-{i}",handle_x,y+d+f,dz+(dh-handle_height)/2,8,18,handle_height,"HD01","DETAIL")
        stations=(.13,.40,.64,.88) if dh>1500 else (.17,.83)
        hinge_x=dx+7 if i%2==0 else dx+door_width-32
        for n, station in enumerate(stations):
            hz=dz+dh*station
            add(f"hinge-{i}-{n}",hinge_x,y+d-17,hz-12,25,18,24,"HG01","DETAIL")
            add(f"mounting-plate-{i}-{n}",hinge_x,y+d-36,hz-14,16,19,28,"HG01","DETAIL")
    for i in range(c.drawers):
        dz=z+i*h/c.drawers
        face=h/c.drawers-r
        add(f"drawer-front-{i}",x+r/2,y+d,dz+r/2,w-r,f,face,c.front_material)
        drawer_depth=d-c.service_void-b-35
        box_height=face-20
        drawer_y=back_y+b+8
        drawer_z=dz+10
        add(f"drawer-base-{i}",x+2*t,drawer_y,drawer_z,w-4*t,drawer_depth,t)
        for side,xx in (("left",x+2*t),("right",x+w-3*t)):
            add(f"drawer-side-{i}-{side}",xx,drawer_y,drawer_z+t,t,drawer_depth,box_height-t)
            add(f"runner-{i}-{side}",xx-t/2,drawer_y,drawer_z,t/2,drawer_depth,10,"RN01","DETAIL")
        for tag,yy in (("back",drawer_y),("front",drawer_y+drawer_depth-t)):
            add(f"drawer-wall-{i}-{tag}",x+3*t,yy,drawer_z+t,w-6*t,t,box_height-t)
        add(f"drawer-handle-{i}",x+w*.36,y+d+f,dz+face/2,w*.28,18,8,"HD01","DETAIL")
    return parts
