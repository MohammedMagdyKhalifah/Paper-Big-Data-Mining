// Run the two local services together, and stop both on Ctrl+C.
import {spawn} from 'node:child_process'
import {fileURLToPath} from 'node:url'
import path from 'node:path'
import {setTimeout as delay} from 'node:timers/promises'
const root=path.dirname(fileURLToPath(import.meta.url))
// Caller environment retains precedence over local, untracked settings.
try { process.loadEnvFile(path.join(root,'.env')) }
catch(error) { if(error.code!=='ENOENT') throw error }
const python=process.env.APP_PYTHON ? path.resolve(root,process.env.APP_PYTHON) : path.join(root,'backend','.venv','bin','python')
const apiPort=process.env.APP_API_PORT||'8000'
const backend=spawn(python,['-m','uvicorn','app.backend.main:app','--host','127.0.0.1','--port',apiPort],{cwd:path.dirname(root),stdio:'inherit'})
let frontend
let stopping=false
function stop(code=0){if(stopping)return;stopping=true;backend.kill('SIGTERM');frontend?.kill('SIGTERM');setTimeout(()=>process.exit(code),500).unref()}
function watch(child){
 child.on('error',error=>{console.error(error.message);stop(1)})
 child.on('exit',code=>{if(!stopping)stop(code||0)})
}
watch(backend)
process.on('SIGINT',()=>stop());process.on('SIGTERM',()=>stop())
// A4 loads before FastAPI accepts requests. Start Vite after diagnostics are
// reachable, so a cold model doesn't produce a false frontend connection error.
// A model-load failure still serves diagnostics (200/status=error), never fallback.
const deadline=Date.now()+120000
console.log('Waiting for local Backend/model startup…')
while(!stopping){
 try {
  const response=await fetch(`http://127.0.0.1:${apiPort}/api/models/info`,{signal:AbortSignal.timeout(1000)})
  await response.body?.cancel()
  if(response.ok)break
 } catch { /* Backend has not bound its local port yet. */ }
 if(Date.now()>=deadline){console.error('Backend startup timed out; inspect the local model/dependencies.');stop(1);break}
 await delay(250)
}
if(!stopping){
 frontend=spawn(process.platform==='win32'?'npm.cmd':'npm',['run','dev','--','--host','127.0.0.1'],{cwd:path.join(root,'frontend'),stdio:'inherit'})
 watch(frontend)
}
