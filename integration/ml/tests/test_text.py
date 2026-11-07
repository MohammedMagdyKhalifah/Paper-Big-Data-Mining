from ml.src.text import exclusion_reason, mask_pii, p0, p1


def test_negation_kept():
    for neg in ["لا", "ما", "مش", "مو", "ليس", "مافي"]:
        assert neg in p1(f"التطبيق {neg} يفتح عندي").split()


def test_pii_masked():
    t = "رقمي 0551234567 وهويتي 1098765432 وايميلي a.b@x.com https://x.sa/y @ali"
    out = mask_pii(p0(t))
    for leak in ["0551234567", "1098765432", "a.b@x.com", "https://x.sa", "@ali"]:
        assert leak not in out
    assert "[PHONE]" in out and "[NUM]" in out and "[EMAIL]" in out and "[URL]" in out


def test_arabic_indic_phone_masked():
    assert "[PHONE]" in p0("جوالي ٠٥٥١٢٣٤٥٦٧")


def test_p1_normalization():
    assert p1("أحمد إلى آخر") == "احمد الي اخر"
    assert p1("مستشفى") == "مستشفي"
    assert p1("الخدمة") == "الخدمه"
    assert p1("بطيييييء جداااا") == "بطيء جدا"
    assert p1("مـــرحبا") == "مرحبا"
    assert p1("تَطْبِيق") == "تطبيق"


def test_exclusion():
    assert exclusion_reason("") == "empty"
    assert exclusion_reason("😡😡😡") == "no_letters_emoji_only"
    assert exclusion_reason("very bad app really") == "not_predominantly_arabic"
    assert exclusion_reason("سيء") == "too_short"
    assert exclusion_reason("التطبيق ما يفتح") is None
