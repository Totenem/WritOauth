"""Sample texts for the authorship engine tests.

Two synthetic "personas" with deliberately different writing habits:

* A - long subordinated sentences, semicolons, no contractions, formal
      register, third person.
* B - short sentences, heavy contractions, first/second person, casual.

Every persona text is on a *different topic* from the others, which is the
point: the engine must recognise an author across topics. The previous
embedding-based score could not, because it measured what a text was about.
"""

import pytest

_A_METHODOLOGY = """Although the evidence presented during the inquiry was extensive, the committee remained divided; several members argued that the methodology had been compromised from the outset. It is clear that one of the most persistent difficulties concerns the reliability of the underlying data, which was collected over an unusually short period. Consequently, the recommendations must be treated with a degree of caution by anyone relying upon them.

Furthermore, the report does not adequately address the question of funding. In order to resolve this, the authors propose a supplementary review; however, no timetable has been established. Nevertheless, the general direction of the proposals appears sound, provided that the outstanding questions are answered before implementation begins."""

_A_STATISTICS = """While the initial findings appeared promising, subsequent analysis revealed considerable inconsistencies; the research team acknowledged these openly. It is clear that one of the most significant obstacles remains the absence of a control group, which undermines any causal interpretation of the results. Therefore, the conclusions should be regarded as provisional until further work is completed.

In addition, the statistical treatment raises further concerns. In order to establish confidence, the investigators recommend replication; however, resources have not been allocated. Nonetheless, the underlying approach is defensible, and the authors deserve credit for publishing negative results alongside the positive ones."""

_A_SAMPLING = """Because the sample was drawn from a single institution, the generalisability of the results is limited; the authors concede this point readily. It is clear that one of the most troubling aspects is the reliance on self-reported measures, which are known to be unreliable in this context. Accordingly, the interpretation offered here must remain tentative for the time being.

Moreover, the discussion omits several relevant studies. In order to address this gap, a systematic review would be required; however, such work lies beyond the present scope. Even so, the contribution is worthwhile, and the dataset itself will be valuable to others working in the area."""

# Same author, a topic nowhere near the baselines.
_A_MUSEUMS = """Although the museum's acquisition policy has been revised repeatedly, the underlying tensions persist; curators and trustees continue to disagree. It is clear that one of the most awkward problems concerns provenance, which is frequently incomplete for older holdings. Consequently, any restitution framework must be applied with considerable care by those responsible.

In addition, the funding model constrains what is achievable in practice. In order to broaden access, the trustees propose a digital programme; however, the necessary expertise is scarce. Nevertheless, the ambition is commendable, and the pilot has already attracted interest from several partner institutions abroad.

Because the collection was assembled over two centuries, the documentation is uneven; archivists concede this readily. It is clear that one of the most demanding tasks remains cataloguing, which has been deferred repeatedly for want of staff. Therefore the published timetable should be regarded as optimistic rather than firm. Moreover, the storage facilities are inadequate, although a replacement building has been promised since the last review."""

# Different author, writing about museums too - so a topic-driven score
# would call this a match.
_B_MUSEUMS = """I didn't really get the museum thing at first. It's confusing. They keep changing the rules and nobody tells you why. I think that's a problem. My friend says it's about money. Maybe she's right. I don't know. But it feels like they're not being straight with us.

That's what bugs me the most. You'd think they'd just say it. We went last week and it was packed. I couldn't see anything. My sister loved it though. She's into that stuff. I'd rather stay home honestly. It's not really my thing. But I get why people like it.

We tried again on a Tuesday. Way better. Hardly anyone there. The guy at the desk was nice too. He told us which bits to skip. I wish they'd put that on the website. It'd save everyone a lot of hassle. Anyway, we're going back next month. My mum wants to come. She's never been. I said she'd probably hate it. She said I'm being negative again. Maybe I am."""


@pytest.fixture(scope="session")
def persona_a_baselines() -> list[str]:
    return [_A_METHODOLOGY, _A_STATISTICS, _A_SAMPLING]


@pytest.fixture(scope="session")
def persona_a_heldout() -> str:
    return _A_MUSEUMS


@pytest.fixture(scope="session")
def persona_b_heldout() -> str:
    return _B_MUSEUMS
