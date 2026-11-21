"""Modular skills taxonomy and pattern matcher for TalentRank AI."""

import re
from typing import Dict, List, Set, Tuple

# Canonical skill name -> list of regex patterns or keyword variations
SKILLS_TAXONOMY: Dict[str, List[str]] = {
    # Programming Languages
    "Python": [r"\bpython(?:3)?\b"],
    "Java": [r"\bjava\b(?!\s*script)"],
    "C": [r"\b(?:c\s*,\s*c\+\+|c\s+programming|ansi\s+c|embedded\s+c|\bc/c\+\+)\b", r"(?:languages?|skills?)[:\s]+[^\n]*\bC\b"],
    "C++": [r"\bc\+\+\b", r"\bcpp\b"],
    "C#": [r"\bc#\b", r"\bc-sharp\b", r"\bcsharp\b"],
    "JavaScript": [r"\bjavascript\b", r"\bjs\b(?!\s*on)"],
    "TypeScript": [r"\btypescript\b", r"\bts\b"],
    "Go": [r"\bgolang\b", r"\bgo\s+(?:language|programming|developer)\b", r"(?:languages?|skills?)[:\s]+[^\n]*\bGo\b"],
    "Rust": [r"\brust\b(?:\s+(?:lang|programming|developer))?"],
    "Ruby": [r"\bruby\b(?!\s*on\s*rails)"],
    "PHP": [r"\bphp(?:\d)?\b"],
    "Swift": [r"\bswift\b(?:\s+(?:ios|programming|developer))?"],
    "Kotlin": [r"\bkotlin\b"],
    "R": [r"\br\s+(?:programming|language)\b", r"\b(?:r\s*,\s*python|python\s*,\s*r)\b"],
    "Scala": [r"\bscala\b"],
    "Dart": [r"\bdart\b"],
    "SQL": [r"\bsql\b"],
    "HTML": [r"\bhtml(?:5)?\b"],
    "CSS": [r"\bcss(?:3)?\b"],
    "Shell Scripting": [r"\bshell\s+script(?:ing)?\b", r"\bbash\b", r"\bpowershell\b", r"\bzsh\b"],

    # Web & Backend Frameworks
    "React": [r"\breact(?:\.js|js)?\b(?!\s*native)"],
    "React Native": [r"\breact\s*native\b"],
    "Angular": [r"\bangular(?:\.js|js|\s*\d+)?\b"],
    "Vue.js": [r"\bvue(?:\.js|js)?\b"],
    "Next.js": [r"\bnext(?:\.js|js)?\b"],
    "Nuxt.js": [r"\bnuxt(?:\.js|js)?\b"],
    "Node.js": [r"\bnode(?:\.js|js)?\b"],
    "Express.js": [r"\bexpress(?:\.js|js)?\b"],
    "FastAPI": [r"\bfastapi\b"],
    "Django": [r"\bdjango\b"],
    "Flask": [r"\bflask\b"],
    "Spring Boot": [r"\bspring\s*boot\b", r"\bspring\s*framework\b"],
    "ASP.NET": [r"\basp\.net\b", r"\b\.net\s*core\b", r"\bdotnet\b"],
    "Ruby on Rails": [r"\bruby\s+on\s+rails\b", r"\brails\b"],
    "Laravel": [r"\blaravel\b"],
    "Tailwind CSS": [r"\btailwind(?:\s*css)?\b"],
    "Bootstrap": [r"\bbootstrap\b"],
    "Redux": [r"\bredux\b", r"\bredux\s+toolkit\b"],
    "GraphQL": [r"\bgraphql\b"],
    "REST APIs": [r"\brest(?:ful)?\s*(?:api|apis)?\b", r"\brest\s*api\b"],

    # AI / Machine Learning & Data Science
    "Machine Learning": [r"\bmachine\s+learning\b", r"\bml\b"],
    "Deep Learning": [r"\bdeep\s+learning\b", r"\bdl\b"],
    "Natural Language Processing": [r"\bnatural\s+language\s+processing\b", r"\bnlp\b"],
    "Computer Vision": [r"\bcomputer\s+vision\b", r"\bcv\b(?!\s*writing)"],
    "Large Language Models": [r"\blarge\s+language\s+models?\b", r"\bllms?\b"],
    "Generative AI": [r"\bgenerative\s+ai\b", r"\bgenai\b"],
    "PyTorch": [r"\bpytorch\b"],
    "TensorFlow": [r"\btensorflow\b"],
    "Keras": [r"\bkeras\b"],
    "Scikit-Learn": [r"\bscikit-learn\b", r"\bsklearn\b"],
    "Pandas": [r"\bpandas\b"],
    "NumPy": [r"\bnumpy\b"],
    "SciPy": [r"\bscipy\b"],
    "Hugging Face": [r"\bhugging\s*face\b", r"\btransformers\b"],
    "LangChain": [r"\blangchain\b"],
    "LlamaIndex": [r"\bllamaindex\b"],
    "OpenCV": [r"\bopencv\b"],
    "NLTK": [r"\bnltk\b"],
    "spaCy": [r"\bspacy\b"],

    # Databases & Storage
    "PostgreSQL": [r"\bpostgres(?:ql)?\b"],
    "MySQL": [r"\bmysql\b"],
    "SQLite": [r"\bsqlite(?:3)?\b"],
    "MongoDB": [r"\bmongo(?:db)?\b"],
    "Redis": [r"\bredis\b"],
    "Cassandra": [r"\bcassandra\b"],
    "Elasticsearch": [r"\belasticsearch\b", r"\belastic\s+stack\b"],
    "DynamoDB": [r"\bdynamodb\b"],
    "Oracle Database": [r"\boracle(?:\s+database|\s+db)?\b"],
    "Microsoft SQL Server": [r"\bms\s*sql\b", r"\bsql\s*server\b"],
    "Firebase": [r"\bfirebase\b", r"\bfirestore\b"],
    "Snowflake": [r"\bsnowflake\b"],
    "BigQuery": [r"\bbigquery\b"],

    # Cloud & DevOps
    "AWS": [r"\baws\b", r"\bamazon\s+web\s+services\b"],
    "Azure": [r"\bazure\b", r"\bmicrosoft\s+azure\b"],
    "Google Cloud": [r"\bgoogle\s+cloud\b", r"\bgcp\b"],
    "Docker": [r"\bdocker\b"],
    "Kubernetes": [r"\bkubernetes\b", r"\bk8s\b"],
    "Terraform": [r"\bterraform\b"],
    "Ansible": [r"\bansible\b"],
    "Jenkins": [r"\bjenkins\b"],
    "CI/CD": [r"\bci\s*/\s*cd\b", r"\bcontinuous\s+integration\b"],
    "GitHub Actions": [r"\bgithub\s+actions\b"],
    "GitLab CI": [r"\bgitlab\s*ci\b"],
    "Linux": [r"\blinux\b", r"\bubuntu\b", r"\bdebian\b", r"\bcentos\b", r"\bredhat\b"],
    "Nginx": [r"\bnginx\b"],
    "Apache": [r"\bapache\b"],
    "Prometheus": [r"\bprometheus\b"],
    "Grafana": [r"\bgrafana\b"],

    # Data Engineering & Analytics
    "Apache Spark": [r"\bspark\b", r"\bpyspark\b", r"\bapache\s+spark\b"],
    "Apache Kafka": [r"\bkafka\b", r"\bapache\s+kafka\b"],
    "Hadoop": [r"\bhadoop\b"],
    "Apache Airflow": [r"\bairflow\b", r"\bapache\s+airflow\b"],
    "Databricks": [r"\bdatabricks\b"],
    "Tableau": [r"\btableau\b"],
    "Power BI": [r"\bpower\s*bi\b"],

    # Architecture, Methodologies & Tools
    "Git": [r"\bgit\b(?!\s*lab|\s*hub\s*actions)"],
    "Microservices": [r"\bmicroservices?\b", r"\bmicro-services?\b"],
    "Agile": [r"\bagile\b"],
    "Scrum": [r"\bscrum\b"],
    "Unit Testing": [r"\bunit\s+testing\b", r"\bpytest\b", r"\bjest\b", r"\bjunit\b"],
    "Test-Driven Development": [r"\btdd\b", r"\btest[- ]driven\s+development\b"],
    "System Design": [r"\bsystem\s+design\b"],
    "Object-Oriented Programming": [r"\boop\b", r"\bobject[- ]oriented\s+programming\b"],
}

# Precompile all regex patterns for high-performance matching
COMPILED_SKILLS: List[Tuple[str, List[re.Pattern]]] = [
    (canonical_name, [re.compile(p, re.IGNORECASE) for p in patterns])
    for canonical_name, patterns in SKILLS_TAXONOMY.items()
]


def extract_skills_from_text(text: str) -> List[str]:
    """Scan text against the modular skills taxonomy and return unique canonical skill names.

    Args:
        text: Input string (resume or job description).

    Returns:
        List of identified canonical skill names, deduplicated and sorted.
    """
    if not text or not text.strip():
        return []

    identified: Set[str] = set()

    for canonical_name, regex_list in COMPILED_SKILLS:
        for pattern in regex_list:
            if pattern.search(text):
                identified.add(canonical_name)
                break

    return sorted(list(identified))
