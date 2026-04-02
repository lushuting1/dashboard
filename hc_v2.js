
var BUDGET_DATA = JSON.parse(document.getElementById('budget-data').textContent);
var DIM_LIST = JSON.parse(document.getElementById('dim-data').textContent);

function rc(p){return p>=90?'#22c55e':p>=75?'#f59e0b':'#FF2442'}
function rtc(p){return p>=90?'#166534':p>=75?'#92400e':'#b91c1c'}

function computeRow(r){
  var predict = r.actual + (r.transIn||0) - (r.transOut||0) + r.pending - r.leaving;
  var gap = r.budget - predict;
  var rate = r.budget > 0 ? Math.round(predict / r.budget * 100) : 0;
  return Object.assign({}, r, {predict: predict, gap: gap, rate: rate});
}

function getL1(l1){
  var rows = BUDGET_DATA.filter(function(r){return r.l1===l1;}).map(computeRow);
  var budget=0,actual=0,transIn=0,transOut=0,pending=0,leaving=0;
  rows.forEach(function(r){
    budget+=r.budget; actual+=r.actual; transIn+=(r.transIn||0);
    transOut+=(r.transOut||0); pending+=r.pending; leaving+=r.leaving;
  });
  var predict=actual+transIn-transOut+pending-leaving;
  var gap=budget-predict;
  var rate=budget>0?Math.round(predict/budget*100):0;
  return {l1:l1,budget:budget,actual:actual,transIn:transIn,transOut:transOut,
           pending:pending,leaving:leaving,predict:predict,gap:gap,rate:rate,rows:rows};
}

function naCell(){return '<span class="na">-</span>';}
function mckRate(rate){
  var pct=Math.min(rate,100), c=rc(rate), tc=rtc(rate);
  return '<div class="mck-rate-wrap"><div class="mck-rate-bar"><div class="mck-rate-fill" style="width:'+pct+'%;background:'+c+'"></div></div>'
    +'<span class="mck-rate-text" style="color:'+tc+'">'+(rate>100?'100%+':rate+'%')+'</span></div>';
}
function mckGap(gap){
  if(!gap) return naCell();
  return gap>0 ? '<span class="mck-gap-pos">+'+gap+'</span>' : '<span class="mck-gap-neg">'+gap+'</span>';
}

var _expanded = {};
function renderMckTable(id, l1){
  var el=document.getElementById(id); if(!el) return;
  var grp=getL1(l1);
  if(_expanded[l1]===undefined) _expanded[l1]=true;
  var open=_expanded[l1];
  var h='<table><thead><tr>'
    +'<th>部门</th><th>Budget</th><th>在职</th><th>转入↑</th><th>转出↓</th>'
    +'<th>待入职</th><th>待离职</th><th>预计</th><th>Gap</th><th>满编率</th>'
    +'</tr></thead><tbody>';
  h+='<tr class="mck-l1-row" onclick="_expanded[''+l1+'']=!_expanded[''+l1+''];renderMckTable(''+id+'',''+l1+'')">';
  h+='<td><em class="mck-toggle">'+(open?'−':'+')+'</em>■ '+grp.l1+'('+grp.rows.length+')</td>';
  h+='<td>'+grp.budget+'</td><td>'+grp.actual+'</td>';
  h+='<td>'+(grp.transIn||naCell())+'</td><td>'+(grp.transOut||naCell())+'</td>';
  h+='<td>'+grp.pending+'</td><td>'+grp.leaving+'</td>';
  h+='<td>'+grp.predict+'</td><td>'+mckGap(grp.gap)+'</td><td>'+mckRate(grp.rate)+'</td></tr>';
  if(open){
    grp.rows.forEach(function(r){
      h+='<tr class="mck-l2-row">';
      h+='<td>'+r.l2+(r.real?'<span class="badge-real">真实</span>':'')+'</td>';
      h+='<td>'+r.budget+'</td><td>'+(r.actual||naCell())+'</td>';
      h+='<td>'+(r.transIn>0?r.transIn:naCell())+'</td><td>'+(r.transOut>0?r.transOut:naCell())+'</td>';
      h+='<td>'+(r.pending||naCell())+'</td><td>'+(r.leaving||naCell())+'</td>';
      h+='<td>'+r.predict+'</td><td>'+mckGap(r.gap)+'</td><td>'+mckRate(r.rate)+'</td></tr>';
    });
  }
  h+='</tbody></table>';
  el.innerHTML=h;
}

function renderBars(id, rows){
  var el=document.getElementById(id); if(!el) return;
  var sorted=[].concat(rows).sort(function(a,b){return a.rate-b.rate;});
  el.innerHTML=sorted.map(function(r){
    var pct=Math.min(r.rate,100), c=rc(r.rate), tc=rtc(r.rate);
    var disp=r.rate>100?'100%+':r.rate+'%';
    return '<div class="dept-item">'
      +'<div class="dept-name">'+r.l2+(r.real?'<span class="badge-real">真</span>':'')+'</div>'
      +'<div class="dept-track"><div class="dept-fill" data-pct="'+pct+'" style="background:'+c+'"></div></div>'
      +'<div class="dept-pct" style="color:'+tc+'">'+disp+'</div></div>';
  }).join('');
  setTimeout(function(){
    el.querySelectorAll('.dept-fill').forEach(function(b,i){
      setTimeout(function(){b.style.width=b.dataset.pct+'%';},i*40);
    });
  },80);
}

function renderKpis(id, grp){
  var el=document.getElementById(id); if(!el) return;
  el.innerHTML='<div class="kpi-card"><div class="kpi-label">HC规划</div><div class="kpi-value">'+grp.budget+'</div></div>'
    +'<div class="kpi-card"><div class="kpi-label">在职</div><div class="kpi-value">'+grp.actual+'</div></div>'
    +'<div class="kpi-card"><div class="kpi-label">转入在途</div><div class="kpi-value">'+grp.transIn+'</div></div>'
    +'<div class="kpi-card"><div class="kpi-label">转出在途</div><div class="kpi-value">'+grp.transOut+'</div></div>'
    +'<div class="kpi-card"><div class="kpi-label">入职在途</div><div class="kpi-value">'+grp.pending+'</div></div>'
    +'<div class="kpi-card"><div class="kpi-label">离职在途</div><div class="kpi-value">'+grp.leaving+'</div></div>'
    +'<div class="kpi-card"><div class="kpi-label">满编率</div><div class="kpi-value highlight">'+grp.rate+'%</div></div>';
}

function renderAlerts(id, rows){
  var el=document.getElementById(id); if(!el) return;
  var danger=rows.filter(function(r){return r.rate<75;});
  var warn=rows.filter(function(r){return r.rate>=75&&r.rate<85;});
  var h='';
  if(danger.length) h+='<span class="alert-label">立即关注</span>'+danger.map(function(r){return '<span class="alert-badge badge-danger">🚨 '+r.l2+' '+r.rate+'%</span>';}).join('');
  if(warn.length){if(h)h+='<div class="alert-divider"></div>';h+='<span class="alert-label">建议追进</span>'+warn.map(function(r){return '<span class="alert-badge badge-warn">📌 '+r.l2+' '+r.rate+'%</span>';}).join('');}
  if(!h) h='<span style="color:var(--text-3);font-size:13px">✅ 暂无预警部门</span>';
  el.innerHTML=h;
}

function renderDimTable(id, l1Keywords){
  var el=document.getElementById(id); if(!el) return;
  var items=DIM_LIST.filter(function(d){
    return l1Keywords.some(function(k){return (d.deptPath||'').indexOf(k)>=0||(d.dept||'').indexOf(k)>=0;});
  });
  if(!items.length){el.innerHTML='<div style="padding:16px 18px;color:var(--text-3);font-size:13px">暂无待离职人员</div>';return;}
  var h='<table><thead><tr><th>姓名</th><th>部门</th><th>离职日期</th><th>类型</th><th>层级</th><th>状态</th></tr></thead><tbody>';
  items.forEach(function(d){
    var tag=d.type==='被动'?'tag-p':'tag-a';
    h+='<tr><td style="font-weight:600">'+(d.name||'-')+'</td><td>'+(d.dept||'-')+'</td>'
      +'<td>'+((d.date||'').slice(5)||'-')+'</td>'
      +'<td><span class="tag '+tag+'">'+(d.type||'-')+'</span></td>'
      +'<td>'+(d.lv||'-')+'</td>'
      +'<td><span class="tag tag-s">'+(d.status||'待离职')+'</span></td></tr>';
  });
  h+='</tbody></table>';
  el.innerHTML=h;
}

function renderOverview(){
  var el=document.getElementById('overview-cards'); if(!el) return;
  var l1s=['交易','商业化','职能&DI'];
  var colors={'交易':'#f97316','商业化':'#FF2442','职能&DI':'#0070C0'};
  el.innerHTML=l1s.map(function(l1){
    var g=getL1(l1); var c=colors[l1]||'#888';
    var pct=Math.min(g.rate,100);
    return '<div class="overview-card">'
      +'<div class="ov-dept">'+l1+'</div>'
      +'<div class="ov-budget">'+g.budget+'<span>Budget HC</span></div>'
      +'<div class="progress-wrap">'
      +'<div class="progress-label"><span>在职 '+g.actual+'</span><span>'+g.rate+'%</span></div>'
      +'<div class="progress-track"><div class="progress-bar" data-pct="'+pct+'" style="background:'+rc(g.rate)+'"></div></div>'
      +'</div>'
      +'<div class="ov-meta">'
      +'<div class="ov-meta-item"><span class="ov-meta-label">待入职</span><span class="ov-meta-val">'+g.pending+'</span></div>'
      +'<div class="ov-sep">·</div>'
      +'<div class="ov-meta-item"><span class="ov-meta-label">待离职</span><span class="ov-meta-val">'+g.leaving+'</span></div>'
      +'<div class="ov-sep">·</div>'
      +'<div class="ov-meta-item"><span class="ov-meta-label">转入</span><span class="ov-meta-val">'+g.transIn+'</span></div>'
      +'<div class="ov-sep">·</div>'
      +'<div class="ov-meta-item"><span class="ov-meta-label">Gap</span><span class="ov-meta-val" style="color:'+(g.gap>0?'var(--red)':'var(--green)')+'">'+g.gap+'</span></div>'
      +'</div></div>';
  }).join('');
  setTimeout(function(){
    document.querySelectorAll('.progress-bar[data-pct]').forEach(function(b,i){
      setTimeout(function(){b.style.width=b.dataset.pct+'%';},200+i*100);
    });
  },100);
}

function renderRankList(){
  var el=document.getElementById('rank-list'); if(!el) return;
  var all=BUDGET_DATA.map(computeRow).sort(function(a,b){return a.rate-b.rate;});
  el.innerHTML=all.map(function(r){
    var pct=Math.min(r.rate,100), c=rc(r.rate), tc=rtc(r.rate);
    return '<div class="rank-item">'
      +'<div style="font-size:13px;font-weight:500">'+r.l2+'<span style="font-size:11px;color:var(--text-3);margin-left:4px">['+r.l1+']</span></div>'
      +'<div><div class="rank-track"><div class="rank-fill" data-pct="'+pct+'" style="background:'+c+'"></div></div></div>'
      +'<div class="rank-pct" style="color:'+tc+'">'+(r.rate>100?'100%+':r.rate+'%')+'</div>'
      +'</div>';
  }).join('');
  setTimeout(function(){
    el.querySelectorAll('.rank-fill').forEach(function(b,i){
      setTimeout(function(){b.style.width=b.dataset.pct+'%';},60+i*25);
    });
  },100);
}

function switchTab(id, btn){
  document.querySelectorAll('.tab-panel').forEach(function(p){p.classList.remove('active');});
  document.querySelectorAll('.tab-btn').forEach(function(b){b.classList.remove('active');});
  document.getElementById('tab-'+id).classList.add('active');
  btn.classList.add('active');
  setTimeout(function(){
    document.querySelectorAll('#tab-'+id+' [data-pct]').forEach(function(b,i){
      b.style.width='0';
      setTimeout(function(){b.style.width=b.dataset.pct+'%';},60+i*35);
    });
  },50);
}

(function init(){
  renderOverview();
  renderRankList();

  var trade=getL1('交易');
  renderAlerts('trade-alerts', trade.rows);
  renderKpis('trade-kpis', trade);
  renderMckTable('mck-trade','交易');
  renderBars('trade-bars', trade.rows);

  var biz=getL1('商业化');
  renderAlerts('biz-alerts', biz.rows);
  renderKpis('biz-kpis', biz);
  renderDimTable('biz-dim', ['行业八部','行业九部','渠道业务','创作者营销','策略中台','商业']);
  renderMckTable('mck-commercial','商业化');
  renderBars('commercial-bars', biz.rows);

  var func=getL1('职能&DI');
  renderAlerts('func-alerts', func.rows);
  renderKpis('func-kpis', func);
  renderDimTable('func-dim', ['财务','税务','内控','内审','采购','资本市场','法务','DI']);
  renderMckTable('mck-finance','职能&DI');
  renderBars('finance-bars', func.rows);
}  } catch(e) {
    document.body.insertAdjacentHTML('afterbegin',
      '<div style="background:red;color:white;padding:20px;font-size:14px;z-index:9999;position:fixed;top:0;left:0;right:0">JS ERROR: '+e.message+'</div>'
    );
  }
})();
