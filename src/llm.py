from typing import Optional
from openai import OpenAI

from database import AbstractRepository
from prompts.get_query import prompt as get_query_prompt
from prompts.get_explanation import prompt as explanation_prompt


from settings import get_settings
from logger import get_logger


settings = get_settings()
logger = get_logger(__name__)


class LLMClient:
    def __init__(self):
        self.client = OpenAI(
            base_url=settings.LLM_API_URL, api_key=settings.LLM_API_KEY
        )
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.seed = settings.LLM_SEED

    def query(self, prompt: str) -> Optional[str]:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                seed=self.seed,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"LLM request error: {e}")
            return None


class QueryHandler:
    def __init__(self, db_manager: AbstractRepository):
        self.db = db_manager
        self.llm = LLMClient()
        self.table = settings.SQLITE_TABLE

    def handle_request(self, question: str, verbose: bool = False) -> None:
        if not question.strip() or len(question.strip()) < 5:
            logger.error("Question too short or empty.")
            return

        if not self.db.table_exists(self.table):
            logger.error(f"Table '{self.table}' not found in database.")
            return

        structure = self.db.get_table_structure()
        categorical, numerical = self.db.analyze_columns(self.table)

        prompt = get_query_prompt.format(
            table_name=self.table,
            columns=", ".join(structure[self.table]),
            question=question,
            categorical="\n".join(
                [f"{col} - {', '.join(values)}" for col, values in categorical.items()]
            ),
            numerical=", ".join(numerical),
        )

        sql_code = self.llm.query(prompt).strip("`sql").strip("`").strip()
        if not sql_code.lower().startswith("select"):
            logger.error("Invalid SQL generated:")
            print(sql_code)
            return

        try:
            result_df = self.db.execute_query(sql_code)
        except Exception as e:
            logger.error(f"SQL execution failed:\n{e}")
            return

        if result_df.empty:
            logger.info("Query returned no results.")
            return

        if verbose:
            print("\n🔍 Generated SQL:")
            print(sql_code)
            print("\n📊 Result:")
            print(result_df.to_string(index=False))

        explanation = explanation_prompt.format(
            sql_code=sql_code,
            result=result_df.head(10).to_markdown(index=False),
            question=question,
        )

        answer = self.llm.query(explanation)
        if not answer or any(
            k in answer.lower() for k in ["error", "can't", "unknown"]
        ):
            logger.warning("Failed to interpret result.")
            return

        print("\n💬 Answer:")
        print(answer)
