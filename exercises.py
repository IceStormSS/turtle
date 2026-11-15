"""Подбор неверных вариантов ответа для упражнений.

Главная идея: среди вариантов должно быть слово, похожее по звучанию
(`they` / `think` / `then`), иначе ответ угадывается по первой букве.
"""

import random

# Группы слов, которые легко перепутать на слух или при быстром чтении.
# Используются только как «ловушки» в вариантах ответа, в словарь они не входят.
_SOUND_ALIKE = [
    # ---- A0 / A1 ----
    ["they", "then", "than", "there", "their", "them", "these", "those", "think", "thank", "thing"],
    ["we", "be", "me", "he", "she", "see", "sea"],
    ["you", "your", "young", "yours"],
    ["eat", "it", "ate", "eight"],
    ["read", "red", "road", "ready"],
    ["go", "so", "to", "do", "no", "now", "know"],
    ["like", "look", "lake", "line", "life"],
    ["have", "half", "has", "hate"],
    ["house", "horse", "hours"],
    ["bread", "bred", "bead", "brand"],
    ["water", "waiter", "weather", "whether"],
    ["cat", "cut", "cart", "cap", "cot"],
    ["dog", "dig", "dot", "dock"],
    ["book", "look", "cook", "took", "back"],
    ["name", "game", "same", "came"],
    ["boy", "buy", "by", "bye", "toy"],
    ["girl", "goal", "curl"],
    ["sun", "son", "run", "fun", "sung"],
    ["big", "bag", "beg", "bug", "pig"],
    ["small", "smell", "smile"],
    ["good", "god", "food", "wood", "could"],
    ["blue", "blow", "blew", "glue"],
    ["black", "block", "back", "blank"],
    ["one", "won", "on", "once", "own"],
    ["two", "too", "do", "tow"],
    ["three", "tree", "free", "throw", "through"],
    ["mother", "matter", "another", "weather"],
    ["father", "farther", "further", "rather"],
    ["friend", "friendly", "fried"],
    # ---- A2 ----
    ["school", "cool", "skill", "schedule"],
    ["teacher", "teach", "feature", "creature"],
    ["city", "sit"],
    ["family", "famous", "finally"],
    ["milk", "mild", "mill", "silk"],
    ["coffee", "copy", "cough", "toffee"],
    ["food", "foot", "fool", "fed"],
    ["river", "driver", "rider"],
    ["mountain", "mounting", "count", "fountain"],
    ["holiday", "holy", "hospital"],
    ["neighbor", "behaviour", "neighbour", "neighbourhood"],
    ["table", "able", "tale", "stable"],
    ["room", "broom", "root", "rule"],
    ["car", "card", "care", "cat"],
    ["street", "straight", "sweet"],
    ["brother", "bother", "another"],
    ["sister", "system", "sisterly"],
    ["morning", "mourning", "warning"],
    ["night", "knight", "nine", "light", "right"],
    ["day", "they", "say", "may", "stay"],
    ["phone", "fun", "fine", "found"],
    ["music", "museum", "magic"],
    ["work", "walk", "word", "world", "woke"],
    ["live", "leave", "life", "love", "line"],
    ["play", "plan", "place", "pray"],
    ["write", "white", "right", "ride", "wide"],
    ["speak", "peak", "break", "speech"],
    ["want", "won't", "wand", "went"],
    ["see", "sea", "say", "seen", "she"],
    ["walk", "work", "talk", "wake", "wall"],
    ["sleep", "slip", "steep", "sheep", "sweep"],
    ["happy", "happen"],
    ["old", "cold", "gold", "odd"],
    ["new", "now", "few", "knew"],
    ["cold", "gold", "hold", "called"],
    ["hot", "hat", "hit", "hut", "shot"],
    ["today", "tonight", "tomorrow"],
    ["very", "every", "wary", "vary"],
    # ---- B1 ----
    ["weather", "whether", "water", "waiter"],
    ["ticket", "pocket", "ticket"],
    ["shop", "ship", "shape", "stop", "chop"],
    ["doctor", "daughter", "actor"],
    ["price", "prize", "prince", "practice"],
    ["journey", "journal", "journey"],
    ["airport", "report", "import"],
    ["message", "massage", "messenger"],
    ["breakfast", "fast", "break"],
    ["buy", "by", "bye", "boy", "bay"],
    ["travel", "trouble", "traveler"],
    ["forget", "forgive", "forgot"],
    ["remember", "reminder", "member"],
    ["learn", "lean", "earn", "yearn"],
    ["wait", "what", "wet", "weight", "white"],
    ["help", "held", "hello", "yell"],
    ["carry", "marry", "hurry", "cart"],
    ["expensive", "expansive", "expense", "extensive"],
    ["cheap", "chip", "cheat", "sheep", "cheep"],
    ["tired", "tried", "tied", "hired"],
    ["busy", "business", "easy"],
    ["dangerous", "stranger", "danger"],
    ["easy", "busy", "ease", "east"],
    ["difficult", "different", "difficulty"],
    ["famous", "family", "famous"],
    ["never", "ever", "clever", "neither"],
    ["already", "ready", "all ready"],
    ["because", "cause", "become"],
    ["but", "bat", "bit", "cut"],
    ["quickly", "quietly", "quick"],
    ["together", "altogether", "gather"],
    # ---- B2 / C1 ----
    ["experience", "experiment", "expansive"],
    ["opinion", "onion", "opinionated"],
    ["advice", "advise", "device", "devise"],
    ["career", "carrier", "carer", "care"],
    ["government", "environment", "govern"],
    ["habit", "rabbit", "habitat"],
    ["health", "wealth", "help", "heal"],
    ["choice", "choose", "voice", "chose"],
    ["mistake", "take", "mistaken"],
    ["success", "access", "succeed", "assess"],
    ["knowledge", "know", "acknowledge"],
    ["improve", "approve", "prove", "remove"],
    ["suggest", "digest"],
    ["explain", "complain"],
    ["achieve", "archive", "attractive"],
    ["manage", "damage", "manager"],
    ["refuse", "confuse", "refuge", "refute"],
    ["prefer", "prepare", "preferable"],
    ["depend", "defend", "dependable"],
    ["compare", "prepare", "compare"],
    ["increase", "decrease", "increase"],
    ["independent", "dependent", "independently"],
    ["serious", "various", "curious"],
    ["polite", "police", "pilot"],
    ["confident", "confidential", "confidant"],
    ["necessary", "unnecessary", "necessity"],
    ["modern", "mother", "modest"],
    ["curious", "serious", "furious"],
    ["available", "valuable", "avail"],
    ["although", "though", "thought"],
    ["however", "whatever", "whoever", "whenever"],
    ["especially", "specially", "specifically"],
    ["achievement", "agreement", "achieve"],
    ["awareness", "business", "wariness"],
    ["challenge", "change", "challenging"],
    ["consequence", "sequence", "consequent"],
    ["impact", "compact"],
    ["pressure", "pleasure", "treasure"],
    ["resource", "recourse", "source"],
    ["research", "search", "researcher"],
    ["threat", "treat", "thread", "throat"],
    ["acquire", "require", "inquire", "enquire"],
    ["assume", "consume", "presume", "resume"],
    ["contribute", "distribute", "attribute"],
    ["convince", "convict", "convincing"],
    ["overcome", "become", "come"],
    ["reduce", "produce", "deduce", "induce"],
    ["struggle", "structure", "straggle"],
    ["maintain", "obtain", "contain", "remain"],
    ["reliable", "liable", "rely"],
    ["efficient", "sufficient", "inefficient"],
    ["ambitious", "anxious", "ambiguous"],
    ["sufficient", "efficient", "insufficient"],
    ["vulnerable", "valuable", "variable"],
    ["complex", "complete", "complexity"],
    ["hardly", "hard", "hardy"],
    ["rather", "father", "rather"],
]

# слово -> другие слова из его групп
_SIMILAR_INDEX = {}
for _group in _SOUND_ALIKE:
    for _word in _group:
        _key = _word.lower()
        _SIMILAR_INDEX.setdefault(_key, set()).update(
            other.lower() for other in _group if other.lower() != _key
        )


def sound_alikes(word):
    """Слова, которые легко спутать с данным на слух."""
    return sorted(_SIMILAR_INDEX.get((word or "").lower(), ()))


def _common_prefix(a, b):
    n = 0
    for x, y in zip(a, b):
        if x != y:
            break
        n += 1
    return n


def _common_suffix(a, b):
    n = 0
    for x, y in zip(reversed(a), reversed(b)):
        if x != y:
            break
        n += 1
    return n


def spelling_similarity(a, b):
    """Грубая оценка похожести написания: общий префикс/суффикс, длина, буквы."""
    a, b = a.lower(), b.lower()
    if not a or not b:
        return 0
    return (
        _common_prefix(a, b) * 4
        + _common_suffix(a, b) * 3
        + max(0, 3 - abs(len(a) - len(b)))
        + len(set(a) & set(b))
    )


def pick_distractors(correct, candidates, count=3, lang="en", alike_count=2, usage=None, avoid=None):
    """Возвращает `count` неверных вариантов, начиная с похожих по звучанию.

    `candidates` — слова из словаря (правильные ответы других заданий).
    При `lang="en"` в варианты добавляются «ловушки» из групп похожих слов,
    даже если их нет в словаре курса.

    `usage` — необязательный словарь {слово: сколько раз уже было вариантом}.
    Слова с меньшим счётчиком выбираются первыми, поэтому внутри одного урока
    одни и те же варианты не повторяются. Счётчик обновляется на месте.

    `avoid` — слова, которые уже показывали в этом уроке. Они не попадут в
    ответ, пока есть другие подходящие варианты.
    """
    if usage is None:
        usage = {}
    avoid = {w.lower() for w in (avoid or ())}
    correct = (correct or "").strip()
    if not correct:
        return []

    seen = {correct.lower()}
    pool = []
    known = set(seen)
    for cand in candidates:
        cand = (cand or "").strip()
        key = cand.lower()
        if not cand or key in known:
            continue
        known.add(key)
        pool.append(cand)

    chosen = []

    if lang == "en":
        traps = [w for w in sound_alikes(correct) if w not in seen and len(w) > 1]
        fresh = [w for w in traps if w.lower() not in avoid]
        # если свежих «ловушек» не осталось — лучше взять обычные слова,
        # чем повторять те же варианты второй раз
        traps = fresh
        # сначала слова, которые ещё не были вариантами, затем самые похожие
        # по написанию (they -> then/thank/these)
        traps.sort(key=lambda w: (usage.get(w.lower(), 0), -spelling_similarity(correct, w)))
        head = traps[: max(alike_count * 3, 6)]
        random.shuffle(head)
        for trap in head[:alike_count]:
            chosen.append(trap)
            seen.add(trap.lower())

    # добираем словами из словаря: сначала неиспользованные, потом похожие по написанию
    rest = [w for w in pool if w.lower() not in seen]
    need = count - len(chosen)
    fresh = [w for w in rest if w.lower() not in avoid]
    if len(fresh) >= need:
        rest = fresh
    rest.sort(key=lambda w: (usage.get(w.lower(), 0), -spelling_similarity(correct, w)))
    head = rest[:8]
    random.shuffle(head)
    rest = head + rest[8:]
    for word in rest:
        if len(chosen) >= count:
            break
        chosen.append(word)
        seen.add(word.lower())

    # запоминаем, что эти варианты уже показывали
    for word in chosen:
        key = word.lower()
        usage[key] = usage.get(key, 0) + 1

    return chosen[:count]
