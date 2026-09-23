"""HTML-страницы сервиса: лендинг и рабочий экран.

Вынесено из app.py, чтобы маршруты остались читаемыми.
"""

LANDING = """
<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Сверка · анализ организационной структуры и функционала</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap">
<style>
:root{
  --bg:#0a1214; --bg2:#0f1b1e; --card:#132226; --ink:#e8f0ef; --mut:#8fa5a6;
  --line:#22373b; --acc:#3fc9d6; --acc2:#0b6f80; --warn:#e0a340; --bad:#e2785c; --ok:#5fc08d;
  --sans:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,Consolas,monospace;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:16px;line-height:1.6;
  -webkit-font-smoothing:antialiased}
.wrap{max-width:1120px;margin:0 auto;padding-inline:24px}
a{color:inherit;text-decoration:none}

nav{position:sticky;top:0;z-index:20;background:rgba(10,18,20,.86);backdrop-filter:blur(10px);
  border-bottom:1px solid var(--line)}
nav .wrap{display:flex;align-items:center;justify-content:space-between;padding-block:14px}
.logo{display:flex;align-items:center;gap:10px;font-weight:600;letter-spacing:-.01em}
.logo i{width:24px;height:24px;border:2px solid var(--acc);border-radius:3px;display:block;position:relative}
.logo i::after{content:"";position:absolute;inset:4px 4px auto 4px;height:2px;background:var(--acc);
  box-shadow:0 5px 0 var(--acc2),0 10px 0 var(--acc2)}
.btn{display:inline-block;font-weight:600;padding:11px 22px;border-radius:2px;border:1px solid var(--acc);
  background:var(--acc);color:#04191c;transition:transform .12s ease,box-shadow .12s ease}
.btn:hover{transform:translateY(-1px);box-shadow:0 6px 22px rgba(63,201,214,.24)}
.btn.ghost{background:transparent;color:var(--acc)}
.btn.sm{padding:8px 16px;font-size:14px}

.hero{padding-block:76px 60px;border-bottom:1px solid var(--line);
  background:radial-gradient(1000px 420px at 78% -10%,rgba(63,201,214,.11),transparent 62%)}
.hero .grid{display:grid;grid-template-columns:1.08fr .92fr;gap:54px;align-items:center}
.eyebrow{font-family:var(--mono);font-size:12px;letter-spacing:.16em;text-transform:uppercase;color:var(--acc);margin:0 0 18px}
h1{font-size:clamp(38px,5.2vw,60px);line-height:1.04;letter-spacing:-.025em;margin:0;font-weight:700;text-wrap:balance}
h1 em{font-style:normal;color:var(--acc)}
.lead{color:var(--mut);font-size:clamp(16px,1.7vw,19px);max-width:52ch;margin:22px 0 32px}
.cta{display:flex;gap:12px;flex-wrap:wrap;align-items:center}
.cta small{color:var(--mut);font-size:13px}

/* визуальная метафора: два документа и найденное отклонение */
.demo{background:var(--card);border:1px solid var(--line);border-radius:4px;overflow:hidden;
  box-shadow:0 26px 60px rgba(0,0,0,.42)}
.demo-top{display:flex;align-items:center;gap:8px;padding:11px 14px;border-bottom:1px solid var(--line);background:var(--bg2)}
.dot{width:9px;height:9px;border-radius:50%;background:var(--line)}
.demo-top span{font-family:var(--mono);font-size:11.5px;color:var(--mut);margin-left:6px}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--line)}
.col{background:var(--card);padding:14px}
.col h4{margin:0 0 10px;font-family:var(--mono);font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--mut)}
.cl{font-family:var(--mono);font-size:11.5px;line-height:1.7;color:var(--mut);padding:3px 6px;border-left:2px solid transparent}
.cl b{color:var(--ink);font-weight:500}
.cl.add{border-left-color:var(--ok);background:rgba(95,192,141,.09)}
.cl.gone{border-left-color:var(--bad);background:rgba(226,120,92,.09)}
.verdict{padding:13px 14px;border-top:1px solid var(--line);background:var(--bg2);font-size:13px}
.verdict .row{display:flex;gap:9px;align-items:flex-start;margin-bottom:7px}
.verdict .row:last-child{margin:0}
.tag{font-family:var(--mono);font-size:10px;letter-spacing:.06em;text-transform:uppercase;padding:2px 7px;white-space:nowrap}
.tag.ok{background:rgba(95,192,141,.16);color:var(--ok)}
.tag.warn{background:rgba(224,163,64,.16);color:var(--warn)}
.cite{font-family:var(--mono);font-size:11.5px;color:var(--acc)}

.strip{border-bottom:1px solid var(--line);background:var(--bg2)}
.strip .wrap{display:grid;grid-template-columns:repeat(4,1fr);gap:28px;padding-block:26px}
.st b{display:block;font-size:30px;font-weight:700;letter-spacing:-.02em;line-height:1.1;font-variant-numeric:tabular-nums}
.st span{font-size:12.5px;color:var(--mut)}

section{padding-block:68px;border-bottom:1px solid var(--line)}
h2{font-size:clamp(26px,3.4vw,34px);line-height:1.14;letter-spacing:-.02em;margin:0 0 12px;text-wrap:balance}
.sec-lead{color:var(--mut);max-width:62ch;margin:0 0 36px}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.card{background:var(--card);border:1px solid var(--line);padding:22px;border-radius:3px}
.card .n{font-family:var(--mono);font-size:11px;letter-spacing:.1em;color:var(--acc);margin-bottom:11px}
.card h3{margin:0 0 8px;font-size:17px}
.card p{margin:0;color:var(--mut);font-size:14.5px}

.steps{display:grid;gap:14px}
.step{display:grid;grid-template-columns:42px 1fr auto;gap:20px;align-items:start;background:var(--card);
  border:1px solid var(--line);padding:20px 22px;border-radius:3px}
.step .num{font-family:var(--mono);font-size:19px;color:var(--acc);font-weight:600}
.step h3{margin:0 0 5px;font-size:17px}
.step p{margin:0;color:var(--mut);font-size:14.5px;max-width:64ch}
.who{font-family:var(--mono);font-size:10.5px;letter-spacing:.07em;text-transform:uppercase;padding:5px 10px;white-space:nowrap}
.who.code{background:rgba(63,201,214,.13);color:var(--acc)}
.who.ai{background:rgba(224,163,64,.14);color:var(--warn)}
.step.key{border-color:var(--acc);box-shadow:0 0 0 1px rgba(63,201,214,.18)}

.guarantee{display:grid;grid-template-columns:1fr 1fr;gap:40px;align-items:center}
.quote{border-left:3px solid var(--acc);padding:4px 0 4px 20px;color:var(--mut);font-size:15.5px}
.quote b{color:var(--ink);font-weight:500}
.final{padding-block:74px;text-align:center}
.final h2{margin-bottom:14px}
.final p{color:var(--mut);max-width:56ch;margin:0 auto 28px}
footer{border-top:1px solid var(--line);padding-block:26px;color:var(--mut);font-size:13px}
footer .wrap{display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap}

@media(max-width:940px){
  .hero .grid,.guarantee{grid-template-columns:1fr;gap:34px}
  .cards{grid-template-columns:1fr}
  .strip .wrap{grid-template-columns:repeat(2,1fr);gap:20px}
  .step{grid-template-columns:32px 1fr;gap:14px}
  .step .who{grid-column:2}
}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
</style></head><body>

<nav><div class="wrap">
  <div class="logo"><i></i> Сверка</div>
  <a class="btn sm" href="/app">Открыть сервис</a>
</div></nav>

<header class="hero"><div class="wrap grid">
  <div>
    <p class="eyebrow">HackAlem AI · спец-трек Казахтелеком</p>
    <h1>Реорганизация прошла.<br><em>Какие функции потерялись?</em></h1>
    <p class="lead">Загрузите комплекты документов «до» и «после». Агент находит потерянные и задвоенные функции, пересечение зон ответственности и конфликт интересов — и на каждый вывод показывает пункт документа, откуда он взят.</p>
    <div class="cta">
      <a class="btn" href="/app">Начать анализ</a>
      <a class="btn ghost" href="#how">Как это работает</a>
      <small>Готовый комплект для проверки уже внутри</small>
    </div>
  </div>

  <div class="demo">
    <div class="demo-top"><i class="dot"></i><i class="dot"></i><i class="dot"></i>
      <span>положение · редакция 8 → редакция 9</span></div>
    <div class="cols">
      <div class="col"><h4>до</h4>
        <div class="cl">п. 3.4 БВА состоит из:</div>
        <div class="cl"><b>ДНМ</b> — непрерывный мониторинг</div>
        <div class="cl"><b>ДККМ</b> — контроль качества</div>
        <div class="cl gone">п. 5.3 Директор направления<br>внутреннего аудита</div>
        <div class="cl">п. 5.7.4 присутствовать<br>на заседаниях органов</div>
      </div>
      <div class="col"><h4>после</h4>
        <div class="cl">п. 3.4 БВА состоит из:</div>
        <div class="cl add"><b>ДИТААД</b> — ИТ-аудит и анализ данных</div>
        <div class="cl add"><b>ДОА</b> — операционный аудит</div>
        <div class="cl"><b>ДНМ</b>, <b>ДККМ</b> — сохранены</div>
        <div class="cl">п. 5.3 Директоры департаментов<br>и направлений ДИТААД и ДОА</div>
      </div>
    </div>
    <div class="verdict">
      <div class="row"><span class="tag ok">создано</span>
        <div>Два департамента <span class="cite">п. 3.4</span></div></div>
      <div class="row"><span class="tag warn">стало общим</span>
        <div>13 функций перестали быть закреплены за подразделением</div></div>
      <div class="row"><span class="tag ok">снято агентом</span>
        <div>Подозрение на потерю не подтвердилось: функция найдена <span class="cite">п. 5.6.2</span></div></div>
    </div>
  </div>
</div></header>

<div class="strip"><div class="wrap">
  <div class="st"><b>7 / 7</b><span>контрольных случаев найдено</span></div>
  <div class="st"><b>100%</b><span>выводов со ссылкой на пункт</span></div>
  <div class="st"><b>~45 с</b><span>на два документа по 300+ пунктов</span></div>
  <div class="st"><b>0</b><span>выдуманных источников</span></div>
</div></div>

<section><div class="wrap">
  <h2>Что происходит при реорганизации</h2>
  <p class="sec-lead">Положения и приложения сопоставляют вручную. В комплекте из двух редакций — больше трёхсот пунктов и 84 тысячи знаков. Глазами это не сводится.</p>
  <div class="cards">
    <div class="card"><div class="n">РИСК 01</div><h3>Функция исчезла</h3>
      <p>Обязанность была у отдела, а в новой редакции её нет ни у кого. Выясняется на ближайшей проверке.</p></div>
    <div class="card"><div class="n">РИСК 02</div><h3>Функция задвоилась</h3>
      <p>Одно и то же записано двум подразделениям. Каждое считает, что отвечает другое.</p></div>
    <div class="card"><div class="n">РИСК 03</div><h3>Конфликт интересов</h3>
      <p>Подразделение одновременно проводит проверки и оценивает их качество — то есть проверяет само себя.</p></div>
  </div>
</div></section>

<section id="how"><div class="wrap">
  <h2>Как работает</h2>
  <p class="sec-lead">Всё, что однозначно записано в документе, извлекает код. Модель подключается только там, где нужен смысл. Поэтому сослаться на несуществующий пункт невозможно.</p>
  <div class="steps">
    <div class="step"><span class="num">01</span>
      <div><h3>Разбор на пункты</h3><p>Документ раскладывается на пронумерованные пункты с сохранением раздела и точной цитаты. Ссылка формируется из структуры файла, а не придумывается.</p></div>
      <span class="who code">код</span></div>
    <div class="step"><span class="num">02</span>
      <div><h3>Карта подразделений</h3><p>Из состава структуры извлекаются подразделения, а из обязанностей их руководителей — закреплённые функции.</p></div>
      <span class="who code">код</span></div>
    <div class="step"><span class="num">03</span>
      <div><h3>Сопоставление по смыслу</h3><p>«Вести переписку с руководителями» и «взаимодействовать с руководителями» — одна функция. Это понимает модель, а не поиск по словам.</p></div>
      <span class="who ai">модель</span></div>
    <div class="step key"><span class="num">04</span>
      <div><h3>Агент перепроверяет каждое подозрение</h3><p>Получив список возможных потерь, агент сам решает, что искать, вызывает инструменты поиска по документу и выносит вердикт: потеря подтверждена, функция найдена в другом пункте или честное «не уверен, нужен человек». Вердикт без ссылки на пункт система не принимает.</p></div>
      <span class="who ai">агент</span></div>
    <div class="step"><span class="num">05</span>
      <div><h3>Заключение с источниками</h3><p>Итоговый документ: что изменилось, на что смотреть в первую очередь, какие риски — и пункт-подтверждение под каждым выводом.</p></div>
      <span class="who code">код + модель</span></div>
  </div>
</div></section>

<section><div class="wrap guarantee">
  <div>
    <h2>Почему выводам можно верить</h2>
    <p class="sec-lead" style="margin-bottom:22px">Языковая модель, которой отдали документ целиком, уверенно называет номера пунктов, которых не существует. Для анализа реорганизации это недопустимо: вывод, который нельзя проверить, бесполезен.</p>
    <div class="quote"><b>Номера пунктов и принадлежность функций извлекает код.</b> Модель получает цитаты только через инструменты и не может сослаться на то, чего нет в документе.</div>
  </div>
  <div class="demo">
    <div class="demo-top"><i class="dot"></i><i class="dot"></i><i class="dot"></i><span>работа агента</span></div>
    <div class="verdict" style="border-top:0">
      <div class="row"><span class="tag warn">шаг 1</span><div><span class="cite">search_clauses</span> — поиск формулировки в комплекте «после»</div></div>
      <div class="row"><span class="tag warn">шаг 2</span><div><span class="cite">get_clause(«5.6.2»)</span> — точный текст найденного пункта</div></div>
      <div class="row"><span class="tag ok">вердикт</span><div>Функция сохранена, формулировка совпадает — <span class="cite">п. 5.6.2</span>. Подозрение снято.</div></div>
    </div>
  </div>
</div></section>

<section class="final"><div class="wrap">
  <h2>Проверьте на своём комплекте</h2>
  <p>Загрузите два комплекта документов — или запустите анализ на контрольном комплекте, он уже загружен в сервис.</p>
  <a class="btn" href="/app">Начать анализ</a>
</div></section>

<footer><div class="wrap">
  <span>Сверка · анализ организационной структуры и функционала</span>
  <span>HackAlem AI 2026 · команда Solnik</span>
</div></footer>
</body></html>
"""
