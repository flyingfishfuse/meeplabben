gitdownloads = {
    "opsxcq": ("exploit-CVE-2017-7494", "exploit-CVE-2016-10033"),
    "t0kx": ("exploit-CVE-2016-9920"),
    "helmL64": "https://get.helm.sh/helm-v3.7.0-linux-amd64.tar.gz",
    "helmW64": "https://get.helm.sh/helm-v3.7.0-windows-amd64.zip"
}
helmchartrepos = {
    "gitlab": "helm repo add gitlab https://charts.gitlab.io/",
    "ingress-nginx": "helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx",
    "prometheus": "helm repo add prometheus-community https://prometheus-community.github.io/helm-charts",
    "gitlab-omnibus": "https://artifacthub.io/packages/helm/slamdev/gitlab-omnibus"
}
helchartinstalls = {
    "prometheus-community" : "helm install [RELEASE_NAME] prometheus-community/kube-prometheus-stack"
}
#for pi
raspipulls= {
    "opevpn"    : "cambarts/openvpn",
    "webgoat"   : "cambarts/webgoat-8.0-rpi",
    "bwapp"     : "cambarts/arm-bwapp",
    "dvwa"      : "cambarts/arm-dvwa",
    "LAMPstack" : "cambarts/arm-lamp"
}
#for pi
rpiruns = {
    "bwapp"     : '-d -p 80:80 cambarts/arm-bwapp',
    "dvwa"      : '-d -p 80:80 -p 3306:3306 -e MYSQL_PASS="password" cambarts/dvwa',
    "webgoat"   : "-d -p 80:80 -p cambarts/webgoat-8.0-rpi",
    "nginx"     : "-d nginx",
}
