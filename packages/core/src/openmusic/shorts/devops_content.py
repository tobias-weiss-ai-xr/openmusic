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
        description="Declarative deployment management",
        category="kubernetes",
        source="tobias-weiss.org/kubernetes",
    ),
    DevOpsTip(
        title="K8s Service",
        code="apiVersion: v1\nkind: Service\nmetadata:\n  name: web",
        language="yaml",
        description="Expose service access endpoints",
        category="kubernetes",
        source="tobias-weiss.org/kubernetes",
    ),
    DevOpsTip(
        title="K8s ConfigMap",
        code="apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: config",
        language="yaml",
        description="Store configuration data externally",
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
        description="Automated build and test on push",
        category="ci-cd",
        source="tobias-weiss.org/ci-cd",
    ),
    DevOpsTip(
        title="Jenkins Pipeline",
        code="pipeline {\n  agent any\n  stages {\n    stage('Build') {\n      steps { sh 'npm run build' }\n    }\n  }\n}",
        language="groovy",
        description="Define pipelines as code",
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
        description="Automated configuration management",
        category="ansible",
        source="tobias-weiss.org/ansible",
    ),
    DevOpsTip(
        title="Ansible Inventory",
        code="[webservers]\nweb1 ansible_host=192.168.1.10\nweb2 ansible_host=192.168.1.11",
        language="yaml",
        description="Define managed host inventory",
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
        description="Prevent overfitting: stop after 10 rounds with no improvement",
        category="ai",
        source="tobias-weiss.org/ai",
    ),
    DevOpsTip(
        title="LangChain Prompt Template",
        code="from langchain.prompts import PromptTemplate\n\ntemplate = \"Explain {topic} to {user}\nusing simple language.\"",
        language="python",
        description="Structured prompt engineering",
        category="ai",
        source="tobias-weiss.org/ai",
    ),
    DevOpsTip(
        title="Gemma 4 Batch Inference",
        code="outputs = model.generate(\n  input_ids,\n  max_new_tokens=256,\n  do_sample=False,\n  batch_size=8\n)",
        language="python",
        description="Batch inference for higher throughput",
        category="ai",
        source="tobias-weiss.org/ai",
    ),
    DevOpsTip(
        title="RAG Chunking Strategy",
        code="from langchain.text_splitter import (\n  RecursiveCharacterTextSplitter\n)\n\nsplitter = RecursiveCharacterTextSplitter(\n  chunk_size=1000,\n  chunk_overlap=200\n)",
        language="python",
        description="Intelligent text splitting strategy",
        category="ai",
        source="tobias-weiss.org/ai",
    ),
    DevOpsTip(
        title="MLflow Experiment Tracking",
        code="import mlflow\n\nwith mlflow.start_run():\n  mlflow.log_param('lr', 0.01)\n  mlflow.log_metric('acc', 0.92)",
        language="python",
        description="Track experiment parameters and metrics",
        category="ai",
        source="tobias-weiss.org/ai",
    ),
    DevOpsTip(
        title="TensorBoard Monitoring",
        code="from torch.utils.tensorboard import (\n  SummaryWriter\n)\n\nwriter = SummaryWriter('./logs')\nwriter.add_scalar('loss', loss, step)",
        language="python",
        description="Real-time training process monitoring",
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
        description="Interactive rebase to clean up commit history",
        category="git",
        source="tobias-weiss.org/git",
    ),
    DevOpsTip(
        title="Git Bisect Debugging",
        code="git bisect start\n# <bad>标记错误提交 <good>标记正确提交\ngit bisect run python -m tests\n",
        language="bash",
        description="Binary search to find the bug-introducing commit",
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
        description="Define systemd service configuration",
        category="linux",
        source="tobias-weiss.org/linux",
    ),
    DevOpsTip(
        title="Nginx Reverse Proxy",
        code="server {\n  listen 80;\n  location / {\n    proxy_pass http://localhost:3000;\n  }\n}",
        language="nginx",
        description="Reverse proxy configuration",
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
        description="Define metric labels for observability",
        category="monitoring",
        source="tobias-weiss.org/monitoring",
    ),
    DevOpsTip(
        title="Grafana Dashboard",
        code="query: rate(http_requests_total[5m])\n\n# 查询最近5分钟的请求速率",
        language="promql",
        description="Build monitoring dashboards",
        category="monitoring",
        source="tobias-weiss.org/monitoring",
    ),
]

# ── Additional AI/ML tips ──
AI_TIPS_EXTRA = [
    DevOpsTip(
        title="OpenAI Structured Outputs",
        code="from openai import OpenAI\n\nclient = OpenAI()\nresponse = client.chat.completions.create(\n  model='gpt-4o',\n  response_format={\n    'type': 'json_schema',\n    'json_schema': {'name': 'schema'}\n  }\n)",
        language="python",
        description="Enforce JSON schema output from LLMs",
        category="ai",
        source="tobias-weiss.org/ai",
    ),
    DevOpsTip(
        title="Vector Embedding Search",
        code="results = collection.query(\n  query_embeddings=[embedding],\n  n_results=5\n)\n# cosine similarity search",
        language="python",
        description="Semantic search with vector embeddings",
        category="ai",
        source="tobias-weiss.org/ai",
    ),
    DevOpsTip(
        title="Agent Function Calling",
        code="tools = [{\n  'type': 'function',\n  'function': {\n    'name': 'search',\n    'parameters': {'query': {'type': 'string'}}\n  }\n}]\nresponse = client.chat.completions.create(\n  tools=tools\n)",
        language="python",
        description="LLM agent function calling pattern",
        category="ai",
        source="tobias-weiss.org/ai",
    ),
    DevOpsTip(
        title="RAG Context Window",
        code="context = retriever.invoke(query)\nprompt = f\"\"\"\nContext: {context}\nQuestion: {query}\nAnswer: \"\"\"",
        language="python",
        description="Retrieval-Augmented Generation pipeline",
        category="ai",
        source="tobias-weiss.org/ai",
    ),
    DevOpsTip(
        title="Fine-Tuning LoRA",
        code="from peft import LoraConfig\n\nlora_config = LoraConfig(\n  r=8,\n  lora_alpha=32,\n  target_modules=['q_proj', 'v_proj']\n)",
        language="python",
        description="Parameter-efficient fine-tuning with LoRA",
        category="ai",
        source="tobias-weiss.org/ai",
    ),
]

# ── Knowledge Graph / Cypher tips ──
GRAPH_TIPS = [
    DevOpsTip(
        title="Cypher CREATE Node",
        code="CREATE (n:Artist {name: 'Basic Channel'})\nRETURN n",
        language="cypher",
        description="Create a labeled node with properties",
        category="graph",
        source="tobias-weiss.org/knowledge-graph",
    ),
    DevOpsTip(
        title="Cypher MATCH Query",
        code="MATCH (a:Artist)-[:PRODUCED]->(t:Track)\nWHERE a.name = 'Rhythm & Sound'\nRETURN t.title, t.year",
        language="cypher",
        description="Query relationships in the graph",
        category="graph",
        source="tobias-weiss.org/knowledge-graph",
    ),
    DevOpsTip(
        title="Cypher CREATE Relationship",
        code="MATCH (a:Artist {name: 'Mono'})\nMATCH (t:Track {title: 'Life in Dub'})\nCREATE (a)-[:PRODUCED]->(t)",
        language="cypher",
        description="Connect nodes with relationships",
        category="graph",
        source="tobias-weiss.org/knowledge-graph",
    ),
    DevOpsTip(
        title="Neo4j Vector Index",
        code="CREATE VECTOR INDEX track_embeddings\nFOR (t:Track) ON (t.embedding)\nOPTIONS {indexConfig: {\n  `vector.dimensions`: 1536,\n  `vector.similarity`: 'cosine'\n}}",
        language="cypher",
        description="Vector similarity search in Neo4j",
        category="graph",
        source="tobias-weiss.org/knowledge-graph",
    ),
    DevOpsTip(
        title="Knowledge Graph RAG",
        code="result = graph.query(\"\"\"\n  MATCH (n)-[r]->(m)\n  WHERE n.name CONTAINS $query\n  RETURN n, r, m\n\"\"\", params={'query': query})",
        language="python",
        description="Graph-enhanced RAG with structured knowledge",
        category="graph",
        source="tobias-weiss.org/knowledge-graph",
    ),
    DevOpsTip(
        title="Cypher Aggregation",
        code="MATCH (a:Artist)-[:PRODUCED]->(t:Track)\nRETURN a.name, count(t) AS tracks\nORDER BY tracks DESC",
        language="cypher",
        description="Aggregate and analyze graph data",
        category="graph",
        source="tobias-weiss.org/knowledge-graph",
    ),
    DevOpsTip(
        title="Graph Path Traversal",
        code="MATCH path = (a:Artist)-[:PRODUCED*1..3]->(:Track)\nWHERE a.name = 'DeepChord'\nRETURN path",
        language="cypher",
        description="Traverse variable-length relationships",
        category="graph",
        source="tobias-weiss.org/knowledge-graph",
    ),
]

# ── Terraform / IaC tips ──
TERRAFORM_TIPS = [
    DevOpsTip(
        title="Terraform Init & Plan",
        code="terraform init\\nterraform plan -out=tfplan\\nterraform apply tfplan",
        language="bash",
        description="Standard Terraform workflow: init, plan, apply",
        category="terraform",
        source="tobias-weiss.org/terraform",
    ),
    DevOpsTip(
        title="Terraform Variables",
        code='variable "instance_type" {\\n  type    = string\\n  default = "t3.micro"\\n}\\n\\nresource "aws_instance" "web" {\\n  instance_type = var.instance_type\\n}',
        language="terraform",
        description="Parameterize infrastructure with variables",
        category="terraform",
        source="tobias-weiss.org/terraform",
    ),
    DevOpsTip(
        title="Terraform State",
        code='terraform {\\n  backend "s3" {\\n    bucket = "tf-state-prod"\\n    key    = "infra/terraform.tfstate"\\n    region = "eu-central-1"\\n  }\\n}',
        language="terraform",
        description="Remote state storage for team collaboration",
        category="terraform",
        source="tobias-weiss.org/terraform",
    ),
]

# ── Cloud / AWS tips ──
CLOUD_TIPS = [
    DevOpsTip(
        title="AWS S3 Bucket",
        code='resource "aws_s3_bucket" "data" {\\n  bucket = "my-data-lake\\n  force_destroy = true\\n}',
        language="terraform",
        description="Provision S3 storage with Terraform",
        category="cloud",
        source="tobias-weiss.org/cloud",
    ),
    DevOpsTip(
        title="AWS ECS Fargate",
        code='resource "aws_ecs_service" "app" {\\n  name            = "web-app"\\n  launch_type     = "FARGATE"\\n  task_definition = aws_ecs_task_definition.app.arn\\n  desired_count   = 2\\n}',
        language="terraform",
        description="Serverless container orchestration on AWS",
        category="cloud",
        source="tobias-weiss.org/cloud",
    ),
]

# ── Security tips ──
SECURITY_TIPS = [
    DevOpsTip(
        title="Trivy Vulnerability Scan",
        code="trivy image myapp:latest\\n# Scans OS pkgs & app deps\\n# CVSS scores, fix versions",
        language="bash",
        description="Container image vulnerability scanning",
        category="security",
        source="tobias-weiss.org/security",
    ),
    DevOpsTip(
        title="Docker Secrets",
        code='echo "my_secret" | docker secret create db_password -\\n# Mounted at /run/secrets/\\n# Never in env vars or image layers',
        language="bash",
        description="Securely manage secrets in Docker Swarm",
        category="security",
        source="tobias-weiss.org/security",
    ),
]

# ── Networking tips ──
NETWORKING_TIPS = [
    DevOpsTip(
        title="Docker Network",
        code="docker network create --driver overlay \\\\\\n  --subnet 10.0.1.0/24 \\\\\\n  my-app-net",
        language="bash",
        description="Create overlay network for multi-host communication",
        category="networking",
        source="tobias-weiss.org/networking",
    ),
    DevOpsTip(
        title="Curl Health Check",
        code='curl -s -o /dev/null -w "%{http_code}" \\\\\\n  https://api.example.com/health',
        language="bash",
        description="HTTP health check with status code extraction",
        category="networking",
        source="tobias-weiss.org/networking",
    ),
]

# ── Additional AI/ML tips (extra batch) ──
AI_TIPS_MORE = [
    DevOpsTip(
        title="LLM Evaluation with DeepEval",
        code="from deepeval import evaluate\\nfrom deepeval.metrics import HallucinationMetric\\n\\nmetric = HallucinationMetric()\\nresult = evaluate(\\n  test_cases=[\\n    LLMTestCase(actual_output=resp, context=docs)\\n  ],\\n  metrics=[metric]\\n)",
        language="python",
        description="Evaluate LLM outputs for hallucination and quality",
        category="ai",
        source="tobias-weiss.org/ai",
    ),
    DevOpsTip(
        title="Prompt Chaining Pattern",
        code="def generate_article(topic):\\n    outline = llm(f'Outline: {topic}')\\n    draft = llm(f'Draft based on: {outline}')\\n    review = llm(f'Review and fix: {draft}')\\n    return review",
        language="python",
        description="Chain multiple LLM calls for complex tasks",
        category="ai",
        source="tobias-weiss.org/ai",
    ),
    DevOpsTip(
        title="Embedding Caching",
        code="from functools import lru_cache\\n\\n@lru_cache(maxsize=10000)\\ndef get_embedding(text: str) -> list[float]:\\n    response = client.embeddings.create(\\n      model='text-embedding-3-small',\\n      input=text\\n    )\\n    return response.data[0].embedding",
        language="python",
        description="Cache embeddings to reduce API costs",
        category="ai",
        source="tobias-weiss.org/ai",
    ),
    DevOpsTip(
        title="Reranking for RAG",
        code="from cohere import Client\\n\\nco = Client(api_key)\\nresults = co.rerank(\\n  query=query,\\n  documents=documents,\\n  top_n=3,\\n  model='rerank-english-v3.0'\\n)",
        language="python",
        description="Improve RAG quality with semantic reranking",
        category="ai",
        source="tobias-weiss.org/ai",
    ),
    DevOpsTip(
        title="Multi-Agent Supervisor",
        code="class SupervisorAgent:\\n    def route(self, task: str) -> str:\\n        if 'code' in task: return 'coder'\\n        if 'math' in task: return 'analyst'\\n        return 'general'\\n\\nsupervisor = SupervisorAgent()\\nagent = supervisor.route(user_input)",
        language="python",
        description="Route tasks to specialized sub-agents",
        category="ai",
        source="tobias-weiss.org/ai",
    ),
]

# ── Additional Knowledge Graph tips (extra batch) ──
GRAPH_TIPS_MORE = [
    DevOpsTip(
        title="Graph BFS Traversal",
        code="MATCH (start:Node {id: 'A'})\\nCALL apoc.path.bfs(start,\\n  'RELATED_TO>', 1, 3)\\nYIELD path\\nRETURN path",
        language="cypher",
        description="Breadth-first search through graph relationships",
        category="graph",
        source="tobias-weiss.org/knowledge-graph",
    ),
    DevOpsTip(
        title="PageRank Centrality",
        code="CALL gds.pageRank.stream('myGraph')\\nYIELD nodeId, score\\nRETURN gds.util.asNode(nodeId).name AS name, score\\nORDER BY score DESC\\nLIMIT 10",
        language="cypher",
        description="Find influential nodes with PageRank algorithm",
        category="graph",
        source="tobias-weiss.org/knowledge-graph",
    ),
    DevOpsTip(
        title="GraphQL Schema Basics",
        code="type Artist {\\n  name: String!\\n  tracks: [Track!]!\\n}\\n\\ntype Track {\\n  title: String!\\n  duration: Int\\n  artist: Artist!\\n}\\n\\ntype Query {\\n  artists: [Artist!]!\\n  track(id: ID!): Track\\n}",
        language="graphql",
        description="Define graph API with GraphQL schema",
        category="graph",
        source="tobias-weiss.org/knowledge-graph",
    ),
    DevOpsTip(
        title="Neo4j Graph Data Science",
        code="CALL gds.graph.project('trackGraph',\\n  'Artist', 'Track',\\n  {PRODUCED: {orientation: 'UNDIRECTED'}}\\n)\\nYIELD graphName, nodeCount, relationshipCount",
        language="cypher",
        description="Project in-memory graphs for graph algorithms",
        category="graph",
        source="tobias-weiss.org/knowledge-graph",
    ),
    DevOpsTip(
        title="Node2Vec Embeddings",
        code="CALL gds.node2vec.stream('trackGraph', {\\n  embeddingDimension: 64,\\n  walkLength: 20,\\n  walksPerNode: 10\\n})\\nYIELD nodeId, embedding\\nRETURN gds.util.asNode(nodeId).name, embedding",
        language="cypher",
        description="Generate graph node embeddings for ML",
        category="graph",
        source="tobias-weiss.org/knowledge-graph",
    ),
    DevOpsTip(
        title="Cypher Subgraph Query",
        code="MATCH path = (a:Artist)-[:PRODUCED*1..2]-(related)\\nWHERE a.name = 'Basic Channel'\\nWITH a, collect(DISTINCT related) AS subgraph\\nUNWIND subgraph AS node\\nRETURN labels(node), node.name",
        language="cypher",
        description="Extract a subgraph around a seed node",
        category="graph",
        source="tobias-weiss.org/knowledge-graph",
    ),
]

# All tips combined
TIPS: list[DevOpsTip] = [
    *DOCKER_TIPS,
    *K8S_TIPS,
    *CI_TIPS,
    *ANSIBLE_TIPS,
    *AI_TIPS,
    *AI_TIPS_EXTRA,
    *AI_TIPS_MORE,
    *GIT_TIPS,
    *LINUX_TIPS,
    *MONITORING_TIPS,
    *TERRAFORM_TIPS,
    *CLOUD_TIPS,
    *SECURITY_TIPS,
    *NETWORKING_TIPS,
    *GRAPH_TIPS,
    *GRAPH_TIPS_MORE,
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
    "terraform": ["terraform", "iac", "infrastructure", "opentofu"],
    "cloud": ["cloud", "aws", "gcp", "azure", "s3", "ecs"],
    "security": ["security", "trivy", "vulnerability", "secrets", "scan"],
    "networking": ["networking", "network", "dns", "http", "curl"],
    "graph": ["graph", "knowledge graph", "neo4j", "cypher", "knowledge"],
}


def get_random_devops_tip(seed: int | None = None) -> DevOpsTip:
    """Return a random DevOps tip from the collection."""
    rng = random.Random(seed)
    all_tips = (
        DOCKER_TIPS + K8S_TIPS + CI_TIPS + ANSIBLE_TIPS +
        AI_TIPS + AI_TIPS_EXTRA + AI_TIPS_MORE +
        GIT_TIPS + LINUX_TIPS + MONITORING_TIPS +
        TERRAFORM_TIPS + CLOUD_TIPS + SECURITY_TIPS + NETWORKING_TIPS +
        GRAPH_TIPS + GRAPH_TIPS_MORE
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