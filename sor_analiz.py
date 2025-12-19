#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import otdrparser
except ImportError as e:
    raise SystemExit("Hata: otdrparser kurulu değil. Kur: pip install otdrparser") from e


def load_sor(path: Path) -> Dict[str, Any]:
    """Parse .sor file and return blocks dict (parse2)."""
    with path.open("rb") as fp:
        return otdrparser.parse2(fp)


def auto_distance_factor(blocks: Dict[str, Any]) -> float:
    """
    OTDR dosyalarında bazı alanlar 'round-trip (2-yön)' gibi görünebilir.
    Fiber Trace Viewer genelde 'tek-yön (one-way)' mesafeyi gösterir.

    Heuristik:
      KeyEvents.fiber_length ile max(event.distance_of_travel) oranı ~2 ise -> 0.5 uygula
      Yoksa -> default 0.5 (en sık gereken)
    """
    ke = blocks.get("KeyEvents") or {}
    events = ke.get("events") or []
    fl = ke.get("fiber_length")

    max_ev = max((float(e.get("distance_of_travel") or 0.0) for e in events), default=0.0)

    if fl and max_ev:
        r = max_ev / float(fl)
        if 1.7 < r < 2.3:
            return 0.5
        if 0.85 < r < 1.15:
            return 1.0

    # Çoğu durumda viewer ile aynı mesafeyi görmek için 0.5 gerekir.
    return 0.5


def extract_events_table(
    blocks: Dict[str, Any],
    distance_factor: float,
) -> List[Dict[str, Any]]:
    """
    Viewer'daki tabloya benzer şekilde:
      - distance
      - rel_distance
      - event_loss (splice_loss)
      - slope (dB/km)
      - section_loss = slope * rel_dist_km
      - cumulative_loss = sum(event_loss + section_loss)
      - reflectance (reflection_loss)
    """
    ke = blocks.get("KeyEvents") or {}
    events = ke.get("events") or []

    rows: List[Dict[str, Any]] = []
    prev_dist_m = 0.0
    cum_loss_db = 0.0

    for e in events:
        dist_m = float(e.get("distance_of_travel") or 0.0) * distance_factor
        slope_db_per_km = float(e.get("slope") or 0.0)
        event_loss_db = float(e.get("splice_loss") or 0.0)
        reflectance_db = float(e.get("reflection_loss") or 0.0)

        rel_dist_m = dist_m - prev_dist_m
        if rel_dist_m < 0:
            # bazı dosyalarda sıralama / offset durumları olabilir
            rel_dist_m = 0.0

        section_loss_db = slope_db_per_km * (rel_dist_m / 1000.0)
        cum_loss_db += event_loss_db + section_loss_db

        etd = e.get("event_type_details") or {}
        rows.append(
            {
                "event_number": e.get("event_number"),
                "distance_m": dist_m,
                "rel_distance_m": rel_dist_m,
                "event_loss_db": event_loss_db,
                "slope_db_per_km": slope_db_per_km,
                "section_loss_db": section_loss_db,
                "cumulative_loss_db": cum_loss_db,
                "reflectance_db": reflectance_db,
                "event_type": e.get("event_type"),
                "event": etd.get("event"),
                "note": etd.get("note"),
                "comment": e.get("comment") or "",
            }
        )

        prev_dist_m = dist_m

    return rows


def summarize(blocks: Dict[str, Any], rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Uzunluk ve loss özetini çıkar.
    - fiber_length_m: event'lerdeki maksimum distance
    - total_loss_db: KeyEvents.total_loss varsa onu al, yoksa son cumulative_loss
    """
    ke = blocks.get("KeyEvents") or {}

    fiber_length_m = 0.0
    if rows:
        fiber_length_m = max(float(r["distance_m"]) for r in rows)

    total_loss_db = ke.get("total_loss")
    if total_loss_db is None:
        total_loss_db = float(rows[-1]["cumulative_loss_db"]) if rows else 0.0
    else:
        total_loss_db = float(total_loss_db)

    fiber_length_km = fiber_length_m / 1000.0
    avg_att_db_per_km = (total_loss_db / fiber_length_km) if fiber_length_km > 0 else None

    return {
        "fiber_length_m": fiber_length_m,
        "fiber_length_km": fiber_length_km,
        "total_loss_db": total_loss_db,
        "avg_att_db_per_km": avg_att_db_per_km,
        "optical_return_loss_db": ke.get("optical_return_loss"),
    }


def write_csv(rows: List[Dict[str, Any]], out_csv: Path) -> None:
    if not rows:
        return
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def plot_trace(blocks: Dict[str, Any], distance_factor: float, out_png: Path) -> None:
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib yok -> plot atlandı (pip install matplotlib)")
        return

    dp = blocks.get("DataPts") or {}
    pts = dp.get("data_points") or []
    if not pts:
        print("DataPts yok -> plot atlandı")
        return

    xs = [float(p[0]) * distance_factor for p in pts]
    ys = [float(p[1]) for p in pts]

    out_png.parent.mkdir(parents=True, exist_ok=True)

    plt.figure()
    plt.plot(xs, ys)
    plt.xlabel("Mesafe (m)")
    plt.ylabel("Seviye (dBm)")
    plt.title("OTDR Trace")
    plt.grid(True, which="both")
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()


def main() -> None:
    ap = argparse.ArgumentParser(description="SOR (.sor) dosyasından loss (dB) ve uzunluk analizi")
    ap.add_argument("sor_file", type=Path, help="Örn: 1.sor")
    ap.add_argument("--distance", choices=["auto", "oneway", "twoway"], default="auto",
                    help="Mesafe ölçeği. Viewer çoğu zaman oneway gösterir.")
    ap.add_argument("--csv", type=Path, default=None, help="Event tablosunu CSV yaz. Örn: events.csv")
    ap.add_argument("--plot", type=Path, default=None, help="Trace grafiğini PNG yaz. Örn: trace.png")
    args = ap.parse_args()

    blocks = load_sor(args.sor_file)

    if args.distance == "twoway":
        factor = 1.0
    elif args.distance == "oneway":
        factor = 0.5
    else:
        factor = auto_distance_factor(blocks)

    rows = extract_events_table(blocks, distance_factor=factor)
    summary = summarize(blocks, rows)

    print(f"\nDosya: {args.sor_file}")
    print(f"Mesafe faktörü: {factor}  (1.0=2-yön, 0.5=tek-yön)")
    print(f"Fiber uzunluğu: {summary['fiber_length_m']:.2f} m  ({summary['fiber_length_km']:.4f} km)")
    print(f"Toplam loss:    {summary['total_loss_db']:.3f} dB")
    if summary["avg_att_db_per_km"] is not None:
        print(f"Ortalama zayıflama: {summary['avg_att_db_per_km']:.3f} dB/km")
    if summary.get("optical_return_loss_db") is not None:
        print(f"ORL: {float(summary['optical_return_loss_db']):.3f} dB")

    # kısa event özeti
    if rows:
        print("\nEvent listesi (ilk 10):")
        for r in rows[:10]:
            print(
                f"  #{r['event_number']}: {r['distance_m']:.2f} m | "
                f"loss={r['event_loss_db']:.3f} dB | "
                f"slope={r['slope_db_per_km']:.3f} dB/km | "
                f"section={r['section_loss_db']:.3f} dB | "
                f"cum={r['cumulative_loss_db']:.3f} dB | "
                f"refl={r['reflectance_db']:.2f} dB"
            )

    if args.csv:
        write_csv(rows, args.csv)
        print(f"\nCSV yazıldı: {args.csv}")

    if args.plot:
        plot_trace(blocks, factor, args.plot)
        print(f"PNG yazıldı: {args.plot}")


if __name__ == "__main__":
    main()
