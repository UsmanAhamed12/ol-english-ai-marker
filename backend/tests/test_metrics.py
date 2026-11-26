"""The metrics must be right, because every number in the report depends on them."""

from evaluation.metrics import (
    accuracy,
    band,
    cer,
    classification_report,
    mae,
    prf1,
    quadratic_weighted_kappa,
    rmse,
    spearman,
    wer,
)


def test_cer_is_zero_for_a_perfect_transcript():
    assert cer("Completing the blanks", "Completing the blanks") == 0


def test_cer_ignores_case_and_extra_spaces():
    assert cer("Completing  the blanks", "completing the blanks") == 0


def test_cer_counts_one_substitution_over_the_reference_length():
    value = cer("abcd", "abce")
    assert round(value, 3) == 0.25


def test_cer_handles_a_deletion_and_an_insertion():
    assert round(cer("abcd", "abc"), 3) == 0.25
    assert round(cer("abcd", "abcde"), 3) == 0.25


def test_wer_is_measured_per_word():
    assert round(wer("the train will leave", "the train will go"), 3) == 0.25


def test_prf1_of_a_perfect_run():
    scores = prf1(tp=10, fp=0, fn=0)
    assert scores["precision"] == scores["recall"] == scores["f1"] == 1.0


def test_prf1_when_everything_is_missed():
    scores = prf1(tp=0, fp=0, fn=5)
    assert scores["precision"] == 0.0
    assert scores["recall"] == 0.0
    assert scores["f1"] == 0.0


def test_classification_report_separates_the_bands():
    report = classification_report(["A", "B", "C"], ["A", "C", "C"], ["A", "B", "C"])
    assert report["per_label"]["A"]["precision"] == 1.0
    assert report["per_label"]["B"]["recall"] == 0.0
    assert round(report["micro"]["precision"], 3) == round(2 / 3, 3)


def test_mae_and_rmse_on_known_values():
    assert mae([10, 20], [12, 18]) == 2
    assert round(rmse([10, 20], [12, 18]), 3) == 2


def test_qwk_is_one_for_identical_marks():
    assert quadratic_weighted_kappa([80, 60, 40], [80, 60, 40]) == 1.0


def test_qwk_punishes_a_large_miss_more_than_a_small_one():
    close = quadratic_weighted_kappa([80, 60, 40, 20], [78, 61, 39, 22])
    far = quadratic_weighted_kappa([80, 60, 40, 20], [60, 40, 20, 5])
    assert close > far


def test_spearman_is_one_for_a_monotonic_relationship():
    assert round(spearman([1, 2, 3, 4], [10, 20, 30, 40]), 6) == 1.0


def test_band_boundaries():
    assert band(75) == "A"
    assert band(74.9) == "B"
    assert band(35) == "S"
    assert band(34.9) == "F"


def test_accuracy_counts_exact_matches():
    assert accuracy(["A", "B", "A"], ["A", "A", "A"]) == 2 / 3