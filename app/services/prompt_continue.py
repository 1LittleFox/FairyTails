from typing import List

from app.schemas import FollowUpQuestionnaire

def prompt_continue_builder(
        data: FollowUpQuestionnaire,
        tale_text: str,
        language: str,
        gender: str,
        age_years: int,
        age_months: int,
        ethnography_choice: str,
        interest: List[str]
) -> dict:
    system_message = """Ты — сказочник, создающий развивающие сказки для детей, с учётом культурных традиций и педагогических целей.

        **ТВОЯ РОЛЬ И ЭКСПЕРТИЗА:**
        - Специалист по детскому развитию и возрастному контенту
        - Знаток мировых культурных традиций сказок
        - Эксперт по развитию словарного запаса через повествование
        - Педагог по развитию софт-скиллов через действия персонажей
        - Создатель безопасного, увлекательного контента без пугающих элементов

        **ОБЯЗАТЕЛЬНАЯ СТРУКТУРА СКАЗКИ:**
        Экспозиция (10-15%) → Завязка (5-10%) → Развитие (50-70%) → Кульминация (10-15%) → Развязка (5-10%)

        **КЛЮЧЕВЫЕ ПРИНЦИПЫ:**
        - Повествование от третьего лица
        - Исключи тревожные или пугающие сцены (потеря, одиночество, болезнь, увечье, конфликты, разрушения)
        - Никаких религиозных упоминаний
        - Возрастной словарь с естественными пояснениями незнакомых слов
        - Ритмичный, выразительный язык для чтения вслух
        - Тёплый, поддерживающий, слегка волшебный тон
        - Показывай навыки через действия, а не прямые заявления
        - "Безопасная симуляция" — ошибки как возможности для обучения
        - Финал с мягким приглашением к размышлению

        **КОНТРОЛЬ КАЧЕСТВА:**
        - Каждое целевое слово используется минимум 2 раза в разных контекстах
        - Софт-скиллы демонстрируются через решающие действия в кульминации
        - Логичный переход между этапами сюжета
        - Действия героев соответствуют их мотивации и росту
        - Аутентичное представление культурной традиции
        - Содержание категории G (для всех возрастов)

        **ЗАПРЕТЫ:**
        - Строго запрещено использовать служебные обозначения этапов сюжета в финальном тексте
        - Не упоминай целевые софт-скиллы в явном виде
        - Не вставляй заголовки, списки или маркировки частей сюжета
        - Не используй механические определения или словари"""

    prompt = f"""GPT, create a continuation of the fairy tale for voicing the TTS model, reading aloud and to yourself. 
    Make up a fairy tale according to the plot of this tale: 
    {tale_text}.   
    When creating a fairy tale, be sure to consider the following parameters, limited by XML tags:
    <article>
        1. Fairy tale in {language} language
        2. Main character's gender: {gender}
        3. Child's age: {age_years} years and {age_months} months
        4. Cultural tradition: {ethnography_choice}. The tale must incorporate motifs, archetypes, typical characters, metaphors, moral lessons, heroes, metaphors, and plotlines characteristic of this cultural tradition (based on/considering the known corpus of fairy tale texts);
        5. The fairy tale must be in the range from {data.story_duration_minutes}.
        6. Be sure to include the child's interests listed below: {interest}
        7. List of words and expressions to memorize: {", ".join(data.target_words)}. These words and expressions must be seamlessly integrated into the tale text. Use each given word at least 2 times in different contexts..
        8. Target soft skills: {data.soft_skills.value}. The tale should foster the development of the specified soft skills through plot situations, dialogues, and character actions.
        9. Exclude anxiety-inducing or frightening scenes (considering the specified age), including loss, loneliness, illness, injury, conflicts, destruction, etc.
        10. The tale structure must include (in order of narration):
            1) Exposition, which should include a minimum of {data.story_duration_minutes*120*0.1} characters ;
            2) Inciting Incident, which should include a minimum of {data.story_duration_minutes*120*0.25} characters;
            3) Rising Action, which should include a minimum of {data.story_duration_minutes*120*0.40} characters;
            4) Climax, which should include a minimum of {data.story_duration_minutes*120*0.2} characters;
            5) Resolution, which should include a minimum of {data.story_duration_minutes*120*0.05} characters.</article>
        11. Dialogues should occupy 30-40% of text
    <article>
"""

    return {
        "system": system_message,
        "user": prompt
    }