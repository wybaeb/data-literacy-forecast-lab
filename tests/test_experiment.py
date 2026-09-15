import json,subprocess,os,math
from pathlib import Path
from scipy.stats import norm
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
p={'traffic':200,'lag':7,'horizon':14,'sigma':500,'mde':100,'power':80,'effect':100,'seed':91524}
script="""const M=require('./experiment-model.js');const p=JSON.parse(process.argv[1]);const m=M.simulate(p);console.log(JSON.stringify({plan:m.plan,rows:m.rows,early:m.at(21),first:m.at(22),last:m.at(m.plan.finish),same:M.simulate(p).rows,high:M.plan({...p,power:90}),small:M.plan({...p,mde:50})}));"""
d=json.loads(subprocess.check_output(['node','-e',script,json.dumps(p)],cwd=root));n=math.ceil(2*(norm.ppf(.975)+norm.ppf(.8))**2*500**2/100**2)
assert d['plan']['n']==n==393 and d['plan']['finish']==25
assert d['early']['n']==0 and d['first']['n']==100 and d['last']['n']==n and d['last']['ready']
assert d['rows']==d['same'] and d['high']['n']>n and d['small']['n']>=4*n-3
last=d['last'];assert abs((last['high']-last['low'])/2-norm.ppf(.975)*500*math.sqrt(2/n))<1e-8
assert all(x['n']<=x['active']<=x['enrolled']<=n for x in d['rows'])
base=os.environ.get('LAB_BASE','http://127.0.0.1:8841/')
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1080});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 for name in ['index.html','harmonics.html','clusters.html','distributions.html','experiment.html']:
  page.goto(base+name);assert page.locator('.lab-nav a').count()==5;assert page.locator('.lab-nav [aria-current=page]').get_attribute('href')==name
 page.wait_for_function('window.experimentState');assert page.locator('#finish').inner_text()=='день 41'
 def val(id,v):page.locator('#'+id).evaluate('(e,v)=>{e.value=v;e.dispatchEvent(new Event("input",{bubbles:true}));}',str(v))
 val('day',21);assert 'Ещё нет' in page.locator('#difference').inner_text();assert page.locator('#chart polygon').count()==0
 val('day',22);assert page.locator('#chart polygon').count()==2;assert not page.evaluate('experimentState.current.ready')
 val('day',41);assert page.evaluate('experimentState.current.ready')
 old=page.evaluate('experimentState.current.delta');page.locator('#rerun').click();assert page.evaluate('experimentState.current.delta')!=old
 val('traffic',100);assert page.locator('#finish').inner_text()=='день 29'
 val('horizon',28);assert page.locator('#finish').inner_text()=='день 43'
 page.locator('#effect').select_option('0');assert page.evaluate('experimentState.params.effect')==0
 page.locator('#play').click();page.wait_for_timeout(350);assert page.evaluate('experimentState.current.day')>0;page.locator('#play').click()
 page.goto(base+'experiment.html#method');assert page.locator('#method').get_attribute('open') is not None
 val('day',41);page.screenshot(path='/tmp/experiment-desktop.png',full_page=True)
 page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.screenshot(path='/tmp/experiment-mobile.png',full_page=True)
 assert not errors,errors;b.close()
print(json.dumps({'math':'passed','sample_per_arm':n,'planned_finish':25,'maturation':'passed','determinism':'passed','power_and_mde':'passed','navigation_five_pages':'passed','controls_and_animation':'passed','mobile_overflow':False,'console_errors':errors},indent=2))
