function fitCanvas(){
  var cv=document.getElementById("cv");
  var w=cv.parentElement.clientWidth-16;
  var h=cv.parentElement.clientHeight-16;
  if(w<200)w=200;
  if(h<200)h=200;
  cv.width=w; cv.height=h;
}
window.addEventListener("resize",function(){fitCanvas();if(window._last)draw(window._last);});
var _origDraw=draw;
draw=function(d){window._last=d;fitCanvas();_origDraw(d);};