-- Apply once to a new Supabase project. The browser never receives a secret key.
create type public.app_role as enum ('viewer', 'admin');
create type public.media_key as enum ('Digmedia', '就活市場', 'ベンチャー就活');
create type public.device_kind as enum ('SP', 'PC', '不明');

create table public.profiles (
  user_id uuid primary key references auth.users(id) on delete cascade,
  email text not null unique check (email = lower(email) and email like '%@hr-team.co.jp'),
  role public.app_role not null default 'viewer',
  created_at timestamptz not null default now()
);
create table public.categories (id bigint generated always as identity primary key, name text not null unique, display_order int not null default 0);
create table public.subcategories (id bigint generated always as identity primary key, category_id bigint not null references public.categories(id) on delete cascade, name text not null, display_order int not null default 0, unique(category_id,name));
create table public.ads (
  media public.media_key not null, ad_id text not null, device public.device_kind not null,
  placement text not null, cv_point text, lp_number text, destination text, comment text,
  category text, subcategory text,
  status text not null default '', start_date date, end_date date,
  is_current boolean not null default true, updated_at timestamptz not null default now(),
  primary key(media,ad_id)
);
create table public.category_mappings (
  id bigint generated always as identity primary key, media public.media_key not null,
  original_category text not null, original_subcategory text not null default '',
  category_id bigint not null references public.categories(id), subcategory_id bigint references public.subcategories(id),
  unique(media,original_category,original_subcategory)
);
create table public.ad_daily_metrics (
  metric_date date not null, media public.media_key not null, ad_id text not null,
  impressions bigint not null default 0 check(impressions>=0), clicks bigint not null default 0 check(clicks>=0), cv bigint not null default 0 check(cv>=0),
  allocation_status text not null default '対象PVなし',
  primary key(metric_date,media,ad_id), foreign key(media,ad_id) references public.ads(media,ad_id) on delete cascade
);
create table public.ad_daily_cv_by_grad (
  metric_date date not null, media public.media_key not null, ad_id text not null, graduation_year smallint not null, cv bigint not null default 0 check(cv>=0),
  primary key(metric_date,media,ad_id,graduation_year), foreign key(media,ad_id) references public.ads(media,ad_id) on delete cascade
);
create table public.sync_runs (
  id bigint generated always as identity primary key, started_at timestamptz not null default now(), finished_at timestamptz,
  trigger text not null check(trigger in ('schedule','manual')), status text not null check(status in ('running','success','failed')),
  ads_count int not null default 0, metrics_count int not null default 0, error_message text
);
create table public.sync_issues (
  id bigint generated always as identity primary key,
  sync_run_id bigint not null references public.sync_runs(id) on delete cascade,
  issue_type text not null, media text, source_id text, details text,
  created_at timestamptz not null default now()
);
create index ad_daily_metrics_filter_idx on public.ad_daily_metrics(media,metric_date,ad_id);
create index ad_daily_grad_filter_idx on public.ad_daily_cv_by_grad(media,graduation_year,metric_date,ad_id);
create index ad_daily_metrics_ad_fk_idx on public.ad_daily_metrics(media,ad_id);
create index ad_daily_grad_ad_fk_idx on public.ad_daily_cv_by_grad(media,ad_id);
create index category_mappings_category_fk_idx on public.category_mappings(category_id);
create index category_mappings_subcategory_fk_idx on public.category_mappings(subcategory_id);
create index sync_issues_run_fk_idx on public.sync_issues(sync_run_id);

create schema if not exists private;
revoke all on schema private from public, anon;
grant usage on schema private to authenticated;
create table private.dashboard_api_tokens (
  token_hash text primary key,
  active boolean not null default true,
  created_at timestamptz not null default now()
);

create or replace function private.is_company_user() returns boolean
language sql stable security definer set search_path='' as $$
  select exists(select 1 from public.profiles where user_id=(select auth.uid()))
$$;
create or replace function private.is_admin() returns boolean
language sql stable security definer set search_path='' as $$
  select exists(select 1 from public.profiles where user_id=(select auth.uid()) and role='admin')
$$;
revoke all on function private.is_company_user() from public, anon;
revoke all on function private.is_admin() from public, anon;
grant execute on function private.is_company_user() to authenticated;
grant execute on function private.is_admin() to authenticated;

create or replace function private.handle_new_company_user() returns trigger
language plpgsql security definer set search_path='' as $$
begin
  if new.email is null or lower(new.email) !~ '@hr-team[.]co[.]jp$' then
    raise exception 'このアプリはhr-team.co.jpのGoogleアカウント限定です';
  end if;
  insert into public.profiles(user_id,email,role)
  values (
    new.id,
    lower(new.email),
    case when lower(new.email)='t-kobayashi@hr-team.co.jp'
      then 'admin'::public.app_role else 'viewer'::public.app_role end
  ) on conflict(user_id) do update set email=excluded.email;
  return new;
end;
$$;
revoke all on function private.handle_new_company_user() from public, anon, authenticated;
create trigger on_auth_user_created
after insert or update of email on auth.users
for each row execute function private.handle_new_company_user();

alter table public.profiles enable row level security; alter table public.categories enable row level security;
alter table public.subcategories enable row level security; alter table public.ads enable row level security;
alter table public.category_mappings enable row level security; alter table public.ad_daily_metrics enable row level security;
alter table public.ad_daily_cv_by_grad enable row level security; alter table public.sync_runs enable row level security;
alter table public.sync_issues enable row level security;
create policy "self or admin reads profiles" on public.profiles for select to authenticated
using(user_id=(select auth.uid()) or (select private.is_admin()));
create policy "admin updates profiles" on public.profiles for update to authenticated
using((select private.is_admin())) with check((select private.is_admin()));
create policy "company reads categories" on public.categories for select to authenticated using((select private.is_company_user()));
create policy "admin inserts categories" on public.categories for insert to authenticated with check((select private.is_admin()));
create policy "admin updates categories" on public.categories for update to authenticated using((select private.is_admin())) with check((select private.is_admin()));
create policy "admin deletes categories" on public.categories for delete to authenticated using((select private.is_admin()));
create policy "company reads subcategories" on public.subcategories for select to authenticated using((select private.is_company_user()));
create policy "admin inserts subcategories" on public.subcategories for insert to authenticated with check((select private.is_admin()));
create policy "admin updates subcategories" on public.subcategories for update to authenticated using((select private.is_admin())) with check((select private.is_admin()));
create policy "admin deletes subcategories" on public.subcategories for delete to authenticated using((select private.is_admin()));
create policy "company reads ads" on public.ads for select to authenticated using((select private.is_company_user()));
create policy "company reads mappings" on public.category_mappings for select to authenticated using((select private.is_company_user()));
create policy "admin inserts mappings" on public.category_mappings for insert to authenticated with check((select private.is_admin()));
create policy "admin updates mappings" on public.category_mappings for update to authenticated using((select private.is_admin())) with check((select private.is_admin()));
create policy "admin deletes mappings" on public.category_mappings for delete to authenticated using((select private.is_admin()));
create policy "company reads metrics" on public.ad_daily_metrics for select to authenticated using((select private.is_company_user()));
create policy "company reads grad metrics" on public.ad_daily_cv_by_grad for select to authenticated using((select private.is_company_user()));
create policy "admin reads runs" on public.sync_runs for select to authenticated using((select private.is_admin()));
create policy "admin reads issues" on public.sync_issues for select to authenticated using((select private.is_admin()));

grant usage on schema public to authenticated;
grant select on public.profiles, public.categories, public.subcategories, public.ads,
  public.category_mappings, public.ad_daily_metrics, public.ad_daily_cv_by_grad,
  public.sync_runs, public.sync_issues to authenticated;
grant insert, update, delete on public.categories, public.subcategories, public.category_mappings to authenticated;
grant update(role) on public.profiles to authenticated;
grant usage, select on all sequences in schema public to authenticated;

create or replace function public.ingest_ad_analysis(
  p_start_date date, p_end_date date, p_trigger text,
  p_ads jsonb, p_metrics jsonb, p_grad_metrics jsonb, p_issues jsonb default '[]'::jsonb
) returns bigint
language plpgsql security definer set search_path='' as $$
declare v_run_id bigint;
begin
  if p_trigger not in ('schedule','manual') then raise exception 'invalid sync trigger'; end if;
  if p_end_date < p_start_date then raise exception 'invalid sync date range'; end if;
  if jsonb_array_length(p_ads) = 0 then raise exception 'ad master is empty'; end if;

  -- 広告マスターは毎回全件スナップショットとして同期する。
  update public.ads set is_current=false,updated_at=now() where is_current;

  insert into public.ads(media,ad_id,device,placement,cv_point,lp_number,destination,comment,category,subcategory,status,start_date,end_date,is_current,updated_at)
  select x.media::public.media_key,x.ad_id,x.device::public.device_kind,x.placement,x.cv_point,x.lp_number,x.destination,x.comment,x.category,x.subcategory,x.status,x.start_date,x.end_date,true,now()
  from jsonb_to_recordset(p_ads) as x(media text,ad_id text,device text,placement text,cv_point text,lp_number text,destination text,comment text,category text,subcategory text,status text,start_date date,end_date date)
  on conflict(media,ad_id) do update set device=excluded.device,placement=excluded.placement,cv_point=excluded.cv_point,lp_number=excluded.lp_number,destination=excluded.destination,comment=excluded.comment,category=excluded.category,subcategory=excluded.subcategory,status=excluded.status,start_date=excluded.start_date,end_date=excluded.end_date,is_current=true,updated_at=now();

  delete from public.ad_daily_cv_by_grad where metric_date between p_start_date and p_end_date;
  delete from public.ad_daily_metrics where metric_date between p_start_date and p_end_date;

  insert into public.ad_daily_metrics(metric_date,media,ad_id,impressions,clicks,cv,allocation_status)
  select x.metric_date,x.media::public.media_key,x.ad_id,x.impressions,x.clicks,x.cv,x.allocation_status
  from jsonb_to_recordset(p_metrics) as x(metric_date date,media text,ad_id text,impressions bigint,clicks bigint,cv bigint,allocation_status text);

  insert into public.ad_daily_cv_by_grad(metric_date,media,ad_id,graduation_year,cv)
  select x.metric_date,x.media::public.media_key,x.ad_id,x.graduation_year,x.cv
  from jsonb_to_recordset(p_grad_metrics) as x(metric_date date,media text,ad_id text,graduation_year smallint,cv bigint);

  insert into public.sync_runs(started_at,finished_at,trigger,status,ads_count,metrics_count)
  values(now(),now(),p_trigger,'success',jsonb_array_length(p_ads),jsonb_array_length(p_metrics)) returning id into v_run_id;
  insert into public.sync_issues(sync_run_id,issue_type,media,source_id,details)
  select v_run_id,x.issue_type,x.media,x.source_id,x.details
  from jsonb_to_recordset(p_issues) as x(issue_type text,media text,source_id text,details text);
  return v_run_id;
end;
$$;
revoke all on function public.ingest_ad_analysis(date,date,text,jsonb,jsonb,jsonb,jsonb) from public,anon,authenticated;
grant execute on function public.ingest_ad_analysis(date,date,text,jsonb,jsonb,jsonb,jsonb) to service_role;

-- 大量データを1リクエストで処理するとAPIの120秒上限を超えるため、
-- 広告マスターと日別実績を分割して冪等に保存する。
create or replace function public.sync_ad_master(p_ads jsonb) returns integer
language plpgsql security definer set search_path='' as $$
begin
  if jsonb_array_length(p_ads) = 0 then raise exception 'ad master is empty'; end if;
  update public.ads set is_current=false,updated_at=now() where is_current;
  insert into public.ads(media,ad_id,device,placement,cv_point,lp_number,destination,comment,category,subcategory,status,start_date,end_date,is_current,updated_at)
  select x.media::public.media_key,x.ad_id,x.device::public.device_kind,x.placement,x.cv_point,x.lp_number,x.destination,x.comment,x.category,x.subcategory,x.status,x.start_date,x.end_date,true,now()
  from jsonb_to_recordset(p_ads) as x(media text,ad_id text,device text,placement text,cv_point text,lp_number text,destination text,comment text,category text,subcategory text,status text,start_date date,end_date date)
  on conflict(media,ad_id) do update set device=excluded.device,placement=excluded.placement,cv_point=excluded.cv_point,lp_number=excluded.lp_number,destination=excluded.destination,comment=excluded.comment,category=excluded.category,subcategory=excluded.subcategory,status=excluded.status,start_date=excluded.start_date,end_date=excluded.end_date,is_current=true,updated_at=now();
  return jsonb_array_length(p_ads);
end;
$$;

create or replace function public.replace_ad_metrics(
  p_start_date date, p_end_date date, p_metrics jsonb, p_grad_metrics jsonb
) returns integer
language plpgsql security definer set search_path='' as $$
begin
  if p_end_date < p_start_date then raise exception 'invalid sync date range'; end if;
  delete from public.ad_daily_cv_by_grad where metric_date between p_start_date and p_end_date;
  delete from public.ad_daily_metrics where metric_date between p_start_date and p_end_date;
  insert into public.ad_daily_metrics(metric_date,media,ad_id,impressions,clicks,cv,allocation_status)
  select x.metric_date,x.media::public.media_key,x.ad_id,x.impressions,x.clicks,x.cv,x.allocation_status
  from jsonb_to_recordset(p_metrics) as x(metric_date date,media text,ad_id text,impressions bigint,clicks bigint,cv bigint,allocation_status text);
  insert into public.ad_daily_cv_by_grad(metric_date,media,ad_id,graduation_year,cv)
  select x.metric_date,x.media::public.media_key,x.ad_id,x.graduation_year,x.cv
  from jsonb_to_recordset(p_grad_metrics) as x(metric_date date,media text,ad_id text,graduation_year smallint,cv bigint);
  return jsonb_array_length(p_metrics);
end;
$$;

create or replace function public.record_sync_success(
  p_trigger text, p_ads_count integer, p_metrics_count integer, p_issues jsonb default '[]'::jsonb
) returns bigint
language plpgsql security definer set search_path='' as $$
declare v_run_id bigint;
begin
  if p_trigger not in ('schedule','manual') then raise exception 'invalid sync trigger'; end if;
  insert into public.sync_runs(started_at,finished_at,trigger,status,ads_count,metrics_count)
  values(now(),now(),p_trigger,'success',p_ads_count,p_metrics_count) returning id into v_run_id;
  insert into public.sync_issues(sync_run_id,issue_type,media,source_id,details)
  select v_run_id,x.issue_type,x.media,x.source_id,x.details
  from jsonb_to_recordset(p_issues) as x(issue_type text,media text,source_id text,details text);
  return v_run_id;
end;
$$;

revoke all on function public.sync_ad_master(jsonb) from public,anon,authenticated;
revoke all on function public.replace_ad_metrics(date,date,jsonb,jsonb) from public,anon,authenticated;
revoke all on function public.record_sync_success(text,integer,integer,jsonb) from public,anon,authenticated;
grant execute on function public.sync_ad_master(jsonb) to service_role;
grant execute on function public.replace_ad_metrics(date,date,jsonb,jsonb) to service_role;
grant execute on function public.record_sync_success(text,integer,integer,jsonb) to service_role;

-- 旧版の一括集計関数が残っている環境では公開経路ごと削除する。
drop function if exists public.read_dashboard_snapshot(text,date,date,text,text,text,text,smallint,text,integer,integer);
drop function if exists public.get_dashboard_snapshot(date,date,text,text,text,text,smallint,text,integer,integer);

create or replace function public.get_dashboard_performance(
  p_start_date date,
  p_end_date date,
  p_media text default null,
  p_category text default null,
  p_subcategory text default null,
  p_placement text default null,
  p_graduation_year smallint default 2028,
  p_search text default null,
  p_limit integer default 100,
  p_offset integer default 0
) returns jsonb
language sql stable security definer set search_path='' as $$
with selected_ads as materialized (
  select * from public.ads a
  where a.is_current
    and (a.start_date is null or a.start_date <= p_end_date)
    and (a.end_date is null or a.end_date >= p_start_date)
    and (p_media is null or a.media::text = p_media)
    and (p_category is null or a.category = p_category)
    and (p_subcategory is null or a.subcategory = p_subcategory)
    and (p_placement is null or a.placement = p_placement)
    and (p_search is null or concat_ws(' ',a.ad_id,a.placement,a.cv_point,a.comment) ilike '%'||p_search||'%')
), metric_totals as materialized (
  select m.media,m.ad_id,sum(m.impressions)::bigint impressions,sum(m.clicks)::bigint clicks,sum(m.cv)::bigint cv
  from public.ad_daily_metrics m
  where m.metric_date between p_start_date and p_end_date
  group by m.media,m.ad_id
), grad_totals as materialized (
  select g.media,g.ad_id,sum(g.cv)::bigint grad_cv
  from public.ad_daily_cv_by_grad g
  where g.metric_date between p_start_date and p_end_date and g.graduation_year=p_graduation_year
  group by g.media,g.ad_id
), performance as materialized (
  select a.media::text media,a.ad_id,a.device::text device,a.placement,a.cv_point destination,a.comment,a.start_date,a.end_date,
    coalesce(a.category,'未設定') category,coalesce(a.subcategory,'未設定') subcategory,a.status,
    coalesce(m.impressions,0) impressions,coalesce(m.clicks,0) clicks,coalesce(m.cv,0) cv,coalesce(g.grad_cv,0) grad_cv
  from selected_ads a left join metric_totals m using(media,ad_id) left join grad_totals g using(media,ad_id)
)
select jsonb_build_object(
  'rows',coalesce((select jsonb_agg(to_jsonb(r) order by r.clicks desc,r.ad_id) from (select * from performance order by clicks desc,ad_id limit least(greatest(p_limit,1),500) offset greatest(p_offset,0)) r),'[]'::jsonb),
  'totals',coalesce((select jsonb_build_object('impressions',sum(impressions),'clicks',sum(clicks),'cv',sum(cv),'gradCv',sum(grad_cv)) from performance),'{}'::jsonb),
  'options',jsonb_build_object(
    'categories',coalesce((select jsonb_agg(x.category order by x.category) from (select distinct category from public.ads where is_current and (start_date is null or start_date<=p_end_date) and (end_date is null or end_date>=p_start_date) and (p_media is null or media::text=p_media) and category is not null and category<>'') x),'[]'::jsonb),
    'subcategories',coalesce((select jsonb_agg(x.subcategory order by x.subcategory) from (select distinct subcategory from public.ads where is_current and (start_date is null or start_date<=p_end_date) and (end_date is null or end_date>=p_start_date) and (p_media is null or media::text=p_media) and (p_category is null or category=p_category) and subcategory is not null and subcategory<>'') x),'[]'::jsonb),
    'placements',coalesce((select jsonb_agg(x.placement order by x.placement) from (select distinct placement from public.ads where is_current and (start_date is null or start_date<=p_end_date) and (end_date is null or end_date>=p_start_date) and (p_media is null or media::text=p_media) and (p_category is null or category=p_category) and (p_subcategory is null or subcategory=p_subcategory) and placement<>'') x),'[]'::jsonb)
  ),
  'lastUpdated',(select max(finished_at) from public.sync_runs where status='success'),
  'rowCount',(select count(*) from performance),
  'startDate',p_start_date,
  'endDate',p_end_date
);
$$;
revoke all on function public.get_dashboard_performance(date,date,text,text,text,text,smallint,text,integer,integer) from public,anon,authenticated;
grant execute on function public.get_dashboard_performance(date,date,text,text,text,text,smallint,text,integer,integer) to service_role;

create or replace function public.get_dashboard_trends(
  p_start_date date,p_end_date date,p_media text default null,p_category text default null,
  p_subcategory text default null,p_placement text default null,p_graduation_year smallint default 2028
) returns jsonb
language sql stable security definer set search_path='' as $$
with selected_ads as materialized (
  select * from public.ads a where a.is_current
    and (a.start_date is null or a.start_date <= p_end_date)
    and (a.end_date is null or a.end_date >= p_start_date)
    and (p_media is null or a.media::text=p_media)
    and (p_category is null or a.category=p_category)
    and (p_subcategory is null or a.subcategory=p_subcategory)
    and (p_placement is null or a.placement=p_placement)
), metric_by_ad as materialized (
  select date_trunc('week',m.metric_date)::date week_start,m.media,m.ad_id,
    sum(m.impressions)::bigint impressions,sum(m.clicks)::bigint clicks,sum(m.cv)::bigint cv
  from public.ad_daily_metrics m
  where m.metric_date between p_start_date and p_end_date group by 1,2,3
), grad_by_ad as materialized (
  select date_trunc('week',g.metric_date)::date week_start,g.media,g.ad_id,sum(g.cv)::bigint grad_cv
  from public.ad_daily_cv_by_grad g
  where g.metric_date between p_start_date and p_end_date and g.graduation_year=p_graduation_year group by 1,2,3
), metrics as materialized (
  select m.week_start,a.media::text media,a.placement,a.device::text device,
    coalesce(a.category,'未設定') category,coalesce(a.subcategory,'未設定') subcategory,
    sum(m.impressions)::bigint impressions,sum(m.clicks)::bigint clicks,sum(m.cv)::bigint cv
  from metric_by_ad m join selected_ads a using(media,ad_id)
  group by 1,2,3,4,5,6
), grads as materialized (
  select g.week_start,a.media::text media,a.placement,a.device::text device,
    coalesce(a.category,'未設定') category,coalesce(a.subcategory,'未設定') subcategory,sum(g.grad_cv)::bigint grad_cv
  from grad_by_ad g join selected_ads a using(media,ad_id)
  group by 1,2,3,4,5,6
), placement_weekly as (
  select m.*,coalesce(g.grad_cv,0) grad_cv from metrics m
  left join grads g using(week_start,media,placement,device,category,subcategory)
)
select jsonb_build_object(
  'weekly',coalesce((select jsonb_agg(jsonb_build_object('week_start',week_start,'clicks',clicks,'cv',cv) order by week_start)
    from (select week_start,sum(clicks)::bigint clicks,sum(cv)::bigint cv from metrics group by week_start) w),'[]'::jsonb),
  'placementWeekly',coalesce((select jsonb_agg(to_jsonb(w) order by week_start desc,clicks desc) from placement_weekly w),'[]'::jsonb)
);
$$;
revoke all on function public.get_dashboard_trends(date,date,text,text,text,text,smallint) from public,anon,authenticated;
grant execute on function public.get_dashboard_trends(date,date,text,text,text,text,smallint) to service_role;

create or replace function public.read_dashboard_performance(
  p_access_token text,p_start_date date,p_end_date date,p_media text default null,p_category text default null,
  p_subcategory text default null,p_placement text default null,p_graduation_year smallint default 2028,
  p_search text default null,p_limit integer default 100,p_offset integer default 0
) returns jsonb
language plpgsql stable security definer set search_path='' as $$
begin
  if not exists (
    select 1 from private.dashboard_api_tokens
    where active and token_hash=encode(extensions.digest(p_access_token,'sha256'),'hex')
  ) then raise exception 'not authorized'; end if;
  return public.get_dashboard_performance(p_start_date,p_end_date,p_media,p_category,p_subcategory,p_placement,p_graduation_year,p_search,p_limit,p_offset);
end;
$$;
revoke all on function public.read_dashboard_performance(text,date,date,text,text,text,text,smallint,text,integer,integer) from public,authenticated;
grant execute on function public.read_dashboard_performance(text,date,date,text,text,text,text,smallint,text,integer,integer) to anon;

create or replace function public.read_dashboard_trends(
  p_access_token text,p_start_date date,p_end_date date,p_media text default null,p_category text default null,
  p_subcategory text default null,p_placement text default null,p_graduation_year smallint default 2028
) returns jsonb
language plpgsql stable security definer set search_path='' as $$
begin
  if not exists (select 1 from private.dashboard_api_tokens where active and token_hash=encode(extensions.digest(p_access_token,'sha256'),'hex'))
  then raise exception 'not authorized'; end if;
  return public.get_dashboard_trends(p_start_date,p_end_date,p_media,p_category,p_subcategory,p_placement,p_graduation_year);
end;
$$;
revoke all on function public.read_dashboard_trends(text,date,date,text,text,text,text,smallint) from public,authenticated;
grant execute on function public.read_dashboard_trends(text,date,date,text,text,text,text,smallint) to anon;

create or replace function public.log_failed_sync(p_trigger text,p_error text) returns bigint
language plpgsql security definer set search_path='' as $$
declare v_run_id bigint;
begin
  insert into public.sync_runs(started_at,finished_at,trigger,status,error_message)
  values(now(),now(),p_trigger,'failed',left(p_error,4000)) returning id into v_run_id;
  return v_run_id;
end;
$$;
revoke all on function public.log_failed_sync(text,text) from public,anon,authenticated;
grant execute on function public.log_failed_sync(text,text) to service_role;

insert into public.profiles(user_id,email,role)
select id,lower(email),'admin'::public.app_role from auth.users where lower(email)='t-kobayashi@hr-team.co.jp'
on conflict(user_id) do update set role='admin';
