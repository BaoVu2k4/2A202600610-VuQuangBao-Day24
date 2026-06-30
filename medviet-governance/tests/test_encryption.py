import pandas as pd

from src.encryption.vault import SimpleVault


def test_vault_encrypt_decrypt_roundtrip(tmp_path):
    vault = SimpleVault(master_key_path=str(tmp_path / ".vault_key"))
    original = "Nguyen Van A - CCCD: 012345678901"

    encrypted = vault.encrypt_data(original)
    decrypted = vault.decrypt_data(encrypted)

    assert encrypted["algorithm"] == "AES-256-GCM"
    assert encrypted["ciphertext"] != original
    assert decrypted == original


def test_encrypt_column_replaces_plaintext_values(tmp_path):
    vault = SimpleVault(master_key_path=str(tmp_path / ".vault_key"))
    df = pd.DataFrame({"cccd": ["012345678901", "987654321098"]})

    encrypted_df = vault.encrypt_column(df, "cccd")

    assert encrypted_df["cccd"].tolist() != df["cccd"].tolist()
    assert "012345678901" not in encrypted_df.to_string()
