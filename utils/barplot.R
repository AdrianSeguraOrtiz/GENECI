library("ggplot2")
library("magrittr")
library("dplyr")
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
  df_proc["Group"] <- "Tecs"
  df_proc[df_proc$Technique %in% c("BEST_GENECI", "MEDIAN_GENECI"), "Group"] <- "GENECI"  
  df_proc["File"] <- tag
  df_proc <- df_proc[order(-df_proc$Value), ]
  return(df_proc)
}

# Función para generar gráfica
generar_grafica <- function(df, output_file) {
    # Establecer paleta de colores
    colores <- c("#FF96A5", "#85D5D5", "#FFD275", "#FF847F", "#FF92A2", "#C7E8B7", "#95DFA6", "#6FAF9C", "#FFBE91", "#5C7373", "#FFA56B", "#8CD9AB", "#B1E9FF", "#FFD58C", "#70BDBD", "#FF8A9F", "#D57AB3", "#FCA2B7", "#59789A", "#6BB7A1", "#87BFE8", "#FFA563", "#E7A9C8", "#D1EABE", "#BCC9DB", "#B89FB5", "#42576B", "#FF96A5")

    # Convertir la columna Technique en factor para que aparezca las técnicas del grupo GENECI al final
    geneci_techniques <- c("BEST_GENECI", "MEDIAN_GENECI")
    other_techniques <- unique(df$Technique[!df$Technique %in% geneci_techniques])
    df$Technique <- factor(df$Technique, levels = c(geneci_techniques, other_techniques))

    # Draw barplot with grouping & stacking
    ## AUROC
    df1 <- subset(df, Metric == "AUROC")
    p1 <- ggplot(df1,
                aes(x = Group,
                    y = Value,
                    fill = Technique)) +
        geom_bar(stat = "identity",
                position = "identity") +
        facet_grid(~ File) +
        scale_fill_manual(values = colores) +
        labs(title = "Accuracy comparison: AUROC") +
        theme(plot.title = element_text(color = "#333333", size = 12, face = "bold")) +
        guides(fill = "none")  # Eliminar la leyenda de p1
    ## AUPR
    df2 <- subset(df, Metric == "AUPR")
    p2 <- ggplot(df2,
                aes(x = Group,
                    y = Value,
                    fill = Technique)) +
        geom_bar(stat = "identity",
                position = "identity") +
        facet_grid(~ File) +
        scale_fill_manual(values = colores) +
        labs(title = "Accuracy comparison: AUPR") +
        theme(plot.title = element_text(color = "#333333", size = 12, face = "bold")) +
        guides(fill = "none")  # Eliminar la leyenda de p2

    # Agregar línea discontinua horizontal para técnica y grupo específicos
    ## AUROC
    p1 <- p1 +
    geom_hline(data = subset(df1, Group == "GENECI" & Technique == "BEST_GENECI"),
               aes(yintercept = Value),
               linetype = "dashed",
               color = "black")
    ## AUPR
    p2 <- p2 +
    geom_hline(data = subset(df2, Group == "GENECI" & Technique == "BEST_GENECI"),
               aes(yintercept = Value),
               linetype = "dashed",
               color = "black")
    
    # Agregar cantidad de técnicas superadas
    ## AUROC
    anotacion1 <- unlist(lapply(split(df1, df1$File), function(cp) sum(cp[cp$Group == "Tecs", "Value"] < as.numeric(cp[cp$Technique == "BEST_GENECI", "Value"]))))
    ## AUPR
    anotacion2 <- unlist(lapply(split(df2, df2$File), function(cp) sum(cp[cp$Group == "Tecs", "Value"] < as.numeric(cp[cp$Technique == "BEST_GENECI", "Value"]))))

    # Calcular las posiciones de las anotaciones
    ## AUROC
    anotacion1_df <- data.frame(File = names(anotacion1), Anotacion = as.numeric(anotacion1))
    anotacion1_df <- merge(anotacion1_df, df1, by = "File")
    ## AUPR
    anotacion2_df <- data.frame(File = names(anotacion2), Anotacion = as.numeric(anotacion2))
    anotacion2_df <- merge(anotacion2_df, df2, by = "File")

    # Añadir anotaciones encima de las barras del grupo GENECI
    ## AUROC
    p1 <- p1 +
        geom_text(data = subset(anotacion1_df, Technique == "BEST_GENECI"),
                  aes(x = Group, y = Value, label = Anotacion),
                  vjust = -0.5, color = "black", inherit.aes = FALSE, size = 2)
    ## AUPR
    p2 <- p2 +
        geom_text(data = subset(anotacion2_df, Technique == "BEST_GENECI"),
                  aes(x = Group, y = Value, label = Anotacion),
                  vjust = -0.5, color = "black", inherit.aes = FALSE, size = 2)

    # Obtener las técnicas correspondientes a "Tecs" con el mayor valor en cada facet
    ## AUROC
    tecs_max1 <- subset(df1, Group == "Tecs") %>%
      group_by(File) %>%
      slice(which.max(Value))
    ## AUPR
    tecs_max2 <- subset(df2, Group == "Tecs") %>%
      group_by(File) %>%
      slice(which.max(Value))

    # Añadir etiquetas encima de las barras más altas del grupo "Tecs" en cada facet
    ## AUROC
    p1 <- p1 +
      geom_text(data = tecs_max1,
                aes(x = Group, y = Value, label = Technique),
                vjust = -0.5, color = "black", inherit.aes = FALSE, size = 2)
    ## AUPR
    p2 <- p2 +
      geom_text(data = tecs_max2,
                aes(x = Group, y = Value, label = Technique),
                vjust = -0.5, color = "black", inherit.aes = FALSE, size = 2)

    # Añadir espacio al eje x para que las etiquetas no se corten
    ## AUROC
    p1 <- p1 + coord_cartesian(ylim = range(df1$Value) + c(0, 0.05 * diff(range(df1$Value))))
    ## AUPR
    p2 <- p2 + coord_cartesian(ylim = range(df2$Value) + c(0, 0.05 * diff(range(df2$Value))))

    # Combinar gráficas con patchwork
    combined_plot <- p1 + p2 + plot_layout(guides = "collect", nrow = 2)

    # Ajustar la leyenda
    combined_plot <- combined_plot + 
      theme(legend.key.size = unit(0.4, "cm")) +
      guides(fill = guide_legend(ncol = 1, title = paste(length(other_techniques), "Indv Tecs +", length(geneci_techniques), "GENECI")))
      
    # Guardar la gráfica en formato PDF
    ggsave(output_file, combined_plot, width = 12, height = 6, dpi = 500, device = "pdf")
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
