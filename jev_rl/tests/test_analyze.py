import pytest

import analyze


def test_auroc_perfect():
    assert analyze.auroc([0.9, 0.8, 0.2, 0.1], [True, True, False, False]) == 1.0


def test_auroc_ties_half():
    assert analyze.auroc([0.5, 0.5, 0.5, 0.5], [True, False, True, False]) == 0.5


def test_auroc_single_class_none():
    assert analyze.auroc([0.1, 0.2], [True, True]) is None
    assert analyze.auroc([0.1, 0.2], [False, False]) is None


def test_test_split_requires_final(tmp_path):
    with pytest.raises(SystemExit):
        analyze.main(["--split", "test", "--runs", "a"], log_path=tmp_path / "t.log")


def test_test_split_refuses_repeat(tmp_path):
    log = tmp_path / "t.log"
    log.write_text("a\n")
    with pytest.raises(SystemExit):
        analyze.main(["--split", "test", "--runs", "a", "--final"], log_path=log)


def test_auroc_zero_is_not_nan():
    rows = [{"id": str(i), "run": "a", "parseable": True,
             "reward": {"x": s}, "match": {"x": y}}
            for i, (s, y) in enumerate([(0.1, True), (0.2, True), (0.8, False), (0.9, False)])]
    assert analyze._row_auroc(rows, "x") == 0.0
    lo, hi = analyze.cluster_ci(rows, lambda rs: analyze._row_auroc(rs, "x"), n_boot=50)
    assert lo == 0.0 and hi == 0.0


def test_parseable_filter():
    rows = [{"parseable": True, "id": "1"}, {"parseable": False, "id": "2"}]
    assert analyze._parseable(rows) == [rows[0]]


def test_cluster_bootstrap_by_item_id_deterministic():
    rows = []
    for run in "ab":
        for i, (s, y) in enumerate([(0.9, True), (0.8, True), (0.2, False), (0.1, False), (0.5, True), (0.4, False)]):
            rows.append({"id": f"i{i}", "run": run, "parseable": True,
                         "reward": {"x": s}, "match": {"x": y}})
    m = lambda rs: analyze._row_auroc(rs, "x")
    c1 = analyze.cluster_ci(rows, m, n_boot=100, seed=3)
    assert c1 == analyze.cluster_ci(rows, m, n_boot=100, seed=3)
    # resampling ids moves both runs' rows together: replicate sizes are multiples of 2
    seen = []
    analyze.cluster_ci(rows, lambda rs: seen.append(len(rs)) or 0.5, n_boot=20)
    assert all(n % 2 == 0 for n in seen)
