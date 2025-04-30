import subprocess
from typing import List, Optional

def run_command(cmd: List[str]) -> str:
    """
    Run a command via subprocess and return its stdout as a decoded string.
    Uses UTF-8 encoding with replacement for undecodable bytes to prevent UnicodeDecodeError.
    Raises subprocess.CalledProcessError on non-zero exit.
    """
    # Run the command, capturing stdout as text with specified encoding
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        check=True
    )
    return result.stdout

def list_profiles() -> List[str]:
    """
    Returns a list of existing ferium profile names by parsing the output of
    `ferium profile list`, extracting only the profile names.

    Sample output format:
        1.21.4
          Output directory: ...
        Skyblock 1.21
          Output directory: ...
        Server 1.21.4 *
          Output directory: ...

    This function picks only the lines with no leading whitespace and strips
    any trailing '*' markers.
    """
    output = run_command(["ferium", "profile", "list"])
    profiles: List[str] = []
    for line in output.splitlines():
        # Lines without leading whitespace indicate profile names
        if line and not line.startswith((' ', '\t')):
            # Remove trailing '*' (active profile marker) and surrounding whitespace
            name = line.strip().rstrip('*').strip()
            profiles.append(name)
    return profiles

def get_active_profile() -> str:
    """
    Returns the name of the currently active ferium profile by running
    `ferium profile` and parsing its first non-indented line.
    """
    output = run_command(["ferium", "profile"])
    for line in output.splitlines():
        if line and not line.startswith((' ', '\t')):
            return line.strip().rstrip('*').strip()
    return ""

def create_profile(
    name: str,
    game_version: str,
    mod_loader: str,
    output_dir: Optional[str] = None
) -> str:
    """
    Create a new ferium profile with the given name, game version, and mod loader.
    Optionally specify a custom output directory with `--output-dir <OUTPUT_DIR>`.
    After creation, verifies and returns the active profile name.
    """
    # Required flags: --game-version, --mod-loader, --name
    cmd = [
        "ferium", "profile", "create",
        "--game-version", game_version,
        "--mod-loader", mod_loader,
        "--name", name
    ]
    if output_dir:
        cmd.extend(["--output-dir", output_dir])
    # Execute creation command
    run_command(cmd)
    # Verify active profile
    active = get_active_profile()
    if active != name:
        raise RuntimeError(f"Profile creation mismatch: expected '{name}', got '{active}'")
    return active

def switch_profile(name: str) -> str:
    """
    Switches the active ferium profile and returns the new active profile name.
    """
    run_command(["ferium", "profile", "switch", name])
    active = get_active_profile()
    if active != name:
        raise RuntimeError(f"Profile switch mismatch: expected '{name}', got '{active}'")
    return active

def list_mods() -> List[str]:
    """
    Returns a list of Modrinth mod IDs in the active profile by parsing the output
    of `ferium list` and extracting the second token on lines prefixed with "MR".
    """
    output = run_command(["ferium", "list"])
    mod_ids: List[str] = []
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] == "MR":
            mod_ids.append(parts[1])
    return mod_ids

def add_mods(mod_ids: List[str]) -> str:
    """
    Add one or more Modrinth mod IDs to the active profile.
    """
    if not mod_ids:
        return ""
    cmd = ["ferium", "add"] + mod_ids
    return run_command(cmd)
