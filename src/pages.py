"""HTML-страницы сервиса: лендинг и рабочий экран.

Вёрстка без фреймворков: проект должен запускаться одной командой из README,
поэтому сборка фронтенда сюда не вводится. Композиция повторяет макет,
выбранный заказчиком: компактная навигация, центрированный герой, рамка
с превью продукта и сворачивающийся сайдбар на рабочем экране.
"""

BASE_CSS = """
:root{
  --bg:#f7f8f8; --card:#fff; --ink:#0b1416; --mut:#6b7d7f; --mut2:#93a3a4;
  --line:#e3e8e8; --line2:#d3dbdb; --acc:#0b6f80; --acc-ink:#fff;
  --ok:#2e6b45; --ok-bg:#e7f1ea; --warn:#8a6510; --warn-bg:#f6eed9;
  --bad:#9b3520; --bad-bg:#f8e6e0;
  --sans:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,Consolas,monospace;
  --r:12px;
}
@media(prefers-color-scheme:dark){:root{
  --bg:#08100f; --card:#0f1a1b; --ink:#e8f0ef; --mut:#93a5a6; --mut2:#6e8385;
  --line:#1d2c2e; --line2:#27393b; --acc:#45c0cf; --acc-ink:#04181b;
  --ok:#6fc08f; --ok-bg:#132a1f; --warn:#d7ae4e; --warn-bg:#2a2415;
  --bad:#e2785c; --bad-bg:#2e1c17;
}}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:15px;
  line-height:1.55;-webkit-font-smoothing:antialiased}
a{color:inherit;text-decoration:none}
.btn{display:inline-flex;align-items:center;gap:8px;font:inherit;font-weight:500;cursor:pointer;
  border-radius:10px;padding:10px 18px;border:1px solid transparent;background:var(--ink);color:var(--bg);
  transition:opacity .15s ease,transform .15s ease}
.btn:hover{opacity:.9;transform:translateY(-1px)}
.btn.outline{background:transparent;color:var(--ink);border-color:var(--line2)}
.btn.sm{padding:6px 14px;font-size:13.5px;border-radius:9px}
.btn:disabled{opacity:.5;cursor:default;transform:none}
.kbd{display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;font-size:11px;
  border:1px solid var(--line2);border-radius:5px;font-family:var(--mono);color:var(--mut)}
:focus-visible{outline:2px solid var(--acc);outline-offset:2px}
@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
"""

LANDING = """
<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Сверка — анализ организационной структуры и функционала</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap">
<style>
__BASE__
.container{max-width:1060px;margin:0 auto;padding-inline:20px}
header{padding-top:18px}
nav.bar{display:flex;align-items:center;justify-content:space-between;background:var(--card);
  border:1px solid var(--line);border-radius:14px;padding:9px 14px;box-shadow:0 8px 26px rgba(8,20,22,.07)}
.brand{display:flex;align-items:center;gap:9px;font-weight:600;font-size:15px}
.brand i{width:20px;height:20px;border:2px solid var(--acc);border-radius:5px;position:relative;display:block}
.brand i::after{content:"";position:absolute;left:3px;right:3px;top:4px;height:1.5px;background:var(--acc);
  box-shadow:0 4px 0 var(--acc),0 8px 0 var(--acc)}
.navlinks{display:flex;gap:22px;margin-left:26px}
.navlinks a{font-size:13.5px;color:var(--mut2);transition:color .15s}
.navlinks a:hover{color:var(--ink)}
@media(max-width:760px){.navlinks{display:none}}

main{padding-block:78px 0;text-align:center}
.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--acc);margin:0 0 20px}
h1{font-size:clamp(36px,6.2vw,66px);line-height:1.02;letter-spacing:-.035em;font-weight:700;margin:0;
  text-wrap:balance}
h1 span{color:var(--mut2)}
.lead{margin:22px auto 30px;max-width:44ch;font-size:clamp(16px,2vw,20px);color:var(--mut)}
.lead b{color:var(--ink);font-weight:600}
.actions{display:flex;gap:12px;justify-content:center;flex-wrap:wrap}
.meta{margin:26px 0 8px;display:flex;gap:16px;justify-content:center;flex-wrap:wrap;font-size:13.5px}
.meta .on{color:var(--acc)}
.meta .off{color:var(--mut2)}
.metanote{font-size:13px;color:var(--mut2);margin:0 0 44px}

/* рамка с превью продукта */
.frame{border:1px solid var(--line);border-radius:22px;padding:8px;background:var(--card);
  box-shadow:0 30px 70px rgba(8,20,22,.1);position:relative}
.shot{border:1px solid var(--line);border-radius:16px;overflow:hidden;position:relative;background:var(--bg)}
.shot img{display:block;width:100%;height:auto}
.fade{position:absolute;inset:auto 0 0 0;height:46%;pointer-events:none;
  background:linear-gradient(to top,var(--bg),transparent)}

/* встроенное превью интерфейса, если скриншот не подложен */
.mock{text-align:left;display:grid;grid-template-columns:52px 1fr;min-height:330px;font-size:12px}
.mock .rail{border-right:1px solid var(--line);padding:10px 0;display:flex;flex-direction:column;
  align-items:center;gap:14px;background:var(--card)}
.mock .rail b{width:18px;height:18px;border-radius:5px;background:var(--line2);display:block}
.mock .rail b.on{background:var(--acc)}
.mock .body{padding:14px 16px;background:var(--card)}
.mock .h{font-size:14px;font-weight:600;margin-bottom:10px}
.mock .stats{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);
  border:1px solid var(--line);border-radius:8px;overflow:hidden;margin-bottom:12px}
.mock .stats div{background:var(--card);padding:8px 10px}
.mock .stats b{display:block;font-size:17px;font-weight:600}
.mock .stats span{font-size:10px;color:var(--mut2);text-transform:uppercase;letter-spacing:.04em}
.mock .card{border:1px solid var(--line);border-left:3px solid var(--line2);border-radius:8px;
  padding:9px 11px;margin-bottom:7px;background:var(--card)}
.mock .card.ok{border-left-color:var(--ok)}
.mock .card.warn{border-left-color:var(--warn)}
.mock .card strong{display:block;font-size:12.5px;margin-bottom:3px}
.mock .card em{font-style:normal;font-family:var(--mono);font-size:10.5px;color:var(--acc)}
.mock .card p{margin:3px 0 0;color:var(--mut);font-size:11.5px}

section{padding-block:76px;text-align:left}
section.bordered{border-top:1px solid var(--line)}
h2{font-size:clamp(25px,3.4vw,34px);line-height:1.15;letter-spacing:-.025em;margin:0 0 12px;text-wrap:balance}
.sec-lead{color:var(--mut);max-width:62ch;margin:0 0 34px}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.c{background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:22px}
.c .n{font-family:var(--mono);font-size:11px;letter-spacing:.1em;color:var(--acc);margin-bottom:10px}
.c h3{margin:0 0 7px;font-size:16.5px}
.c p{margin:0;color:var(--mut);font-size:14px}
.steps{display:grid;gap:12px}
.step{display:grid;grid-template-columns:38px 1fr auto;gap:18px;align-items:start;background:var(--card);
  border:1px solid var(--line);border-radius:var(--r);padding:19px 21px}
.step.key{border-color:var(--acc)}
.step .num{font-family:var(--mono);font-size:17px;color:var(--acc);font-weight:500}
.step h3{margin:0 0 4px;font-size:16px}
.step p{margin:0;color:var(--mut);font-size:14px;max-width:62ch}
.who{font-family:var(--mono);font-size:10.5px;letter-spacing:.06em;text-transform:uppercase;
  padding:4px 9px;border-radius:6px;white-space:nowrap}
.who.code{background:var(--ok-bg);color:var(--ok)}
.who.ai{background:var(--warn-bg);color:var(--warn)}
.final{text-align:center;padding-block:78px;border-top:1px solid var(--line)}
.final p{color:var(--mut);max-width:52ch;margin:0 auto 26px}
footer{border-top:1px solid var(--line);padding-block:24px;color:var(--mut2);font-size:13px}
footer .container{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
@media(max-width:860px){.cards{grid-template-columns:1fr}.step{grid-template-columns:30px 1fr}
  .step .who{grid-column:2}.mock .stats{grid-template-columns:repeat(2,1fr)}}
</style></head><body>

<div class="container">
  <header>
    <nav class="bar">
      <div style="display:flex;align-items:center">
        <div class="brand"><i></i> Сверка</div>
        <div class="navlinks">
          <a href="#problem">Задача</a>
          <a href="#how">Как работает</a>
          <a href="#trust">Доверие к выводам</a>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:10px">
        <a class="btn outline sm" href="#how">Подробнее</a>
        <a class="btn sm" href="/app">Начать анализ</a>
      </div>
    </nav>
  </header>

  <main>
    <p class="eyebrow">HackAlem AI · спец-трек Казахтелеком</p>
    <h1>Реорганизация прошла.<br><span>Какие функции потерялись?</span></h1>
    <p class="lead">Сравниваем комплекты документов <b>«до»</b> и <b>«после»</b> и показываем потери, дублирование и конфликт интересов — <b>со ссылкой на пункт</b>.</p>
    <div class="actions">
      <a class="btn" href="/app">Начать анализ
        <span style="display:inline-flex;gap:4px"><span class="kbd" style="border-color:currentColor;opacity:.5">↵</span></span>
      </a>
      <a class="btn outline" href="#how">Как это работает</a>
    </div>
    <div class="meta">
      <span class="on">7 из 7 контрольных случаев</span>
      <span class="off">100% выводов со ссылкой на пункт</span>
      <span class="on">~45 секунд на разбор</span>
    </div>
    <p class="metanote">Контрольный комплект уже загружен — можно проверить без своих файлов</p>

    <div class="frame">
      <div class="shot">
        __PREVIEW__
        <div class="fade"></div>
      </div>
    </div>
  </main>
</div>

<div class="container">
  <section id="problem" class="bordered">
    <h2>Что происходит при реорганизации</h2>
    <p class="sec-lead">Положения и приложения сверяют вручную. В комплекте из двух редакций — более трёхсот пунктов и 84 тысячи знаков. Глазами это не сводится.</p>
    <div class="cards">
      <div class="c"><div class="n">РИСК 01</div><h3>Функция исчезла</h3>
        <p>Обязанность была у подразделения, а в новой редакции её нет ни у кого. Выясняется на ближайшей проверке.</p></div>
      <div class="c"><div class="n">РИСК 02</div><h3>Функция задвоилась</h3>
        <p>Одно и то же записано двум подразделениям. Каждое считает, что отвечает другое.</p></div>
      <div class="c"><div class="n">РИСК 03</div><h3>Конфликт интересов</h3>
        <p>Подразделение проводит проверки и само же оценивает их качество — то есть проверяет себя.</p></div>
    </div>
  </section>

  <section id="how" class="bordered">
    <h2>Как работает</h2>
    <p class="sec-lead">Всё, что однозначно записано в документе, извлекает код. Модель подключается там, где нужен смысл. Поэтому сослаться на несуществующий пункт невозможно.</p>
    <div class="steps">
      <div class="step"><span class="num">01</span>
        <div><h3>Разбор на пункты</h3><p>Документ раскладывается на пронумерованные пункты с сохранением раздела и точной цитаты. Ссылка берётся из структуры файла.</p></div>
        <span class="who code">код</span></div>
      <div class="step"><span class="num">02</span>
        <div><h3>Карта подразделений</h3><p>Из состава структуры извлекаются подразделения, а из обязанностей их руководителей — закреплённые функции.</p></div>
        <span class="who code">код</span></div>
      <div class="step"><span class="num">03</span>
        <div><h3>Сопоставление по смыслу</h3><p>«Вести переписку с руководителями» и «взаимодействовать с руководителями» — одна функция. Это понимает модель, а не поиск по словам.</p></div>
        <span class="who ai">модель</span></div>
      <div class="step key"><span class="num">04</span>
        <div><h3>Агент перепроверяет каждое подозрение</h3><p>Агент сам решает, что искать, вызывает инструменты поиска по документу и выносит вердикт: потеря подтверждена, функция найдена в другом пункте или честное «не уверен». Вердикт без ссылки на пункт система не принимает.</p></div>
        <span class="who ai">агент</span></div>
      <div class="step"><span class="num">05</span>
        <div><h3>Заключение с источниками</h3><p>Что изменилось, на что смотреть в первую очередь, какие риски — и пункт-подтверждение под каждым выводом.</p></div>
        <span class="who code">код + модель</span></div>
    </div>
  </section>

  <section id="trust" class="bordered">
    <h2>Почему выводам можно верить</h2>
    <p class="sec-lead">Модель, которой отдали документ целиком, уверенно называет номера пунктов, которых не существует. Для анализа реорганизации это недопустимо: вывод, который нельзя проверить, бесполезен.</p>
    <div class="cards">
      <div class="c"><div class="n">ГАРАНТИЯ</div><h3>Ссылку даёт код</h3>
        <p>Номера пунктов и принадлежность функций извлекаются из структуры документа, а не генерируются.</p></div>
      <div class="c"><div class="n">ПРОВЕРКА</div><h3>Агент ищет подтверждение</h3>
        <p>Цитаты он получает только через инструменты. Вердикт «функция найдена» без пункта отклоняется.</p></div>
      <div class="c"><div class="n">ЧЕСТНОСТЬ</div><h3>«Не уверен» — нормальный ответ</h3>
        <p>Где данных не хватает, система говорит об этом прямо и отдаёт решение человеку.</p></div>
    </div>
  </section>
</div>

<div class="final"><div class="container">
  <h2>Проверьте на своём комплекте</h2>
  <p>Загрузите два комплекта документов — или запустите анализ на контрольном, он уже в сервисе.</p>
  <a class="btn" href="/app">Начать анализ</a>
</div></div>

<footer><div class="container">
  <span>Сверка · анализ организационной структуры и функционала</span>
  <span>HackAlem AI 2026 · команда Solnik</span>
</div></footer>
</body></html>
""".replace("__BASE__", BASE_CSS)


MOCK_PREVIEW = """
<div class="mock">
  <div class="rail"><b class="on"></b><b></b><b></b><b></b><b></b></div>
  <div class="body">
    <div class="h">Анализ организационной структуры и функционала</div>
    <div class="stats">
      <div><b>4</b><span>подразделения</span></div>
      <div><b>2</b><span>создано</span></div>
      <div><b>24</b><span>дублирования</span></div>
      <div><b>5</b><span>снято агентом</span></div>
    </div>
    <div class="card ok"><strong>Создано подразделение ДИТААД</strong>
      <em>polozhenie_red9.docx, п. 3.4</em>
      <p>Департамент ИТ-аудита и анализа данных отсутствует в комплекте «до».</p></div>
    <div class="card warn"><strong>Функция ДНМ перенесена в общий раздел</strong>
      <em>polozhenie_red9.docx, п. 5.6.2</em>
      <p>Ответственность перестала быть закреплённой за подразделением.</p></div>
    <div class="card ok"><strong>Снято агентом: функция сохранена</strong>
      <em>подтверждение — п. 5.6.4</em>
      <p>Подозрение на потерю не подтвердилось, агент нашёл формулировку в новой редакции.</p></div>
  </div>
</div>
"""


LANDING = LANDING.replace("__PREVIEW__", MOCK_PREVIEW)
