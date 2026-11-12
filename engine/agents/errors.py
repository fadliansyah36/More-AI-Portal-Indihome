class RunPausedForApproval(Exception):
    """Durable pause committed and worker lease released pending an owner decision."""
