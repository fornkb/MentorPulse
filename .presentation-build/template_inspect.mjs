import fs from 'node:fs/promises';
import {PresentationFile,FileBlob} from 'file:///C:/Users/babur/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const p=await PresentationFile.importPptx(await FileBlob.load('C:/Users/babur/Downloads/Project Presentation Template.pptx'));
console.log((await p.inspect({kind:'slide,textbox,image',maxChars:25000})).ndjson);
for(let i=0;i<6;i++)console.log(JSON.stringify({i,shapes:p.slides.items[i].shapes.items.map(s=>({id:s.id,name:s.name,text:s.text.toString(),position:s.position,style:s.text.style})),placeholders:p.slides.items[i].placeholders.items.map(s=>({name:s.name,text:s.text.toString(),position:s.position}))}));
