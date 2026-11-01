"""Plotly chart helpers: one palette, one set of mark specs, light and dark modes.

Colour rules followed throughout:
- islands keep the same hue in every chart (colour follows the entity);
- the first three categorical slots are the only ones used where every pair can
  meet (scatter), and they validate all-pairs in both modes;
- Unallocated (months INE did not publish) is a neutral grey, never a hue;
- one y-axis per chart; two measures with different units get two charts.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

FONT = 'system-ui, -apple-system, "Segoe UI", sans-serif'

THEMES = {
    "light": {
        "surface": "#fcfcfb",
        "ink": "#0b0b0b",
        "ink_2": "#52514e",
        "muted": "#898781",
        "grid": "#e1e0d9",
        "axis": "#c3c2b7",
        "series": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"],
        "neutral": "#a3a29c",
        "up": "#2a78d6",
        "down": "#e34948",
        "sequential": ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"],
    },
    "dark": {
        "surface": "#1a1a19",
        "ink": "#f0efec",
        "ink_2": "#c3c2b7",
        "muted": "#898781",
        "grid": "#2c2c2a",
        "axis": "#383835",
        "series": ["#3987e5", "#d95926", "#199e70", "#c98500"],
        "neutral": "#6f6e69",
        "up": "#3987e5",
        "down": "#e66767",
        "sequential": ["#0d366b", "#184f95", "#256abf", "#3987e5", "#6da7ec", "#9ec5f4", "#cde2fb"],
    },
}

ISLANDS = ["Mallorca", "Menorca", "Ibiza-Formentera"]
UNALLOCATED = "Unallocated"


def island_colors(mode: str) -> dict[str, str]:
    t = THEMES[mode]
    colors = dict(zip(ISLANDS, t["series"]))
    colors[UNALLOCATED] = t["neutral"]
    colors["All islands"] = t["series"][0]
    return colors


def base_layout(fig: go.Figure, mode: str, height: int = 360, y_format: str | None = None,
                y_title: str | None = None, legend: bool = True, hovermode: str = "x unified") -> go.Figure:
    t = THEMES[mode]
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=36 if legend else 12, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, size=13, color=t["ink_2"]),
        hovermode=hovermode,
        hoverlabel=dict(bgcolor=t["surface"], bordercolor=t["axis"], font=dict(family=FONT, color=t["ink"])),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    title=None, font=dict(color=t["ink_2"])),
        barcornerradius=4,
        bargap=0.35,
    )
    fig.update_xaxes(automargin=True, showgrid=False, linecolor=t["axis"], ticks="", tickfont=dict(color=t["muted"]),
                     title=None, showspikes=hovermode == "x unified", spikecolor=t["axis"],
                     spikethickness=1, spikedash="solid", spikemode="across")
    fig.update_yaxes(automargin=True, gridcolor=t["grid"], gridwidth=1, zeroline=False, linecolor=t["axis"],
                     tickfont=dict(color=t["muted"]), title=y_title, title_font=dict(color=t["muted"], size=12),
                     tickformat=y_format, rangemode="tozero")
    return fig


def _end_labels(fig: go.Figure, ends: list, values: pd.Series, colors: dict[str, str], mode: str, height: int,
                zero_base: bool) -> None:
    """End-dots at the true last points; text nudged apart so labels never overlap."""
    t = THEMES[mode]
    span = (values.max() - (min(values.min(), 0) if zero_base else values.min())) or 1
    min_gap = span * 18 / max(height - 90, 100)  # ~18 px expressed in data units
    ends = sorted(ends, key=lambda e: e[0])
    label_y = [e[0] for e in ends]
    for i in range(1, len(label_y)):
        label_y[i] = max(label_y[i], label_y[i - 1] + min_gap)
    for (yv, xv, name), ly in zip(ends, label_y):
        fig.add_trace(go.Scatter(x=[xv], y=[yv], mode="markers", hoverinfo="skip", showlegend=False,
                                 marker=dict(size=9, color=colors[name], line=dict(width=2, color=t["surface"]))))
        fig.add_annotation(x=xv, y=ly, text=name, showarrow=False, xanchor="left", xshift=8,
                           font=dict(color=t["ink_2"], size=12))


def lines(df: pd.DataFrame, x: str, y: str, series: str, order: list[str], colors: dict[str, str],
          mode: str, value_format: str, height: int = 360, y_format: str | None = None,
          y_title: str | None = None, end_labels: bool = True, markers: bool = False,
          zero_base: bool = True) -> go.Figure:
    """One line per series on one shared y-axis. Gaps stay gaps (unpublished months are not zero)."""
    fig = go.Figure()
    present = [s for s in order if s in set(df[series])]
    integer_x = pd.api.types.is_integer_dtype(df[x])
    date_x = pd.api.types.is_datetime64_any_dtype(df[x])
    if (integer_x or date_x) and len(df):
        # complete the x range so a missing year or month shows as a gap, not a bridge
        if integer_x:
            full = range(int(df[x].min()), int(df[x].max()) + 1)
        else:
            full = pd.date_range(df[x].min(), df[x].max(), freq="MS")
        df = pd.MultiIndex.from_product([present, full], names=[series, x]).to_frame(index=False).merge(
            df, on=[series, x], how="left")
    for name in present:
        d = df[df[series] == name].sort_values(x)
        fig.add_trace(go.Scatter(
            x=d[x], y=d[y], name=name, mode="lines+markers" if markers else "lines",
            connectgaps=False, line=dict(width=2, color=colors[name], shape="linear"),
            marker=dict(size=8, line=dict(width=2, color=THEMES[mode]["surface"])),
            hovertemplate=f"%{{y:{value_format}}}<extra>{name}</extra>",
        ))
    base_layout(fig, mode, height=height, y_format=y_format, y_title=y_title, legend=len(present) > 1)
    if not zero_base:
        fig.update_yaxes(rangemode="normal")
    if integer_x and len(df):
        fig.update_xaxes(range=[df[x].min() - 0.4, df[x].max() + 0.4])
    elif date_x and len(df):
        fig.update_xaxes(range=[df[x].min() - pd.Timedelta(days=15), df[x].max() + pd.Timedelta(days=15)])
    if end_labels and 1 < len(present) <= 4:
        ends = []
        for name in present:
            d = df[(df[series] == name) & df[y].notna()].sort_values(x)
            if len(d):
                ends.append([d[y].iloc[-1], d[x].iloc[-1], name])
        if ends:
            _end_labels(fig, ends, df[y], colors, mode, height, zero_base)
            fig.update_layout(margin=dict(r=24 + 7 * max(len(e[2]) for e in ends)))
    return fig


def hbar(df: pd.DataFrame, category: str, value: str, mode: str, value_format: str,
         height: int | None = None, x_format: str | None = None, diverging: bool = False,
         highlight: str | None = None) -> go.Figure:
    """Horizontal ranked bars. One colour for a single measure; blue/red for signed change."""
    t = THEMES[mode]
    d = df.sort_values(value)
    if diverging:
        colors = [t["up"] if v >= 0 else t["down"] for v in d[value]]
    else:
        colors = [t["series"][0] if highlight is None or c == highlight else t["neutral"] for c in d[category]]
    fig = go.Figure(go.Bar(
        x=d[value], y=d[category], orientation="h", marker=dict(color=colors, line=dict(width=0)),
        width=0.6, hovertemplate=f"%{{x:{value_format}}}<extra>%{{y}}</extra>",
        text=[format(v, value_format) if pd.notna(v) else "" for v in d[value]],
        textposition="outside", cliponaxis=False, textfont=dict(color=t["ink_2"], size=12),
    ))
    base_layout(fig, mode, height=height or 40 + 34 * len(d), legend=False, hovermode="closest")
    fig.update_xaxes(showgrid=True, gridcolor=t["grid"], tickformat=x_format, zeroline=diverging,
                     zerolinecolor=t["axis"], zerolinewidth=1)
    fig.update_yaxes(showgrid=False, rangemode=None, tickfont=dict(color=t["ink_2"]))
    lo, hi = min(d[value].min(), 0), max(d[value].max(), 0)
    pad = (hi - lo) * 0.18
    fig.update_xaxes(range=[lo - (pad if lo < 0 else 0), hi + pad])
    fig.update_layout(margin=dict(l=8, r=16, t=12, b=8))
    return fig


def stacked_columns(df: pd.DataFrame, x: str, y: str, series: str, order: list[str], colors: dict[str, str],
                    mode: str, value_format: str, height: int = 360, y_format: str | None = None,
                    y_title: str | None = None) -> go.Figure:
    t = THEMES[mode]
    fig = go.Figure()
    for name in order:
        d = df[df[series] == name]
        if d.empty:
            continue
        fig.add_trace(go.Bar(x=d[x], y=d[y], name=name, marker=dict(color=colors[name], line=dict(width=1, color=t["surface"])),
                             hovertemplate=f"%{{y:{value_format}}}<extra>{name}</extra>"))
    base_layout(fig, mode, height=height, y_format=y_format, y_title=y_title)
    fig.update_layout(barmode="stack", bargap=0.3)
    return fig


def heatmap(df: pd.DataFrame, x: str, y: str, z: str, mode: str, value_format: str,
            x_order: list, y_order: list, height: int = 380, colorbar_format: str | None = None) -> go.Figure:
    """Month x year grid on a single-hue sequential ramp. Missing cells stay empty."""
    t = THEMES[mode]
    grid = df.pivot_table(index=y, columns=x, values=z, aggfunc="first").reindex(index=y_order, columns=x_order)
    ramp = t["sequential"]
    scale = [[i / (len(ramp) - 1), c] for i, c in enumerate(ramp)]
    fig = go.Figure(go.Heatmap(
        z=grid.values, x=grid.columns, y=grid.index, colorscale=scale, xgap=2, ygap=2,
        hovertemplate=f"%{{y}} %{{x}}: %{{z:{value_format}}}<extra></extra>",
        colorbar=dict(thickness=10, outlinewidth=0, tickformat=colorbar_format, tickfont=dict(color=t["muted"])),
    ))
    base_layout(fig, mode, height=height, legend=False, hovermode="closest")
    fig.update_yaxes(autorange="reversed", showgrid=False, rangemode=None, type="category", dtick=1)
    fig.update_xaxes(type="category")
    return fig


def scatter(df: pd.DataFrame, x: str, y: str, series: str, order: list[str], colors: dict[str, str], mode: str,
            x_format: str, y_format: str, hover_label: str, height: int = 380,
            x_title: str | None = None, y_title: str | None = None) -> go.Figure:
    t = THEMES[mode]
    fig = go.Figure()
    for name in order:
        d = df[df[series] == name]
        if d.empty:
            continue
        fig.add_trace(go.Scatter(
            x=d[x], y=d[y], name=name, mode="markers", customdata=d[[hover_label]],
            marker=dict(size=9, color=colors[name], opacity=0.85, line=dict(width=1.5, color=t["surface"])),
            hovertemplate=(f"<b>%{{customdata[0]}}</b><br>{x_title}: %{{x:{x_format}}}<br>"
                           f"{y_title}: %{{y:{y_format}}}<extra>{name}</extra>"),
        ))
    base_layout(fig, mode, height=height, legend=True, hovermode="closest")
    fig.update_xaxes(showgrid=True, gridcolor=t["grid"], tickformat=x_format,
                     title=x_title, title_font=dict(color=t["muted"], size=12), rangemode=None)
    fig.update_yaxes(title=y_title, rangemode=None)
    return fig


def small_multiples(df: pd.DataFrame, x: str, y: str, facet: str, facet_order: list[str], mode: str,
                    value_format: str, cols: int = 4, height_per_row: int = 170, y_format: str | None = None,
                    series: str | None = None, series_order: list[str] | None = None,
                    series_colors: dict[str, str] | None = None) -> go.Figure:
    """A grid of panels sharing one y-scale. Without `series`, every panel is one line in slot 1."""
    t = THEMES[mode]
    rows = -(-len(facet_order) // cols)
    fig = make_subplots(rows=rows, cols=cols, shared_yaxes=True, shared_xaxes=True,
                        subplot_titles=facet_order, horizontal_spacing=0.03, vertical_spacing=0.18 if rows > 1 else 0.1)
    seen = set()
    for i, panel in enumerate(facet_order):
        r, c = i // cols + 1, i % cols + 1
        d = df[df[facet] == panel]
        groups = [(None, d)] if series is None else [(s, d[d[series] == s]) for s in series_order]
        for name, g in groups:
            g = g.sort_values(x)
            color = t["series"][0] if name is None else series_colors[name]
            fig.add_trace(go.Scatter(
                x=g[x], y=g[y], mode="lines", name=name or panel, connectgaps=False,
                line=dict(width=2, color=color), legendgroup=name, showlegend=name is not None and name not in seen,
                hovertemplate=f"%{{x}}: %{{y:{value_format}}}<extra>{name or panel}</extra>",
            ), row=r, col=c)
            seen.add(name)
    base_layout(fig, mode, height=height_per_row * rows + 60, y_format=y_format,
                legend=series is not None, hovermode="closest")
    fig.update_annotations(font=dict(color=t["ink_2"], size=12), yshift=6)
    fig.update_layout(margin=dict(t=72 if series is not None else 36),
                      legend=dict(y=1.0, yref="container", yanchor="top"))
    fig.update_xaxes(showspikes=False)
    return fig
