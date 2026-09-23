"""HTML-страницы сервиса: лендинг и рабочий экран.

Вёрстка без фреймворков: проект должен запускаться одной командой из README,
поэтому сборка фронтенда не вводится. Оформление следует эталонам, выбранным
заказчиком: белый лендинг с левым выравниванием и чёрно-белой парой кнопок,
рабочий экран — постоянный сайдбар и светло-серое полотно с белыми карточками.
"""

BASE_CSS = """
:root{
  color-scheme:light;
  --bg:#ffffff; --surface:#fafafa; --card:#ffffff;
  --ink:#09090b; --mut:#71717a; --mut2:#a1a1aa;
  --line:#e8e8ec; --line2:#d4d4d8; --muted:#f4f4f5;
  --acc:#09090b;                 /* основное действие — чёрное */
  --link:#2563eb;                /* ссылки на пункты документа */
  --ok:#16a34a; --ok-bg:#f0fdf4; --warn:#ca8a04; --warn-bg:#fefce8;
  --bad:#dc2626; --bad-bg:#fef2f2;
  --sans:"Inter",system-ui,-apple-system,"Segoe UI",sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,Consolas,monospace;
  --r:10px;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:15px;
  line-height:1.55;-webkit-font-smoothing:antialiased;letter-spacing:-.006em}
a{color:inherit;text-decoration:none}

.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;font:inherit;
  font-weight:500;font-size:14px;cursor:pointer;border-radius:9px;padding:10px 18px;
  border:1px solid var(--acc);background:var(--acc);color:var(--bg);white-space:nowrap;
  transition:opacity .14s ease,background .14s ease,border-color .14s ease}
.btn:hover{opacity:.88}
.btn.outline{background:var(--card);color:var(--ink);border-color:var(--line2)}
.btn.outline:hover{background:var(--muted);opacity:1}
.btn.sm{padding:7px 14px;font-size:13.5px;border-radius:8px}
.btn:disabled{opacity:.45;cursor:default}

/* поле выбора файла оформлено как кнопка */
input[type=file]{font:inherit;font-size:13px;color:var(--mut);max-width:100%}
input[type=file]::file-selector-button{font:inherit;font-size:13.5px;font-weight:500;
  margin-right:10px;padding:8px 14px;border-radius:8px;border:1px solid var(--line2);
  background:var(--card);color:var(--ink);cursor:pointer;transition:background .14s}
input[type=file]::file-selector-button:hover{background:var(--muted)}

:focus-visible{outline:2px solid var(--link);outline-offset:2px}
@media(prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
"""

LANDING = """
<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>OrgTrace — трассировка функций при реорганизации</title>
<link rel="icon" type="image/png" href="/static/favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=Inter:wght@400;500;600;700;800&display=swap">
<style>
__BASE__
.container{max-width:1180px;margin:0 auto;padding-inline:36px}
@media(max-width:700px){.container{padding-inline:20px}}

nav{border-bottom:1px solid var(--line);background:var(--bg);position:sticky;top:0;z-index:20}
nav .container{display:flex;align-items:center;justify-content:space-between;height:66px;gap:20px}
.brandrow{display:flex;align-items:center;gap:34px}
.brand{display:flex;align-items:center}
.brand img{height:28px;width:auto;display:block}
.navlinks{display:flex;gap:26px}
.navlinks a{font-size:14.5px;font-weight:500;color:var(--ink);opacity:.9}
.navlinks a:hover{opacity:.6}
.navbtns{display:flex;gap:10px}
@media(max-width:820px){.navlinks{display:none}}
@media(max-width:520px){.navbtns .btn.outline{display:none}.brand img{height:24px}}

.hero{padding-block:86px 60px;
  background:radial-gradient(760px 300px at 12% 0%,var(--muted),transparent 70%)}
.pill{display:inline-flex;align-items:center;border:1px solid var(--line);border-radius:999px;
  background:var(--card);padding:4px;font-size:13.5px;margin-bottom:34px;
  box-shadow:0 1px 2px rgba(9,9,11,.04)}
.pill b{font-family:var(--mono);font-size:11px;letter-spacing:.06em;text-transform:uppercase;
  background:var(--muted);border-radius:999px;padding:4px 10px;font-weight:500}
.pill span{padding:0 12px;color:var(--mut)}
.pill i{display:inline-flex;width:24px;height:24px;border-radius:999px;background:var(--muted);
  align-items:center;justify-content:center;font-style:normal;font-size:12px;margin-right:2px}
h1{font-size:clamp(38px,5.6vw,68px);line-height:1.04;letter-spacing:-.045em;font-weight:700;
  margin:0;max-width:17ch}
.lead{margin:24px 0 36px;max-width:50ch;font-size:clamp(16px,1.6vw,19px);color:var(--mut)}
.lead b{color:var(--ink);font-weight:600}
.actions{display:flex;gap:12px;flex-wrap:wrap}
.facts{display:flex;gap:30px;flex-wrap:wrap;margin-top:44px;padding-top:26px;
  border-top:1px solid var(--line)}
.fact b{display:block;font-size:22px;font-weight:600;letter-spacing:-.03em;line-height:1.2;
  font-variant-numeric:tabular-nums}
.fact span{font-size:13px;color:var(--mut)}

.shotwrap{padding-bottom:84px}
.frame{border:1px solid var(--line);border-radius:16px;padding:7px;background:var(--surface);
  box-shadow:0 24px 60px rgba(9,9,11,.09)}
.shot{border:1px solid var(--line);border-radius:11px;overflow:hidden;position:relative;background:var(--card)}
.shot img{display:block;width:100%;height:auto}

.mock{display:grid;grid-template-columns:186px 1fr;min-height:340px;font-size:12px;text-align:left}
.mock .rail{border-right:1px solid var(--line);padding:10px 9px;background:var(--card)}
.mock .rail .r{display:flex;align-items:center;gap:8px;padding:6px 9px;border-radius:7px;
  color:var(--mut);margin-bottom:2px}
.mock .rail .r.on{background:var(--ink);color:var(--bg);font-weight:500}
.mock .rail .r b{width:12px;height:12px;border-radius:3px;background:currentColor;opacity:.45;display:block}
.mock .rail .r.on b{opacity:.9}
.mock .rail .grp{font-size:10px;color:var(--mut2);text-transform:uppercase;letter-spacing:.08em;
  padding:12px 9px 5px}
.mock .body{padding:14px 16px;background:var(--surface)}
.mock .stats{display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin-bottom:11px}
.mock .stats div{background:var(--card);border:1px solid var(--line);border-radius:9px;padding:9px 11px}
.mock .stats b{display:block;font-size:19px;font-weight:600;letter-spacing:-.03em}
.mock .stats span{font-size:10px;color:var(--mut)}
.mock .card{background:var(--card);border:1px solid var(--line);border-left:3px solid var(--line2);
  border-radius:9px;padding:9px 11px;margin-bottom:7px}
.mock .card.ok{border-left-color:var(--ok)} .mock .card.warn{border-left-color:var(--warn)}
.mock .card strong{display:block;font-size:12.5px;margin-bottom:2px}
.mock .card em{font-style:normal;font-family:var(--mono);font-size:10.5px;color:var(--link)}
.mock .card p{margin:3px 0 0;color:var(--mut);font-size:11.5px}

section{padding-block:80px;border-top:1px solid var(--line)}
/* сетка возможностей: пунктирные границы и клетчатый узор в углу карточки */
.features h2.center,.features .center{text-align:center;margin-left:auto;margin-right:auto}
.features h2.center{max-width:none}
.fgrid{display:grid;grid-template-columns:repeat(3,1fr);border-top:1px dashed var(--line2);
  border-left:1px dashed var(--line2)}
.fcell{position:relative;overflow:hidden;padding:26px 26px 30px;
  border-right:1px dashed var(--line2);border-bottom:1px dashed var(--line2)}
.fpat{pointer-events:none;position:absolute;top:0;left:50%;margin:-8px 0 0 -80px;width:100%;height:100%;
  -webkit-mask-image:linear-gradient(#000,transparent);mask-image:linear-gradient(#000,transparent)}
.fpat-in{position:absolute;inset:0;background:linear-gradient(90deg,rgba(9,9,11,.05),rgba(9,9,11,.01));
  -webkit-mask-image:radial-gradient(farthest-side at top,#000,transparent);
  mask-image:radial-gradient(farthest-side at top,#000,transparent)}
.fpat svg{position:absolute;inset:0}
.fpat path{stroke:rgba(9,9,11,.30)}
.fpat rect{fill:rgba(9,9,11,.06)}
.ficon{width:24px;height:24px;color:var(--ink);opacity:.78;position:relative}
.fcell h3{position:relative;margin:38px 0 0;font-size:15.5px;font-weight:500;letter-spacing:-.015em}
.fcell p{position:relative;margin:7px 0 0;color:var(--mut);font-size:13.5px;font-weight:300;line-height:1.55}
@media(max-width:900px){.fgrid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:600px){.fgrid{grid-template-columns:1fr}}

h2{font-size:clamp(26px,3.3vw,38px);line-height:1.12;letter-spacing:-.035em;margin:0 0 14px;
  font-weight:700;max-width:20ch}
.sec-lead{color:var(--mut);max-width:60ch;margin:0 0 40px;font-size:16px}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.c{background:var(--card);border:1px solid var(--line);border-radius:var(--r);padding:24px;
  box-shadow:0 1px 2px rgba(9,9,11,.04)}
.c .n{font-family:var(--mono);font-size:11px;letter-spacing:.09em;color:var(--mut2);margin-bottom:12px}
.c h3{margin:0 0 8px;font-size:17px;letter-spacing:-.02em}
.c p{margin:0;color:var(--mut);font-size:14.5px}
.steps{display:grid;gap:10px}
.step{display:grid;grid-template-columns:34px 1fr auto;gap:18px;align-items:start;background:var(--card);
  border:1px solid var(--line);border-radius:var(--r);padding:20px 22px}
.step.key{border-color:var(--ink)}
.step .num{font-family:var(--mono);font-size:15px;color:var(--mut2)}
.step.key .num{color:var(--ink)}
.step h3{margin:0 0 5px;font-size:16.5px;letter-spacing:-.02em}
.step p{margin:0;color:var(--mut);font-size:14.5px;max-width:64ch}
.who{font-family:var(--mono);font-size:10.5px;letter-spacing:.05em;text-transform:uppercase;
  padding:5px 10px;border-radius:7px;white-space:nowrap;background:var(--muted);color:var(--mut)}
.who.ai{background:var(--ink);color:var(--bg)}
.cta2{padding-block:96px;border-top:1px solid var(--line)}
.cta2 .grid{display:grid;grid-template-columns:1fr 1fr;gap:56px;align-items:center}
.cta2 .art{background:#f4f4f5;border-radius:12px;overflow:hidden;aspect-ratio:4/3}
.cta2 .art img{width:100%;height:100%;object-fit:cover;display:block}
.cta2 h2{font-size:clamp(30px,4vw,46px);line-height:1.08;letter-spacing:-.035em;margin:0 0 20px;
  max-width:16ch;font-weight:600}
.cta2 p{color:var(--mut);font-size:clamp(16px,1.5vw,18px);max-width:46ch;margin:0 0 30px}
.cta2 .actions{display:flex;gap:10px;flex-wrap:wrap}
@media(max-width:900px){.cta2 .grid{grid-template-columns:1fr;gap:34px}
  .cta2 .art{min-height:260px}.cta2 .text{text-align:center}
  .cta2 h2,.cta2 p{margin-left:auto;margin-right:auto}.cta2 .actions{justify-content:center}}

footer{border-top:1px solid var(--line);background:var(--surface);color:var(--mut);font-size:14px}
.ftop{display:grid;grid-template-columns:1.4fr repeat(3,1fr);gap:40px;padding-block:56px 44px}
.fbrand img{height:28px;width:auto;display:block;margin-bottom:16px}
.fbrand p{margin:0;max-width:34ch;font-size:14px;line-height:1.6}
.fcol h4{margin:0 0 14px;font-size:13px;font-weight:600;color:var(--ink);letter-spacing:-.005em}
.fcol ul{list-style:none;margin:0;padding:0;display:grid;gap:10px}
.fcol a{color:var(--mut);transition:color .14s}
.fcol a:hover{color:var(--ink)}
.fcol li{font-size:14px}
.fbottom{border-top:1px solid var(--line);padding-block:22px;display:flex;justify-content:space-between;
  gap:14px;flex-wrap:wrap;font-size:13px;color:var(--mut2)}
@media(max-width:820px){.ftop{grid-template-columns:1fr 1fr}.fbrand{grid-column:1/-1}}
@media(max-width:480px){.ftop{grid-template-columns:1fr}}
@media(max-width:880px){.cards{grid-template-columns:1fr}
  .step{grid-template-columns:28px 1fr}.step .who{grid-column:2}
  .mock{grid-template-columns:1fr}.mock .rail{display:none}
  .mock .stats{grid-template-columns:repeat(2,1fr)}}
</style></head><body>

<nav><div class="container">
  <div class="brandrow">
    <a class="brand" href="/"><img src="/static/logo.png" alt="OrgTrace"></a>
    <div class="navlinks">
      <a href="#problem">Задача</a>
      <a href="#how">Как работает</a>
      <a href="#trust">Доверие к выводам</a>
    </div>
  </div>
  <div class="navbtns">
    <a class="btn outline sm" href="#how">Подробнее</a>
    <a class="btn sm" href="/app">Начать анализ</a>
  </div>
</div></nav>

<header class="hero"><div class="container">
  <div class="pill"><b>Кейс</b><span>спец-трек Казахтелеком · HackAlem AI</span><i>→</i></div>
  <h1>Реорганизация прошла. Какие функции потерялись?</h1>
  <p class="lead">Сравниваем комплекты документов <b>«до»</b> и <b>«после»</b>: находим потери, дублирование и конфликт интересов — и показываем <b>пункт, откуда взят каждый вывод</b>.</p>
  <div class="actions">
    <a class="btn outline" href="#how">Как это работает</a>
    <a class="btn" href="/app">Начать анализ →</a>
  </div>
  <div class="facts">
    <div class="fact"><b>7 из 7</b><span>контрольных случаев найдено</span></div>
    <div class="fact"><b>100%</b><span>выводов со ссылкой на пункт</span></div>
    <div class="fact"><b>~45 сек</b><span>на два документа по 300+ пунктов</span></div>
    <div class="fact"><b>0</b><span>выдуманных источников</span></div>
  </div>
</div></header>

<div class="container shotwrap">
  <div class="frame"><div class="shot">__PREVIEW__</div></div>
</div>

<div class="container">
  <section id="problem">
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

  <section id="how">
    <h2>Как работает</h2>
    <p class="sec-lead">Всё, что однозначно записано в документе, извлекает код. Модель подключается там, где нужен смысл. Поэтому сослаться на несуществующий пункт невозможно.</p>
    <div class="steps">
      <div class="step"><span class="num">01</span>
        <div><h3>Разбор на пункты</h3><p>Документ раскладывается на пронумерованные пункты с сохранением раздела и точной цитаты. Ссылка берётся из структуры файла.</p></div>
        <span class="who">код</span></div>
      <div class="step"><span class="num">02</span>
        <div><h3>Карта подразделений</h3><p>Из состава структуры извлекаются подразделения, а из обязанностей их руководителей — закреплённые функции.</p></div>
        <span class="who">код</span></div>
      <div class="step"><span class="num">03</span>
        <div><h3>Сопоставление по смыслу</h3><p>«Вести переписку с руководителями» и «взаимодействовать с руководителями» — одна функция. Это понимает модель, а не поиск по словам.</p></div>
        <span class="who ai">модель</span></div>
      <div class="step key"><span class="num">04</span>
        <div><h3>Агент перепроверяет каждое подозрение</h3><p>Агент сам решает, что искать, вызывает инструменты поиска по документу и выносит вердикт: потеря подтверждена, функция найдена в другом пункте или честное «не уверен». Вердикт без ссылки на пункт система не принимает.</p></div>
        <span class="who ai">агент</span></div>
      <div class="step"><span class="num">05</span>
        <div><h3>Заключение с источниками</h3><p>Что изменилось, на что смотреть в первую очередь, какие риски — и пункт-подтверждение под каждым выводом. Выгружается в Word.</p></div>
        <span class="who">код + модель</span></div>
    </div>
  </section>

  <section id="trust" class="features">
    <h2 class="center">Точно. Проверяемо. Честно.</h2>
    <p class="sec-lead center">Модель, которой отдали документ целиком, уверенно называет пункты, которых не существует. Здесь каждый вывод можно проверить по документу.</p>
    <div class="fgrid">
      <div class="fcell"><div class="fpat" aria-hidden="true"><div class="fpat-in"><svg width="100%" height="100%"><defs><pattern id="fg3" width="20" height="20" patternUnits="userSpaceOnUse" x="-12" y="4"><path d="M.5 20V.5H20" fill="none"/></pattern></defs><rect width="100%" height="100%" fill="url(#fg3)" stroke-width="0"/><svg x="-12" y="4" style="overflow:visible"><rect x="160" y="100" width="21" height="21"/><rect x="160" y="60" width="21" height="21"/><rect x="200" y="120" width="21" height="21"/><rect x="140" y="100" width="21" height="21"/><rect x="140" y="80" width="21" height="21"/></svg></svg></div></div><svg class="ficon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 9h16M4 15h16M10 3 8 21M16 3l-2 18"/></svg><h3>Ссылку даёт код</h3><p>Номера пунктов извлекаются из структуры документа, а не генерируются моделью.</p></div>
      <div class="fcell"><div class="fpat" aria-hidden="true"><div class="fpat-in"><svg width="100%" height="100%"><defs><pattern id="fg4" width="20" height="20" patternUnits="userSpaceOnUse" x="-12" y="4"><path d="M.5 20V.5H20" fill="none"/></pattern></defs><rect width="100%" height="100%" fill="url(#fg4)" stroke-width="0"/><svg x="-12" y="4" style="overflow:visible"><rect x="160" y="60" width="21" height="21"/><rect x="140" y="120" width="21" height="21"/><rect x="200" y="80" width="21" height="21"/><rect x="160" y="20" width="21" height="21"/><rect x="140" y="20" width="21" height="21"/></svg></svg></div></div><svg class="ficon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/><path d="m8.5 11 1.8 1.8 3.4-3.6"/></svg><h3>Агент ищет подтверждение</h3><p>Каждое подозрение он проверяет по документу и ссылается только на пункт, который сам получил.</p></div>
      <div class="fcell"><div class="fpat" aria-hidden="true"><div class="fpat-in"><svg width="100%" height="100%"><defs><pattern id="fg5" width="20" height="20" patternUnits="userSpaceOnUse" x="-12" y="4"><path d="M.5 20V.5H20" fill="none"/></pattern></defs><rect width="100%" height="100%" fill="url(#fg5)" stroke-width="0"/><svg x="-12" y="4" style="overflow:visible"><rect x="180" y="120" width="21" height="21"/><rect x="180" y="120" width="21" height="21"/><rect x="140" y="80" width="21" height="21"/><rect x="160" y="120" width="21" height="21"/><rect x="140" y="40" width="21" height="21"/></svg></svg></div></div><svg class="ficon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.7.3-1 .9-1 1.7"/><path d="M12 17h.01"/></svg><h3>«Не уверен» — нормальный ответ</h3><p>Где данных не хватает, система говорит об этом прямо и отдаёт решение человеку.</p></div>
      <div class="fcell"><div class="fpat" aria-hidden="true"><div class="fpat-in"><svg width="100%" height="100%"><defs><pattern id="fg6" width="20" height="20" patternUnits="userSpaceOnUse" x="-12" y="4"><path d="M.5 20V.5H20" fill="none"/></pattern></defs><rect width="100%" height="100%" fill="url(#fg6)" stroke-width="0"/><svg x="-12" y="4" style="overflow:visible"><rect x="140" y="80" width="21" height="21"/><rect x="180" y="20" width="21" height="21"/><rect x="140" y="40" width="21" height="21"/><rect x="200" y="120" width="21" height="21"/><rect x="180" y="60" width="21" height="21"/></svg></svg></div></div><svg class="ficon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m12 3 9 5-9 5-9-5 9-5Z"/><path d="m3 13 9 5 9-5"/></svg><h3>Потери, дубли, конфликты</h3><p>Три риска реорганизации в одном разборе — с разделами и счётчиками по каждому.</p></div>
      <div class="fcell"><div class="fpat" aria-hidden="true"><div class="fpat-in"><svg width="100%" height="100%"><defs><pattern id="fg7" width="20" height="20" patternUnits="userSpaceOnUse" x="-12" y="4"><path d="M.5 20V.5H20" fill="none"/></pattern></defs><rect width="100%" height="100%" fill="url(#fg7)" stroke-width="0"/><svg x="-12" y="4" style="overflow:visible"><rect x="180" y="40" width="21" height="21"/><rect x="200" y="120" width="21" height="21"/><rect x="140" y="20" width="21" height="21"/><rect x="140" y="60" width="21" height="21"/><rect x="140" y="100" width="21" height="21"/></svg></svg></div></div><svg class="ficon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8Z"/><path d="M14 3v5h5"/><path d="M9 13h6M9 17h4"/></svg><h3>Заключение в Word</h3><p>Таблица отклонений с пунктами-основаниями — документ, который можно нести руководителю.</p></div>
      <div class="fcell"><div class="fpat" aria-hidden="true"><div class="fpat-in"><svg width="100%" height="100%"><defs><pattern id="fg8" width="20" height="20" patternUnits="userSpaceOnUse" x="-12" y="4"><path d="M.5 20V.5H20" fill="none"/></pattern></defs><rect width="100%" height="100%" fill="url(#fg8)" stroke-width="0"/><svg x="-12" y="4" style="overflow:visible"><rect x="160" y="60" width="21" height="21"/><rect x="200" y="40" width="21" height="21"/><rect x="160" y="120" width="21" height="21"/><rect x="140" y="20" width="21" height="21"/><rect x="160" y="40" width="21" height="21"/></svg></svg></div></div><svg class="ficon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3 4 6v6c0 4.5 3.4 8 8 9 4.6-1 8-4.5 8-9V6Z"/><path d="m9 12 2 2 4-4"/></svg><h3>Работает без сети</h3><p>Если OpenAI недоступен, разбор продолжается в резервном режиме без модели.</p></div>
    </div>
  </section>
</div>

<section class="cta2"><div class="container"><div class="grid">
  <div class="art"><img src="/static/cta.jpg" alt="Два комплекта документов, пункты которых связаны линиями, лупа и отметка проверки"></div>
  <div class="text">
    <h2>Проверьте на своём комплекте</h2>
    <p>Загрузите положения «до» и «после» реорганизации — или запустите разбор на контрольном комплекте из кейса. Через минуту вы увидите потерянные, задвоенные и ставшие общими функции с пунктом-основанием для каждого вывода.</p>
    <div class="actions">
      <a class="btn" href="/app">Начать анализ</a>
      <a class="btn outline" href="#how">Как это работает</a>
    </div>
  </div>
</div></div></section>

<footer><div class="container">
  <div class="ftop">
    <div class="fbrand">
      <img src="/static/logo.png" alt="OrgTrace">
      <p>Трассировка функций при реорганизации: потери, дублирование и конфликт интересов — со ссылкой на пункт документа.</p>
    </div>
    <div class="fcol"><h4>Продукт</h4><ul>
      <li><a href="/app">Рабочий экран</a></li>
      <li><a href="#how">Как работает</a></li>
      <li><a href="#trust">Доверие к выводам</a></li>
    </ul></div>
    <div class="fcol"><h4>Задача</h4><ul>
      <li><a href="#problem">Риски реорганизации</a></li>
      <li><a href="/app">Контрольный комплект</a></li>
      <li><a href="#trust">Заключение в Word</a></li>
    </ul></div>
    <div class="fcol"><h4>Хакатон</h4><ul>
      <li>HackAlem AI 2026</li>
      <li>Спец-трек Казахтелеком</li>
      <li>Команда Solnik</li>
    </ul></div>
  </div>
  <div class="fbottom">
    <span>© 2026 OrgTrace</span>
    <span>Выводы носят рекомендательный характер и требуют проверки ответственным сотрудником.</span>
  </div>
</div></footer>
</body></html>
""".replace("__BASE__", BASE_CSS)


MOCK_PREVIEW = """
<div class="mock">
  <div class="rail">
    <div class="r on"><b></b> Сводка</div>
    <div class="grp">Отклонения</div>
    <div class="r"><b></b> Потери функций</div>
    <div class="r"><b></b> Снято агентом</div>
    <div class="r"><b></b> Дублирование</div>
    <div class="r"><b></b> Конфликт интересов</div>
    <div class="grp">Документы</div>
    <div class="r"><b></b> Подразделения</div>
    <div class="r"><b></b> Заключение</div>
  </div>
  <div class="body">
    <div class="stats">
      <div><b>4</b><span>подразделения</span></div>
      <div><b>2</b><span>создано</span></div>
      <div><b>24</b><span>дублирования</span></div>
      <div><b>1</b><span>конфликт интересов</span></div>
    </div>
    <div class="card ok"><strong>Создано подразделение ДИТААД</strong>
      <em>polozhenie_red9.docx, п. 3.4</em>
      <p>Департамент ИТ-аудита и анализа данных отсутствует в комплекте «до».</p></div>
    <div class="card warn"><strong>Конфликт интересов в ДККМ</strong>
      <em>п. 5.5.4 · п. 5.5.2</em>
      <p>Разрабатывает методические материалы и сам оценивает качество аудита.</p></div>
    <div class="card ok"><strong>Снято агентом: функция сохранена</strong>
      <em>подтверждение — п. 5.6.4</em>
      <p>Подозрение на потерю не подтвердилось, агент нашёл формулировку в новой редакции.</p></div>
  </div>
</div>
"""


def render_landing(preview_html: str) -> str:
    """preview_html — либо <img> с настоящим скриншотом, либо встроенный макет."""
    return LANDING.replace("__PREVIEW__", preview_html)
