/* MUKIAI Blog — UI挙動（進捗バー / モバイルメニュー / 目次ハイライト） */
(function(){
  "use strict";

  /* モバイルメニュー */
  var burger=document.getElementById("burger");
  var mobile=document.getElementById("mobileMenu");
  if(burger&&mobile){
    burger.addEventListener("click",function(){
      mobile.classList.toggle("open");
      document.body.style.overflow=mobile.classList.contains("open")?"hidden":"";
    });
    mobile.querySelectorAll("a").forEach(function(a){
      a.addEventListener("click",function(){mobile.classList.remove("open");document.body.style.overflow="";});
    });
  }

  /* 読書進捗バー */
  var bar=document.getElementById("progress");
  var article=document.querySelector(".article-main");
  if(bar&&article){
    var onScroll=function(){
      var rect=article.getBoundingClientRect();
      var total=article.offsetHeight-window.innerHeight;
      var passed=Math.min(Math.max(-rect.top,0),Math.max(total,1));
      bar.style.width=(total>0?(passed/total*100):0)+"%";
    };
    window.addEventListener("scroll",onScroll,{passive:true});
    window.addEventListener("resize",onScroll);
    onScroll();
  }

  /* 目次：スクロール連動ハイライト */
  var tocLinks=Array.prototype.slice.call(document.querySelectorAll(".toc-list a"));
  if(tocLinks.length){
    var map={};
    var heads=tocLinks.map(function(a){
      var id=a.getAttribute("href").slice(1);
      var el=document.getElementById(id);
      if(el)map[id]=a;
      return el;
    }).filter(Boolean);

    if("IntersectionObserver" in window){
      var current=null;
      var io=new IntersectionObserver(function(entries){
        entries.forEach(function(e){
          if(e.isIntersecting){
            if(current)current.forEach(function(l){l.classList.remove("active");});
            var id=e.target.getAttribute("id");
            // 同じidが複数TOC(インライン+レール)にあるので全部点灯
            current=tocLinks.filter(function(l){return l.getAttribute("href")==="#"+id;});
            current.forEach(function(l){l.classList.add("active");});
          }
        });
      },{rootMargin:"-80px 0px -70% 0px",threshold:0});
      heads.forEach(function(h){io.observe(h);});
    }
  }
})();
