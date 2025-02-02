import subprocess
import os
import logging


logging.basicConfig(
    filename="commits.log",
    encoding="utf-8",  # Ensure Unicode support
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def run_command(command, cwd=None):
    """Run a command in the shell and print its output."""
    result = subprocess.run(
        command, shell=True, text=True, capture_output=True, cwd=cwd, encoding="utf-8"
    )
    if result.returncode != 0:
        print(f"Error running command: {command}")
        print(f"Error: {result.stderr}")
    else:
        print(result.stdout)


def get_submodules(repo_path):
    """Get the list of submodules"""
    result = subprocess.run(
        "git submodule",
        shell=True,
        text=True,
        capture_output=True,
        cwd=repo_path,
        encoding="utf-8",
    )

    submodules = []
    for line in result.stdout.splitlines():
        submodules.append(line.split()[1])

    return submodules


def run_command_in_all_project(repo_path):
    # subprocess.run("")
    subprocess.run(
        ["git", "submodule", "update", "--init", "--recursive"],
        cwd=repo_path,
        shell=True,
        text=True,
        capture_output=True,
        encoding="utf-8",
    )

    # Get the list of modified submodules (those that are out of sync)
    submodules = get_submodules(repo_path)

    # pull, Commit, and push the submodules repository concurrently
    for submodule in submodules:
        submodule_path = os.path.join(repo_path, submodule)
        path_in_submodule = os.path.join("packages", "ui")

        command = [
            "powershell",
            "-Command",
            f"echo Hack Shadcn CLI > ./next.config.js",
        ]
        run_command(
            "echo Hack Shadcn CLI > ./next.config.js",
            cwd=os.path.join(submodule_path, path_in_submodule),
        )

        run_command(
            "echo @tailwind base;\n@tailwind components;\n@tailwind utilities; > ./src/global.css",
            cwd=os.path.join(submodule_path, path_in_submodule),
        )

        run_command(
            "npm install -D tailwindcss@3",
            cwd=os.path.join(submodule_path, path_in_submodule),
        )

        run_command(
            "npx tailwindcss init",
            cwd=os.path.join(submodule_path, path_in_submodule),
        )

        run_command(
            "npx shadcn@latest init",
            cwd=os.path.join(submodule_path, path_in_submodule),
        )


if __name__ == "__main__":
    run_command_in_all_project(os.getcwd())
