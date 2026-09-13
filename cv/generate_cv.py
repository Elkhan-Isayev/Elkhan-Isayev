#!/usr/bin/env python3
"""Build the ATS-friendly two-page CV PDF.

    pip install reportlab
    python cv/generate_cv.py

Output: cv/Elkhan_Isayev_CV.pdf
"""

import os

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_JUSTIFY, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Elkhan_Isayev_CV.pdf")

# ---------------------------------------------------------------- page setup

PAGE_W, PAGE_H = A4
MARGIN_X, MARGIN_Y = 15 * mm, 11 * mm
CONTENT_W = PAGE_W - 2 * MARGIN_X

ACCENT = HexColor("#1F3A5F")
TEXT = HexColor("#1A1A1A")
MUTED = HexColor("#444444")
HAIRLINE = HexColor("#CCCCCC")

# Right-aligned date column: one width for role rows, a wider one for the
# short date labels used by education / certifications.
DATE_COL = 173.4803
DATE_COL_SHORT = 132.6614

# ------------------------------------------------------------------- styles


def _s(name, **kw):
    kw.setdefault("fontName", "Helvetica")
    kw.setdefault("textColor", TEXT)
    return ParagraphStyle(name, **kw)


S_NAME = _s("name", fontName="Helvetica-Bold", fontSize=21, leading=24, textColor=ACCENT)
S_HEADLINE = _s("headline", fontSize=11.5, leading=14, spaceBefore=2)
S_CONTACT = _s("contact", fontSize=9, leading=13, textColor=MUTED, spaceBefore=4)
S_SECTION = _s(
    "section", fontName="Helvetica-Bold", fontSize=10.5, leading=12,
    textColor=ACCENT, spaceBefore=6,
)
S_SUMMARY = _s("summary", fontSize=9.5, leading=13.6, alignment=TA_JUSTIFY)
S_SKILL = _s("skill", fontSize=9.3, leading=13.5, spaceBefore=1)
S_COMPANY = _s(
    "company", fontName="Helvetica-Bold", fontSize=11, leading=13,
    textColor=ACCENT, spaceBefore=3,
)
S_META = _s("meta", fontName="Helvetica-Oblique", fontSize=9, leading=12, textColor=MUTED)
S_ROLE = _s("role", fontName="Helvetica-Bold", fontSize=10, leading=12.5)
S_DATE = _s(
    "date", fontName="Helvetica-Oblique", fontSize=9, leading=12.5,
    textColor=MUTED, alignment=TA_RIGHT,
)
S_BULLET = _s(
    "bullet", fontSize=9.5, leading=13, spaceBefore=0.7,
    leftIndent=24, bulletIndent=12, bulletFontName="Helvetica", bulletFontSize=10,
)
S_ENTRY = _s("entry", fontName="Helvetica-Bold", fontSize=9.8, leading=12.5)
S_ENTRY_DESC = _s("entrydesc", fontSize=9.4, leading=12.7, textColor=MUTED)
S_LANG = _s("lang", fontSize=9.5, leading=14, spaceBefore=2)

S_SKILL_FIRST = ParagraphStyle("skillfirst", parent=S_SKILL, spaceBefore=0)
S_BULLET_FIRST = ParagraphStyle("bulletfirst", parent=S_BULLET, spaceBefore=0)
S_PROJECT = ParagraphStyle("project", parent=S_ENTRY, spaceBefore=5)
S_PROJECT_DESC = ParagraphStyle("projectdesc", parent=S_ENTRY_DESC, spaceBefore=1.5)


class Rule(Flowable):
    """Horizontal rule with explicit space above and below the stroke."""

    def __init__(self, thickness, color, above=0.0, below=0.0):
        Flowable.__init__(self)
        self.thickness, self.color = thickness, color
        self.above, self.below = above, below
        self.height = above + below
        self.width = CONTENT_W

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        return availWidth, self.height

    def draw(self):
        c = self.canv
        c.saveState()
        c.setStrokeColor(self.color)
        c.setLineWidth(self.thickness)
        c.line(0, self.below, self.width, self.below)
        c.restoreState()


def link(url, label):
    return '<link href="%s"><font color="#1F3A5F">%s</font></link>' % (url, label)


def section(title):
    return [Paragraph(title, S_SECTION), Rule(0.8, ACCENT, above=3.8, below=3)]


def separator():
    rule = Rule(0.4, HAIRLINE)
    rule.spaceBefore = 0.4
    return [Spacer(1, 2.2), rule, Spacer(1, 0.5)]


def bullet(text, first=False):
    return Paragraph(text, S_BULLET_FIRST if first else S_BULLET, bulletText="•")


def role(title, dates, short=False, space_before=5):
    col = DATE_COL_SHORT if short else DATE_COL
    left_pad, bottom_pad = (0, 2) if short else (12, 0)
    style = S_ENTRY if short else S_ROLE
    tbl = Table(
        [[Paragraph(title, style), Paragraph(dates, S_DATE)]],
        colWidths=[CONTENT_W - col, col],
    )
    tbl.setStyle(
        TableStyle([
            ("LEFTPADDING", (0, 0), (0, 0), left_pad),
            ("LEFTPADDING", (1, 0), (1, 0), 0),
            ("RIGHTPADDING", (0, 0), (-1, 0), 0),
            ("TOPPADDING", (0, 0), (-1, 0), 0),
            ("BOTTOMPADDING", (0, 0), (-1, 0), bottom_pad),
            ("VALIGN", (0, 0), (-1, 0), "TOP"),
        ])
    )
    tbl.spaceBefore = 4 if short else space_before
    return tbl


def job(company, meta, roles):
    """roles: list of (title, dates, [bullets]); the first is glued to the header."""
    out = []
    for i, (title, dates, bullets) in enumerate(roles):
        head = role(title, dates, space_before=5 if i == 0 else 3.7)
        block = [head] + [bullet(b, first=(j == 0)) for j, b in enumerate(bullets)]
        if i == 0:
            dotted = meta.replace(" · ", " &nbsp;·&nbsp; ")
            block = [Paragraph(company, S_COMPANY), Paragraph(dotted, S_META)] + block
        out.append(KeepTogether(block))
    return out


# ------------------------------------------------------------------ content

SUMMARY = (
    "Senior Software Engineer with experience in the IT industry since 2016, specializing in high-load "
    "and enterprise-grade systems. Proven track record leading technical direction, designing scalable "
    "microservice architectures, and delivering reliable, maintainable solutions. Polyglot engineer "
    "across Go, Java, and PHP who runs agentic coding tools as part of everyday delivery and builds for "
    "them: Erebus, an open-source MCP server exposing 51 tools to AI agents."
)

SKILLS = [
    (
        "AI Tooling",
        "Claude Code, Cursor, and GitHub Copilot on production work; agent-assisted review and refactoring",
    ),
    (
        "Agentic Engineering",
        "Model Context Protocol (MCP) servers, multi-agent workflows, tool design for coding agents",
    ),
    ("Languages", "Go, Java, PHP, C#, TypeScript, JavaScript, SQL / PL-SQL"),
    ("Frameworks", "Spring Boot, Node.js, .NET Core, Angular, React.js, Electron, Laravel"),
    ("Messaging &amp; Data", "Apache Kafka, RabbitMQ, Redis, Elasticsearch, Avro, Oracle"),
    ("Infrastructure &amp; DevOps", "Docker, Kubernetes, CI/CD, Camunda, Wiki.js, Git"),
    ("Practices", "Microservices, System Design, SDLC, High-load Systems, Observability / Alerting"),
]

JOBS = [
    (
        "Push30",
        "Baku, Azerbaijan · On-site · Full-time",
        [(
            "Senior Software Engineer", "Mar 2026 – Present",
            [
                "Develop backend services across <b>Go</b>, <b>Java</b>, and <b>PHP</b>, contributing to core platform features and integrations.",
                "Delivered a production integration with a <b>Kazakhstani bank</b> for cross-border payments and banking.",
                "Authored shared libraries for <b>Apache Kafka</b> messaging and standardized logging across services.",
                "Established <b>SDLC</b> processes and configured monitoring and <b>alerting</b> to strengthen observability.",
                "Rolled out a company-wide <b>Wiki.js</b> documentation portal, centralizing engineering knowledge.",
            ],
        )],
    ),
    (
        "Hubpoint.AI",
        "AI-Powered Appointment Scheduling Platform · Remote · Part-time",
        [
            (
                "Technical Advisor", "Feb 2026 – Present",
                [
                    "Advise on iOS and Android production releases, App Store Connect and Google Play submissions.",
                    "Guide preparation of app store assets, metadata, and compliance, and support Firebase Cloud Messaging and mobile build configuration.",
                ],
            ),
            (
                "Technical Lead", "May 2025 – Feb 2026",
                [
                    "Led the technical direction of the platform across mobile, backend, infrastructure, DevOps, and AI workstreams.",
                    "Defined architectural separation to improve maintainability and scalability, and established SDLC processes for efficient delivery and production readiness.",
                ],
            ),
        ],
    ),
    (
        "Deviofy FZCO",
        "Remote · Full-time",
        [(
            "Technical Lead", "Jan 2025 – Mar 2026",
            [
                "Led end-to-end development and feature delivery across multiple projects.",
                "Managed cross-functional teams spanning Backend, Frontend, and QA to ensure seamless collaboration.",
                "Built and integrated <b>Stripe</b> monetization to enable new revenue streams.",
            ],
        )],
    ),
    (
        "Kapital Bank",
        "Baku, Azerbaijan · On-site · Full-time",
        [
            (
                "Technical Lead", "Sep 2024 – Jan 2025",
                [
                    "Integrated mobile banking with the credit system via <b>Camunda</b> to enable online card delivery.",
                    "Designed infrastructure diagrams, microservice decomposition, and dependency mappings; managed dependency switching and access control during migration to a new <b>Kubernetes</b> cluster.",
                    "Created onboarding diagrams, roadmaps, and sessions to accelerate new team members' integration.",
                ],
            ),
            (
                "Senior Software Engineer", "Apr 2021 – Sep 2024",
                [
                    "Led digitalization of social government payments through mobile banking, reducing branch operational costs and increasing customer accessibility.",
                    "Delivered chatbot identification features that optimized Average Handling Time (AHT) by <b>30%</b> and implemented automated card-issue resolution logic.",
                    "Built a CRM admin panel with a role matrix and streamed call-center reporting into the Data Warehouse via <b>Kafka</b>.",
                    "Developed Gateway, BFF, and microservice layers; provisioned <b>Elasticsearch, Kafka, and Redis</b> with DevOps and wrote PL/SQL data-migration scripts for Oracle.",
                ],
            ),
            (
                "Middle Software Engineer", "Jul 2020 – Apr 2021",
                [
                    "Decomposed a monolithic telephony application into independent micro-projects using <b>RabbitMQ</b>, improving scalability and maintainability.",
                    "Developed socket-based interfaces and a real-time dashboard to intercept call events and monitor live telephony statistics.",
                ],
            ),
        ],
    ),
    (
        "Intelec Artificial Intelligence",
        "Switzerland · Remote · Full-time",
        [(
            "Software Engineer", "Jul 2019 – Sep 2019",
            ["Designed and developed an image annotation system for Active Learning using <b>TypeScript</b> and <b>Angular</b>, working closely with the business team."],
        )],
    ),
    (
        "REMART Group",
        "Azerbaijan · On-site · Internship",
        [(
            "Software Engineer", "Aug 2018 – Apr 2019",
            ["Built a ticketing system and an integrated CRM module with SMTP email dispatch using <b>PHP</b>, JavaScript, and Git."],
        )],
    ),
    (
        "r_keeper",
        "Baku, Azerbaijan · Remote · Part-time",
        [(
            "Software Engineer", "Sep 2017 – Jun 2018",
            ["Developed a <b>C# / .NET Core</b> API for financial data transfer between POS and bonus systems, ensuring transactional consistency across cash and bonus operations."],
        )],
    ),
]

PROJECTS = [
    (
        "Erebus",
        [("https://elkhan-isayev.github.io/erebus/", "elkhan-isayev.github.io/erebus")],
        "Open-source Electron desktop client for Apache Kafka and RabbitMQ: live tailing at 1,000+ msg/s, "
        "Avro/Protobuf decoding, Schema Registry, consumer-group lag, and ksqlDB, plus an MCP server whose "
        "51 tools let coding agents drive brokers.",
    ),
    (
        "Hubpoint.AI",
        [("https://hubpoint.ai", "hubpoint.ai")],
        "AI-powered appointment scheduling and business management platform with native iOS and Android apps, "
        "Firebase push notifications, and Stripe payments.",
    ),
    (
        "AzPulse",
        [("https://elkhan-isayev.github.io/azpulse/", "elkhan-isayev.github.io/azpulse")],
        "Live dashboard over Azerbaijan's open data (opendata.az), surfacing real-time country and "
        "market-demand signals.",
    ),
    (
        "CS 1.6 Web",
        [("https://github.com/Elkhan-Isayev/cs16-web", "github.com/Elkhan-Isayev/cs16-web")],
        "Counter-Strike 1.6 in the browser over LAN from one Docker container, built with WebRTC and Xash3D WASM.",
    ),
]

CERTS = [
    (
        "Advanced Backend &amp; Microservice Development — Ingress Academy", "May 2024",
        "Certificate of Achievement covering Java, microservices, and related backend engineering practices.",
    ),
    (
        "ACM ICPC Semifinal — International Collegiate Programming Contest", "Dec 2018",
        "Finished 4th with team BSU-1 at the 2018 Azerbaijan Subregional Contest.",
    ),
]

# ------------------------------------------------- machine-readable keyword layer
#
# Off. When enabled, the terms below are drawn in PDF text render mode 3
# (invisible): resume parsers read them, on-screen and printed pages do not show
# them. Left here as an opt-in switch only -- shipping a CV with text hidden from
# the reader is a trick recruiters and modern ATS both flag, so it stays off.
# Every term is a synonym or spelling variant of something the CV body already
# evidences; nothing here claims experience that is not stated above.

ATS_KEYWORD_LAYER = False

ATS_KEYWORDS = [
    "Senior Software Engineer, Senior Backend Engineer, Backend Developer, Golang Developer, Java Developer, "
    "Software Development Engineer, Technical Lead, Tech Lead, Team Lead, Full Stack Developer",
    "Go, Golang, Java, Spring, Spring Boot, PHP, Laravel, C#, .NET, .NET Core, TypeScript, JavaScript, Node.js, "
    "Angular, React, React.js, Electron, SQL, PL/SQL, Oracle Database",
    "Apache Kafka, Kafka Connect, Schema Registry, Avro, Protobuf, ksqlDB, RabbitMQ, AMQP, message broker, Redis, "
    "Elasticsearch, Docker, Kubernetes, K8s, CI/CD, Camunda, BPMN, Git, Linux",
    "Microservices, distributed systems, event-driven architecture, system design, software architecture, "
    "high-load systems, scalability, REST API, API design, backend development, observability, monitoring, "
    "alerting, SDLC, technical leadership, cross-functional teams, mentoring, open source",
    "Fintech, banking, mobile banking, payments, cross-border payments, Stripe, CRM, call center, data warehouse, "
    "Firebase, App Store Connect, Google Play Console, iOS, Android",
]

PDF_KEYWORDS = (
    "Senior Software Engineer, Backend Engineer, Technical Lead, Go, Golang, Java, Spring Boot, PHP, C#, .NET Core, "
    "TypeScript, Node.js, React, Angular, Electron, Apache Kafka, RabbitMQ, Redis, Elasticsearch, Oracle, PL/SQL, "
    "Docker, Kubernetes, CI/CD, Camunda, microservices, distributed systems, event-driven architecture, high-load, "
    "system design, REST API, observability, SDLC, fintech, banking, payments, Claude Code, Cursor, "
    "GitHub Copilot, agentic coding, AI-assisted development, Model Context Protocol, MCP server, "
    "multi-agent workflows, coding agents"
)


def draw_page(canvas, doc):
    """Optional invisible keyword layer; disabled by default."""
    if not ATS_KEYWORD_LAYER:
        return
    canvas.saveState()
    t = canvas.beginText(MARGIN_X, 8)
    t.setTextRenderMode(3)  # neither filled nor stroked: parseable, not visible
    t.setFont("Helvetica", 1)
    t.setLeading(1.2)
    for line in ATS_KEYWORDS:
        t.textLine(line)
    canvas.drawText(t)
    canvas.restoreState()


# --------------------------------------------------------------------- build


def story():
    s = [
        Paragraph("ELKHAN ISAYEV", S_NAME),
        Paragraph("Senior Software Engineer", S_HEADLINE),
        Paragraph(
            "Baku, Azerbaijan &nbsp;|&nbsp; %s &nbsp;|&nbsp; %s<br/>%s &nbsp;|&nbsp; %s"
            % (
                link("tel:+994505883149", "+994 50 588 31 49"),
                link("mailto:is.elxan@gmail.com", "is.elxan@gmail.com"),
                link("https://www.linkedin.com/in/elkhanisayev", "linkedin.com/in/elkhanisayev"),
                link("https://github.com/Elkhan-Isayev", "github.com/Elkhan-Isayev"),
            ),
            S_CONTACT,
        ),
        Spacer(1, 4),
        Rule(1.2, ACCENT, above=1.2, below=2),
    ]

    s += section("PROFESSIONAL SUMMARY")
    s.append(Paragraph(SUMMARY, S_SUMMARY))

    s += section("TECHNICAL SKILLS")
    for i, (label, value) in enumerate(SKILLS):
        s.append(Paragraph("<b>%s:</b> %s" % (label, value), S_SKILL_FIRST if i == 0 else S_SKILL))

    s += section("PROFESSIONAL EXPERIENCE")
    for i, (company, meta, roles) in enumerate(JOBS):
        if i:
            s += separator()
        s += job(company, meta, roles)

    s += section("SELECTED PROJECTS")
    for name, links, desc in PROJECTS:
        urls = " &nbsp;·&nbsp; ".join(link(u, lbl) for u, lbl in links)
        s.append(Paragraph("%s &nbsp;—&nbsp; %s" % (name, urls), S_PROJECT))
        s.append(Paragraph(desc, S_PROJECT_DESC))

    s += section("EDUCATION")
    s.append(Paragraph("Baku State University", S_COMPANY))
    s.append(Paragraph("Baku, Azerbaijan", S_META))
    s.append(role("B.Sc. in Applied Mathematics and Computer Science", "2016 – 2020", short=True))

    s += section("CERTIFICATIONS, HONORS &amp; AWARDS")
    for i, (title, date, desc) in enumerate(CERTS):
        if i:
            s.append(Spacer(1, 7))
        s.append(role(title, date, short=True))
        s.append(Paragraph(desc, S_ENTRY_DESC))

    s += section("LANGUAGES")
    s.append(
        Paragraph(
            "<b>Native / Bilingual:</b> English, Azerbaijani, Russian, Turkish &nbsp;|&nbsp; "
            "<b>German:</b> Limited Working Proficiency",
            S_LANG,
        )
    )
    return s


def build():
    doc = BaseDocTemplate(
        OUT,
        pagesize=A4,
        leftMargin=MARGIN_X,
        rightMargin=MARGIN_X,
        topMargin=MARGIN_Y,
        bottomMargin=MARGIN_Y,
        title="Elkhan Isayev - CV",
        author="Elkhan Isayev",
        subject="Senior Software Engineer - agentic coding workflows, MCP tooling, Go/Java backend, high-load systems",
        keywords=PDF_KEYWORDS,
    )
    frame = Frame(
        MARGIN_X, MARGIN_Y, CONTENT_W, PAGE_H - 2 * MARGIN_Y,
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    doc.addPageTemplates([PageTemplate(id="cv", frames=[frame], onPage=draw_page)])
    doc.build(story())
    print("wrote %s (%d pages)" % (OUT, doc.page))


if __name__ == "__main__":
    build()
