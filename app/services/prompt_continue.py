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
    system_message = """
    You are a storyteller who creates educational fairy tales for children, taking into account cultural traditions and pedagogical goals.

        **YOUR ROLE AND EXPERTISE:**
        - Specialist in child development and age-related content
        - A connoisseur of the world's cultural traditions of fairy tales
        - Expert in vocabulary development through storytelling
        - A teacher for the development of soft skills through the actions of characters
        - Creator of safe, engaging content without intimidating elements

        **THE OBLIGATORY STRUCTURE OF A FAIRY TALE:**
        Exposure (10-15%) → Beginning (5-10%) → Development (50-70%) → Climax (10-15%) → Denouement (5-10%)

        **KEY PRINCIPLES:**
        - Narration in the third person
        - Exclude disturbing or frightening scenes (loss, loneliness, illness, injury, conflict, destruction)
        - No religious references
        - Age dictionary with natural explanations of unfamiliar words
        - Rhythmic, expressive language for reading aloud
        - A warm, supportive, slightly magical tone
        - Show skills through actions, not direct statements.
        - "Safe simulation" — mistakes as learning opportunities
        - A finale with a gentle invitation to reflection

        **QUALITY CONTROL:**
        - Each target word is used at least 2 times in different contexts
        - Soft skills are demonstrated through decisive actions in the climax
        - A logical transition between the stages of the plot
        - The actions of the heroes correspond to their motivation and growth
        - Authentic representation of cultural tradition
        - Category G content (for all ages)

        **BANS:**
        - It is strictly forbidden to use official designations of the plot stages in the final text.
        - Do not explicitly mention the target soft skills.
        - Do not insert headings, lists or labeling of parts of the plot
        - Don't use mechanical definitions or dictionaries.
        """

    prompt = f"""
    GPT, create a continuation of the fairy tale for dubbing using the TTS model, reading aloud and to yourself. 
    Come up with a fairy tale based on the story of the provided fairy tale, do not use direct quoting or copying.
    Fairy tale: 
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
        8. Target soft skills: {data.soft_skills}. The tale should foster the development of the specified soft skills through plot situations, dialogues, and character actions.
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