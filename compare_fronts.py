import argparse

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def add_3d_poblation (fig, ef: pd.DataFrame, color_column: str, color: str, bar_position: list, trace_position: list, trace_label: str):
    fig.add_trace(go.Scatter3d(
        x=ef["quality"],
        y=ef["degreedistribution"],
        z=ef["motifs"],
        mode='markers',
        marker=dict(
            size=5,
            color=ef[color_column],
            colorscale=color,
            showscale=True,
            colorbar=dict(
                title=color_column,
                titlefont=dict(size=15),
                tickfont=dict(size=13),
                orientation = 'h',
                x = bar_position[0],
                y = bar_position[1],
                len = bar_position[2],
                tickangle=-90,
            ),
        ),
        name=trace_label
    ), row=trace_position[0], col=trace_position[1])
    
def add_3d_ref_point(fig, ref_point: list, color: str, trace_label: str, trace_position: list):
    fig.add_trace(go.Scatter3d(
        x=[ref_point[1]],
        y=[ref_point[2]],
        z=[ref_point[3]],
        mode='markers',
        marker=dict(
            size=8,
            color=color,
            symbol='diamond'
        ),
        name=trace_label
    ), row=trace_position[0], col=trace_position[1])

def add_half_violin(fig, ef: pd.DataFrame, column: str, color: str, side: str, trace_position: list):
    fig.add_trace(go.Violin(
        x=[0] * len(ef),
        y=ef[column],
        side=side,
        line_color=color,
        meanline_visible=True,
        points="all",
        span=[min(ef[column]), max(ef[column])],
        showlegend=False,
    ), row=trace_position[0], col=trace_position[1])
    
def add_violin_point(fig, value: float, color:str, trace_position: list):
    fig.add_trace(go.Scatter(
        x=[0], 
        y=[value],
        mode='markers',
        marker=dict(size=15, symbol='diamond', color=color),
        showlegend=False
    ), row=trace_position[0], col=trace_position[1])

def main(
        initial_evaluated_front: str,
        ref_point_evaluated_fronts: list, 
        ref_points_csv: list,
        output_folder: str
    ) -> None:
    
    # Cargar los archivos con los valores de las funciones de fitness y métricas de validación
    orig_ef = pd.read_csv(initial_evaluated_front, header=1)
    
    ref_efs = []
    for ref_ef_csv in ref_point_evaluated_fronts:
        ref_efs.append(pd.read_csv(ref_ef_csv, header=1))
        
    ref_points = []
    for ref_point_csv in ref_points_csv:
        ref_points.append(list(pd.read_csv(ref_point_csv, sep=";", header=None).loc[0, :]))
        
    ref_points_rows = []
    for ref_point in ref_points:
        ref_points_rows.append(orig_ef.loc[
            (orig_ef["quality"] == ref_point[1]) &
            (orig_ef["degreedistribution"] == ref_point[2]) &
            (orig_ef["motifs"] == ref_point[3])
        ])
    
    
    # Crear gráficos combinados
    fig_combined = make_subplots(
        rows=1, cols=3,
        column_widths=[0.7, 0.15, 0.15],  # Ajusta el tamaño relativo
        specs=[[{"type": "scatter3d"}, {"type": "xy"}, {"type": "xy"}]],
        subplot_titles=("3D Scatter Plot", "AUPR", "AUROC")
    )
    
    # Calcular la longitud de las barras
    num_populations = len(ref_efs) + 1
    bar_len = 0.6/num_populations
    
    # Trazar los puntos del primer archivo con una paleta (e.g., Blues)
    add_3d_poblation(fig_combined, orig_ef, "Accuracy Mean", 'Blues', [bar_len/2, -0.1, bar_len], [1, 1], "Initial Front")
    
    # Trazar los puntos de los otros archivos con otras paletas
    palettes = ["Reds", "Greens", "Purples", "Greys"]
    colors = ["red", "green", "purple", "grey"]
    for i in range(len(ref_efs)):
        add_3d_poblation(fig_combined, ref_efs[i], "Accuracy Mean", palettes[i], [bar_len/2 + (i+1)*bar_len, -0.1, bar_len], [1, 1], f"Reference Point Front {i+1} ({ref_points[i][0]})")
        add_3d_ref_point(fig_combined, ref_points[i], colors[i], f"Reference Point {i+1} ({ref_points[i][0]})", [1, 1])
    
    # Crear gráficos de violín para AUPR
    add_half_violin(fig_combined, orig_ef, "AUPR", "blue", "negative", [1, 2])
    for i in range(len(ref_efs)):
        add_half_violin(fig_combined, ref_efs[i], "AUPR", colors[i], "positive", [1, 2])
        add_violin_point(fig_combined, ref_points_rows[i].iloc[0]['AUPR'], colors[i], [1, 2])
    
    # Crear gráficos de violín para AUROC
    add_half_violin(fig_combined, orig_ef, "AUROC", "blue", "negative", [1, 3])
    for i in range(len(ref_efs)):
        add_half_violin(fig_combined, ref_efs[i], "AUROC", colors[i], "positive", [1, 3])
        add_violin_point(fig_combined, ref_points_rows[i].iloc[0]['AUROC'], colors[i], [1, 3])
    

    # Configurar la figura 3d
    fig_combined.update_layout(
        scene=dict(
            xaxis=dict(
                title="Quality",
                titlefont=dict(size=18),  # Tamaño del título del eje X
                tickfont=dict(size=13)   # Tamaño de los valores del eje X
            ),
            yaxis=dict(
                title="Degree Distribution",
                titlefont=dict(size=18),  # Tamaño del título del eje Y
                tickfont=dict(size=13)   # Tamaño de los valores del eje Y
            ),
            zaxis=dict(
                title="Motifs",
                titlefont=dict(size=18),  # Tamaño del título del eje Z
                tickfont=dict(size=13)   # Tamaño de los valores del eje Z
            )
        ),
        legend=dict(
            font=dict(size=15),  # Tamaño del texto de la leyenda
            itemsizing="constant",  # Tamaño constante de los símbolos de la leyenda
            x=0,
            y=1,
            bgcolor="rgba(255,255,255,0.7)"
        )
    )
    
    # Establecer tamaño de fuente de los títulos
    fig_combined.update_annotations(font_size=22)
    
    # Guardar el gráfico como HTML en la carpeta de salida
    output_file = f"{output_folder}/3d_scatter_plot_violin.html"
    fig_combined.write_html(output_file)
    print(f"Gráfico guardado en: {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--initial-evaluated-front", type=str, required=True, help="Path to the initial evaluated front CSV file.")
    parser.add_argument("--ref-point-evaluated-fronts", nargs='+', required=True, help="Path to the reference point evaluated front CSV file.")
    parser.add_argument("--ref-points-csv", nargs='+', required=True, help="Path to the reference point CSV file.")
    parser.add_argument("--output-folder", type=str, required=True, help="Path to the output folder.")
    args = parser.parse_args()

    main(
        args.initial_evaluated_front,
        args.ref_point_evaluated_fronts,
        args.ref_points_csv,
        args.output_folder
    )