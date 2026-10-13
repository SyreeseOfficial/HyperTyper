import os
import tempfile

os.environ["XDG_CONFIG_HOME"] = tempfile.mkdtemp()  # keep tests out of the real ~/.config
import hypertyper as h


def test_combo_tiers():
    assert h.get_combo_tier(2)[:2] == ("", 1.0)
    assert h.get_combo_tier(3)[:2] == ("FLOW STATE", 1.5)
    assert h.get_combo_tier(11)[:2] == ("UNSTOPPABLE", 5.0)
    assert h.get_combo_tier(12)[:2] == ("GOD MODE", 8.0)


def test_wpm():
    assert h.wpm(250, 60) == 50.0   # 250 chars = 50 words in one minute
    assert h.wpm(5, 0) == 60.0      # elapsed is clamped to 1 s


def test_load_words_filters_and_dedupes():
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("Apple\napple\nhi\nit's\nbanana\n\n")
    assert h.load_words(f.name, False) == ["apple", "banana"]   # lowercased, >=3 letters, alpha only, unique
    assert h.load_words(f.name, True) == ["Apple", "apple", "hi", "it's", "banana"]


def test_word_bag_never_repeats_back_to_back():
    bag = h.word_bag(["a", "b", "c"])
    seq = [next(bag) for _ in range(300)]
    assert all(x != y for x, y in zip(seq, seq[1:]))


def test_accent_insensitive():
    assert h.same("albanil", "albañil") and not h.same("albanol", "albañil")


def test_achievements_ignore_practice():
    god = h.ACHIEVEMENTS[0]
    assert h.earned({"best_combo": 12}, god)
    assert not h.earned({"best_combo": 12, "practice": True}, god)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
