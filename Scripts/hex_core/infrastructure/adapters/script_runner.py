import subprocess
import os
import threading
import uuid

class ScriptRunner:
    def __init__(self, base_dir: str, venv_python: str):
        self.base_dir = base_dir
        self.venv_python = venv_python
        self.active_processes = {} # task_id -> {"process": Popen, "logs": [], "status": "running", "returncode": None}

    def run_script(self, script_path: str, env_vars: dict = None, args: list = None) -> tuple:
        """
        Executes a script and returns (stdout_output, return_code)
        """
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)
            
        cmd = [self.venv_python, script_path]
        if args:
            cmd.extend(args)
            
        try:
            # We use Popen and communicate to capture the output, but in a real async environment we'd stream it.
            # For simplicity in this sync call, we capture it.
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # Merge stderr into stdout
                text=True,
                env=env,
                cwd=self.base_dir
            )
            stdout, _ = process.communicate()
            return stdout, process.returncode
        except Exception as e:
            return str(e), 1

    def start_script(self, script_path: str, env_vars: dict = None, args: list = None) -> str:
        """
        Starts a script asynchronously and returns a task_id
        """
        task_id = str(uuid.uuid4())
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)
        env["PYTHONUNBUFFERED"] = "1"
            
        cmd = [self.venv_python, script_path]
        if args:
            cmd.extend(args)
            
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
                cwd=self.base_dir,
                bufsize=1, # Line buffered
                universal_newlines=True
            )
            
            self.active_processes[task_id] = {
                "process": process,
                "logs": ["Iniciando script..."],
                "status": "running",
                "returncode": None
            }
            
            def _read_output(proc, t_id):
                for line in proc.stdout:
                    if t_id in self.active_processes:
                        self.active_processes[t_id]["logs"].append(line.rstrip('\\n'))
                proc.wait()
                if t_id in self.active_processes:
                    if self.active_processes[t_id]["status"] != "cancelled":
                        self.active_processes[t_id]["status"] = "completed" if proc.returncode == 0 else "error"
                        self.active_processes[t_id]["returncode"] = proc.returncode

            t = threading.Thread(target=_read_output, args=(process, task_id), daemon=True)
            t.start()
            
            return task_id
        except Exception as e:
            raise e

    def get_status(self, task_id: str) -> dict:
        if task_id not in self.active_processes:
            return None
        return {
            "status": self.active_processes[task_id]["status"],
            "logs": self.active_processes[task_id]["logs"],
            "returncode": self.active_processes[task_id]["returncode"]
        }

    def cancel_script(self, task_id: str):
        if task_id in self.active_processes:
            proc = self.active_processes[task_id]["process"]
            try:
                proc.terminate()
            except:
                pass
            self.active_processes[task_id]["status"] = "cancelled"
            self.active_processes[task_id]["logs"].append("🛑 Proceso cancelado por el usuario.")
