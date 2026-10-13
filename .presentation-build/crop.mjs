import {createRequire} from 'node:module';
const sharp=createRequire('C:/Users/babur/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/runtime.cjs')('sharp');
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const dir=path.dirname(fileURLToPath(import.meta.url));
for(const [name,rect] of [['dashboard',{left:72,top:129,width:1296,height:700}],['workspace',{left:72,top:177,width:1296,height:813}],['wallet',{left:72,top:303,width:416,height:221}],['certificate',{left:127,top:209,width:1187,height:810}]]){
 await sharp(path.join(dir,name+'.png')).extract(rect).png().toFile(path.join(dir,name+'-crop.png'));
}
