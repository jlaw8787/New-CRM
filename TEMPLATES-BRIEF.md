# Captain Contract, build brief: SMS templates + live merge preview

You are working in `index.html`, a single file vanilla JS app backed by Supabase,
deployed to GitHub Pages. Build this feature into the existing file. Do not
scaffold a new project.

## Hard rules, non negotiable
1. No em dashes anywhere, in code, comments, UI copy, or this document's outputs.
   Use commas, periods, or "to" for ranges.
2. Any number, count, money, or date rendered in the UI uses
   `font-variant-numeric: tabular-nums`.
3. Borders are shadows: `box-shadow: 0 0 0 1px rgba(22,21,26,.055)`, not
   `border: 1px solid`.
4. One accent colour, purple. Semantic colours for state only.
5. Plain spoken copy. No corporate filler.
Design tokens and patterns live in `CAPTAIN-CONTRACT-DESIGN.md`. Read it before
you style anything. Reuse the messages hub classes already in the file.

## What already exists, do not rebuild
- `msgSegments(n)` is the segment counter. Reuse it, do not write a new one.
- `sendMessage(candidateId, body)` is the hard consent gate. All sends go through
  it. Do not add a second send path.
- `msgComposerHtml(c)` renders the composer. `#msgBox` is the textarea,
  `#msgCnts` is the counter, `msgCnt(cid)` recomputes chars and segments.
- `CU` is the logged in user with `.id`, `.name`, `.role`. It is set in both auth
  modes, the real Supabase login and the dev profile picker, so owner filtering
  works the same in both.
- `candidates` is the in memory array. Fields you will merge against:
  `name`, `classification`, `state`, `availableFrom`, `consultantId`,
  `contracts[]` (each has `facility` and `status`).
- Helpers: `esc()`, `fmt()`, `showToast(msg, 'err'|'warn')`, `uById(id)`.
- The Messages hub is `renderMessagesHub()`. The open thread's candidate id is
  `msgHubSelectedId` in the hub, and `curCandId` on the candidate profile.

## The build

### 1. Merge resolver
Add these near the other message helpers.

```js
function tplActiveFacility(c){
  var ks=(c.contracts||[]);
  var active=ks.filter(function(k){return k.status==='Active'||k.status==='Confirmed';});
  var k=active[0]||ks[0];
  return (k&&k.facility)?k.facility:'the facility';
}
function mergeTemplate(body,c){
  if(!c)return body||'';
  var first=((c.name||'').trim().split(/\s+/)[0])||'there';
  var map={
    'first_name':first,
    'full_name':c.name||'',
    'specialty':c.classification||'',
    'facility':tplActiveFacility(c),
    'start_date':c.availableFrom?fmt(c.availableFrom):'',
    'state':c.state||'',
    'consultant':(uById(c.consultantId)||{}).name||(CU&&CU.name)||''
  };
  return String(body||'').replace(/\{(first_name|full_name|specialty|facility|start_date|state|consultant)\}/g,
    function(m,k){return map[k]!=null?map[k]:m;});
}
```
The clickable token list for the editor is exactly these seven:
`{first_name} {full_name} {specialty} {facility} {start_date} {state} {consultant}`.

### 2. Load templates at startup
Add a module level `var smsTemplates=[];` and this loader, then call
`loadSmsTemplates()` in the same startup sequence where the other
`sb.from(...).select()` hydration runs (same place messages and candidates load).

```js
function loadSmsTemplates(){
  return sb.from('sms_templates').select('*').then(function(r){
    if(r.error){console.error('[DB] sms_templates load',r.error);return;}
    smsTemplates=(r.data||[]).map(function(t){
      return {id:t.id,name:t.name,body:t.body,scope:t.scope||'personal',
        ownerId:t.owner_id,updatedAt:t.updated_at};
    });
  });
}
function tplMine(){return smsTemplates.filter(function(t){return t.scope!=='team'&&t.ownerId===CU.id;});}
function tplTeam(){return smsTemplates.filter(function(t){return t.scope==='team';});}
```

### 3. Insert into the composer
The candidate whose thread is open:
```js
function tplCurrentCand(){
  var id=(curPage==='messages')?msgHubSelectedId:curCandId;
  return candidates.find(function(x){return x.id===id;});
}
function tplInsert(id){
  var t=smsTemplates.find(function(x){return x.id===id;});
  var box=document.getElementById('msgBox');
  var c=tplCurrentCand();
  if(!t||!box||!c)return;
  box.value=mergeTemplate(t.body,c);
  msgCnt(c.id);
  box.focus();
  showToast('Template inserted and merged.');
}
```

### 4. Composer entry point
Add a small "Templates" button inside `msgComposerHtml(c)`, sitting next to the
Internal note toggle so it is only visible when the composer is (consent given).
Clicking it opens a popover anchored above the composer listing templates for the
open candidate. Match the messages hub look, shadow borders, purple accent, no
new colours.

Popover contents:
- Section label "MY TEMPLATES" then `tplMine()`, each row showing the template
  name and its merged preview via `mergeTemplate(t.body, tplCurrentCand())`.
  Clicking a row calls `tplInsert(t.id)` and closes the popover.
- Section label "TEAM TEMPLATES" then `tplTeam()`, same rendering, insert only.
- A "Manage templates" link at the bottom opening the editor modal (part 5).
Previews are live: they resolve against the currently open candidate, so the same
template reads differently per person. That is the point of the feature.

### 5. Editor modal, personal template CRUD
A modal to create, edit, and delete personal templates. Fields: Name (text),
Message (textarea). Under the textarea, the seven token chips, clicking a chip
inserts that token at the cursor. Below that, a live preview resolved for the
open candidate, and a char plus segment readout using `msgSegments()` on the
merged length, warning in amber past one segment. Save, Cancel, and on an
existing template a Delete.

```js
function tplUpsert(rec){ // rec: {id?, name, body, scope}
  var payload={name:rec.name,body:rec.body,scope:rec.scope||'personal',
    owner_id:(rec.scope==='team')?null:CU.id,updated_at:new Date().toISOString()};
  var q=rec.id
    ? sb.from('sms_templates').update(payload).eq('id',rec.id).select().single()
    : sb.from('sms_templates').insert(payload).select().single();
  return q.then(function(r){
    if(r.error){showToast('Could not save template: '+r.error.message,'err');return r;}
    return loadSmsTemplates().then(function(){return r;});
  });
}
function tplDelete(id){
  return sb.from('sms_templates').delete().eq('id',id).then(function(r){
    if(r.error){showToast('Could not delete: '+r.error.message,'err');return r;}
    return loadSmsTemplates().then(function(){return r;});
  });
}
```

Scope rule: a normal user creates and edits personal templates only. Team
templates are read only in the popover for everyone, and only an ops user
(`CU.role==='ops'`) sees a "Team template" toggle in the editor that sets
`scope:'team'`. Keep it simple, no per user team ownership.

### 6. Refresh
After any save or delete, re render whatever is on screen
(`renderMessagesHub()` when `curPage==='messages'`, else the candidate page)
so the popover and previews reflect the change.

## SQL, run by hand in Supabase before testing
Idempotent. Safe to run twice. `owner_id` 1 is Josh O. in the dev picker.

```sql
create table if not exists public.sms_templates (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  body text not null,
  scope text not null default 'personal',
  owner_id bigint,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
alter table public.sms_templates add column if not exists scope text not null default 'personal';
alter table public.sms_templates add column if not exists owner_id bigint;
alter table public.sms_templates add column if not exists updated_at timestamptz not null default now();

alter table public.sms_templates enable row level security;
drop policy if exists anon_all on public.sms_templates;
create policy anon_all on public.sms_templates for all using (true) with check (true);

insert into public.sms_templates (name, body, scope, owner_id)
select 'New opportunity','Hi {first_name}, a new {specialty} contract has come up that suits your profile. Want the detail?','personal',1
where not exists (select 1 from public.sms_templates where name='New opportunity');

insert into public.sms_templates (name, body, scope, owner_id)
select 'Compliance chase','Hi {first_name}, your compliance is due for renewal soon. Can you get it started this week?','personal',1
where not exists (select 1 from public.sms_templates where name='Compliance chase');

insert into public.sms_templates (name, body, scope, owner_id)
select 'Week one check in','Hi {first_name}, checking in on how week one at {facility} is going. All good?','team',null
where not exists (select 1 from public.sms_templates where name='Week one check in');
```

## Test checklist
- Templates load on login in both auth modes.
- Popover opens from the composer, only when consent is given.
- Each row's preview resolves for the open candidate, and changes when you
  switch candidate.
- Insert drops merged text into `#msgBox` and the counter updates.
- Create, edit, delete a personal template, list refreshes each time.
- Team template shows as read only for a non ops user, editable toggle appears
  for an ops user.
- No em dashes anywhere in the diff.
