/* Keep the expanded footprint stable while only the sticky header changes size. */
"use strict";
document.addEventListener("DOMContentLoaded", () => {
 const header=document.querySelector(".geometric-header"),shell=header?.closest(".header-scroll-shell");
 if(!header||!shell)return;
 let pending=0,compact=false;
 function update(){
  pending=0;
  const scroll=window.scrollY;
  const next=compact?scroll>24:scroll>80;
  if(next!==compact){
   compact=next;
   header.classList.toggle("is-compact",compact);
  }
 }
 function schedule(){if(!pending)pending=requestAnimationFrame(update);}
 function measure(){
  if(!compact&&!header.getAnimations().some(animation=>animation.playState==="running")){
   const height=header.getBoundingClientRect().height;
   shell.style.setProperty("--expanded-header-size",height+"px");
  }
 }
 const observer=new ResizeObserver(measure);observer.observe(header);
 header.addEventListener("transitionend",measure);
 window.addEventListener("scroll",schedule,{passive:true});
 window.addEventListener("resize",schedule,{passive:true});
 window.addEventListener("pageshow",schedule);
 measure();update();
 window.addEventListener("pagehide",event=>{
  if(event.persisted)return;
  observer.disconnect();
  header.removeEventListener("transitionend",measure);
  window.removeEventListener("scroll",schedule);
  window.removeEventListener("resize",schedule);
  window.removeEventListener("pageshow",schedule);
  if(pending)cancelAnimationFrame(pending);
 },{once:true});
});
