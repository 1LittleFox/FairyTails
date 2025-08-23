from app.schemas import Questionnaire

# Расширенная таблица соответствия длительности и количества слов
DURATION_TO_CHARS = {
    1: {"min": 600, "max": 700},
    2: {"min": 1200, "max": 1400},
    3: {"min": 1800, "max": 2100},
    4: {"min": 2400, "max": 2800},
    5: {"min": 3000, "max": 3500},
    6: {"min": 3600, "max": 4200},
    7: {"min": 4200, "max": 4900},
    8: {"min": 4800, "max": 5600},
    9: {"min": 5400, "max": 6300},
    10: {"min": 6000, "max": 7000},
    11: {"min": 6600, "max": 7700},
    12: {"min": 7200, "max": 8400},
    13: {"min": 7800, "max": 9100},
    14: {"min": 8400, "max": 9800},
    15: {"min": 9000, "max": 10500},
    16: {"min": 9600, "max": 11200},
    17: {"min": 10200, "max": 11900},
    18: {"min": 10800, "max": 12600},
    19: {"min": 11400, "max": 13300},
    20: {"min": 12000, "max": 14000},
    21: {"min": 12600, "max": 14700},
    22: {"min": 13200, "max": 15400},
    23: {"min": 13800, "max": 16100},
    24: {"min": 14400, "max": 16800},
    25: {"min": 15000, "max": 17500},
    26: {"min": 15600, "max": 18200},
    27: {"min": 16200, "max": 18900},
    28: {"min": 16800, "max": 19600},
    29: {"min": 17400, "max": 20300},
    30: {"min": 18000, "max": 21000},
    31: {"min": 18600, "max": 21700},
    32: {"min": 19200, "max": 22400},
    33: {"min": 19800, "max": 23100},
    34: {"min": 20400, "max": 23800},
    35: {"min": 21000, "max": 24500},
    36: {"min": 21600, "max": 25200},
    37: {"min": 22200, "max": 25900},
    38: {"min": 22800, "max": 26600},
    39: {"min": 23400, "max": 27300},
    40: {"min": 24000, "max": 28000},
    41: {"min": 24600, "max": 28700},
    42: {"min": 25200, "max": 29400},
    43: {"min": 25800, "max": 30100},
    44: {"min": 26400, "max": 30800},
    45: {"min": 27000, "max": 31500},
    46: {"min": 27600, "max": 32200},
    47: {"min": 28200, "max": 32900},
    48: {"min": 28800, "max": 33600},
    49: {"min": 29400, "max": 34300},
    50: {"min": 30000, "max": 35000},
    51: {"min": 30600, "max": 35700},
    52: {"min": 31200, "max": 36400},
    53: {"min": 31800, "max": 37100},
    54: {"min": 32400, "max": 37800},
    55: {"min": 33000, "max": 38500},
    56: {"min": 33600, "max": 39200},
    57: {"min": 34200, "max": 39900},
    58: {"min": 34800, "max": 40600},
    59: {"min": 35400, "max": 41300},
    60: {"min": 36000, "max": 42000},
}

def prompt_user_builder(data: Questionnaire) -> dict:
    word_range = DURATION_TO_CHARS.get(
        data.story_duration_minutes,
        {"min": data.story_duration_minutes * 120, "max": data.story_duration_minutes * 138}
    )

    # Форматируем возраст
    age_text = f"{data.age_years} лет"
    if data.age_months > 0:
        age_text += f" {data.age_months} месяцев"

    # Форматируем гендер
    gender = {"M": "boy", "F": "girl"}.get(data.gender, "any gender")

    # Форматируем язык
    language = {"РУС": "Russian", "ENG": "English", "FRA": "French"}.get(data.language)

    awg_chars = (word_range['min'] + word_range['max']) / 2


    system_message = """
        # System Prompt: Educational Storyteller for Children

        You are a master storyteller specializing in educational fairy tales that nurture children's development through engaging narratives.
        
        ## Your Expertise
        - **Child Development**: Age-appropriate content and vocabulary building
        - **Cultural Storytelling**: Authentic representation of global fairy tale traditions
        - **Pedagogical Design**: Soft skills development through character actions
        - **Safe Content Creation**: Positive, encouraging narratives without frightening elements
        
        ## Story Structure Framework
        Follow classic narrative arc with balanced pacing:
        - **Opening** (10-15%): Introduce character and setting
        - **Inciting Incident** (5-10%): Present the challenge or adventure
        - **Rising Action** (50-70%): Character growth through experiences
        - **Climax** (10-15%): Key moment demonstrating learned skills
        - **Resolution** (5-10%): Satisfying conclusion with gentle reflection
        
        ## Core Storytelling Principles
        
        **Narrative Style:**
        - Third-person narration with warm, engaging tone
        - Rhythmic, expressive language suitable for read-aloud
        - Natural vocabulary expansion through context clues
        - Show character growth through actions, not exposition
        
        **Content Guidelines:**
        - Maintain G-rated, universally appropriate content
        - Focus on positive problem-solving and collaboration
        - Present challenges as learning opportunities
        - Include gentle humor and wonder without scary elements
        
        **Strict Content Restrictions:**
        - NO violence, injury, death, or physical harm to any character
        - NO frightening elements (darkness, monsters, being lost or abandoned)
        - NO conflict resolution through aggression or punishment
        - NO profanity, inappropriate language, or adult themes
        - NO religious references or specific denominational content
        - NO stereotypes or culturally insensitive portrayals
        
        **Educational Integration:**
        - Embed target vocabulary naturally in multiple contexts
        - Demonstrate soft skills through character decisions
        - Represent cultural traditions authentically
        - End with subtle invitation for reflection
        
        ## Quality Standards
        
        **Vocabulary Development:**
        - Use each target word minimum 2 times in different contexts
        - Provide natural context clues for unfamiliar terms
        - Balance familiar and new vocabulary appropriately
        
        **Skill Demonstration:**
        - Show soft skills through pivotal character actions
        - Make skill application feel natural to the story
        - Avoid explicit skill naming or forced teaching moments
        
        **Cultural Authenticity:**
        - Research and respect cultural storytelling traditions
        - Include authentic details that enhance rather than stereotype
        - Balance cultural specificity with universal themes
        
        ## Output Requirements
        - Deliver complete story in flowing narrative prose
        - No structural labels, headers, or visible story mechanics
        - Maintain consistent tone and pacing throughout
        - Ensure logical character motivation and growth
        - Create satisfying resolution that feels earned
        
        ## Example Opening Style
        *"In a village where morning mist danced between ancient olive trees, young Aria discovered that the most ordinary stones could hold extraordinary secrets. As she carefully examined each smooth pebble by the fountain, her grandmother's words echoed in her mind: 'Patient eyes see what hurried ones miss.'"*
        
        **Task**: Create an educational fairy tale incorporating specified vocabulary, cultural tradition, and soft skills while maintaining engaging storytelling that captivates young listeners.
    """

    user_message = f"""
        Create a fairy tale for read-aloud narration based on the following parameters:
        
        STORY PARAMETERS:       
            Language: {language}
            Main character gender: {gender}
            Child's age: {age_text}
            Cultural tradition: {data.ethnography_choice} (incorporate motifs, archetypes, characters, metaphors, and moral lessons from this tradition)
            Duration: {data.story_duration_minutes} minutes (from {word_range['min']} to {word_range['max']} characters)
            Child's interests: {", ".join(data.subcategories)}
            Target vocabulary: {", ".join(data.target_words)} (integrate naturally into text, use each word minimum 2 times, explain unfamiliar words through actions or dialogue)
            Target soft skills: {data.soft_skills} (develop through plot situations, dialogue, and character actions)
            
        DETAILED STRUCTURE:
            Exposition — Story opening with basic information about the story world: where, when, who the main character is, their circumstances, character traits, setting. Create "foundation" for the reader, establish tone and atmosphere. Answer: who? where? when? Introduce key characters, hint at their qualities. Use vivid world descriptions, brief everyday scenes. Don't overload with facts — create a living world while maintaining interest.
            Inciting Incident — Moment when an event appears that triggers change. "First push" toward action, reason for disrupting the peaceful world. Clear transition from calm to action, first conflict or challenge. Formulate the story's main questions: will the hero succeed? What goal lies before them? Show that the hero must act differently.
            Rising Action — Largest section. Series of events showing the hero's response to the challenge: tries different approaches, makes mistakes, learns, interacts with characters, faces difficulties, progresses toward the goal. Deepen characters, show character changes. Create dynamics with increasing tension. Hero's actions must logically flow from their character.
            Climax — Peak of tension. Greatest challenge, critical situation, strongest opponent. Here it's decided whether the hero can overcome the obstacle and reach their goal. Reveal the main intrigue. Hero uses everything learned or makes a choice showing growth. Key soft skill is tested in action.
            Resolution — Ending showing changes after the climax. Characters' fates are clear, conflict is resolved. Answer: what became of the hero? What did they learn? What about the world? Make it clear, bright, and kind. Include a hidden question — invitation to apply the experience in life.
            Create a complete artistic story that sounds natural when read aloud with warmth and expression. The tale should be magical and engaging, subtly developing target soft skills and vocabulary.
        
        OUTPUT GUIDELINES:        
            Write in flowing narrative prose without structural labels
            Use warm, expressive language suitable for read-aloud
            Maintain consistent tone and cultural authenticity
            Balance familiar and new vocabulary naturally
            End with gentle invitation for reflection
    """

    return {
        "system": system_message,
        "user": user_message,
        "awg": awg_chars
    }