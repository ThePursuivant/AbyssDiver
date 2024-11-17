'''
@SPOOKEXE - GitHub

One-click ComfyUI installer and runner for Abyss Diver to install the ComfyUI Local Generator!

Installs the following:
1. ComfyUI
2. ComfyUI Manager
3. PonyV6HassakuXLHentai checkpoint and Dalle3_AnimeStyle_PONY Lora
4. Additional python packages in a virtual environment (x2)

To uninstall, delete the "tools" folder under this folder and optionally uninstall git as needed.
'''

from pydantic import BaseModel
from tqdm import tqdm
from typing import Optional, Union
from pathlib import Path

import os
import platform
import re
import requests
import signal
import subprocess
import tarfile
import time

COMFYUI_REPOSITORY_URL : str = "https://github.com/comfyanonymous/ComfyUI"
COMFYUI_API_REPOSITORY_URL : str = "https://api.github.com/repos/comfyanonymous/ComfyUI"
COMFYUI_CUSTOM_NODES : list[str] = ["https://github.com/ltdrdata/ComfyUI-Manager", "https://github.com/Fannovel16/comfyui_controlnet_aux", "https://github.com/jags111/efficiency-nodes-comfyui", "https://github.com/WASasquatch/was-node-suite-comfyui"]

CIVITAI_MODELS_TO_DOWNLOAD : dict[str, str] = {"PonyV6HassakuXLHentai.safetensors" : "https://civitai.com/api/download/models/575495?type=Model&format=SafeTensor&size=pruned&fp=bf16"}
CIVITAI_LORAS_TO_DOWNLOAD : dict[str, str] = {"Dalle3_AnimeStyle_PONY_Lora.safetensors" : "https://civitai.com/api/download/models/695621?type=Model&format=SafeTensor"}

HUGGINGFACE_CHECKPOINTS_TO_DOWNLOAD : dict[str, str] = {"PonyV6HassakuXLHentai.safetensors" : "https://huggingface.co/FloricSpacer/AbyssDiverModels/resolve/main/hassakuXLPony_v13BetterEyesVersion.safetensors?download=true"}
HUGGINGFACE_LORAS_TO_DOWNLOAD : dict[str, str] = {"Dalle3_AnimeStyle_PONY_Lora.safetensors" : "https://huggingface.co/FloricSpacer/AbyssDiverModels/resolve/main/DallE3-magik.safetensors?download=true"}

WHITELISTED_OPERATION_SYSTEMS : list[str] = ["Linux", "Windows"]
WINDOWS_ZIP_FILENAME : str = "ComfyUI_windows_portable_nvidia.7z"
LINUX_ZIP_FILENAME : str = "source.tar.gz"

FILEPATH_FOR_7z : Optional[str] = None
COMFYUI_INSTALLATION_FOLDER : Optional[str] = None
PYTHON_COMMAND : Optional[str] = None

class GithubFile(BaseModel):
	name : str
	browser_download_url : str
	class Config:
		extra = 'ignore'

def request_prompt(prompt : str, allowed_responses : list[str]) -> str:
	print(prompt)
	value = input("")
	while value not in allowed_responses:
		print("Invalid response.") # github @spookexe was here
		value = input("")
	return value

def download_file(url : str, destination : str) -> None:
	"""Download a file from a URL and save it to a specified destination with a progress bar."""
	response = requests.get(url, stream=True)
	response.raise_for_status()
	total_size = int(response.headers.get('content-length', 0))
	with tqdm(desc=destination, total=total_size, unit='iB', unit_scale=True, unit_divisor=1024,) as bar:
		with open(destination, 'wb') as file:
			for data in response.iter_content(chunk_size=1024):
				size = file.write(data)
				bar.update(size)

def run_command(command: str) -> tuple[int, str]:
	"""Run a command in the command prompt and return the status code and output message."""
	try:
		result : subprocess.CompletedProcess = subprocess.run(command, shell=True, capture_output=True,text=True)
		status_code : int = result.returncode
		output_message : str = result.stdout.strip()
		error_message : str = result.stderr.strip()
		if status_code == 0:
			return 0, output_message # SUCCESS
		return 1, error_message # ERROR
	except Exception as e:
		return -1, str(e) # FAILEDS

def unzip_targz(filepath : str, directory : str) -> None:
	os.makedirs(directory, exist_ok=True)
	with tarfile.open(filepath, 'r:gz') as tar_ref:
			tar_ref.extractall(directory)

def get_python_version() -> tuple[Union[str, None], Union[str, None]]:
	"""Find the python version that is installed."""
	pattern = r"Python (.+)"
	# check 'python' command
	status, output = run_command("python --version")
	if status == 0:
		return "python", re.match(pattern, output).group(1)
	# check 'py' command
	status, output = run_command("py --version")
	if status == 0:
		return "py", re.match(pattern, output).group(1)
	# no python available
	return None, None

def download_git_portal_windows() -> None:
	status, _ = run_command("git --version")
	if status == 0:
		return

	print("You are required to install git to download ComfyUI nodes on Windows.")
	print("Please install by visiting https://git-scm.com/downloads and installing the Windows 64-bit version.")
	print("Note: for most options, you can press next, if you aren't sure, press next.")
	print("Press enter to continue once git is installed... ")
	input()

	status, _ = run_command("git --version")
	assert status == 0, "Could not locate the 'git' package which is required for Linux."

def download_git_portal_linux() -> None:
	status, _ = run_command("git --version")
	if status == 0:
		return

	print("You are required to install git to download ComfyUI on Linux.")
	print("Please install with `sudo apt update && sudo apt install -y git`.")
	print("Press enter to continue once git is installed... ")
	input()

	status, _ = run_command("git --version")
	assert status == 0, "Could not locate the 'git' package which is required for Linux."

def get_github_repository_latest_release_files(api_url : str) -> list[GithubFile]:
	"""Get the latest release files of the target github repository"""
	response = requests.get(api_url, allow_redirects=True)
	response.raise_for_status()
	data : dict = response.json()
	assets : list[GithubFile] = []
	assets.append(GithubFile(name="source.zip", browser_download_url=data['zipball_url']))
	assets.append(GithubFile(name="source.tar.gz", browser_download_url=data['tarball_url']))
	assets.extend([GithubFile(**asset) for asset in data['assets']])
	return assets

def get_comfyui_latest_release_files() -> list[GithubFile]:
	"""Get the comfyui latest release files"""
	return get_github_repository_latest_release_files(f'{COMFYUI_API_REPOSITORY_URL}/releases/latest')

def find_github_file_of_name(files : list[GithubFile], name : str) -> Optional[GithubFile]:
	"""Search the list of files for the target filename."""
	for item in files:
		if item.name == name:
			return item
	return None

def install_comfyui_nodes(custom_nodes_folder : str) -> None:
	print("Installing ComfyUI Custom Nodes")
	before_cwd : str = os.getcwd()
	os.chdir(custom_nodes_folder)
	for url in COMFYUI_CUSTOM_NODES:
		os.system(f"git clone {url}")
	os.chdir(before_cwd)
	print("Installed ComfyUI Custom Nodes")

def prompt_safetensor_file_install(folder : str, filename : str, download_url : str) -> None:
	if os.path.exists(Path(os.path.join(folder, filename)).as_posix()) is True:
		print(filename, "already exists.")
		return
	while True:
		print("Press enter to continue once downloaded... ")
		input()
		if os.path.exists(Path(os.path.join(folder, filename)).as_posix()) is True:
			break
		print(f"You have not renamed the safetensors file or placed it in the directory {folder}!")
		print(f"Make sure to rename the downloaded file {download_url} to {filename} and place it in the directory specified above.")

def install_comfyui_checkpoints(checkpoints_folder : str) -> None:
	index = 0
	for filename, download_url in CIVITAI_MODELS_TO_DOWNLOAD.items():
		if os.path.exists(Path(os.path.join(checkpoints_folder, filename)).as_posix()) is True:
			index += 1
			continue
		print(index, '/', len(CIVITAI_MODELS_TO_DOWNLOAD.values()))
		print("Due to age restrictions you have to download models manually.")
		print(f"Download the following model: {download_url}")
		print(f"Place the model in the folder: {checkpoints_folder}")
		print(f"Rename the file to {filename}.")
		os.system(f"start '{download_url}'")
		os.system(f"explorer {checkpoints_folder}")
		prompt_safetensor_file_install(checkpoints_folder, filename, download_url)
		index += 1

def install_comfyui_loras(loras_folder : str) -> None:
	index = 0
	for filename, download_url in CIVITAI_LORAS_TO_DOWNLOAD.items():
		if os.path.exists(Path(os.path.join(loras_folder, filename)).as_posix()) is True:
			index += 1
			continue
		print(index, '/', len(CIVITAI_LORAS_TO_DOWNLOAD.values()))
		print("Due to age restrictions you have to download LORAs manually.")
		print(f"Download the following lora: {download_url}")
		print(f"Place the lora in the folder: {loras_folder}")
		print(f"Rename the file to {filename}.")
		os.system(f"start '{download_url}'")
		os.system(f"explorer {loras_folder}")
		prompt_safetensor_file_install(loras_folder, filename, download_url)
		index += 1

def is_huggingface_models_available() -> bool:
	for name, url in HUGGINGFACE_CHECKPOINTS_TO_DOWNLOAD.items():
		if requests.get(url, stream=True).status_code != 200:
			print(f"Model {name} is unavailable on huggingface!")
			return False
	for name, url in HUGGINGFACE_LORAS_TO_DOWNLOAD.items():
		if requests.get(url, stream=True).status_code != 200:
			print(f"Model {name} is unavailable on huggingface!")
			return False
	return True

def has_all_required_comfyui_models() -> bool:
	if COMFYUI_INSTALLATION_FOLDER is None or os.path.exists(Path(COMFYUI_INSTALLATION_FOLDER).as_posix()) is False:
		print("Missing ComfyUI.")
		return False
	checkpoints_folder : str = Path(os.path.join(COMFYUI_INSTALLATION_FOLDER, "ComfyUI", "models", "checkpoints")).as_posix()
	for name, _ in HUGGINGFACE_CHECKPOINTS_TO_DOWNLOAD.items():
		if os.path.exists(Path(os.path.join(checkpoints_folder, name)).as_posix()) is False:
			print(f"Missing Checkpoint: {os.path.join(checkpoints_folder, name)}")
			return False
	loras_folder : str = Path(os.path.join(COMFYUI_INSTALLATION_FOLDER, "ComfyUI", "models", "loras")).as_posix()
	for name, _ in HUGGINGFACE_LORAS_TO_DOWNLOAD.items():
		if os.path.exists(Path(os.path.join(loras_folder, name)).as_posix()) is False:
			print(f"Missing LORA: {Path(os.path.join(loras_folder, name)).as_posix()}")
			return False
	return True

def install_comfyui_models_from_hugginface() -> None:
	checkpoints_folder : str = Path(os.path.join(COMFYUI_INSTALLATION_FOLDER, "ComfyUI", "models", "checkpoints")).as_posix()
	for name, url in HUGGINGFACE_CHECKPOINTS_TO_DOWNLOAD.items():
		print(name)
		try:
			download_file(url, Path(os.path.join(checkpoints_folder, name)).as_posix())
		except Exception as e:
			print("Failed to download model file:")
			print(e)
			exit()

	loras_folder : str = Path(os.path.join(COMFYUI_INSTALLATION_FOLDER, "ComfyUI", "models", "loras")).as_posix()
	for name, url in HUGGINGFACE_LORAS_TO_DOWNLOAD.items():
		print(name)
		try:
			download_file(url, Path(os.path.join(loras_folder, name)).as_posix())
		except Exception as e:
			print("Failed to download model file:")
			print(e)
			exit()

def download_comfyui_latest(filename : str, directory : str) -> None:
	"""Download the latest release."""
	os.makedirs(directory, exist_ok=True)

	filepath : str = Path(os.path.join(directory, filename)).as_posix()
	if os.path.exists(filepath) is True:
		print(f"File {filename} has already been downloaded. Delete for it to be re-downloaded.")
		return

	latest_files : list[str] = get_comfyui_latest_release_files()

	target_file : Optional[GithubFile] = find_github_file_of_name(latest_files, filename)
	if target_file is None:
		raise ValueError(f"Unable to find latest release file for ComfyUI: {filename}")

	download_file(target_file.browser_download_url, filepath)

def install_comfyui_and_models_process(install_directory : str) -> None:
	global COMFYUI_INSTALLATION_FOLDER
	COMFYUI_INSTALLATION_FOLDER = Path(os.path.abspath(install_directory)).as_posix() # install_directory

	if has_all_required_comfyui_models() is False:
		print("="*20)
		print("Note: The total file size required for ComfyUI will add up over 9GB.")
		print("Note: The total file size required for the Abyss Diver content will add up to 7.1GB")
		print("You will need a total of at least 17GBs available.")
		print("Press enter to continue...")
		input()

	print("ComfyUI is located at: ", Path(os.path.abspath(install_directory)).as_posix()) # install_directory)
	install_comfyui_nodes(Path(os.path.join(COMFYUI_INSTALLATION_FOLDER, "ComfyUI", "custom_nodes")).as_posix())

	print("="*20)

	if has_all_required_comfyui_models():
		print("All models are already downloaded - skipping step.")
		return

	if is_huggingface_models_available():
		print("HuggingFace resource is available - automatically downloading models.")
		install_comfyui_models_from_hugginface()
	else:
		print("HuggingFace resource unavailable - manual installation needed.")
		print("For this section you will be manually installing and placing safetensor (AI Model) files in the given directories.")
		print("Both the directory and the download will automatically open/start when you proceed.")
		print("This is REQUIRED to run the local generation.")
		print(f"You will need to download a total of {len(CIVITAI_MODELS_TO_DOWNLOAD.values()) + len(CIVITAI_LORAS_TO_DOWNLOAD.values())} files.")
		print("Press enter to continue...")
		input()

		install_comfyui_checkpoints(Path(os.path.join(COMFYUI_INSTALLATION_FOLDER, "ComfyUI", "models", "checkpoints")).as_posix())
		install_comfyui_loras(Path(os.path.join(COMFYUI_INSTALLATION_FOLDER, "ComfyUI", "models", "loras")).as_posix())

def comfyui_windows_installer() -> None:
	"""Install the ComfyUI portable on Windows."""
	directory : str = "tools"

	# unzip the file if not already done
	install_directory : str = Path(os.path.join(directory, "ComfyUI_windows_portable")).as_posix()

	if os.path.isdir(Path(install_directory).as_posix()) is False:
		download_git_portal_windows()

		download_comfyui_latest(WINDOWS_ZIP_FILENAME, directory)

		print("Extracting the 7zip file using patool.")
		before_cwd = os.getcwd()
		os.chdir(Path(os.path.abspath(directory)).as_posix())
		result : int = os.system(f"""patool extract ComfyUI_windows_portable_nvidia.7z --outdir .""")
		if result != 0:
			print("Failed to extract ComfyUI_windows_portable_nvidia.7z - please do it manually.")
			input()
		os.chdir(before_cwd)
	else:
		print("ComfyUI is already downloaded - skipping unpacking and release download.")

	install_comfyui_and_models_process(install_directory)

def comfyui_linux_installer() -> None:
	"""Install ComfyUI on Linux"""
	directory : str = "tools"

	# install directory
	install_directory = Path(os.path.abspath(os.path.join(directory, "ComfyUI"))).as_posix()
	if os.path.exists(Path(install_directory).as_posix()) is False:
		download_git_portal_linux() # make sure git is installed

		status, message = run_command(f"git clone {COMFYUI_REPOSITORY_URL}")
		assert status == 0, f"Failed to clone repository {COMFYUI_REPOSITORY_URL}: {message}"

	install_comfyui_and_models_process(install_directory)

def ask_windows_gpu_cpu() -> int:
	is_gpu_mode : str = request_prompt("Will you be running image generation on your graphics card? (y/n)", ["y", "n"])
	if is_gpu_mode == "n": return 0

	is_nvidia_gpu : str = request_prompt("Is your graphics card a NVIDIA one? (y/n)", ["y", "n"])
	if is_nvidia_gpu == "y": return 1

	print("Unfortunately only NVIDIA cards are supported on Windows.")
	print("Image generation will be running on the CPU.")
	return 0

def ask_linux_gpu_cpu() -> int:
	is_gpu_mode : str = request_prompt("Will you be running image generation on your graphics card? (y/n)", ["y", "n"])
	if is_gpu_mode == "n":
		return 0

	is_nvidia_gpu : str = request_prompt("Is your graphics card a NVIDIA one? (y/n)", ["y", "n"])
	if is_nvidia_gpu == "y":
		return 1

	is_amd_linux : str = request_prompt("Is your graphics card a AMD one? (y/n)", ["y", "n"])
	if is_amd_linux == "y":
		return 2

	print("You have a unsupported graphics card - will default to CPU mode.")
	return 0

def get_last_device() -> Optional[int]:
	if os.path.exists('device') is False:
		return None
	try:
		with open("device", "r") as file:
			return int(file.read())
	except:
		return None

def write_last_device(device : int) -> None:
	with open("device", "w") as file:
		file.write(device)

def comfyui_windows_runner() -> subprocess.Popen:
	"""Run the ComfyUI portable on Windows."""
	assert COMFYUI_INSTALLATION_FOLDER, "COMFYUI_INSTALLATION_FOLDER is not set to anything - exiting."

	print("Running ComfyUI.")

	device : int = ask_windows_gpu_cpu() # 0:cpu, 1:cuda

	process : subprocess.Popen = None
	args = [".\python_embeded\python.exe", "-s", "ComfyUI\main.py", "--windows-standalone-build", '--lowvram', '--disable-auto-launch']
	if device == 0:
		# cpu
		args.append("--cpu")

	process = subprocess.Popen(args, cwd=COMFYUI_INSTALLATION_FOLDER, shell=True)
	return process

def comfyui_linux_runner() -> None:
	"""Run ComfyUI on Linux"""
	assert COMFYUI_INSTALLATION_FOLDER, "COMFYUI_INSTALLATION_FOLDER is not set to anything - exiting."

	# 0:cpu, 1:cuda, 2:romc
	last_device : Optional[int] = get_last_device()
	device : int = ask_linux_gpu_cpu()

	# remove torch for it to be reinstalled for GPU
	if device != 0 and (last_device is None or last_device != device):
		os.system("pip uninstall torch")

	if device == 0:
		# CPU
		os.system("pip install torch torchvision torchaudio")
	elif device == 1:
		# NVIDIA (CUDA)
		os.system("pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu124")
	elif device == 2:
		# AMD (ROCM)
		os.system("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm6.1")

	write_last_device(device)

	os.system(f"pip install -r {COMFYUI_INSTALLATION_FOLDER}/requirements.txt")
	os.system(f"{PYTHON_COMMAND} {COMFYUI_INSTALLATION_FOLDER}/main.py --lowvram --disable-auto-launch")

def proxy_runner() -> subprocess.Popen:
	return subprocess.Popen([PYTHON_COMMAND, 'python/main.py'], shell=True)

def main() -> None:
	os_platform : str = platform.system() # Windows, Linux

	available_ops : str = ", ".join(WHITELISTED_OPERATION_SYSTEMS)
	assert os_platform in WHITELISTED_OPERATION_SYSTEMS, f"Operating System {os_platform} is unsupported! Available platforms are: {available_ops}"

	print(f'Running one-click-comfyui on operating system {os_platform}.')

	py_cmd, version = get_python_version()
	assert py_cmd and version, "You must install python before continuing. Recommended version is 3.10.9 which is available at: https://www.python.org/downloads/release/python-3109/"

	global PYTHON_COMMAND
	PYTHON_COMMAND = py_cmd

	print(f"Found python ({py_cmd}) of version {version}.")

	process_proxy : subprocess.Popen
	process_comfyui : subprocess.Popen

	if os_platform == "Windows":
		print('Installing for Windows!')
		comfyui_windows_installer()
		process_proxy = proxy_runner()
		time.sleep(3) # let proxy output its message first
		process_comfyui = comfyui_windows_runner()
	elif os_platform == "Linux":
		print('Installing for Linux!')
		comfyui_linux_installer()
		process_proxy = proxy_runner()
		time.sleep(3) # let proxy output its message first
		process_comfyui = comfyui_linux_runner()
	else:
		exit()

	try:
		process_proxy.wait() # wait for process to terminate
		process_comfyui.wait() # wait for comfyui to terminate
	except KeyboardInterrupt: # CTRL+C
		os.kill(process_proxy.pid, signal.SIGTERM)
		os.kill(process_comfyui.pid, signal.SIGTERM)

if __name__ == '__main__':
	main()