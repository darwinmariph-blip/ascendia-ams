import sys

with open('/Users/darwinmari/ascendia-ams/dashboard.html', 'r') as f:
    content = f.read()

# Find analytics page boundaries
start = content.find('function AnalyticsPage({assets,users}){')
end_marker = '\n/* -- Disposal / Retirement Page -- */'
end = content.find('function DisposalPage(', start)
old_analytics = content[start:end]
print(f"Found analytics: {len(old_analytics)} chars at line approx {content[:start].count(chr(10))}")

new_analytics = r'''function AnalyticsPage({assets,users}){
  const chartRef1=useRef(null),chartRef2=useRef(null),chartRef3=useRef(null);
  const chartRef4=useRef(null),chartRef5=useRef(null),chartRef6=useRef(null);
  const inst1=useRef(null),inst2=useRef(null),inst3=useRef(null);
  const inst4=useRef(null),inst5=useRef(null),inst6=useRef(null);
  const [analyticsTab,setAnalyticsTab]=useState('overview');

  const totalValue=assets.reduce((s,a)=>s+(parseFloat((a.purchase_cost||'0').toString().replace(/,/g,''))||0),0);
  const byCategory={};assets.forEach(a=>{const c=a.category?.name||'Other';byCategory[c]=(byCategory[c]||0)+1;});
  const byLocation={};assets.forEach(a=>{const l=a.location?.name||'Unknown';byLocation[l]=(byLocation[l]||0)+1;});
  const highAI=assets.filter(a=>getAiScore(a)==='High').length;
  const medAI=assets.filter(a=>getAiScore(a)==='Medium').length;
  const lowAI=assets.filter(a=>getAiScore(a)==='Low').length;
  const healthScores=Object.values(TELEMETRY).map(t=>t.health);
  const avgHealth=healthScores.length?Math.round(healthScores.reduce((s,h)=>s+h,0)/healthScores.length):0;

  const byYear={2023:0,2024:0,2025:0,2026:0};
  assets.forEach(a=>{const y=parseInt((a.purchase_date?.date||'2026').substring(0,4));if(byYear[y]!==undefined)byYear[y]++;});

  const depreciationByYear={};
  [2023,2024,2025,2026].forEach(yr=>{
    const ya=assets.filter(a=>(a.purchase_date?.date||'').startsWith(yr));
    const cost=ya.reduce((s,a)=>s+(parseFloat((a.purchase_cost||'0').toString().replace(/,/g,''))||0),0);
    const age=2026-yr;
    depreciationByYear[yr]={cost:Math.round(cost),bookValue:Math.round(cost*Math.max(0,(1-age/5))),depreciation:Math.round(cost*(age/5))};
  });

  const bySupplier={};
  assets.forEach(a=>{const s=(a.supplier?.name||'Unknown').replace(' Philippines','').replace(' by Schneider Electric','');bySupplier[s]=(bySupplier[s]||0)+1;});

  const needsMaintenance=assets.filter(a=>{const yr=parseInt((a.purchase_date?.date||'2026').substring(0,4));return(2026-yr)>=3||getAiScore(a)==='High';}).length;
  const replacementDue=assets.filter(a=>{const yr=parseInt((a.purchase_date?.date||'2026').substring(0,4));return(2026-yr)>=4;}).length;

  useEffect(()=>{
    if(!chartRef1.current)return;
    if(inst1.current)inst1.current.destroy();
    inst1.current=new Chart(chartRef1.current,{type:'doughnut',data:{labels:Object.keys(byCategory),datasets:[{data:Object.values(byCategory),backgroundColor:['#378ADD','#1D9E75','#EF9F27','#E24B4A','#9B59B6','#E67E22','#1ABC9C','#E74C3C','#3498DB','#2ECC71','#F39C12'],borderWidth:0}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'right',labels:{color:'#8B90A0',font:{size:10}}}}}});
  },[JSON.stringify(byCategory)]);

  useEffect(()=>{
    if(!chartRef2.current)return;
    if(inst2.current)inst2.current.destroy();
    inst2.current=new Chart(chartRef2.current,{type:'bar',data:{labels:['High','Medium','Low','Unscored'],datasets:[{data:[highAI,medAI,lowAI,assets.length-highAI-medAI-lowAI],backgroundColor:['#E24B4A','#EF9F27','#1D9E75','#555B6E'],borderRadius:5,borderSkipped:false}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,ticks:{color:'#555B6E'},grid:{color:'rgba(255,255,255,0.05)'}},x:{ticks:{color:'#555B6E'},grid:{display:false}}}}});
  },[assets.length]);

  useEffect(()=>{
    if(!chartRef3.current)return;
    if(inst3.current)inst3.current.destroy();
    const locs=Object.keys(byLocation).slice(0,6);
    inst3.current=new Chart(chartRef3.current,{type:'bar',indexAxis:'y',data:{labels:locs,datasets:[{data:locs.map(l=>byLocation[l]),backgroundColor:'#378ADD',borderRadius:5}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{beginAtZero:true,ticks:{color:'#555B6E'},grid:{color:'rgba(255,255,255,0.05)'}},y:{ticks:{color:'#555B6E',font:{size:10}},grid:{display:false}}}}});
  },[JSON.stringify(byLocation)]);

  useEffect(()=>{
    if(!chartRef4.current)return;
    if(inst4.current)inst4.current.destroy();
    const years=['2023','2024','2025','2026'];
    inst4.current=new Chart(chartRef4.current,{type:'bar',data:{labels:years,datasets:[
      {label:'Total Cost (PHP)',data:years.map(y=>depreciationByYear[parseInt(y)]?.cost||0),backgroundColor:'#1D9E75',borderRadius:5,yAxisID:'y'},
      {label:'Assets Acquired',data:years.map(y=>byYear[parseInt(y)]||0),backgroundColor:'#378ADD',borderRadius:5,yAxisID:'y1'},
    ]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#8B90A0',font:{size:11}}}},scales:{y:{beginAtZero:true,ticks:{color:'#555B6E',callback:v=>`PHP ${(v/1000000).toFixed(1)}M`},grid:{color:'rgba(255,255,255,0.05)'}},y1:{position:'right',beginAtZero:true,ticks:{color:'#555B6E'},grid:{display:false}},x:{ticks:{color:'#555B6E'},grid:{display:false}}}}});
  },[assets.length]);

  useEffect(()=>{
    if(!chartRef5.current)return;
    if(inst5.current)inst5.current.destroy();
    const years=['2023','2024','2025','2026'];
    inst5.current=new Chart(chartRef5.current,{type:'bar',data:{labels:years,datasets:[
      {label:'Book Value',data:years.map(y=>depreciationByYear[parseInt(y)]?.bookValue||0),backgroundColor:'#1D9E75',borderRadius:5,stack:'a'},
      {label:'Depreciated',data:years.map(y=>depreciationByYear[parseInt(y)]?.depreciation||0),backgroundColor:'#E24B4A',borderRadius:5,stack:'a'},
    ]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:'#8B90A0',font:{size:11}}}},scales:{y:{stacked:true,beginAtZero:true,ticks:{color:'#555B6E',callback:v=>`PHP ${(v/1000000).toFixed(1)}M`},grid:{color:'rgba(255,255,255,0.05)'}},x:{stacked:true,ticks:{color:'#555B6E'},grid:{display:false}}}}});
  },[assets.length]);

  useEffect(()=>{
    if(!chartRef6.current)return;
    if(inst6.current)inst6.current.destroy();
    const topV=Object.entries(bySupplier).sort((a,b)=>b[1]-a[1]).slice(0,8);
    inst6.current=new Chart(chartRef6.current,{type:'bar',data:{labels:topV.map(v=>v[0]),datasets:[{data:topV.map(v=>v[1]),backgroundColor:['#1D9E75','#378ADD','#EF9F27','#E24B4A','#9B59B6','#E67E22','#1ABC9C','#3498DB'],borderRadius:5}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,ticks:{color:'#555B6E'},grid:{color:'rgba(255,255,255,0.05)'}},x:{ticks:{color:'#555B6E',font:{size:10}},grid:{display:false}}}}});
  },[JSON.stringify(bySupplier)]);

  const tabs=[{id:'overview',label:'Overview'},{id:'timeline',label:'Timeline'},{id:'cost',label:'Cost Intelligence'},{id:'predict',label:'Predictions'}];

  return(<>
    <div className="metrics" style={{marginBottom:14}}>
      <div className="metric-card"><div className="metric-top"><div className="metric-icon teal">📦</div></div><div className="metric-val">{assets.length}</div><div className="metric-label">Total assets</div></div>
      <div className="metric-card"><div className="metric-top"><div className="metric-icon amber">💰</div></div><div className="metric-val">₱{(totalValue/1000000).toFixed(1)}M</div><div className="metric-label">Total value</div></div>
      <div className="metric-card"><div className="metric-top"><div className="metric-icon teal">❤️</div></div><div className="metric-val">{avgHealth}%</div><div className="metric-label">Avg health</div></div>
      <div className={`metric-card ${highAI>0?'alert':''}`}><div className="metric-top"><div className="metric-icon red">⚠️</div></div><div className="metric-val red">{highAI}</div><div className="metric-label">High priority</div></div>
      <div className="metric-card"><div className="metric-top"><div className="metric-icon amber">🔧</div></div><div className="metric-val">{needsMaintenance}</div><div className="metric-label">Need maintenance</div></div>
      <div className="metric-card"><div className="metric-top"><div className="metric-icon red">♻️</div></div><div className="metric-val">{replacementDue}</div><div className="metric-label">Due for replacement</div></div>
    </div>
    <div style={{display:'flex',gap:8,marginBottom:14,flexWrap:'wrap'}}>
      {tabs.map(t=><button key={t.id} className={`btn btn-sm ${analyticsTab===t.id?'btn-primary':''}`} onClick={()=>setAnalyticsTab(t.id)}>{t.label}</button>)}
    </div>
    {analyticsTab==='overview'&&(<>
      <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:14,marginBottom:14}}>
        <div className="card"><div className="card-head"><span className="card-title">📊 Assets by Category</span></div><div style={{position:'relative',height:220}}><canvas ref={chartRef1}/></div></div>
        <div className="card"><div className="card-head"><span className="card-title">🤖 AI Priority Distribution</span></div><div style={{position:'relative',height:220}}><canvas ref={chartRef2}/></div></div>
      </div>
      <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:14,marginBottom:14}}>
        <div className="card"><div className="card-head"><span className="card-title">📍 Assets by Location</span></div><div style={{position:'relative',height:220}}><canvas ref={chartRef3}/></div></div>
        <div className="card"><div className="card-head"><span className="card-title">🏭 Vendor Distribution</span></div><div style={{position:'relative',height:220}}><canvas ref={chartRef6}/></div></div>
      </div>
    </>)}
    {analyticsTab==='timeline'&&(<>
      <div className="card" style={{marginBottom:14}}>
        <div className="card-head"><span className="card-title">📅 Asset Acquisition Timeline (2023-2026)</span></div>
        <div style={{position:'relative',height:280}}><canvas ref={chartRef4}/></div>
      </div>
      <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:14,marginBottom:14}}>
        {[2023,2024,2025,2026].map(yr=>(
          <div key={yr} className="card">
            <div style={{fontSize:12,color:'var(--text3)',marginBottom:4}}>{yr}</div>
            <div style={{fontSize:22,fontWeight:600}}>{byYear[yr]||0}</div>
            <div style={{fontSize:11,color:'var(--text2)'}}>assets acquired</div>
            <div style={{fontSize:12,color:'var(--teal)',marginTop:4}}>₱{((depreciationByYear[yr]?.cost||0)/1000000).toFixed(2)}M spent</div>
          </div>
        ))}
      </div>
    </>)}
    {analyticsTab==='cost'&&(<>
      <div className="card" style={{marginBottom:14}}>
        <div className="card-head"><span className="card-title">💰 Depreciation and Book Value by Year</span><span style={{fontSize:11,color:'var(--text3)'}}>Straight-line 5-year useful life</span></div>
        <div style={{position:'relative',height:280}}><canvas ref={chartRef5}/></div>
      </div>
      <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:14,marginBottom:14}}>
        {[2023,2024,2025,2026].map(yr=>{
          const d=depreciationByYear[yr]||{cost:0,bookValue:0,depreciation:0};
          const pct=d.cost>0?Math.round((d.bookValue/d.cost)*100):100;
          return(<div key={yr} className="card">
            <div style={{fontSize:12,color:'var(--text3)',marginBottom:4}}>Batch {yr}</div>
            <div style={{fontSize:18,fontWeight:600,color:'var(--teal)'}}>₱{(d.bookValue/1000000).toFixed(2)}M</div>
            <div style={{fontSize:11,color:'var(--text2)'}}>book value</div>
            <div style={{fontSize:11,color:'var(--red)',marginTop:4}}>₱{(d.depreciation/1000000).toFixed(2)}M depreciated</div>
            <div style={{marginTop:6,background:'var(--bg3)',borderRadius:99,height:4}}>
              <div style={{width:`${pct}%`,background:'var(--teal)',borderRadius:99,height:'100%'}}/>
            </div>
            <div style={{fontSize:10,color:'var(--text3)',marginTop:2}}>{pct}% remaining value</div>
          </div>);
        })}
      </div>
      <div className="card" style={{marginBottom:14}}>
        <div className="card-head"><span className="card-title">💵 Cost Intelligence Summary</span></div>
        {[['Total Inventory Cost','₱'+Math.round(totalValue).toLocaleString()],['Total Book Value','₱'+[2023,2024,2025,2026].reduce((s,y)=>s+(depreciationByYear[y]?.bookValue||0),0).toLocaleString()],['Total Depreciation','₱'+[2023,2024,2025,2026].reduce((s,y)=>s+(depreciationByYear[y]?.depreciation||0),0).toLocaleString()],['Avg Cost per Asset','₱'+Math.round(totalValue/Math.max(assets.length,1)).toLocaleString()],['Avg Cost per Staff','₱'+Math.round(totalValue/Math.max(users.length,1)).toLocaleString()],['Highest Spend Year',[2023,2024,2025,2026].reduce((a,y)=>depreciationByYear[y]?.cost>depreciationByYear[a]?.cost?y:a,2023).toString()],].map(([k,v])=>(
          <div className="result-row" key={k}><span style={{color:'var(--text2)',fontSize:12}}>{k}</span><span style={{fontWeight:500,fontSize:13}}>{v}</span></div>
        ))}
      </div>
    </>)}
    {analyticsTab==='predict'&&(<>
      <div style={{display:'grid',gridTemplateColumns:'1fr 1fr',gap:14,marginBottom:14}}>
        <div className="card">
          <div className="card-head"><span className="card-title">🔮 Maintenance Predictions</span></div>
          {[['Needs maintenance soon',needsMaintenance,'Assets 3+ years old or High AI priority'],['Due for replacement',replacementDue,'Assets 4+ years old'],['Critical health (<40%)',Object.values(TELEMETRY).filter(t=>t.health<40).length,'Based on telemetry'],['Warning health (40-65%)',Object.values(TELEMETRY).filter(t=>t.health>=40&&t.health<65).length,'Monitor closely'],['Healthy (>65%)',Object.values(TELEMETRY).filter(t=>t.health>=65).length,'No action needed'],].map(([label,val,desc])=>(
            <div key={label} style={{padding:'8px 0',borderBottom:'0.5px solid var(--border)'}}>
              <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                <div><div style={{fontSize:13,fontWeight:500}}>{label}</div><div style={{fontSize:11,color:'var(--text3)'}}>{desc}</div></div>
                <div style={{fontSize:22,fontWeight:600,color:val>20?'var(--red)':val>10?'var(--amber)':'var(--teal)'}}>{val}</div>
              </div>
            </div>
          ))}
        </div>
        <div className="card">
          <div className="card-head"><span className="card-title">📅 Budget Forecast (Next 2 Years)</span></div>
          <div style={{fontSize:12,color:'var(--text3)',marginBottom:12}}>Based on historical spend and replacement cycles</div>
          {[{year:'2027',type:'Maintenance',est:Math.round(needsMaintenance*8000),desc:`~${needsMaintenance} assets x PHP 8,000 avg`},{year:'2027',type:'Replacement',est:Math.round(replacementDue*55000),desc:`~${replacementDue} assets x PHP 55,000 avg`},{year:'2028',type:'Maintenance',est:Math.round(needsMaintenance*1.2*8000),desc:'Projected 20% increase'},{year:'2028',type:'Replacement',est:Math.round(replacementDue*1.3*55000),desc:'Projected 30% increase'},].map((item,i)=>(
            <div key={i} style={{padding:'8px 0',borderBottom:'0.5px solid var(--border)'}}>
              <div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}>
                <div><div style={{fontSize:13,fontWeight:500}}>{item.year} — {item.type}</div><div style={{fontSize:11,color:'var(--text3)'}}>{item.desc}</div></div>
                <div style={{fontSize:15,fontWeight:600,color:'var(--teal)'}}>₱{item.est.toLocaleString()}</div>
              </div>
            </div>
          ))}
          <div style={{marginTop:12,padding:'10px',background:'var(--bg3)',borderRadius:8}}>
            <div style={{fontSize:12,color:'var(--text2)',marginBottom:4}}>Total 2-Year Budget Estimate</div>
            <div style={{fontSize:20,fontWeight:600,color:'var(--amber)'}}>₱{Math.round((needsMaintenance*8000*2.2)+(replacementDue*55000*2.3)).toLocaleString()}</div>
          </div>
        </div>
      </div>
      <div className="card" style={{marginBottom:14}}>
        <div className="card-head"><span className="card-title">🏷️ Asset Age Distribution</span></div>
        <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:10}}>
          {[{label:'< 1 year',count:assets.filter(a=>2026-parseInt((a.purchase_date?.date||'2026').substring(0,4))<1).length,color:'var(--teal)'},{label:'1-2 years',count:assets.filter(a=>{const age=2026-parseInt((a.purchase_date?.date||'2026').substring(0,4));return age>=1&&age<2;}).length,color:'#378ADD'},{label:'2-3 years',count:assets.filter(a=>{const age=2026-parseInt((a.purchase_date?.date||'2026').substring(0,4));return age>=2&&age<3;}).length,color:'var(--amber)'},{label:'3+ years',count:assets.filter(a=>2026-parseInt((a.purchase_date?.date||'2026').substring(0,4))>=3).length,color:'var(--red)'},].map(item=>(
            <div key={item.label} style={{textAlign:'center',padding:12,background:'var(--bg3)',borderRadius:8}}>
              <div style={{fontSize:28,fontWeight:600,color:item.color}}>{item.count}</div>
              <div style={{fontSize:12,color:'var(--text2)',marginTop:4}}>{item.label}</div>
              <div style={{fontSize:11,color:'var(--text3)'}}>{Math.round(item.count/Math.max(assets.length,1)*100)}% of fleet</div>
            </div>
          ))}
        </div>
      </div>
    </>)}
  </>);
}
'''

content = content[:start] + new_analytics + content[end:]

with open('/Users/darwinmari/ascendia-ams/dashboard.html', 'w') as f:
    f.write(content)
print("✅ Analytics page updated and saved!")
