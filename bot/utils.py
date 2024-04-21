from datetime import datetime
from requests import RequestException
from g4f.client import Client, AsyncClient
import deepl
from bot.settings import settings
from googletrans import Translator


g4f_client = AsyncClient()

prompt = '''
You're the best friend!
'''.strip()


async def translate_sentence(text: str, target_lang: str = 'en'):
    '''Translate sentence to destination language'''
    if settings.DEEPL_TOKEN:
        # deepl
        translator = deepl.Translator(settings.DEEPL_TOKEN)
        translation = await translator.translate_text("Hello, world!", target_lang=target_lang).text
    else:
        # googletrans (optional - free). But not that good translation. Use deepl (below)
        translator = Translator()
        translation = await translator.translate(text, target_lang).text

    return translation


async def ask_llm(prompt: str) -> str:
    """
    Generate a LLM completion based on the provided prompt
    Args:
        prompt: str     
    """
    try:
        resp = await g4f_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": f"Always talk in English. Prompt: {prompt}"}],
        )
        resp_text = resp.choices[0].message.content

        return resp_text
    except RequestException as e:
        print('ask_llm RequestException exc:', e)
        return ''
    except Exception as e:
        print('ask_llm exc:', e)
        return ''
