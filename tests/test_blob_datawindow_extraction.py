#!/usr/bin/env python3
"""Test blob metadata extraction in DataWindow AST."""

from generate.generate_coordinator import extract_datawindow_from_ast


def test_blob_metadata_extraction():






    """Test that blob columns get proper metadata when extracted from AST."""

    # Create a sample DataWindow AST with blob columns
    dw_ast = {
        "node_type": "DataWindow",
        "table": {"name": "employee"},
        "columns": [
                {
                    "name": "employee_id",
                    "type": "integer",
                    "is_primary_key": True,
                },
                {
                    "name": "employee_name", 
                    "type": "string",
                    "length": 50,
                },
                {
                    "name": "profile_photo",
                    "type": "blob",
                    "nullable": True,
                },
                {
                    "name": "resume_pdf",
                    "type": "blob",
                    "nullable": True,
                    "blob_size": "large",
                },
                {
                    "name": "fingerprint_data",
                    "type": "blob",
                    "nullable": True,
                },
            ],
            "retrieve_sql": "SELECT employee_id, employee_name, profile_photo, resume_pdf, fingerprint_data FROM employee",
    }

    # Extract DataWindow info
    result = extract_datawindow_from_ast(dw_ast)

    # Verify basic extraction
    assert result is not None
    print(f"Result keys: {result.keys()}")
    print(f"Table name: {result.get('table_name')}")
    assert result["table_name"] == "employee"
    assert len(result["columns"]) == 5
    assert result["primary_keys"] == ["employee_id"]

    # Find blob columns
    blob_columns = [col for col in result["columns"] if col["type"].lower() == "blob"]
    assert len(blob_columns) == 3

    # Test profile_photo column
    photo_col = next(col for col in result["columns"] if col["name"] == "profile_photo")
    assert photo_col["type"] == "blob"
    assert "blob_metadata" in photo_col
    assert photo_col["blob_metadata"]["usage"] == "image"
    assert photo_col["blob_metadata"]["display_widget"] == "ProfilePhotoBlobDisplay"
    assert photo_col["blob_metadata"]["mime_type"] == "image/jpeg"
    assert photo_col["blob_metadata"]["expected_size"] == "medium"
    print("✓ profile_photo has correct image blob metadata")

    # Test resume_pdf column
    resume_col = next(col for col in result["columns"] if col["name"] == "resume_pdf")
    assert resume_col["type"] == "blob"
    assert "blob_metadata" in resume_col
    assert resume_col["blob_metadata"]["usage"] == "document"
    assert resume_col["blob_metadata"]["display_widget"] == "ResumePdfBlobDisplay"
    assert resume_col["blob_metadata"]["mime_type"] == "application/pdf"
    assert resume_col["blob_metadata"]["expected_size"] == "large"  # From AST
    print("✓ resume_pdf has correct document blob metadata")

    # Test fingerprint_data column
    fingerprint_col = next(col for col in result["columns"] if col["name"] == "fingerprint_data")
    assert fingerprint_col["type"] == "blob"
    assert "blob_metadata" in fingerprint_col
    assert fingerprint_col["blob_metadata"]["usage"] == "data"
    assert fingerprint_col["blob_metadata"]["display_widget"] == "FingerprintDataBlobDisplay"
    assert fingerprint_col["blob_metadata"]["mime_type"] == "application/octet-stream"
    assert fingerprint_col["blob_metadata"]["expected_size"] == "medium"
    print("✓ fingerprint_data has correct generic blob metadata")

    # Test non-blob column doesn't have blob metadata
    name_col = next(col for col in result["columns"] if col["name"] == "employee_name")
    assert "blob_metadata" not in name_col
    print("✓ non-blob columns don't have blob metadata")

    print("\n✅ All blob metadata extraction tests passed!")


def test_blob_usage_detection():






    """Test various column names for blob usage detection."""
    from generate.generate_coordinator import _determine_blob_usage

    # Test image detection
    assert _determine_blob_usage("employee_photo") == "image"
    assert _determine_blob_usage("profile_picture") == "image"
    assert _determine_blob_usage("company_logo") == "image"
    assert _determine_blob_usage("avatar_png") == "image"
    assert _determine_blob_usage("screenshot_2024") == "image"
    print("✓ Image blob detection working")

    # Test document detection  
    assert _determine_blob_usage("contract_pdf") == "document"
    assert _determine_blob_usage("report_attachment") == "document"
    assert _determine_blob_usage("excel_file") == "document"
    assert _determine_blob_usage("word_document") == "document"
    assert _determine_blob_usage("presentation_slides") == "document"
    print("✓ Document blob detection working")

    # Test generic data
    assert _determine_blob_usage("binary_data") == "data"
    assert _determine_blob_usage("encrypted_content") == "data"
    assert _determine_blob_usage("blob_field") == "data"
    print("✓ Generic blob detection working")

    print("\n✅ All blob usage detection tests passed!")


def test_mime_type_guessing():






    """Test MIME type guessing for blob columns."""
    from generate.generate_coordinator import _guess_mime_type

    # Test image MIME types
    assert _guess_mime_type("image", "profile_jpg") == "image/jpeg"
    assert _guess_mime_type("image", "logo_png") == "image/png"
    assert _guess_mime_type("image", "animation_gif") == "image/gif"
    assert _guess_mime_type("image", "bitmap_bmp") == "image/bmp"
    assert _guess_mime_type("image", "employee_photo") == "image/jpeg"  # Default
    print("✓ Image MIME type detection working")

    # Test document MIME types
    assert _guess_mime_type("document", "report_pdf") == "application/pdf"
    assert _guess_mime_type("document", "data_excel") == "application/vnd.ms-excel"
    assert _guess_mime_type("document", "letter_word") == "application/msword"
    assert _guess_mime_type("document", "attachment") == "application/octet-stream"  # Default
    print("✓ Document MIME type detection working")

    # Test generic data MIME type
    assert _guess_mime_type("data", "binary_blob") == "application/octet-stream"
    print("✓ Generic MIME type detection working")

    print("\n✅ All MIME type guessing tests passed!")


if __name__ == "__main__":
    test_blob_metadata_extraction()
    test_blob_usage_detection() 
    test_mime_type_guessing()
