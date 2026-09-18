from evidence_agent.skills import SkillRegistry


def test_peak_richness_question_is_routed():
    registry = SkillRegistry()

    skill = registry.match(
        "What month had the highest observed bird species richness?"
    )

    assert skill is not None
    assert skill.name == "peak_richness"


def test_abundance_question_is_routed():
    registry = SkillRegistry()

    skill = registry.match(
        "What does the dataset show about quantified abundance?"
    )

    assert skill is not None
    assert skill.name == "abundance_summary"


def test_effort_question_is_routed():
    registry = SkillRegistry()

    skill = registry.match(
        "Are there sampling effort differences?"
    )

    assert skill is not None
    assert skill.name == "effort_discrepancy"


def test_unsupported_question_is_not_routed():
    registry = SkillRegistry()

    skill = registry.match(
        "What will bird populations look like in 2050?"
    )

    assert skill is None