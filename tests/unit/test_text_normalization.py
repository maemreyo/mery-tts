from mery_tts.text_normalization import normalize_text_for_locale


def test_normalize_text_for_locale_applies_unicode_punctuation_and_whitespace_rules() -> None:
    result = normalize_text_for_locale('“Xin chào”…\u3000Hẹn—gặp\tlại!', locale='vi-vn')

    assert result.text == '"Xin chào"... Hẹn-gặp lại!'
    assert result.locale == 'vi-VN'
    assert result.normalizer_version == 'core-text-v1'
    assert result.categories_applied == (
        'unicode_nfkc',
        'punctuation_ascii',
        'whitespace_collapse',
        'segmentation',
    )
    assert result.length_before == 24
    assert result.length_after == 26


def test_normalize_text_for_locale_segments_sentences_without_raw_text_diagnostics() -> None:
    result = normalize_text_for_locale('One. Two? Three! Four', locale='en-us', max_segment_chars=8)

    assert result.segments == ('One.', 'Two?', 'Three!', 'Four')
    assert result.diagnostics() == {
        'locale': 'en-US',
        'normalizer_version': 'core-text-v1',
        'categories_applied': 'unicode_nfkc,punctuation_ascii,whitespace_collapse,segmentation',
        'length_before': 21,
        'length_after': 21,
        'segment_count': 4,
        'warnings': '',
    }
    assert 'One' not in str(result.diagnostics())


def test_normalize_text_for_locale_reports_long_segment_warning() -> None:
    result = normalize_text_for_locale(
        'A sentence that is too long.', locale='en-US', max_segment_chars=8
    )

    assert result.segments == ('A sentence that is too long.',)
    assert result.warnings == ('segment_too_long',)
