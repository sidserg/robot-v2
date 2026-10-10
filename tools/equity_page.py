# -*- coding: utf-8 -*-
"""equity_page.py - HTML strandica for /equity."""

HTML = '''<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8"><title>Equity</title><style>*{box-sizing:border-box}body{font-family:sans-serif;background:#0a0c10;color:#e6edf3;margin:0;padding:16px}h1{color:#7ab8f5;margin:0 0 12px 0}#tabs{margin-bottom:10px}#tabs button{background:#1a232d;color:#8892a0;border:1px solid #30363d;padding:6px 14px;margin-right:6px;border-radius:4px;cursor:pointer;font-size:13px}#tabs button.on{background:#243b57;color:#7ab8f5;border-color:#7ab8f5}#cv{background:#1a232d;border-radius:6px;width:100%;max-width:1100px}#info{margin-top:10px;color:#8892a0;font-family:monospace;font-size:13px}</style></head><body><h1>Equity Curve</h1><div id="tabs"></div><canvas id="cv"></canvas><div id="info">loading...</div><script>
var CUR_RID=0;
var ROBOTS=[];
function initTabs(){
fetch("/api/state").then(function(r){return r.json();}).then(function(d){
var tb=document.getElementById("tabs");
tb.innerHTML="";
var pos=d.positions||[];
var tickers={};
for(var i=0;i<pos.length;i++){tickers[pos[i].robot_id]=pos[i].ticker;}
for(var i=1;i<=6;i++){
var b=document.createElement("button");
b.textContent="R"+i+" "+(tickers[i]||"");
b.onclick=(function(rid){return function(){load(rid);};})(i);
tb.appendChild(b);
}
if(!CUR_RID&&pos.length>0){load(pos[0].robot_id);}
});
}
function load(rid){
CUR_RID=rid;
var tb=document.getElementById("tabs");
var bs=tb.getElementsByTagName("button");
for(var i=0;i<bs.length;i++){bs[i].className=(i+1===rid)?"on":"";}
fetch("/api/equity?rid="+rid+"&days=30").then(function(r){return r.json();}).then(draw);
}
function fitCanvas(){
var cv=document.getElementById("cv");
var w=cv.parentElement.clientWidth-40;
if(w<200)w=200;
cv.width=w; cv.height=400;
}
function draw(d){
fitCanvas();
var cv=document.getElementById("cv");
var ctx=cv.getContext("2d");
var W=cv.width,H=cv.height;
ctx.clearRect(0,0,W,H);
var rows=d.rows||[];
if(!rows.length){ctx.fillStyle="#888";ctx.font="20px sans-serif";ctx.fillText("no data yet",W/2-60,H/2);document.getElementById("info").textContent="Не данных трейдей еще (CUR_RID="+d.rid+")";return;}
var PL=70,PR=30,PT=30,PB=40;
var iw=W-PL-PR,ih=H-PT-PB;
var vals=rows.map(function(x){return Number(x.total||0);});
var ymin=Math.min.apply(null,vals);
var ymax=Math.max.apply(null,vals);
if(ymax<=ymin)ymax=ymin+1;
var pad=(ymax-ymin)*0.05;ymin-=pad;ymax+=pad;
var n=rows.length;
function X(i){return PL+i*iw/Math.max(1,n-1);}
function Y(v){return PT+ih-(v-ymin)/(ymax-ymin)*ih;}
ctx.strokeStyle="#2e3348";
ctx.fillStyle="#8892a0";
ctx.font="12px sans-serif";
ctx.textAlign="right";
for(var k=0;k<=4;k++){
var v=ymin+(ymax-ymin)*k/4;
var yy=Y(v);
ctx.beginPath();ctx.moveTo(PL,yy);ctx.lineTo(PL+iw,yy);ctx.stroke();
ctx.fillText(Math.round(v),PL-6,yy+4);
}
ctx.textAlign="left";
ctx.strokeStyle="#7ab8f5";
ctx.lineWidth=2;
ctx.beginPath();
for(var i=0;i<n;i++){
var xx=X(i);
var yy=Y(vals[i]);
if(i===0)ctx.moveTo(xx,yy);else ctx.lineTo(xx,yy);
}
ctx.stroke();
ctx.fillStyle="#7ab8f5";
ctx.beginPath();ctx.arc(X(n-1),Y(vals[n-1]),4,0,Math.PI2*1);ctx.fill();
last=vals[n-1];
first=vals[0];
delta=last-first;
sign=delta>=0?"+":"";
document.getElementById("info").textContent="R1"+d.rid+" points="+n+"  first="+Math.round(first)+"  last="+Math.round(last)+"  delta="+sign+Math.round(delta)+" RUB";
}
window.addEventListener("resize",function(){if(CUR_RID)load(CUR_RID);});
initTabs();
setInterval(function(){if(CUR_RID)load(CUR_RID);},30000);
</script></body></html>'''
