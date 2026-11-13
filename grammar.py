"""Грамматический модуль TurtleLingo: окончания, формы слов и правила.

Содержит вопросы по окончаниям (-s, -ed, -ing, -er, -est, -ly, суффиксы -ment, -able, -tion и др.)
с вариантами ответов и поддержкой ввода «от руки».
"""

GRAMMAR_QUESTIONS = [
    # ---------- УРОВЕНЬ A1 (Tier 1) ----------
    {
        "id": "a1_s_works",
        "tier": 1,
        "level_name": "A1",
        "title": "Окончание Present Simple",
        "question": "Какое окончание нужно добавить к глаголу?",
        "sentence": "She work___ at a hospital every day.",
        "target_ending": "-s",
        "target_full": "works",
        "accepted": ["s", "-s", "works"],
        "options": ["-s", "-es", "-ing", "-ed"],
        "correct_idx": 0,
        "explanation": "В Present Simple для местоимений he/she/it к глаголу добавляется окончание -s: she works.",
    },
    {
        "id": "a1_ing_playing",
        "tier": 1,
        "level_name": "A1",
        "title": "Окончание Present Continuous",
        "question": "Какое окончание нужно в Present Continuous?",
        "sentence": "Look! The children are play___ with a ball.",
        "target_ending": "-ing",
        "target_full": "playing",
        "accepted": ["ing", "-ing", "playing"],
        "options": ["-ing", "-s", "-ed", "-es"],
        "correct_idx": 0,
        "explanation": "В Present Continuous (are + глагол) используется окончание -ing: are playing.",
    },
    {
        "id": "a1_es_boxes",
        "tier": 1,
        "level_name": "A1",
        "title": "Окончание множественного числа",
        "question": "Какое окончание нужно для множественного числа слова box?",
        "sentence": "I have two big box___ in my room.",
        "target_ending": "-es",
        "target_full": "boxes",
        "accepted": ["es", "-es", "boxes"],
        "options": ["-es", "-s", "-ies", "-ed"],
        "correct_idx": 0,
        "explanation": "После шипящих звуков и буквы 'x' во множественном числе пишется -es: boxes.",
    },
    {
        "id": "a1_es_goes",
        "tier": 1,
        "level_name": "A1",
        "title": "Окончание глагола на -o",
        "question": "Какое окончание нужно добавить к глаголу go?",
        "sentence": "He go___ to school every morning.",
        "target_ending": "-es",
        "target_full": "goes",
        "accepted": ["es", "-es", "goes"],
        "options": ["-es", "-s", "-ing", "-ed"],
        "correct_idx": 0,
        "explanation": "Глаголы, оканчивающиеся на гласную -o (go, do), в 3-м лице ед. числа принимают -es: goes.",
    },

    # ---------- УРОВЕНЬ A2 (Tier 2) ----------
    {
        "id": "a2_ed_watched",
        "tier": 2,
        "level_name": "A2",
        "title": "Окончание Past Simple (прошедшее время)",
        "question": "Какое окончание нужно глаголу в прошедшем времени?",
        "sentence": "Yesterday we watch___ a fantastic movie.",
        "target_ending": "-ed",
        "target_full": "watched",
        "accepted": ["ed", "-ed", "watched"],
        "options": ["-ed", "-ing", "-s", "-en"],
        "correct_idx": 0,
        "explanation": "В Past Simple правильные глаголы получают окончание -ed: watched.",
    },
    {
        "id": "a2_er_faster",
        "tier": 2,
        "level_name": "A2",
        "title": "Сравнительная степень прилагательных",
        "question": "Какое окончание нужно для сравнения (быстрее)?",
        "sentence": "A train is fast___ than a bicycle.",
        "target_ending": "-er",
        "target_full": "faster",
        "accepted": ["er", "-er", "faster"],
        "options": ["-er", "-est", "-ly", "-ing"],
        "correct_idx": 0,
        "explanation": "Для сравнения односложных прилагательных используется суффикс/окончание -er: faster.",
    },
    {
        "id": "a2_est_highest",
        "tier": 2,
        "level_name": "A2",
        "title": "Превосходная степень прилагательных",
        "question": "Какое окончание нужно для превосходной степени (самый высокий)?",
        "sentence": "Mount Everest is the high___ mountain in the world.",
        "target_ending": "-est",
        "target_full": "highest",
        "accepted": ["est", "-est", "highest"],
        "options": ["-est", "-er", "-ly", "-ed"],
        "correct_idx": 0,
        "explanation": "Превосходная степень с артиклем the образуется с помощью окончания -est: the highest.",
    },
    {
        "id": "a2_d_lived",
        "tier": 2,
        "level_name": "A2",
        "title": "Окончание Past Simple для глаголов на -e",
        "question": "Какое окончание добавляется к live в Past Simple?",
        "sentence": "They liv___ in London two years ago.",
        "target_ending": "-d",
        "target_full": "lived",
        "accepted": ["d", "-d", "ed", "-ed", "lived"],
        "options": ["-d", "-ed", "-ing", "-es"],
        "correct_idx": 0,
        "explanation": "Если глагол уже заканчивается на букву 'e', в Past Simple добавляется только -d: lived.",
    },
    {
        "id": "a2_ied_studied",
        "tier": 2,
        "level_name": "A2",
        "title": "Замена -y на -ied в Past Simple",
        "question": "Какое окончание принимает глагол study в прошедшем времени?",
        "sentence": "He stud___ hard for the exam last night.",
        "target_ending": "-ied",
        "target_full": "studied",
        "accepted": ["ied", "-ied", "studied", "ed", "-ed"],
        "options": ["-ied", "-ed", "-ing", "-s"],
        "correct_idx": 0,
        "explanation": "После согласной буква 'y' меняется на 'i' перед -ed: study -> studied.",
    },

    # ---------- УРОВЕНЬ B1 (Tier 3) ----------
    {
        "id": "b1_ed_perfect",
        "tier": 3,
        "level_name": "B1",
        "title": "Present Perfect (have + V3)",
        "question": "Какое окончание нужно для 3-й формы глагола finish?",
        "sentence": "I have already finish___ my project.",
        "target_ending": "-ed",
        "target_full": "finished",
        "accepted": ["ed", "-ed", "finished"],
        "options": ["-ed", "-ing", "-en", "-s"],
        "correct_idx": 0,
        "explanation": "В Present Perfect (have + V3) правильные глаголы получают окончание -ed: have finished.",
    },
    {
        "id": "b1_ly_fluently",
        "tier": 3,
        "level_name": "B1",
        "title": "Образование наречия от прилагательного",
        "question": "Какой суффикс/окончание превращает fluent (беглый) в 'бегло'?",
        "sentence": "She speaks English very fluent___.",
        "target_ending": "-ly",
        "target_full": "fluently",
        "accepted": ["ly", "-ly", "fluently"],
        "options": ["-ly", "-ful", "-ness", "-ity"],
        "correct_idx": 0,
        "explanation": "Наречия образа действия образуются с помощью суффикса -ly: fluent -> fluently.",
    },
    {
        "id": "b1_ing_preposition",
        "tier": 3,
        "level_name": "B1",
        "title": "Герундий после предлога",
        "question": "Какое окончание требуется после предлога for?",
        "sentence": "Thank you for help___ me with my homework.",
        "target_ending": "-ing",
        "target_full": "helping",
        "accepted": ["ing", "-ing", "helping"],
        "options": ["-ing", "-ed", "-s", "-to"],
        "correct_idx": 0,
        "explanation": "После предлогов (for, in, at, without) глагол всегда ставится с окончанием -ing: helping.",
    },
    {
        "id": "b1_ed_passive",
        "tier": 3,
        "level_name": "B1",
        "title": "Пассивный залог (Passive Voice)",
        "question": "Какое окончание нужно глаголу в пассивном залоге (was deliver___)?",
        "sentence": "The important letter was deliver___ this morning.",
        "target_ending": "-ed",
        "target_full": "delivered",
        "accepted": ["ed", "-ed", "delivered"],
        "options": ["-ed", "-ing", "-s", "-en"],
        "correct_idx": 0,
        "explanation": "Пассивный залог образуется: be + V3 (причастие прошедшего времени с -ed): was delivered.",
    },
    {
        "id": "b1_ed_feeling",
        "tier": 3,
        "level_name": "B1",
        "title": "Прилагательные на -ed и -ing (чувства)",
        "question": "Какое окончание описывает чувство человека (мне скучно)?",
        "sentence": "I was really bor___ during that long conference.",
        "target_ending": "-ed",
        "target_full": "bored",
        "accepted": ["ed", "-ed", "bored"],
        "options": ["-ed", "-ing", "-ly", "-ful"],
        "correct_idx": 0,
        "explanation": "Окончание -ed выражает чувство человека (bored = скучающий), а -ing — качество предмета (boring = скучный).",
    },

    # ---------- УРОВЕНЬ B2 (Tier 4) ----------
    {
        "id": "b2_ment_achievement",
        "tier": 4,
        "level_name": "B2",
        "title": "Суффикс существительного от achieve",
        "question": "Какой суффикс образует существительное 'достижение'?",
        "sentence": "Winning the competition was a great achieve___.",
        "target_ending": "-ment",
        "target_full": "achievement",
        "accepted": ["ment", "-ment", "achievement"],
        "options": ["-ment", "-tion", "-ness", "-ity"],
        "correct_idx": 0,
        "explanation": "От глагола achieve существительное образуется с помощью суффикса -ment: achievement.",
    },
    {
        "id": "b2_able_reliable",
        "tier": 4,
        "level_name": "B2",
        "title": "Суффикс прилагательного (надёжный)",
        "question": "Какой суффикс нужен для образования слова 'reliable'?",
        "sentence": "He is a very reli___ friend whom you can always trust.",
        "target_ending": "-able",
        "target_full": "reliable",
        "accepted": ["able", "-able", "reliable"],
        "options": ["-able", "-ible", "-ful", "-ous"],
        "correct_idx": 0,
        "explanation": "От rely (полагаться) прилагательное 'надёжный' образуется с суффиксом -able: reliable.",
    },
    {
        "id": "b2_ence_evidence",
        "tier": 4,
        "level_name": "B2",
        "title": "Суффикс абстрактного существительного",
        "question": "Какой суффикс образует слово 'доказательство' (evidence)?",
        "sentence": "There is strong scientific evid___ supporting this theory.",
        "target_ending": "-ence",
        "target_full": "evidence",
        "accepted": ["ence", "-ence", "evidence"],
        "options": ["-ence", "-ance", "-ment", "-ness"],
        "correct_idx": 0,
        "explanation": "От прилагательного evident существительное образуется с помощью суффикса -ence: evidence.",
    },
    {
        "id": "b2_participle_having",
        "tier": 4,
        "level_name": "B2",
        "title": "Перфектное причастие (Participle Clause)",
        "question": "Какое окончание образует деепричастную форму 'Закончив работу'?",
        "sentence": "Hav___ completed the report, she turned off the computer.",
        "target_ending": "-ing",
        "target_full": "Having",
        "accepted": ["ing", "-ing", "having"],
        "options": ["-ing", "-en", "-ed", "-s"],
        "correct_idx": 0,
        "explanation": "Perfect Participle образуется конструкцией Having + V3: Having completed... (Закончив...).",
    },
    {
        "id": "b2_ly_eventually",
        "tier": 4,
        "level_name": "B2",
        "title": "Продвинутое наречие связи",
        "question": "Какой суффикс образует наречие 'eventually' (в конце концов)?",
        "sentence": "It was a tough challenge, but eventual___ they succeeded.",
        "target_ending": "-ly",
        "target_full": "eventually",
        "accepted": ["ly", "-ly", "eventually"],
        "options": ["-ly", "-ness", "-able", "-tion"],
        "correct_idx": 0,
        "explanation": "От прилагательного eventual наречие образуется с суффиксом -ly: eventually.",
    },
]

# Группировка вопросов по уровням
QUESTIONS_BY_TIER = {
    1: [q for q in GRAMMAR_QUESTIONS if q["tier"] == 1],
    2: [q for q in GRAMMAR_QUESTIONS if q["tier"] == 2],
    3: [q for q in GRAMMAR_QUESTIONS if q["tier"] == 3],
    4: [q for q in GRAMMAR_QUESTIONS if q["tier"] == 4],
}


def normalize_answer(ans: str) -> str:
    """Очищает строку ответа для сравнения: нижний регистр, без дефисов и пробелов."""
    if ans is None:
        return ""
    text = str(ans).strip().lower()
    # удаляем ведущий дефис, если есть (например '-ed' -> 'ed')
    if text.startswith("-"):
        text = text[1:]
    return text.strip()


def check_grammar_answer(q: dict, user_val) -> tuple[bool, str]:
    """Проверяет ответ пользователя (индекс опции или введенный вручную текст).

    Возвращает (is_correct, explanation_text).
    """
    if isinstance(user_val, int) or (isinstance(user_val, str) and user_val.isdigit()):
        idx = int(user_val)
        is_ok = (idx == q["correct_idx"])
        return is_ok, q["explanation"]

    # Проверка текста, введенного от руки
    norm_val = normalize_answer(str(user_val))
    norm_accepted = [normalize_answer(a) for a in q.get("accepted", [])]
    norm_target = normalize_answer(q.get("target_ending", ""))
    norm_full = normalize_answer(q.get("target_full", ""))

    is_ok = (norm_val in norm_accepted) or (norm_val == norm_target) or (norm_val == norm_full)
    return is_ok, q["explanation"]


# Справочник грамматических правил для вкладки «Грамматика» в приложении
GRAMMAR_TOPICS = [
    {
        "level": "A1",
        "title": "Окончания -s / -es в Present Simple",
        "badge": "Базовый",
        "description": "В настоящем простом времени (Present Simple), когда подлежащее he, she или it (он, она, оно), к смысловому глаголу обязательно прибавляется окончание -s или -es.",
        "rules": [
            {"label": "Обычные глаголы", "rule": "work -> works, play -> plays, read -> reads"},
            {"label": "Глаголы на -ch, -sh, -s, -x, -z, -o", "rule": "watch -> watches, wash -> washes, go -> goes, do -> does"},
            {"label": "Глаголы на согласную + y", "rule": "fly -> flies, study -> studies (y меняется на ie)"},
        ],
        "example": "She work<b>s</b> at a hospital. He go<b>es</b> to school.",
    },
    {
        "level": "A1",
        "title": "Окончание -ing в Present Continuous",
        "badge": "Базовый",
        "description": "Когда действие происходит прямо сейчас, мы используем форму am/is/are + глагол с окончанием -ing.",
        "rules": [
            {"label": "Обычное добавление", "rule": "play -> playing, read -> reading"},
            {"label": "Удвоение согласной", "rule": "run -> running, swim -> swimming (если один краткий гласный звук перед согласной)"},
            {"label": "Немая -e на конце", "rule": "make -> making, write -> writing (буква 'e' выпадает)"},
        ],
        "example": "The children are play<b>ing</b> with a ball right now.",
    },
    {
        "level": "A2",
        "title": "Окончание -ed в Past Simple",
        "badge": "Элементарный",
        "description": "Для выражения действий в прошлом у правильных английских глаголов добавляется окончание -ed.",
        "rules": [
            {"label": "Стандартное окончание", "rule": "watch -> watched, help -> helped"},
            {"label": "Если глагол уже на -e", "rule": "live -> lived, decide -> decided (добавляем только -d)"},
            {"label": "Глагол на согласную + y", "rule": "study -> studied, carry -> carried (y меняется на ied)"},
        ],
        "example": "Yesterday we watch<b>ed</b> a movie and liv<b>ed</b> the moment.",
    },
    {
        "level": "A2",
        "title": "Степени сравнения: -er и -est",
        "badge": "Элементарный",
        "description": "Для коротких (односложных) прилагательных сравнительная степень образуется добавлением -er, а превосходная — артиклем the и окончанием -est.",
        "rules": [
            {"label": "Сравнительная (-er)", "rule": "fast -> faster (быстрее), tall -> taller (выше)"},
            {"label": "Превосходная (-est)", "rule": "fast -> the fastest (самый быстрый), high -> the highest (самый высокий)"},
        ],
        "example": "A train is fast<b>er</b> than a bicycle, but planes are the fast<b>est</b>.",
    },
    {
        "level": "B1",
        "title": "Окончание -ed в Present Perfect и Passive Voice",
        "badge": "Средний",
        "description": "3-я форма правильных глаголов (Past Participle) также оканчивается на -ed. Она нужна для Present Perfect (have + V3) и пассивного залога (be + V3).",
        "rules": [
            {"label": "Present Perfect", "rule": "I have finish<b>ed</b> my work. (Я закончил работу)"},
            {"label": "Passive Voice", "rule": "The letter was deliver<b>ed</b>. (Письмо было доставлено)"},
            {"label": "Суффикс наречия -ly", "rule": "fluent -> fluent<b>ly</b> (бегло), quick -> quick<b>ly</b> (быстро)"},
        ],
        "example": "She speaks English fluent<b>ly</b> and has finish<b>ed</b> her project.",
    },
    {
        "level": "B2",
        "title": "Словообразовательные суффиксы: -ment, -able, -ence, -tion",
        "badge": "Выше среднего",
        "description": "На уровне B2 важно понимать словообразование: как из глаголов получаются существительные и сложные прилагательные.",
        "rules": [
            {"label": "-ment (существительное действия)", "rule": "achieve -> achieve<b>ment</b> (достижение), develop -> develop<b>ment</b>"},
            {"label": "-able / -ible (возможность качества)", "rule": "rely -> reli<b>able</b> (надёжный), flex -> flex<b>ible</b> (гибкий)"},
            {"label": "-ence / -ance (абстрактные понятия)", "rule": "evident -> evid<b>ence</b> (доказательство), perform -> perform<b>ance</b>"},
            {"label": "Participle clauses (-ing / -ed)", "rule": "Hav<b>ing</b> finished... (Закончив...), Know<b>ing</b> the answer..."},
        ],
        "example": "Winning was a great achieve<b>ment</b> for this reli<b>able</b> team.",
    },
]
