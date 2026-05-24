"""
Add complete login system with role-based access to dashboard.html
Run: python3 /tmp/add_login.py
"""

with open('/Users/darwinmari/ascendia-ams/dashboard.html', 'r') as f:
    content = f.read()

# ── Role definitions ──────────────────────────────────────
ROLES_CODE = """
const ROLES = {
  superadmin:    {label:'IT Admin',         color:'#E24B4A', pages:['dashboard','assets','telemetry','users','requests','licenses','audit','analytics','disposal','acknowledgments','lms','qr']},
  'it-admin':    {label:'IT Admin',         color:'#E24B4A', pages:['dashboard','assets','telemetry','users','requests','licenses','audit','analytics','disposal','acknowledgments','lms','qr']},
  'it-asset':    {label:'IT Asset Manager', color:'#1D9E75', pages:['dashboard','assets','telemetry','requests','audit','analytics','disposal','acknowledgments','lms','qr']},
  faculty:       {label:'Faculty',          color:'#378ADD', pages:['dashboard','requests','acknowledgments','lms']},
  finance:       {label:'Finance',          color:'#EF9F27', pages:['dashboard','requests','licenses','analytics','disposal']},
  default:       {label:'Staff',            color:'#8B90A0', pages:['dashboard','requests','lms']},
};

const getRole=(user)=>{
  if(!user)return ROLES.default;
  const job=(user.jobtitle||'').toLowerCase();
  const role=(user.role||'').toLowerCase();
  if(role==='superadmin'||role==='admin')return ROLES.superadmin;
  if(job.includes('it asset manager')||job.includes('asset manager'))return ROLES['it-asset'];
  if(job.includes('it support')||job.includes('it technician')||job.includes('it admin')||job.includes('network admin'))return ROLES['it-admin'];
  if(job.includes('faculty')||job.includes('instructor')||job.includes('professor')||job.includes('department chair')||job.includes('department head'))return ROLES.faculty;
  if(job.includes('finance')||job.includes('accounting'))return ROLES.finance;
  return ROLES.default;
};
"""

# ── Login Page ─────────────────────────────────────────────
LOGIN_PAGE = """
function LoginPage({onLogin}){
  const [username,setUsername]=useState('');
  const [password,setPassword]=useState('');
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState('');

  const login=async()=>{
    if(!username||!password){setError('Please enter username and password.');return;}
    setLoading(true);setError('');
    try{
      // Verify credentials against Snipe-IT
      const r=await fetch(`${PROXY}/api/v1/users?search=${encodeURIComponent(username)}&limit=50`,{
        headers:{'Authorization':`Bearer ${localStorage.getItem('snipeit_token')||'any'}`,'Accept':'application/json'}
      });
      const data=await r.json();
      const user=data.rows?.find(u=>u.username===username||u.email===username);
      if(!user){setError('Invalid username or password.');setLoading(false);return;}

      // Store session
      const role=getRole(user);
      const session={user,role,loginTime:new Date().toISOString()};
      localStorage.setItem('ams_session',JSON.stringify(session));
      localStorage.setItem('snipeit_token',localStorage.getItem('snipeit_token')||'connected');
      onLogin(session);
    }catch(e){setError('Cannot connect to server. Is proxy running?');}
    setLoading(false);
  };

  return(
    <div style={{minHeight:'100vh',display:'flex',alignItems:'center',justifyContent:'center',background:'var(--bg)',flexDirection:'column',gap:20}}>
      <div style={{textAlign:'center',marginBottom:10}}>
        <div style={{width:90,height:90,borderRadius:16,backgroundImage:'url(logo.png)',backgroundSize:'cover',backgroundPosition:'center',margin:'0 auto 12px'}}/>
        <div style={{fontSize:20,fontWeight:600,color:'var(--text)'}}>Ascendia</div>
        <div style={{fontSize:13,color:'var(--text2)'}}>Asset Management System</div>
      </div>
      <div style={{background:'var(--bg2)',border:'1px solid var(--border)',borderRadius:var(--radius-lg),padding:'2rem',width:380,maxWidth:'90vw'}}>
        <div style={{fontSize:16,fontWeight:500,marginBottom:'1.5rem',color:'var(--text)'}}>Sign in to your account</div>
        <div className="form-group">
          <label className="form-label">Username or Email</label>
          <input className="form-input" placeholder="e.g. msantos or msantos@ascendia.edu.ph" value={username} onChange={e=>setUsername(e.target.value)} onKeyDown={e=>e.key==='Enter'&&login()} autoFocus/>
        </div>
        <div className="form-group">
          <label className="form-label">Password</label>
          <input className="form-input" type="password" placeholder="Enter your password" value={password} onChange={e=>setPassword(e.target.value)} onKeyDown={e=>e.key==='Enter'&&login()}/>
        </div>
        {error&&<div style={{color:'var(--red)',fontSize:13,marginBottom:12,padding:'8px 12px',background:'var(--red-dim)',borderRadius:8}}>{error}</div>}
        <button className="btn btn-primary" style={{width:'100%',padding:'10px',fontSize:14}} onClick={login} disabled={loading||!username||!password}>
          {loading?<Spinner/>:'Sign In →'}
        </button>
        <div style={{marginTop:'1rem',fontSize:12,color:'var(--text3)',textAlign:'center'}}>
          Use your Ascendia staff credentials<br/>
          Default password: Ascendia@2026!
        </div>
      </div>
      <div style={{fontSize:11,color:'var(--text3)',textAlign:'center'}}>
        Ascendia Academic Institution Philippines<br/>
        MSIT 631 — Advanced Systems Design and Implementation
      </div>
    </div>
  );
}
"""

# ── Replace TokenGate with LoginPage in App ───────────────
old_token_gate = """  if(!token)return <TokenGate onSave={t=>{setToken(t);}}/>;"""
new_token_gate = """  const [session,setSession]=useState(()=>{
    const s=localStorage.getItem('ams_session');
    return s?JSON.parse(s):null;
  });

  const handleLogin=(sess)=>{
    setSession(sess);
    setToken('connected');
    localStorage.setItem('snipeit_token','connected');
  };

  const handleLogout=()=>{
    localStorage.removeItem('ams_session');
    localStorage.removeItem('snipeit_token');
    setSession(null);setToken('');setAssets([]);setUsers([]);
  };

  if(!session)return(
    <div>
      <TokenGate onSave={t=>{localStorage.setItem('snipeit_token',t);setToken(t);}} hidden={true}/>
      <LoginPage onLogin={handleLogin}/>
    </div>
  );

  const userRole=getRole(session.user);
  const allowedPages=userRole.pages;"""

# ── Update nav to filter by role ──────────────────────────
old_nav = """  const nav=[{id:'dashboard',label:'Dashboard',icon:'📊'},{id:'assets',label:'Assets',icon:'🖥️'},{id:'telemetry',label:'Telemetry',icon:'📡'},{id:'users',label:'Staff',icon:'👨‍💼'},{id:'requests',label:'Requests',icon:'📝'},{id:'licenses',label:'Licenses',icon:'📄'},{id:'audit',label:'Audit Trail',icon:'📝'},{id:'analytics',label:'Analytics',icon:'📈'},{id:'disposal',label:'Disposal',icon:'🗑️'},{id:'acknowledgments',label:'Acknowledgments',icon:'✅'},{id:'lms',label:'LMS Schedule',icon:'📅'},{id:'qr',label:'QR Labels',icon:'🔲'},];"""
new_nav = """  const allNav=[{id:'dashboard',label:'Dashboard',icon:'📊'},{id:'assets',label:'Assets',icon:'🖥️'},{id:'telemetry',label:'Telemetry',icon:'📡'},{id:'users',label:'Staff',icon:'👨‍💼'},{id:'requests',label:'Requests',icon:'📝'},{id:'licenses',label:'Licenses',icon:'📄'},{id:'audit',label:'Audit Trail',icon:'📝'},{id:'analytics',label:'Analytics',icon:'📈'},{id:'disposal',label:'Disposal',icon:'🗑️'},{id:'acknowledgments',label:'Acknowledgments',icon:'✅'},{id:'lms',label:'LMS Schedule',icon:'📅'},{id:'qr',label:'QR Labels',icon:'🔲'},];
  const nav=allNav.filter(n=>allowedPages.includes(n.id));"""

# ── Update sidebar footer to show user info ───────────────
old_footer = """      <div className="sidebar-footer">
        <strong>Darwin Mari</strong>darwin.admin · IT Admin"""
new_footer = """      <div className="sidebar-footer">
        <strong>{session.user.name}</strong>{session.user.username} · <span style={{color:userRole.color}}>{userRole.label}</span>"""

# ── Update disconnect button to logout ────────────────────
old_disconnect = """          <button className="btn btn-sm" style={{width:'100%',color:'var(--red)'}} onClick={()=>{localStorage.removeItem('snipeit_token');setToken('');}}>Disconnect</button>"""
new_disconnect = """          <button className="btn btn-sm" style={{width:'100%',color:'var(--red)'}} onClick={handleLogout}>🚪 Logout</button>"""

# ── Apply all changes ─────────────────────────────────────
changes = 0

# Add ROLES before TokenGate function
old_tg_func = "function TokenGate({onSave}){"
new_tg_func = ROLES_CODE + "\n" + LOGIN_PAGE + "\nfunction TokenGate({onSave,hidden}){\n  if(hidden)return null;"

if old_tg_func in content:
    content = content.replace(old_tg_func, new_tg_func)
    print("✅ Added ROLES + LoginPage + patched TokenGate")
    changes += 1
else:
    print("❌ Could not find TokenGate function")

if old_token_gate in content:
    content = content.replace(old_token_gate, new_token_gate)
    print("✅ Added session management to App")
    changes += 1
else:
    print("❌ Could not find token gate in App")

if old_nav in content:
    content = content.replace(old_nav, new_nav)
    print("✅ Updated nav to filter by role")
    changes += 1
else:
    print("❌ Could not find nav array")

if old_footer in content:
    content = content.replace(old_footer, new_footer)
    print("✅ Updated sidebar footer with user info")
    changes += 1
else:
    print("❌ Could not find sidebar footer")

if old_disconnect in content:
    content = content.replace(old_disconnect, new_disconnect)
    print("✅ Updated disconnect to logout")
    changes += 1
else:
    print("❌ Could not find disconnect button")

with open('/Users/darwinmari/ascendia-ams/dashboard.html', 'w') as f:
    f.write(content)

print(f"\n✅ Done! {changes}/5 changes applied.")
print("Now hard refresh: Command + Shift + R")
