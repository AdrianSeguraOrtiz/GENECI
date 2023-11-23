library("ggplot2")
library("tidyr")
library("fmsb")

# Función principal del script
main <- function(input_files, output_file) {

    # Realizar inner join con los demás archivos
    for (i in seq_along(input_files)) {
        archivo <- input_files[i]
        datos <- leer_archivo(archivo)
        tag <- tags[i]
        datos_proc <- procesar_datos(datos, tag)

        # Realizar inner join basado en la primera columna
        if (i == 1) {
            resultado_AUPR <- datos_proc$aupr
            resultado_AUROC <- datos_proc$auroc
        } else {
            resultado_AUPR <- merge(resultado_AUPR, datos_proc$aupr, by = 1)
            resultado_AUROC <- merge(resultado_AUROC, datos_proc$auroc, by = 1)
        }
    }

    # Generar gráfica
    resultado_AUPR <- procesar_resultados(resultado_AUPR)
    resultado_AUROC <- procesar_resultados(resultado_AUROC)
    generar_grafica(resultado_AUPR, resultado_AUROC, output_file)
}

# Función para leer un archivo de entrada
leer_archivo <- function(archivo) {
  df <- read.csv(archivo, skip=1, sep=";")
  return(df)
}

# Función para procesar los datos
procesar_datos <- function(df, tag) {
  df_proc <- subset(df, !Technique %in% c("MEAN", "MEDIAN")) 
  df_proc["File"] <- tag
  df_proc_AUPR <- df_proc[, !names(df) %in% c("Mean", "AUROC")] 
  df_proc_AUPR <- pivot_wider(df_proc_AUPR, names_from = File, values_from = AUPR)
  df_proc_AUROC <- df_proc[, !names(df) %in% c("Mean", "AUPR")] 
  df_proc_AUROC <- pivot_wider(df_proc_AUROC, names_from = File, values_from = AUROC)
  return(list(auroc = df_proc_AUROC, aupr = df_proc_AUPR))
}

# Función para procesar los resultados
procesar_resultados <- function(df, tag) {
    rownames(df) <- df[, 1]
    df <- df[, -1]
    valores_maximos <- apply(df, 2, max)
    valores_minimos <- apply(df, 2, min)
    df <- rbind(valores_minimos, df)
    df <- rbind(valores_maximos, df)
    rownames(df) <- c("Max", "Min", tail(rownames(df), -2))
    return(df)
}

# Función para generar gráfica
generar_grafica <- function(df1, df2, output_file) {
    # Establecer paleta de colores
    colores <- c("#FF96A5", "#85D5D5", "#FFD275", "#FF847F", "#FF92A2", "#C7E8B7", "#95DFA6", "#6FAF9C", "#FFBE91", "#5C7373", "#FFA56B", "#8CD9AB", "#B1E9FF", "#FFD58C", "#70BDBD", "#FF8A9F", "#D57AB3", "#FCA2B7", "#59789A", "#6BB7A1", "#87BFE8", "#FFA563", "#E7A9C8", "#D1EABE", "#BCC9DB", "#B89FB5", "#42576B", "#FF96A5")
    fill_colors <- scales::alpha(colores, 0.5)
    fill_colors[-which(tail(rownames(df1), -2) == "BEST_MO-GENECI")] <- NA

    # Guardar las gráficas en un archivo PDF
    pdf(file = output_file, width = 10, height = 5)  # Aumenta la altura para acomodar la leyenda

    # Crear gráfico de radar utilizando radarchart de fmsb
    par(mai=c(0, 0.5, 0.25, 0.5))
    layout(matrix(c(1,2,3,3), ncol = 2, nrow = 2, byrow = TRUE), heights=c(3,1))
    radarchart(
        df1,
        cglty = 1,       # Tipo de línea del grid
        cglcol = "gray", # Color del grid
        cglwd = 1,       # Ancho líneas grid
        pcol = colores,  # Color de la línea
        plwd = ifelse(tail(rownames(df1), -2) == "BEST_MO-GENECI", 3, 1),        # Ancho de la línea
        plty = 1,        # Tipo de línea
        pfcol = fill_colors,         # Color del área
        title = "AUPR",        # Título del radar
    )

    radarchart(
        df2,
        cglty = 1,       # Tipo de línea del grid
        cglcol = "gray", # Color del grid
        cglwd = 1,       # Ancho líneas grid
        pcol = colores,  # Color de la línea
        plwd = ifelse(tail(rownames(df1), -2) == "BEST_MO-GENECI", 3, 1),        # Ancho de la línea
        plty = 1,        # Tipo de línea
        pfcol = fill_colors,         # Color del área
        title = "AUROC",        # Título del radar
    )

    # Ajustar la leyenda
    plot.new()
    legend("top",
           legend = tail(rownames(df1), -2),
           bty = "n", pch = 20, col = colores,
           pt.cex = 2, ncol = 6, cex=0.85)

    dev.off()  # Cerrar el archivo PDF
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
