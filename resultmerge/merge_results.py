"""Combine extracted application results without opening or parsing PDFs."""

from __future__ import annotations

import re
import unicodedata
from collections import OrderedDict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable

import pandas as pd


DISPLAY_NAME = "Összefűzött"
SOURCE_COLUMN = "Kérelmező"
SECONDARY_COLUMNS = [
    "Blokk",
    "Tábla",
    "Sorszám",
    "Típus",
    "Megnevezés",
    "Anyag",
    "Növény kód",
    "Terület",
]
REPORT_COLUMNS = [
    "Kód",
    "Megnevezés",
    "Terület (Eredeti)",
    "Fővetés (Számított)",
    "Másodvetés (Számított)",
    "Összesen (Számított)",
]
ZERO = Decimal("0")


def merge_processed_results(results: Iterable[dict]) -> dict:
    """Merge two or more successful per-PDF results into one report object.

    The function receives parser outputs already held in memory. It deliberately
    does not deduplicate detail rows: deduplication belongs to the extractors,
    and table numbers are only meaningful within their source application.
    """
    selected = [
        result
        for result in results
        if result.get("success") and not result.get("is_merged")
    ]
    if len(selected) < 2:
        raise ValueError("Az összefűzéshez legalább két sikeresen feldolgozott kérelem szükséges.")

    contributors = []
    main_frames = []
    secondary_rows = []

    for result in selected:
        filename = str(result.get("filename") or "Ismeretlen PDF")
        applicant = result.get("analysis_data", {}).get("applicant_info", {}) or {}
        applicant_name = _clean_label(applicant.get("name"))
        if not applicant_name:
            applicant_name = Path(filename).stem or filename

        contributors.append(
            {
                "name": applicant_name,
                "mak_id": _clean_label(applicant.get("mak_id")) or "N/A",
                "filename": filename,
            }
        )

        main_df = result.get("fovetes_df")
        if main_df is None:
            main_df = pd.DataFrame()
        elif not isinstance(main_df, pd.DataFrame):
            main_df = pd.DataFrame(main_df)
        if not main_df.empty:
            main_df = main_df.copy()
            main_df[SOURCE_COLUMN] = applicant_name
            main_frames.append(main_df)

        for source_row in result.get("masodvetes_list") or []:
            row = list(source_row)
            if len(row) != len(SECONDARY_COLUMNS):
                raise ValueError(
                    f"A(z) {filename} másodvetési/agrotechnikai sora nem a várt "
                    f"{len(SECONDARY_COLUMNS)} mezőt tartalmazza."
                )
            secondary_rows.append(row + [applicant_name])

    if main_frames:
        fovetes_df = pd.concat(main_frames, ignore_index=True, sort=False)
    else:
        fovetes_df = pd.DataFrame(columns=[SOURCE_COLUMN])

    summary_dict = _merge_summary_dict(selected)
    processed_data = {
        "Fővetés": fovetes_df,
        "Másodvetés": secondary_rows,
        "Hasznosítás": summary_dict["hasznositas"],
        "Jogcímek": summary_dict["jogcim"],
        "Blokkok": summary_dict["blokkok"],
    }
    analysis_data = _build_analysis_data(
        fovetes_df=fovetes_df,
        secondary_rows=secondary_rows,
        summary_dict=summary_dict,
        contributors=contributors,
        source_results=selected,
    )

    return {
        "success": True,
        "is_merged": True,
        "filename": DISPLAY_NAME,
        "fovetes_df": fovetes_df,
        "masodvetes_list": secondary_rows,
        "summary_dict": summary_dict,
        "analysis_data": analysis_data,
        "processed_data": processed_data,
        "contributors": contributors,
    }


def _merge_summary_dict(results: list[dict]) -> dict:
    jogcimek: OrderedDict[str, dict] = OrderedDict()
    hasznositas: OrderedDict[str, dict] = OrderedDict()
    blokkok: OrderedDict[str, dict] = OrderedDict()

    for result in results:
        source = result.get("summary_dict", {}) or {}

        for row in source.get("jogcim", []) or []:
            if len(row) < 2:
                continue
            name = _clean_label(row[0])
            if not name:
                continue
            key = _normalize_label(name)
            entry = jogcimek.setdefault(key, {"name": name, "area": ZERO})
            entry["area"] += _to_decimal(row[1])

        for row in source.get("hasznositas", []) or []:
            if len(row) < 3:
                continue
            code = _clean_label(row[0])
            name = _clean_label(row[1])
            if not code and not name:
                continue
            key = _crop_key(code, name)
            entry = hasznositas.setdefault(
                key, {"code": code or "N/A", "name": name or code, "area": ZERO}
            )
            if entry["name"] == entry["code"] and name:
                entry["name"] = name
            entry["area"] += _to_decimal(row[2])

        for row in source.get("blokkok", []) or []:
            if len(row) < 2:
                continue
            block = _clean_label(row[0])
            if not block:
                continue
            key = block.casefold()
            entry = blokkok.setdefault(key, {"block": block, "area": ZERO})
            entry["area"] += _to_decimal(row[1])

    merged_hasznositas = [
        [entry["code"], entry["name"], _format_area(entry["area"])]
        for entry in hasznositas.values()
    ]
    merged_jogcimek = [
        [entry["name"], _format_area(entry["area"])]
        for entry in jogcimek.values()
    ]
    merged_blokkok = [
        [entry["block"], _format_area(entry["area"])]
        for entry in blokkok.values()
    ]

    return {
        "jogcim": merged_jogcimek,
        "hasznositas": merged_hasznositas,
        "hasznositas_total": float(sum((entry["area"] for entry in hasznositas.values()), ZERO)),
        "blokkok": merged_blokkok,
        "blokkok_total": float(sum((entry["area"] for entry in blokkok.values()), ZERO)),
    }


def _build_analysis_data(
    fovetes_df: pd.DataFrame,
    secondary_rows: list[list],
    summary_dict: dict,
    contributors: list[dict],
    source_results: list[dict],
) -> dict:
    report_rows: OrderedDict[tuple[str, str], dict] = OrderedDict()

    def ensure_crop(code: str, name: str) -> dict | None:
        code = _clean_label(code)
        name = _clean_label(name)
        key = _crop_key(code, name)
        if key == ("name", ""):
            return None
        entry = report_rows.setdefault(
            key,
            {
                "Kód": code or "N/A",
                "Megnevezés": name or code,
                "Terület (Eredeti)": ZERO,
                "Fővetés (Számított)": ZERO,
                "Másodvetés (Számított)": ZERO,
            },
        )
        if entry["Megnevezés"] in {"", "N/A", entry["Kód"]} and name:
            entry["Megnevezés"] = name
        if entry["Kód"] == "N/A" and code:
            entry["Kód"] = code
        return entry

    # The original area comes from the application summary table.
    for code, name, area in summary_dict["hasznositas"]:
        entry = ensure_crop(code, name)
        if entry is not None:
            entry["Terület (Eredeti)"] += _to_decimal(area)

    # Recalculate main-crop areas from all detail rows, preserving every row.
    if not fovetes_df.empty:
        for _, row in fovetes_df.iterrows():
            entry = ensure_crop(row.get("Kód"), row.get("Név"))
            if entry is not None:
                entry["Fővetés (Számított)"] += _to_decimal(row.get("Méret (ha)"))

    # Agrotechnika rows remain in the detail sheet but do not count as crop area.
    for row in secondary_rows:
        if len(row) < 8 or _normalize_label(row[3]) != _normalize_label("Másodvetés"):
            continue
        code = row[6]
        name = row[5] if _clean_label(row[5]) else row[4]
        entry = ensure_crop(code, name)
        if entry is not None:
            entry["Másodvetés (Számított)"] += _to_decimal(row[7])

    report_data = []
    for entry in report_rows.values():
        main_area = entry["Fővetés (Számított)"]
        secondary_area = entry["Másodvetés (Számított)"]
        report_data.append(
            {
                **entry,
                "Összesen (Számított)": main_area + secondary_area,
            }
        )

    total_row = {
        "Kód": "",
        "Megnevezés": "Összesen:",
        "Terület (Eredeti)": sum((row["Terület (Eredeti)"] for row in report_data), ZERO),
        "Fővetés (Számított)": sum((row["Fővetés (Számított)"] for row in report_data), ZERO),
        "Másodvetés (Számított)": sum((row["Másodvetés (Számított)"] for row in report_data), ZERO),
        "Összesen (Számított)": sum((row["Összesen (Számított)"] for row in report_data), ZERO),
    }
    summary_df = pd.DataFrame(
        [
            {key: (float(value) if isinstance(value, Decimal) else value) for key, value in row.items()}
            for row in report_data + [total_row]
        ],
        columns=REPORT_COLUMNS,
    )

    support_requests = _merge_unique_text_lists(source_results, "support_requests")
    agrotechnics = _merge_unique_text_lists(source_results, "agrotechnics")

    nitrate_sum = ZERO
    plot_areas = []
    if not fovetes_df.empty:
        for _, row in fovetes_df.iterrows():
            area = _to_decimal(row.get("Méret (ha)"))
            plot_areas.append(area)
            if _normalize_label(row.get("Nitrát")) == _normalize_label("Igen"):
                nitrate_sum += area

    top_five_sum = sum(sorted(plot_areas, reverse=True)[:5], ZERO)
    applicant_info = {
        "name": DISPLAY_NAME,
        "mak_id": "Több kérelmező",
        "support_id": "Több kérelmező",
        "contributors": contributors,
    }
    return {
        "applicant_info": applicant_info,
        "summary_df": summary_df,
        "extra_stats": {
            "nitrate_sum": float(nitrate_sum),
            "top_5_plots_sum": float(top_five_sum),
            "tables_count": len(fovetes_df),
            "agrotechnics": agrotechnics or ["Nincs agrotechnikai művelet."],
            "support_requests": support_requests or ["Nincs támogatási igény kiválasztva."],
        },
    }


def _merge_unique_text_lists(results: list[dict], key: str) -> list[str]:
    unique: OrderedDict[str, str] = OrderedDict()
    for result in results:
        values = (result.get("analysis_data", {}).get("extra_stats", {}) or {}).get(key, []) or []
        for value in values:
            if isinstance(value, dict):
                value = value.get("name") or value.get("label") or str(value)
            text = _clean_label(value)
            if not text or text.casefold().startswith("nincs ") or text.casefold().startswith("nem található"):
                continue
            unique.setdefault(_normalize_label(text), text)
    return list(unique.values())


def _crop_key(code, name) -> tuple[str, str]:
    normalized_code = _normalize_label(code)
    if normalized_code and normalized_code not in {"n/a", "na", "none"}:
        return "code", normalized_code
    return "name", _normalize_label(name)


def _normalize_label(value) -> str:
    text = _clean_label(value)
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text).casefold()
    text = re.sub(r"\s*\+\s*", "+", text)
    return re.sub(r"\s+", " ", text).strip()


def _clean_label(value) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.casefold() in {"", "n/a", "na", "none", "nan"}:
        return ""
    return re.sub(r"\s+", " ", text)


def _to_decimal(value) -> Decimal:
    if value is None:
        return ZERO
    try:
        if pd.isna(value):
            return ZERO
    except (TypeError, ValueError):
        pass
    if isinstance(value, Decimal):
        return value
    raw = str(value).strip().replace("\u00a0", "").replace(" ", "")
    if raw.casefold() in {"", "n/a", "na", "none", "nan", "-"}:
        return ZERO
    if "," in raw and "." in raw and raw.rfind(",") > raw.rfind("."):
        raw = raw.replace(".", "").replace(",", ".")
    else:
        raw = raw.replace(",", ".")
    try:
        return Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(f"Nem értelmezhető területérték: {value!r}") from exc


def _format_area(value: Decimal) -> str:
    return f"{value:.4f}".replace(".", ",")
