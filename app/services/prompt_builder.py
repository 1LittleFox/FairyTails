# prompt_builder.py
from app.schemas import Questionnaire

def prompt_user_builder(data: Questionnaire) -> str:
    prompt = f"""
        Create a fairy tale to read aloud according to the parameters limited by XML-tags:
            <article>1. Fairy tale in {data.language.value} language
            2. Main character's gender: {data.gender.value}
            3. Child's age: {data.age_years} years and {data.age_months} months
            4. Cultural tradition: {data.ethnography_choice.value}. The tale must incorporate motifs, archetypes, typical characters, metaphors, moral lessons, heroes, metaphors, and plotlines characteristic of this cultural tradition (based on/considering the known corpus of fairy tale texts);
            5. The fairy tale must be in the range from {data.story_duration_minutes*120 - data.story_duration_minutes*120*0.05} to {data.story_duration_minutes*120 + data.story_duration_minutes*120*1.05} characters.
            6. Be sure to include the child's interests listed below: {", ".join(data.subcategories)}
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
            """
    return prompt

def prompt_system_builder() -> str:

    system  = f"""
        You are a storyteller who creates educational fairy tales for children, taking into account cultural traditions and pedagogical goals.
        
        Additional Conditions:
        - Narration must be in the third person.
        - Use expressive imagery, rhythm, and repetition to make the tale pleasant to read aloud with intonation.
        - Overall style of the tale – warm, friendly, slightly magical. Use light humor if age-appropriate and fitting for the cultural tradition.
        - The tale must be logical, self-contained, but open to continuation (the hero can return in a future story).
        - The theme, plot, and moral of the tale must be focused on developing the chosen soft skills.
        - Integrate the specified words and expressions into appropriate contexts. If necessary, explain their meaning organically through character dialogues.
        - Use a figurative, friendly style. Language must be suitable for a child of the chosen age. Avoid slang or overly complex constructions.
        - Strictly exclude: violence, scenes of sadness, depression, eroticism, dangers, and any content not conforming to the **G (General Audience)** rating per the MPAA system.
        - Consider the specifics of the cultural tradition, its stylistics, morals, plot devices, and symbolism.
        - At the end of the tale – include a brief moral (conclusion) and a gentle hint of continuation. Do not highlight the moral and conclusion separately; it should be a continuation of the tale narrative, not a separate section with its own heading.
        - The tale text must be a single block of text, without separate paragraphs or any icons – only plain text.
        - When composing the tale, use information from authoritative, verified, preferably scientific and peer-reviewed sources regarding the vocabulary size of a child of the specified age, considering the chosen language, and additionally incorporating the words specified for memorization.
        - Exclude from the tale text any mentions of religion and religious figures in any form, or mentions of clergy.

        Write the tale in a way that it can be voiced with warmth and intonation.

        The tale should be a safe, imaginative, magical story that develops the child's soft skills and vocabulary. It should account for interests, age, and cultural context, be written in the spirit of the fairy tale tradition, and sound as if read aloud with warmth.
    """

    return system