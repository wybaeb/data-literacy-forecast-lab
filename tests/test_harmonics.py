"""Numerical reference, no-future-leakage and browser interactions for the new page."""
import json,subprocess,os
from pathlib import Path
import numpy as np
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];data=json.loads((root/'data.json').read_text())['datasets']
js="""const H=require('./harmonics-model.js'),D=require('./data.json').datasets,out=[];
for(const key of ['real','case'])for(const cut of [730,1800,2465]){const parts=H.components(key),selected=[];let previous=Infinity;
for(const p of [null,...parts]){if(p)selected.push(p.id);const r=H.fit(D[key],cut,parts,selected);if(r.trainRMSE>previous+1e-7)throw Error('Nested training error grew');previous=r.trainRMSE;}
const r=H.fit(D[key],cut,parts,selected),before=r.prediction.slice(cut,cut+90);const changed={...D[key],y:D[key].y.map((y,i)=>i>=cut?y+100000:y)};const after=H.fit(changed,cut,parts,selected).prediction.slice(cut,cut+90);if(JSON.stringify(before)!==JSON.stringify(after))throw Error('Future leak');out.push({key,cut,prediction:r.prediction,rank:r.rank});}console.log(JSON.stringify(out));"""
r=json.loads(subprocess.check_output(['node','-e',js],cwd=root));report=[]
for item in r:
 d=data[item['key']];X=np.array(d['features']);y=np.array(d['y']);cut=item['cut'];beta=np.linalg.lstsq(X[:cut],y[:cut],rcond=None)[0];err=float(np.max(np.abs(X@beta-np.array(item['prediction']))));assert err<1e-6,err;report.append({'dataset':item['key'],'cut':cut,'max_numpy_difference':err,'no_future_leakage':True})
url=os.environ.get('LAB_URL','http://127.0.0.1:8834/harmonics.html')
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1050});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url);page.wait_for_function('window.harmonicsState');assert page.evaluate('harmonicsState.rank')==1
 baseline=page.evaluate('harmonicsState.trainRMSE');page.check('#year1');assert page.evaluate('harmonicsState.trainRMSE')<=baseline;page.click('[data-preset=all]');assert page.evaluate('harmonicsState.rank')==26;page.select_option('#dataset','case');page.check('#bend');assert page.evaluate('harmonicsState.rank')==27
 page.fill('#cut','2020-12-31');page.locator('#cut').dispatch_event('change');assert page.evaluate('harmonicsState.discarded.length')>0
 page.fill('#cut','2025-09-30');page.locator('#cut').dispatch_event('change');page.click('[data-preset=all]');state=page.evaluate('harmonicsState.prediction');page.select_option('#window','90');assert page.evaluate('harmonicsState.prediction')==state
 page.locator('#contributionBox summary').click();assert page.locator('#partsPlot polyline').count()>0
 page.select_option('#window','365');page.select_option('#dataset','real');page.click('[data-preset=all]');page.screenshot(path='/tmp/harmonics-desktop.png',full_page=True)
 page.goto(url+'#method');page.wait_for_function('window.harmonicsState');assert page.locator('#method').get_attribute('open') is not None
 page.set_viewport_size({'width':390,'height':844});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth');page.check('#year1');page.screenshot(path='/tmp/harmonics-mobile.png',full_page=True)
 assert not errors,errors;browser.close()
print(json.dumps({'numerical_checks':report,'browser':'passed','console_errors':errors},ensure_ascii=False,indent=2))
