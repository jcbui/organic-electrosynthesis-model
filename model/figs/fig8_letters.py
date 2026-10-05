"""Jonas Rein's comment 1500, option 2: letter every marker in the cell, and put that letter on
each failure mode's leader where it leaves its box.  Then no line has to be followed.

Letters skip I (reads as 1).  Each mode's letters are exactly the markers its leaders reach,
derived from the vector paths (not from the caption prose).
"""
import pymupdf

import os
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(os.path.dirname(_HERE))
SRC = os.path.join(_ROOT, "Figures", "Organic ESynth Failure Modes Figure_v3.pdf")
LATO = os.path.expanduser("~/Library/Fonts/Lato-Bold.ttf")
COL = {"red":(0.847,0.141,0.208),"blue":(0.0,0.498,0.737),"cyan":(0.0,0.741,0.804),
       "purple":(0.545,0.494,0.647),"yellow":(0.992,0.745,0.063),"grey":(0.6,0.608,0.62),
       "dark":(0.216,0.227,0.259)}

# letter -> (component, colour, where the token sits)
MARKERS = [
 ("A","flow field (left)",   "cyan",  (577, 372)),
 ("B","anode assembly",      "red",   (575, 511)),
 ("C","anode",               "red",   (699, 410)),
 ("D","porous transport layer","dark",(640, 718)),
 ("E","anolyte",             "purple",(884, 497)),
 ("F","separator",           "yellow",(912, 628)),
 ("G","interelectrode gap",  "grey",  (975, 568)),
 ("H","catholyte",           "purple",(1094,643)),
 ("J","cathode assembly",    "blue",  (1330,497)),
 ("K","cathode",             "blue",  (1190,714)),
 ("L","flow field (right)",  "cyan",  (1373,623)),
]

# a chip on each leader, just outside the box it leaves
CHIPS = [
 ("E","purple",(372, 144)),    # Solvent boil-off
 ("C","red",   (372, 327)),    # Sacrificial anode consumption
 ("C","red",   (368, 670)),    # Electrode fouling
 ("C","red",   (372, 965)),    # Corrosion product accumulation
 ("K","blue",  (113, 884)),    # Corrosion product accumulation
 ("A","cyan",  (368, 1069)),   # Corrosion product accumulation
 ("D","dark",  (567, 880)),    # Solids precipitation
 ("F","yellow",(725, 880)),    # Solids precipitation
 ("K","blue",  (744, 840)),    # Solids precipitation
 ("F","yellow",(960, 880)),    # Electrolyte breakdown
 ("H","purple",(1046,880)),    # Electrolyte breakdown
 ("C","red",   (1718,884)),    # Native oxide passivation
 ("K","blue",  (1580,887)),    # Native oxide passivation
 ("L","cyan",  (1522,930)),    # Native oxide passivation
 ("G","grey",  (1528,578)),    # Dendritic structure formation
 ("F","yellow",(1520,350)),    # Membrane fouling
 ("B","red",   (1522,64)),     # Uneven transport
 ("J","blue",  (1522,140)),    # Uneven transport
]

R_TOK, R_CHIP, FS = 19.0, 17.0, 26.0

def draw(doc, out_png=None, zoom=1100/1920):
    p = doc[0]
    p.insert_font(fontname="latob", fontfile=LATO)
    F = pymupdf.Font(fontfile=LATO)
    def token(letter, colour, xy, r):
        c = COL[colour]
        p.draw_circle(pymupdf.Point(*xy), r+3.0, color=None, fill=(1,1,1), width=0)
        p.draw_circle(pymupdf.Point(*xy), r,     color=None, fill=c,       width=0)
        w = F.text_length(letter, fontsize=FS)
        p.insert_text(pymupdf.Point(xy[0]-w/2, xy[1]+FS*0.35), letter,
                      fontname="latob", fontsize=FS, color=(1,1,1))
    for L,_,col,xy in MARKERS: token(L, col, xy, R_TOK)
    for L,col,xy in CHIPS:     token(L, col, xy, R_CHIP)
    return doc

