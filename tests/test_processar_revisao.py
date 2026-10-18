import pytest
from datetime import datetime, timedelta

from app import processar_revisao, ProgressoFlashcard

# Helper to allow small time differences
def approx_delta(dt1, dt2, seconds=5):
    return abs((dt1 - dt2).total_seconds()) < seconds

def test_processar_revisao_again():
    prog = ProgressoFlashcard(usuario_id=1, flashcard_id=1)
    before = datetime.utcnow()
    prog = processar_revisao(prog, 'again')
    assert prog.lapses == 1
    assert prog.stability == 0.0
    assert prog.difficulty == 6.0  # default 5 + 1
    assert prog.state == 1
    assert prog.next_review is not None
    assert approx_delta(prog.next_review, before + timedelta(minutes=10))

def test_processar_revisao_hard_new():
    prog = ProgressoFlashcard(usuario_id=1, flashcard_id=1)
    prog.state = 0  # New
    prog = processar_revisao(prog, 'hard')
    assert prog.difficulty == 5.5  # 5 + 0.5
    assert prog.stability == 0.5
    assert prog.state == 0
    assert prog.next_review is not None
    assert approx_delta(prog.next_review, datetime.utcnow() + timedelta(hours=6))

def test_processar_revisao_good_new():
    prog = ProgressoFlashcard(usuario_id=1, flashcard_id=1)
    prog.state = 0
    prog = processar_revisao(prog, 'good')
    assert prog.reps == 1
    assert prog.stability == 1.0
    assert prog.state == 2
    assert prog.next_review is not None
    assert approx_delta(prog.next_review, datetime.utcnow() + timedelta(days=1))

def test_processar_revisao_easy_new():
    prog = ProgressoFlashcard(usuario_id=1, flashcard_id=1)
    prog.state = 0
    prog = processar_revisao(prog, 'easy')
    assert prog.reps == 1
    assert prog.difficulty == 4.5  # 5 - 0.5
    assert prog.stability == 4.0
    assert prog.state == 2
    assert prog.next_review is not None
    assert approx_delta(prog.next_review, datetime.utcnow() + timedelta(days=4))
