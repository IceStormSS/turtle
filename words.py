"""Словарь для TurtleLingo.

Формат строки: английское слово | перевод | часть речи | предложение с пропуском ___
Части речи: n - существительное, v - глагол, a - прилагательное, o - прочее.

Чтобы добавить слова, просто допиши новые строки в нужный уровень
(в конце, перед закрывающими тройными кавычками).
"""

LEVEL_NAMES = {
    0: "A0 — Начальный 🥚",
    1: "A1 — Базовый 🐣",
    2: "A2 — Элементарный 🐢",
    3: "B1 — Средний 🌿",
    4: "B2 — Выше среднего 🏆",
}

RAW = {
    # ---------- Уровень 0: самая база ----------
    0: """
hello|привет|o|___, my name is Tom.
goodbye|до свидания|o|___, see you tomorrow!
yes|да|o|___, I like it.
no|нет|o|___, thank you.
please|пожалуйста|o|Water, ___!
thanks|спасибо|o|___ for the book!
I|я|o|___ am a student.
you|ты, вы|o|___ are my friend.
he|он|o|___ is my brother.
she|она|o|___ is my mother.
we|мы|o|___ are friends.
they|они|o|___ are students.
mother|мама|n|My ___ is at home.
father|папа|n|My ___ is a doctor.
friend|друг|n|He is my ___.
water|вода|n|I drink ___.
bread|хлеб|n|I eat ___.
apple|яблоко|n|The ___ is red.
cat|кот|n|The ___ sleeps on the sofa.
dog|собака|n|The ___ is big.
house|дом|n|This is my ___.
book|книга|n|I read a ___.
name|имя|n|My ___ is Tom.
boy|мальчик|n|The ___ is small.
girl|девочка|n|The ___ has a cat.
sun|солнце|n|The ___ is big.
red|красный|a|The apple is ___.
blue|синий|a|The sky is ___.
big|большой|a|The house is ___.
small|маленький|a|The cat is ___.
good|хороший|a|This is a ___ book.
black|чёрный|a|The cat is ___.
one|один|o|I have ___ cat.
two|два|o|I have ___ dogs.
three|три|o|We have ___ books.
eat|есть, кушать|v|I ___ bread.
drink|пить|v|I ___ water.
read|читать|v|I ___ a book.
go|идти, ехать|v|I ___ home.
like|любить, нравиться|v|I ___ cats.
have|иметь|v|I ___ a dog.
""",
    # ---------- Уровень 1: A1 ----------
    1: """
school|школа|n|I go to ___.
teacher|учитель|n|My ___ is kind.
city|город|n|I live in a big ___.
family|семья|n|I love my ___.
food|еда|n|I like Italian ___.
milk|молоко|n|I drink ___ in the morning.
coffee|кофе|n|He drinks ___ every day.
table|стол|n|The book is on the ___.
room|комната|n|My ___ is small.
car|машина|n|My father has a new ___.
street|улица|n|The ___ is very long.
brother|брат|n|My ___ is ten years old.
sister|сестра|n|My ___ likes music.
morning|утро|n|Good ___!
night|ночь|n|Good ___!
day|день|n|It is a nice ___.
phone|телефон|n|My ___ is on the table.
music|музыка|n|I listen to ___.
work|работать|v|I ___ in a bank.
live|жить|v|We ___ in Ukraine.
play|играть|v|The children ___ in the park.
write|писать|v|I ___ a letter.
speak|говорить|v|Do you ___ English?
want|хотеть|v|I ___ some tea.
see|видеть|v|I ___ a bird.
walk|гулять, ходить пешком|v|We ___ to school.
sleep|спать|v|I ___ at night.
happy|счастливый|a|I am ___ today.
old|старый|a|My grandfather is ___.
new|новый|a|I have a ___ phone.
beautiful|красивый|a|It is a ___ city.
cold|холодный|a|The water is ___.
hot|горячий, жаркий|a|The tea is ___.
today|сегодня|o|I am at home ___.
tomorrow|завтра|o|See you ___!
always|всегда|o|I ___ drink tea in the morning.
now|сейчас|o|I am at school ___.
with|с|o|I go to school ___ my friend.
very|очень|o|The cat is ___ small.
""",
    # ---------- Уровень 2: A2 ----------
    2: """
weather|погода|n|The ___ is nice today.
holiday|отпуск, праздник|n|We go on ___ in summer.
ticket|билет|n|I need a train ___.
mountain|гора|n|We climb the ___.
river|река|n|The ___ is very wide.
shop|магазин|n|I buy bread in the ___.
doctor|врач|n|I must see a ___.
price|цена|n|The ___ is too high.
journey|поездка|n|It was a long ___.
neighbor|сосед|n|My ___ has a loud dog.
airport|аэропорт|n|The ___ is far from the city.
message|сообщение|n|I got a ___ from my friend.
breakfast|завтрак|n|I have ___ at eight.
buy|покупать|v|I want to ___ a jacket.
travel|путешествовать|v|I like to ___ by train.
decide|решать|v|I can't ___ what to eat.
forget|забывать|v|Don't ___ your keys!
remember|помнить|v|I ___ this song.
learn|учить, изучать|v|I ___ new words every day.
wait|ждать|v|Please ___ for me.
help|помогать|v|Can you ___ me?
invite|приглашать|v|I will ___ my friends to the party.
carry|нести|v|Can you ___ this bag?
expensive|дорогой|a|This watch is too ___.
cheap|дешёвый|a|The bus ticket is ___.
tired|уставший|a|I am ___ after work.
busy|занятой|a|He is ___ today.
dangerous|опасный|a|This road is ___.
easy|лёгкий|a|The test is ___.
difficult|трудный|a|English grammar is ___.
famous|известный|a|He is a ___ singer.
usually|обычно|o|I ___ get up at seven.
sometimes|иногда|o|___ we eat in a café.
never|никогда|o|I ___ drink coffee at night.
already|уже|o|I have ___ done my homework.
because|потому что|o|I stay home ___ it rains.
but|но|o|I like tea, ___ I don't like coffee.
quickly|быстро|o|He runs very ___.
together|вместе|o|Let's go ___!
""",
    # ---------- Уровень 3: B1 ----------
    3: """
experience|опыт|n|She has a lot of work ___.
opinion|мнение|n|In my ___, this film is great.
environment|окружающая среда|n|We must protect the ___.
advice|совет|n|Thanks for your ___.
career|карьера|n|He wants to build a ___ in IT.
government|правительство|n|The ___ plans new laws.
habit|привычка|n|Reading is a good ___.
health|здоровье|n|Sport is good for your ___.
choice|выбор|n|It was a difficult ___.
mistake|ошибка|n|Everyone makes a ___.
success|успех|n|Hard work leads to ___.
knowledge|знания|n|___ is power.
relationship|отношения|n|They have a good ___.
improve|улучшать|v|I want to ___ my English.
suggest|предлагать|v|I ___ we go to the cinema.
explain|объяснять|v|Can you ___ this rule?
avoid|избегать|v|Try to ___ stress.
achieve|достигать|v|She wants to ___ her goals.
manage|справляться, управлять|v|I can ___ this project alone.
refuse|отказываться|v|He will ___ the offer.
prefer|предпочитать|v|I ___ tea to coffee.
depend|зависеть|v|It will ___ on the weather.
notice|замечать|v|Did you ___ the sign?
compare|сравнивать|v|Let's ___ these two phones.
increase|увеличиваться, повышаться|v|Prices ___ every year.
comfortable|удобный|a|This sofa is very ___.
independent|независимый|a|She is a very ___ person.
serious|серьёзный|a|It is a ___ problem.
polite|вежливый|a|Be ___ to older people.
confident|уверенный|a|I feel ___ before the exam.
necessary|необходимый|a|Water is ___ for life.
modern|современный|a|It is a ___ building.
curious|любопытный|a|Children are ___.
available|доступный, свободный|a|Is this table ___?
although|хотя|o|___ it was late, we kept working.
however|однако|o|He is young; ___, he is very wise.
actually|на самом деле|o|I ___ like this idea.
probably|вероятно|o|It will ___ rain tomorrow.
especially|особенно|o|I like fruit, ___ apples.
recently|недавно|o|I ___ moved to a new flat.
""",
    # ---------- Уровень 4: B2 ----------
    4: """
achievement|достижение|n|Winning was a great ___.
awareness|осведомлённость|n|We need more ___ of this issue.
challenge|вызов, сложная задача|n|Learning a language is a real ___.
consequence|последствие|n|Every action has a ___.
development|развитие|n|The ___ of technology is fast.
evidence|доказательство|n|There is no ___ for this theory.
impact|влияние|n|Social media has a big ___ on teenagers.
opportunity|возможность|n|This job is a great ___.
pressure|давление|n|He works well under ___.
resource|ресурс|n|Water is a valuable ___.
research|исследование|n|Scientists did new ___ on sleep.
behavior|поведение|n|His ___ surprised everyone.
threat|угроза|n|Climate change is a global ___.
acquire|приобретать|v|Children ___ language skills quickly.
assume|предполагать|v|I ___ you are right.
contribute|вносить вклад|v|Everyone can ___ to the project.
convince|убеждать|v|I couldn't ___ him to stay.
demonstrate|демонстрировать|v|Let me ___ how it works.
emphasize|подчёркивать|v|The teacher wants to ___ this point.
establish|основывать|v|They want to ___ a new company.
overcome|преодолевать|v|She had to ___ many difficulties.
reduce|сокращать|v|We should ___ plastic waste.
struggle|бороться|v|Many people ___ with stress.
maintain|поддерживать|v|It is hard to ___ a healthy diet.
reliable|надёжный|a|He is a ___ colleague.
efficient|эффективный|a|This method is very ___.
ambitious|амбициозный|a|She is young and ___.
sufficient|достаточный|a|One hour is not ___.
significant|значительный|a|There was a ___ change.
vulnerable|уязвимый|a|Old systems are ___ to attacks.
flexible|гибкий|a|My schedule is ___.
reluctant|неохотный|a|He was ___ to help.
complex|сложный|a|The problem is very ___.
nevertheless|тем не менее|o|It was hard; ___, we finished.
furthermore|кроме того|o|It is cheap; ___, it is fast.
generally|в целом|o|___, I agree with you.
eventually|в конце концов|o|___ we found the answer.
hardly|едва|o|I can ___ hear you.
whereas|тогда как|o|She likes tea, ___ he likes coffee.
rather|довольно|o|It is ___ cold today.
""",
}


def _parse(pool, text):
    words = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        en, ru, pos, sent = line.split("|")
        words.append(
            {"en": en, "ru": ru, "pos": pos, "sent": sent, "pool": pool, "key": f"{pool}:{en}"}
        )
    return words


POOLS = {level: _parse(level, text) for level, text in RAW.items()}
