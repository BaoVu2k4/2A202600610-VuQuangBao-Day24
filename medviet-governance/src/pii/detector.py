# src/pii/detector.py
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.predefined_recognizers import EmailRecognizer

# Common Vietnamese surnames for pattern-based person recognition
# Bao gồm toàn bộ họ trong Faker("vi_VN") và các họ phổ biến
VN_SURNAMES = [
    "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Phan", "Vũ", "Võ",
    "Đặng", "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý", "Lưu", "Đinh",
    "Trịnh", "Trương", "Quách", "Tô", "Cao", "Mai", "Tạ", "Thiều",
    "Lã", "Châu", "La", "Lâm", "Vương", "Thái", "Tống", "Mã", "Diệp",
    "Đào", "Tăng", "Liêu", "Trì", "Tôn", "Hàn", "Khổng", "Dư",
    # Họ từ Faker vi_VN
    "Chu", "Hà", "Kiều", "Phùng", "Hứa", "Tiền", "Giang"
]


def build_vietnamese_analyzer() -> AnalyzerEngine:
    """Build AnalyzerEngine với các recognizer tùy chỉnh cho tiếng Việt."""

    # TASK 2.2.1: CCCD recognizer — số CCCD VN có đúng 12 chữ số
    cccd_pattern = Pattern(
        name="cccd_pattern",
        regex=r"\b\d{12}\b",
        score=0.9
    )
    cccd_recognizer = PatternRecognizer(
        supported_entity="VN_CCCD",
        supported_language="vi",
        patterns=[cccd_pattern],
        context=["cccd", "căn cước", "chứng minh", "cmnd"]
    )

    # TASK 2.2.2: Phone recognizer — 0[3|5|7|8|9]xxxxxxxx
    phone_recognizer = PatternRecognizer(
        supported_entity="VN_PHONE",
        supported_language="vi",
        patterns=[Pattern(
            name="vn_phone",
            regex=r"\b0[35789]\d{8}\b",
            score=0.85
        )],
        context=["điện thoại", "sdt", "phone", "liên hệ"]
    )

    # Vietnamese person name recognizer dựa trên danh sách họ phổ biến
    # Faker("vi_VN") tạo tên theo 2 thứ tự: họ-đầu (truyền thống) VÀ họ-cuối (phương Tây)
    # Cũng thêm title: "Ông", "Bà", "Cô", "Bác", "Quý ông"
    _VN_CHARS = (
        "A-ZĐa-zđ"
        "ÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬ"
        "áàảãạăắằẳẵặâấầẩẫậ"
        "ÉÈẺẼẸÊẾỀỂỄỆéèẻẽẹêếềểễệ"
        "ÍÌỈĨỊíìỉĩị"
        "ÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢóòỏõọôốồổỗộơớờởỡợ"
        "ÚÙỦŨỤƯỨỪỬỮỰúùủũụưứừửữự"
        "ÝỲỶỸỴýỳỷỹỵ"
    )
    _WORD = rf"[{_VN_CHARS}]+"
    surnames_pattern = "|".join(VN_SURNAMES)
    _TITLES = r"(?:Quý ông|Quý bà|Ông|Bà|Cô|Bác|Anh|Chị|Em)\s+"

    # Pattern 1: Họ trước (truyền thống): "Nguyễn Văn An"
    p1 = rf"(?:{surnames_pattern})(?:\s+{_WORD}){{1,3}}"
    # Pattern 2: Họ sau (phương Tây, Faker hay dùng): "Bảo Lê", "Tùng Nguyễn", "Hương Mai"
    p2 = rf"(?:{_TITLES})?{_WORD}(?:\s+{_WORD}){{0,2}}\s+(?:{surnames_pattern})"
    vn_name_regex = rf"(?:{p1}|{p2})"
    vn_person_recognizer = PatternRecognizer(
        supported_entity="PERSON",
        supported_language="vi",
        patterns=[Pattern(name="vn_person_pattern", regex=vn_name_regex, score=0.8)]
    )

    # Email recognizer cho tiếng Việt
    email_recognizer = EmailRecognizer(supported_language="vi")

    # TASK 2.2.3: NLP engine — thử vi_core_news_lg, fallback về đa ngôn ngữ
    import spacy as _spacy

    nlp_engine = None
    for model_name in ["vi_core_news_lg", "xx_ent_wiki_sm", "en_core_web_sm"]:
        # Chỉ thử nếu model đã được cài sẵn (tránh sys.exit từ spaCy download)
        if not _spacy.util.is_package(model_name):
            continue
        try:
            provider = NlpEngineProvider(nlp_configuration={
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "vi", "model_name": model_name}]
            })
            nlp_engine = provider.create_engine()
            break
        except BaseException:
            continue

    if nlp_engine is None:
        raise RuntimeError("Không tìm được spaCy model. Chạy: python -m spacy download en_core_web_sm")

    # TASK 2.2.4: Khởi tạo AnalyzerEngine và add các recognizer
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine, supported_languages=["vi"])
    analyzer.registry.add_recognizer(cccd_recognizer)
    analyzer.registry.add_recognizer(phone_recognizer)
    analyzer.registry.add_recognizer(vn_person_recognizer)
    analyzer.registry.add_recognizer(email_recognizer)

    return analyzer


def detect_pii(text: str, analyzer: AnalyzerEngine) -> list:
    """Detect PII trong text tiếng Việt. Trả về list RecognizerResult."""
    results = analyzer.analyze(
        text=text,
        language="vi",
        entities=["PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"]
    )
    return results
