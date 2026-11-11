from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    supabase_url: str | None
    supabase_anon_key: str | None
    supabase_service_role_key: str | None
    agent_execution_enabled: bool
    artifacts_bucket: str

    @classmethod
    def from_env(cls) -> "Settings":
        url = os.getenv("SUPABASE_URL")
        return cls(
            supabase_url=url.rstrip("/") if url else None,
            supabase_anon_key=os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_PUBLISHABLE_KEY"),
            supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
            agent_execution_enabled=os.getenv("MOREAI_AGENT_EXECUTION_ENABLED", "false").lower() == "true",
            artifacts_bucket=os.getenv("MOREAI_ARTIFACTS_BUCKET", ""),
        )

    @property
    def supabase_auth_ready(self) -> bool:
        return bool(self.supabase_url and self.supabase_anon_key)

    @property
    def supabase_data_ready(self) -> bool:
        return bool(self.supabase_url and self.supabase_service_role_key)
