"""The knowledge base every new studio starts with.

Same four sources the hosted studio shows: paper structure, syllabus competencies,
how answers are marked, and recurring weaknesses. They are written into the
teacher's own knowledge base on first use, chunked and searchable immediately —
no upload, no OCR, no network.
"""

from sqlalchemy.orm import Session

from app.models import KnowledgeSource
from app.rag import retriever as rag

STARTERS: list[dict] = [
    {
        "title": "Paper structure and mark allocation",
        "kind": "Guidance",
        "year": "",
        "content": """O/L English Language paper structure
The paper has sixteen tests and is marked out of 100. Paper I carries Tests 1 to 8 and Paper II carries Tests 9 to 16, and the two parts together make the single score a teacher records.

Closed tests are answered with a letter, a word or a tick, one mark per item unless the paper prints otherwise, and half marks appear in Tests 3 and 11 where items are worth half a mark each. The margin of each test carries a "Q. n Total" box giving that test's full allocation; that printed total, not the number of blanks, is the maximum for the test. Reading the printed totals first is what lets a marker check that the sixteen tests add up to 100.

Open tests are written answers. Test 6 is a short functional writing task such as an announcement, usually forty to fifty words. Test 8 is a short paragraph of about fifty to sixty words. Test 14 is a letter, description or notice of roughly one hundred words. Test 15 is comprehension on a passage. Test 16 is a longer piece - an article, essay, speech or story - of about one hundred and fifty to two hundred words.

Writing is marked on the criteria printed beside it, shown as the letters C L O M: content, language, organisation and mechanics. Content marks come from the points the task asks for; language marks from grammar and vocabulary; organisation from paragraphing and linking; mechanics from spelling, punctuation and capitalisation. Word limits are part of the task: a piece far shorter than the stated length cannot earn full content marks, and a piece far longer usually loses organisation marks.

The first item of many closed tests is printed as a worked example: it is labelled "done for you" and carries no mark, so it must never be counted as the candidate's own answer.""",
    },
    {
        "title": "Syllabus competencies the paper tests",
        "kind": "Syllabus",
        "year": "",
        "content": """Competencies the O/L English paper is built on

Reading for detail and inference. Tests 1, 2, 7, 9, 10, 12, 13 and 15 ask the candidate to find stated information, follow instructions in a notice or advertisement, match headings to paragraphs, and infer meaning that is implied rather than printed. Comprehension answers must be in the candidate's own words where the question asks for explanation, and must answer the question actually asked.

Vocabulary and word formation. Tests 3 and 11 test precise word choice: the correct form of a word in a gap, the correct option to underline, the word that fits the meaning of the sentence. Half marks here reward accuracy, so a near-miss form such as "remembering" for "remember" is wrong.

Grammar and tense control. Correct present perfect for finished actions with present relevance, simple past for finished past actions, subject-verb agreement, articles, prepositions, pronouns and question forms. Grammar is tested directly in the fill-in tests and indirectly in every writing task.

Functional and transactional writing. Writing an announcement, notice or short message that states purpose, place, time and the change being announced. Writing a letter with the correct opening and closing, a clear purpose statement, the required points and an appropriate register.

Creative and argumentative writing. A paragraph, description, article, speech or story with a clear opening, ordered ideas, linking devices and a conclusion - and content that answers every bullet of the task.

Mechanics. Spelling, punctuation, capital letters for names, days, months and sentence starts, and paragraph indentation.

The syllabus rewards communication over imitation: an answer that conveys the meaning with a valid alternative the scheme accepts earns the mark, while a memorised phrase that does not answer the question does not.""",
    },
    {
        "title": "How O/L English answers are marked",
        "kind": "Guidance",
        "year": "",
        "content": """How answers are marked against the scheme

The scheme is the answer key. Every mark awarded or withheld must be traceable to a line in it, never to the marker's own opinion of what the answer should have been. Where the scheme lists more than one accepted answer, any listed answer earns the mark: alternatives joined by "OR" accept either, and answers joined by "AND" require both.

Closed tests are marked item by item. Compare the candidate's item with the key item, count correct items, multiply by the printed value, and check the total against the printed "Q. n Total". The example item printed as "done for you" is not marked. A blank, doubled or clearly wrong answer earns zero. Capital letters do not matter for a word answer; the spelling does. In an underline test the answer matches only if the underlined option equals the key. In a True/False test the tick must sit in the correct column.

Short and long writing is marked against the scheme's content points first, then language, organisation and mechanics. A model answer is not a word-for-word requirement: credit every point the candidate actually made, and do not deduct for wording the scheme would accept. A letter missing its purpose statement, or an announcement missing the time it changes, loses the content marks those points carry. Respect the stated word limit when judging content and organisation.

Marks are never invented and never inflated. If the scheme has no criterion for an item, or the handwriting genuinely cannot be read, the item is flagged for the teacher rather than guessed, and the reason is written down so the mark can be checked later.

Feedback speaks to the candidate: what earned marks, what the scheme asked for and the candidate missed, and how many marks each gap cost. Improvement advice names a technique the candidate can practise, not a vague instruction to "do better".""",
    },
    {
        "title": "Recurring weaknesses and what good feedback says",
        "kind": "Guidance",
        "year": "",
        "content": """Recurring weaknesses in O/L English scripts

Tense control collapses in narrative and letter writing: a piece opens in the past, drifts into the present, then mixes both in one sentence. Verb forms are the single most common source of lost language marks.

Articles and prepositions are dropped or added: "I went to school by bus" becomes "I went to the school by the bus", and "in the morning" becomes "at morning". These errors cluster in the same sentences as tense errors.

Word limits are ignored. An announcement written in fifteen words cannot carry the five required points; an essay of sixty words cannot show organisation. Candidates also answer the topic rather than the bullets, so one required point is silently missing.

Instructions are misread in closed tests: the candidate answers two items out of five, leaves an item doubled, ticks both columns, or writes a word where the paper asks for a letter.

Handwriting and layout cost marks: answers written in margins, corrections left unclearly struck out, no paragraph breaks, and a letter with no address or closing.

What good feedback sounds like
"Your matching items 2 to 5 are correct, but item 6 chose (e) where the key is (c) - check the meaning of 'seldom' again."
"The announcement gives the train name and the delay, but never states the new departure time or the platform, which is 2 of the 5 content marks."
"Your letter has a clear purpose in the first line and a correct closing. The past perfect in paragraph two slips into the present, and that is what cost the language marks."
"Answer every bullet in the task. In Test 16 the last bullet was skipped, so the conclusion had nothing to conclude."

Knowledge gaps name the skill behind the lost marks, not the symptom: "cannot keep one tense across a narrative", "does not distinguish 'a' from 'the' with countable nouns", "stops at stating facts instead of explaining them".""",
    },
]


def ensure(db: Session, user_id: str) -> None:
    """Give a teacher the starter sources once. Safe to call repeatedly."""
    existing = (
        db.query(KnowledgeSource)
        .filter(
            KnowledgeSource.user_id == user_id,
            KnowledgeSource.kind != rag.EXAMPLE_KIND,
        )
        .count()
    )
    if existing:
        return

    for entry in STARTERS:
        source = KnowledgeSource(
            user_id=user_id,
            title=entry["title"],
            kind=entry["kind"],
            year=entry["year"],
            notes="Starter knowledge — edit or replace with your own syllabus.",
            content=entry["content"],
        )
        db.add(source)
        db.commit()
        db.refresh(source)
        rag.index_source(db, source)