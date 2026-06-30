from src.quality.validation import validate_anonymized_data


def test_validate_anonymized_data_passes_for_generated_output():
    result = validate_anonymized_data("data/processed/patients_anonymized.csv")

    assert result["success"] is True
    assert result["failed_checks"] == []
    assert result["stats"]["total_rows"] == 200
