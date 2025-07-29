import tempfile
import os, cv2, numpy as np, pandas as pd, matplotlib.pyplot as plt
import plotly.express as px
from matplotlib.ticker import MaxNLocator
import streamlit as st

def draw_counter(frame, count):
    # reuse this from your main file or refactor as needed
    ...

def display_graphs_and_outputs():
    # Retrieve outputs from session state
    df_counts = st.session_state.get("df_counts")
    preview_frame = st.session_state.get("preview_frame")
    csv_path = st.session_state.get("csv_path")
    graph_path = st.session_state.get("graph_path")
    out_path = st.session_state.get("output_video_path")

    st.success("Processing complete!")
    with open(out_path, "rb") as f:
        st.download_button("Download Tracked Video", f, file_name="tracked_output.mp4")

    st.write("### Output Frame Preview")
    if preview_frame is not None:
        st.image(preview_frame, caption="First Frame of Output Video", channels="RGB")

    st.write("### Detection Counts per Interval")
    st.dataframe(df_counts)
    with open(csv_path, "rb") as f:
        st.download_button("Download Detection Counts CSV", f, file_name="detection_counts.csv", mime="text/csv")

    st.write("### Detection Graph")

    customize = st.checkbox("Customize Graph", value=False)
    col1, col2 = st.columns([1, 3])

    with col1:
        if customize:
            chart_title = st.text_input("Title", value="Object Count per Interval")
            x_axis_label = st.text_input("X Axis Label", value="Second")
            y_axis_label = st.text_input("Y Axis Label", value="Unique IDs")
            image_format = st.selectbox("Graph Image Format", options=["PNG", "JPEG"], index=0)
            png_dpi = st.number_input("PNG DPI", min_value=50, max_value=1200, value=300, step=50, format="%d")

            col_tick, col_bg = st.columns(2)
            with col_tick:
                tick_interval_x = st.number_input("X Tick Interval", min_value=1, value=1, step=1)
                tick_interval_y = st.number_input("Y Tick Interval", min_value=1, value=1, step=1)
            with col_bg:
                background_color = st.color_picker("BG Color", value="#ffffff")
                line_color = st.color_picker("Line Color", value="#636EFA")

            line_width = st.number_input("Line Width", min_value=1, max_value=10, value=2)

            col_ymax, col_xmax = st.columns([1, 1])
            with col_ymax:
                y_axis_max = st.number_input("Y Max", min_value=1, value=int(df_counts["Unique IDs"].max()), key="y_max_input")
            with col_xmax:
                x_axis_max = st.number_input("X Max", min_value=1, value=int(df_counts["Second"].max()), key="x_max_input")

            graph_width = st.slider("Width (px)", min_value=400, max_value=1200, value=800, step=50)
            graph_height = st.slider("Height (px)", min_value=300, max_value=800, value=500, step=50)
            show_grid = st.checkbox("Grid", value=True)
        else:
            tick_interval_x, tick_interval_y = 1, 1
            graph_width, graph_height = 800, 500
            chart_title = "Object Count per Interval"
            x_axis_label = "Second"
            y_axis_label = "Unique IDs"
            show_grid = True
            background_color = "#ffffff"
            y_axis_max = int(df_counts["Unique IDs"].max())
            x_axis_max = int(df_counts["Second"].max())
            png_dpi = 300
            line_color = "#636EFA"
            image_format = "PNG"
            line_width = 2

    # Static matplotlib
    fig, ax = plt.subplots(figsize=(graph_width / 100, graph_height / 100))
    df_counts.set_index("Second").plot(ax=ax, legend=False, color=line_color, linewidth=line_width)
    ax.set_facecolor(background_color)
    ax.set_title(chart_title)
    ax.set_xlabel(x_axis_label)
    ax.set_ylabel(y_axis_label)
    if show_grid:
        ax.grid(True, linestyle='--', linewidth=0.5, color='lightgrey')
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_xticks(np.arange(0, x_axis_max + 1, tick_interval_x))
    ax.set_yticks(np.arange(0, y_axis_max + 1, tick_interval_y))
    ax.set_ylim(bottom=0, top=y_axis_max)
    image_ext = "png" if image_format == "PNG" else "jpg"
    graph_path = os.path.join(tempfile.gettempdir(), f"detection_graph.{image_ext}")
    fig.savefig(graph_path, dpi=png_dpi, format=image_format.lower())
    plt.close(fig)

    with col2:
        fig = px.line(
            df_counts,
            x="Second",
            y="Unique IDs",
            title=chart_title,
            labels={"Second": x_axis_label, "Unique IDs": y_axis_label}
        )
        fig.update_layout(
            plot_bgcolor=background_color,
            height=graph_height,
            width=graph_width,
            xaxis=dict(tickmode="linear", dtick=tick_interval_x, tickformat='d', range=[0, x_axis_max]),
            yaxis=dict(tickformat='d', dtick=tick_interval_y, range=[0, y_axis_max], gridcolor='lightgrey' if show_grid else None)
        )
        fig.update_traces(line=dict(color=line_color, width=line_width))
        st.plotly_chart(fig)
        with open(graph_path, "rb") as f:
            col_dl1, col_dl2, col_dl3 = st.columns([1, 2, 1])
            with col_dl2:
                st.download_button("Download Graph", f, file_name=f"detection_graph.{image_format.lower()}", key="centered_graph_button")

    # with open(graph_path, "rb") as f:
    #     st.download_button("Download Graph", f, file_name="detection_graph.png")

    # PDF report download button
    from utils.pdf_report import generate_pdf_report

    video_filename = st.session_state["uploaded_video"].name if "uploaded_video" in st.session_state else "Unknown"
    pdf_path = generate_pdf_report(df_counts, preview_frame, graph_path, video_filename)
    with open(pdf_path, "rb") as f:
        st.download_button("Download PDF Report", f, file_name="tracking_report.pdf", mime="application/pdf")