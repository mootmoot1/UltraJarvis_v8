import logging


def log_job(
    job_name: str,
    prompt_hash: str,
    files_written: list[str],
    gates_summary: str,
    critic_result: str,
) -> None:
    logging.info(
        f"Job: {job_name}, Prompt Hash: {prompt_hash}, Files Written: {files_written}, Gates Summary: {gates_summary}, Critic Result: {critic_result}"
    )
