import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Presentation, PresentationFile } from 'file:///C:/Users/babur/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
import { finalizePresentation } from 'file:///C:/Users/babur/.codex/plugins/cache/openai-primary-runtime/presentations/26.1009.11318/skills/presentations/container_tools/artifact_tool_utils.mjs';
const dir=path.dirname(fileURLToPath(import.meta.url)),root=path.dirname(dir);
const skill='C:/Users/babur/.codex/plugins/cache/openai-primary-runtime/presentations/26.1009.11318/skills/presentations';
process.env.RUNTIME_NODE_MODULES='C:/Users/babur/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const p=Presentation.create({slideSize:{width:1280,height:720}});
const C={navy:'#0B1020',ink:'#172039',muted:'#5B667C',purple:'#6D47D9',cyan:'#167C9D',light:'#F5F5F9',white:'#FFFFFF',line:'#DDDDEA'};
function text(s,t,x,y,w,h,size=26,color=C.ink,bold=false){const v=s.shapes.add({geometry:'textbox',name:t.slice(0,50),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});v.text=t;v.text.style={fontSize:size,typeface:'Arial',color,bold,insets:0,autoFit:'none',wrap:'square',verticalAlignment:'top'};return v;}
function slide(title,dark=false){let s=p.slides.add();s.background.fill=dark?C.navy:C.light;if(title)text(s,title,64,52,1152,72,44,dark?C.white:C.ink,true);text(s,'IIIT Kottayam',64,675,400,23,15,dark?'#BBC3D7':C.muted);text(s,String(p.slides.items.length).padStart(2,'0'),1164,675,50,23,15,dark?'#BBC3D7':C.muted);return s;}
function notes(s,body,files=[]){s.speakerNotes.text=body+'\n\nProject sources (reviewed 12 October 2026):\n'+files.map(f=>path.join(root,f)).join('\n');}
async function pic(s,name,x,y,w,h,fit='contain'){const bytes=await fs.readFile(path.join(dir,name));s.images.add({blob:bytes,contentType:'image/png',alt:name.replace('.png','')+' project screenshot',position:{left:x,top:y,width:w,height:h},fit});}
function table(s,data,x,y,w,h,widths){let tb=s.tables.add({rows:data.length,columns:data[0].length,left:x,top:y,width:w,height:h,values:data,columnWidths:widths});tb.borders.assign({fill:C.line,width:1,style:'solid'});for(let r=0;r<data.length;r++){tb.rows[r].height=h/data.length;for(let c=0;c<data[r].length;c++){const cell=tb.getCell(r,c);cell.fill=r===0?C.navy:(r%2?C.white:'#F0EDF8');cell.text.style={fontSize:r===0?23:23,typeface:'Arial',color:r===0?C.white:C.ink,bold:r===0,insets:14,verticalAlignment:'middle'};}}return tb;}

let s=slide('',true);await pic(s,'cover.png',0,0,1280,720,'cover');
text(s,'MentorPulse',64,178,850,100,78,C.white,true);
text(s,'Skill-based mentor matching\nand progress tracking',68,286,750,110,34,'#DAE0F0');
text(s,'GROUP 11',68,74,500,35,19,'#91D7EB',true);
text(s,'Navaneeth Krishna   /   Shivamshi Ullas\nChandhana   /   Prakshitha Pradeep',68,503,800,75,24,C.white);
text(s,'Indian Institute of Information Technology Kottayam',68,621,970,32,20,'#BBC3D7');
notes(s,'MentorPulse is a local Django project that covers mentor discovery through completion. Team names and institution follow the supplied presentation. Cover illustration generated with the built-in ImageGen tool. Prompt: two translucent violet and cyan glass ribbons ascending at right on a midnight navy background, calm negative space at left, no text. Embedded asset: '+path.join(dir,'cover.png'),['README.md','MentorPulse_Project_Description.md']);

s=slide('A shared workspace for mentorship');
text(s,'Learners find mentors by skill,\navailability and experience.',64,164,490,130,33,C.ink,true);
text(s,'Each pair can schedule sessions,\ntrack milestones and share resources\nthrough a single mentorship record.',64,318,490,152,27,C.muted);
text(s,'Local demonstration project\nFive Django domain apps',64,535,490,70,23,C.purple,true);
await pic(s,'dashboard-crop.png',586,158,630,470);
notes(s,'The product is a server-rendered local demonstration. Screenshot shows the seeded learner dashboard. Seeded accounts and scenarios are demonstration data, not real adoption metrics. The five apps are accounts, matching, mentorship, gamification and notifications.',['README.md','mentorpulse/settings.py','accounts/views.py','templates/accounts/dashboard.html']);

s=slide('Problem statement and objectives');
text(s,'Mentorship challenges',64,159,520,50,28,C.muted,true);text(s,'Project objectives',672,159,540,50,28,C.purple,true);
const problems=[['Finding a suitable mentor','Rank mentors using an explainable score'],['Keeping learning organised','Give each pair a workspace and milestones'],['Recognising contribution','Record credits, feedback and achievements'],['Showing completion','Provide a printable completion certificate']];
problems.forEach((r,i)=>{text(s,r[0],64,239+i*95,520,70,28);text(s,r[1],672,239+i*95,540,70,28);});
notes(s,'These are the project motivations and design objectives from the supplied specification, not measured findings from a user study. No survey percentages or impact claims are inferred. The certificate exists in the current code even though the early specification listed it as a stretch goal.',['MentorPulse_Project_Description.md','mentorship/views.py']);

s=slide('Functional requirements and user roles');
table(s,[['Role','Implemented capabilities'],['Learner','Browse mentors, request guidance, track learning and give feedback'],['Mentor','Review requests, log sessions and support shared milestones'],['Dual role','Hold active Mentor and Learner assignments at the same time'],['Administrator','Manage users, mentorship records and content through Django Admin']],64,164,1152,368,[240,912]);
text(s,'Operating constraints',64,570,300,42,26,C.purple,true);text(s,'Local SQLite database, local file storage, in-app notifications\nDocument uploads up to 10 MB with an extension allowlist',418,568,786,74,24,C.muted);
notes(s,'RoleAssignment stores role start and end times. Profile exposes active Mentor and Learner assignments independently. Staff access uses Django Admin. Upload validator accepts .pdf, .png, .jpg, .jpeg, .txt, .docx and .doc up to 10 MiB. The interface labels this as 10 MB. No cloud object storage, payment processor or push notification service exists.',['accounts/models.py','mentorship/forms.py','accounts/admin.py','mentorship/admin.py','mentorpulse/settings.py']);

s=slide('The mentorship lifecycle');
const steps=[['01','Discover','Set skills and goals, then review ranked mentors'],['02','Request','Send a standard or priority request with learning goals'],['03','Review','Mentor accepts or rejects the pending request'],['04','Collaborate','Use sessions, milestones, resources and discussions'],['05','Complete','Mark complete, exchange feedback and print the certificate']];
steps.forEach((r,i)=>{text(s,r[0],64,164+i*94,72,65,38,C.purple,true);text(s,r[1],174,164+i*94,240,60,30,C.ink,true);text(s,r[2],447,168+i*94,769,68,25,C.muted);});
notes(s,'States in code: PENDING, ACTIVE, COMPLETED, REJECTED and CANCELLED. Requests block self-matching, require an active mentor role, and reject duplicate pending or active pairs. Rejected or cancelled requests refund the learner. Either participant or staff can access the workspace. Current completion view permits any authorised participant to mark an active mentorship completed and then forces progress to 100%.',['mentorship/models.py','mentorship/views.py','gamification/services.py']);

s=slide('Transparent matching rules',true);
[['50%','Skill overlap','Shared skills divided by\nthe learner’s selected skills'],['30%','Availability','Exact match, flexible schedule\nor a lower compatibility score'],['20%','Experience','Highest affinity when the mentor\nis one or two levels ahead']].forEach((r,i)=>{let x=64+i*394;text(s,r[0],x,175,360,102,74,i===1?'#88D9EE':'#C3AFFA',true);text(s,r[1],x,303,360,47,30,C.white,true);text(s,r[2],x,371,360,100,24,'#C3CCDE');});
text(s,'72% example',64,549,340,63,39,C.white,true);text(s,'2 of 4 skills: 25 points   +   flexible: 27   +   one level ahead: 20',414,550,795,68,24,'#C3CCDE');
notes(s,'Deterministic matching, not a trained AI model. Total = round(skill_ratio*50 + availability_ratio*30 + experience_ratio*20), clamped 0 to 100. Availability ratios: exact non-empty match 1.0, either flexible 0.9, missing 0.6, incompatible 0.2. Experience gaps +1/+2 score 1.0, +3 scores 0.9, equal levels 0.65, mentor lower 0.25. Skills default to 0.5 if none selected. Tie-breaking uses mentor profile skill_score. Illustrative example is calculated from these rules, not an observed match.',['matching/services.py','matching/views.py']);

s=slide('A workspace for each mentorship');
await pic(s,'workspace-crop.png',64,159,784,475);
text(s,'Scheduled sessions',889,166,327,42,27,C.purple,true);text(s,'Date, agenda and an\nexternal meeting link',889,222,327,78,24,C.muted);
text(s,'Shared learning',889,332,327,42,27,C.purple,true);text(s,'Milestone checklist, files,\nlinks and discussion posts',889,389,327,81,24,C.muted);
text(s,'Participant access',889,502,327,42,27,C.purple,true);text(s,'Mentor, learner or staff',889,559,327,50,24,C.muted);
notes(s,'Screenshot: active seeded mentorship between Alex Rivera and Sarah Connor. Session records store meeting URLs, not integrated video calls. DiscussionPost is an asynchronous thread, not websocket chat. Workspace permission checks rely on Mentorship.can_access. Resource upload validation lives in mentorship/forms.py.',['mentorship/models.py','mentorship/views.py','templates/mentorship/workspace.html']);

s=slide('Progress combines milestones and sessions');
text(s,'70%',64,169,480,100,76,C.purple,true);text(s,'Milestone completion',64,291,500,53,30,C.ink,true);text(s,'2 completed out of 3\ncontributes 46.7 percentage points',64,357,510,91,25,C.muted);
text(s,'30%',672,169,510,100,76,C.cyan,true);text(s,'Session completion',672,291,510,53,30,C.ink,true);text(s,'1 completed out of 2\ncontributes 15 percentage points',672,357,510,91,25,C.muted);
text(s,'61.7%',64,521,304,97,66,C.ink,true);text(s,'Active demo progress\n70 × (2/3) + 30 × (1/2)',418,524,794,93,30,C.muted);
notes(s,'Current active demo database stores 61.7%, not the 67% claimed in README and the older slide deck. Formula when both record types exist: 70*(completed milestones/total milestones)+30*(completed sessions/total sessions). When only one type exists it receives 100% weight. No records means 0%. Marking COMPLETED forces 100%, regardless of remaining checklist items. This is a workflow completion signal, not a verified competency assessment.',['mentorship/models.py','accounts/management/commands/seed_demo_data.py']);

s=slide('Credits record participation');
table(s,[['Event','Credits'],['New account','+50'],['Standard request','−10'],['Priority request','−15 total'],['Completed session','+10 to mentor'],['Rejection or cancellation','Request fee refunded']],64,169,631,377,[429,202]);
await pic(s,'wallet-crop.png',740,169,476,377);
text(s,'Every automated change creates a ledger entry.\nCredits are internal points with no monetary value.',64,580,1152,66,25,C.muted);
notes(s,'Priority costs 10 standard plus 5 extra. Priority request ordering is -is_priority then -id, with a visible flag. CreditService records starting bonus, request deduction, priority unlock, refunds and completed-session rewards. Refund and session reward services check a context string to prevent duplicates. This does not prove concurrency safety. Screenshot shows the demo learner wallet.',['gamification/models.py','gamification/services.py','gamification/signals.py','mentorship/views.py']);

s=slide('Achievements and the leaderboard');
table(s,[['Badge','Current rule'],['First Steps','Complete 1 mentorship'],['Committed Mentor','Complete 2 as mentor'],['Rising Star','Skill score at least 8.0'],['Top Rated','Average at least 4.5, with 1+ review'],['Helpful Hand','Share 2 resources']],64,164,699,423,[273,426]);
text(s,'Leaderboard score',812,171,404,54,30,C.purple,true);text(s,'10 × skill score\n+ 0.5 × credit balance\n+ 15 × badge count',812,267,404,175,30,C.ink,true);
text(s,'Ranks recalculate on\nrelevant application events.',812,500,404,88,25,C.muted);
notes(s,'These are implemented rules in BadgeService, which supersede the original specification thresholds of 5 completed mentorships, skill score >80, 5 ratings and 5 resources. First Steps checks completed mentorships despite a badge description mentioning a milestone. Skill score is a stored profile value rather than an automatic mastery score. LeaderboardService iterates all active users, calculates the score and assigns consecutive ranks after sorting. No background job or push leaderboard exists.',['gamification/services.py','accounts/models.py']);

s=slide('System architecture');
table(s,[['Layer','Implementation'],['Presentation','Django templates, Bootstrap 5.3.3 and custom CSS'],['Application','Django 5.x with authentication, ORM and migrations'],['Domain logic','Python services and view handlers run synchronously'],['Persistence','SQLite database and local media files']],64,164,1152,335,[278,874]);
text(s,'Five domain apps',64,542,350,48,28,C.purple,true);text(s,'accounts    matching    mentorship\ngamification    notifications',418,542,797,83,27,C.ink);
notes(s,'Single Django project organised into five apps, not microservices. requirements.txt constrains Django >=5.0,<6.0. The local runtime test reports Django 5.2.17. Bootstrap version 5.3.3 appears in templates/base.html. Django auth User provides authentication, extended by Profile and RoleAssignment. Credit is a wallet model and is not an authentication model. Server-rendered HTTP requests execute synchronous business logic. No Celery, Redis, REST frontend or cloud dependency exists.',['requirements.txt','mentorpulse/settings.py','mentorpulse/urls.py','templates/base.html']);

s=slide('Core data relationships');
table(s,[['Domain','Relationships'],['Identity','User has one Profile and multiple RoleAssignments'],['Skills','Profile and Skill share a many-to-many relationship'],['Mentorship','Mentor and learner reference User, with one Progress record'],['Collaboration','Mentorship has sessions, milestones, resources and posts'],['Participation','User has one credit wallet, transactions and earned badges'],['Feedback and alerts','Feedback links a pair and reviewers, notifications belong to User']],64,160,1152,465,[278,874]);
notes(s,'Core relationship summary from current Django models. Mentorship has two user foreign keys (mentor and learner). Progress has a OneToOne relationship to Mentorship. Resource records uploaded_by. Feedback has unique_together on mentorship and given_by. UserBadge has unique_together on user and badge. LeaderboardEntry has one user record in the current implementation rather than the separate Leaderboard entity proposed in the initial specification.',['accounts/models.py','mentorship/models.py','gamification/models.py','notifications/models.py']);

s=slide('Automated validation');
text(s,'53',64,190,344,130,104,C.purple,true);text(s,'tests passed',68,347,342,58,34,C.ink,true);text(s,'12 October 2026\nDjango system checks: no issues',68,451,359,100,24,C.muted);
table(s,[['App','Tests','Coverage examples'],['accounts','12','Profiles, roles and authentication'],['matching','10','Scoring, ranking and filters'],['mentorship','7','Request flow, access and completion'],['gamification','18','Credits, badges, ratings and ranks'],['notifications','6','Inbox and read state']],464,168,752,406,[190,99,463]);
text(s,'Functional test coverage does not establish production readiness.',464,598,752,47,23,C.muted);
notes(s,'Executed python manage.py test --noinput against this workspace. Result: Ran 53 tests in 46.340s, OK, system check identified no issues (0 silenced). Per-app counts obtained from test methods in the current source: accounts 12, matching 10, mentorship 7, gamification 18, notifications 6. These tests verify selected functionality. The project has development settings and no load, security or deployment certification.',['accounts/tests.py','matching/tests.py','mentorship/tests.py','gamification/tests.py','notifications/tests.py']);

s=slide('Demonstration walkthrough');
const demos=[['Alex Rivera','Review mentor matches, then open the\nactive workspace at 61.7% progress'],['Jordan Lee','Show the pending priority request\nand its 15-credit cost'],['Priya Sharma','Open the completed mentorship\nand print the certificate']];
demos.forEach((r,i)=>{text(s,r[0],64,164+i*143,533,46,29,C.purple,true);text(s,r[1],64,220+i*143,533,81,25,C.muted);});
await pic(s,'certificate-crop.png',647,162,569,442);
text(s,'Demo Switcher supports role changes while DEBUG is enabled.',647,615,569,46,20,C.muted);
notes(s,'All named people are seeded demo accounts. Active scenario: sarah_backend / alex_learner. Priority pending scenario: jordan_learner / sarah_backend. Completed scenario: marcus_frontend / priya_learner. Screenshot captures the certificate for the completed pair. Start with dependencies installed, then python manage.py migrate, python manage.py seed_demo_data and python manage.py runserver. Windows scripts debug.bat and run_demo.bat automate local setup. The seeder deletes and rebuilds demonstration scenarios, so use it with demo data. Demo switching is gated by settings.DEBUG.',['accounts/management/commands/seed_demo_data.py','accounts/views.py','run_demo.bat','mentorship/views.py','templates/mentorship/certificate.html']);

s=slide('Current scope and future improvements');
text(s,'Current local scope',64,164,533,54,30,C.ink,true);text(s,'SQLite and local file uploads\n\nIn-app alerts on page refresh\n\nManual dates and external meeting links\n\nCompletion status unlocks the certificate',64,247,533,335,27,C.muted);
text(s,'Proposed next steps',672,164,544,54,30,C.purple,true);text(s,'Harden settings and remove demo access\n\nAdd atomic credit transactions\n\nRequire completion criteria for certificates\n\nEvaluate matching quality with user feedback',672,247,544,335,27,C.muted);
notes(s,'Proposed steps are recommendations, not implemented features or existing project commitments. Current DEBUG=True settings, a development secret and empty ALLOWED_HOSTS suit local demonstration only. Browser bootstrap assets come from public CDNs. Notifications use database records and request-time rendering, with no websocket or background reminder scheduler. Credit operations have duplicate checks but no transaction.atomic wrapper in current services. Certificate completion can be set by a participant before checklist completion. Real payments, native video integration, automated calendar sync and cloud hosting are outside the agreed local project scope.',['mentorpulse/settings.py','accounts/views.py','gamification/services.py','notifications/services.py','notifications/context_processors.py','mentorship/views.py','MentorPulse_Project_Description.md']);

s=slide('',true);await pic(s,'cover.png',0,0,1280,720,'cover');
text(s,'Mentorship with\na visible learning record',64,157,971,161,57,C.white,true);
text(s,'Explainable mentor discovery\nShared learning workspaces\nRecorded participation and completion',68,380,850,165,31,'#CDD6E8');
text(s,'Thank you',68,596,750,54,34,'#91D7EB',true);
notes(s,'The demonstrated outcome is a complete local workflow from matching to completion, with 53 passing functional tests. No learning impact, adoption or scalability outcome has been measured.',['README.md','mentorship/models.py','matching/services.py']);

await fs.writeFile(path.join(dir,'content-inspection.ndjson'),(await p.inspect({kind:'slide,textbox,table,notes',maxChars:150000})).ndjson);
for(let i=0;i<p.slides.items.length;i++){await fs.writeFile(path.join(dir,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await (await p.export({slide:p.slides.items[i],format:'png',scale:1})).arrayBuffer()));console.log('Rendered',i+1);}
const candidate=path.join(dir,'candidate.pptx');await (await PresentationFile.exportPptx(p)).save(candidate);
console.log('Draft exported');
const result=await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:path.join(root,'output/presentations/MentorPulse_Refactored.pptx'),pythonExecutable:'C:/Users/babur/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit'],fontPolicy:{basis:'design',families:['Arial']},requiredNativeTableOwnerSlides:[4,9,10,11,12,13],explicitTotalSlideCount:16,verifyArtifactToolImport:true,receiptPath:path.join(dir,'validation.json')});
console.log(JSON.stringify(result));
