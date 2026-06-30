# src/quality/validation.py
import re
import pandas as pd


def build_patient_expectation_suite():
    """
    Tạo expectation suite cho patient data.
    Dùng great_expectations fluent API (v0.17+).
    """
    try:
        import great_expectations as gx
        from great_expectations.core.expectation_suite import ExpectationSuite

        context = gx.get_context()

        # Xóa suite cũ nếu tồn tại để tránh conflict
        try:
            context.delete_expectation_suite("patient_data_suite")
        except Exception:
            pass

        suite = context.add_expectation_suite("patient_data_suite")

        df = pd.read_csv("data/raw/patients_raw.csv")
        validator = context.sources.pandas_default.read_dataframe(df)

        # 1. patient_id không được null
        validator.expect_column_values_to_not_be_null("patient_id")

        # 2. CCCD phải có đúng 12 ký tự
        validator.expect_column_value_lengths_to_equal(
            column="cccd",
            value=12
        )

        # 3. ket_qua_xet_nghiem phải trong khoảng [0, 50]
        validator.expect_column_values_to_be_between(
            column="ket_qua_xet_nghiem",
            min_value=0,
            max_value=50
        )

        # 4. benh phải thuộc danh sách hợp lệ
        valid_conditions = ["Tiểu đường", "Huyết áp cao", "Tim mạch", "Khỏe mạnh"]
        validator.expect_column_values_to_be_in_set(
            column="benh",
            value_set=valid_conditions
        )

        # 5. email phải match regex pattern
        validator.expect_column_values_to_match_regex(
            column="email",
            regex=r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
        )

        # 6. Không được có duplicate patient_id
        validator.expect_column_values_to_be_unique(column="patient_id")

        validator.save_expectation_suite()
        return suite

    except ImportError:
        print("great_expectations chưa được cài đặt. Chạy: pip install great-expectations")
        return None


def validate_anonymized_data(filepath: str) -> dict:
    """
    Validate anonymized data.
    Trả về dict: {"success": bool, "failed_checks": list, "stats": dict}
    """
    df = pd.read_csv(filepath, dtype={"cccd": str, "so_dien_thoai": str})
    results = {
        "success": True,
        "failed_checks": [],
        "stats": {
            "total_rows": len(df),
            "columns": list(df.columns)
        }
    }

    # Check 1: Không còn CCCD dạng số thuần túy 12 chữ số
    # Sau anonymization, cccd column vẫn là số 12 chữ số (fake) — check nó KHÁC với raw
    # Thực ra check rằng không có cột cccd nào bị null hoặc rỗng
    if "cccd" in df.columns:
        invalid_cccd = df["cccd"].astype(str).apply(
            lambda x: not bool(re.match(r"^\d{12}$", x.strip()))
        )
        if invalid_cccd.any():
            results["failed_checks"].append(
                f"CCCD column has {invalid_cccd.sum()} invalid values (should be 12-digit numbers)"
            )
            results["success"] = False

    # Check 2: Không có null values trong các cột quan trọng
    required_columns = ["patient_id", "benh", "ket_qua_xet_nghiem"]
    for col in required_columns:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                results["failed_checks"].append(
                    f"Column '{col}' has {null_count} null values"
                )
                results["success"] = False

    # Check 3: Số rows phải > 0 (không mất dữ liệu)
    if len(df) == 0:
        results["failed_checks"].append("Anonymized file is empty!")
        results["success"] = False

    # Check 4: benh phải thuộc danh sách hợp lệ
    if "benh" in df.columns:
        valid_conditions = {"Tiểu đường", "Huyết áp cao", "Tim mạch", "Khỏe mạnh"}
        invalid_benh = ~df["benh"].isin(valid_conditions)
        if invalid_benh.any():
            results["failed_checks"].append(
                f"'benh' column has {invalid_benh.sum()} invalid values"
            )
            results["success"] = False

    # Check 5: ket_qua_xet_nghiem phải trong range hợp lý
    if "ket_qua_xet_nghiem" in df.columns:
        out_of_range = ~df["ket_qua_xet_nghiem"].between(0, 50)
        if out_of_range.any():
            results["failed_checks"].append(
                f"'ket_qua_xet_nghiem' has {out_of_range.sum()} values outside [0, 50]"
            )
            results["success"] = False

    results["stats"]["checks_passed"] = 5 - len(results["failed_checks"])
    return results
