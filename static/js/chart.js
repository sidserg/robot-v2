var _last=null;
var REQ_ID=0;
var CUR_TICKER="";
var CUR_TF="D1";
function fitCanvas(){
  var cv=document.getElementById("cv");
  var w=cv.parentElement.clientWidth-16;
  var h=cv.parentElement.clientHeight-16;
  if(w<200)w=200;
  if(h<200)h=200;
  cv.width=w; cv.height=h;
}
async function load(t){
  CUR_TICKER=t;
  var myid=++REQ_ID;
  var r=await fetch("/api?ticker="+t+"&tf="+CUR_TF);
  var d=await r.json();
  if(myid!==REQ_ID)return;
  draw(d);
}
var MARKERS=[];
function draw(d){
  _last=d;MARKERS=[];
  fitCanvas();
  var cv=document.getElementById("cv");
  var ctx=cv.getContext("2d");
  var W=cv.width,H=cv.height;
  ctx.clearRect(0,0,W,H);
  var cds=d.candles||[],trs=d.trades||[];
  if(!cds.length){ctx.fillStyle="#888";ctx.font="20px sans-serif";ctx.fillText("no data",W/2-40,H/2);return;}
  var PL=70,PR=30,PT=40,PB=50;
  var iw=W-PL-PR,ih=H-PT-PB;
  var closes=cds.map(function(c){return c[4];});
  var ymin=Math.min.apply(null,cds.map(function(c){return c[3];}));
  var ymax=Math.max.apply(null,cds.map(function(c){return c[2];}));
  trs.forEach(function(t){var v=Number(t[5]);if(v<ymin)ymin=v;if(v>ymax)ymax=v;});
  if(ymax<=ymin)ymax=ymin+1;
  var pad=(ymax-ymin)*0.05;ymin-=pad;ymax+=pad;
  var n=cds.length;
  function X(i){return PL+i*iw/Math.max(1,n-1);}
  function Y(v){return PT+ih-(v-ymin)/(ymax-ymin)*ih;}  ctx.strokeStyle="#2e3348";ctx.fillStyle="#8892a0";ctx.font="12px sans-serif";
  for(var k=0;k<=4;k++){var v=ymin+(ymax-ymin)*k/4;var yy=Y(v);ctx.beginPath();ctx.moveTo(PL,yy);ctx.lineTo(PL+iw,yy);ctx.stroke();ctx.fillText(v.toFixed(2),6,yy+4);}
  ctx.strokeStyle="#7ab8f5";ctx.lineWidth=2;
  ctx.beginPath();for(var i=0;i<n;i++){var xx=X(i);var yy=Y(closes[i]);if(i===0)ctx.moveTo(xx,yy);else ctx.lineTo(xx,yy);}ctx.stroke();
  var tidx={};for(var i2=0;i2<n;i2++){var kk=cds[i2][0].slice(0,16);tidx[kk]=i2;}
  function t2s(t){var ss=String(t).trim();if(ss.length<1)return 0;ss=ss.replace(" ","T");if(ss.length<=19)ss+="Z";var ms=new Date(ss).getTime();if(isNaN(ms))return 0;return Math.floor(ms/1000);}
  var cand_epoch=[];for(var ci=0;ci<n;ci++){cand_epoch.push(t2s(cds[ci][0]));}
  var usedidx={};
  for(var j=0;j<trs.length;j++){
    var t=trs[j];var _ts=t2s(t[2]);if(!_ts)continue;
    var _tfmap={M1:60,M5:300,M15:900,H1:3600,D1:86400};var _tfs=_tfmap[CUR_TF]||86400;var ii=-1;for(var bi=0;bi<n;bi++){var _s=cand_epoch[bi];if(_ts>=_s&&_ts<_s+_tfs){ii=bi;break;}}
    if(ii<0)continue;
    var _cnt=usedidx[ii]||0;usedidx[ii]=_cnt+1;
    var _dx=(_cnt%5)*6-12;
    var xx2=X(ii)+_dx;var yy2=Y(t[5]);

    var isBuy=t[3].toUpperCase().indexOf("BUY")>=0;
    MARKERS.push({x:xx2,y:yy2,t:t,isBuy:isBuy});
    ctx.fillStyle=isBuy?"#22c55e":"#ef4444";
    ctx.beginPath();ctx.arc(xx2,yy2,8,0,Math.PI*2);ctx.fill();ctx.strokeStyle="#fff";ctx.lineWidth=1.5;ctx.stroke();
    ctx.fillStyle="#fff";ctx.font="bold 9px sans-serif";ctx.textAlign="center";ctx.fillText(isBuy?"B":"S",xx2,yy2+(isBuy?-12:18));
  }
  var info=document.getElementById("info");
  var last=closes[closes.length-1],first=closes[0];
  var chg=((last-first)/first*100).toFixed(2);
  info.innerHTML="<b>"+d.ticker+"</b> px="+last.toFixed(2)+" chg="+chg+"% trades="+trs.length;
}function _ttShow(ev){var cv=document.getElementById("cv");var r=cv.getBoundingClientRect();var mx=ev.clientX-r.left,my=ev.clientY-r.top;var hit=null;for(var i=0;i<MARKERS.length;i++){var m=MARKERS[i];var dx=mx-m.x,dy=my-m.y;if(dx*dx+dy*dy<=100){hit=m;break;}}var tt=document.getElementById("tt");if(!tt){tt=document.createElement("div");tt.id="tt";tt.style.cssText="position:fixed;background:#1a1f2e;color:#e6edf3;border:1px solid #30363d;border-radius:6px;padding:6px 10px;font:12px monospace;pointer-events:none;z-index:9999;display:none;box-shadow:0 4px 12px rgba(0,0,0,.5)";document.body.appendChild(tt);}if(hit){var t=hit.t;var kind=(t[3]||"").toUpperCase();var col=hit.isBuy?"#22c55e":"#ef4444";tt.innerHTML="<b style=color:"+col+">"+kind+"</b> "+Number(t[5]).toFixed(2)+" ₽ <span style=color:#8892a0>x"+t[4]+"</span><br><span style=color:#8892a0>"+t[2]+"</span>";tt.style.display="block";tt.style.left=(ev.clientX+12)+"px";tt.style.top=(ev.clientY+12)+"px";cv.style.cursor="pointer";}else{tt.style.display="none";cv.style.cursor="default";}}
window.addEventListener("resize",function(){if(_last)draw(_last);});
document.addEventListener("mousemove",_ttShow);
function initTabs(robots,cur){
  var tb=document.getElementById("tabs");tb.innerHTML="";
  robots.forEach(function(r){
    var a=document.createElement("a");a.textContent=r.ticker;a.href="#";
    if(r.ticker===cur)a.className="on";
    a.onclick=function(e){e.preventDefault();load(r.ticker);Array.prototype.forEach.call(tb.children,function(c){c.className="";});a.className="on";};
    tb.appendChild(a);
  });
}
function initTfs(){
  var tfs=["M1","M5","M15","H1","D1"];
  var box=document.getElementById("tfs");box.innerHTML="";
  tfs.forEach(function(t){
    var b=document.createElement("button");b.textContent=t;
    if(t===CUR_TF)b.className="on";
    b.onclick=function(){CUR_TF=t;Array.prototype.forEach.call(box.children,function(c){c.className="";});b.className="on";load(CUR_TICKER);};
    box.appendChild(b);
  });
}
async function boot(){
  var r=await fetch("/api?robots=1");
  var d=await r.json();
  var cur=location.hash.slice(1)||(d.robots[0]&&d.robots[0].ticker)||"";
  initTabs(d.robots,cur);
  initTfs();
  load(cur);
  setInterval(function(){if(CUR_TICKER)load(CUR_TICKER);},15000);
}
boot();