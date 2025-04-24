import os
import subprocess
import re
import sys
import shutil
import difflib
from datetime import datetime
from colorama import init, Fore, Style
from groq import Groq

init(autoreset=True)

command_history = []
current_mode = "default"
groq_client = Groq(api_key="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")


def sanitize_filename(name):
    name = re.sub(r'[^\w\-_. ]', '', name)
    if not name.endswith(".py"):
        name += ".py"
    return name.replace(" ", "_").lower()


def log_history(command, filename):
    with open("history.log", "a", encoding="utf-8") as log:
        log.write(f"{datetime.now()}: {command} → {filename}\n")


def backup_file(filename):
    if os.path.exists(filename):
        shutil.copyfile(filename, filename + ".bak")


def undo_last_change(filename):
    backup = filename + ".bak"
    if os.path.exists(backup):
        shutil.copyfile(backup, filename)
        print(Fore.YELLOW + "↩️ Undo complete.")


def show_diff(old_code, new_code):
    diff = difflib.unified_diff(
        old_code.splitlines(), new_code.splitlines(), lineterm="", fromfile="Before", tofile="After"
    )
    print(Fore.BLUE + "\n📝 Code changes:")
    for line in diff:
        print(line)


def install_and_retry(error_msg, filename):
    match = re.search(r"No module named '(.+?)'", error_msg)
    if match:
        module = match.group(1)
        print(Fore.YELLOW + f"📦 Installing missing module: {module}")
        subprocess.run([sys.executable, "-m", "pip", "install", module])
        return run_code(filename)
    return False, error_msg


def generate_code_and_filename(user_instruction: str) -> tuple[str, str]:
    system_prompt = (
        "You are a Python code assistant. Return only valid Python code and a matching short filename. "
        "Format your output like this:\n\n"
        "<filename>\n<code>\n\n"
        "No markdown formatting. Do not include explanations."
        "Dont put ''' these syntax before or after the code"
    )

    chat_completion = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_instruction}
        ],
        model="llama3-70b-8192",
        temperature=0.3,
        max_tokens=1024,
        top_p=1,
        stream=False,
    )

    full_output = chat_completion.choices[0].message.content.strip()
    lines = full_output.splitlines()
    filename = sanitize_filename(lines[0])
    code = "\n".join(lines[1:])
    return filename, code


def explain_usage(filename):
    explain_prompt = f"Explain how to use the program in {filename} to a beginner. Keep it simple."
    chat_completion = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": "You explain how to use Python programs."},
            {"role": "user", "content": explain_prompt}
        ],
        model="llama3-70b-8192",
    )
    print(Fore.CYAN + "\n📘 How to use it:")
    print(chat_completion.choices[0].message.content.strip())


def save_code_to_file(filename: str, code: str):
    backup_file(filename)
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            old_code = f.read()
            show_diff(old_code, code)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(code)
    print(Fore.GREEN + f"💾 Code saved to '{filename}'")


def run_code(filename):
    try:
        print(Fore.BLUE + f"\n⚡ Executing: {filename}\n")
        subprocess.run(["python", filename], check=True)
        return True, ""
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        print(Fore.RED + f"❌ Error: {error_msg}")
        return False, error_msg


def fix_code(error_msg, old_code):
    repair_prompt = f"The following code has an error:\n{error_msg}\n\nFix this Python code:\n{old_code}"
    response = groq_client.chat.completions.create(
        messages=[
            {"role": "system", "content": "Fix Python code. Return just fixed code."},
            {"role": "user", "content": repair_prompt}
        ],
        model="llama3-70b-8192",
        temperature=0.2
    )
    return response.choices[0].message.content.strip()


if __name__ == "__main__":
    print(Fore.CYAN + "🧠 Self-Coding AI is online.")
    def list_features():
        print("\n✨ Features of Your Self-Coding AI Assistant:")
        print("1. 🤖 Generates Python code from instructions")
        print("2. 🛠 Auto-fixes errors until the code works")
        print("3. 📂 Saves code with a clean, consistent filename")
        print("4. ❌ Shows the exact error message when something goes wrong")
        print("5. 📄 Explains how to *use* the program after successful fix")
        print("6. 🔁 Skips auto-run after final successful repair")
        print("7. 🧠 Maintains a history log of instructions and file names")
        print("8. 🧼 Prevents clutter by overwriting the same file when fixing")
        print("9. 💬 Interactive command interface: type instructions or run scripts")
        print("10. ⏹ Type 'exit' or 'quit' to stop the assistant\n")

    list_features()


    while True:
        instruction = input(Fore.YELLOW + "💬 Command: ").strip()

        if instruction.lower() in ["exit", "quit"]:
            print(Fore.RED + "🛑 Shutting down...")
            break

        elif instruction.startswith("run "):
            file_to_run = instruction[4:].strip()
            run_code(file_to_run)

        elif instruction == "undo":
            if command_history:
                last_command = command_history[-1]
                filename, _ = generate_code_and_filename(last_command)
                undo_last_change(filename)

        elif instruction == "history":
            with open("history.log", "r") as log:
                print(Fore.BLUE + log.read())

        elif instruction.startswith("mode:"):
            current_mode = instruction.split(":")[1].strip()
            print(Fore.MAGENTA + f"🎮 Mode set to: {current_mode}")

        else:
            command_history.append(instruction)
            filename, code = generate_code_and_filename(instruction)
            log_history(instruction, filename)
            save_code_to_file(filename, code)

            success, error_msg = run_code(filename)

            while not success:
                print(Fore.YELLOW + "🔁 Attempting to fix the code...")
                fixed_code = fix_code(error_msg, code)
                filename = sanitize_filename(filename)
                save_code_to_file(filename, fixed_code)
                code = fixed_code
                success, error_msg = run_code(filename)

                if not success:
                    success, error_msg = install_and_retry(error_msg, filename)

            explain_usage(filename)
            print(Fore.GREEN + f"✅ Ready. Type 'run {filename}' to execute manually.")
