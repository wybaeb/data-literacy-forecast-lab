import json,subprocess,os
from pathlib import Path
import numpy as np
from sklearn.metrics import silhouette_score
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
m=json.loads(subprocess.check_output(['node','-e',"console.log(JSON.stringify(require('./clusters-model.js').calculate(require('./clusters-data.json').points)))"],cwd=root));Z=np.array(m['Z']);last=float('inf');checks=[]
for r in m['results']:
 labels=np.array(r['labels']);c=np.array(r['centers']);assert len(set(labels))==r['k'];assert r['inertia']<=last+1e-8;last=r['inertia'];assert np.allclose(c,np.array([Z[labels==j].mean(axis=0) for j in range(r['k'])]),atol=1e-8)
 assert np.array_equal(np.argmin(((Z[:,None,:]-c[None,:,:])**2).sum(axis=2),axis=1),labels)
 error=abs(float(((Z-c[labels])**2).sum())-r['inertia']);assert error<1e-8
 if r['k']>1:assert abs(silhouette_score(Z,labels)-r['silhouette'])<1e-10
 checks.append({'k':r['k'],'inertia':r['inertia'],'silhouette':r['silhouette'],'centers_and_nearest_assignments':True})
assert max(m['results'][1:],key=lambda x:x['silhouette'])['k']==2
base=os.environ.get('LAB_BASE','http://127.0.0.1:8834/')
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox']);page=b.new_page(viewport={'width':1440,'height':1100});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base+'clusters.html');page.wait_for_function('window.clusterState');points=page.evaluate('clusterState.points');positions=page.locator('#scatter .observation').evaluate_all('(els)=>els.map(e=>[e.getAttribute("cx"),e.getAttribute("cy")])')
 for k in range(1,9):
  page.locator('#k').fill(str(k));page.locator('#k').dispatch_event('input');assert page.locator('.centroid').count()==k;assert page.evaluate('clusterState.points')==points;assert page.locator('#scatter .observation').evaluate_all('(els)=>els.map(e=>[e.getAttribute("cx"),e.getAttribute("cy")])')==positions
 page.locator('#k').fill('2');page.locator('#k').dispatch_event('input');page.screenshot(path='/tmp/clusters-desktop.png',full_page=True)
 page.locator('.lab-nav a[href="harmonics.html"]').click();page.wait_for_function('window.harmonicsState');page.check('#year1');page.locator('.lab-nav a[href="index.html"]').click();page.wait_for_function('window.labState');assert len(page.evaluate('labState.predictions'))==4
 page.locator('.lab-nav a[href="clusters.html"]').click();page.wait_for_function('window.clusterState');assert page.locator('.lab-nav [aria-current="page"]').get_attribute('href')=='clusters.html'
 page.goto(base+'clusters.html#method');page.wait_for_function('window.clusterState');assert page.locator('#method').get_attribute('open') is not None
 page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.locator('#method summary').click();page.locator('#k').fill('2');page.locator('#k').dispatch_event('input');page.screenshot(path='/tmp/clusters-mobile.png',full_page=True)
 assert not errors,errors;b.close()
print(json.dumps({'math':checks,'browser':'passed','navigation_three_pages':'passed','stationary_points':'passed','console_errors':errors},ensure_ascii=False,indent=2))
