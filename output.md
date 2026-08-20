FUNCTION
seed_metric_templates
seed_database.py:23
Triggered by: "I have a list of LLM as a judge metric"
🎯 Intent: I have a list of LLM as a judge metric
seed_metric_templates (function) at seed_database.py:23
Signature: def seed_metric_templates(db: Database)
python • lines 23-105

Copy
def seed_metric_templates(db: Database):
    """Seed quality evaluation metric templates"""
    print("\n📊 Seeding Metric Templates (Quality Evaluation)...")
    
    metric_templates = [
        {
            "key": "accuracy",
            "metric_kind": "standard",
            "impl_type": "llm_judge",
            "value_type": "numeric",
            "unit": "%",
            "definition": "Measures correctness of the response",
            "aggregation_strategy": "mean",
            "default_weight": 1.0,
            "default_visible": True,
            "version": 1
        },
        {
            "key": "relevance",
            "metric_kind": "standard",
            "impl_type": "llm_judge",
            "value_type": "numeric",
            "unit": "score",
            "definition": "Measures how relevant the response is to the query",
            "aggregation_strategy": "mean",
            "default_weight": 1.0,
            "default_visible": True,
            "version": 1
        },
        {
            "key": "completeness",
            "metric_kind": "standard",
            "impl_type": "llm_judge",
            "value_type": "numeric",
            "unit": "score",
            "definition": "Measures whether the response fully addresses the query",
            "aggregation_strategy": "mean",
            "default_weight": 0.8,
            "default_visible": True,
            "version": 1
        },
        {
            "key": "conciseness",
            "metric_kind": "
Total: 17428.2ms
FTS: 53.4ms
Qwen: 16863ms
FUNCTION
seed_metric_templates
seed_database.py:23
Triggered by: "I have a list of LLM as a judge metric"
🎯 Intent: I have a list of LLM as a judge metric
seed_metric_templates (function) at seed_database.py:23
Signature: def seed_metric_templates(db: Database)
python • lines 23-105

Copy
def seed_metric_templates(db: Database):
    """Seed quality evaluation metric templates"""
    print("\n📊 Seeding Metric Templates (Quality Evaluation)...")
    
    metric_templates = [
        {
            "key": "accuracy",
            "metric_kind": "standard",
            "impl_type": "llm_judge",
            "value_type": "numeric",
            "unit": "%",
            "definition": "Measures correctness of the response",
            "aggregation_strategy": "mean",
            "default_weight": 1.0,
            "default_visible": True,
            "version": 1
        },
        {
            "key": "relevance",
            "metric_kind": "standard",
            "impl_type": "llm_judge",
            "value_type": "numeric",
            "unit": "score",
            "definition": "Measures how relevant the response is to the query",
            "aggregation_strategy": "mean",
            "default_weight": 1.0,
            "default_visible": True,
            "version": 1
        },
        {
            "key": "completeness",
            "metric_kind": "standard",
            "impl_type": "llm_judge",
            "value_type": "numeric",
            "unit": "score",
            "definition": "Measures whether the response fully addresses the query",
            "aggregation_strategy": "mean",
            "default_weight": 0.8,
            "default_visible": True,
            "version": 1
        },
        {
            "key": "conciseness",
            "metric_kind": "
Total: 17428.2ms
FTS: 53.4ms
Qwen: 16863ms
FUNCTION
seed_metric_templates
seed_database.py:23
Triggered by: "I want to tell you about what are the LLM as a judge metric that I used for evaluations"
🎯 Intent: The developer wants to identify and understand the LLM-as-a-judge evaluation metrics and templates configured in the codebase.
The codebase defines quality evaluation metrics, vulnerability templates, and attack vectors seeded via seed_metric_templates(db: Database) (in seed_database.py:23), seed_vulnerability_templates(db: Database) (in seed_database.py:108), and seed_attack_vector_templates(db: Database) (in seed_database.py:164).
These metrics are registered into the PostgreSQL database managed by the Database class (in app/database_v2.py:25) during the database seeding process orchestrated by the main() function (in seed_database.py:248).
python • lines 23-105

Copy
def seed_metric_templates(db: Database):
    """Seed quality evaluation metric templates"""
    print("\n📊 Seeding Metric Templates (Quality Evaluation)...")
    
    metric_templates = [
        {
            "key": "accuracy",
            "metric_kind": "standard",
            "impl_type": "llm_judge",
            "value_type": "numeric",
            "unit": "%",
            "definition": "Measures correctness of the response",
            "aggregation_strategy": "mean",
            "default_weight": 1.0,
            "default_visible": True,
            "version": 1
        },
        {
            "key": "relevance",
            "metric_kind": "standard",
            "impl_type": "llm_judge",
            "value_type": "numeric",
            "unit": "score",
            "definition": "Measures how relevant the response is to the query",
            "aggregation_strategy": "mean",
            "default_weight": 1.0,
            "default_visible": True,
            "version": 1
        },
        {
            "key": "completeness",
            "metric_kind": "standard",
            "impl_type": "llm_judge",
            "value_type": "numeric",
            "unit": "score",
            "definition": "Measures whether the response fully addresses the query",
            "aggregation_strategy": "mean",
            "default_weight": 0.8,
            "default_visible": True,
            "version": 1
        },
        {
            "key": "conciseness",
            "metric_kind": "
Total: 5447.8ms
FTS: 62.4ms
Qwen: 4828.1ms
FUNCTION
seed_metric_templates
seed_database.py:23
Triggered by: "I want to tell you about what are the LLM as a judge metric that I used for evaluations"
🎯 Intent: The developer wants to identify and understand the LLM-as-a-judge evaluation metrics and templates configured in the codebase.
The codebase defines quality evaluation metrics, vulnerability templates, and attack vectors seeded via seed_metric_templates(db: Database) (in seed_database.py:23), seed_vulnerability_templates(db: Database) (in seed_database.py:108), and seed_attack_vector_templates(db: Database) (in seed_database.py:164).
These metrics are registered into the PostgreSQL database managed by the Database class (in app/database_v2.py:25) during the database seeding process orchestrated by the main() function (in seed_database.py:248).
python • lines 23-105

Copy
def seed_metric_templates(db: Database):
    """Seed quality evaluation metric templates"""
    print("\n📊 Seeding Metric Templates (Quality Evaluation)...")
    
    metric_templates = [
        {
            "key": "accuracy",
            "metric_kind": "standard",
            "impl_type": "llm_judge",
            "value_type": "numeric",
            "unit": "%",
            "definition": "Measures correctness of the response",
            "aggregation_strategy": "mean",
            "default_weight": 1.0,
            "default_visible": True,
            "version": 1
        },
        {
            "key": "relevance",
            "metric_kind": "standard",
            "impl_type": "llm_judge",
            "value_type": "numeric",
            "unit": "score",
            "definition": "Measures how relevant the response is to the query",
            "aggregation_strategy": "mean",
            "default_weight": 1.0,
            "default_visible": True,
            "version": 1
        },
        {
            "key": "completeness",
            "metric_kind": "standard",
            "impl_type": "llm_judge",
            "value_type": "numeric",
            "unit": "score",
            "definition": "Measures whether the response fully addresses the query",
            "aggregation_strategy": "mean",
            "default_weight": 0.8,
            "default_visible": True,
            "version": 1
        },
        {
            "key": "conciseness",
            "metric_kind": "
Total: 5447.8ms
FTS: 62.4ms
Qwen: 4828.1ms
CLASS
EvaluationEngine
app/evaluator/engine.py:21
Triggered by: "also I have a list of metric that I used for LLM as a judge for evaluation of prompts and outputs"
🎯 Intent: also I have a list of metric that I used for LLM as a judge for evaluation of prompts and outputs
- MetricConfig (app/evaluator/config.py:28) – defines each metric (name, enabled flag, optional custom prompt). - MetricsListResponse (app/models.py:99) – API response model that returns the available metrics as a list of {name, description} dictionaries. - EvaluationEngine (app/evaluator/engine.py:21) – orchestrates loading of metric configurations and makes them available to the evaluation pipeline.
python • lines 21-793

Copy
class EvaluationEngine:
    """
    Main evaluation orchestrator
    
    Features:
    ---------
    • Loads traces from various sources
    • Extracts evaluation context
    • Executes metrics in parallel
    • Aggregates results
    • Enhances traces with scores
    • Exports results
    
    Example:
    --------
    engine = EvaluationEngine(config)
    result = engine.evaluate_trace("trace.json", metrics=["hallucination", "relevance"])
    print(f"Quality: {result.overall_quality:.2f} ({result.quality_grade})")
    """
    
    def __init__(self, config: Optional[EvaluationConfig] = None):
        """
        Initialize evaluation engine
        
        Args:
            config: Evaluation configuration (uses defaults if None)
        """
        self.config = config or EvaluationConfig()
        
        # Initialize components
        self.loader = TraceLoader()
Total: 8737.6ms
FTS: 70.4ms
Qwen: 6538.4ms
CLASS
EvaluationEngine
app/evaluator/engine.py:21
Triggered by: "also I have a list of metric that I used for LLM as a judge for evaluation of prompts and outputs"
🎯 Intent: also I have a list of metric that I used for LLM as a judge for evaluation of prompts and outputs
- MetricConfig (app/evaluator/config.py:28) – defines each metric (name, enabled flag, optional custom prompt). - MetricsListResponse (app/models.py:99) – API response model that returns the available metrics as a list of {name, description} dictionaries. - EvaluationEngine (app/evaluator/engine.py:21) – orchestrates loading of metric configurations and makes them available to the evaluation pipeline.
python • lines 21-793

Copy
class EvaluationEngine:
    """
    Main evaluation orchestrator
    
    Features:
    ---------
    • Loads traces from various sources
    • Extracts evaluation context
    • Executes metrics in parallel
    • Aggregates results
    • Enhances traces with scores
    • Exports results
    
    Example:
    --------
    engine = EvaluationEngine(config)
    result = engine.evaluate_trace("trace.json", metrics=["hallucination", "relevance"])
    print(f"Quality: {result.overall_quality:.2f} ({result.quality_grade})")
    """
    
    def __init__(self, config: Optional[EvaluationConfig] = None):
        """
        Initialize evaluation engine
        
        Args:
            config: Evaluation configuration (uses defaults if None)
        """
        self.config = config or EvaluationConfig()
        
        # Initialize components
        self.loader = TraceLoader()
Total: 8737.6ms
FTS: 70.4ms
Qwen: 6538.4ms
CLASS
Vulnerability
app/security/core.py:14
Triggered by: "So now I have list of vulnerabilities that I use in the guardrails."
🎯 Intent: Identify where the list of vulnerability categories used by the guardrails is defined.
app/security/core.py:14 – The Vulnerability enum enumerates all guardrail vulnerability categories (S1‑S23).
This enum supplies the canonical list for guardrail logic: it is referenced by ValiqorAttackGenerator._generate_base_prompts, run_red_team_simulation, and other security components to select and apply specific vulnerability‑based attacks.
python • lines 14-44

Copy
class Vulnerability(enum.Enum):
    """
    Enumeration of vulnerability categories corresponding to the guardrail's S1-S23.
    """
    VIOLENCE = ("S1", "Violence")
    SEXUAL = ("S2", "Sexual")
    CRIMINAL_PLANNING = ("S3", "Criminal Planning/Confessions")
    GUNS_ILLEGAL_WEAPONS = ("S4", "Guns and Illegal Weapons")
    CONTROLLED_SUBSTANCES = ("S5", "Controlled/Regulated Substances")
    SUICIDE_SELF_HARM = ("S6", "Suicide and Self Harm")
    SEXUAL_MINOR = ("S7", "Sexual (minor)")
    HATE_IDENTITY_HATE = ("S8", "Hate/Identity Hate")
    PII_PRIVACY = ("S9", "PII/Privacy")
    HARASSMENT = ("S10", "Harassment")
    THREAT = ("S11", "Threat")
    PROFANITY = ("S12", "Profanity")
    NEEDS_CAUTION = ("S13", "Needs Caution")
    OTHER = ("S14", "Other")
    MANIPULATION = ("S15", "Manipulation")
    FRAUD_DECEPTION = ("S16", "Fraud/Deception")
    MALWARE = ("S17", "Malware")
    HIGH_RISK_GOV = ("S18", "High Risk Gov Decision Making")
    POLITICAL_MISINFO = ("S19", "Political/Misinformation/Conspiracy")
    COPYRIGHT = ("S20", "Copyright/Trademark/Plagiarism")
    UNAUTHORIZED_ADVICE = ("S21", "Unauthorized Advice")
    ILLEGAL_ACTIVITY = ("S22", "Illegal Activity")
    IMMORAL_UNETHICAL = ("S23", "Immoral/Unethical")

    def __init__(self, code: str, description: str):
        self.code = code
        self.description = description
Total: 7926.7ms
FTS: 39.7ms
Qwen: 6825.7ms
CLASS
Vulnerability
app/security/core.py:14
Triggered by: "So now I have list of vulnerabilities that I use in the guardrails."
🎯 Intent: Identify where the list of vulnerability categories used by the guardrails is defined.
app/security/core.py:14 – The Vulnerability enum enumerates all guardrail vulnerability categories (S1‑S23).
This enum supplies the canonical list for guardrail logic: it is referenced by ValiqorAttackGenerator._generate_base_prompts, run_red_team_simulation, and other security components to select and apply specific vulnerability‑based attacks.
python • lines 14-44

Copy
class Vulnerability(enum.Enum):
    """
    Enumeration of vulnerability categories corresponding to the guardrail's S1-S23.
    """
    VIOLENCE = ("S1", "Violence")
    SEXUAL = ("S2", "Sexual")
    CRIMINAL_PLANNING = ("S3", "Criminal Planning/Confessions")
    GUNS_ILLEGAL_WEAPONS = ("S4", "Guns and Illegal Weapons")
    CONTROLLED_SUBSTANCES = ("S5", "Controlled/Regulated Substances")
    SUICIDE_SELF_HARM = ("S6", "Suicide and Self Harm")
    SEXUAL_MINOR = ("S7", "Sexual (minor)")
    HATE_IDENTITY_HATE = ("S8", "Hate/Identity Hate")
    PII_PRIVACY = ("S9", "PII/Privacy")
    HARASSMENT = ("S10", "Harassment")
    THREAT = ("S11", "Threat")
    PROFANITY = ("S12", "Profanity")
    NEEDS_CAUTION = ("S13", "Needs Caution")
    OTHER = ("S14", "Other")
    MANIPULATION = ("S15", "Manipulation")
    FRAUD_DECEPTION = ("S16", "Fraud/Deception")
    MALWARE = ("S17", "Malware")
    HIGH_RISK_GOV = ("S18", "High Risk Gov Decision Making")
    POLITICAL_MISINFO = ("S19", "Political/Misinformation/Conspiracy")
    COPYRIGHT = ("S20", "Copyright/Trademark/Plagiarism")
    UNAUTHORIZED_ADVICE = ("S21", "Unauthorized Advice")
    ILLEGAL_ACTIVITY = ("S22", "Illegal Activity")
    IMMORAL_UNETHICAL = ("S23", "Immoral/Unethical")

    def __init__(self, code: str, description: str):
        self.code = code
        self.description = description
Total: 7926.7ms
FTS: 39.7ms
Qwen: 6825.7ms
FUNCTION
run_guardrail_check
app/security/guardrail.py:69
Triggered by: "I work with various guardrails for the LLM and the prompt and the outputs. It has a list of it."
🎯 Intent: Provide an inventory of the LLM guardrail components (functions, classes, enums) and explain how they are invoked.
- Guardrail entry point: run_guardrail_check (app/security/guardrail.py:69) - Core evaluator class: ValiqorEvaluator (app/security/core.py:381) - Vulnerability categories enum: Vulnerability (app/security/core.py:14) - Dataset‑level safety evaluator: evaluate_security_dataset (app/security/evaluator.py:12)
The workflow starts with run_guardrail_check(user_input, agent_output, conversation_memory, openai_api_key), which constructs a ValiqorEvaluator instance and calls its evaluate method (ValiqorEvaluator.evaluate(self, user_input, agent_output, conversation_memory)). The evaluator uses the Vulnerability enum to map detected issues to the S1‑S23 guardrail list and may invoke evaluate_security_dataset for batch assessments. All guardrail logic is centralized around these symbols.
python • lines 69-99

Copy
def run_guardrail_check(user_input: str, agent_output: str, conversation_memory: str, openai_api_key: Optional[str] = None) -> dict:
    # Use custom client if API key provided, otherwise use default
    llm_client = OpenAI(api_key=openai_api_key) if openai_api_key else client
    
    prompt = GUARDRAIL_PROMPT.format(
        user_input=user_input,
        agent_output=agent_output,
        conversation_memory=conversation_memory
    )

    response = llm_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        # max_tokens=150
    )

    raw = response.choices[0].message.content.strip()
    
    # Remove markdown code blocks if present
    if raw.startswith("```json"):
        raw = raw[7:]  # Remove ```json
    if raw.startswith("```"):
        raw = raw[3:]  # Remove ```
    if raw.endswith("```"):
        raw = raw[:-3]  # Remove trailing ```
    raw = raw.strip()
    
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "invalid JSON", "raw": raw}
Total: 7156.6ms
FTS: 52.7ms
Qwen: 6313.9ms
FUNCTION
run_guardrail_check
app/security/guardrail.py:69
Triggered by: "I work with various guardrails for the LLM and the prompt and the outputs. It has a list of it."
🎯 Intent: Provide an inventory of the LLM guardrail components (functions, classes, enums) and explain how they are invoked.
- Guardrail entry point: run_guardrail_check (app/security/guardrail.py:69) - Core evaluator class: ValiqorEvaluator (app/security/core.py:381) - Vulnerability categories enum: Vulnerability (app/security/core.py:14) - Dataset‑level safety evaluator: evaluate_security_dataset (app/security/evaluator.py:12)
The workflow starts with run_guardrail_check(user_input, agent_output, conversation_memory, openai_api_key), which constructs a ValiqorEvaluator instance and calls its evaluate method (ValiqorEvaluator.evaluate(self, user_input, agent_output, conversation_memory)). The evaluator uses the Vulnerability enum to map detected issues to the S1‑S23 guardrail list and may invoke evaluate_security_dataset for batch assessments. All guardrail logic is centralized around these symbols.
python • lines 69-99

Copy
def run_guardrail_check(user_input: str, agent_output: str, conversation_memory: str, openai_api_key: Optional[str] = None) -> dict:
    # Use custom client if API key provided, otherwise use default
    llm_client = OpenAI(api_key=openai_api_key) if openai_api_key else client
    
    prompt = GUARDRAIL_PROMPT.format(
        user_input=user_input,
        agent_output=agent_output,
        conversation_memory=conversation_memory
    )

    response = llm_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        # max_tokens=150
    )

    raw = response.choices[0].message.content.strip()
    
    # Remove markdown code blocks if present
    if raw.startswith("```json"):
        raw = raw[7:]  # Remove ```json
    if raw.startswith("```"):
        raw = raw[3:]  # Remove ```
    if raw.endswith("```"):
        raw = raw[:-3]  # Remove trailing ```
    raw = raw.strip()
    
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "invalid JSON", "raw": raw}
Total: 7156.6ms
FTS: 52.7ms
Qwen: 6313.9ms