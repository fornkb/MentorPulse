import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {PresentationFile,FileBlob} from 'file:///C:/Users/babur/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
import {finalizePresentation} from 'file:///C:/Users/babur/.codex/plugins/cache/openai-primary-runtime/presentations/26.1009.11318/skills/presentations/container_tools/artifact_tool_utils.mjs';
const dir=path.dirname(fileURLToPath(import.meta.url)),root=path.dirname(dir);
const source='C:/Users/babur/Downloads/Project Presentation Template.pptx';
const skill='C:/Users/babur/.codex/plugins/cache/openai-primary-runtime/presentations/26.1009.11318/skills/presentations';
process.env.RUNTIME_NODE_MODULES='C:/Users/babur/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const p=await PresentationFile.importPptx(await FileBlob.load(source));
function txt(s,t,x,y,w,h,size=30,bold=false){const v=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});v.text=t;v.text.style={typeface:'Calibri',fontSize:size,color:'#000000',bold,alignment:'left',verticalAlignment:'top',insets:0,wrap:'square',autoFit:'none'};return v;}
function note(s,t,files){s.speakerNotes.text=t+'\n\nProject sources reviewed 12 October 2026:\n'+files.map(f=>path.join(root,f)).join('\n');}
function body(s){return s.shapes.items.find(v=>v.name?.startsWith('Content Placeholder'));}
let s=p.slides.items[0];
s.shapes.items.find(v=>v.text.toString()==='Project Title').text='MentorPulse';
s.shapes.items.find(v=>v.text.toString().includes('Name of all')).text='BY\nNavaneeth Krishna, Shivamshi Ullas\nChandhana, Prakshitha Pradeep';
s.shapes.items.find(v=>v.text.toString()==='Team Number').text='Team 11';
note(s,'MentorPulse: skill-based mentor matching and progress tracking. Team names follow the supplied presentation. Local demonstration project with five Django domain apps.',['README.md','MentorPulse_Project_Description.md']);

s=p.slides.items[1];
const intro=body(s);intro.text='MentorPulse connects learners with suitable mentors and manages the mentorship journey in one local web application.';
intro.position={left:88,top:192,width:1104,height:100};intro.text.style={fontSize:32,typeface:'Calibri',color:'#000000',insets:0,autoFit:'none'};
const info=[['Matching','Rule-based score: 50% skills, 30% availability, 20% experience'],['Collaboration','Sessions, milestones, shared resources and asynchronous discussions'],['Recognition','Credit ledger, feedback, badges and printable completion certificates'],['Implementation','Django 5.x, SQLite and five domain apps with 53 passing tests']];
info.forEach((r,i)=>{txt(s,r[0],88,325+i*75,245,45,30,true);txt(s,r[1],342,325+i*75,850,60,29);});
note(s,'Matching is deterministic, not a trained AI model. Availability and experience use discrete rules. Notifications and leaderboard updates are synchronous application events, not pushed real-time updates. Certificates exist in the current implementation. Executed python manage.py test --noinput on 12 October 2026: 53 tests passed, no system check issues.',['matching/services.py','mentorship/models.py','gamification/services.py','notifications/services.py','requirements.txt','README.md']);

s=p.slides.items[2];body(s).text='';
txt(s,'Problem statement',88,204,514,55,34,true);
txt(s,'Learners need a mentor whose skills,\navailability and experience fit their goals.\n\nMentorship needs shared tools for\nsessions and visible learning progress.',88,277,518,245,30);
txt(s,'Objectives',668,204,524,55,34,true);
[['1','Rank mentors with a transparent\ncompatibility score'],['2','Keep sessions, milestones and\nresources in a shared workspace'],['3','Record participation with credits,\nfeedback and achievements'],['4','Recognise completion with a\nprintable certificate']].forEach((r,i)=>{txt(s,r[0],668,277+i*86,44,60,30,true);txt(s,r[1],729,277+i*86,463,77,30);});
note(s,'These are project motivations and objectives, not quantified results from a user study. The current implementation supports Mentor and Learner roles simultaneously through separate RoleAssignment records. Standard mentorship flow: discover, request, accept or reject, collaborate, complete.',['MentorPulse_Project_Description.md','accounts/models.py','mentorship/views.py']);

s=p.slides.items[3];body(s).text='';
txt(s,'Functional',88,235,514,49,32,true);txt(s,'Non-functional',668,235,524,49,32,true);
txt(s,'Accounts and roles\nSign in as a Mentor, Learner or both\n\nMatching and collaboration\nRank mentors, review requests and track progress\n\nParticipation and completion\nCredits, badges, feedback and a certificate',88,300,515,337,28);
txt(s,'Local operation\nSQLite database and local media storage\n\nAccess and uploads\nAuthentication and participant access checks\nFiles up to 10 MB with an extension allowlist\n\nValidation and traceability\n53 passing tests and a credit ledger',668,300,524,337,28);
note(s,'Credit rules in current code: +50 starting credits, -10 for a standard request, -15 total for priority, +10 to mentor per completed session, request fee refunded on rejection/cancellation. Badge thresholds: First Steps one completed mentorship, Committed Mentor two completed as mentor, Rising Star skill_score >=8.0, Top Rated average >=4.5 with at least one review, Helpful Hand at least two resources. Leaderboard = skill_score*10 + credit_balance*0.5 + badge_count*15. Extension allowlist: .pdf, .png, .jpg, .jpeg, .txt, .docx and .doc, limit 10 MiB. Development settings and demo switching require hardening before production.',['accounts/models.py','mentorship/forms.py','mentorship/models.py','gamification/services.py','mentorpulse/settings.py']);

s=p.slides.items[4];body(s).text='';
const rows=[['Presentation layer','Django templates, Bootstrap 5.3.3 and custom CSS'],['Application layer','Django authentication, ORM, views and Python services'],['Data layer','SQLite database and local files for uploaded resources']];
rows.forEach((r,i)=>{txt(s,r[0],88,203+i*98,316,53,32,true);txt(s,r[1],432,206+i*98,760,68,30);});
txt(s,'Five domain apps',88,523,316,55,32,true);txt(s,'accounts    matching    mentorship\ngamification    notifications',432,523,760,99,30);
note(s,'Single Django project, not microservices. User authentication uses Django auth, extended by Profile and RoleAssignment. Credit is a wallet model, not an authentication model. Profile has a many-to-many relationship with Skill. Mentorship references two Users and one Progress record, with related Session, Milestone, Resource and DiscussionPost records. Gamification owns Credit, CreditTransaction, Feedback, Badge, UserBadge and LeaderboardEntry. Notification belongs to User. Services run synchronously in HTTP handlers. No Celery, Redis, payment gateway, video API or calendar sync exists. External meeting URLs support session records.',['mentorpulse/settings.py','mentorpulse/urls.py','accounts/models.py','mentorship/models.py','gamification/models.py','notifications/models.py','templates/base.html']);

s=p.slides.items[5];body(s).text='';
txt(s,'Seeded demonstration scenarios',88,200,562,48,31,true);
[['Alex Rivera','Active workspace: 61.7% progress'],['Jordan Lee','Pending priority request: 15 credits'],['Priya Sharma','Completed mentorship and certificate']].forEach((r,i)=>{txt(s,r[0],88,273+i*89,553,41,29,true);txt(s,r[1],88,314+i*89,553,46,27);});
const bytes=await fs.readFile(path.join(dir,'workspace-crop.png'));
s.images.add({blob:bytes,contentType:'image/png',alt:'MentorPulse active mentorship workspace for seeded demonstration accounts',fit:'contain',position:{left:681,top:252,width:511,height:321}});
txt(s,'Demo Switcher changes accounts while DEBUG is enabled',681,592,511,47,21);
txt(s,'Local launch: migrate, seed_demo_data, runserver',88,592,553,52,23);
note(s,'Live demo uses fictional seeded accounts. Active pair: Sarah Connor and Alex Rivera. Progress = 70*(2/3 completed milestones) + 30*(1/2 completed sessions) =61.7%. Workspace rounds this to 62% in its display. The README and old presentation say 67%, which does not match the implemented weighted formula. Completed pair: Marcus Vance and Priya Sharma, 100% and certificate. Jordan Lee has a priority pending request to Sarah Connor costing 15 credits. Setup: pip install -r requirements.txt, python manage.py migrate, python manage.py seed_demo_data, python manage.py runserver. Windows debug.bat/run_demo.bat automate setup. Seeder rebuilds demo data. Tests: python manage.py test --noinput, 53 passed on 12 October 2026. Per-app counts: accounts12, matching10, mentorship7, gamification18, notifications6. Credit/refund and session rewards include duplicate guards but lack atomic database transactions. Marking a mentorship COMPLETED forces 100% regardless of checklist completion, so certificates indicate workflow completion rather than independently assessed mastery.',['accounts/management/commands/seed_demo_data.py','accounts/views.py','mentorship/models.py','templates/mentorship/workspace.html','mentorship/views.py','gamification/services.py','run_demo.bat']);

for(let i=0;i<6;i++){const b=await p.export({slide:p.slides.items[i],format:'png',scale:1});await fs.writeFile(path.join(dir,`template-final-${i+1}.png`),new Uint8Array(await b.arrayBuffer()));console.log('Rendered template slide',i+1);}
const candidate=path.join(dir,'template-candidate.pptx');await (await PresentationFile.exportPptx(p)).save(candidate);
await fs.writeFile(path.join(dir,'template-font-hash.txt'),createHash('sha256').update(await fs.readFile(source)).digest('hex'));
console.log('Template draft ready');
