"""Tiện ích PII cho lab — hỗ trợ model tiếng Việt cộng đồng hoặc fallback."""

from __future__ import annotations

from pathlib import Path

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider

VI_MODEL_CANDIDATES = ("vi_spacy_model", "vi_core_news_lg")
VI_MODEL_INSTALL_URL = (
    "https://gitlab.com/trungtv/vi_spacy/-/raw/master/packages/"
    "vi_core_news_lg-3.6.0/dist/vi_core_news_lg-3.6.0.tar.gz"
)
VI_LANGUAGE = "vi"
SUPPORTED_ENTITIES = ["PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"]


def _cccd_recognizer() -> PatternRecognizer:
    return PatternRecognizer(
        supported_entity="VN_CCCD",
        supported_language=VI_LANGUAGE,
        patterns=[Pattern(name="cccd_pattern", regex=r"\b\d{12}\b", score=0.9)],
        context=["cccd", "căn cước", "chứng minh", "cmnd"],
    )


def _phone_recognizer() -> PatternRecognizer:
    return PatternRecognizer(
        supported_entity="VN_PHONE",
        supported_language=VI_LANGUAGE,
        patterns=[Pattern(name="vn_phone", regex=r"\b0[35789]\d{8}\b", score=0.85)],
        context=["điện thoại", "sdt", "phone", "liên hệ"],
    )


def _email_recognizer() -> PatternRecognizer:
    return PatternRecognizer(
        supported_entity="EMAIL_ADDRESS",
        supported_language=VI_LANGUAGE,
        patterns=[
            Pattern(
                name="email_pattern",
                regex=r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
                score=0.9,
            )
        ],
        context=["email", "mail", "gmail"],
    )


def _person_recognizer() -> PatternRecognizer:
    return PatternRecognizer(
        supported_entity="PERSON",
        supported_language=VI_LANGUAGE,
        patterns=[
            Pattern(
                name="vn_person_latin",
                regex=(
                    r"\b[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]"
                    r"[a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]*"
                    r"(?:\s+[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ"
                    r"a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+){0,3}\b"
                ),
                score=0.65,
            ),
        ],
    )


def _resolve_vi_model_name() -> str:
    import spacy

    for name in VI_MODEL_CANDIDATES:
        try:
            spacy.load(name)
            return name
        except OSError:
            continue
    return ""


def _blank_vi_model_path(cache_dir: Path) -> str:
    import spacy

    blank_path = cache_dir / ".spacy_models" / "vi_blank"
    if not blank_path.exists():
        blank_path.parent.mkdir(parents=True, exist_ok=True)
        spacy.blank("vi").to_disk(blank_path)
    return str(blank_path)


def build_vietnamese_analyzer(cache_dir: Path | None = None) -> AnalyzerEngine:
    """Xây AnalyzerEngine — pattern recognizers dùng supported_language='vi'."""
    cache_dir = cache_dir or Path.cwd()
    model_name = _resolve_vi_model_name()

    if model_name:
        nlp_config = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": VI_LANGUAGE, "model_name": model_name}],
        }
    else:
        nlp_config = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": VI_LANGUAGE, "model_name": _blank_vi_model_path(cache_dir)}],
        }

    nlp_engine = NlpEngineProvider(nlp_configuration=nlp_config).create_engine()
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=[VI_LANGUAGE])

    for recognizer in (
        _cccd_recognizer(),
        _phone_recognizer(),
        _email_recognizer(),
        _person_recognizer(),
    ):
        analyzer.registry.add_recognizer(recognizer)

    return analyzer


def detect_pii(text: str, analyzer: AnalyzerEngine) -> list:
    return analyzer.analyze(
        text=text,
        language=VI_LANGUAGE,
        entities=SUPPORTED_ENTITIES,
    )


def print_model_setup_hint() -> None:
    model_name = _resolve_vi_model_name()
    if model_name:
        print(f"✓ Đã tìm thấy model spaCy: {model_name}")
    else:
        print("⚠ Không tìm thấy model NER tiếng Việt — dùng pattern recognizers (đủ cho lab)")
        print("  (Tùy chọn) Cài model cộng đồng để NER tốt hơn:")
        print("    pip install pyvi")
        print(f"    pip install --no-deps {VI_MODEL_INSTALL_URL}")
