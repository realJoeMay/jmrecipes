"""QR utilities."""

from segno import make_qr


def create(link: str, filepath: str) -> None:
    """Create QR code file."""

    qr_code = make_qr(link)
    qr_code.save(filepath, scale=5, border=0)
