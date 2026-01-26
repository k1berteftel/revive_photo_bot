
def get_rate_form(amount: int, rate_type: str = "restore") -> str:
    """
    Склонение слов 'реставрация' или 'оживление' в зависимости от числа

    Args:
        amount: количество
        word_type: тип слова - "restore" (реставрация) или "revive" (оживление)

    Returns:
        Слово в правильной форме
    """
    if rate_type == "restore":
        word_forms = ["реставрация", "реставрации", "реставраций"]
    else:
        word_forms = ["оживление", "оживления", "оживлений"]

    # Правило для чисел
    if amount % 10 == 1 and amount % 100 != 11:
        return word_forms[0]  # 1, 21, 31, ... (но не 11)
    elif 2 <= amount % 10 <= 4 and not (12 <= amount % 100 <= 14):
        return word_forms[1]  # 2-4, 22-24, 32-34, ... (но не 12-14)
    else:
        return word_forms[2]


def get_action_prompt(action: str) -> tuple[str, str]:
    if action == 'hug':
        prompt = ("cinematic short film, professional color grading, person making gentle hugging gesture with arms, "
                  "affectionate expression, warm smile, subtle arm movement as if embracing someone, "
                  "emotional connection visible in eyes, soft natural lighting, realistic skin textures, "
                  "film grain, 24fps, 4k, photorealistic, masterpiece, modest clothing, family moment")
        motion_id = 'd2389a9a-91c2-4276-bc9c-c9e35e8fb85a'
    elif action == 'kiss':
        prompt = ("cinematic short film, professional color grading, person showing tender affectionate expression, "
                  "gentle lip movement suggesting a kiss, soft romantic smile, eyes expressing warmth, "
                  "subtle head tilt, emotional moment, soft cinematic lighting, realistic textures, ")
        motion_id = 'aab8440c-0d65-4554-b88a-7a9a5e084b6e'
    elif action == 'greeting':
        prompt = ("cinematic short film, professional color grading, person giving friendly greeting, "
                  "subtle wave of hand, warm welcoming smile, eye contact with viewer, "
                  "gentle nod, approachable expression, natural friendly gesture, "
                  "soft lighting, realistic skin details, film grain, 4k, photorealistic")
        motion_id = 'd2389a9a-91c2-4276-bc9c-c9e35e8fb85a'
    elif action == 'air':
        prompt = ("cinematic short film, professional color grading, person playfully blowing air kiss, "
                  "flirtatious but tasteful expression, subtle wink, hand gracefully raised, "
                  "charming smile, elegant gesture, lighthearted moment, soft lighting, "
                  "realistic textures, film grain, 4k, photorealistic, classy")
        motion_id = '0ab33462-481e-4c78-8ffc-086bebd84187'
    else:
        prompt = ("professional historical photo restoration, cinematic color grading, "
                  "natural subtle facial animation, gentle breathing movement, soft blink, "
                  "very slight smile, realistic skin textures restored, authentic colorization, "
                  "soft cinematic lighting, film grain, 4k, photorealistic masterpiece, "
                  "period-accurate appearance, respectful restoration")
        motion_id = 'aab8440c-0d65-4554-b88a-7a9a5e084b6e'
    return prompt, motion_id