import plotly.graph_objects as go

COLORS = {"Front": "#4C9AFF", "Middle": "#22A06B", "Rear": "#E2A400"}

def cabin_figure(assignments, rows=30):
    fig = go.Figure()
    if assignments.empty:
        return fig
    for zone, group in assignments.groupby("zone"):
        xs, ys, zs, hover = [], [], [], []
        for _, p in group.iterrows():
            # условные координаты: шесть кресел поперёк салона
            letter_order = "ABCDEF"
            x = letter_order.index(str(p["letter"])) - 2.5
            xs.append(x)
            ys.append(float(p["row"]))
            zs.append(0.0)
            hover.append(
                f"Seat: {p['seat']}<br>Passenger: {p['passenger_id']}"
                f"<br>Mass: {p['weight_kg']} kg<br>Zone: {zone}"
            )
        fig.add_trace(go.Scatter3d(
            x=xs, y=ys, z=zs, mode="markers+text",
            text=group["seat"], textposition="top center",
            hovertext=hover, hoverinfo="text",
            marker=dict(size=5, color=COLORS.get(zone, "#888")),
            name=zone
        ))
    fig.update_layout(
        height=650, margin=dict(l=0, r=0, t=20, b=0),
        scene=dict(
            xaxis=dict(title="Across cabin", showticklabels=False),
            yaxis=dict(title="Row", autorange="reversed"),
            zaxis=dict(title="", visible=False),
            aspectmode="manual", aspectratio=dict(x=0.7, y=2.8, z=0.25)
        ),
        legend_title="Cabin zone"
    )
    return fig
