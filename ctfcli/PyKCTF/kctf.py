import os,sys,platform

from pathlib import Path
from hashlib import sha1

# deployment managment
from kubernetes import client, config, watch
import docker,yaml,requests


from ctfcli.utils.utils import infolog,errorlogger,greenprint,redprint,yellowboldprint,blueprint
from ctfcli.utils.utils import getsubfiles
from ctfcli.core.yamlstuff import Yaml,KubernetesYaml

if platform.system == "Windows" or "Darwin":
		print("[-] Cannot CURRENTLY run this application on windows or MacOS, Exiting!")


# env vars should be set but check them anyways

class Cluster_Handler():
	def __init__(self,
				 tools_folder:Path,
				 challenge_repo:Path,
				 # defaults to linux
				 platform:str="linux",
				 cluster_type:str="kind",
				 cluster_name:str="meeplabben"
				 ):
		'''
		Manages the kubernetes cluster
		'''
		self.KIND_VERSION = os.environ.get("KIND_VERSION", "v0.14.0")
		self.KUBECTL_VERSION = os.environ.get("KUBECTL_VERSION", "v1.24.2")
		self.platform = platform
		# GCE registry name
		self.registry = str
		# GCE project name?
		self.project = str
		# kind for local, GCE costs money
		self.cluster_type = cluster_type
		# default is project name
		self.cluster_name = cluster_name
		# config is member of class for scope
		self.config = config.load_kube_config()
		# docker client
		self.client = docker.from_env()
		self.runcontainerdetached = lambda container: client.containers.run(container, detach=True)

		#cluster Dockerfile repository
		self.tools_folder = tools_folder
		self.dockerfile_repo = challenge_repo

		#paths to required binaries
		self.kubeconfig_path = Path(self.tools_folder, "kubectl")
		self.kind_path = Path(self.tools_folder, "kind")

	def ensure_kind(self):
		'''
		Checks for the existance of KIND binary
		'''
		if not self.kind_path.exists():
			url = os.getenv(
				"KIND_DOWNLOAD_URL",
				f"https://github.com/kubernetes-sigs/kind/releases/download/{self.KIND_VERSION}/kind-{self.platform}-amd64",
			)
			blueprint(f"[+] Downloading {url}..")
			tmp_file = self.kind_path.with_suffix(".tmp")
			with requests.get(url, stream=True) as r:
				r.raise_for_status()
				with tmp_file.open("wb") as fd:
					for chunk in r.iter_content(chunk_size=8192):
						if chunk:
							fd.write(chunk)
			tmp_file.chmod(0o755)
			tmp_file.rename(self.kind_path)

	def ensure_kubectl(self):
		'''
		Ensures the existance of kubectl and downloads if necessary
		'''
		if not self.kubectl_path.exists():
			if self.platform == "windows":
				url = os.getenv(
					"KUBECTL_DOWNLOAD_URL",
					f"https://dl.k8s.io/release/{self.KUBECTL_VERSION}/bin/{self.platform}/amd64/kubectl.exe",
				)
			else:
				url = os.getenv(
					"KUBECTL_DOWNLOAD_URL",
					f"https://dl.k8s.io/release/{self.KUBECTL_VERSION}/bin/{self.platform}/amd64/kubectl",
				)
			blueprint(f"Downloading {url}..")
			tmp_file = self.kubectl_path.with_suffix(".tmp")
			with requests.get(url, stream=True) as r:
				r.raise_for_status()
				with tmp_file.open("wb") as fd:
					for chunk in r.iter_content(chunk_size=8192):
						if chunk:
							fd.write(chunk)
			tmp_file.chmod(0o755)
			tmp_file.rename(self.kubectl_path)

	def listallpods(self):
		'''
		Lists all kubernetes pods, and their status
		'''
		self.setkubeconfig()
		# Configs can be set in Configuration class directly or using helper utility
		print("Listing pods with their IPs:")
		pods = self.client.list_pod_for_all_namespaces(watch=False)
		for pod in pods.items:
			print("%s\t%s\t%s" % (
					pods.status.pod_ip, 
					pods.metadata.namespace, 
					pods.metadata.name
					)
				)

	def watchpodevents(self):
		self.setkubeconfig()
		count = 10
		watcher = watch.Watch()
		for event in watcher.stream(self.client.list_namespace, _request_timeout=60):
			print("Event: %s %s" % (event['type'], event['object'].metadata.name))
			count -= 1
			if not count:
				watcher.stop()

	def startcontainerset(self,containerset:dict):
		''' 
		Starts the set given by params
		'''
		for name,container in containerset.items:
			self.runcontainerdetached(container=containerset[name])

	def runcontainerwithargs(self,container:str,arglist:list):
		client.containers.run(container, arglist)

	def listcontainers(self):
		'''
		lists installed docker containers
		'''
		for container in client.containers.list():
			print(container.name)


	def opencomposefile(self,docker_config):
		'''
		'''
		with open(docker_config, 'r') as ymlfile:
			docker_config = yaml.load(ymlfile)
			return docker_config

	def writecomposefile(self, docker_config,newyamldata):
		with open(docker_config, 'w') as newconf:
			yaml.dump(docker_config, newyamldata, default_flow_style=False)

	def get_k8s_nodes(exclude_node_label_key=app_config["EXCLUDE_NODE_LABEL_KEY"]):
		"""
		Returns a list of kubernetes nodes
		"""

		try:
			config.load_incluster_config()
		except config.ConfigException:
			try:
				config.load_kube_config()
			except config.ConfigException:
				raise Exception("Could not configure kubernetes python client")

		k8s_api = client.CoreV1Api()
		infolog("Getting k8s nodes...")
		response = k8s_api.list_node()
		if exclude_node_label_key is not None:
			nodes = []
			for node in response.items:
				if exclude_node_label_key not in node.metadata.labels:
					nodes.append(node)
			response.items = nodes
		infolog.info("Current k8s node count is {}".format(len(response.items)))
		return response.items 

	def _init_nginx(self,path:Path):
		"""
		from docs/examples

		The nginx yaml resides in $PROJECTROOT/containers/nginx
		"""
		with open(path.join(path.dirname(__file__), "nginx-deployment.yaml")) as f:
			dep = yaml.safe_load(f)
			k8s_apps_v1 = client.AppsV1Api()
			resp = k8s_apps_v1.create_namespaced_deployment(
				body=dep, namespace="default")
			print("Deployment created. status='%s'" % resp.metadata.name)


	def has_cluster_config(self):
		'''
		if cluster config exists
		'''

	def require_cluster_config(self):
		"""
		"""
		pass

	def require_active_challenge(self):
		'''
		checks for existance of challenge directory
		'''

	def build_image(self,container_name:str,container_dir:Path):
		'''
		uses docker to build image from dockerfile
		'''
		for file in getsubfiles(container_dir):
			if file.stem == "Dockerfile":
				self.client.images.build(file)


	def healthcheck_enabled(self):
		'''
		test expression

		function healthcheck_enabled {
		[[ $("${KCTF_BIN}/yq" eval 'select(.kind == "Challenge") | .spec.healthcheck.enabled' "${CHALLENGE_DIR}/challenge.yaml") == "true" ]]
		}
		'''

	def build_images(self):
		'''
		Builds a SET of images
		'''
		
	def push_image(self, image_name:str,image_id:str,challenge_name:str,cluster_type:str="kind"):
		'''
		kind)
			IMAGE_URL="kind/${IMAGE_NAME}:${IMAGE_ID}"
			docker tag "${IMAGE_ID}" "${IMAGE_URL}" || return
			"${KCTF_BIN}/kind" load docker-image --name "${CLUSTER_NAME}" "${IMAGE_URL}" || return
			
			on error
				_kctf_log_err "unknown cluster type \"${CLUSTER_TYPE}\""
			on success
				_k	ctf_log "Image pushed to \"${IMAGE_URL}\""
		} 
		'''
		match cluster_type:
			case "gce":
				redprint("[-] how the heck? This shouldnt be happening")
				pass
				#image_url = f"{self.registry}/{self.project}/{challenge_name}-{image_name}:{image_id}"
			case "kind":
				image_url=f"kind/${image_name}:${image_id}"
				command = self.tools_folder + '/kind" load docker-image --name "${CLUSTER_NAME}" "${IMAGE_URL}"'
				os.popen(command)

	def push_images(self):
		'''function push_images {
			push_image "challenge" "${CHALLENGE_IMAGE_LOCAL}" || return
			CHALLENGE_IMAGE_REMOTE="${IMAGE_URL}"
			if healthcheck_enabled; then
				push_image "healthcheck" "${HEALTHCHECK_IMAGE_LOCAL}" || return
				HEALTHCHECK_IMAGE_REMOTE="${IMAGE_URL}"
			fi
		}
		'''
	def  kctf_chal_start(self):
		'''function kctf_chal_start {
			require_cluster_config
			COMMAND="start" DESCRIPTION="Deploy the challenge to the cluster." parse_help_arg_only $@ || return
			build_images || return
			push_images || return

		# update challenge.yaml with the image urls
			"${KCTF_BIN}/yq" eval "select(.kind == \"Challenge\") | .spec.image = \"${CHALLENGE_IMAGE_REMOTE}\", select(.kind == \"Challenge\" | not)" --inplace "${CHALLENGE_DIR}/challenge.yaml"
			if healthcheck_enabled; then
				"${KCTF_BIN}/yq" eval "select(.kind == \"Challenge\") | .spec.healthcheck.image = \"${HEALTHCHECK_IMAGE_REMOTE}\", select(.kind == \"Challenge\" | not)" --inplace "${CHALLENGE_DIR}/challenge.yaml"
			fi

			"${KCTF_BIN}/kubectl" apply -f "${CHALLENGE_DIR}/challenge.yaml" || return
		}
		'''
	def kctf_chal_stop(self):
		'''function kctf_chal_stop {
			require_cluster_config
			COMMAND="stop" DESCRIPTION="Stop a challenge running on the cluster." parse_help_arg_only $@ || return
			"${KCTF_BIN}/kubectl" delete -f "${CHALLENGE_DIR}/challenge.yaml" || return
		}
		'''

	def debug_port_forward(self,remote_port:str="1337",local_port:str=""):
		'''
		Sets Port forwarding for the challenge
		'''

		self.require_active_challenge()

		yellowboldprint(f'[+] Starting port-forward from {remote_port} to {local_port}')
		"${KCTF_BIN}/kubectl" port-forward "deployment/${CHALLENGE_NAME}" --namespace "${CHALLENGE_NAMESPACE}" --address=127.0.0.1 "${LOCAL_PORT}:${REMOTE_PORT}"

	'''
	function kctf_chal_debug_docker {
		COMMAND="debug docker" parse_container_name $@ || return

		build_image "${CONTAINER}" || return

		DOCKER_NAME="kctf-${KCTF_CTF_NAME}-${CHALLENGE_NAME}-${CONTAINER}"

		# kill any existing containers
		docker kill "${DOCKER_NAME}" >/dev/null 2>/dev/null
		docker container rm "${DOCKER_NAME}" >/dev/null 2>/dev/null

		_kctf_log "Running docker container ${IMAGE_ID} using name ${DOCKER_NAME}"
		docker run -d --name "${DOCKER_NAME}" -it -p 1337 --privileged "${IMAGE_ID}" || return 1
		docker ps -f "name=${DOCKER_NAME}" || return 1
		_kctf_log "Container running, ctrl+c to exit"
		docker attach "${DOCKER_NAME}"
	}
	'''
'''
function kctf_chal_debug_usage {
	echo -e "usage: kctf chal debug command" >&2
	echo -e "available commands:" >&2
	echo -e "	logs:				 print logs of the container" >&2
	echo -e "	ssh:					spawn an interactive bash in the container" >&2
	echo -e "	port-forward: create a port-forward to the container's default port" >&2
	echo -e "	docker:			 run the docker container locally" >&2
	echo -e "NOTE: you can use --container=healthcheck flag to debug the healthcheck" >&2
}
'''
'''function kctf_chal_debug {
	if [[ $# -lt 1 ]]; then
		_kctf_log_err "unexpected argument count"
		kctf_chal_debug_usage
		exit 1
	fi

	case "$1" in
		-h|--help)
			kctf_chal_debug_usage
			exit 0
			;;
		logs)
			shift
			kctf_chal_debug_logs $@
			;;
		ssh)
			shift
			kctf_chal_debug_ssh $@
			;;
		port-forward)
			shift
			kctf_chal_debug_port_forward $@
			;;
		docker)
			shift
			kctf_chal_debug_docker $@
			;;
		*)
			_kctf_log_err "unknown command"
			kctf_chal_debug_usage
			exit 1
			;;
	esac
}
'''
'''function kctf_chal_create_usage {
	echo "usage: kctf chal create [args] name" >&2
	echo "args:" >&2
	echo "	-h|--help			 print this help" >&2
	echo "	--template			which template to use (run --template list to print available templates)" >&2
	echo "	--challenge-dir path where to create the new challenge" >&2
	echo "									default: \"${KCTF_CTF_DIR}/\${CHALLENGE_NAME}\"" >&2
}
'''
'''function kctf_chal_create {
	OPTS="h"
	LONGOPTS="help,template:,challenge-dir:"
	PARSED=$(${GETOPT} --options=$OPTS --longoptions=$LONGOPTS --name "kctf chal create" -- "$@")
	if [[ $? -ne 0 ]]; then
		kctf_chal_create_usage
		exit 1
	fi
	eval set -- "$PARSED"

	CHALLENGE_DIR=
	TEMPLATE=pwn
	while true; do
		case "$1" in
			-h|--help)
				kctf_chal_create_usage
				exit 0
				;;
			--template)
				TEMPLATE="$2"
				shift 2
				;;
			--challenge-dir)
				CHALLENGE_DIR="$2"
				shift 2
				;;
			--)
				shift
				break
				;;
			*)
				_kctf_log_err "Unrecognized argument \"$1\"."
				parse_help_arg_only_usage
				exit 1
				;;
		esac
	done

	if [[ "${TEMPLATE}" == "list" ]]; then
		echo "available templates:"
		for template in ${KCTF_CTF_DIR}/kctf/challenge-templates/*; do
			echo "	$(basename ${template})"
		done
		exit 0
	fi

	if [[ $# -ne 1 ]]; then
		_kctf_log_err "kctf chal create: name missing"
		kctf_chal_create_usage
		exit 1
	fi

	TEMPLATE_DIR="${KCTF_CTF_DIR}/kctf/challenge-templates/${TEMPLATE}"
	if [[ ! -e "${TEMPLATE_DIR}/challenge.yaml" ]]; then
		_kctf_log_err "kctf chal create: template \"${TEMPLATE}\" not found"
		_kctf_log_err "	run \"kctf chal create --template list\" to list available templates"
		exit 1
	fi

	CHALLENGE_NAME="$1"
	shift

	if [[ -z "${CHALLENGE_DIR}" ]]; then
		CHALLENGE_DIR="${KCTF_CTF_DIR}/${CHALLENGE_NAME}"
	else
		CHALLENGE_DIR_REALPATH=$(realpath --canonicalize-missing "${CHALLENGE_DIR}")
		if [[ "${CHALLENGE_DIR_REALPATH}" != "${KCTF_CTF_DIR}"/* ]]; then
			_kctf_log_err "Challenge dir needs to be under the CTF dir:"
			_kctf_log_err "	\"${CHALLENGE_DIR_REALPATH}\""
			_kctf_log_err "	not under"
			_kctf_log_err "	\"${KCTF_CTF_DIR}\""
			exit 1
		fi
	fi
	if [[ -e "${CHALLENGE_DIR}" ]]; then
		_kctf_log_err "error: challenge dir \"${CHALLENGE_DIR}\" does already exist"
		exit 1
	fi

	mkdir -p $(dirname "${CHALLENGE_DIR}") >/dev/null 2>/dev/null

	umask a+rx
	cp -p -r "${TEMPLATE_DIR}" "${CHALLENGE_DIR}"
	${KCTF_BIN}/yq eval ".metadata.name = \"${CHALLENGE_NAME}\"" --inplace "${CHALLENGE_DIR}/challenge.yaml"
}
'''
'''function kctf_chal_list {
	echo '== challenges in repository =='

	for challenge_yaml in $(find "${KCTF_CTF_DIR}" -path "${KCTF_CTF_DIR}/kctf" -prune -false -o -name "challenge.yaml"); do
		challenge_name=$(${KCTF_BIN}/yq eval "select(.kind == \"Challenge\") | .metadata.name" "${challenge_yaml}")
		challenge_dir=$(realpath --relative-to "${KCTF_CTF_DIR}" $(dirname "${challenge_yaml}"))
		if [[ "${challenge_name}" == ${challenge_dir} ]]; then
			echo "${challenge_name}"
		else
			echo "${challenge_name} (dir: ${challenge_dir})"
		fi
	done

	if has_cluster_config; then
		echo '== deployed challenges =='
		"${KCTF_BIN}/kubectl" get challenges
	fi
}
'''
'''function kctf_chal_usage {
	echo -e "usage: kctf chal command" >&2
	echo -e "available commands:" >&2
	echo -e "	create: create a new challenge from a template" >&2
	echo -e "	list:	 list existing challenges" >&2
	echo -e "	start:	deploy the challenge to the cluster" >&2
	echo -e "	stop:	 delete the challenge from the cluster" >&2
	echo -e "	status: print the current status of the challenge" >&2
	echo -e "	debug:	commands for debugging the challenge" >&2
}
'''
'''
if [[ $# -lt 1 ]]; then
	_kctf_log_err "unexpected argument count"
	kctf_chal_usage
	exit 1
fi

case "$1" in
	-h|--help)
		kctf_chal_usage
		exit 0
		;;
	create)
		shift
		kctf_chal_create $@
		;;
	list)
		shift
		kctf_chal_list $@
		;;
	start)
		shift
		kctf_chal_start $@
		;;
	stop)
		shift
		kctf_chal_stop $@
		;;
	status)
		shift
		kctf_chal_status $@
		;;
	debug)
		shift
		kctf_chal_debug $@
		;;
	*)
		_kctf_log_err "unknown command"
		kctf_chal_usage
		exit 1
		;;
esac

'''