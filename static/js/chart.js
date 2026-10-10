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
function draw(d){
  _last=d;
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
  function t2s(t){var ss=String(t);if(ss.indexOf("T")>=0){return Math.floor(new Date(ss).getTime()/1000);}if(ss.indexOf(" ")>=0){return Math.floor(new Date(ss.replace(" ","T")+"Z").getTime()/1000);}return 0;}
  var cand_epoch=[];for(var ci=0;ci<n;ci++){cand_epoch.push(t2s(cds[ci][0]));}
  var usedidx={};
  for(var j=0;j<trs.length;j++){
    var t=trs[j];var _ts=t2s(t[2]);if(!_ts)continue;
    var best=-1,bestd=1e18;for(var bi=0;bi<n;bi++){var dd2=Math.abs(cand_epoch[bi]-_ts);if(dd2<bestd){bestd=dd2;best=bi;}}
    if(best<0)continue;
    if(bestd>3600*6)continue;
    var ii=best;
    var _cnt=usedidx[ii]||0;usedidx[ii]=_cnt+1;
    var _dx=(_cnt%5)*6-12;
    var xx2=X(ii)+_dx;var yy2=Y(t[5]);

    var isBuy=t[3].toUpperCase().indexOf("BUY")>=0;
    ctx.fillStyle=isBuy?"#22c55e":"#ef4444";
    ctx.beginPath();
    if(isBuy){ctx.moveTo(xx2,yy2-10);ctx.lineTo(xx2+7,yy2+6);ctx.lineTo(xx2-7,yy2+6);}
    else{ctx.moveTo(xx2,yy2+10);ctx.lineTo(xx2+7,yy2-6);ctx.lineTo(xx2-7,yy2-6);}
    ctx.closePath();ctx.fill();ctx.strokeStyle="#fff";ctx.lineWidth=1;ctx.stroke();
    ctx.fillStyle="#fff";ctx.font="bold 9px sans-serif";ctx.textAlign="center";ctx.fillText(isBuy?"B":"S",xx2,yy2+(isBuy?-12:18));
  }
  var info=document.getElementById("info");
  var last=closes[closes.length-1],first=closes[0];
  var chg=((last-first)/first*100).toFixed(2);
  info.innerHTML="<b>"+d.ticker+"</b> px="+last.toFixed(2)+" chg="+chg+"% trades="+trs.length;
}window.addEventListener("resize",function(){if(_last)draw(_last);});
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