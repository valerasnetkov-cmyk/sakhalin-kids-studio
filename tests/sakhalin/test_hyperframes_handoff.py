"""Tests for sakhalin hyperframes_handoff.py - SKIDS-009."""

from __future__ import annotations
import copy
import json
import tempfile
import unittest
from pathlib import Path

from tools.character.sakhalin.hyperframes_handoff import (
    HyperFramesHandoffError,
    _collect_boundaries,
    _intervals_from_bounds,
    build_hyperframes_workspace,
)

_FOX_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 700" data-rig-profile="fox_cartoon"><g data-part="body"><rect width="100" height="100"/></g><g data-part="head"><g data-motion-root=""><circle r="50"/></g></g><g data-part="mouth"><g data-viseme="REST"><rect width="8" height="4"/></g><g data-viseme="A"><rect width="8" height="4"/></g><g data-viseme="E"><rect width="8" height="4"/></g><g data-viseme="O"><rect width="8" height="4"/></g><g data-viseme="U"><rect width="8" height="4"/></g><g data-viseme="MBP"><rect width="8" height="4"/></g><g data-viseme="FV"><rect width="8" height="4"/></g><g data-viseme="SH"><rect width="8" height="4"/></g><g data-viseme="L"><rect width="8" height="4"/></g><g data-viseme="S"><rect width="8" height="4"/></g></g></svg>'
_LION_SVG = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 700" data-rig-profile="sea_lion_cartoon"><g data-part="body"><rect width="80" height="80"/></g><g data-part="head"><g data-motion-root=""><circle r="40"/></g></g><g data-part="mouth"><g data-viseme="REST"><rect width="6" height="3"/></g><g data-viseme="A"><rect width="6" height="3"/></g><g data-viseme="E"><rect width="6" height="3"/></g><g data-viseme="O"><rect width="6" height="3"/></g><g data-viseme="U"><rect width="6" height="3"/></g><g data-viseme="MBP"><rect width="6" height="3"/></g><g data-viseme="FV"><rect width="6" height="3"/></g><g data-viseme="SH"><rect width="6" height="3"/></g><g data-viseme="L"><rect width="6" height="3"/></g><g data-viseme="S"><rect width="6" height="3"/></g></g></svg>'

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

def _ch(asset,tl,poses,inst='makar',x=100,y=200,scale=1.0):
    return {'instance_id':inst,'asset_path':asset,'x':x,'y':y,'scale':scale,
            'timeline':tl,'poses_by_id':{p['id']:p for p in poses}}

def _wf(tmp,n,c): (tmp/n).write_text(c,encoding='utf-8')

class TBoundaryUnion(unittest.TestCase):
  def test_single_char(self):
    tl=_tl(dur=100,poses=['idle'])
    b,d=_collect_boundaries([_ch('f.svg',tl,[_fox('idle')])])
    self.assertEqual(d,100)
    self.assertEqual(b[0],0)
    self.assertEqual(b[-1],100)

  def test_two_chars_same_dur(self):
    tf=_tl(dur=300,poses=['idle','talk'])
    tl=_tl(rig='sea_lion_cartoon',dur=300,poses=['idle','talk'])
    c=[_ch('f.svg',tf,[_fox('idle'),_fox('talk')]),
       _ch('l.svg',tl,[_lion('idle'),_lion('talk')],inst='leva')]
    b,d=_collect_boundaries(c)
    self.assertEqual(d,300)
    self.assertEqual(b[0],0)
    self.assertEqual(b[-1],300)

  def test_different_boundaries_same_dur(self):
    tf={'version':'1.0','rig_profile':'fox_cartoon','duration_ms':300,
        'segments':[{'start_ms':0,'end_ms':150,'pose':'idle','viseme':'REST'},
                    {'start_ms':150,'end_ms':300,'pose':'talk','viseme':'REST'}]}
    tl={'version':'1.0','rig_profile':'sea_lion_cartoon','duration_ms':300,
        'segments':[{'start_ms':0,'end_ms':100,'pose':'idle','viseme':'REST'},
                    {'start_ms':100,'end_ms':200,'pose':'talk','viseme':'REST'},
                    {'start_ms':200,'end_ms':300,'pose':'idle','viseme':'REST'}]}
    c=[_ch('f.svg',tf,[_fox('idle'),_fox('talk')]),
       _ch('l.svg',tl,[_lion('idle'),_lion('talk')],inst='leva')]
    b,d=_collect_boundaries(c)
    self.assertEqual(d,300)
    self.assertIn(100,b)
    self.assertIn(150,b)
    self.assertIn(200,b)

  def test_duration_mismatch_fails(self):
    tf=_tl(dur=300,poses=['idle'])
    tl=_tl(rig='sea_lion_cartoon',dur=400,poses=['idle'])
    c=[_ch('f.svg',tf,[_fox('idle')]),
       _ch('l.svg',tl,[_lion('idle')],inst='leva')]
    with self.assertRaises(HyperFramesHandoffError):
      _collect_boundaries(c)

  def test_empty_fails(self):
    with self.assertRaises(HyperFramesHandoffError):
      _collect_boundaries([])

  def test_invalid_duration_fails(self):
    tl={'version':'1.0','rig_profile':'fox_cartoon','duration_ms':0,
        'segments':[]}
    with self.assertRaises(HyperFramesHandoffError):
      _collect_boundaries([_ch('f.svg',tl,[])])

class TIntervals(unittest.TestCase):
  def test_no_gaps(self):
    bounds=[0,100,200,300]
    ivs=_intervals_from_bounds(bounds,300)
    self.assertEqual(len(ivs),3)
    for i in range(len(ivs)-1):
      self.assertEqual(ivs[i][1],ivs[i+1][0])

  def test_no_overlaps(self):
    bounds=[0,100,200,300]
    ivs=_intervals_from_bounds(bounds,300)
    for i in range(len(ivs)-1):
      self.assertLessEqual(ivs[i][1],ivs[i+1][0])

  def test_final_equals_duration(self):
    bounds=[0,50,100]
    ivs=_intervals_from_bounds(bounds,100)
    self.assertEqual(ivs[-1][1],100)

  def test_single_interval(self):
    ivs=_intervals_from_bounds([0,100],100)
    self.assertEqual(len(ivs),1)
    self.assertEqual(ivs[0],(0,100))

class TConversion(unittest.TestCase):
  def test_ms_to_seconds(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); (t/'a.svg').write_text(_FOX_SVG,encoding='utf-8')
      tl=_tl(dur=1500,poses=['idle'])
      r=build_hyperframes_workspace(t,t/'out',640,480,
        [_ch('a.svg',tl,[_fox('idle')])])
      self.assertAlmostEqual(r['duration_s'],1.5,places=3)
      self.assertEqual(r['duration_ms'],1500)

  def test_interval_durations_sum_to_total(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); (t/'a.svg').write_text(_FOX_SVG,encoding='utf-8')
      tl=_tl(dur=600,poses=['idle','talk'])
      r=build_hyperframes_workspace(t,t/'out',640,480,
        [_ch('a.svg',tl,[_fox('idle'),_fox('talk')])])
      comp=t/'out'/f'compositions/{r["composition_id"]}.html'
      html=comp.read_text(encoding='utf-8')
      import re
      # Only snapshot divs have data-start attribute
      snapshot_divs=re.findall(r'<div data-start="([\d.]+)" data-duration="([\d.]+)"',html)
      durations=[float(d) for _,d in snapshot_divs]
      self.assertAlmostEqual(sum(durations),0.6,places=3)

class TDeterministic(unittest.TestCase):
  def test_same_output(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); (t/'a.svg').write_text(_FOX_SVG,encoding='utf-8')
      tl=_tl(dur=200,poses=['idle'])
      c=[_ch('a.svg',tl,[_fox('idle')])]
      r1=build_hyperframes_workspace(t,t/'o1',640,480,c)
      r2=build_hyperframes_workspace(t,t/'o2',640,480,copy.deepcopy(c))
      h1=(t/'o1'/f'compositions/{r1["composition_id"]}.html').read_text()
      h2=(t/'o2'/f'compositions/{r2["composition_id"]}.html').read_text()
      self.assertEqual(h1,h2)

class TImmutability(unittest.TestCase):
  def test_input_not_mutated(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); (t/'a.svg').write_text(_FOX_SVG,encoding='utf-8')
      tl=_tl(dur=200,poses=['idle'])
      c=[_ch('a.svg',tl,[_fox('idle')])]
      cc=copy.deepcopy(c)
      build_hyperframes_workspace(t,t/'o',640,480,c)
      self.assertEqual(c,cc)

class TPathSafety(unittest.TestCase):
  def test_nonexistent_asset_root(self):
    with tempfile.TemporaryDirectory() as td:
      with self.assertRaises(HyperFramesHandoffError):
        build_hyperframes_workspace(Path(td)/'nope',Path(td)/'o',640,480,[])

  def test_no_external_urls_in_index(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); (t/'a.svg').write_text(_FOX_SVG,encoding='utf-8')
      tl=_tl(dur=100,poses=['idle'])
      r=build_hyperframes_workspace(t,t/'o',640,480,
        [_ch('a.svg',tl,[_fox('idle')])])
      idx=(Path(r['workspace_path'])/'index.html').read_text(encoding='utf-8')
      self.assertNotIn('http',idx)
      self.assertNotIn('cdn',idx)

  def test_no_external_urls_in_composition(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); (t/'a.svg').write_text(_FOX_SVG,encoding='utf-8')
      tl=_tl(dur=100,poses=['idle'])
      r=build_hyperframes_workspace(t,t/'o',640,480,
        [_ch('a.svg',tl,[_fox('idle')])])
      comp=(Path(r['workspace_path'])/'compositions'/
            f'{r["composition_id"]}.html').read_text(encoding='utf-8')
      # Remove SVG namespace declarations before checking for external URLs
      import re
      stripped=re.sub(r'\s*xmlns(?::\w+)?="[^"]*"','',comp)
      self.assertNotIn('http://',stripped)
      self.assertNotIn('https://',stripped)
      self.assertNotIn('cdn',stripped.lower())
      self.assertNotIn('<script',comp)

class TWorkspaceStructure(unittest.TestCase):
  def test_files_created(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); (t/'a.svg').write_text(_FOX_SVG,encoding='utf-8')
      tl=_tl(dur=100,poses=['idle'])
      r=build_hyperframes_workspace(t,t/'o',640,480,
        [_ch('a.svg',tl,[_fox('idle')])])
      o=Path(r['workspace_path'])
      self.assertTrue((o/'index.html').is_file())
      self.assertTrue((o/'styles.css').is_file())
      self.assertTrue((o/'hyperframes.json').is_file())
      self.assertTrue((o/'DESIGN.md').is_file())
      self.assertTrue((o/'compositions'/f'{r["composition_id"]}.html').is_file())
      self.assertTrue((o/'assets').is_dir())

  def test_hyperframes_json_valid(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); (t/'a.svg').write_text(_FOX_SVG,encoding='utf-8')
      tl=_tl(dur=100,poses=['idle'])
      r=build_hyperframes_workspace(t,t/'o',640,480,
        [_ch('a.svg',tl,[_fox('idle')])])
      hf=json.loads((Path(r['workspace_path'])/'hyperframes.json').read_text())
      self.assertIn('paths',hf)
      self.assertIn('blocks',hf['paths'])
      self.assertNotIn('registry',hf)

  def test_snapshot_count(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); (t/'a.svg').write_text(_FOX_SVG,encoding='utf-8')
      tl=_tl(dur=600,poses=['idle','talk'])
      r=build_hyperframes_workspace(t,t/'o',640,480,
        [_ch('a.svg',tl,[_fox('idle'),_fox('talk')])])
      self.assertGreaterEqual(r['snapshot_count'],2)
      self.assertEqual(r['snapshot_count'],r['interval_count'])

class TSvgRendererIntegration(unittest.TestCase):
  def test_svg_renders_in_composition(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td); (t/'a.svg').write_text(_FOX_SVG,encoding='utf-8')
      tl=_tl(dur=100,poses=['idle'])
      r=build_hyperframes_workspace(t,t/'o',640,480,
        [_ch('a.svg',tl,[_fox('idle')])])
      comp=(Path(r['workspace_path'])/'compositions'/
            f'{r["composition_id"]}.html').read_text(encoding='utf-8')
      self.assertIn('data-character-instance',comp)
      self.assertIn('data-part',comp)
      self.assertIn('data-viseme',comp)

  def test_two_characters_in_scene(self):
    with tempfile.TemporaryDirectory() as td:
      t=Path(td)
      (t/'f.svg').write_text(_FOX_SVG,encoding='utf-8')
      (t/'l.svg').write_text(_LION_SVG,encoding='utf-8')
      tf=_tl(dur=200,poses=['idle'])
      tl=_tl(rig='sea_lion_cartoon',dur=200,poses=['idle'])
      r=build_hyperframes_workspace(t,t/'o',640,480,[
        _ch('f.svg',tf,[_fox('idle')]),
        _ch('l.svg',tl,[_lion('idle')],inst='leva')])
      comp=(Path(r['workspace_path'])/'compositions'/
            f'{r["composition_id"]}.html').read_text(encoding='utf-8')
      self.assertIn('makar',comp)
      self.assertIn('leva',comp)

class TBoundaryEdgeCases(unittest.TestCase):
  def test_many_boundaries(self):
    segs=[{'start_ms':i*100,'end_ms':(i+1)*100,'pose':'idle','viseme':'REST'}
          for i in range(5)]
    tl={'version':'1.0','rig_profile':'fox_cartoon','duration_ms':500,'segments':segs}
    b,d=_collect_boundaries([_ch('f.svg',tl,[_fox('idle')])])
    self.assertEqual(d,500)
    self.assertEqual(len(b),6)

if __name__=='__main__': unittest.main()