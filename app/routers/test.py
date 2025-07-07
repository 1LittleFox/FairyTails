from app.schemas import Questionnaire


def prompt_user_builder(data: Questionnaire) -> str:
    signs_before = data.story_duration_minutes * 120 - (data.story_duration_minutes * 120)/2
    sings_after = data.story_duration_minutes * 120 + (data.story_duration_minutes * 120)/2

    conclusion = f"От {signs_before} до {sings_after} символов"
    return conclusion

print(prompt_user_builder())