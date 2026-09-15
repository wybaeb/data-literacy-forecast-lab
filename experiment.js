'use strict';
const $=id=>document.getElementById(id),fmt=n=>n.toLocaleString('ru-RU',{maximumFractionDigits:1});
let seed=91524,model,params,timer=null;
const inputs=['traffic','lag','horizon','sigma','mde','power'];
const text=(x,y,t,fill='#69717e',anchor='start',size=16)=>`<text x="${x}" y="${y}" fill="${fill}" text-anchor="${anchor}" font-family="Arial,sans-serif" font-size="${size}">${t}</text>`;
function rebuild(){
 stop();params=Object.fromEntries(inputs.map(id=>[id,+$(id).value]));params.effect=+$('effect').value*params.mde;params.seed=seed;model=ExperimentModel.simulate(params);window.experimentState={params,model};
 inputs.forEach(id=>{if($(id+'Out'))$(id+'Out').textContent=fmt(params[id]);});
 $('target').textContent=fmt(model.plan.n);$('enrollment').textContent=`день ${model.plan.enrollment}`;$('finish').textContent=`день ${model.plan.finish}`;
 $('formula').textContent=`${model.plan.enrollment} дн. набора + ${params.lag} дн. до активации + ${params.horizon} дн. наблюдения = ${model.plan.finish} дней. План фиксируется до просмотра результатов.`;
 $('day').max=model.plan.finish;$('day').value=model.plan.finish;draw();
}
function draw(){
 const day=+$('day').value,q=model.plan,s=model.at(day);window.experimentState.current=s;$('dayOut').textContent=day;
 $('enrolled').textContent=fmt(s.enrolled*2);$('mature').textContent=fmt(s.n*2);$('difference').textContent=s.n?`${fmt(s.delta)} [${fmt(s.low)}; ${fmt(s.high)}]`:'Ещё нет данных';
 $('phase').textContent=s.ready?'Плановый срок достигнут: все участники завершили одинаковый горизонт.':s.n?`Идёт накопление зрелых результатов: ${s.n} из ${q.n} на группу. Это промежуточный просмотр, решение ещё не принимаем.`:s.enrolled<q.n?'Набираем участников. Полный результат пока не созрел.':'Набор завершён. Ждём первые полностью созревшие результаты.';
 $('verdict').textContent=!s.ready?'Даже если отдельные интервалы уже разошлись, сохраняем запланированный срок анализа.':s.low>0?'Плановый анализ: интервал разницы выше нуля — данные поддерживают преимущество B на выбранном горизонте.':s.high<0?'Плановый анализ: интервал разницы ниже нуля — данные поддерживают преимущество A на выбранном горизонте.':'Плановый анализ: интервал разницы включает ноль. Данных недостаточно для вывода о различии; это не доказательство равенства.';
 const px=d=>70+d/q.finish*860;
 let flow='';[[0,q.enrollment,'#2274b8','Набор'],[q.enrollment,q.finish,'#b9dcd7','Ожидание последних результатов']].forEach(([a,b,c,label],i)=>{flow+=`<rect x="${px(a)}" y="${40+i*32}" width="${Math.max(1,px(b)-px(a))}" height="20" rx="4" fill="${c}"/>`;});
 flow+=text(70,20,'Набор → активация → полный горизонт метрики');flow+=text(70,113,`Набор: день ${q.enrollment} · Анализ: день ${q.finish}`);flow+=`<line x1="${px(day)}" x2="${px(day)}" y1="30" y2="92" stroke="#20232b" stroke-width="2"/>`+text(px(day),145,`День ${day}`,'#20232b',day>q.finish*.85?'end':'start');$('flow').innerHTML=flow;
 const all=model.rows.filter(r=>r.n),rows=all.filter(r=>r.day<=day);
 if(s.n && !rows.some(r=>r.day===day))rows.push(s);
 const lo=Math.floor(Math.min(0,...all.map(r=>Math.min(r.a,r.b)-r.h))/250)*250,hi=Math.ceil(Math.max(1500,...all.map(r=>Math.max(r.a,r.b)+r.h))/250)*250;
 const py=v=>325-(v-lo)/(hi-lo)*270;let svg='';
 for(let i=0;i<5;i++){const y=lo+(hi-lo)*i/4;svg+=`<line x1="70" x2="930" y1="${py(y)}" y2="${py(y)}" stroke="#e1e5e2"/>`+text(60,py(y)+5,fmt(y),'#69717e','end',14);}
 for(let i=0;i<5;i++){const d=Math.round(q.finish*i/4);svg+=text(px(d),353,d,'#69717e','middle');}
 svg+=text(930,385,'День с начала набора','#69717e','end');
 for(const [key,c] of [['a','#ff5533'],['b','#00868c']]){
  if(!rows.length)continue;
  const points=rows.map(r=>`${px(r.day)},${py(r[key]+r.h)}`).concat([...rows].reverse().map(r=>`${px(r.day)},${py(r[key]-r.h)}`));svg+=`<polygon points="${points.join(' ')}" fill="${c}" opacity=".15"/>`;
  svg+=`<polyline points="${rows.map(r=>`${px(r.day)},${py(r[key])}`).join(' ')}" fill="none" stroke="${c}" stroke-width="3"/>`;
  if(rows.length===1)svg+=`<line x1="${px(rows[0].day)}" x2="${px(rows[0].day)}" y1="${py(rows[0][key]-rows[0].h)}" y2="${py(rows[0][key]+rows[0].h)}" stroke="${c}" opacity=".4"/>`;
 }
 svg+=`<line x1="${px(q.finish)}" x2="${px(q.finish)}" y1="35" y2="325" stroke="#69717e" stroke-dasharray="6 5"/>`+text(930,25,'Плановый анализ','#69717e','end');
 if(!rows.length)svg+=text(500,180,'Ждём результаты полного горизонта','#69717e','middle',22);
 $('chart').innerHTML=svg;
}
function stop(){if(timer)clearInterval(timer);timer=null;$('play').textContent='▶ Показать по дням';}
inputs.forEach(id=>$(id).addEventListener('input',rebuild));$('effect').addEventListener('change',rebuild);$('rerun').onclick=()=>{seed+=17;rebuild();};$('day').addEventListener('input',()=>{stop();draw();});$('play').onclick=()=>{if(timer){stop();return;}$('day').value=0;draw();$('play').textContent='Ⅱ Пауза';timer=setInterval(()=>{$('day').value=Math.min(model.plan.finish,+$('day').value+Math.max(1,Math.ceil(model.plan.finish/120)));draw();if(+$('day').value>=model.plan.finish)stop();},140);};
if(location.hash==='#method')$('method').open=true;window.addEventListener('hashchange',()=>{if(location.hash==='#method')$('method').open=true;});rebuild();
