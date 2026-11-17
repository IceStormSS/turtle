/* ========================================================
   TurtleLingo — Interactive Frontend Application Logic
   ======================================================== */

// Глобальное состояние
const state = {
  user: {
    id: 1,
    name: "Друг",
    level: 2, // По умолчанию A2
    pool: 2,
    xp: 0,
    streak: 0,
    tested: 0,
    learned_count: 0,
    total_words: 180,
  },
  soundEnabled: true,
  currentTab: "learn",
  testSession: null,
  lessonSession: null,
  dictWords: [],
  dictGrammar: [],
  currentDictLevel: "all",
  currentDictTab: "words",
};

// ---------------------------------------------------------------- Telegram Mini App
const tgWebApp = window.Telegram?.WebApp;
const tgInitData = tgWebApp?.initData || "";
const tgUser = tgWebApp?.initDataUnsafe?.user;

if (tgWebApp) {
  try {
    tgWebApp.ready();
    tgWebApp.expand();
  } catch (e) {
    console.log("TG WebApp init error:", e);
  }
}

// Подписанные данные Telegram уходят с каждым запросом к API:
// сервер сам определяет пользователя по подписи и отдаёт его прогресс.
const _fetch = window.fetch.bind(window);
window.fetch = (url, opts = {}) => {
  if (tgInitData && typeof url === "string" && url.startsWith("/api/")) {
    opts.headers = { ...(opts.headers || {}), "X-Tg-Init-Data": tgInitData };
  }
  return _fetch(url, opts);
};

const LEVEL_NAMES = {
  0: "A0 — Начальный 🥚",
  1: "A1 — Базовый 🐣",
  2: "A2 — Элементарный 🐢",
  3: "B1 — Средний 🌿",
  4: "B2 — Выше среднего 🏆",
};

const LEVEL_SHORT = {
  0: "A0",
  1: "A1",
  2: "A2",
  3: "B1",
  4: "B2",
};

// ---------------------------------------------------------------- Звуковые эффекты (Web Audio API)
let audioCtx = null;

function initAudio() {
  if (!audioCtx) {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (AudioContext) {
      audioCtx = new AudioContext();
    }
  }
}

function playTone(freq, duration, type = "sine", delay = 0) {
  if (!state.soundEnabled) return;
  initAudio();
  if (!audioCtx) return;

  setTimeout(() => {
    try {
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, audioCtx.currentTime);

      gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);

      osc.connect(gain);
      gain.connect(audioCtx.destination);

      osc.start();
      osc.stop(audioCtx.currentTime + duration);
    } catch (e) {
      console.warn("Audio error:", e);
    }
  }, delay * 1000);
}

function playSuccessSound() {
  playTone(523.25, 0.12, "sine", 0);     // C5
  playTone(659.25, 0.12, "sine", 0.08);  // E5
  playTone(783.99, 0.25, "triangle", 0.16); // G5
}

function playErrorSound() {
  playTone(260, 0.15, "triangle", 0);
  playTone(220, 0.25, "sawtooth", 0.1);
}

function playFinishSound() {
  playTone(523.25, 0.15, "sine", 0);
  playTone(659.25, 0.15, "sine", 0.12);
  playTone(783.99, 0.15, "sine", 0.24);
  playTone(1046.5, 0.4, "triangle", 0.36);
}

function toggleSound() {
  state.soundEnabled = !state.soundEnabled;
  document.getElementById("sound-icon").textContent = state.soundEnabled ? "🔊" : "🔇";
}

// Озвучка английского через браузерный SpeechSynthesis
function speakText(text) {
  if (!("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const clean = text.replace(/___/g, "").replace(/[<>]/g, "");
  const utter = new SpeechSynthesisUtterance(clean);
  utter.lang = "en-US";
  utter.rate = 0.9;
  window.speechSynthesis.speak(utter);
}

// ---------------------------------------------------------------- Навигация по вкладкам
function navigate(tabName) {
  state.currentTab = tabName;

  document.querySelectorAll(".nav-item").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.tab === tabName);
  });

  document.querySelectorAll(".view-section").forEach((sec) => {
    sec.classList.remove("active");
  });

  const target = document.getElementById(`view-${tabName}`);
  if (target) {
    target.classList.add("active");
  }

  if (tabName === "dictionary") {
    loadDictionaryData();
  } else if (tabName === "profile") {
    renderProfile();
  }
}

// ---------------------------------------------------------------- Загрузка данных пользователя
async function fetchUser() {
  try {
    const res = await fetch("/api/user");
    if (res.ok) {
      const data = await res.json();
      state.user = data;
      updateHeaderStats();
    }
  } catch (e) {
    console.warn("API user fetch error:", e);
  }
}

function updateHeaderStats() {
  document.getElementById("stat-streak").textContent = state.user.streak;
  document.getElementById("stat-xp").textContent = state.user.xp;
  document.getElementById("stat-level").textContent = LEVEL_SHORT[state.user.level] || "A2";
  
  const learnBadge = document.getElementById("learn-level-badge");
  if (learnBadge) {
    learnBadge.textContent = `Уровень: ${LEVEL_NAMES[state.user.level]}`;
  }

  // Обновление активной кнопки на профиле
  for (let i = 0; i <= 4; i++) {
    const b = document.getElementById(`btn-lvl-${i}`);
    if (b) b.classList.toggle("active", state.user.level === i);
  }
}

// ---------------------------------------------------------------- ТЕСТ УРОВНЯ
async function startTest() {
  initAudio();
  try {
    const res = await fetch("/api/test/start");
    const data = await res.json();

    state.testSession = {
      questions: data.questions,
      curIndex: 0,
      scoresByTier: { 1: 0, 2: 0, 3: 0, 4: 0 },
      history: [],
      answeredCurrent: false,
    };

    document.getElementById("test-intro").style.display = "none";
    document.getElementById("test-summary").style.display = "none";
    document.getElementById("test-runner").style.display = "block";

    renderTestQuestion();
  } catch (err) {
    alert("Ошибка загрузки теста: " + err);
  }
}

function renderTestQuestion() {
  const s = state.testSession;
  const q = s.questions[s.curIndex];
  s.answeredCurrent = false;

  // Прогресс
  const total = s.questions.length;
  const current = s.curIndex + 1;
  const pct = Math.round(((current - 1) / total) * 100);
  document.getElementById("test-progress-fill").style.width = `${pct}%`;
  document.getElementById("test-counter").textContent = `Вопрос ${current}/${total}`;

  // Бейджи и заголовки
  document.getElementById("test-tier-badge").textContent = `Уровень ${q.level_name || 'A' + q.tier}`;
  document.getElementById("test-kind-badge").textContent = q.category === "grammar" ? "📐 Грамматика и окончания" : "📖 Словарный запас";
  document.getElementById("test-q-title").textContent = q.title || "Вопрос";
  document.getElementById("test-q-prompt").textContent = q.question;

  // Предложение с пропуском
  const sentBox = document.getElementById("test-sentence-text");
  sentBox.innerHTML = q.sentence ? q.sentence.replace("___", "<u>&nbsp;&nbsp;?&nbsp;&nbsp;</u>") : "";

  // Варианты ответов
  const grid = document.getElementById("test-options-grid");
  grid.innerHTML = "";
  q.options.forEach((opt, idx) => {
    const btn = document.createElement("button");
    btn.className = "option-btn";
    btn.innerHTML = `<span style="opacity: 0.5; font-size: 13px;">${idx + 1}.</span> ${opt}`;
    btn.onclick = () => submitTestAnswer(idx);
    grid.appendChild(btn);
  });

  // Поле ввода от руки
  const handInput = document.getElementById("test-hand-input");
  handInput.value = "";
  handInput.disabled = false;
  handInput.placeholder = q.category === "grammar" 
    ? "Введи окончание (например: -ed, watched)..." 
    : "Введи перевод или пропущенное слово...";
  handInput.onkeydown = (e) => {
    if (e.key === "Enter") submitTestHandwritten();
  };

  // Скрыть панель обратной связи
  document.getElementById("test-feedback").style.display = "none";

  // Новый вопрос теста начинаем с его начала
  requestAnimationFrame(() => {
    const card = document.getElementById("test-runner");
    if (card) card.scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

async function submitTestAnswer(choice) {
  const s = state.testSession;
  if (s.answeredCurrent) return;
  s.answeredCurrent = true;

  const q = s.questions[s.curIndex];
  
  // Запрос на сервер для точной валидации
  let isCorrect = false;
  let explanation = "";

  try {
    const res = await fetch("/api/test/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question_id: q.id,
        q_data: q,
        user_input: choice,
      }),
    });
    const checkRes = await res.json();
    isCorrect = checkRes.is_correct;
    explanation = checkRes.explanation;
  } catch (e) {
    // Резервная клиентская проверка
    if (choice === -1) {
      isCorrect = false;
    } else if (typeof choice === "number") {
      isCorrect = (choice === q.correct_idx);
    }
    explanation = q.explanation || "";
  }

  // Обновление баллов
  if (isCorrect) {
    s.scoresByTier[q.tier] = (s.scoresByTier[q.tier] || 0) + 1;
    playSuccessSound();
  } else {
    playErrorSound();
  }

  s.history.push({ q, isCorrect, choice });

  // Подсветка кнопок
  const buttons = document.querySelectorAll("#test-options-grid .option-btn");
  buttons.forEach((btn, idx) => {
    btn.disabled = true;
    if (idx === q.correct_idx) {
      btn.classList.add("correct-highlight");
    } else if (idx === choice && !isCorrect) {
      btn.classList.add("wrong-highlight");
    }
  });

  document.getElementById("test-hand-input").disabled = true;

  // Показ фидбека
  const fb = document.getElementById("test-feedback");
  fb.className = `feedback-drawer ${isCorrect ? "correct" : "wrong"}`;
  document.getElementById("test-fb-icon").textContent = isCorrect ? "✅" : "💡";
  document.getElementById("test-fb-title").textContent = isCorrect ? "Верно!" : "Не совсем";
  document.getElementById("test-fb-desc").textContent = explanation;
  fb.style.display = "flex";

  // Прокручиваем к панели с кнопкой «Следующий вопрос»
  requestAnimationFrame(() => {
    fb.scrollIntoView({ behavior: "smooth", block: "center" });
    const nextBtn = document.getElementById("test-next-btn");
    if (nextBtn) nextBtn.focus({ preventScroll: true });
  });
}

function submitTestHandwritten() {
  const input = document.getElementById("test-hand-input");
  const val = input.value.trim();
  if (!val) return;
  submitTestAnswer(val);
}

function speakCurrentTestSentence() {
  const s = state.testSession;
  if (!s) return;
  const q = s.questions[s.curIndex];
  if (q && q.sentence) speakText(q.sentence);
}

async function nextTestQuestion() {
  const s = state.testSession;
  s.curIndex++;

  // Проверка завершения блока уровня (по 3 вопроса на уровень)
  const answered = s.curIndex;
  const currentQ = s.questions[answered - 1];
  const tier = currentQ.tier;

  const tierFinished = answered % 3 === 0;
  // Если на текущем уровне пользователь набрал меньше 2 из 3, завершаем тест досрочно,
  // чтобы не завышать уровень до B2 тем, кто знает только A2-B1!
  const shouldEarlyStop = tierFinished && (s.scoresByTier[tier] < 2);

  if (answered >= s.questions.length || shouldEarlyStop) {
    await finishTest();
  } else {
    renderTestQuestion();
  }
}

async function finishTest() {
  const s = state.testSession;
  document.getElementById("test-progress-fill").style.width = "100%";

  // Определение уровня:
  // Уровень 0 (A0) - база
  // Уровень 1 (A1) - если Tier 1 >= 2
  // Уровень 2 (A2) - если Tier 1 >= 2 и Tier 2 >= 2
  // Уровень 3 (B1) - если Tier 1, 2, 3 >= 2
  // Уровень 4 (B2) - если Tier 1, 2, 3, 4 >= 2
  let determinedLevel = 0;
  for (let t = 1; t <= 4; t++) {
    if (s.scoresByTier[t] >= 2) {
      determinedLevel = t;
    } else {
      break;
    }
  }

  try {
    const res = await fetch("/api/test/finish", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        level: determinedLevel,
        scores: s.scoresByTier,
      }),
    });
    if (res.ok) {
      const data = await res.json();
      state.user = data.user;
      updateHeaderStats();
    }
  } catch (e) {
    state.user.level = determinedLevel;
    state.user.tested = 1;
    updateHeaderStats();
  }

  // Показ сводки
  document.getElementById("test-runner").style.display = "none";
  const summary = document.getElementById("test-summary");
  summary.style.display = "block";

  document.getElementById("test-final-level-name").textContent = LEVEL_NAMES[determinedLevel];
  
  const descriptions = {
    0: "Самое начало пути! Мы начнём с базовых местоимений, приветствий и простых слов.",
    1: "Базовый уровень (A1). Ты понимаешь простую речь и настоящее время. Будем развивать фразы и окончания!",
    2: "Элементарный уровень (A2). Ты отлично справляешься с базой и прошедшим временем -ed! Мы закрепим сравнения и расширим словарный запас.",
    3: "Средний уровень (B1). Уверенное владение временами (Present Perfect, -ly, предлоги). Движемся к свободным обсуждениям!",
    4: "Выше среднего (B2). Отличное понимание сложных суффиксов (-ment, -able) и конструкций!",
  };
  document.getElementById("test-result-description").textContent = descriptions[determinedLevel] || "";

  // Разбивка по этапам
  const breakdown = document.getElementById("test-tier-breakdown");
  breakdown.innerHTML = "";
  for (let t = 1; t <= 4; t++) {
    const row = document.createElement("div");
    row.className = "tier-score-row";
    const passed = (s.scoresByTier[t] >= 2);
    row.innerHTML = `
      <span>Уровень ${t === 1 ? 'A1 (Базовый)' : t === 2 ? 'A2 (Элементарный)' : t === 3 ? 'B1 (Средний)' : 'B2 (Выше среднего)'}</span>
      <span style="color: ${passed ? 'var(--primary-dark)' : 'var(--text-muted)'}">${s.scoresByTier[t]} из 3 ${passed ? '✅' : '⚪'}</span>
    `;
    breakdown.appendChild(row);
  }

  playFinishSound();
  launchConfetti();
}

function exitTest() {
  if (confirm("Выйти из теста уровня? Прогресс текущего теста не сохранится.")) {
    document.getElementById("test-runner").style.display = "none";
    document.getElementById("test-intro").style.display = "block";
  }
}

// ---------------------------------------------------------------- УРОКИ (ОБУЧЕНИЕ)
async function startLesson() {
  initAudio();
  try {
    const res = await fetch("/api/lesson/start");
    const data = await res.json();

    state.lessonSession = {
      words: data.words,
      queue: data.queue,
      curItem: null,
      xpGained: 0,
      okCount: 0,
      totalCount: data.words.length,
      currentDone: 0,
    };

    document.getElementById("lesson-welcome").style.display = "none";
    document.getElementById("lesson-summary").style.display = "none";
    document.getElementById("lesson-runner").style.display = "block";

    renderLessonQuestion();
  } catch (err) {
    alert("Ошибка загрузки урока: " + err);
  }
}

function renderLessonQuestion() {
  const s = state.lessonSession;
  if (!s.queue.length) {
    finishLesson();
    return;
  }

  const item = s.queue[0];
  s.curItem = item;
  s.answeredCurrent = false;

  // Прогресс
  const pct = Math.round((s.currentDone / s.totalCount) * 100);
  document.getElementById("lesson-progress-fill").style.width = `${pct}%`;
  document.getElementById("lesson-counter").textContent = `${s.currentDone + 1}/${s.totalCount}`;

  // Тексты вопроса
  const qType = document.getElementById("lesson-q-type");
  const qPrompt = document.getElementById("lesson-q-prompt");
  const sentBox = document.getElementById("lesson-sentence-text");
  const hintBox = document.getElementById("lesson-hint-box");
  const hintText = document.getElementById("lesson-hint-text");

  if (item.kind === "grammar") {
    qType.textContent = "📐 Грамматика и окончания";
    qPrompt.textContent = item.ex.question;
    sentBox.innerHTML = item.ex.sentence.replace("___", "<u>&nbsp;&nbsp;?&nbsp;&nbsp;</u>");
    hintBox.style.display = "none";
  } else if (item.kind === "gap") {
    qType.textContent = "Вставь пропущенное слово";
    qPrompt.textContent = "Какое слово пропущено в предложении?";
    sentBox.innerHTML = item.word.sent.replace("___", "<u>&nbsp;&nbsp;?&nbsp;&nbsp;</u>");
    hintBox.style.display = "block";
    hintText.textContent = item.word.ru;
  } else if (item.kind === "en2ru") {
    qType.textContent = "Перевод с английского";
    qPrompt.textContent = `Как переводится слово:`;
    sentBox.innerHTML = `<b>${item.word.en}</b>`;
    hintBox.style.display = "none";
  } else {
    qType.textContent = "Перевод на английский";
    qPrompt.textContent = `Как по-английски:`;
    sentBox.innerHTML = `<b>${item.word.ru}</b>`;
    hintBox.style.display = "none";
  }

  // Варианты ответов
  const grid = document.getElementById("lesson-options-grid");
  grid.innerHTML = "";
  item.ex.options.forEach((opt, idx) => {
    const btn = document.createElement("button");
    btn.className = "option-btn";
    btn.innerHTML = `<span style="opacity: 0.5; font-size: 13px;">${idx + 1}.</span> ${opt}`;
    btn.onclick = () => submitLessonAnswer(idx);
    grid.appendChild(btn);
  });

  // Ввод от руки
  const handInput = document.getElementById("lesson-hand-input");
  handInput.value = "";
  handInput.disabled = false;
  handInput.placeholder = item.kind === "grammar" 
    ? "Введи окончание (например: -ed, -s)..." 
    : "Введи слово на английском или перевод...";
  handInput.onkeydown = (e) => {
    if (e.key === "Enter") submitLessonHandwritten();
  };

  document.getElementById("lesson-feedback").style.display = "none";

  // Новый вопрос начинаем с его начала, а не с места, где была кнопка «Дальше»
  requestAnimationFrame(() => {
    document.getElementById("lesson-runner").scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

async function submitLessonAnswer(choice) {
  const s = state.lessonSession;
  if (s.answeredCurrent) return;
  s.answeredCurrent = true;

  const item = s.curItem;
  let isCorrect = false;
  let explanation = "";

  try {
    const res = await fetch("/api/lesson/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        item: item,
        choice: choice,
      }),
    });
    const checkRes = await res.json();
    isCorrect = checkRes.is_correct;
    explanation = checkRes.explanation;
  } catch (e) {
    if (typeof choice === "number") {
      isCorrect = (choice === item.ex.correct);
    }
  }

  if (isCorrect) {
    s.xpGained += item.retry ? 5 : 10;
    if (!item.retry) s.okCount++;
    s.currentDone++;
    playSuccessSound();
    s.queue.shift(); // Убираем из очереди
  } else {
    playErrorSound();
    // Если ошибся, отправляем повторить в конец урока
    s.queue.shift();
    item.retry = true;
    s.queue.push(item);
  }

  // Подсветка кнопок
  const buttons = document.querySelectorAll("#lesson-options-grid .option-btn");
  buttons.forEach((btn, idx) => {
    btn.disabled = true;
    if (idx === item.ex.correct) {
      btn.classList.add("correct-highlight");
    } else if (idx === choice && !isCorrect) {
      btn.classList.add("wrong-highlight");
    }
  });

  document.getElementById("lesson-hand-input").disabled = true;

  // Показ фидбека
  const fb = document.getElementById("lesson-feedback");
  fb.className = `feedback-drawer ${isCorrect ? "correct" : "wrong"}`;
  document.getElementById("lesson-fb-icon").textContent = isCorrect ? "🎉" : "💡";
  document.getElementById("lesson-fb-title").textContent = isCorrect ? "Правильно!" : "Правильный ответ:";
  document.getElementById("lesson-fb-desc").textContent = explanation || (item.word ? `${item.word.en} — ${item.word.ru}` : "");
  fb.style.display = "flex";

  // Прокручиваем к панели с кнопкой «Дальше», чтобы не искать её вручную
  requestAnimationFrame(() => {
    fb.scrollIntoView({ behavior: "smooth", block: "center" });
    const nextBtn = document.getElementById("lesson-next-btn");
    if (nextBtn) nextBtn.focus({ preventScroll: true });
  });
}

function submitLessonHandwritten() {
  const input = document.getElementById("lesson-hand-input");
  const val = input.value.trim();
  if (!val) return;
  submitLessonAnswer(val);
}

function speakCurrentSentence() {
  const s = state.lessonSession;
  if (!s || !s.curItem) return;
  const item = s.curItem;
  if (item.word && item.word.sent) {
    speakText(item.word.sent.replace("___", item.word.en));
  } else if (item.ex && item.ex.sentence) {
    speakText(item.ex.sentence.replace("___", item.ex.target_full || ""));
  }
}

function nextLessonQuestion() {
  renderLessonQuestion();
}

async function finishLesson() {
  const s = state.lessonSession;
  document.getElementById("lesson-progress-fill").style.width = "100%";

  try {
    const res = await fetch("/api/lesson/finish", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        xp: s.xpGained,
        words: s.words,
        ok_count: s.okCount,
      }),
    });
    if (res.ok) {
      const data = await res.json();
      state.user = data.user;
      updateHeaderStats();
    }
  } catch (e) {
    console.warn("Finish lesson error:", e);
  }

  document.getElementById("lesson-runner").style.display = "none";
  const summary = document.getElementById("lesson-summary");
  summary.style.display = "block";

  document.getElementById("sum-xp").textContent = `+${s.xpGained}`;
  const accuracy = Math.round((s.okCount / s.totalCount) * 100) || 100;
  document.getElementById("sum-accuracy").textContent = `${accuracy}%`;
  document.getElementById("sum-streak").textContent = `${state.user.streak} дн.`;

  playFinishSound();
  launchConfetti();
}

function exitLesson() {
  if (confirm("Выйти из урока? Прогресс урока не сохранится.")) {
    document.getElementById("lesson-runner").style.display = "none";
    document.getElementById("lesson-welcome").style.display = "block";
  }
}

// ---------------------------------------------------------------- СЛОВАРЬ И ПРАВИЛА
async function loadDictionaryData() {
  if (state.dictWords.length === 0) {
    try {
      const [wordsRes, gramRes] = await Promise.all([
        fetch("/api/dictionary"),
        fetch("/api/grammar"),
      ]);
      state.dictWords = await wordsRes.json();
      state.dictGrammar = await gramRes.json();
    } catch (e) {
      console.warn("Dict load error:", e);
    }
  }
  renderDictionary();
}

function switchDictTab(type) {
  state.currentDictTab = type;
  document.getElementById("tab-btn-words").classList.toggle("active", type === "words");
  document.getElementById("tab-btn-grammar").classList.toggle("active", type === "grammar");

  document.getElementById("dict-words-list").style.display = type === "words" ? "grid" : "none";
  document.getElementById("dict-grammar-list").style.display = type === "grammar" ? "flex" : "none";

  renderDictionary();
}

function filterDictLevel(lvl) {
  state.currentDictLevel = lvl;
  document.querySelectorAll("#dict-level-filters .chip").forEach((chip, i) => {
    chip.classList.toggle("active", (lvl === "all" && i === 0) || (lvl !== "all" && i === (Number(lvl) + 1)));
  });
  renderDictionary();
}

function onDictSearch(query) {
  renderDictionary(query.trim().toLowerCase());
}

function renderDictionary(searchQuery = "") {
  if (state.currentDictTab === "words") {
    renderWords(searchQuery);
  } else {
    renderGrammar(searchQuery);
  }
}

function renderWords(query = "") {
  const container = document.getElementById("dict-words-list");
  container.innerHTML = "";

  const filtered = state.dictWords.filter((w) => {
    const levelMatch = state.currentDictLevel === "all" || w.pool == state.currentDictLevel;
    if (!levelMatch) return false;
    if (!query) return true;
    return (
      w.en.toLowerCase().includes(query) ||
      w.ru.toLowerCase().includes(query) ||
      (w.sent && w.sent.toLowerCase().includes(query))
    );
  });

  if (filtered.length === 0) {
    container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-muted); padding: 40px;">Слова не найдены</div>`;
    return;
  }

  filtered.forEach((w) => {
    const card = document.createElement("div");
    card.className = "word-card";
    const sentDisplay = (w.sent || "").replace("___", `<b>${w.en}</b>`);
    card.innerHTML = `
      <div class="word-card-top">
        <span class="word-en">${w.en}</span>
        <button class="speak-btn" style="width: 32px; height: 32px; font-size: 14px;" onclick="speakText('${w.en}')">🔊</button>
      </div>
      <div class="word-ru">${w.ru}</div>
      <div class="word-sent">${sentDisplay}</div>
    `;
    container.appendChild(card);
  });
}

function renderGrammar(query = "") {
  const container = document.getElementById("dict-grammar-list");
  container.innerHTML = "";

  const filtered = state.dictGrammar.filter((g) => {
    const levelMatch = state.currentDictLevel === "all" || g.level.toLowerCase().includes(String(state.currentDictLevel).toLowerCase());
    if (!levelMatch) return false;
    if (!query) return true;
    return (
      g.title.toLowerCase().includes(query) ||
      g.description.toLowerCase().includes(query) ||
      g.level.toLowerCase().includes(query)
    );
  });

  if (filtered.length === 0) {
    container.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 40px;">Правила не найдены</div>`;
    return;
  }

  filtered.forEach((g) => {
    const card = document.createElement("div");
    card.className = "rule-card";
    
    let tableHtml = "";
    if (g.rules && g.rules.length) {
      tableHtml = `
        <div class="rule-table">
          ${g.rules.map(r => `
            <div class="rule-row">
              <span class="rule-row-label">${r.label}:</span>
              <span class="rule-row-val">${r.rule}</span>
            </div>
          `).join("")}
        </div>
      `;
    }

    card.innerHTML = `
      <div class="rule-card-header">
        <span class="badge badge-purple">${g.level}</span>
        <span class="badge badge-gray">${g.badge || 'Грамматика'}</span>
        <h3 class="rule-card-title">${g.title}</h3>
      </div>
      <p class="rule-desc">${g.description}</p>
      ${tableHtml}
      <div class="rule-example-box">
        💡 <b>Пример:</b> ${g.example}
      </div>
    `;
    container.appendChild(card);
  });
}

// ---------------------------------------------------------------- ПРОФИЛЬ
function renderProfile() {
  document.getElementById("profile-user-name").textContent = state.user.name || "Друг";
  document.getElementById("profile-level-badge").textContent = LEVEL_NAMES[state.user.level];
  document.getElementById("profile-streak-val").textContent = state.user.streak;
  document.getElementById("profile-xp-val").textContent = state.user.xp;
  document.getElementById("profile-words-val").textContent = `${state.user.learned_count} / ${state.user.total_words}`;
  
  for (let i = 0; i <= 4; i++) {
    const b = document.getElementById(`btn-lvl-${i}`);
    if (b) b.classList.toggle("active", state.user.level === i);
  }
}

async function setUserLevel(lvl) {
  try {
    const res = await fetch("/api/user/set-level", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ level: lvl }),
    });
    if (res.ok) {
      const data = await res.json();
      state.user = data.user;
      updateHeaderStats();
      renderProfile();
      playTone(523, 0.1, "sine");
    }
  } catch (e) {
    alert("Ошибка изменения уровня: " + e);
  }
}

// Модальное окно выбора уровня
function showLevelSelectorModal() {
  document.getElementById("level-modal").style.display = "flex";
}

function closeLevelModal() {
  document.getElementById("level-modal").style.display = "none";
}

function closeModalOnBg(e) {
  if (e.target.id === "level-modal") closeLevelModal();
}

async function chooseModalLevel(lvl) {
  await setUserLevel(lvl);
  closeLevelModal();
}

async function resetProgress() {
  if (confirm("Сбросить весь прогресс (XP, серия, изученные слова) и начать с нуля?")) {
    try {
      const res = await fetch("/api/user/reset", { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        state.user = data.user;
        updateHeaderStats();
        renderProfile();
        alert("Прогресс сброшен.");
      }
    } catch (e) {
      alert("Ошибка сброса: " + e);
    }
  }
}

// ---------------------------------------------------------------- КОНФЕТТИ АНИМАЦИЯ
function launchConfetti() {
  const canvas = document.getElementById("confetti-canvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  const pieces = [];
  const colors = ["#10B981", "#3B82F6", "#F59E0B", "#EC4899", "#8B5CF6", "#14B8A6"];

  for (let i = 0; i < 90; i++) {
    pieces.push({
      x: canvas.width / 2,
      y: canvas.height / 2,
      vx: (Math.random() - 0.5) * 16,
      vy: (Math.random() - 0.7) * 16,
      size: Math.random() * 8 + 4,
      color: colors[Math.floor(Math.random() * colors.length)],
      rotation: Math.random() * 360,
      rSpeed: (Math.random() - 0.5) * 10,
      opacity: 1,
    });
  }

  let frames = 0;
  function update() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    let alive = 0;

    pieces.forEach((p) => {
      p.x += p.vx;
      p.y += p.vy;
      p.vy += 0.35; // gravity
      p.rotation += p.rSpeed;
      p.opacity -= 0.012;

      if (p.opacity > 0) {
        alive++;
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate((p.rotation * Math.PI) / 180);
        ctx.fillStyle = p.color;
        ctx.globalAlpha = Math.max(p.opacity, 0);
        ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size);
        ctx.restore();
      }
    });

    frames++;
    if (alive > 0 && frames < 140) {
      requestAnimationFrame(update);
    } else {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
  }

  requestAnimationFrame(update);
}

// ---------------------------------------------------------------- Инициализация и Telegram WebApp
function initTelegramWebApp() {
  // ready()/expand() уже вызваны при загрузке скрипта
  if (!tgWebApp) return;
  try {
    if (tgWebApp.enableClosingConfirmation) tgWebApp.enableClosingConfirmation();
  } catch (e) {
    console.log("TG WebApp init error:", e);
  }

  // Пока сервер отвечает, показываем имя из Telegram:
  // прогресс всё равно берётся с сервера по подписанному initData.
  if (tgUser) {
    state.user.name =
      [tgUser.first_name, tgUser.last_name].filter(Boolean).join(" ") ||
      tgUser.username ||
      "Друг";
  }
}

window.addEventListener("DOMContentLoaded", () => {
  initTelegramWebApp();
  fetchUser();
});
