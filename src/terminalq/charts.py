"""TerminalQ Charts — pure utility module for terminal-based visualizations.

Every function takes data and returns a formatted string.
No API calls, no caching, no imports from terminalq providers.
"""

from __future__ import annotations

import re

SPARK_CHARS = "▁▂▃▄▅▆▇█"


def sparkline(data: list[float], label: str = "") -> str:
    """Map values to 8 Unicode block characters.

    Handles: all equal -> all ▄, <2 points -> raw value.
    """
    if not data:
        return f"{label} (no data)" if label else "(no data)"

    if len(data) == 1:
        val = f"{data[0]:.2f}"
        return f"{label} {val}" if label else val

    lo, hi = min(data), max(data)

    if lo == hi:
        mid = SPARK_CHARS[len(SPARK_CHARS) // 2]  # ▄
        line = mid * len(data)
    else:
        span = hi - lo
        line = ""
        for v in data:
            idx = int((v - lo) / span * (len(SPARK_CHARS) - 1))
            idx = max(0, min(idx, len(SPARK_CHARS) - 1))
            line += SPARK_CHARS[idx]

    if label:
        return f"{label}  {line}"
    return line


def line_chart(
    data: list[float],
    labels: list[str] | None = None,
    title: str = "",
    height: int = 15,
) -> str:
    """Render an ASCII line chart using asciichartpy.

    Downsamples if len(data) > 60. Prepends title, appends x-axis labels.
    """
    import asciichartpy

    if not data:
        return f"{title}\n(no data)" if title else "(no data)"

    plot_data = _downsample(data, 60) if len(data) > 60 else list(data)
    plot_labels = None
    if labels:
        if len(data) > 60:
            step = max(1, len(labels) // 60)
            plot_labels = labels[::step][: len(plot_data)]
        else:
            plot_labels = list(labels)

    cfg = {"height": height}
    chart = asciichartpy.plot(plot_data, cfg)

    parts: list[str] = []
    if title:
        parts.append(title)
        parts.append("")

    parts.append(chart)

    # Append x-axis labels (first, middle, last)
    if plot_labels and len(plot_labels) >= 2:
        chart_lines = chart.split("\n")
        chart_width = max(len(line) for line in chart_lines) if chart_lines else 60
        # Estimate the padding on the left from the y-axis labels
        y_axis_pad = 0
        if chart_lines:
            # asciichartpy pads with spaces for y-axis values
            for ch in chart_lines[-1]:
                if ch == " ":
                    y_axis_pad += 1
                else:
                    break

        data_width = chart_width - y_axis_pad
        if data_width > 0 and len(plot_labels) >= 2:
            first_lbl = plot_labels[0]
            last_lbl = plot_labels[-1]
            mid_lbl = plot_labels[len(plot_labels) // 2] if len(plot_labels) >= 3 else ""

            if mid_lbl:
                mid_pos = data_width // 2
                gap1 = max(mid_pos - len(first_lbl), 1)
                gap2 = max(data_width - mid_pos - len(mid_lbl), 1)
                axis_line = " " * y_axis_pad + first_lbl + " " * gap1 + mid_lbl + " " * gap2 + last_lbl
            else:
                gap = max(data_width - len(first_lbl) - len(last_lbl), 1)
                axis_line = " " * y_axis_pad + first_lbl + " " * gap + last_lbl

            parts.append(axis_line)

    return "\n".join(parts)


def candlestick_chart(
    ohlcv: list[dict],
    title: str = "",
    height: int = 20,
) -> str:
    """Render a candlestick chart using plotext.

    Falls back to line_chart(close prices) on ImportError.
    Each dict in ohlcv must have: date, open, high, low, close.
    """
    if not ohlcv:
        return f"{title}\n(no data)" if title else "(no data)"

    # Downsample if too many bars
    if len(ohlcv) > 50:
        step = max(1, len(ohlcv) // 50)
        ohlcv = ohlcv[::step]

    try:
        import plotext as plt

        # Convert YYYY-MM-DD dates to DD/MM/YYYY for plotext
        dates_raw = [bar["date"] for bar in ohlcv]
        dates = []
        for d in dates_raw:
            parts = d.split("-")
            if len(parts) == 3:
                dates.append(f"{parts[2]}/{parts[1]}/{parts[0]}")
            else:
                dates.append(d)

        opens = [bar["open"] for bar in ohlcv]
        highs = [bar["high"] for bar in ohlcv]
        lows = [bar["low"] for bar in ohlcv]
        closes = [bar["close"] for bar in ohlcv]

        plt.clear_figure()
        plt.date_form("d/m/Y")
        plt.theme("clear")
        plt.plot_size(width=80, height=height)
        plt.candlestick(dates, {"Open": opens, "Close": closes, "High": highs, "Low": lows})
        if title:
            plt.title(title)

        chart_str = plt.build()
        # Strip any remaining ANSI escape codes
        chart_str = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", chart_str)
        return chart_str

    except (ImportError, Exception):
        # Fallback: render a line chart of close prices
        closes = [bar["close"] for bar in ohlcv]
        labels = [bar["date"] for bar in ohlcv]
        fallback_title = title or "Price Chart (close)"
        return line_chart(closes, labels=labels, title=fallback_title, height=height)


def bar_chart(
    labels: list[str],
    values: list[float],
    title: str = "",
    width: int = 40,
) -> str:
    """Render horizontal bars using block characters.

    Pads labels to the same width. Scales proportionally.
    """
    if not labels or not values:
        return f"{title}\n(no data)" if title else "(no data)"

    max_label_len = max(len(lbl) for lbl in labels)
    max_val = max(abs(v) for v in values) if values else 1
    if max_val == 0:
        max_val = 1

    parts: list[str] = []
    if title:
        parts.append(title)
        parts.append("")

    for lbl, val in zip(labels, values):
        padded = lbl.rjust(max_label_len)
        bar_len = int(abs(val) / max_val * width)
        # Use full blocks and half block for the remainder
        full_blocks = bar_len
        bar = "\u2588" * full_blocks
        if bar_len < width and abs(val) / max_val * width - bar_len >= 0.5:
            bar += "\u258c"  # half block

        val_str = f"{val:>10,.2f}"
        prefix = "-" if val < 0 else " "
        parts.append(f"  {padded}  {prefix}{bar} {val_str}")

    return "\n".join(parts)


def comparison_chart(
    series: dict[str, list[float]],
    labels: list[str] | None = None,
    title: str = "",
    height: int = 15,
) -> str:
    """Normalize all series to % return from first value and render multi-series chart.

    Uses asciichartpy multi-series plot. Builds legend line.
    """
    import asciichartpy

    if not series:
        return f"{title}\n(no data)" if title else "(no data)"

    legend_styles = ["──", "╌╌", "┈┈", "- -", "··"]
    names = list(series.keys())

    # Normalize each series to % return from first value
    normalized: list[list[float]] = []
    for name in names:
        raw = series[name]
        if not raw or raw[0] == 0:
            normalized.append([0.0] * max(len(raw), 1))
            continue
        base = raw[0]
        pct = [(v / base - 1) * 100 for v in raw]
        # Downsample if needed
        if len(pct) > 60:
            pct = _downsample(pct, 60)
        normalized.append(pct)

    # Ensure all series are the same length (trim to shortest)
    min_len = min(len(s) for s in normalized) if normalized else 0
    normalized = [s[:min_len] for s in normalized]

    cfg = {"height": height}
    chart = asciichartpy.plot(normalized, cfg)

    parts: list[str] = []
    if title:
        parts.append(title)
        parts.append("")

    parts.append(chart)

    # Build legend
    legend_parts = []
    for i, name in enumerate(names):
        style = legend_styles[i % len(legend_styles)]
        # Show final return %
        final_pct = normalized[i][-1] if normalized[i] else 0.0
        sign = "+" if final_pct >= 0 else ""
        legend_parts.append(f"{style} {name} ({sign}{final_pct:.1f}%)")
    parts.append("")
    parts.append("  ".join(legend_parts))

    # X-axis labels
    if labels and len(labels) >= 2:
        ds_labels = labels
        if len(labels) > 60:
            step = max(1, len(labels) // 60)
            ds_labels = labels[::step][:min_len]
        if len(ds_labels) >= 2:
            parts.append(f"  {ds_labels[0]}{'':>{40}}{ds_labels[-1]}")

    return "\n".join(parts)


def yield_curve_chart(
    maturities: list[str],
    yields: list[float],
    title: str = "US Treasury Yield Curve",
) -> str:
    """Render a yield curve chart. Detects inversion and appends spread value."""
    if not maturities or not yields:
        return f"{title}\n(no data)"

    chart = line_chart(yields, labels=maturities, title=title, height=12)

    parts = [chart]

    # Detect inversion: compare shortest vs longest maturity
    short_yield = yields[0]
    long_yield = yields[-1]
    spread = long_yield - short_yield

    parts.append("")
    if spread < 0:
        parts.append(
            f"  *** INVERTED ***  Spread: {spread:+.2f}%  ({maturities[0]}: {short_yield:.2f}%  vs  {maturities[-1]}: {long_yield:.2f}%)"
        )
    else:
        parts.append(
            f"  Spread: {spread:+.2f}%  ({maturities[0]}: {short_yield:.2f}%  vs  {maturities[-1]}: {long_yield:.2f}%)"
        )

    # Check for mid-curve inversion
    if len(yields) >= 3:
        peak_idx = yields.index(max(yields))
        trough_idx = yields.index(min(yields))
        if peak_idx < trough_idx and peak_idx > 0:
            parts.append(f"  Mid-curve inversion detected: peak at {maturities[peak_idx]} ({yields[peak_idx]:.2f}%)")

    return "\n".join(parts)


def allocation_pie(
    categories: dict[str, float],
    title: str = "Portfolio Allocation",
) -> str:
    """Render a proportional bar allocation chart.

    Sorted descending. Shows % and $ values.
    """
    if not categories:
        return f"{title}\n(no data)"

    total = sum(categories.values())
    if total == 0:
        return f"{title}\n(no data — total is $0)"

    # Sort descending by value
    sorted_items = sorted(categories.items(), key=lambda x: x[1], reverse=True)

    max_label_len = max(len(name) for name, _ in sorted_items)
    bar_width = 30

    parts: list[str] = [title, ""]

    for name, value in sorted_items:
        pct = value / total * 100
        bar_len = max(1, int(pct / 100 * bar_width))
        bar = "\u2588" * bar_len
        padded_name = name.rjust(max_label_len)
        parts.append(f"  {padded_name}  {bar} {pct:5.1f}%  ${value:>12,.2f}")

    parts.append(f"{'':>{max_label_len + 2}}  {'─' * (bar_width + 25)}")
    parts.append(f"{'Total':>{max_label_len + 2}}  {'':>{bar_width}} 100.0%  ${total:>12,.2f}")

    return "\n".join(parts)


def heatmap(data: dict[str, float], title: str = "") -> str:
    """Render a performance heatmap sorted best to worst.

    Uses block density to indicate magnitude.
    """
    if not data:
        return f"{title}\n(no data)" if title else "(no data)"

    sorted_items = sorted(data.items(), key=lambda x: x[1], reverse=True)
    max_label_len = max(len(name) for name, _ in sorted_items)
    max_abs = max(abs(v) for _, v in sorted_items) if sorted_items else 1
    if max_abs == 0:
        max_abs = 1

    bar_width = 20

    parts: list[str] = []
    if title:
        parts.append(title)
        parts.append("")

    for name, value in sorted_items:
        padded = name.rjust(max_label_len)
        magnitude = abs(value) / max_abs
        bar_len = max(1, int(magnitude * bar_width))

        if value > 0:
            # Dense blocks for positive
            if magnitude > 0.75:
                bar = "\u2588" * bar_len
            elif magnitude > 0.5:
                bar = "\u2593" * bar_len
            elif magnitude > 0.25:
                bar = "\u2592" * bar_len
            else:
                bar = "\u2591" * bar_len
            sign_indicator = "+"
        elif value < 0:
            # Light blocks for negative
            if magnitude > 0.75:
                bar = "\u2591" * bar_len
            elif magnitude > 0.5:
                bar = "\u2591" * bar_len
            else:
                bar = "\u2591" * bar_len
            sign_indicator = "-"
        else:
            bar = "\u2500"
            sign_indicator = " "

        parts.append(f"  {padded}  {sign_indicator}{value:>+7.2f}%  {bar}")

    return "\n".join(parts)


def _downsample(data: list[float], target_len: int) -> list[float]:
    """Pick evenly-spaced points to reduce data to target_len."""
    n = len(data)
    if n <= target_len:
        return list(data)

    indices = [int(i * (n - 1) / (target_len - 1)) for i in range(target_len)]
    return [data[i] for i in indices]
