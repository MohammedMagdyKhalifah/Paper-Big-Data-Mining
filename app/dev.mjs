// Run the two local services together, and stop both on Ctrl+C.
import {spawn} from 'node:child_process'
import {fileURLToPath} from 'node:url'
import path from 'node:path'
const root=path.dirname(fileURLToPath(import.meta.url))
const python=process.env.APP_PYTHON || path.join(root,'backend','.venv','bin','python')
const backend=spawn(python,['-m','uvicorn','app.backend.main:app','--host','127.0.0.1','--port','8000'],{cwd:path.dirname(root),stdio:'inherit'})
const frontend=spawn(process.platform==='win32'?'npm.cmd':'npm',['run','dev','--','--host','127.0.0.1'],{cwd:path.join(root,'frontend'),stdio:'inherit'})
let stopping=false
function stop(code=0){if(stopping)return;stopping=true;backend.kill('SIGTERM');frontend.kill('SIGTERM');setTimeout(()=>process.exit(code),500).unref()}
for(const child of [backend,frontend]){
 child.on('error',error=>{console.error(error.message);stop(1)})
 child.on('exit',code=>{if(!stopping)stop(code||0)})
}
process.on('SIGINT',()=>stop());process.on('SIGTERM',()=>stop())
