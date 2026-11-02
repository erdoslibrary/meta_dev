import modal

image = modal.Image.debian_slim(python_version="3.11")
app = modal.App("hello-gpu", image=image)

@app.function(gpu="T4")
def gpu_info():
    import subprocess
    return subprocess.run(["nvidia-smi"], capture_output=True, text=True).stdout

@app.local_entrypoint()
def main():
    print(gpu_info.remote())