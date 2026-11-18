-- Customer session closure is a durable request; the isolated worker closes Chromium and acknowledges it.
alter table public.moreai_browser_sessions
  drop constraint if exists moreai_browser_sessions_status_check;
alter table public.moreai_browser_sessions
  add constraint moreai_browser_sessions_status_check
  check (status in ('active','close_requested','closed','expired'));
