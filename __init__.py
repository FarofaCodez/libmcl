import requests
from pathlib import Path
import os

versions = []

def get_versions():
	global versions
	raw_versions = requests.get("https://piston-meta.mojang.com/mc/game/version_manifest_v2.json").json()
	versions = raw_versions["versions"]
	return versions

def get_version(requested_version):
	for version in versions:
		if version["id"] == requested_version:
			version_data = requests.get(version["url"]).json()
			return version_data

def check_rules(thing):
	rules = None
	try:
		rules = thing["rules"]
	except:
		return True
	
	for rule in rules:
		try:
			if rule["os"]["name"] == "linux":
				if rule["action"] == "allow":
					return True
		except:
			return False

def get_args(version_data):
	jvm_args = []
	game_args = []
	
	for arg in version_data["arguments"]["game"]:
		if isinstance(arg, str):
			game_args.append(arg)

	for arg in version_data["arguments"]["jvm"]:
		if isinstance(arg, str):
			jvm_args.append(arg)
		else:
			if check_rules(arg):
				jvm_args.append(arg["value"])
	
	args = {}
	args["game"] = game_args
	args["jvm"] = jvm_args

	return args

def download_file(url, target_path):
	path = Path(target_path)

	path.parent.mkdir(parents=True, exist_ok=True)
	
	response = requests.get(url, stream=True)
	response.raise_for_status()

	print(url, target_path)
	
	with open(path, 'wb') as f:
		for chunk in response.iter_content(chunk_size=8192):
			f.write(chunk)

def get_libs(version_data):
	# TODO: Handle older versions with funky artifact paths
	for library in version_data["libraries"]:
		url = library["downloads"]["artifact"]["url"]
		if "aarch_64" in url.lower():
			continue
		if check_rules(library) == True:
			if not os.path.exists("libraries/" + library["downloads"]["artifact"]["path"]):
				download_file(url, "libraries/" + library["downloads"]["artifact"]["path"])
	download_file(version_data["downloads"]["client"]["url"], "client.jar")

import random
import uuid
name = "Player" + str(random.randint(1000, 9999))
playerUuid = str(uuid.uuid4())

def launch(version):
	# TODO: Microsoft auth
	try:
		os.mkdir("game")
	except:
		pass
	os.chdir("game")

	get_versions()
	version = get_version(version)
	get_libs(version)

	libraries = []
	for library in version["libraries"]:
		if check_rules(library) == True:
			libraries.append("libraries/" + library["downloads"]["artifact"]["path"])
	libraries.append("client.jar")

	command = f"java {' '.join(get_args(version)['jvm'])} net.minecraft.client.main.Main {' '.join(get_args(version)['game'])}"
	command = command.replace("${classpath}", ":".join(libraries))
	command = command.replace("${auth_player_name}", name)
	command = command.replace("${auth_uuid}", playerUuid)
	command = command.replace("${auth_access_token}", "0")
	command = command.replace("${auth_xuid}", "0")
	command = command.replace("${version_name}", version["id"])
	command = command.replace("${game_directory}", ".")
	command = command.replace("${assets_root}", "assets")
	command = command.replace("${assets_index_name}", version["assetIndex"]["id"])
	command = command.replace("${version_type}", version["type"])
	command = command.replace("${clientid}", "0")
	command = command.replace("${launcher_version}", "0.1")
	command = command.replace("${launcher_name}", "libmcl")
	command = command.replace("${natives_directory}", "natives")
	os.system(command)

if __name__ == "__main__":
	launch("1.21.11")