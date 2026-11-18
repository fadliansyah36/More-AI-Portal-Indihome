drop policy if exists llm_request_records_server_only on public.llm_request_records;
create policy llm_request_records_server_only on public.llm_request_records
as restrictive for all to anon,authenticated using (false) with check (false);
revoke all on public.llm_request_records from anon,authenticated;
grant select,insert,update,delete on public.llm_request_records to service_role;