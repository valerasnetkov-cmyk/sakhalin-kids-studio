"""Tests for sakhalin svg_scene_renderer.py - SKIDS-008."""

from __future__ import annotations
import tempfile
import unittest
from pathlib import Path

from tools.character.sakhalin.svg_scene_renderer import (
    SvgRenderError,
    render_frame,
)

_FOX_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 700" data-rig-profile="fox_cartoon"><g data-part="body"><rect width="100" height="100"/></g><g data-part="head"><g data-motion-root=""><circle r="50"/></g></g><g data-part="eye_left" data-default-variant="open"><g data-variant="open"><circle r="5"/></g><g data-variant="closed"><line x1="-5" y1="0" x2="5" y2="0"/></g></g><g data-expression="neutral"><rect width="10" height="10"/></g><g data-expression="curious"><rect width="20" height="20"/></g><g data-gaze="center"><circle cx="0" cy="0" r="2"/></g><g data-gaze="left"><circle cx="-3" cy="0" r="2"/></g><g data-gaze="right"><circle cx="3" cy="0" r="2"/></g><g data-part="mouth"><g data-viseme="REST"><rect width="8" height="4"/></g><g data-viseme="A"><rect width="8" height="4"/></g><g data-viseme="E"><rect width="8" height="4"/></g><g data-viseme="O"><rect width="8" height="4"/></g><g data-viseme="U"><rect width="8" height="4"/></g><g data-viseme="MBP"><rect width="8" height="4"/></g><g data-viseme="FV"><rect width="8" height="4"/></g><g data-viseme="SH"><rect width="8" height="4"/></g><g data-viseme="L"><rect width="8" height="4"/></g><g data-viseme="S"><rect width="8" height="4"/></g></g></svg>'
_LION_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 700" data-rig-profile="sea_lion_cartoon"><g data-part="body"><rect width="80" height="80"/></g><g data-part="head"><g data-motion-root=""><circle r="40"/></g></g><g data-part="mouth"><g data-viseme="REST"><rect width="6" height="3"/></g><g data-viseme="A"><rect width="6" height="3"/></g><g data-viseme="E"><rect width="6" height="3"/></g><g data-viseme="O"><rect width="6" height="3"/></g><g data-viseme="U"><rect width="6" height="3"/></g><g data-viseme="MBP"><rect width="6" height="3"/></g><g data-viseme="FV"><rect width="6" height="3"/></g><g data-viseme="SH"><rect width="6" height="3"/></g><g data-viseme="L"><rect width="6" height="3"/></g><g data-viseme="S"><rect width="6" height="3"/></g></g></svg>'
_SCRIPT_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" data-rig-profile="fox_cartoon"><script>alert(1)</script><g data-part="body"><rect width="100" height="100"/></g><g data-part="head"><g data-motion-root=""><circle r="50"/></g></g><g data-part="mouth"><g data-viseme="REST"><rect width="8" height="4"/></g></g></svg>'
_NOROOT_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 700" data-rig-profile="fox_cartoon"><g data-part="head"><circle r="50"/></g><g data-part="mouth"><g data-viseme="REST"><rect width="8" height="4"/></g></g></svg>'
_EVENT_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" data-rig-profile="fox_cartoon"><g onclick="alert(1)" data-part="body"><rect width="100" height="100"/></g><g data-part="head"><g data-motion-root=""><circle r="50"/></g></g><g data-part="mouth"><g data-viseme="REST"><rect width="8" height="4"/></g></g></svg>'
_HREF_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" data-rig-profile="fox_cartoon"><g href="https://evil.com" data-part="body"><rect width="100" height="100"/></g><g data-part="head"><g data-motion-root=""><circle r="50"/></g></g><g data-part="mouth"><g data-viseme="REST"><rect width="8" height="4"/></g></g></svg>'

def _fox(pid, **ov):
    p={"version":"1.0","id":pid,"rig_profile":"fox_cartoon",
       "state":{"parts":{"head":{"rotation_deg":0}}}}
    if ov: p['state'].update(ov)
    return p

def _lion(pid, **ov):
    p={"version":"1.0","id":pid,"rig_profile":"sea_lion_cartoon",
       "state":{"parts":{"head":{"rotation_deg":0}}}}
    if ov: p['state'].update(ov)
    return p

def _tl(rig='fox_cartoon', dur=900, poses=None):
    if poses is None: poses=['idle','talk','idle']
    sd=dur//len(poses); segs=[]
    for i,pid in enumerate(poses):
        segs.append({'start_ms':i*sd,'end_ms':(i+1)*sd,'pose':pid,'viseme':'REST'})
    segs[-1]['end_ms']=dur
    return {'version':'1.0','rig_profile':rig,'duration_ms':dur,'segments':segs}

def _wf(tmp,n,c): (tmp/n).write_text(c,encoding='utf-8')

def _ch(asset,tl,poses,inst='makar',x=300,y=620,scale=1.0):
    return {'instance_id':inst,'asset_path':asset,'x':x,'y':y,'scale':scale,
            'timeline':tl,'poses_by_id':{p['id']:p for p in poses}}

class T1(unittest.TestCase):
  def test_single(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'f.svg',_FOX_SVG)
      p=[_fox('idle')]; tl=_tl(dur=100,poses=['idle'])
      s=render_frame(t,640,480,0,[_ch('f.svg',tl,p,x=100,y=200)])
      self.assertIn("makar",s)
      self.assertIn("translate(100 200)",s)

  def test_two(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'f.svg',_FOX_SVG); _wf(t,'l.svg',_LION_SVG)
      tf=_tl(dur=100,poses=['idle'])
      tl=_tl(rig='sea_lion_cartoon',dur=100,poses=['idle'])
      s=render_frame(t,640,480,0,[
        _ch('f.svg',tf,[_fox('idle')],inst='makar'),
        _ch('l.svg',tl,[_lion('idle')],inst='leva',x=500)])
      self.assertIn("makar",s); self.assertIn("leva",s)

  def test_deterministic(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'f.svg',_FOX_SVG)
      p=[_fox('idle')]; tl=_tl(dur=100,poses=['idle'])
      c=[_ch('f.svg',tl,p)]
      self.assertEqual(render_frame(t,640,480,0,c),render_frame(t,640,480,0,c))

class T2(unittest.TestCase):
  def test_boundary(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'f.svg',_FOX_SVG)
      tl=_tl(dur=600,poses=['idle','talk'])
      s=render_frame(t,640,480,300,[_ch('f.svg',tl,[_fox('idle'),_fox('talk')])])
      self.assertIn("<svg",s)

  def test_neg(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'f.svg',_FOX_SVG)
      tl=_tl(dur=100,poses=['idle'])
      with self.assertRaises(SvgRenderError):
        render_frame(t,640,480,-1,[_ch('f.svg',tl,[_fox('idle')])])

  def test_eq_dur(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'f.svg',_FOX_SVG)
      tl=_tl(dur=100,poses=['idle'])
      with self.assertRaises(SvgRenderError):
        render_frame(t,640,480,100,[_ch('f.svg',tl,[_fox('idle')])])

  def test_over(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'f.svg',_FOX_SVG)
      tl=_tl(dur=100,poses=['idle'])
      with self.assertRaises(SvgRenderError):
        render_frame(t,640,480,200,[_ch('f.svg',tl,[_fox('idle')])])

class T3(unittest.TestCase):
  def test_missing(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'f.svg',_FOX_SVG)
      tl=_tl(dur=100,poses=['nope'])
      with self.assertRaises(SvgRenderError):
        render_frame(t,640,480,0,[_ch('f.svg',tl,[])])

  def test_key_mismatch(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'f.svg',_FOX_SVG)
      p=_fox('idle'); p['id']='wrong'
      tl=_tl(dur=100,poses=['idle'])
      with self.assertRaises(SvgRenderError):
        render_frame(t,640,480,0,[_ch('f.svg',tl,[p])])

  def test_rig_mismatch(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'f.svg',_FOX_SVG)
      p=_fox('idle'); p['rig_profile']='sea_lion_cartoon'
      tl=_tl(dur=100,poses=['idle'])
      with self.assertRaises(SvgRenderError):
        render_frame(t,640,480,0,[_ch('f.svg',tl,[p])])

class T4(unittest.TestCase):
  def test_svg_rig(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'f.svg',_LION_SVG)
      tl=_tl(dur=100,poses=['idle'])
      with self.assertRaises(SvgRenderError):
        render_frame(t,640,480,0,[_ch('f.svg',tl,[_fox('idle')])])

class T5(unittest.TestCase):
  def test_rotate(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'f.svg',_FOX_SVG)
      p=_fox('idle',parts={'head':{'rotation_deg':-4}})
      tl=_tl(dur=100,poses=['idle'])
      s=render_frame(t,640,480,0,[_ch('f.svg',tl,[p])])
      self.assertIn("rotate(-4)",s)

  def test_no_root(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'f.svg',_NOROOT_SVG)
      p=_fox('idle',parts={'head':{'rotation_deg':10}})
      tl=_tl(dur=100,poses=['idle'])
      with self.assertRaises(SvgRenderError):
        render_frame(t,640,480,0,[_ch('f.svg',tl,[p])])

class T6(unittest.TestCase):
  def test_variant(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'f.svg',_FOX_SVG)
      p=_fox('idle',parts={'head':{'rotation_deg':0},'eye_left':{'variant':'closed'}})
      tl=_tl(dur=100,poses=['idle'])
      s=render_frame(t,640,480,0,[_ch('f.svg',tl,[p])])
      self.assertIn("display=\"none\"",s)

  def test_bad_variant(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'f.svg',_FOX_SVG)
      p=_fox('idle',parts={'head':{'rotation_deg':0},'eye_left':{'variant':'blink'}})
      tl=_tl(dur=100,poses=['idle'])
      with self.assertRaises(SvgRenderError):
        render_frame(t,640,480,0,[_ch('f.svg',tl,[p])])

  def test_default(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'f.svg',_FOX_SVG)
      tl=_tl(dur=100,poses=['idle'])
      s=render_frame(t,640,480,0,[_ch('f.svg',tl,[_fox('idle')])])
      self.assertIn("data-variant",s)

class T7(unittest.TestCase):
  def test_expression(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'f.svg',_FOX_SVG)
      p=_fox('idle'); p['state']['expression']='curious'
      tl=_tl(dur=100,poses=['idle'])
      s=render_frame(t,640,480,0,[_ch('f.svg',tl,[p])])
      self.assertIn("data-expression",s)

  def test_bad_expr(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'f.svg',_FOX_SVG)
      p=_fox('idle'); p['state']['expression']='sad'
      tl=_tl(dur=100,poses=['idle'])
      with self.assertRaises(SvgRenderError):
        render_frame(t,640,480,0,[_ch('f.svg',tl,[p])])

class T8(unittest.TestCase):
  def test_gaze(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'f.svg',_FOX_SVG)
      p=_fox('idle'); p['state']['gaze']={'direction':'left'}
      tl=_tl(dur=100,poses=['idle'])
      s=render_frame(t,640,480,0,[_ch('f.svg',tl,[p])])
      self.assertIn("data-gaze",s)

  def test_bad_gaze(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'f.svg',_FOX_SVG)
      p=_fox('idle'); p['state']['gaze']={'direction':'up'}
      tl=_tl(dur=100,poses=['idle'])
      with self.assertRaises(SvgRenderError):
        render_frame(t,640,480,0,[_ch('f.svg',tl,[p])])

class T9(unittest.TestCase):
  def test_rest(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'f.svg',_FOX_SVG)
      tl=_tl(dur=100,poses=['idle'])
      s=render_frame(t,640,480,0,[_ch('f.svg',tl,[_fox('idle')])])
      self.assertIn("data-viseme",s)

  def test_all_vis(self):
    for v in ['REST','A','E','O','U','MBP','FV','SH','L','S']:
      with tempfile.TemporaryDirectory() as td:
        t=Path(td); _wf(t,'f.svg',_FOX_SVG)
        segs=[{'start_ms':0,'end_ms':100,'pose':'idle','viseme':v}]
        tl={'version':'1.0','rig_profile':'fox_cartoon','duration_ms':100,'segments':segs}
        s=render_frame(t,640,480,0,[_ch('f.svg',tl,[_fox('idle')])])
        self.assertIn("data-viseme",s)

  def test_bad_vis(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'f.svg',_FOX_SVG)
      segs=[{'start_ms':0,'end_ms':100,'pose':'idle','viseme':'X'}]
      tl={'version':'1.0','rig_profile':'fox_cartoon','duration_ms':100,'segments':segs}
      with self.assertRaises(SvgRenderError):
        render_frame(t,640,480,0,[_ch('f.svg',tl,[_fox('idle')])])

class T10(unittest.TestCase):
  def test_place(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'f.svg',_FOX_SVG)
      tl=_tl(dur=100,poses=['idle'])
      s=render_frame(t,640,480,0,[_ch('f.svg',tl,[_fox('idle')],x=10,y=20,scale=2.0)])
      self.assertIn("translate(10 20)",s); self.assertIn("scale(2.0)",s)

  def test_bad_scale(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'f.svg',_FOX_SVG)
      tl=_tl(dur=100,poses=['idle'])
      with self.assertRaises(SvgRenderError):
        render_frame(t,640,480,0,[_ch('f.svg',tl,[_fox('idle')],scale=0)])

  def test_zorder(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'f.svg',_FOX_SVG); _wf(t,'l.svg',_LION_SVG)
      tf=_tl(dur=100,poses=['idle'])
      tl=_tl(rig='sea_lion_cartoon',dur=100,poses=['idle'])
      s=render_frame(t,640,480,0,[
        _ch('f.svg',tf,[_fox('idle')],inst='makar'),
        _ch('l.svg',tl,[_lion('idle')],inst='leva')])
      self.assertLess(s.index('makar'),s.index('leva'))

class T11(unittest.TestCase):
  def test_traversal(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td)
      with self.assertRaises(SvgRenderError):
        render_frame(t,640,480,0,[_ch('../x.svg',_tl(dur=100,poses=['idle']),[_fox('idle')])])

  def test_abs(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td)
      with self.assertRaises(SvgRenderError):
        render_frame(t,640,480,0,[_ch('/etc/x.svg',_tl(dur=100,poses=['idle']),[_fox('idle')])])

  def test_nonsvg(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); (t/'b.txt').write_text('hi')
      with self.assertRaises(SvgRenderError):
        render_frame(t,640,480,0,[_ch('b.txt',_tl(dur=100,poses=['idle']),[_fox('idle')])])

  def test_script(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'b.svg',_SCRIPT_SVG)
      with self.assertRaises(SvgRenderError):
        render_frame(t,640,480,0,[_ch('b.svg',_tl(dur=100,poses=['idle']),[_fox('idle')])])

  def test_event(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'b.svg',_EVENT_SVG)
      with self.assertRaises(SvgRenderError):
        render_frame(t,640,480,0,[_ch('b.svg',_tl(dur=100,poses=['idle']),[_fox('idle')])])

  def test_href(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'b.svg',_HREF_SVG)
      with self.assertRaises(SvgRenderError):
        render_frame(t,640,480,0,[_ch('b.svg',_tl(dur=100,poses=['idle']),[_fox('idle')])])

class T12(unittest.TestCase):
  def test_no_mutate(self):
    import copy
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); _wf(t,'f.svg',_FOX_SVG)
      p=[_fox('idle')]; tl=_tl(dur=100,poses=['idle'])
      pc=copy.deepcopy(p); tc=copy.deepcopy(tl)
      render_frame(t,640,480,0,[_ch('f.svg',tl,p)])
      self.assertEqual(p,pc); self.assertEqual(tl,tc)

if __name__=='__main__': unittest.main()