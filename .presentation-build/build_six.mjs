import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {PresentationFile,FileBlob} from 'file:///C:/Users/babur/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const dir=path.dirname(fileURLToPath(import.meta.url));
const p=await PresentationFile.importPptx(await FileBlob.load(path.join(path.dirname(dir),'output/presentations/MentorPulse_Enhanced_Presentation.pptx')));
const oldNotes=p.slides.items.map(s=>s.speakerNotes.text);
p.slides.keep([0,1,3,4,8,10]);
const slides=p.slides.items;
const inspection=await p.inspect({kind:'textbox,shape,table,chart',maxChars:150000});
const ids=[...new Set(inspection.ndjson.split('\n').filter(Boolean).map(l=>JSON.parse(l)).filter(r=>[1,3,4,5].includes(r.slideIndex)&&!/^Title 1$|^Footer Placeholder|^Slide Number/.test(r.name||'')).map(r=>r.id))];
if(ids.length)p.delete(ids);
for(let i=0;i<6;i++){for(const q of slides[i].shapes.items)if(q.name?.startsWith('Slide Number'))q.text=String(i+1);}
const C={ink:'#213B57',muted:'#596B7C',green:'#138B5D',blue:'#2676AD',line:'#C7D4DE',pale:'#F0F7F4',light:'#F2F6FA'};
function text(s,t,x,y,w,h,z=25,bold=false,color=C.ink,font='Segoe UI',align='left'){const q=s.shapes.add({geometry:'textbox',name:t.slice(0,50),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});q.text=t;q.text.style={fontSize:z,typeface:font,color,bold,insets:0,autoFit:'none',wrap:'square',alignment:align,verticalAlignment:'top'};return q;}
function node(s,t,x,y,w,h,fill=C.light,z=24){const q=s.shapes.add({geometry:'roundRect',name:t.replaceAll('\n',' '),position:{left:x,top:y,width:w,height:h},fill,line:{fill:C.line,width:1.3},borderRadius:10});q.text=t;q.text.style={fontSize:z,typeface:'Segoe UI',color:C.ink,bold:true,insets:10,alignment:'center',verticalAlignment:'middle',autoFit:'none'};return q;}
function link(s,a,b,from='right',to='left',kind='straight'){s.shapes.connect(a,b,{kind,fromSide:from,toSide:to,line:{fill:C.blue,width:2.3},tail:{type:'triangle',width:'sm',length:'sm'}});}
function sub(s,t){text(s,t,88,168,1104,40,25,true,C.green);}
function table(s,data,x,y,w,h,widths,z=23){const q=s.tables.add({rows:data.length,columns:data[0].length,left:x,top:y,width:w,height:h,values:data,columnWidths:widths});q.borders.assign({style:'solid',fill:C.line,width:1});for(let r=0;r<data.length;r++){q.rows[r].height=h/data.length;for(let c=0;c<data[0].length;c++){let a=q.getCell(r,c);a.fill=r===0?C.ink:(r%2?'#FFFFFF':C.light);a.text.style={fontSize:z,typeface:'Segoe UI',color:r===0?'#FFFFFF':C.ink,bold:r===0,insets:8,verticalAlignment:'middle'};}}return q;}
const noteGroups=[[0],[1,2],[3],[4,5,6,7],[8,9],[10,11]];
slides.forEach((s,i)=>s.speakerNotes.text=noteGroups[i].map(n=>oldNotes[n]).join('\n\n'));

let s=slides[1];sub(s,'Platform overview and mentorship journey');
text(s,'MentorPulse connects learners with suitable mentors and gives\neach pair a shared record of their learning journey.',88,227,1104,88,30,true);
const a=node(s,'Learner\nSkills and goals',88,340,293,92,C.pale);const b=node(s,'MentorPulse\nMatching and workspace',493,340,293,92);const c=node(s,'Mentor\nExperience and availability',899,340,293,92,C.pale);link(s,a,b);link(s,c,b,'left','right');
const labels=['Profile','Discover','Request','Collaborate','Complete'],xs=[88,318,548,778,1008];const stages=labels.map((t,i)=>node(s,t,xs[i],491,184,62,i===4?C.pale:C.light,24));for(let i=0;i<4;i++)link(s,stages[i],stages[i+1]);
['Set skills, goals\nand availability','Review ranked\nmentor profiles','Mentor accepts\nor rejects','Sessions, tasks,\nresources and posts','Feedback, badges\nand certificate'].forEach((t,i)=>text(s,t,xs[i],572,184,76,22,false,C.muted,'Segoe UI','center'));

s=slides[3];sub(s,'Functional capabilities and operating rules');
text(s,'Core capabilities',88,229,327,42,27,true);text(s,'Matching and progress',472,229,337,42,27,true);text(s,'Credits and rewards',865,229,327,42,27,true);
const caps=[['Identity','Mentor, Learner or both'],['Discovery','Search, filter and rank mentors'],['Workspace','Sessions, tasks and resources'],['Engagement','Alerts, badges and leaderboard'],['Completion','Feedback and a certificate']];
caps.forEach((r,i)=>{text(s,r[0],88,287+i*53,327,28,23,true);text(s,r[1],88,315+i*53,327,35,21,false,C.muted);});
[['50%','Skill overlap'],['30%','Availability'],['20%','Experience']].forEach((r,i)=>{text(s,r[0],472,285+i*52,107,45,32,true,i===1?C.blue:C.green);text(s,r[1],592,294+i*52,217,38,23);});
text(s,'Progress calculation',472,469,337,35,24,true);text(s,'70% milestones + 30% sessions',472,509,337,57,22,false,C.muted);
table(s,[['Event','Credits'],['Registration','+50'],['Standard request','−10'],['Priority request','−15'],['Completed session','+10 to mentor']],865,283,327,256,[209,118],21);
text(s,'Rejected or cancelled requests\nreceive a refund.',865,555,327,61,21,false,C.muted);
text(s,'Local SQLite and files     Participant access checks     Uploads up to 10 MB     53 tests passed',88,624,1104,34,22,true,C.blue);
// Detailed badge thresholds and ranking formula remain available in speaker notes.
slides[3].speakerNotes.text += '\n\nDisplayed capabilities combine the functional scope with scoring, credit operations and local quality constraints. Achievement badges and the leaderboard remain part of engagement. See the rule descriptions above for all five badge thresholds and the leaderboard calculation.';

s=slides[4];sub(s,'Application layers, records and event processing');
const browser=node(s,'Presentation\nDjango templates\nBootstrap and CSS',88,242,291,132,C.light,24);
const apps=node(s,'Django 5.x domain apps\naccounts    matching\nmentorship    gamification\nnotifications',478,242,357,132,C.pale,24);
const store=node(s,'Storage\nSQLite and ORM\nLocal media files',946,242,246,132,C.light,23);link(s,browser,apps);link(s,apps,store);
text(s,'Identity',88,419,291,37,26,true);text(s,'User, Profile, Skill\nand RoleAssignment',88,464,291,75,23,false,C.muted);
text(s,'Mentorship',478,419,357,37,26,true);text(s,'Sessions, milestones, progress,\nresources and discussions',478,464,357,75,23,false,C.muted);
text(s,'Participation',946,419,246,37,26,true);text(s,'Credits, feedback,\nbadges and notifications',946,464,246,75,23,false,C.muted);
const event=node(s,'Session completed',88,559,291,60,C.light,23);const reward=node(s,'Credits and badge checks',478,559,357,60,C.pale,23);const ranked=node(s,'Ranks and notifications',946,559,246,60,C.light,22);link(s,event,reward);link(s,reward,ranked);
text(s,'Business rules and updates run synchronously in one Django project.',88,634,1104,32,22,false,C.muted);

s=slides[5];sub(s,'Local setup and demonstration checklist');
const run=['python -m pip install -r requirements.txt','python manage.py migrate','python manage.py createsuperuser','python manage.py runserver','http://127.0.0.1:8000/'];
run.forEach((cmd,i)=>{text(s,String(i+1),88,241+i*74,45,50,31,true,C.green);const q=node(s,cmd,151,234+i*74,604,61,C.light,23);q.text.style={fontSize:23,typeface:'Consolas',color:C.ink,insets:13,alignment:'left',verticalAlignment:'middle'};});
text(s,'Demonstration',822,235,370,44,27,true);
const demos=[['Prepare','Create skills, profiles and roles'],['Discover','Review a match and send a request'],['Collaborate','Accept, log a session and finish tasks'],['Verify','Check credits, feedback and certificate']];
demos.forEach((r,i)=>{text(s,r[0],822,295+i*64,370,30,23,true,C.blue);text(s,r[1],822,325+i*64,370,i===3?56:30,22,false,C.muted);});
text(s,'Validation',822,573,370,30,23,true);text(s,'python manage.py test',822,608,370,40,23,false,C.ink,'Consolas');
text(s,'Use the project folder and Python 3.10+.',151,628,604,32,22,false,C.muted);

await fs.writeFile(path.join(dir,'six-inspection.ndjson'),(await p.inspect({kind:'slide,textbox,shape,table,notes',maxChars:150000})).ndjson);
for(let i=0;i<6;i++){await fs.writeFile(path.join(dir,`six-${i+1}.png`),new Uint8Array(await (await p.export({slide:slides[i],format:'png',scale:1})).arrayBuffer()));console.log('Rendered',i+1);}
await (await PresentationFile.exportPptx(p)).save(path.join(dir,'six-candidate.pptx'));
console.log('Six-slide draft ready');
