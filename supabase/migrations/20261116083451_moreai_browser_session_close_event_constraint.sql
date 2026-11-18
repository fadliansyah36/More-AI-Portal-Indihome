-- Keep the event vocabulary aligned with the durable customer close-request lifecycle.
-- The API records close_requested before the worker closes the isolated OpenFuse session.
alter table public.moreai_browser_session_events
  drop constraint if exists moreai_browser_session_events_event_type_check;

alter table public.moreai_browser_session_events
  add constraint moreai_browser_session_events_event_type_check
  check (event_type in (
    'created',
    'restored',
    'state_saved',
    'close_requested',
    'closed',
    'expired'
  ));
