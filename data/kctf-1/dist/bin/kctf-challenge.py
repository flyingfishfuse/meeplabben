
from kubernetes import client, config

import os,sys,platform

if platform.system == "Windows" or "Darwin":
		print("[-] Cannot CURRENTLY run this application on windows or MacOS, Exiting!")

class Cluster_Handler():
	def __init__(self,cluster_type:str="kind",cluster_name:str="meeplabben"):
		'''
		Manages the kubernetes cluster
		'''
		self.cluster_type = cluster_type
		self.cluster_name = cluster_name

	def has_cluster_config():
		'''
		if cluster config exists
		'''

	def require_cluster_config():
		"""
		"""
		pass

	def require_active_challenge():
		'''
		checks for existance of challenge directory
		'''

	def build_image(self,container_name:str):
		'''
		if symbolic link exists in container direcrtory
		use docker to build and write the image id to the file
		else use tar -czh to compress the folder THEN build the image

		if the commands docker or tar fail remove IIDFILE
		
		set the following variables
				IMAGE_ID=$(cat "${IIDFILE}")
				rm "${IIDFILE}"

		# strip optional sha256 prefix
		if [[ "${IMAGE_ID}" = sha256:* ]]; then
				IMAGE_ID=$(echo "${IMAGE_ID}" | cut -d ':' -f 2)
		fi
		_kctf_log "Image ID \"${IMAGE_ID}\""
		}
		'''

def healthcheck_enabled():
		'''
		test expression

		function healthcheck_enabled {
		[[ $("${KCTF_BIN}/yq" eval 'select(.kind == "Challenge") | .spec.healthcheck.enabled' "${CHALLENGE_DIR}/challenge.yaml") == "true" ]]
		}
		'''
		pass
def build_images():
	'''
	function build_images {
		build_image challenge || return
		CHALLENGE_IMAGE_LOCAL="${IMAGE_ID}"
		if healthcheck_enabled; then
			build_image healthcheck || return
			HEALTHCHECK_IMAGE_LOCAL="${IMAGE_ID}"
		fi
	}
	'''
def push_image(image_name:str,image_id:str,cluster_type:str="kind"):
	'''
	function push_image {
		IMAGE_NAME=$1
		IMAGE_ID=$2

		case "${CLUSTER_TYPE}" in
			gce)
				IMAGE_URL="${REGISTRY}/${PROJECT}/${CHALLENGE_NAME}-${IMAGE_NAME}:${IMAGE_ID}"
				docker tag "${IMAGE_ID}" "${IMAGE_URL}" || return
				docker push "${IMAGE_URL}" || return
				;;
			kind)
				IMAGE_URL="kind/${IMAGE_NAME}:${IMAGE_ID}"
				docker tag "${IMAGE_ID}" "${IMAGE_URL}" || return
				"${KCTF_BIN}/kind" load docker-image --name "${CLUSTER_NAME}" "${IMAGE_URL}" || return
			;;	
			*)
				_kctf_log_err "unknown cluster type \"${CLUSTER_TYPE}\""
				return 1
				;;
		esac
		_k	ctf_log "Image pushed to \"${IMAGE_URL}\""
	} 
	'''
	match cluster_type:
		case "gce":
			image_url = f"${registry}/${project}/${challenge_name}-${image_name}:${image_id}"

function push_images {
	push_image "challenge" "${CHALLENGE_IMAGE_LOCAL}" || return
	CHALLENGE_IMAGE_REMOTE="${IMAGE_URL}"
	if healthcheck_enabled; then
		push_image "healthcheck" "${HEALTHCHECK_IMAGE_LOCAL}" || return
		HEALTHCHECK_IMAGE_REMOTE="${IMAGE_URL}"
	fi
}

function kctf_chal_start {
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

function kctf_chal_stop {
	require_cluster_config
	COMMAND="stop" DESCRIPTION="Stop a challenge running on the cluster." parse_help_arg_only $@ || return
	"${KCTF_BIN}/kubectl" delete -f "${CHALLENGE_DIR}/challenge.yaml" || return
}

function kctf_chal_status {
	require_cluster_config
	COMMAND="status" DESCRIPTION="Print the challenge status." parse_help_arg_only $@ || return

	echo "= CHALLENGE RESOURCE ="
	echo
	"${KCTF_BIN}/kubectl" get "challenge/${CHALLENGE_NAME}" --namespace "${CHALLENGE_NAMESPACE}"
	echo
	echo "= INSTANCES / PODs ="
	echo
	echo "Challenge execution status"
	echo "This shows you how many instances of the challenges are running."
	echo
	"${KCTF_BIN}/kubectl" get pods -l "app=${CHALLENGE_NAME}" -o wide --namespace "${CHALLENGE_NAMESPACE}"
	echo
	echo
	echo "= DEPLOYMENTS ="
	echo
	echo "Challenge deployment status"
	echo "This shows you if the challenge was deployed to the cluster."
	echo
	"${KCTF_BIN}/kubectl" get deployments -l "app=${CHALLENGE_NAME}" -o wide --namespace "${CHALLENGE_NAMESPACE}"
	echo
	echo "= EXTERNAL SERVICES ="
	echo
	echo "Challenge external status"
	echo "This shows you if the challenge is exposed externally."
	echo
	echo "SERVICES:"
	"${KCTF_BIN}/kubectl" get services -l "app=${CHALLENGE_NAME}" -o custom-columns="NAME:.metadata.name,TYPE:.spec.type,EXTERNAL-IP:.status.loadBalancer.ingress[*]['ip'],PORT:.spec.ports[*].port,DNS:.metadata.annotations['external-dns\\.alpha\\.kubernetes\\.io/hostname']" --namespace "${CHALLENGE_NAMESPACE}"
	echo
	echo "Ingresses:"
	"${KCTF_BIN}/kubectl" get ingress -l "app=${CHALLENGE_NAME}" -o wide --namespace "${CHALLENGE_NAMESPACE}"
}

function kctf_chal_debug_logs_usage {
	echo -e "usage: kctf chal debug logs [args]" >&2
	echo -e "	-h|--help				print this help" >&2
	echo -e "	--container			name of the container to interact with, e.g. challenge (default) or healthcheck" >&2
	echo -e "	--tail					 how many lines to print per pod (default 20)" >&2
}

function kctf_chal_debug_logs {
	require_cluster_config

	OPTS="h"
	LONGOPTS="help,container:,tail:"
	PARSED=$(${GETOPT} --options=$OPTS --longoptions=$LONGOPTS --name "kctf chal ${COMMAND}" -- "$@")
	if [[ $? -ne 0 ]]; then
		kctf_chal_debug_logs_usage
		exit 1
	fi
	eval set -- "$PARSED"

	CONTAINER="challenge"
	TAIL="20"
	while true; do
		case "$1" in
			-h|--help)
				kctf_chal_debug_logs_usage
				exit 0
				;;
			--container)
				CONTAINER="$2"
				shift 2
				;;
			--tail)
				TAIL="$2"
				shift 2
				;;
			--)
				shift
				break
				;;
			*)
				_kctf_log_err "Unrecognized argument \"$1\"."
				kctf_chal_debug_logs_usage
				exit 1
				;;
		esac
	done

	require_active_challenge

	pods=($("${KCTF_BIN}/kubectl" get pods -l "app=${CHALLENGE_NAME}" -o jsonpath='{.items[*].metadata.name}'))

	if [[ ${#pods[@]} -eq 0 ]]; then
		_kctf_log_err 'No pods found. Is the challenge running?'
		return 1
	fi

	for pod in "${pods[@]}"; do
		startTime=$("${KCTF_BIN}/kubectl" get "pods/${pod}" -o jsonpath='{.status.startTime}')
		_kctf_log "== ${pod} (started @ ${startTime}) =="
		"${KCTF_BIN}/kubectl" logs "pods/${pod}" --tail="${TAIL}" -c "${CONTAINER}" --namespace "${CHALLENGE_NAMESPACE}"
	done
}

function kctf_chal_debug_ssh {
	require_cluster_config
	COMMAND="debug ssh" parse_container_name $@ || return

	pods=($("${KCTF_BIN}/kubectl" get pods -l "app=${CHALLENGE_NAME}" -o jsonpath='{.items[*].metadata.name}'))

	if [[ ${#pods[@]} -eq 0 ]]; then
		_kctf_log_err 'No pods found. Is the challenge running?'
		return 1
	fi

	pod="${pods[0]}"
	if [[ ${#pods[@]} -ne 1 ]]; then
		_kctf_log "Found ${#pods[@]} pods, connecting to the most recent one."
		_kctf_log "You can list the other pods with 'kubectl get pods'"
		_kctf_log "and connect to them using 'kubectl exec pod/PODNAME --namespace ${CHALLENGE_NAMESPACE} -c ${CONTAINER} -it -- /bin/bash'"

		latestStartTime=$(date -d "$("${KCTF_BIN}/kubectl" get "pods/${pod}" -o jsonpath='{.status.startTime}')" '+%s')
		for (( i=1;	i < ${#pods[@]};	i++ )); do
			otherPod="${pods[$i]}"
			otherStartTime=$(date -d "$("${KCTF_BIN}/kubectl" get "pods/${otherPod}" -o jsonpath='{.status.startTime}')" '+%s')
			if [[ -z "$("${KCTF_BIN}/kubectl" get "pod/${otherPod}" -o jsonpath="{.status.containerStatuses[?(@.name==\"${CONTAINER}\")].state.running}")" ]]; then
				_kctf_log_warn "skipping pod/${otherPod} since the container \"${CONTAINER}\" is not running"
				continue
			fi
			if [[ "${otherStartTime}" -gt "${latestStartTime}" ]]; then
				latestStartTime="${otherStartTime}"
				pod="${otherPod}"
			fi
		done
	fi

	_kctf_log "Connecting to pod ${pod}"
	"${KCTF_BIN}/kubectl" exec "pod/${pod}" --namespace "${CHALLENGE_NAMESPACE}" -c "${CONTAINER}" -it -- /bin/bash
}

function kctf_chal_debug_port_forward_usage {
	echo -e "usage: kctf chal debug port-forward [args]" >&2
	echo -e "args:" >&2
	echo -e "	-h|--help		 print this help" >&2
	echo -e "	--port:			 port in the challenge to connect to (default 1337)" >&2
	echo -e "	--local-port: local port to listen on (defaults to random free port)" >&2
}

function kctf_chal_debug_port_forward {
	REMOTE_PORT=1337
	LOCAL_PORT=""

	OPTS="h"
	LONGOPTS="help,challenge-name:,port:,local-port:"
	PARSED=$(${GETOPT} --options=$OPTS --longoptions=$LONGOPTS --name "kctf chal debug port-forward" -- "$@")
	if [[ $? -ne 0 ]]; then
		kctf_chal_debug_port_forward_usage
		exit 1
	fi
	eval set -- "$PARSED"

	while true; do
		case "$1" in
			-h|--help)
				kctf_chal_debug_port_forward_usage
				exit 0
				;;
			--port)
				REMOTE_PORT="$2"
				shift 2
				;;
			--local-port)
				LOCAL_PORT="$2"
				shift 2
				;;
			--)
				shift
				break
				;;
			*)
				_kctf_log_err "Unrecognized argument \"$1\"."
				kctf_chal_debug_port_forward_usage
				exit 1
				;;
		esac
	done

	require_active_challenge

	_kctf_log 'starting port-forward, ctrl+c to exit'
	"${KCTF_BIN}/kubectl" port-forward "deployment/${CHALLENGE_NAME}" --namespace "${CHALLENGE_NAMESPACE}" --address=127.0.0.1 "${LOCAL_PORT}:${REMOTE_PORT}"
}

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


function kctf_chal_debug_usage {
	echo -e "usage: kctf chal debug command" >&2
	echo -e "available commands:" >&2
	echo -e "	logs:				 print logs of the container" >&2
	echo -e "	ssh:					spawn an interactive bash in the container" >&2
	echo -e "	port-forward: create a port-forward to the container's default port" >&2
	echo -e "	docker:			 run the docker container locally" >&2
	echo -e "NOTE: you can use --container=healthcheck flag to debug the healthcheck" >&2
}

function kctf_chal_debug {
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

function kctf_chal_create_usage {
	echo "usage: kctf chal create [args] name" >&2
	echo "args:" >&2
	echo "	-h|--help			 print this help" >&2
	echo "	--template			which template to use (run --template list to print available templates)" >&2
	echo "	--challenge-dir path where to create the new challenge" >&2
	echo "									default: \"${KCTF_CTF_DIR}/\${CHALLENGE_NAME}\"" >&2
}

function kctf_chal_create {
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

function kctf_chal_list {
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

function kctf_chal_usage {
	echo -e "usage: kctf chal command" >&2
	echo -e "available commands:" >&2
	echo -e "	create: create a new challenge from a template" >&2
	echo -e "	list:	 list existing challenges" >&2
	echo -e "	start:	deploy the challenge to the cluster" >&2
	echo -e "	stop:	 delete the challenge from the cluster" >&2
	echo -e "	status: print the current status of the challenge" >&2
	echo -e "	debug:	commands for debugging the challenge" >&2
}

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

