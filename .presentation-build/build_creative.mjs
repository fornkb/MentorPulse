import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {PresentationFile,FileBlob} from 'file:///C:/Users/babur/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const dir=path.dirname(fileURLToPath(import.meta.url)),root=path.dirname(dir);
const p=await PresentationFile.importPptx(await FileBlob.load('C:/Users/babur/Downloads/Project Presentation Template.pptx'));
const base=[...p.slides.items];
// Duplicate the original blank slides to retain each section's logo and footer.
const order=[base[0],base[1],base[1].duplicate(),base[2],base[3],base[3].duplicate(),base[3].duplicate(),base[3].duplicate(),base[4],base[4].duplicate(),base[5],base[5].duplicate()];
order.forEach((s,i)=>s.moveTo(i));
const C={ink:'#213B57',muted:'#596B7C',green:'#138B5D',blue:'#2676AD',line:'#C7D4DE',pale:'#F0F7F4',light:'#F2F6FA'};
function text(s,t,x,y,w,h,z=25,bold=false,color=C.ink,font='Segoe UI',align='left') { const q=s.shapes.add({geometry:'textbox',name:t.slice(0,50),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});q.text=t;q.text.style={fontSize:z,typeface:font,color,bold,insets:0,autoFit:'none',wrap:'square',alignment:align,verticalAlignment:'top'};return q; }
function node(s,t,x,y,w,h,fill=C.light,color=C.ink,z=25){const q=s.shapes.add({geometry:'roundRect',name:t.replaceAll('\n',' '),position:{left:x,top:y,width:w,height:h},fill,line:{fill:C.line,width:1.3},borderRadius:10});q.text=t;q.text.style={fontSize:z,typeface:'Segoe UI',color,bold:true,insets:12,alignment:'center',verticalAlignment:'middle',autoFit:'none'};return q;}
function link(s,a,b,from='right',to='left',color=C.blue,kind='straight'){return s.shapes.connect(a,b,{kind,fromSide:from,toSide:to,line:{fill:color,width:2.4},tail:{type:'triangle',width:'sm',length:'sm'}});}
function note(s,t,files=[]){s.speakerNotes.text=t+'\n\nProject sources (reviewed 12 October 2026):\n'+files.map(f=>path.join(root,f)).join('\n');}
function frame(s,i,sub){s.background.fill='#FFFFFF';for(const q of s.shapes.items){if(q.name?.startsWith('Content Placeholder'))q.text='';if(q.name?.startsWith('Slide Number'))q.text=String(i+1);if(q.name==='Title 1'&&i){q.position={left:88,top:80,width:1104,height:70};q.text.style={typeface:'Calibri Light',fontSize:44,color:'#000000',insets:0,autoFit:'none'};}}if(sub)text(s,sub,88,168,1104,40,25,true,C.green);}
function metric(s,value,label,x,y,w=330){text(s,value,x,y,w,78,58,true,C.green);text(s,label,x,y+85,w,67,23,false,C.muted);}
function tbl(s,data,x,y,w,h,widths){const q=s.tables.add({rows:data.length,columns:data[0].length,left:x,top:y,width:w,height:h,values:data,columnWidths:widths});q.borders.assign({style:'solid',fill:C.line,width:1});for(let r=0;r<data.length;r++){q.rows[r].height=h/data.length;for(let c=0;c<data[0].length;c++){const cell=q.getCell(r,c);cell.fill=r===0?C.ink:(r%2?'#FFFFFF':C.light);cell.text.style={fontSize:23,typeface:'Segoe UI',color:r===0?'#FFFFFF':C.ink,bold:r===0,insets:10,verticalAlignment:'middle'};}}return q;}
order.forEach((s,i)=>frame(s,i,''));

let s=order[0];
let title=s.shapes.items.find(q=>q.text.toString()==='Project Title');title.text='MentorPulse';title.position={left:160,top:232,width:960,height:118};title.text.style={fontSize:82,typeface:'Calibri Light',color:C.ink,alignment:'center',insets:0};
let names=s.shapes.items.find(q=>q.text.toString().includes('Name of all'));names.text='Navaneeth Krishna    Shivamshi Ullas\nChandhana    Prakshitha Pradeep';names.position={left:160,top:458,width:960,height:98};names.text.style={fontSize:29,typeface:'Segoe UI',color:C.ink,alignment:'center',italic:false,insets:0};
let team=s.shapes.items.find(q=>q.text.toString()==='Team Number');team.text='Group 11';team.position={left:160,top:584,width:960,height:50};team.text.style={fontSize:25,typeface:'Segoe UI',alignment:'center',color:C.muted,insets:0};
text(s,'Skill-based mentor matching and progress tracking',160,362,960,76,33,false,C.green,'Segoe UI','center');
note(s,'Local Django mentorship platform. Team identity and institute branding follow the supplied presentation.',['README.md','MentorPulse_Project_Description.md']);

s=order[1];frame(s,1,'Platform overview');
text(s,'MentorPulse connects learners with mentors and gives\neach pair a shared record of their learning journey.',88,231,1104,92,32,true);
const a=node(s,'Learner\nSkills and learning goals',88,371,293,116,C.pale);const b=node(s,'MentorPulse\nMatching and workspace',493,371,293,116);const c=node(s,'Mentor\nExperience and availability',899,371,293,116,C.pale);link(s,a,b);link(s,c,b,'left','right');
text(s,'Discovery',88,541,300,43,27,true,C.blue);text(s,'Rank suitable mentors\nwith an explainable score',88,590,340,63,23,false,C.muted);
text(s,'Collaboration',493,541,300,43,27,true,C.blue);text(s,'Keep sessions and milestones\nin a shared workspace',493,590,340,63,23,false,C.muted);
text(s,'Recognition',899,541,293,43,27,true,C.blue);text(s,'Record feedback, credits\nand completion',899,590,293,63,23,false,C.muted);
note(s,'Profile stores skills, goals, experience and availability. Users may hold Mentor and Learner roles concurrently. This diagram shows the product relationship, not external services.',['accounts/models.py','matching/services.py','mentorship/models.py']);

s=order[2];frame(s,2,'Mentorship workflow');
const xs=[88,318,548,778,1008];const labels=['Profile','Discover','Request','Collaborate','Complete'];let ns=[];
labels.forEach((t,i)=>ns.push(node(s,t,xs[i],269,184,85,i===4?C.pale:C.light)));for(let i=0;i<4;i++)link(s,ns[i],ns[i+1]);
['Set skills, goals\nand availability','Compare ranked\nmentor profiles','Submit goals for\nmentor review','Log sessions,\nresources and tasks','Receive feedback\nand a certificate'].forEach((t,i)=>text(s,t,xs[i],375,184,96,23,false,C.muted,'Segoe UI','center'));
text(s,'Request states',88,523,253,48,27,true,C.ink);
const pending=node(s,'Pending',363,518,210,68);const active=node(s,'Active',671,518,210,68,C.pale);const done=node(s,'Completed',982,518,210,68,C.pale);link(s,pending,active);link(s,active,done);
text(s,'Rejection or cancellation refunds the request fee.',363,611,829,37,24,false,C.muted);
note(s,'Request validation blocks self-requests, requires an active mentor, prevents duplicate active/pending pairs and checks credits. Mentor acceptance creates an active workspace. States also include REJECTED and CANCELLED. Any authorised participant or staff can mark an active mentorship complete.',['mentorship/views.py','mentorship/models.py','gamification/services.py']);

s=order[3];frame(s,3,'Problems and the corresponding objectives');
const pairs=[['Finding a suitable mentor','Rank candidates by skills, availability\nand experience'],['Keeping mentorship organised','Give each pair sessions, milestones\nand shared learning resources'],['Recognising participation','Record credits, reviews and\nachievement badges'],['Showing completion','Unlock a printable certificate\nwhen mentorship is completed']];
text(s,'Problem',88,229,421,44,28,true);text(s,'Objective',671,229,521,44,28,true,C.green);
pairs.forEach((r,i)=>{let y=303+i*85;let l=node(s,r[0],88,y,421,64,'#FFFFFF',C.ink,25);let rt=node(s,r[1],671,y-3,521,72,C.pale,C.ink,24);link(s,l,rt);});
note(s,'Design objectives from the project specification. These are motivations, not measured survey findings or claims of learning impact.',['MentorPulse_Project_Description.md','mentorship/views.py']);

s=order[4];frame(s,4,'Functional requirements');
tbl(s,[['Capability','Implemented behaviour'],['Identity and roles','Register, sign in and activate Mentor or Learner roles'],['Mentor discovery','Search and filter profiles, then rank compatibility'],['Mentorship workspace','Sessions, milestones, resources and discussions'],['Participation','Credits, ratings, badges and the leaderboard'],['Communication','In-app notifications with read state and destination links'],['Completion','Mark the mentorship complete and print a certificate']],88,236,1104,379,[315,789]);
text(s,'Learners and mentors can both contribute to the shared workspace.',88,632,1104,30,22,false,C.muted);
note(s,'Dual roles use RoleAssignment records. Resources include links, files and notes. Notifications are database records rendered with HTTP requests, not pushed websocket events. Certificates reflect workflow completion.',['accounts/models.py','matching/views.py','mentorship/models.py','notifications/views.py','gamification/views.py']);

s=order[5];frame(s,5,'Matching and progress calculations');
text(s,'Compatibility score',88,230,505,42,28,true);text(s,'Learning progress',687,230,505,42,28,true);
[['50%','Skill overlap'],['30%','Availability'],['20%','Experience']].forEach((r,i)=>{text(s,r[0],88,297+i*79,166,66,43,true,i===1?C.blue:C.green);text(s,r[1],270,310+i*79,323,46,27);});
text(s,'2 of 4 skills, a flexible schedule and\na mentor one level ahead gives 72%.',88,566,505,73,24,false,C.muted);
const m=node(s,'Milestones\n70% weight',687,294,224,119,C.pale);const se=node(s,'Sessions\n30% weight',968,294,224,119);const total=node(s,'Weighted progress',795,476,289,70,C.light);link(s,m,total,'bottom','top',C.green,'elbow');link(s,se,total,'bottom','top',C.blue,'elbow');
text(s,'Example: 2 of 3 milestones and 1 of 2 sessions\n70 × (2/3) + 30 × (1/2) = 61.7%',687,571,505,78,24,false,C.muted);
note(s,'Illustrative arithmetic examples, not seeded-user scenarios. Matching total is round(skill overlap*50 + availability ratio*30 + experience ratio*20), clamped 0–100. Availability ratios: exact 1, flexible .9, missing .6, incompatible .2. Experience affinity: +1/+2 tiers 1, +3 .9, same .65, lower .25. Skill overlap uses shared skills / learner skills, or .5 when none selected. Progress uses 70/30 when both types exist, 100% for the only existing type, 0% for no records. COMPLETED forces100%, rather than assessing competency.',['matching/services.py','mentorship/models.py']);

s=order[6];frame(s,6,'Credits, achievements and ranking');
tbl(s,[['Event','Credits'],['New account','+50'],['Standard request','−10'],['Priority request','−15 total'],['Completed session','+10 to mentor'],['Rejected / cancelled','Request fee refunded']],88,235,513,350,[296,217]);
text(s,'Achievement rules',667,232,525,48,28,true);
const badges=[['First Steps','1 completed mentorship'],['Committed Mentor','2 completed as mentor'],['Rising Star','Skill score at least 8.0'],['Top Rated','Average 4.5+, with 1+ review'],['Helpful Hand','2 shared resources']];badges.forEach((r,i)=>{text(s,r[0],667,295+i*54,254,47,23,true);text(s,r[1],932,295+i*54,260,48,22,false,C.muted);});
text(s,'Leaderboard = 10 × skill score + 0.5 × credits + 15 × badges',88,607,1104,46,27,true,C.blue);
note(s,'Credits have no monetary value. Priority costs10 plus5. Automatic wallet operations create CreditTransaction records. Refunds and completed-session rewards include context-based duplicate guards. BadgeService uses the shown thresholds, superseding the earlier specification. First Steps checks mentorship completion, not a single milestone. Skill score is a stored profile value. Leaderboard recalculates at relevant events and when its page opens.',['gamification/services.py','gamification/models.py','gamification/signals.py','gamification/views.py']);

s=order[7];frame(s,7,'Non-functional requirements and validation');
const qualities=[['Local execution','SQLite database and local file storage'],['Controlled access','Django sign-in and participant checks'],['Upload validation','10 MB limit and an allowed file extension list'],['Traceability','Credit transactions and recorded feedback']];qualities.forEach((r,i)=>{text(s,r[0],88,239+i*98,503,46,28,true,C.ink);text(s,r[1],88,283+i*98,503,65,23,false,C.muted);});
metric(s,'53','Automated tests passed',687,231,505);
tbl(s,[['App','Tests'],['accounts','12'],['matching','10'],['mentorship','7'],['gamification','18'],['notifications','6']],687,407,505,233,[340,165]);
note(s,'Test command python manage.py test --noinput ran successfully earlier in this presentation task:53 tests, OK, no system check issues. Counts come from current test methods. Upload validator allows .pdf,.png,.jpg,.jpeg,.txt,.docx,.doc and checks 10*1024*1024 bytes. Authentication and participant checks exist, but no production security review or load test is claimed. Settings DEBUG=True suit local development. Proposed future hardening includes disabling demo switching, atomic credit writes, stricter completion criteria and deployment configuration.',['mentorship/forms.py','mentorship/models.py','mentorpulse/settings.py','accounts/tests.py','matching/tests.py','mentorship/tests.py','gamification/tests.py','notifications/tests.py']);

s=order[8];frame(s,8,'Application layers and domain modules');
const browser=node(s,'Browser\nServer-rendered pages',88,247,281,98,C.light);
const web=node(s,'Django presentation\nTemplates and Bootstrap',88,397,281,113,C.light);link(s,browser,web,'bottom','top');
const apps=node(s,'Domain apps\naccounts    matching\nmentorship    gamification\nnotifications',480,365.5,355,176,C.pale,C.ink,25);link(s,web,apps,'right','left');
const data=node(s,'Persistence\nSQLite and Django ORM',946,250,246,119,C.light,C.ink,24);const files=node(s,'Local media\nUploaded learning resources',946,439,246,119,C.light,C.ink,24);link(s,apps,data,'right','left',C.blue,'elbow');link(s,apps,files,'right','left',C.green,'elbow');
text(s,'A single Django project keeps authentication, business rules and data together.',88,604,1104,60,25,false,C.muted);
note(s,'Native architecture diagram represents implemented local system. Templates use Bootstrap5.3.3 and custom CSS. Django5.x requirement. Five apps run in one process with synchronous request handlers. SQLite and local MEDIA_ROOT provide storage. Bootstrap and font files normally load from public CDNs. External meeting links are fields, not video integrations.',['mentorpulse/settings.py','mentorpulse/urls.py','templates/base.html','requirements.txt']);

s=order[9];frame(s,9,'Core records and event flow');
const user=node(s,'User\nProfile and role assignments',88,241,292,104,C.pale);const match=node(s,'Mentorship\nMentor and learner',494,241,292,104,C.pale);const related=node(s,'Learning records\nProgress, sessions and milestones',899,241,293,104,C.light,C.ink,23);link(s,user,match);link(s,match,related);
text(s,'User owns a credit wallet\nand earned badges',88,379,292,85,24,false,C.muted);text(s,'Resources and discussion\nposts belong to a mentorship',494,379,292,92,24,false,C.muted);text(s,'Milestone and session states\ndrive weighted progress',899,379,293,92,24,false,C.muted);
const event=node(s,'Session completed',88,529,292,70,C.light);const reward=node(s,'Credits and badge checks',494,529,292,70,C.pale,C.ink,23);const notify=node(s,'Ranking and notifications',899,529,293,70,C.light,C.ink,23);link(s,event,reward);link(s,reward,notify);
text(s,'Updates run synchronously in application handlers.',88,623,1104,35,24,false,C.muted);
note(s,'Conceptual relationship diagram: Mentorship references two User records. Profile is one-to-one to User, RoleAssignment is many-to-one. Progress is one-to-one to Mentorship. Sessions,milestones,resources and posts have foreign keys to Mentorship. Completion handler invokes reward service and recalculates progress. Reward service checks badges and refreshes ranks; notification helper records events. Updates need no background queue.',['accounts/models.py','mentorship/models.py','mentorship/views.py','gamification/services.py','notifications/services.py']);

s=order[10];frame(s,10,'How to install and run locally');
const run=[['1','Install dependencies','python -m pip install -r requirements.txt'],['2','Apply the database schema','python manage.py migrate'],['3','Create an admin account','python manage.py createsuperuser'],['4','Start the application','python manage.py runserver'],['5','Open in the browser','http://127.0.0.1:8000/']];
run.forEach((r,i)=>{text(s,r[0],88,232+i*78,61,62,39,true,C.green);text(s,r[1],175,235+i*78,403,53,27,true);const q=node(s,r[2],617,229+i*78,575,63,C.light,C.ink,23);q.text.style={fontSize:23,typeface:'Consolas',color:C.ink,insets:13,alignment:'left',verticalAlignment:'middle'};});
text(s,'Run commands from the project folder after installing Python 3.10+.',175,626,1017,35,23,false,C.muted);
note(s,'requirements.txt installs Django>=5.0,<6.0 plus asgiref,sqlparse,tzdata and Pillow. Python3.10+ is named in README and launcher. Optional virtual environment: python -m venv .venv, then on Windows .venv\\Scripts\\activate or Unix source .venv/bin/activate. Skills taxonomy and mentor profiles can be managed through Django Admin at /admin/ after python manage.py createsuperuser. Run setup commands from the project directory.',['README.md','requirements.txt','manage.py','debug.bat']);

s=order[11];frame(s,11,'Live demonstration sequence and expected results');
const demo=[['Prepare','Create skills in Django Admin. Register a learner and\na mentor, then complete their profiles and roles.'],['Discover','Open /mentors/, filter by skill and inspect the\ncompatibility breakdown before sending a request.'],['Collaborate','Accept the request. Add a session and milestone,\nthen mark each complete and share a resource.'],['Verify','Check progress and the wallet ledger. Submit feedback,\ncomplete the mentorship and print its certificate.']];
demo.forEach((r,i)=>{text(s,String(i+1).padStart(2,'0'),88,240+i*92,72,53,34,true,C.green);text(s,r[0],192,241+i*92,231,52,27,true);text(s,r[1],458,240+i*92,734,80,25,false,C.muted);});
text(s,'Validation command',88,615,334,42,25,true,C.blue);text(s,'python manage.py test',458,615,734,42,26,false,C.ink,'Consolas');
note(s,'Create the skill taxonomy and any required profile data through Django Admin after creating a superuser. Registration creates a profile and starting credit wallet. Activate roles through profile controls. Expected standard request costs10,priority15, mentor completion reward10, refund on rejection/cancellation. Milestone/session update changes weighted progress. Completion unlocks certificate. Test command checks current functional suite;53 tests passed during this task. Sessions support external meeting URLs.',['accounts/forms.py','accounts/views.py','accounts/admin.py','matching/views.py','mentorship/views.py','gamification/services.py','mentorship/tests.py']);

for(let i=0;i<order.length;i++){await fs.writeFile(path.join(dir,`creative-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await (await p.export({slide:order[i],format:'png',scale:1})).arrayBuffer()));console.log('Rendered',i+1);}
await (await PresentationFile.exportPptx(p)).save(path.join(dir,'creative-candidate.pptx'));
console.log('Creative template draft exported');
