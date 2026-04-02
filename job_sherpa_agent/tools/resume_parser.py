"""
Tool 1: resume_parser.py
Reads PDF uploaded via ADK UI using artifact system.
"""

import re
import io
from typing import Any
import pymupdf
from google.adk.tools import ToolContext


async def parse_resume(tool_context: ToolContext) -> dict[str, Any]:
    """
    Parse a PDF resume uploaded by the user in the chat UI.
    Call this tool immediately when the user uploads any file or PDF.

    Returns:
        Dictionary with extracted text, links found, and page count.
    """
    try:
        # List all artifacts in current session
        artifacts = await tool_context.list_artifacts()
        print(f"[parse_resume] All artifacts: {artifacts}")

        if not artifacts:
            return {
                "text": "",
                "links": [],
                "pages": 0,
                "error": "No file found in session. Please upload your PDF resume.",
            }

        # Try each artifact until we find one that is a PDF
        for artifact_name in artifacts:
            print(f"[parse_resume] Trying artifact: {artifact_name}")
            try:
                artifact = await tool_context.load_artifact(artifact_name)

                if artifact is None:
                    print(f"[parse_resume] Artifact {artifact_name} is None")
                    continue

                # Get bytes — handle both inline_data and text parts
                pdf_bytes = None
                mime = ""

                if hasattr(artifact, "inline_data") and artifact.inline_data:
                    mime = artifact.inline_data.mime_type or ""
                    pdf_bytes = artifact.inline_data.data
                    print(f"[parse_resume] mime={mime}, bytes_len={len(pdf_bytes) if pdf_bytes else 0}")

                # Accept if mime is pdf OR if name ends with .pdf OR just try anyway
                is_pdf = (
                    "pdf" in mime.lower()
                    or artifact_name.lower().endswith(".pdf")
                    or True  # try all artifacts as fallback
                )

                if pdf_bytes and is_pdf:
                    # Try to open with PyMuPDF
                    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
                    full_text = ""
                    links = set()

                    for page in doc:
                        full_text += page.get_text()
                        for link in page.get_links():
                            uri = link.get("uri", "")
                            if uri and uri.startswith("http"):
                                links.add(uri.strip())

                    doc.close()

                    if not full_text.strip():
                        print(f"[parse_resume] Empty text from {artifact_name}")
                        continue

                    # Extract URLs from text
                    url_pattern = re.compile(r'https?://[^\s\)\]\>\"\'\,]+')
                    for url in url_pattern.findall(full_text):
                        links.add(url.strip())

                    # Catch profile patterns without http
                    profile_patterns = [
                        r'github\.com/[\w\-]+(?:/[\w\-\.]+)*',
                        r'linkedin\.com/in/[\w\-]+',
                        r'leetcode\.com/[\w\-]+',
                        r'kaggle\.com/[\w\-]+',
                    ]
                    for pattern in profile_patterns:
                        for match in re.findall(pattern, full_text, re.IGNORECASE):
                            if not match.startswith("http"):
                                links.add(f"https://{match}")

                    print(f"[parse_resume] Success! Extracted {len(full_text)} chars, {len(links)} links")

                    return {
                        "text": full_text.strip(),
                        "links": list(links),
                        "pages": len(doc.pages) if not doc.is_closed else 0,
                        "error": None,
                    }

            except Exception as e:
                print(f"[parse_resume] Failed on {artifact_name}: {e}")
                continue

        return {
            "text": "",
            "links": [],
            "pages": 0,
            "error": f"Could not parse any uploaded file. Artifacts found: {artifacts}",
        }

    except Exception as e:
        return {
            "text": "",
            "links": [],
            "pages": 0,
            "error": f"Tool error: {str(e)}",
        }