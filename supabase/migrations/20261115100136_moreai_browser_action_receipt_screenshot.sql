alter table public.moreai_browser_action_receipts
  drop constraint if exists moreai_browser_action_receipts_action_type_check;
alter table public.moreai_browser_action_receipts
  add constraint moreai_browser_action_receipts_action_type_check
  check (action_type in ('navigate','extract','input','screenshot','close','downloads'));