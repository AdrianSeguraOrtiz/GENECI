library("ggplot2")
library("tidyr")
library("patchwork")

# Función principal del script
main <- function(input_files, output_file) {
    # Crear un dataframe vacío para almacenar los resultados
    resultado <- data.frame()

    # Leer y procesar los archivos de entrada
    resultados <- list()
    for (i in seq_along(input_files)) {
        archivo <- input_files[i]
        datos <- leer_archivo(archivo)
        tag <- tags[i]
        datos_proc <- procesar_datos(datos, tag)

        # Concatenar los datos_proc al dataframe resultado
        resultado <- rbind(resultado, datos_proc)
    }
  
  # Generar gráfica
  generar_grafica(resultado, output_file)
}

# Función para leer un archivo de entrada
leer_archivo <- function(archivo) {
  df <- read.csv(archivo, skip=1, sep=";")
  return(df)
}

# Función para procesar los datos
procesar_datos <- function(df, tag) {
  df_proc <- subset(df, !Technique %in% c("MEAN", "MEDIAN"))
  df_proc <- df_proc[, names(df_proc) != "Mean"]
  df_proc <- tidyr::pivot_longer(df_proc, cols = c(AUROC, AUPR), names_to = "Metric", values_to = "Value") 
  df_proc["File"] <- tag
  df_proc <- df_proc[order(-df_proc$Value), ]
  return(df_proc)
}

# Función para generar gráfica
generar_grafica <- function(df, output_file, tecnica_resaltada) {
    colores <- c("#FF96A5", "#85D5D5", "#FFD275", "#FF847F", "#FF92A2", "#C7E8B7", "#95DFA6", "#6FAF9C", "#FFBE91", "#5C7373", "#FFA56B", "#8CD9AB", "#B1E9FF", "#FFD58C", "#70BDBD", "#FF8A9F", "#D57AB3", "#FCA2B7", "#59789A", "#6BB7A1", "#87BFE8", "#FFA563", "#E7A9C8", "#D1EABE", "#BCC9DB", "#B89FB5", "#42576B", "#FF96A5")
    
    # Convertir la columna Technique en factor para que aparezca las técnicas del grupo GENECI al final
    geneci_techniques <- c("BEST_GENECI", "MEDIAN_GENECI")
    other_techniques <- unique(df$Technique[!df$Technique %in% geneci_techniques])
    df$Technique <- factor(df$Technique, levels = c(geneci_techniques, other_techniques))

    df1 <- subset(df, Metric == "AUROC")
    p1 <- ggplot(df1, aes(x = File, y = Value, group = Technique, color = Technique)) +
            geom_line(stat = "identity",
                         position = "identity",
                         linetype = 5) +
            geom_point(stat = "identity",
                         position = "identity") +
            geom_density(data = subset(df1, Technique == "BEST_GENECI"), 
                         aes(fill = Technique), 
                         alpha = 0.3,
                         stat = "identity",
                         position = "identity",
                         show.legend = FALSE) + 
            scale_color_manual(values = colores) +
            coord_cartesian(ylim = range(df1$Value)) +
            theme_bw() +
            labs(title = "Accuracy comparison: AUROC") +
            theme(plot.title = element_text(color = "#333333", size = 12, face = "bold")) +
            theme(axis.text.x = element_text(angle = 30, hjust = 1)) +
            guides(color = guide_legend(ncol = 1)) +
            theme(legend.key.size = unit(0.4, "cm"))
    
    df2 <- subset(df, Metric == "AUPR")
    p2 <- ggplot(df2, aes(x = File, y = Value, group = Technique, color = Technique)) +
            geom_line(stat = "identity",
                         position = "identity",
                         linetype = 5,
                         show.legend = FALSE) +
            geom_point(stat = "identity",
                         position = "identity",
                         show.legend = FALSE) +
            geom_density(data = subset(df2, Technique == "BEST_GENECI"), 
                         aes(fill = Technique), 
                         alpha = 0.3,
                         stat = "identity",
                         position = "identity",
                         show.legend = FALSE) + 
            scale_color_manual(values = colores) +
            coord_cartesian(ylim = range(df2$Value)) +
            theme_bw() +
            labs(title = "Accuracy comparison: AUPR") +
            theme(plot.title = element_text(color = "#333333", size = 12, face = "bold")) +
            theme(axis.text.x = element_text(angle = 30, hjust = 1)) +
            guides(color = guide_legend(ncol = 1)) +
            theme(legend.key.size = unit(0.4, "cm"))


    # Combinar gráficas con patchwork
    combined_plot <- p1 + p2 + plot_layout(guides = "collect", nrow = 2)

    # Guardar la gráfica en formato PDF
    ggsave(output_file, combined_plot, width = 10, height = 6, dpi = 500, device = "pdf")
}





# Obtener los argumentos de línea de comandos
args <- commandArgs(trailingOnly = TRUE)

# Verificar que se proporcionen al menos 2 argumentos
if (length(args) < 2) {
  stop("Se deben proporcionar al menos 2 argumentos: archivos de entrada y archivo de salida")
}

# Obtener los archivos de entrada (todos los argumentos pares excepto el último)
input_files <- args[(seq_along(args) %% 2 == 0) & seq_along(args) < length(args)]

# Obtener etiquetas (todos los argumentos impares excepto el último)
tags <- args[(seq_along(args) %% 2 != 0) & seq_along(args) < length(args)]

# Obtener el archivo de salida (último argumento)
output_file <- tail(args, 1)

# Llamar a la función principal del script
main(input_files, output_file)
