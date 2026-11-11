#!/usr/bin/env python3
"""Build a dependency-free conference site into docs/ for GitHub Pages."""
from __future__ import annotations

import json
import shutil
from html import escape
from pathlib import Path
from urllib.parse import urlencode, urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs"
C = json.loads((ROOT / "data/conference.json").read_text(encoding="utf-8"))
TBU = '<span class="tbu" title="To be updated">TBU</span>'
ARROW = '<span class="arrow" aria-hidden="true">↗</span>'


def e(value):
    return escape(str(value), quote=True)


def value_or_tbu(value):
    return e(value) if value is not None and str(value).strip() else TBU


def checked_url(value):
    if not value:
        return None
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"External service links must be full HTTPS URLs: {value!r}")
    return e(value)


def email_link(subject=None):
    query = "?" + urlencode({"subject": subject}) if subject else ""
    return e("mailto:" + C["email"] + query)


def button(label, url, kind=""):
    return f'<a class="button {kind}" href="{url}">{e(label)}{ARROW}</a>'


def text_link(label, url):
    return f'<a class="text-link" href="{url}">{e(label)}<span aria-hidden="true">↗</span></a>'


def icon(kind, cls="detail-icon"):
    paths = {
        "calendar": '<rect x="4" y="6" width="24" height="22" rx="1"/><path d="M4 13h24M10 3v6M22 3v6M10 18h4M18 18h4M10 23h4"/>',
        "pin": '<path d="M26 13c0 8-10 16-10 16S6 21 6 13a10 10 0 0 1 20 0Z"/><circle cx="16" cy="13" r="3.5"/>',
        "dialogue": '<path d="M3 5h21v15H12l-6 5v-5H3Z"/><path d="M25 10h4v16h-5l-5 4v-4h-5v-3"/>',
        "humanism": '<circle cx="13" cy="11" r="5"/><circle cx="28" cy="15" r="5"/><path d="M3 36v-9a10 10 0 0 1 20 0v9M20 36v-7a9 9 0 0 1 18 0v7M7 36h30"/>',
        "science": '<ellipse cx="22" cy="22" rx="19" ry="7" transform="rotate(-35 22 22)"/><ellipse cx="22" cy="22" rx="19" ry="7" transform="rotate(35 22 22)"/><ellipse cx="22" cy="22" rx="7" ry="19"/><circle cx="22" cy="22" r="2" fill="currentColor"/>',
        "religion": '<path d="M7 39V20a15 15 0 0 1 30 0v19M14 39V20a8 8 0 0 1 16 0v19M3 39h38M22 1v5"/><circle cx="22" cy="24" r="3"/>',
    }
    view = "0 0 44 44" if kind in ("humanism", "science", "religion") else "0 0 32 32"
    return f'<svg class="{cls}" viewBox="{view}" fill="none" stroke="currentColor" stroke-width="1.1" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{paths[kind]}</svg>'


def brand():
    return '''<svg class="brand-mark" viewBox="0 0 44 48" fill="none" stroke="currentColor" stroke-width="1.1" aria-hidden="true"><path d="M7 44V22a15 15 0 0 1 30 0v22M14 44V22a8 8 0 0 1 16 0v22M2 44h40M22 1v7"/><circle cx="22" cy="26" r="3.5"/><path d="M4 13 1 10M40 13l3-3"/></svg><span><span class="brand-title">WYD·SOGANG <span>2027</span></span><span class="brand-caption">INTERNATIONAL CONFERENCE</span></span>'''


PAGES = [
    ("", "Home"),
    ("call-for-papers", "Call for Papers"),
    ("speakers", "Speakers"),
    ("program", "Program"),
    ("venue", "Venue"),
    ("organizers", "Organizers"),
    ("registration", "Registration"),
]


def header(slug, prefix):
    links = []
    for path, label in PAGES:
        if path == "organizers":
            continue
        current = ' aria-current="page"' if slug == path else ""
        css = ' class="nav-register"' if path == "registration" else ""
        arrow = ' <span aria-hidden="true">↗</span>' if path == "registration" else ""
        href = prefix + (path + "/" if path else "")
        links.append(f'<a href="{href}"{css}{current}>{e(label)}{arrow}</a>')
    return f'''<a class="skip-link" href="#main-content">Skip to content</a>
<header class="site-header"><div class="wrap header-inner">
<a class="brand" href="{prefix}" aria-label="WYD-Sogang 2027 home">{brand()}</a>
<button class="menu-toggle" type="button" aria-controls="site-navigation" aria-expanded="false" aria-label="Open navigation menu">Menu<span class="menu-lines" aria-hidden="true"></span></button>
<nav class="site-nav" id="site-navigation" aria-label="Main navigation">{''.join(links)}</nav>
</div></header>'''


def footer(prefix):
    links = ''.join(f'<a href="{prefix}{path}/">{label}</a>' for path, label in PAGES if path)
    planned_domain = ''
    if C.get('planned_site_url') and C.get('domain_status') != 'active':
        planned_domain = f'<p class="footer-domain">Planned conference address: <span>{e(urlparse(C["planned_site_url"]).netloc)}</span> {TBU}</p>'
    return f'''<footer class="site-footer"><div class="wrap">
<div class="footer-grid"><div><p class="footer-brand">AI and Human Flourishing.</p><p class="footer-description">{e(C['name'])}<br>{e(C['dates'])} · {e(C['venue'])}<br>{e(C['location'])}</p></div>
<div><h2 class="footer-heading">Explore the conference</h2><div class="footer-links">{links}</div></div>
<div><h2 class="footer-heading">Get in touch</h2><a class="footer-contact" href="{email_link()}">{e(C['email'])} ↗</a><p class="footer-description" style="margin-top:12px">For conference, submission and<br>registration inquiries.</p></div></div>
{planned_domain}<div class="footer-bottom"><p>© 2027 WYD-Sogang International Conference</p><p>Details will be updated as arrangements are finalized. TBU = To be updated.</p></div>
</div></footer>'''


def render(slug, title, description, body):
    prefix = "../" if slug else "./"
    canonical = C["site_url"] + (f"/{slug}/" if slug else "/")
    title_text = f"{title} | {C['short_name']}" if slug else f"{C['theme']} | {C['short_name']}"
    hero_preload = f'<link rel="preload" as="image" href="{prefix}assets/images/human-flourishing.jpg" fetchpriority="high">' if not slug else ""
    noindex = '<meta name="robots" content="noindex">' if slug == "404" else ""
    html = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title_text)}</title>
<meta name="description" content="{e(description)}">
<meta name="theme-color" content="#173d38">
{noindex}<link rel="canonical" href="{e(canonical)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(title_text)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{e(canonical)}">
<meta property="og:image" content="{e(C['site_url'])}/assets/images/social-preview.jpg">
<meta property="og:image:alt" content="An original illustration of people in dialogue, architectural arches and scientific orbits">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/svg+xml" href="{prefix}assets/images/favicon.svg">
<link rel="stylesheet" href="{prefix}assets/css/site.css">
{hero_preload}<script src="{prefix}assets/js/site.js" defer></script>
</head>
<body>
{header(slug,prefix)}
<main id="main-content" tabindex="-1">{body}</main>
{footer(prefix)}
</body>
</html>
'''
    if slug == "404":
        # The special GitHub Pages 404 may be served from any URL depth.
        html = html.replace('href="../', 'href="/').replace('src="../', 'src="/')
        target = OUT / "404.html"
    else:
        target = OUT / slug / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8")


def dates():
    return [
        ("Proposal submission", C["submission_deadline"]),
        ("Acceptance notification", C["notification_date"]),
        ("Early Bird registration", C["early_bird_deadline"]),
        ("Conference", C["dates"]),
    ]


def date_rows(rows):
    return '<dl class="dates-list">' + ''.join(f'<div class="date-row"><dt>{e(label)}</dt><dd>{value_or_tbu(value)}</dd></div>' for label,value in rows) + '</dl>'


def speakers(full=False):
    cards = []
    for speaker in C["speakers"]:
        title = f'<p class="speaker-title">Talk title: {value_or_tbu(speaker["talk_title"])}</p>' if full else ""
        bio = f'<p class="affiliation" style="margin-top:15px">{e(speaker["bio"])}</p>' if full and speaker["bio"] else ""
        cards.append(f'''<article class="speaker-card"><div class="speaker-art" aria-hidden="true"><span class="speaker-monogram">{e(speaker['initials'])}</span><span class="speaker-track">{e(speaker['track'])}</span></div><h3>{e(speaker['name'])}</h3><p class="affiliation">{e(speaker['affiliation'])}</p>{title}{bio}</article>''')
    return f'<div class="speakers">{"".join(cards)}</div><p class="source-note">{e(C["speakers_status"])}</p>'


def heading(title, subtitle, eyebrow):
    return f'''<div class="page-heading"><div class="wrap"><nav class="breadcrumb" aria-label="Breadcrumb"><a href="../">Home</a><span aria-hidden="true">/</span><span>{e(title)}</span></nav><p class="eyebrow">{e(eyebrow)}</p><h1>{e(title)}</h1><p class="lead">{e(subtitle)}</p></div></div>'''


def sidebar(items=(), registration=False):
    if registration:
        panel = f'<h2>Registration inquiries</h2><p>For questions about participation, fees or payment arrangements, contact the conference team.</p>{button("Email the conference team",email_link("WYD-Sogang 2027 registration inquiry"))}'
    else:
        panel = f'<h2>At a glance</h2><p>{e(C["dates"])}<br>{e(C["venue"])}<br>{e(C["location"])}</p>{date_rows(dates()[:2])}{button("Registration information","../registration/")}'
    nav = f'<nav class="side-nav" aria-label="On this page"><p class="side-label">On this page</p>{"".join(f"<a href=\"#{key}\">{e(label)}</a>" for key,label in items)}</nav>' if items else ""
    return f'<aside class="sidebar"><div class="side-panel">{panel}</div>{nav}</aside>'


def layout(content, items=(), registration=False):
    return f'<div class="wrap page-layout"><div>{content}</div>{sidebar(items, registration)}</div>'


def article(key, title, body):
    return f'<section class="article-section" id="{key}"><h2>{title}</h2>{body}</section>'


def home():
    track_cards = []
    for track in C['tracks']:
        track_cards.append(f'''<a class="track" href="./call-for-papers/#{track['id']}"><div class="track-top"><span class="track-number">{track['number']}</span>{icon(track['id'],'track-glyph')}</div><h3>{track['name']}</h3><p>{e(track['summary'])}</p><div class="track-bottom"><span>Explore topics</span><span aria-hidden="true">↗</span></div></a>''')
    body = f'''<section class="hero" aria-labelledby="hero-title"><div class="wrap hero-inner">
<div class="hero-copy"><p class="eyebrow">2027 WYD-Sogang International Conference</p><h1 id="hero-title">AI and Human<br><em>Flourishing.</em></h1><p class="hero-summary">A dialogue across humanism, science and religion on the future we shape with AI.</p><div class="actions">{button('Explore the Call for Papers','./call-for-papers/')}{text_link('About the conference','#about')}</div></div>
<img class="hero-art" src="./assets/images/human-flourishing.jpg" width="1536" height="1024" alt="An imagined landscape of people in conversation among open arches, a garden and scientific orbits, illustrating humanism, science and religion." fetchpriority="high"><span class="hero-art-label">A place for shared inquiry · Original illustration</span>
</div></section>
<div class="event-ribbon"><div class="wrap ribbon-inner"><div class="event-detail">{icon('calendar')}<div><span class="detail-label">The dates</span><span class="detail-value">{e(C['dates'])}</span></div></div><div class="event-detail">{icon('pin')}<div><span class="detail-label">The place</span><span class="detail-value">Sogang University, Seoul</span></div></div><div class="event-detail">{icon('dialogue')}<div><span class="detail-label">The conversation</span><span class="detail-value">Humanism · Science · Religion</span></div></div></div></div>
<section class="section section-rule" id="about"><div class="wrap intro-grid"><div><p class="eyebrow">The conference</p><h2>What does it mean<br>to flourish in<br>an age of AI?</h2></div><div class="intro-text"><p>Artificial intelligence is changing how we learn, work, discover and understand ourselves. Its possibilities invite hope. Its risks call for careful thought.</p><p>The 2027 WYD-Sogang International Conference brings these questions into a shared conversation. Hosted at Sogang University in Seoul, the conference explores AI and human flourishing through humanism, science and religion.</p><p>We invite scholars from across disciplines to examine the benefits and risks of AI, and to consider how its development can serve human life.</p></div></div></section>
<section class="section"><div class="wrap"><div class="section-head"><div><p class="eyebrow">Three perspectives. A shared inquiry.</p><h2>Across disciplines.</h2></div>{text_link('All topics & submission details','./call-for-papers/')}</div><div class="tracks">{''.join(track_cards)}</div><p class="open-track">Thinking beyond these fields? <a href="./call-for-papers/#open-track">Open-track and interdisciplinary proposals are also welcome.</a></p></div></section>
<section class="section sage-section"><div class="wrap"><div class="section-head"><div><p class="eyebrow">Voices in the conversation</p><h2>Keynote speakers.</h2></div>{text_link('Meet the speakers','./speakers/')}</div>{speakers()}</div></section>
<section class="section"><div class="wrap dates-grid"><div><p class="eyebrow">Plan your participation</p><h2>Dates to know.</h2><p class="lead">Join us in Seoul in August 2027. Submission and registration milestones will be announced here.</p></div><div>{date_rows(dates())}<p class="tbu-legend">TBU = To be updated. Deadline times and time zone: {value_or_tbu(C['deadline_timezone'])}</p></div></div></section>
<section class="invitation"><div class="wrap invitation-inner"><div><p class="eyebrow">An invitation to contribute</p><h2>Bring your perspective<br>to the conversation.</h2><p>We welcome 300-word proposals exploring AI through humanism, science, religion and beyond.</p></div>{button('Read the Call for Papers','./call-for-papers/','light')}</div></section>'''
    render('', 'Home', 'AI and Human Flourishing. Join the 2027 WYD-Sogang International Conference, 3–5 August 2027 at Sogang University, Seoul, South Korea.', body)


def cfp():
    topics = ''
    for track in C['tracks']:
        items = ''.join(f'<li>{e(topic)}</li>' for topic in track['topics'])
        topics += f'<section class="topic-section" id="{track["id"]}"><div class="topic-title"><span class="track-number">{track["number"]}</span><h3>{track["name"]}</h3></div><p>{e(track["description"])}</p><ul class="topic-list">{items}</ul></section>'
    content = article('invitation', 'An invitation to scholars.', '<p>Sogang University invites proposals for the 2027 WYD-Sogang International Conference: AI and Human Flourishing, taking place on 3–5 August 2027.</p><p>Amid the coexisting promises and perils of artificial intelligence, the conference examines the theme “AI: humanism, science and religion.” We welcome submissions that analyze the risks and benefits of AI through these fields, including multidisciplinary approaches that bridge them.</p>')
    content += article('topics', 'Themes & topics.', f'<p>The following topics offer starting points for proposals. Contributions need not be limited to these areas.</p>{topics}<section class="topic-section" id="open-track"><div class="topic-title"><span class="track-number">+</span><h3>Open track</h3></div><p>Proposals beyond the three primary domains are welcome, including diverse perspectives and multidisciplinary work addressing AI and human flourishing.</p></section>')
    content += article('submission', 'Preparing your proposal.', f'<p>Please prepare a {C["proposal_words"]}-word proposal. Further submission requirements will be published as arrangements are finalized.</p>{date_rows([("Proposal length",str(C["proposal_words"])+" words"),("Submission deadline",C["submission_deadline"]),("Deadline time zone",C["deadline_timezone"]),("File format & template",C["submission_instructions"]),("Review & presentation format",None),("Proceedings / publication policy",None)])}')
    submission_url = checked_url(C['submission_url'])
    if submission_url:
        how = f'<p>Submit your proposal using the conference submission portal.</p>{button("Open the submission portal",submission_url)}'
    elif C['submission_email']:
        how = f'<p>Send your proposal to <a href="mailto:{e(C["submission_email"])}">{e(C["submission_email"])}</a>.</p>'
    else:
        how = f'<div class="notice"><h3 class="notice-heading">Submission method {TBU}</h3><p>The submission portal or submission email address and opening date will be announced here. Proposal submission is not yet open.</p></div><p>For questions about the Call for Papers, contact <a href="{email_link("WYD-Sogang 2027 submission inquiry")}">{e(C["email"])}</a>.</p>'
    content += article('how-to-submit', 'How to submit.', how)
    content += article('important-dates', 'Important dates.', date_rows([('Proposal submission',C['submission_deadline']),('Acceptance notification',C['notification_date']),('Final paper / materials',C['final_paper_deadline']),('Conference',C['dates'])]) + '<p class="source-note">The Call for Papers is being finalized. Items marked TBU will be updated on this website.</p>')
    body = heading('Call for Papers', 'Explore the promises and risks of AI, and what they mean for human life, through humanism, science, religion and beyond.', 'Contribute to the conversation')
    body += layout(content, [('invitation','The invitation'),('topics','Themes & topics'),('submission','Proposal guidelines'),('how-to-submit','How to submit'),('important-dates','Important dates')])
    render('call-for-papers','Call for Papers','Submit a 300-word proposal to WYD-Sogang 2027. Explore topics in humanism, science, religion and the open track.',body)


def speakers_page():
    body = heading('Keynote speakers', 'Perspectives from humanism, science and religion, brought into a shared conversation about AI and human flourishing.', 'Voices across disciplines')
    body += f'<section class="section"><div class="wrap">{speakers(True)}<div style="margin-top:48px" class="notice"><h2 class="notice-heading">Speaker details {TBU}</h2><p>Final participation, biographies, talk abstracts, additional invited speakers and the session schedule will be announced as they are confirmed. Names and affiliations above follow the Call for Papers draft.</p></div>{text_link("View program information","../program/")}</div></section>'
    render('speakers','Keynote Speakers','Keynote speakers listed in the WYD-Sogang 2027 Call for Papers draft: Stanton E. F. Wortham, Hyunjung Kim and Andrew Davison.',body)


def program():
    content = article('overview','Three days of shared inquiry.', f'<p>The conference will take place on {e(C["dates"])} at {e(C["venue"])} in {e(C["location"])}. The detailed program is being prepared.</p><div class="program-empty"><p class="eyebrow">Conference program</p><h3>Session schedule {TBU}</h3><p>{e(C["program_note"]) if C["program_note"] else "Session times, keynote talks, presentation formats and other program details will appear here once confirmed."}</p>{text_link("Explore the keynote speakers","../speakers/")}</div>')
    content += article('schedule','Program details.',date_rows([('Daily session schedule',None),('Keynote titles & times',None),('Paper presentations',None),('Presentation language',None),('On-site / online participation',None),('Social events & meals',None)]))
    content += article('presenters','For presenters.', '<p>Presentation duration, slide requirements, session allocation and technical arrangements will be shared once the program is confirmed.</p><p>Presentation instructions: '+TBU+'</p>')
    render('program','Program','Program and schedule for the 2027 WYD-Sogang International Conference, 3–5 August 2027 at Sogang University.',heading('Program','3–5 August 2027 · Sogang University, Seoul. The detailed schedule will be published as arrangements are confirmed.','The conference at a glance')+layout(content,[('overview','Overview'),('schedule','Program details'),('presenters','For presenters')]))


def registration():
    fees = C['fees']
    url = checked_url(C['registration_url'])
    # An active registration form requires published terms, not just a URL.
    ready = bool(url and C['privacy_policy'] and C['refund_policy'] and C['registration_inclusions'] and fees['status'] == 'confirmed')
    status = f'<p>Registration is open. Please review the fees, inclusions and policies before registering.</p>{button("Open registration",url)}' if ready else '<p>Registration is not yet open. The registration form, opening date and payment instructions will be published here once confirmed.</p>'
    content = article('registration-status','Registration information.',f'<div class="notice"><div class="status-heading"><span class="status-dot" aria-hidden="true"></span><h2>{"Registration open" if ready else "Registration opening"}</h2>{"" if ready else TBU}</div>{status}</div>{date_rows([("Registration opens",C["registration_open_date"]),("Early Bird deadline",C["early_bird_deadline"]),("Registration closes",C["registration_deadline"])])}')
    fee_status = 'Confirmed rates' if fees['status']=='confirmed' else 'Proposed rates'
    fee_note = 'Rates are confirmed.' if fees['status']=='confirmed' else 'The rates below are proposed and subject to final confirmation. They are shown in US dollars. Payment is not yet available.'
    cards = f'<div class="fee-grid"><div class="fee-card early"><h3 class="fee-label">Early Bird</h3><p class="price"><small>US$</small>{fees["early_bird"]}</p><p class="fee-deadline">Deadline: {value_or_tbu(C["early_bird_deadline"])}</p></div><div class="fee-card"><h3 class="fee-label">Standard registration</h3><p class="price"><small>US$</small>{fees["standard"]}</p><p class="fee-deadline">Registration period: {value_or_tbu(C["registration_deadline"])}</p></div></div>'
    content += article('fees','Registration fees.',f'<p class="eyebrow">{fee_status}</p><p>{fee_note}</p>{cards}{date_rows([("Domestic fee & currency",fees["domestic_amount"]),("Student / special rates",None),("What the fee includes",C["registration_inclusions"])])}')
    paypal = checked_url(fees['paypal_url'])
    international = f'<p>PayPal payment is available through the official conference payment link.</p>{button("Pay with PayPal",paypal)}' if ready and paypal else f'<p>PayPal Business is being considered for international payments. The payment method and official payment link are {TBU}. No payment is being collected at this stage.</p>'
    domestic_url = checked_url(fees['domestic_payment_url'])
    if ready and (fees['domestic_payment_instructions'] or domestic_url):
        domestic = f'<p>{e(fees["domestic_payment_instructions"])}</p>' if fees['domestic_payment_instructions'] else '<p>Pay using the official domestic payment page.</p>'
        if domestic_url:
            domestic += button('Domestic payment · 국내 결제', domestic_url)
    else:
        domestic = f'<p>The domestic payment method, receiving entity, payment currency and payment confirmation process are {TBU}. Please wait for official payment instructions.</p>'
    content += article('payment','Payment methods.',f'<div class="payment-block"><div class="payment-title"><h3>International participants</h3>{"" if ready and paypal else TBU}</div>{international}</div><div class="payment-block"><div class="payment-title"><h3>Participants in Korea · 국내 참가자</h3>{"" if ready and (fees["domestic_payment_instructions"] or domestic_url) else TBU}</div>{domestic}</div>')
    content += article('policies','Registration policies.',date_rows([('Cancellation & refunds',C['refund_policy']),('Registration confirmation / receipt',None),('Author registration requirements',None),('Privacy notice & consent',C['privacy_policy'])]))
    faqs = [
        ('Can I register or pay now?', 'Registration and payment are not yet open. The official form and payment instructions will be published on this page once confirmed.' if not ready else 'Use the registration link above, and follow the official payment instructions.'),
        ('Can participants in Korea pay in Korean won?', 'The domestic payment currency, fee and receiving account are TBU. The proposed US dollar rates do not yet specify a Korean won amount.' if not fees['domestic_amount'] else str(fees['domestic_amount'])),
        ('What is included in the fee?', C['registration_inclusions'] or 'TBU. Conference access, meals, refreshments, materials and any social events will be specified before registration opens.'),
        ('Who should I contact about registration?', f'Please email the conference team at {C["email"]}.'),
    ]
    content += article('faq','Frequently asked questions.', ''.join(f'<details><summary>{e(question)}</summary><p>{e(answer)}</p></details>' for question,answer in faqs))
    render('registration','Registration','WYD-Sogang 2027 registration information. Proposed fees: Early Bird US$100, standard US$150. Registration and payment details to be updated.',heading('Registration','Join the conversation in Seoul. Find participation fees, registration updates and payment information here.','Plan your participation')+layout(content,[('registration-status','Registration status'),('fees','Fees'),('payment','Payment methods'),('policies','Policies'),('faq','Frequently asked questions')],registration=True))


def venue():
    content = f'<div class="venue-panel"><p class="venue-city">Seoul · South Korea</p><h2>Sogang University</h2><p>{e(C["dates"])}</p>{text_link("Visit the university website","https://www.sogang.ac.kr/en/home")}</div>'
    content += article('location','Conference venue.',f'<p>The conference will be hosted at Sogang University in Seoul, South Korea. The exact building, room and campus directions will be published here.</p>{date_rows([("Host university",C["venue"]),("City",C["location"]),("Building",C["venue_building"]),("Room / registration desk",C["venue_room"])])}')
    content += article('travel','Travel & accommodation.',f'{date_rows([("Airport & public transport",C["travel_information"]),("Accommodation information",C["accommodation_information"]),("Visa / invitation letter support",C["visa_information"])])}<p class="source-note">Travel arrangements and conference-specific guidance will be updated as they are confirmed.</p>')
    content += article('accessibility','Accessibility & assistance.',f'<p>Venue accessibility information and on-site assistance arrangements are {value_or_tbu(C["accessibility_contact"])}.</p><p>For questions about access or other participation needs, please contact <a href="{email_link("WYD-Sogang 2027 accessibility inquiry")}">{e(C["email"])}</a>.</p>')
    render('venue','Venue & Travel','Venue and travel information for WYD-Sogang 2027 at Sogang University, Seoul, South Korea.',heading('Venue & travel','Sogang University · Seoul, South Korea. We look forward to welcoming you in August 2027.','Meet us in Seoul')+layout(content,[('location','Conference venue'),('travel','Travel & accommodation'),('accessibility','Accessibility')]))


def organizers():
    content = article('host','Host institution.', '<div class="committee-row"><h3>Sogang University</h3><p>Seoul, South Korea</p></div>')
    content += article('committee','Organizing committee.',f'<p>{e(C["committee_note"]) if C["committee_note"] else "The full organizing committee, official roles and program committee will be published after confirmation."}</p>{date_rows([("Conference chairs",None),("Organizing committee",None),("Program committee",None),("Sponsors & partners",None)])}')
    content += article('contact','Conference contact.',f'<p>For conference information, submission questions, registration and participation inquiries, please contact:</p><p><a href="{email_link()}">{e(C["email"])}</a></p><div class="committee-row"><h3>Website coordination</h3><p>Taehoon Kim · Sogang University</p></div>')
    render('organizers','Organizers & Contact','Organizing committee and official contact for the 2027 WYD-Sogang International Conference: wydsc2027@sogang.ac.kr.',heading('Organizers & contact','Hosted by Sogang University. Contact the conference team for information about participating or contributing.','The people behind the conversation')+layout(content,[('host','Host institution'),('committee','Organizing committee'),('contact','Contact')]))


def main():
    OUT.mkdir(exist_ok=True)
    # Never delete arbitrary files from docs/. Copy only site-owned assets.
    shutil.copytree(ROOT/'assets',OUT/'assets',dirs_exist_ok=True)
    for build in [home,cfp,speakers_page,program,registration,venue,organizers]:
        build()
    render('404','Page not found','This page could not be found on the WYD-Sogang 2027 website.',f'<div class="wrap not-found"><p class="eyebrow">404 · Page not found</p><h1>Let’s find your way.</h1><p class="lead">The page you’re looking for may have moved.</p>{button("Back to the conference","../")}</div>')
    (OUT/'.nojekyll').write_text('',encoding='utf-8')
    if C.get('domain_status') == 'active':
        if C['site_url'] != C.get('planned_site_url'):
            raise ValueError('The active site_url must match planned_site_url before custom-domain publication.')
        (OUT/'CNAME').write_text(urlparse(C['site_url']).netloc+'\n',encoding='utf-8')
    urls = [C['site_url'] + (f'/{slug}/' if slug else '/') for slug,_ in PAGES]
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(f'<url><loc>{e(url)}</loc><lastmod>{e(C["updated"])}</lastmod></url>\n' for url in urls) + '</urlset>\n'
    (OUT/'sitemap.xml').write_text(sitemap,encoding='utf-8')
    (OUT/'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {C["site_url"]}/sitemap.xml\n',encoding='utf-8')
    print(f'Built {len(PAGES)} pages + 404 into {OUT}')


if __name__ == '__main__':
    main()
