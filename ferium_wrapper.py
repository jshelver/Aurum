import subprocess
from typing import List, Optional


class FeriumError(Exception):
    """Custom exception for Ferium wrapper errors."""
    pass


def run_command(cmd: List[str]) -> str:
    """
    Run a command via subprocess and return its stdout as a decoded string.
    Uses UTF-8 encoding with replacement for undecodable bytes to prevent UnicodeDecodeError.
    Raises subprocess.CalledProcessError on non-zero exit.
    """
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        check=True
    )
    return result.stdout


def get_active_profile() -> str:
    """
    Returns the name of the currently active ferium profile by running
    `ferium profile`. Raises FeriumError on failure.
    """
    try:
        output = run_command(["ferium", "profile"])
    except subprocess.CalledProcessError as e:
        err = e.stderr or e.stdout or str(e)
        raise FeriumError(f"Failed to get active profile: {err.strip()}")
    for line in output.splitlines():
        if line and not line.startswith((' ', '\t')):
            return line.strip().rstrip('*').strip()
    return ""


def list_profiles() -> List[str]:
    """
    Returns a list of existing ferium profile names by parsing
    `ferium profile list`. Raises FeriumError on failure.
    """
    try:
        output = run_command(["ferium", "profile", "list"])
    except subprocess.CalledProcessError as e:
        err = e.stderr or e.stdout or str(e)
        raise FeriumError(f"Failed to list profiles: {err.strip()}")
    profiles: List[str] = []
    for line in output.splitlines():
        if line and not line.startswith((' ', '\t')):
            profiles.append(line.strip().rstrip('*').strip())
    return profiles


def create_profile(
    name: str,
    game_version: str,
    mod_loader: str,
    output_dir: Optional[str] = None
) -> str:
    """
    Create a new ferium profile with the given settings.
    Raises FeriumError on failure.
    """
    cmd = [
        "ferium", "profile", "create",
        "--game-version", game_version,
        "--mod-loader", mod_loader,
        "--name", name
    ]
    if output_dir:
        cmd.extend(["--output-dir", output_dir])
    try:
        run_command(cmd)
    except subprocess.CalledProcessError as e:
        err = e.stderr or e.stdout or str(e)
        raise FeriumError(f"Failed to create profile '{name}': {err.strip()}")
    # verify
    active = get_active_profile()
    if active != name:
        raise FeriumError(f"Profile creation mismatch: expected '{name}', got '{active}'")
    return active


def switch_profile(name: str) -> str:
    """
    Switches the active ferium profile. Raises FeriumError on failure.
    """
    try:
        run_command(["ferium", "profile", "switch", name])
    except subprocess.CalledProcessError as e:
        err = e.stderr or e.stdout or str(e)
        raise FeriumError(f"Failed to switch to profile '{name}': {err.strip()}")
    # verify
    active = get_active_profile()
    if active != name:
        raise FeriumError(f"Profile switch mismatch: expected '{name}', got '{active}'")
    return active


def list_mods() -> List[str]:
    """
    Returns a list of Modrinth mod IDs in the active profile.
    If the profile is empty, returns an empty list.
    Raises FeriumError on unexpected failures.
    """
    try:
        output = run_command(["ferium", "list"])
    except subprocess.CalledProcessError as e:
        err = (e.stdout or e.stderr or "").lower()
        if "currently selected profile is empty" in err:
            return []
        raise FeriumError(f"Failed to list mods: {(e.stderr or e.stdout or str(e)).strip()}")
    if "currently selected profile is empty" in output.lower():
        return []
    mod_ids: List[str] = []
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] == "MR":
            mod_ids.append(parts[1])
    return mod_ids


def add_mod(mod_id: str) -> str:
    """
    Add a single Modrinth mod ID to the active profile.
    Returns the terminal output or raises FeriumError on failure.
    """
    try:
        result = run_command(["ferium", "add", mod_id]).strip()
        return result
    except subprocess.CalledProcessError as e:
        err = (e.stdout or e.stderr or "").strip()
        if "project does not exist" in err.lower():
            raise FeriumError(f"{mod_id}: project does not exist")
        raise FeriumError(err)


def upgrade_mods() -> str:
    """
    Download and install all mods for the active profile.
    Returns stdout output string or raises FeriumError on failure.
    """
    try:
        return run_command(["ferium", "upgrade"]).strip()
    except subprocess.CalledProcessError as e:
        err = (e.stdout or e.stderr or "").strip()
        raise FeriumError(f"Failed to upgrade mods: {err}")
