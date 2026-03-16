from dataclasses import dataclass


@dataclass(frozen=True)
class TaggedText:
    text: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class ExperienceRecord:
    company: str
    title: str
    date: str
    bullets: tuple[TaggedText, ...]


@dataclass(frozen=True)
class CandidateProfile:
    name: str
    headline: str
    city: str
    address: str
    phone: str
    email: str
    github: str
    linkedin: str
    languages: tuple[str, ...]
    education: tuple[str, ...]
    experiences: tuple[ExperienceRecord, ...]
    projects: tuple[TaggedText, ...]
    founder_experience: tuple[TaggedText, ...]


PROFILE = CandidateProfile(
    name="Rodrigo Ponce Cortes",
    headline="Mechatronics Engineer | Junior Software Engineer | Product Development",
    city="Heilbronn, Germany",
    address="Dammstr. 5, 74076 Heilbronn",
    phone="+49 15730721287",
    email="rodrigo.ponce@gmx.de",
    github="github.com/rodrag0",
    linkedin="linkedin.com/in/rodrigo-ponce-cortes",
    languages=(
        "German: Advanced",
        "English: Proficient",
        "Spanish: Native",
        "French: Intermediate",
    ),
    education=(
        "B.Eng., Mechatronics Engineering | Universidad de las Americas Puebla | 2019 - 2025",
        "Exchange Year, Mechatronics and Automotive Engineering | Hochschule Heilbronn | Sep 2023 - Aug 2024",
        "Software Engineering Program | 42 Heilbronn | Jun 2024 - Present",
    ),
    experiences=(
        ExperienceRecord(
            company="Lemvos, Augsburg, Germany (Remote)",
            title="Engineering Project Manager",
            date="Jul 2025 - Present",
            bullets=(
                TaggedText(
                    "Coordinate engineering execution across software, hardware, autonomy, and data teams for an unmanned surface vessel program.",
                    ("software", "systems", "ops"),
                ),
                TaggedText(
                    "Translate partner and customer requirements into technical tasks, milestones, and implementation-ready specifications.",
                    ("sales", "systems", "product"),
                ),
                TaggedText(
                    "Support software testing, validation, documentation, and deployment readiness in an R&D-heavy environment.",
                    ("software", "ops", "quality"),
                ),
                TaggedText(
                    "Build internal Python automation for data handling and workflow efficiency.",
                    ("software", "ai", "automation"),
                ),
                TaggedText(
                    "Contributed to securing more than EUR300k in grant and tender funding while supporting early-stage investor outreach.",
                    ("sales", "business", "product"),
                ),
            ),
        ),
        ExperienceRecord(
            company="Green Tech Innovation, Nuevo Leon, Mexico",
            title="Engineering Team Lead",
            date="Jul 2024 - Jun 2025",
            bullets=(
                TaggedText(
                    "Led cross-functional UAV development for wildfire mitigation and search-and-rescue use cases.",
                    ("embedded", "systems", "product"),
                ),
                TaggedText(
                    "Aligned hardware, electronics, and software interfaces for reliable system behavior.",
                    ("embedded", "software", "systems"),
                ),
                TaggedText(
                    "Built Unity simulations for validating operational patterns before physical testing.",
                    ("software", "simulation", "product"),
                ),
                TaggedText(
                    "Contributed Python optimization logic that reduced route runtime from roughly 3 hours to under 5 minutes.",
                    ("software", "ai", "automation"),
                ),
            ),
        ),
        ExperienceRecord(
            company="Universidad de las Americas Puebla, Puebla, Mexico",
            title="Engineering Team Lead (R&D Exoskeleton Project)",
            date="Jan 2025 - Jun 2025",
            bullets=(
                TaggedText(
                    "Designed and iterated mechanical and electronic modules for a lower-limb exoskeleton prototype.",
                    ("embedded", "systems", "product"),
                ),
                TaggedText(
                    "Coordinated multidisciplinary teams and aligned subsystem interfaces, sensors, and test plans.",
                    ("systems", "product", "ops"),
                ),
                TaggedText(
                    "Ran structured prototype tests and turned user feedback into reliability and ergonomics improvements.",
                    ("quality", "product", "ops"),
                ),
            ),
        ),
    ),
    projects=(
        TaggedText(
            "Raspberry Pi and Home IoT Automation: built and maintained Linux-based automation systems with MQTT, ESPHome, Node-RED, and ARM troubleshooting.",
            ("embedded", "ops", "automation"),
        ),
        TaggedText(
            "RoSaPadel Scoreboard: developed an ESP32-based embedded IoT system with sensors, wireless communication, and functional prototypes.",
            ("embedded", "product", "software"),
        ),
        TaggedText(
            "Padelkarte and PadelPilot: launched React and Firebase-based web products for tournament discovery, rankings, and operations.",
            ("software", "product", "web"),
        ),
        TaggedText(
            "Traffic Light Recognition System: built Python and OpenCV logic for real-time recognition and stop-go decision making.",
            ("software", "ai", "automation"),
        ),
        TaggedText(
            "Drone Mission Simulation Tools: created Unity environments to validate search patterns, sensor behavior, and mission workflows.",
            ("software", "simulation", "systems"),
        ),
    ),
    founder_experience=(
        TaggedText(
            "Co-founded RoSaPadel and padelkarte.com in Germany, taking digital products from concept to active user-facing platforms.",
            ("product", "business", "startup"),
        ),
        TaggedText(
            "Founded NextElement3D and delivered 3D-printing services to architecture, healthcare, and prototyping clients.",
            ("business", "sales", "startup"),
        ),
        TaggedText(
            "Co-founded BIMO and converted and sold 50 bicycles across three motorized product iterations.",
            ("business", "sales", "product"),
        ),
    ),
)
