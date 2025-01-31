import subprocess
import os
from openai import OpenAI
from langchain_ollama import ChatOllama
import json

def run_command(command, cwd=None):
    """Run a command in the shell and print its output."""
    print(f"Running command: {command}")
    result = subprocess.run(command, shell=True, text=True, capture_output=True, cwd=cwd)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
    else:
        print(result.stdout)

def generate_commit_message(prompt):
    """Generate a commit message using Hugging Face API based on a prompt."""

    # Send the prompt to the model for response
    ollama_llm_engine = ChatOllama(
        model="llama3.2",
        base_url="http://localhost:11434",
        format="json",
        num_predict=-1
    )
    messages = [
        ("system", r"You are a developer who creates short, concise and better commit messages on code changes with best practices. Always respond in JSON with keys: {icon:string, commit_message:{type:string, subject:string, body: string, footer: string}} only. Important: Your response must be in this exact format and icon must be a UTF-8 encoded character (such as an emoji or symbol). If you do not have information for a key, provide an empty string (""). Do not include any non-JSON content, explanations, reviews, or code.If you using person name always use 'Abhishek'. If your response deviates from this format, it will be considered invalid."),
        ("human", prompt),
    ]

    ollama_response = ollama_llm_engine.invoke(messages)
    ollama_response = json.loads(ollama_response.content)

    # Parse the response and return the commit message
    commit_message = f"{ollama_response["icon"]} {ollama_response["commit_message"]["type"]}: {ollama_response["commit_message"]["subject"]}\n\n{ollama_response["commit_message"]["body"]}\n\n{ollama_response["commit_message"]["footer"]}"
    
    return commit_message

def get_modified_files(submodule_path):
    """Get the list of modified files in the repository or submodule."""
    result = subprocess.run(
        'git diff --name-only',
        shell=True,
        text=True,
        capture_output=True,
        cwd=submodule_path
    )
    return result.stdout.strip().splitlines()

def get_submodules(repo_path):
    """Get the list of submodules"""
    result = subprocess.run(
        'git submodule',
        shell=True,
        text=True,
        capture_output=True,
        cwd=repo_path
    )

    submodules = []
    for line in result.stdout.splitlines():
            submodules.append(line.split()[1])

    return submodules

ignored_files = ["package-lock.json"];
def get_diff_summary(submodule_path, modified_files):
    """Get a summary of changes for each modified file."""
    diff_summary = []
    for modified_file in modified_files:
        if modified_file in ignored_files:
            continue
        result = subprocess.run(
            f'git diff {modified_file}',
            shell=True,
            text=True,
            capture_output=True,
            cwd=submodule_path
        )
        diff = result.stdout.strip()

        if diff:
            # We can choose to summarize the diff or just send the first few lines
            # Here we summarize by just counting added or removed lines
            added_lines = [line for line in diff.splitlines() if (line.startswith('+') and not line.startswith('+++') and not line.startswith("+Subproject"))]
            removed_lines = [line for line in diff.splitlines() if (line.startswith('-') and not line.startswith('---') and not line.startswith("-Subproject"))]

            diff_summary.append(f"In the file {modified_file},\n\n added\n\n{"\n".join(added_lines)}\n\nand removed\n\n{"\n".join(removed_lines)}.")
    return '\n\n\n'.join(diff_summary)

def commit_changes_in_submodule(submodule_path):
    """Commit any changes in the submodule with a generated commit message."""    

    # Get the list of modified files
    modified_files = get_modified_files(submodule_path)

    if len(modified_files) == 0:
        return;
    
    # Get the diff summary for each modified file
    diff_summary = get_diff_summary(submodule_path, modified_files)
    if(diff_summary):
        # Generate commit message based on the diff summary
        commit_message = generate_commit_message(f"I have made changes in the repository you have to create a concise commit message from it following good practices and add some icons as well for better readability Here is my changes\n: {diff_summary}")

        # Commit and push changes in the submodule
        run_command("git checkout dev", cwd=submodule_path)
        run_command(f"git add .", cwd=submodule_path)
        run_command(f'git commit -m "{commit_message}"', cwd=submodule_path)
        run_command("git pull origin dev", cwd=submodule_path)
        run_command('git push origin dev', cwd=submodule_path)
    else:
        print(f"No changes in submodule {submodule_path}.")

def push_git_submodules(repo_path):
    """Commit, pull, and push all git submodules recursively."""

    # subprocess.run("")
    subprocess.run(['git', 'submodule', 'update', '--init', '--recursive'], cwd=repo_path)
    
    # Get the list of modified submodules (those that are out of sync)
    submodules = get_submodules(repo_path)

    # pull, Commit, and push the submodules repository
    for submodules in submodules:
        submodule_path = os.path.join(repo_path, submodules)
        commit_changes_in_submodule(submodule_path)

    # Get the diff summary for the main repository
    modified_files = get_modified_files(repo_path)
    if len(modified_files) == 0:
        return;
    
    # Generate commit message for the projects that have changed files
    commit_message = generate_commit_message(f"Generate commit message for the projects that have changed files here is the list of all modified project: \n{"\n".join(modified_files)}")
    print(f"Commit message: {commit_message}")
    run_command(f"git add .", cwd=repo_path)
    run_command(f"git commit -m \"{commit_message}\"", cwd=repo_path)
    run_command(f"git pull origin main", cwd=repo_path)  # Pull before pushing
    run_command(f"git push origin main", cwd=repo_path)

if __name__ == "__main__":
    repo_path = input("Enter the path to your Git repository: ").strip()
    push_git_submodules(repo_path)
