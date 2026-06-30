# src/pii/anonymizer.py
import random
import uuid
import pandas as pd
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from faker import Faker
from .detector import build_vietnamese_analyzer, detect_pii

fake = Faker("vi_VN")


def _fake_cccd() -> str:
    """Tạo số CCCD giả 12 chữ số."""
    return "".join([str(random.randint(0, 9)) for _ in range(12)])


def _fake_phone() -> str:
    """Tạo số điện thoại VN giả."""
    return f"0{random.choice([3, 5, 7, 8, 9])}" + "".join(
        [str(random.randint(0, 9)) for _ in range(8)]
    )


class MedVietAnonymizer:

    def __init__(self):
        self.analyzer = build_vietnamese_analyzer()
        self.anonymizer = AnonymizerEngine()

    def anonymize_text(self, text: str, strategy: str = "replace") -> str:
        """
        Anonymize text với strategy được chọn.

        Strategies:
        - "mask"    : che khuất ký tự giữa bằng '*'
        - "replace" : thay bằng fake data (dùng Faker)
        - "hash"    : SHA-256 one-way hash
        """
        results = detect_pii(text, self.analyzer)
        if not results:
            return text

        operators = {}

        if strategy == "replace":
            # Dùng UUID suffix để đảm bảo email fake không trùng với email gốc
            unique_email = f"anon_{uuid.uuid4().hex[:8]}@medviet-anon.vn"
            operators = {
                "PERSON": OperatorConfig("replace", {"new_value": fake.name()}),
                "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": unique_email}),
                "VN_CCCD": OperatorConfig("replace", {"new_value": _fake_cccd()}),
                "VN_PHONE": OperatorConfig("replace", {"new_value": _fake_phone()}),
            }
        elif strategy == "mask":
            operators = {
                "PERSON": OperatorConfig("mask", {
                    "masking_char": "*", "chars_to_mask": 6, "from_end": False
                }),
                "EMAIL_ADDRESS": OperatorConfig("mask", {
                    "masking_char": "*", "chars_to_mask": 5, "from_end": False
                }),
                "VN_CCCD": OperatorConfig("mask", {
                    "masking_char": "*", "chars_to_mask": 8, "from_end": False
                }),
                "VN_PHONE": OperatorConfig("mask", {
                    "masking_char": "*", "chars_to_mask": 5, "from_end": False
                }),
            }
        elif strategy == "hash":
            operators = {
                "PERSON": OperatorConfig("hash", {"hash_type": "sha256"}),
                "EMAIL_ADDRESS": OperatorConfig("hash", {"hash_type": "sha256"}),
                "VN_CCCD": OperatorConfig("hash", {"hash_type": "sha256"}),
                "VN_PHONE": OperatorConfig("hash", {"hash_type": "sha256"}),
            }

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators=operators
        )
        return anonymized.text

    def anonymize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Anonymize toàn bộ DataFrame:
        - ho_ten, dia_chi, email, bac_si_phu_trach: dùng anonymize_text()
        - cccd, so_dien_thoai: replace trực tiếp bằng fake data
        - benh, ket_qua_xet_nghiem: GIỮ NGUYÊN
        - patient_id: GIỮ NGUYÊN
        - ngay_sinh, ngay_kham: GIỮ NGUYÊN (dữ liệu lâm sàng)
        """
        df_anon = df.copy()

        # Cột text: dùng anonymize_text()
        for col in ["ho_ten", "dia_chi", "email"]:
            if col in df_anon.columns:
                df_anon[col] = df_anon[col].astype(str).apply(
                    lambda x: self.anonymize_text(x, strategy="replace")
                )

        # Bác sĩ phụ trách cũng là PII
        if "bac_si_phu_trach" in df_anon.columns:
            df_anon["bac_si_phu_trach"] = df_anon["bac_si_phu_trach"].apply(
                lambda _: fake.name()
            )

        # Cột CCCD và SDT: replace trực tiếp
        if "cccd" in df_anon.columns:
            df_anon["cccd"] = [_fake_cccd() for _ in range(len(df_anon))]

        if "so_dien_thoai" in df_anon.columns:
            df_anon["so_dien_thoai"] = [_fake_phone() for _ in range(len(df_anon))]

        return df_anon

    def calculate_detection_rate(self,
                                  original_df: pd.DataFrame,
                                  pii_columns: list) -> float:
        """
        Tính % PII được detect thành công.
        Mục tiêu: > 95%
        """
        total = 0
        detected = 0

        for col in pii_columns:
            for value in original_df[col].astype(str):
                total += 1
                results = detect_pii(value, self.analyzer)
                if len(results) > 0:
                    detected += 1

        return detected / total if total > 0 else 0.0
