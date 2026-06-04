"""DevOps and AI tips database for short video generation.

Contains practical tips from DevOps workflows and AI/ML best practices,
with code snippets for split-screen visualization.
"""

from collections import namedtuple
import random

DevOpsTip = namedtuple("DevOpsTip", [
    "title",
    "code",
    "language",
    "description",
    "category",
    "source",
])

# Docker tips
DOCKER_TIPS = [
    DevOpsTip(
        title="Docker Detached Mode",
        code="docker run -d -p 80:80 nginx",
        language="docker",
        description="Run containers in background mode",
        category="docker",
        source="tobias-weiss.org/docker",
    ),
    DevOpsTip(
        title="Docker Volume Mount",
        code="docker run -v /host/path:/container/path nginx",
        language="docker",
        description="Mount host directory into container",
        category="docker",
        source="tobias-weiss.org/docker",
    ),
    DevOpsTip(
        title="Dockerfile Multi-Stage",
        code="FROM builder AS build\nCOPY . .\nRUN build.sh\n\nFROM runtime\nCOPY --from=build /app /app",
        language="docker",
        description="Optimize image size with multi-stage builds",
        category="docker",
        source="tobias-weiss.org/docker",
    ),
    DevOpsTip(
        title="Docker Compose",
        code="version: '3.8'\nservices:\n  web:\n    build: .\n    ports: ['80:80']",
        language="yaml",
        description="Define multi-container applications",
        category="docker",
        source="tobias-weiss.org/docker",
    ),
]

# Kubernetes tips
K8S_TIPS = [
    DevOpsTip(
        title="K8s Deployment",
        code="apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: web",
        language="yaml",
        description="声明式部署管理",
        category="kubernetes",
        source="tobias-weiss.org/kubernetes",
    ),
    DevOpsTip(
        title="K8s Service",
        code="apiVersion: v1\nkind: Service\nmetadata:\n  name: web",
        language="yaml",
        description="暴露服务访问端点",
        category="kubernetes",
        source="tobias-weiss.org/kubernetes",
    ),
    DevOpsTip(
        title="K8s ConfigMap",
        code="apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: config",
        language="yaml",
        description="存储配置数据",
        category="kubernetes",
        source="tobias-weiss.org/kubernetes",
    ),
]

# CI/CD tips
CI_TIPS = [
    DevOpsTip(
        title="GitHub Actions Workflow",
        code="name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest",
        language="yaml",
        description="自动化构建和测试",
        category="ci-cd",
        source="tobias-weiss.org/ci-cd",
    ),
    DevOpsTip(
        title="Jenkins Pipeline",
        code="pipeline {\n  agent any\n  stages {\n    stage('Build') {\n      steps { sh 'npm run build' }\n    }\n  }\n}",
        language="groovy",
        description="定义管道即代码",
        category="ci-cd",
        source="tobias-weiss.org/ci-cd",
    ),
]

# Ansible tips
ANSIBLE_TIPS = [
    DevOpsTip(
        title="Ansible Playbook",
        code="----\n- hosts: web\n  tasks:\n    - name: Install nginx\n      apt: name=nginx state=present",
        language="yaml",
        description="自动化配置管理",
        category="ansible",
        source="tobias-weiss.org/ansible",
    ),
    DevOpsTip(
        title="Ansible Inventory",
        code="[webservers]\nweb1 ansible_host=192.168.1.10\nweb2 ansible_host=192.168.1.11",
        language="yaml",
        description="定义管理主机列表",
        category="ansible",
        source="tobias-weiss.org/ansible",
    ),
]

# AI/ML tips
AI_TIPS = [
    DevOpsTip(
        title="XGBoost Early Stopping",
        code="model = xgb.XGBClassifier(\n  n_estimators=1000,\n  early_stopping_rounds=10\n)",
        language="python",
        description="防止过拟合: 10轮无改善后停止",
        category="ai",
        source="tobias-weiss.org/ai",
    ),
    DevOpsTip(
        title="LangChain Prompt Template",
        code="from langchain.prompts import PromptTemplate\n\ntemplate = \"向{user}解释{topic},\n使用简单的语言。\"",
        language="python",
        description="结构化提示工程",
        category="ai",
        source="tobias-weiss.org/ai",
    ),
    DevOpsTip(
        title="Gemma 4 Batch Inference",
        code="outputs = model.generate(\n  input_ids,\n  max_new_tokens=256,\n  do_sample=False,\n  batch_size=8\n)",
        language="python",
        description="批量推理提高吞吐量",
        category="ai",
        source="tobias-weiss.org/ai",
    ),
    DevOpsTip(
        title="RAG Chunking Strategy",
        code="from langchain.text_splitter import (\n  RecursiveCharacterTextSplitter\n)\n\nsplitter = RecursiveCharacterTextSplitter(\n  chunk_size=1000,\n  chunk_overlap=200\n)",
        language="python",
        description="智能文本分割策略",
        category="ai",
        source="tobias-weiss.org/ai",
    ),
    DevOpsTip(
        title="MLflow Experiment Tracking",
        code="import mlflow\n\nwith mlflow.start_run():\n  mlflow.log_param('lr', 0.01)\n  mlflow.log_metric('acc', 0.92)",
        language="python",
        description="跟踪实验参数和指标",
        category="ai",
        source="tobias-weiss.org/ai",
    ),
    DevOpsTip(
        title="TensorBoard Monitoring",
        code="from torch.utils.tensorboard import (\n  SummaryWriter\n)\n\nwriter = SummaryWriter('./logs')\nwriter.add_scalar('loss', loss, step)",
        language="python",
        description="实时监控训练过程",
        category="ai",
        source="tobias-weiss.org/ai",
    ),
]

# Git tips
GIT_TIPS = [
    DevOpsTip(
        title="Git Interactive Rebase",
        code="git rebase -i HEAD~5\n\n# 选择要修改的提交",
        language="bash",
        description="交互式交互整理提交历史",
        category="git",
        source="tobias-weiss.org/git",
    ),
    DevOpsTip(
        title="Git Bisect Debugging",
        code="git bisect start\n# <bad>标记错误提交 <good>标记正确提交\ngit bisect run python -m tests\n",
        language="bash",
        description="二分查找引入错误的提交",
        category="git",
        source="tobias-weiss.org/git",
    ),
]

# Linux/Admin tips
LINUX_TIPS = [
    DevOpsTip(
        title="Systemd Service",
        code="[Unit]\nDescription=My App\n\n[Service]\nExecStart=/usr/bin/myapp\nRestart=always",
        language="ini",
        description="定义系统服务配置",
        category="linux",
        source="tobias-weiss.org/linux",
    ),
    DevOpsTip(
        title="Nginx Reverse Proxy",
        code="server {\n  listen 80;\n  location / {\n    proxy_pass http://localhost:3000;\n  }\n}",
        language="nginx",
        description="反向代理配置",
        category="linux",
        source="tobias-weiss.org/linux",
    ),
]

# Monitoring tips
MONITORING_TIPS = [
    DevOpsTip(
        title="Prometheus Metrics",
        code="http_requests_total{method=\"POST\",status=\"200\"}",
        language="prometheus",
        description="定义度量指标标签",
        category="monitoring",
        source="tobias-weiss.org/monitoring",
    ),
    DevOpsTip(
        title="Grafana Dashboard",
        code="query: rate(http_requests_total[5m])\n\n# 查询最近5分钟的请求速率",
        language="promql",
        description="构建监控仪表板",
        category="monitoring",
        source="tobias-weiss.org/monitoring",
    ),
]

# All tips combined
TIPS: list[DevOpsTip] = [
    *DOCKER_TIPS,
    *K8S_TIPS,
    *CI_TIPS,
    *ANSIBLE_TIPS,
    *AI_TIPS,
    *GIT_TIPS,
    *LINUX_TIPS,
    *MONITORING_TIPS,
]

# Category map for filtering
CATEGORIES: dict[str, list[str]] = {
    "docker": ["docker", "containers", "images"],
    "kubernetes": ["k8s", "kubernetes", "k8", "deployments", "pods"],
    "ci-cd": ["ci", "cd", "github actions", "jenkins", "pipeline"],
    "ansible": ["ansible", "playbook", "automation"],
    "ai": ["ai", "ml", "machine learning", "llm", "xgboost", "langchain"],
    "git": ["git", "version control"],
    "linux": ["linux", "systemd", "nginx", "admin"],
    "monitoring": ["monitoring", "prometheus", "grafana", "observability"],
}


def get_random_devops_tip(seed: int | None = None) -> DevOpsTip:
    """Return a random DevOps tip from the collection."""
    rng = random.Random(seed)
    all_tips = (
        DOCKER_TIPS + K8S_TIPS + CI_TIPS + ANSIBLE_TIPS +
        AI_TIPS + GIT_TIPS + LINUX_TIPS + MONITORING_TIPS
    )
    return rng.choice(all_tips)


def get_random_tip(seed: int | None = None) -> DevOpsTip:
    """Return a random DevOps tip from the collection (alias)."""
    return get_random_devops_tip(seed=seed)
    """Return a random DevOps/AI tip."""
    rng = random.Random(seed)
    return rng.choice(TIPS)


def get_tips_by_category(category: str) -> list[DevOpsTip]:
    """Return all tips in a given category."""
    category_lower = category.lower()
    tips = [t for t in TIPS if t.category.lower() == category_lower]
    return tips


def get_tips_by_language(language: str) -> list[DevOpsTip]:
    """Return all tips using a given language."""
    language_lower = language.lower()
    tips = [t for t in TIPS if t.language.lower() == language_lower]
    return tips


def get_tips_by_keyword(keyword: str) -> list[DevOpsTip]:
    """Return tips matching a keyword in title or description."""
    keyword_lower = keyword.lower()
    tips = [
        t for t in TIPS
        if keyword_lower in t.title.lower()
        or keyword_lower in t.description.lower()
    ]
    return tips


def search_tips(query: str) -> list[DevOpsTip]:
    """Search tips across all fields (title, description, category)."""
    query_lower = query.lower()
    tips = [
        t for t in TIPS
        if query_lower in t.title.lower()
        or query_lower in t.description.lower()
        or query_lower in t.category.lower()
    ]
    return tips


def get_categories() -> list[str]:
    """Return all unique categories."""
    return sorted(set(t.category for t in TIPS))


def get_languages() -> list[str]:
    """Return all unique languages."""
    return sorted(set(t.language for t in TIPS))