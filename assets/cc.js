/* ===== IZANAI / Claude Code 共通スクリプト ===== */
(function(){
  var header=document.getElementById('header'),floatcta=document.getElementById('floatcta');
  addEventListener('scroll',function(){var y=scrollY;if(header)header.classList.toggle('scrolled',y>40);if(floatcta)floatcta.classList.toggle('show',y>700);});
  var burger=document.getElementById('burger'),mm=document.getElementById('mobileMenu');
  if(burger&&mm){burger.addEventListener('click',function(){mm.classList.toggle('open');});mm.querySelectorAll('a').forEach(function(a){a.addEventListener('click',function(){mm.classList.remove('open');});});}
  function reveal(el){
    if(el.classList.contains('stagger')){
      Array.prototype.forEach.call(el.children,function(c,i){c.style.transitionDelay=(i*90)+'ms';c.classList.add('in');});
    }
    el.classList.add('in');
  }
  var rvItems=[].slice.call(document.querySelectorAll('.reveal,.rv,.stagger'));
  function rvSweep(){
    var vh=window.innerHeight||document.documentElement.clientHeight;
    for(var i=rvItems.length-1;i>=0;i--){
      var el=rvItems[i],r=el.getBoundingClientRect();
      if(r.top < vh*0.9 && r.bottom > 0){ reveal(el); rvItems.splice(i,1); }
    }
  }
  rvSweep();
  addEventListener('scroll',rvSweep,{passive:true});
  addEventListener('resize',rvSweep);
  addEventListener('load',rvSweep);
  // 安全策：万一スクロールを取りこぼしても不可視のまま残さない
  setTimeout(function(){rvItems.slice().forEach(reveal);rvItems.length=0;},3000);

  // trust marquee
  var CLIENTS=["rakuten","microsoft","netflix","uber","shopify","goldmansachs","deloitte","salesforce","sap","gitlab","stripe","coinbase","doordash","instacart","intercom","figma","notion","slack","zoom","dropbox","atlassian","cognizant"];
  var cnames={rakuten:"楽天 Rakuten",goldmansachs:"Goldman Sachs",doordash:"DoorDash",gitlab:"GitLab",sap:"SAP"};
  function buildLogos(arr){return arr.map(function(n){return '<img src="assets/claude-clients/'+n+'.svg" alt="'+(cnames[n]||n)+'" loading="lazy" onerror="this.style.display=\'none\'"/>';}).join('');}
  ['trustTrack','trustTrackA','trustTrackB'].forEach(function(id){var el=document.getElementById(id);if(!el)return;var arr=CLIENTS;if(id==='trustTrackB')arr=CLIENTS.slice(11);if(id==='trustTrackA')arr=CLIENTS.slice(0,11);el.innerHTML=buildLogos(arr)+buildLogos(arr);});

  // terminal typing
  (function(){
    var body=document.getElementById('termBody'); if(!body) return;
    var reduce=matchMedia('(prefers-reduced-motion: reduce)').matches;
    var SCRIPT=[
      {t:'cmd', s:'先月の問い合わせを分類して、対応漏れを一覧にして'},
      {t:'step', s:'データを読み込み中', r:'1,284 件'},
      {t:'step', s:'カテゴリに分類中', r:'6 カテゴリ'},
      {t:'step', s:'対応漏れを抽出中', r:'12 件'},
      {t:'step', s:'レポートを生成中', r:'done'},
      {t:'done', s:'対応漏れ一覧.xlsx を作成しました'},
      {t:'muted', s:'— 約14秒で完了。人は確認と判断に集中できます。'}
    ];
    function renderFinal(){body.innerHTML='';SCRIPT.forEach(function(l){var d=document.createElement('div');d.className='tl '+l.t;if(l.t==='cmd')d.innerHTML='<span class="pr">❯ </span>'+l.s;else if(l.t==='step')d.innerHTML='<span class="dot">● </span>'+l.s+' <span class="ok">✓ '+l.r+'</span>';else if(l.t==='done')d.textContent='✓ '+l.s;else d.textContent=l.s;body.appendChild(d);});}
    if(reduce){renderFinal();return;}
    var line=0;
    function typeCmd(text,el,cb){var i=0;var cur=document.createElement('span');cur.className='cursor';el.appendChild(cur);(function tick(){if(i<text.length){cur.insertAdjacentText('beforebegin',text[i]);i++;setTimeout(tick,42+Math.random()*40);}else{cur.remove();cb&&cb();}})();}
    function next(){
      if(line>=SCRIPT.length){setTimeout(function(){body.innerHTML='';line=0;setTimeout(next,400);},2600);return;}
      var l=SCRIPT[line];var d=document.createElement('div');d.className='tl '+l.t;body.appendChild(d);
      if(l.t==='cmd'){d.innerHTML='<span class="pr">❯ </span>';typeCmd(l.s,d,function(){line++;setTimeout(next,520);});}
      else if(l.t==='step'){d.innerHTML='<span class="dot">● </span>'+l.s+' …';setTimeout(function(){d.innerHTML='<span class="dot">● </span>'+l.s+' <span class="ok">✓ '+l.r+'</span>';line++;setTimeout(next,460);},620+Math.random()*360);}
      else{d.textContent=(l.t==='done'?'✓ ':'')+l.s;line++;setTimeout(next,500);}
    }
    next();
  })();

  // demo tabs/thumbs switching
  window.ccDemoSelect=function(key){
    document.querySelectorAll('.tab').forEach(function(t){t.classList.toggle('on',t.dataset.k===key);});
    document.querySelectorAll('.thumb').forEach(function(t){t.classList.toggle('on',t.dataset.k===key);});
    var data=(window.CC_DEMO||{})[key]; if(!data) return;
    var stage=document.getElementById('demoStage'); if(!stage) return;
    var vsrc=(data.video?('<video controls preload="none" poster="assets/videos/'+data.poster+'"><source src="assets/videos/'+data.video+'" type="video/mp4"></video>'):'');
    stage.querySelector('.videobox').innerHTML=vsrc+
      '<div class="videoph"><span class="tag">録画準備中</span><div class="play"></div><b>'+data.title+'</b><span>'+data.ph+'</span></div>';
    // if video file exists it plays above the placeholder; hide placeholder when video can play
    var v=stage.querySelector('video');
    if(v){v.addEventListener('loadeddata',function(){var ph=stage.querySelector('.videoph');if(ph)ph.style.display='none';});}
    var side=stage.querySelector('.demo-side');
    side.innerHTML='<h4>'+data.title+' <span class="badge">自動化の流れ</span></h4>'+
      '<ul class="flowsteps">'+data.flow.map(function(f,i){return '<li><span class="fn">'+(i+1)+'</span><span>'+f+'</span></li>';}).join('')+'</ul>'+
      '<div class="metrics">'+data.metrics.map(function(m){return '<div class="metric"><b>'+m.v+'</b><span>'+m.l+'</span></div>';}).join('')+'</div>';
  };
  if(window.CC_DEMO){var first=Object.keys(window.CC_DEMO)[0];if(first)window.ccDemoSelect(first);}
})();
