#!/usr/bin/env python
"""
Maintenance script runner for Jyra AI Roleplay Bot
"""

import os
import sys
import argparse
import importlib.util
import subprocess


def run_script(script_name, args=None):
    """
    Run a maintenance script with the correct Python path.

    Args:
        script_name (str): Name of the script to run (without .py extension)
        args (list): Additional arguments to pass to the script
    """
    # Add the current directory to the Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    # Build the script path
    script_path = os.path.join(current_dir, "scripts", f"{script_name}.py")

    if not os.path.exists(script_path):
        print(f"Error: Script {script_path} not found")
        return 1

    # Set PYTHONPATH environment variable
    env = os.environ.copy()
    env["PYTHONPATH"] = current_dir + os.pathsep + env.get("PYTHONPATH", "")

    # Build the command
    cmd = [sys.executable, script_path]
    if args:
        cmd.extend(args)

    # Run the script
    print(f"Running {script_name}...")
    result = subprocess.run(cmd, env=env)

    return result.returncode


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run maintenance scripts for Jyra AI Roleplay Bot")
    parser.add_argument("script", choices=["optimize_db", "clear_cache", "security_check"],
                        help="Script to run")
    parser.add_argument("args", nargs="*",
                        help="Additional arguments to pass to the script")

    args = parser.parse_args()

    # Run the selected script
    sys.exit(run_script(args.script, args.args))
