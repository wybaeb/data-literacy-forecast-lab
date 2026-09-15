import json,subprocess,os
from pathlib import Path
import numpy as np
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
js="""const M=require('./distributions-model.js');const fixtures=[[],[5],[0,100],[1,2,2,3,90],M.preset('normal'),M.preset('spikes'),M.preset('bimodal')];console.log(JSON.stringify(fixtures.map(values=>({values,stats:M.statistics(values),hist:M.histogram(values),rebuilt:M.fromHistogram(M.histogram(values))}))));"""
data=json.loads(subprocess.check_output(['node','-e',js],cwd=root))
for d in data:
 a=np.array(d['values']);s=d['stats'];assert s['n']==len(a) and sum(d['hist'])==len(a)
 if len(a):assert np.allclose([s['mean'],s['median'],s['p90']],[a.mean(),np.median(a),np.quantile(a,.9)])
 else:assert s['mean'] is None and s['median'] is None and s['p90'] is None
 hist=np.histogram(d['rebuilt'],bins=np.linspace(0,100,41))[0];assert hist.tolist()==d['hist']
base=os.environ.get('LAB_BASE','http://127.0.0.1:8841/')
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1150});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base+'distributions.html');page.wait_for_function('window.distributionState')
 def state():return page.evaluate('distributionState')
 def verify():
  d=state();v=np.array(d['values']);assert sum(d['counts'])==len(v);assert np.histogram(v,bins=np.linspace(0,100,41))[0].tolist()==d['counts']
  if len(v):assert np.allclose([d['stats']['mean'],d['stats']['median'],d['stats']['p90']],[v.mean(),np.median(v),np.quantile(v,.9)])
  return d
 for name in ['spikes','bimodal','normal']:
  page.locator(f'[data-preset={name}]').click();verify();assert page.locator(f'[data-preset={name}]').get_attribute('aria-pressed')=='true'
 # Real pointer gesture, including intermediate update before release.
 before=state()['values'];r=page.locator('#series').bounding_box();x0=r['x']+r['width']*.12;y=r['y']+r['height']*.2;page.mouse.move(x0,y);page.mouse.down();page.mouse.move(r['x']+r['width']*.55,r['y']+r['height']*.35,steps=12);page.wait_for_timeout(100);assert state()['values']!=before;verify();page.mouse.up();page.locator('#undo').click();assert state()['values']==before
 # Draw histogram and ensure its integer frequencies round-trip exactly.
 r=page.locator('#histogram').bounding_box();page.mouse.move(r['x']+r['width']*.2,r['y']+r['height']*.6);page.mouse.down();page.mouse.move(r['x']+r['width']*.62,r['y']+r['height']*.35,steps=14);page.wait_for_timeout(100);assert state()['grouped'];verify();page.mouse.up();assert state()['stats']['n']!=160
 # Numeric edits and empty/singleton; true endpoints included in last bin.
 page.locator('#clear').click();verify();assert page.locator('#mean').inner_text()=='—';page.locator('#pointValue').fill('100');page.locator('#applyPoint').click();assert state()['values']==[100];verify()
 page.locator('#clear').click();page.locator('#binIndex').fill('40');page.locator('#binCount').fill('7');page.locator('#applyBin').click();assert state()['values']==[98.75]*7;verify()
 page.locator('#binCount').fill('2001');page.locator('#applyBin').click();assert state()['stats']['n']==7
 page.locator('[data-preset=bimodal]').click();page.screenshot(path='/tmp/distributions-desktop.png',full_page=True)
 with page.expect_download() as download:page.locator('#download').click()
 path=download.value.path();rows=Path(path).read_text().splitlines();assert len(rows)==161
 # All four pages have the permanent nav and appropriate active link.
 for name in ['index.html','harmonics.html','clusters.html','distributions.html']:
  page.goto(base+name);page.wait_for_selector('.lab-nav');assert page.locator('.lab-nav a').count()==4;assert page.locator('.lab-nav [aria-current=page]').get_attribute('href')==name
 page.goto(base+'distributions.html#method');page.wait_for_function('window.distributionState');assert page.locator('#method').get_attribute('open') is not None
 page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path='/tmp/distributions-mobile.png',full_page=True)
 # True touch gestures and cancellation on an emulated touch device.
 touch=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True);tp=touch.new_page();tp.on('pageerror',lambda e:errors.append(str(e)));tp.goto(base+'distributions.html');tp.wait_for_function('window.distributionState');tp.locator('#series').scroll_into_view_if_needed();box=tp.locator('#series').bounding_box();cdp=touch.new_cdp_session(tp);before=tp.evaluate('distributionState.values');x=box['x']+box['width']*.3;y=box['y']+box['height']*.3
 cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]});cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x+60,'y':y+20}]});tp.wait_for_timeout(100);assert tp.evaluate('distributionState.values')!=before;cdp.send('Input.dispatchTouchEvent',{'type':'touchCancel','touchPoints':[]});tp.wait_for_timeout(100);assert tp.evaluate('distributionState.values')==before
 touch.close();assert not errors,errors;browser.close()
print(json.dumps({'math_fixtures':len(data),'pointer_series':'passed','pointer_histogram':'passed','live_updates':'passed','undo':'passed','empty_singleton_endpoints':'passed','numeric_controls':'passed','csv':'passed','navigation_four_pages':'passed','mobile_overflow':False,'touch_and_cancel':'passed','console_errors':errors},ensure_ascii=False,indent=2))
