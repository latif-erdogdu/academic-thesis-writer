"""PDF indirme ve Unpaywall OA kontrolü.

source.json URL'sinden PDF indirme, Unpaywall API ile açık erişim kontrolü.
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)


@dataclass
class DownloadResult:
    """PDF indirme sonucu."""
    success: bool
    file_path: Optional[Path] = None
    file_size: int = 0
    content_type: str = ""
    source_url: str = ""
    is_open_access: bool = False
    oa_source: str = ""  # "unpaywall", "direct", "publisher"
    error: str = ""
    download_time_ms: int = 0


@dataclass
class OAStatus:
    """Unpaywall OA durumu."""
    is_oa: bool
    oa_status: str  # "gold", "hybrid", "bronze", "green", "closed"
    oa_url: str = ""
    license: str = ""
    version: str = ""  # "publishedVersion", "acceptedVersion", "submittedVersion"
    source: str = "unpaywall"


class PDFDownloader:
    """PDF indirme ve OA kontrolü."""

    def __init__(
        self,
        download_dir: str | Path = "downloads/pdfs",
        timeout: int = 60,
        max_retries: int = 3,
        user_agent: str = "AcademicThesisWriter/1.0",
        unpaywall_email: str | None = None,
    ):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent,
            "Accept": "application/pdf,*/*",
        })
        self.unpaywall_email = unpaywall_email or os.getenv("UNPAYWALL_EMAIL")

    def download(self, url: str, filename: str | None = None) -> DownloadResult:
        """URL'den PDF indir."""
        start = time.time()

        if not filename:
            parsed = urlparse(url)
            filename = os.path.basename(parsed.path) or "document.pdf"
            if not filename.endswith(".pdf"):
                filename += ".pdf"

        file_path = self.download_dir / filename

        # Dosya zaten varsa atla
        if file_path.exists():
            return DownloadResult(
                success=True,
                file_path=file_path,
                file_size=file_path.stat().st_size,
                source_url=url,
                download_time_ms=int((time.time() - start) * 1000),
            )

        for attempt in range(self.max_retries):
            try:
                response = self.session.get(
                    url,
                    timeout=self.timeout,
                    stream=True,
                    headers={"Accept": "application/pdf,*/*"},
                )
                response.raise_for_status()

                content_type = response.headers.get("Content-Type", "")
                if "pdf" not in content_type.lower() and not url.lower().endswith(".pdf"):
                    logger.warning(f"Content-Type PDF değil: {content_type}")

                # Dosyayı yaz
                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                file_size = file_path.stat().st_size
                elapsed = int((time.time() - start) * 1000)

                return DownloadResult(
                    success=True,
                    file_path=file_path,
                    file_size=file_size,
                    content_type=content_type,
                    source_url=url,
                    download_time_ms=elapsed,
                )

            except requests.RequestException as e:
                logger.warning(f"İndirme denemesi {attempt + 1} başarısız: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return DownloadResult(
                        success=False,
                        source_url=url,
                        error=str(e),
                        download_time_ms=int((time.time() - start) * 1000),
                    )

        return DownloadResult(
            success=False,
            source_url=url,
            error="Max retries exceeded",
            download_time_ms=int((time.time() - start) * 1000),
        )

    def check_unpaywall(self, doi: str) -> Optional[OAStatus]:
        """Unpaywall API ile OA durumu kontrol et."""
        if not doi:
            return None

        try:
            url = f"https://api.unpaywall.org/v2/{doi}"
            params = {"email": self.unpaywall_email} if self.unpaywall_email else {}
            response = requests.get(f"{url}", params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            is_oa = data.get("is_oa", False)
            oa_status = data.get("oa_status", "closed")

            best_oa = data.get("best_oa_location") or {}
            oa_url = best_oa.get("url", "")
            license_ = best_oa.get("license", "")
            version = best_oa.get("version", "")

            return OAStatus(
                is_oa=is_oa,
                oa_status=oa_status,
                oa_url=oa_url,
                license=license_,
                version=version,
                source="unpaywall",
            )

        except requests.RequestException as e:
            logger.warning(f"Unpaywall API hatası ({doi}): {e}")
            return None

    def download_with_oa_check(self, doi: str, source_url: str = "") -> DownloadResult:
        """OA kontrolü yap, varsa OA URL'den indir, yoksa kaynak URL'den."""
        # Önce OA kontrolü
        oa_status = self.check_unpaywall(doi)

        if oa_status and oa_status.is_oa and oa_status.oa_url:
            logger.info(f"OA bulundu ({oa_status.oa_status}): {oa_status.oa_url}")
            result = self.download(oa_status.oa_url)
            if result.success:
                result.is_open_access = True
                result.oa_source = "unpaywall"
                return result

        # OA yoksa veya indirme başarısızsa kaynak URL'yi dene
        if source_url:
            logger.info(f"OA yok/başarısız, kaynak URL deneniyor: {source_url}")
            result = self.download(source_url)
            if result.success:
                result.is_open_access = False
                result.oa_source = "direct"
            return result

        return DownloadResult(
            success=False,
            source_url=source_url,
            error="No valid download URL",
        )

    def download_from_source_record(self, source_record: dict) -> DownloadResult:
        """source.json kaydından PDF indir (DOI + URL + OA kontrolü)."""
        doi = source_record.get("doi", "").strip()
        url = source_record.get("url", "").strip()

        if doi:
            return self.download_with_oa_check(doi, source_url=url)
        elif source_url:
            return self.download(source_url)
        else:
            return DownloadResult(
                success=False,
                source_url=source_url,
                error="Neither DOI nor URL provided",
            )


def download_pdf(url: str, download_dir: str | Path = "downloads/pdfs") -> DownloadResult:
    """Basit PDF indirme fonksiyonu."""
    downloader = PDFDownloader(download_dir=download_dir)
    return downloader.download(url)


def check_unpaywall_oa(doi: str, email: str | None = None) -> Optional[OAStatus]:
    """Unpaywall OA kontrolü basit fonksiyon."""
    downloader = PDFDownloader(unpaywall_email=email)
    return downloader.check_unpaywall(doi)