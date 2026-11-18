import re

PROGRAMMER = "Программист, разработчик"
MOBILE = re.compile(
    r"android|ios|mobile|мобильн|flutter|swift|kotlin|react native",
    re.IGNORECASE,
)
REQUIRED_COLUMNS = {
    "vacancy_id", "role", "name", "key_skills", "salary_from", "currency", "gross"
}

INVISIBLE = re.compile("[\u200b\u200c\u200d\u2060\ufeff]")
SPACES = re.compile(r"\s+")
EDGES = re.compile("^[ *•-]+|[ .,;:]+$")

def is_mobile(row):
    return row["role"] == PROGRAMMER and MOBILE.search(row["name"] or "") is not None

def parse_skills(row):
    skills = set()

    for raw_skill in (row["key_skills"] or "").split(";"):
        skill = normalize(raw_skill)
        if skill:
            skills.add(skill)

    return skills

def normalize(skill):
    skill = INVISIBLE.sub("", skill)
    skill = SPACES.sub(" ", skill)
    skill = EDGES.sub("", skill)

    return skill.lower().replace("|", "/")