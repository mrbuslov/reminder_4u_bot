from reminder.schemas import RemindersListSchema, GPTModelName
from reminder.utils import GPT_MODELS

from langchain_core.prompts import PromptTemplate


def set_reminder(text: str) -> None:
    model = GPT_MODELS[GPTModelName.GPT_4O.value]
    structured_llm = model.with_structured_output(RemindersListSchema)

    #     model = GPT_MODELS[GPTModelName.GPT_4O_MINI.value]
    #     prompt = PromptTemplate.from_template(SUMMARIZING_PROMPT)
    #     chain = prompt | model.llm_instance
    #     summarized = []
    #     # NOTE: although we take a single-paged pdf, we should make a check, that number of text's tokens is less than max_input_tokens
    #     if num_tokens_from_string(text, model.encoding) > model.max_input_tokens:
    #         for chunk in split_string_up_to_token_limit(text, model):
    #             summarized.append(model.invoke(chunk, runnable=chain))
    #     else:
    #         summarized = [model.invoke(text, runnable=chain)]
