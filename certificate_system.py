"""Certificate issuance, PDF rendering and public verification for Daily Brain Challenge."""
from __future__ import annotations

import io
import os
from datetime import datetime
from pathlib import Path

import qrcode
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from database import (
    get_user_certificates,
    get_certificate,
    get_all_certificates,
    revoke_certificate,
)

BASE_DIR = Path(__file__).resolve().parent
SIGNATURE_PATH = BASE_DIR / "assets" / "founder_signature.png"
NAVY = colors.HexColor("#0B1D3A")
GOLD = colors.HexColor("#C49A42")
PALE_GOLD = colors.HexColor("#E8D7A5")


def verification_url(certificate_id: str) -> str:
    """Return the public URL encoded in the QR code.

    Set [app].base_url in Streamlit secrets (or CERTIFICATE_BASE_URL env var)
    to the deployed app URL. Local fallback is useful for local testing only.
    """
    base = os.getenv("CERTIFICATE_BASE_URL", "").strip()
    try:
        if not base:
            config = st.secrets.get("app", {})
            base = str(config.get("base_url", "")).strip()
    except Exception:
        pass
    if not base:
        base = "http://localhost:8501"
    return f"{base.rstrip('/')}?verify={certificate_id}"


def build_certificate_pdf(certificate: dict) -> bytes:
    """Create a landscape navy-and-gold PDF certificate."""
    buffer = io.BytesIO()
    page_w, page_h = landscape(A4)
    pdf = canvas.Canvas(buffer, pagesize=(page_w, page_h))

    # Background and layered ornamental border.
    pdf.setFillColor(colors.HexColor("#FFFEFA"))
    pdf.rect(0, 0, page_w, page_h, fill=1, stroke=0)
    pdf.setStrokeColor(NAVY)
    pdf.setLineWidth(7)
    pdf.rect(15, 15, page_w - 30, page_h - 30, fill=0, stroke=1)
    pdf.setStrokeColor(GOLD)
    pdf.setLineWidth(1.4)
    pdf.rect(24, 24, page_w - 48, page_h - 48, fill=0, stroke=1)
    pdf.setStrokeColor(PALE_GOLD)
    pdf.setLineWidth(0.5)
    pdf.rect(31, 31, page_w - 62, page_h - 62, fill=0, stroke=1)

    # Corner accents.
    pdf.setFillColor(NAVY)
    pdf.saveState()
    path = pdf.beginPath()
    path.moveTo(15, page_h - 15)
    path.lineTo(105, page_h - 15)
    path.lineTo(15, page_h - 105)
    path.close()
    pdf.drawPath(path, fill=1, stroke=0)
    path = pdf.beginPath()
    path.moveTo(page_w - 15, 15)
    path.lineTo(page_w - 105, 15)
    path.lineTo(page_w - 15, 105)
    path.close()
    pdf.drawPath(path, fill=1, stroke=0)
    pdf.restoreState()

    # Header branding.
    pdf.setFillColor(NAVY)
    pdf.setFont("Times-Bold", 17)
    pdf.drawCentredString(page_w / 2, page_h - 66, "DAILY BRAIN CHALLENGE")
    pdf.setFillColor(colors.HexColor("#52647B"))
    pdf.setFont("Helvetica", 8)
    pdf.drawCentredString(page_w / 2, page_h - 81, "LEARN TODAY  |  PRACTICE DAILY  |  ACHIEVE TOMORROW")

    pdf.setFillColor(NAVY)
    pdf.setFont("Times-Bold", 29)
    pdf.drawCentredString(page_w / 2, page_h - 132, "CERTIFICATE OF ACHIEVEMENT")
    pdf.setFillColor(GOLD)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawCentredString(page_w / 2, page_h - 151, "THIS CERTIFICATE IS PROUDLY PRESENTED TO")

    username = str(certificate.get("username", "Student")).replace("\n", " ")[:45]
    pdf.setFillColor(NAVY)
    pdf.setFont("Times-Italic", 30)
    pdf.drawCentredString(page_w / 2, page_h - 195, username)
    pdf.setStrokeColor(GOLD)
    pdf.setLineWidth(0.9)
    pdf.line(page_w * .28, page_h - 204, page_w * .72, page_h - 204)

    pdf.setFillColor(colors.HexColor("#34445B"))
    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(page_w / 2, page_h - 229, "for successfully demonstrating knowledge and skill in")
    subject = str(certificate.get("subject", "Subject Assessment")).replace("\n", " ")[:65]
    pdf.setFillColor(NAVY)
    pdf.setFont("Times-Bold", 21)
    pdf.drawCentredString(page_w / 2, page_h - 260, subject)
    pdf.setFillColor(colors.HexColor("#45546A"))
    pdf.setFont("Helvetica", 9)
    pdf.drawCentredString(page_w / 2, page_h - 279, "This achievement recognizes successful completion of the subject assessment.")

    # Achievement metrics band.
    band_x, band_y, band_w, band_h = page_w * .26, page_h - 342, page_w * .48, 42
    pdf.setFillColor(colors.HexColor("#EEF2F7"))
    pdf.roundRect(band_x, band_y, band_w, band_h, 8, fill=1, stroke=0)
    pdf.setStrokeColor(colors.HexColor("#C6D0DD"))
    pdf.line(band_x + band_w / 3, band_y + 7, band_x + band_w / 3, band_y + band_h - 7)
    pdf.line(band_x + 2 * band_w / 3, band_y + 7, band_x + 2 * band_w / 3, band_y + band_h - 7)
    issued = str(certificate.get("issued_at", ""))[:10]
    try:
        issued = datetime.fromisoformat(issued).strftime("%d %b %Y")
    except Exception:
        pass
    metrics = [
        (band_x + band_w / 6, "CERTIFICATE ID", certificate["certificate_id"]),
        (band_x + band_w / 2, "ISSUE DATE", issued),
        (band_x + 5 * band_w / 6, "SKILL SCORE", f"{float(certificate.get('accuracy', 0)):.0f}%"),
    ]
    for x, label, value in metrics:
        pdf.setFillColor(colors.HexColor("#596A80"))
        pdf.setFont("Helvetica", 7)
        pdf.drawCentredString(x, band_y + 26, label)
        pdf.setFillColor(NAVY)
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawCentredString(x, band_y + 12, value[:27])

    # Verified seal.
    seal_x, seal_y = page_w - 92, page_h - 135
    pdf.setFillColor(GOLD)
    pdf.circle(seal_x, seal_y, 35, fill=1, stroke=0)
    pdf.setFillColor(NAVY)
    pdf.circle(seal_x, seal_y, 29, fill=1, stroke=0)
    pdf.setStrokeColor(PALE_GOLD)
    pdf.setLineWidth(1)
    pdf.circle(seal_x, seal_y, 25, fill=0, stroke=1)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawCentredString(seal_x, seal_y + 5, "VERIFIED")
    pdf.setFont("Helvetica", 6)
    pdf.drawCentredString(seal_x, seal_y - 6, "BY DATABASE")

    # Signatory and actual uploaded handwritten signature.
    sig_x, sig_y = 64, 73
    if SIGNATURE_PATH.exists():
        pdf.drawImage(ImageReader(str(SIGNATURE_PATH)), sig_x, sig_y + 7,
                      width=88, height=47, preserveAspectRatio=True, mask="auto", anchor="c")
    pdf.setStrokeColor(GOLD)
    pdf.line(sig_x, sig_y + 5, sig_x + 150, sig_y + 5)
    pdf.setFillColor(NAVY)
    pdf.setFont("Times-Bold", 11)
    pdf.drawString(sig_x, sig_y - 10, "Ritesh Kumar Singh")
    pdf.setFillColor(colors.HexColor("#52647B"))
    pdf.setFont("Helvetica", 8)
    pdf.drawString(sig_x, sig_y - 22, "Founder & CEO")
    pdf.drawString(sig_x, sig_y - 33, "Daily Brain Challenge")

    # QR code and its verification hint.
    qr = qrcode.QRCode(box_size=5, border=1, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(verification_url(certificate["certificate_id"]))
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#0B1D3A", back_color="white").convert("RGB")
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    pdf.drawImage(ImageReader(qr_buffer), page_w - 112, 53, width=58, height=58, mask="auto")
    pdf.setFillColor(NAVY)
    pdf.setFont("Helvetica", 7)
    pdf.drawCentredString(page_w - 83, 43, "SCAN TO VERIFY")

    pdf.setFillColor(colors.HexColor("#66758A"))
    pdf.setFont("Helvetica", 7)
    pdf.drawCentredString(page_w / 2, 38, "A SKILL ACHIEVEMENT  |  LEARNING NEVER STOPS")
    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def render_my_certificates(user_id: int):
    st.title("🏅 My Certificates")
    st.caption("Your verified subject achievements from Daily Brain Challenge.")
    certificates = get_user_certificates(user_id)
    if not certificates:
        st.info("You have not earned a certificate yet. Complete a 20-question assessment with at least 70% accuracy.")
        return
    for cert in certificates:
        with st.container(border=True):
            left, right = st.columns([3, 1])
            with left:
                st.subheader(cert["subject"])
                st.write(f"Certificate ID: `{cert['certificate_id']}`")
                st.write(f"Score: **{cert['accuracy']:.2f}%**  ·  Questions: **{cert['total_questions']}**")
                st.caption(f"Issued: {cert['issued_at']}  ·  Status: {cert['status'].upper()}")
            with right:
                if cert["status"] == "valid":
                    pdf_bytes = build_certificate_pdf(cert)
                    st.download_button(
                        "⬇️ Download PDF", data=pdf_bytes,
                        file_name=f"{cert['certificate_id']}.pdf",
                        mime="application/pdf", key=f"download_{cert['certificate_id']}",
                        use_container_width=True,
                    )
                else:
                    st.error("Revoked")
                st.link_button("Verify", verification_url(cert["certificate_id"]), use_container_width=True)


def render_certificate_verification(certificate_id: str | None = None):
    st.title("🔎 Certificate Verification")
    st.caption("Verify a Daily Brain Challenge certificate using its unique ID.")
    typed_id = st.text_input("Certificate ID", value=certificate_id or "", placeholder="DBC-PYT-2026-XXXXXX")
    if st.button("Verify Certificate", type="primary"):
        st.session_state["certificate_lookup_id"] = typed_id.strip()
    lookup = st.session_state.get("certificate_lookup_id")
    if lookup:
        cert = get_certificate(lookup)
        if not cert:
            st.error("Certificate not found. This ID is not present in our official records.")
        elif cert["status"] != "valid":
            st.error("This certificate has been REVOKED. It is not currently valid.")
            st.write(f"Certificate ID: `{cert['certificate_id']}`")
        else:
            st.success("✅ VERIFIED — This certificate matches our official database record.")
            c1, c2 = st.columns(2)
            c1.metric("Student", cert["username"])
            c2.metric("Subject", cert["subject"])
            c3, c4, c5 = st.columns(3)
            c3.metric("Score", f"{cert['accuracy']:.2f}%")
            c4.metric("Questions", cert["total_questions"])
            c5.metric("Status", "VALID")
            st.write(f"**Certificate ID:** `{cert['certificate_id']}`")
            st.write(f"**Issue date:** {cert['issued_at']}")
            st.caption("Verification confirms the record stored by Daily Brain Challenge. It is a platform-issued achievement certificate, not a government or university qualification.")


def render_admin_certificates():
    st.subheader("🎓 Certificate Management")
    certificates = get_all_certificates()
    if not certificates:
        st.info("No certificates have been issued yet.")
        return
    import pandas as pd
    st.dataframe(pd.DataFrame(certificates)[[
        "certificate_id", "username", "subject", "accuracy", "total_questions", "issued_at", "status"
    ]], use_container_width=True, hide_index=True)
    valid_ids = [c["certificate_id"] for c in certificates if c["status"] == "valid"]
    if valid_ids:
        selected = st.selectbox("Select certificate to revoke", valid_ids)
        if st.button("Revoke selected certificate", type="secondary"):
            if revoke_certificate(selected):
                st.success(f"Certificate {selected} has been revoked.")
                st.rerun()
            else:
                st.warning("Certificate could not be revoked.")
