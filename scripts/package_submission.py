import os
import shutil
import zipfile

def package_submission():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    zip_filename = "dealforge_adk.zip"
    zip_path = os.path.join(root_dir, zip_filename)
    submission_zip_path = os.path.join(root_dir, "DealForge_AI_Submission.zip")
    desktop_zip_path = os.path.join(os.path.dirname(root_dir), zip_filename)

    # Directories to exclude from the zip archive
    EXCLUDES = {
        "venv", ".git", ".pytest_cache", "__pycache__", ".DS_Store"
    }

    print(f">> Packaging DealForge AI project into: {zip_path}")
    count = 0
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(root_dir):
            # Modify dirs in-place to avoid descending into excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDES and not d.endswith(".egg-info")]
            
            for file in files:
                # Exclude compiled binaries, bytecode, and any .zip files
                if file.endswith((".pyc", ".pyo", ".pyd", ".zip")):
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, root_dir)
                zipf.write(full_path, rel_path)
                count += 1

    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f">> Successfully packaged {count} files ({size_mb:.2f} MB) into {zip_path}")

    # Duplicate to DealForge_AI_Submission.zip for formal submission requirements
    shutil.copy2(zip_path, submission_zip_path)
    print(f">> Copied to submission archive: {submission_zip_path}")

    # Also place on Desktop for immediate 1-click access
    try:
        shutil.copy2(zip_path, desktop_zip_path)
        print(f">> Copied to Desktop: {desktop_zip_path}")
    except Exception as e:
        print(f">> Note: Could not copy to Desktop directly: {e}")

    # Remove temporary root dealforge_adk.zip so root is clean
    if os.path.exists(zip_path) and os.path.exists(submission_zip_path):
        os.remove(zip_path)

    return submission_zip_path

if __name__ == "__main__":
    package_submission()
