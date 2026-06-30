# tests/test_pii.py
import pytest
import pandas as pd
from src.pii.anonymizer import MedVietAnonymizer


@pytest.fixture(scope="module")
def anonymizer():
    return MedVietAnonymizer()


@pytest.fixture(scope="module")
def sample_df():
    # Đọc với dtype str cho cccd và phone để giữ nguyên số 0 đầu
    return pd.read_csv(
        "data/raw/patients_raw.csv",
        dtype={"cccd": str, "so_dien_thoai": str}
    ).head(50)


class TestPIIDetection:

    def test_cccd_detected(self, anonymizer):
        text = "Bệnh nhân Nguyen Van A, CCCD: 012345678901"
        results = anonymizer.analyzer.analyze(
            text=text, language="vi", entities=["VN_CCCD"]
        )
        assert len(results) >= 1, "CCCD không được detect"

    def test_phone_detected(self, anonymizer):
        text = "Liên hệ: 0912345678"
        results = anonymizer.analyzer.analyze(
            text=text, language="vi", entities=["VN_PHONE"]
        )
        assert len(results) >= 1, "Số điện thoại không được detect"

    def test_email_detected(self, anonymizer):
        text = "Email: nguyenvana@gmail.com"
        results = anonymizer.analyzer.analyze(
            text=text, language="vi", entities=["EMAIL_ADDRESS"]
        )
        assert len(results) >= 1, "Email không được detect"

    def test_person_detected(self, anonymizer):
        text = "Nguyễn Văn An"
        results = anonymizer.analyzer.analyze(
            text=text, language="vi", entities=["PERSON"]
        )
        assert len(results) >= 1, "Tên người không được detect"

    # --- TASK QUAN TRỌNG ---
    def test_detection_rate_above_95_percent(self, anonymizer, sample_df):
        """Pipeline phải đạt >95% detection rate."""
        pii_columns = ["ho_ten", "cccd", "so_dien_thoai", "email"]
        rate = anonymizer.calculate_detection_rate(sample_df, pii_columns)
        print(f"\nDetection rate: {rate:.2%}")
        assert rate >= 0.95, f"Detection rate {rate:.2%} < 95%"


class TestAnonymization:

    def test_pii_not_in_output(self, anonymizer, sample_df):
        """Sau anonymization, không còn CCCD gốc trong output."""
        df_anon = anonymizer.anonymize_dataframe(sample_df)
        anonymized_cccd_values = df_anon["cccd"].astype(str).tolist()
        for original_cccd in sample_df["cccd"]:
            assert str(original_cccd) not in anonymized_cccd_values, (
                f"CCCD gốc '{original_cccd}' vẫn còn trong output!"
            )

    def test_non_pii_columns_unchanged(self, anonymizer, sample_df):
        """Cột benh và ket_qua_xet_nghiem phải giữ nguyên."""
        df_anon = anonymizer.anonymize_dataframe(sample_df)
        pd.testing.assert_series_equal(
            sample_df["benh"].reset_index(drop=True),
            df_anon["benh"].reset_index(drop=True),
            check_names=False
        )
        pd.testing.assert_series_equal(
            sample_df["ket_qua_xet_nghiem"].reset_index(drop=True),
            df_anon["ket_qua_xet_nghiem"].reset_index(drop=True),
            check_names=False
        )

    def test_patient_id_unchanged(self, anonymizer, sample_df):
        """patient_id phải giữ nguyên."""
        df_anon = anonymizer.anonymize_dataframe(sample_df)
        pd.testing.assert_series_equal(
            sample_df["patient_id"].reset_index(drop=True),
            df_anon["patient_id"].reset_index(drop=True),
            check_names=False
        )

    def test_row_count_preserved(self, anonymizer, sample_df):
        """Số rows phải giữ nguyên sau anonymization."""
        df_anon = anonymizer.anonymize_dataframe(sample_df)
        assert len(df_anon) == len(sample_df)

    def test_email_anonymized(self, anonymizer, sample_df):
        """Email gốc không còn trong cột email sau anonymization."""
        df_anon = anonymizer.anonymize_dataframe(sample_df)
        for original_email in sample_df["email"]:
            assert original_email not in df_anon["email"].tolist(), (
                f"Email gốc '{original_email}' vẫn còn trong output!"
            )
